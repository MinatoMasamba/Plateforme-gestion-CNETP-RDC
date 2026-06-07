# Plan : Implémentation Vote WG → Réunion CTM Automatique

## Contexte

La plateforme CNETP gère 200 experts répartis en 8 CTM (Comités Techniques Miroir) et 24 WG (Groupes de Travail). Chaque norme est développée par un WG (3-4 experts). Quand ce WG atteint la majorité (>50% FOR) sur une norme, il faut automatiquement :

1. Détecter la majorité dans le WG
2. Mettre à jour le statut de la norme (`CTM_REVIEW`)
3. Créer une réunion de type CTM pour TOUS les experts du CTM parent
4. Envoyer des notifications à tous les experts CTM
5. Après la réunion CTM : générer automatiquement le PV et envoyer au CTC par mail

Le projet possède déjà toutes les briques (modèles, Celery, notifications), mais le trigger manque et la logique existante `_sync_vote_progression()` saute l'étape CTM_REVIEW.

---

## Architecture actuelle à comprendre

**Modèles clés :**
- `NormeVote` (`apps/norms/models.py`) — vote d'un expert sur une norme (FOR/AGAINST/ABSTAIN), unique par (norme, voter)
- `Norme` (`apps/norms/models.py`) — champ `ctm` (FK), `wg` (FK), `status` (11 étapes dont `INTERNAL_REVIEW`, `CTM_REVIEW`, `LEGISTIC_REVIEW`)
- `Affectation` (`apps/governance/models.py`) — lie Expert ↔ CTM + WG, permet de récupérer TOUS les experts d'un CTM
- `Reunion` (`apps/meetings/models.py`) — type choices : `CTM`, `WG`, `PILOTAGE`, `CTC`, `ASSEMBLEE`
- `ProcessusVerbaux` (`apps/meetings/models.py`) — PV lié OneToOne à une Reunion
- `Notification` (`apps/mobileapp/models.py`) — type `REUNION_INVITE`, `VOTE_OPEN`, `SYSTEM` avec priority
- `dispatch_notification` (`apps/mobileapp/tasks.py`) — tâche Celery déjà opérationnelle
- `TechnicalCell` + `CTCMembership` (`apps/governance/models.py`) — permet d'obtenir les membres du CTC

**Flux statut existant Norme :**
```
DRAFT → INTERNAL_REVIEW → CTM_REVIEW → LEGISTIC_REVIEW → PUBLIC_INQUIRY → PILOTAGE_REVIEW → ADOPTED → HOMOLOGATED → PUBLISHED
```

**Problème actuel :** `_sync_vote_progression()` dans `api/v1/validation_views.py` passe directement de `INTERNAL_REVIEW` à `LEGISTIC_REVIEW` sans passer par `CTM_REVIEW` et sans créer de réunion.

---

## Référence : rôle de l'IA annoncé dans la note officielle (PDF "RÉPONSE DES ITP...")

La note de réponse du Cabinet du Ministre (Réf. RDC/MITP/CAB/2026/05/28, section II « L'Arme Technologique du Ministère : La plateforme Cloud collaborative propulsée par l'IA ») décrit 3 leviers IA censés équiper la plateforme CNETP. À garder en tête comme cadre de référence/cible pour aligner les développements (notifications, votes, synthèses) avec ce qui a été officiellement annoncé :

1. **Ingestion sémantique instantanée des référentiels mondiaux** : l'IA ingère les corpus normatifs internationaux (ISO, Eurocodes, normes US, SADC), exécute l'analyse comparative textuelle et identifie les points à adapter aux réalités congolaises (micro-climats, géologie). Un travail estimé à 9 mois d'effort humain serait automatisé en temps réel.

2. **Harmonisation transversale et détection des conflits en temps réel** : avec 200 experts répartis en 8 sous-commissions sur un Cloud unifié, l'IA agit en « copilote permanent » — dès qu'une formule est validée dans une sous-commission, elle vérifie la cohérence avec les critères des autres sous-commissions et élimine contradictions, doublons et erreurs de légistique.

3. **Automatisation et synthèse de l'enquête publique nationale** : un portail d'enquête publique où l'IA traite, classe par thématique, synthétise et intègre automatiquement les contributions citoyennes et amendements techniques des 26 provinces, réduisant le traitement de plusieurs mois à quelques jours.

Le tableau comparatif de la note chiffre l'impact à « réduction de 70% du temps administratif, élimination des erreurs de calcul et cohérence technique absolue » grâce à la « Plateforme collaborative Cloud + IA métier ».

---

## Implémentation

### Étape 1 : Signal de détection de majorité WG — `apps/norms/signals.py` (NOUVEAU)

Créer ce fichier avec un signal `post_save` sur `NormeVote` :

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import NormeVote
from .tasks import trigger_ctm_meeting_if_majority

@receiver(post_save, sender=NormeVote)
def check_wg_vote_majority(sender, instance, created, **kwargs):
    if not created:
        return
    norme = instance.norme
    # Seulement si la norme est en INTERNAL_REVIEW (phase WG)
    if norme.status not in ('DRAFT', 'INTERNAL_REVIEW'):
        return
    # Déléguer à Celery pour éviter le blocage en requête HTTP
    trigger_ctm_meeting_if_majority.delay(norme.id)
```

### Étape 2 : Tâche Celery — `apps/norms/tasks.py` (NOUVEAU)

```python
from celery import shared_task
from django.utils import timezone
import datetime

@shared_task(bind=True, max_retries=3)
def trigger_ctm_meeting_if_majority(self, norme_id):
    from .models import Norme, NormeVote
    from apps.governance.models import Affectation
    from apps.meetings.models import Reunion
    from apps.mobileapp.models import Notification
    from apps.mobileapp.tasks import dispatch_notification

    norme = Norme.objects.select_related('ctm', 'wg').get(id=norme_id)

    # 1. Calculer les votes des membres du WG uniquement
    wg_expert_ids = Affectation.objects.filter(
        wg=norme.wg
    ).values_list('expert_id', flat=True)

    votes = NormeVote.objects.filter(norme=norme, voter_id__in=wg_expert_ids)
    total = votes.count()
    for_votes = votes.filter(vote='FOR').count()

    # Majorité = >50% des votes exprimés par les membres du WG
    if total == 0 or (for_votes / total) <= 0.5:
        return  # Pas encore majorité

    # 2. Éviter les doublons : vérifier qu'une réunion CTM n'existe pas déjà pour cette norme
    existing = Reunion.objects.filter(
        type='CTM',
        ctm=norme.ctm,
        ordre_jour__icontains=f'norme:{norme.id}'  # marqueur unique
    ).exists()
    if existing:
        return

    # 3. Mettre à jour le statut de la norme
    norme.status = 'CTM_REVIEW'
    norme.ctm_submission_date = timezone.now().date()
    norme.save(update_fields=['status', 'ctm_submission_date'])

    # 4. Créer la réunion CTM dans 3 jours ouvrables
    meeting_date = timezone.now() + datetime.timedelta(days=3)
    vote_summary = f"{for_votes} POUR / {votes.filter(vote='AGAINST').count()} CONTRE / {votes.filter(vote='ABSTAIN').count()} ABSTENTION"

    reunion = Reunion.objects.create(
        type='CTM',
        titre=f"Réunion CTM {norme.ctm.number} - Examen norme {norme.reference_number}",
        description=f"Examen et harmonisation de la norme '{norme.title}' proposée par {norme.wg.name}.",
        ctm=norme.ctm,
        wg=norme.wg,
        date=meeting_date,
        status='PLANNED',
        ordre_jour=(
            f"1. Présentation de la norme '{norme.title}'
"
            f"2. Résultats vote WG: {vote_summary}
"
            f"3. Vérification cohérence inter-WG
"
            f"4. Vote au niveau CTM
"
            f"5. Divers
"
            f"norme:{norme.id}"  # marqueur pour éviter doublons
        ),
    )

    # 5. Notifier TOUS les experts du CTM
    ctm_expert_ids = Affectation.objects.filter(
        ctm=norme.ctm
    ).select_related('expert__user').values_list('expert_id', flat=True).distinct()

    for expert_id in ctm_expert_ids:
        from apps.experts.models import Expert
        expert = Expert.objects.select_related('user').get(id=expert_id)
        notif = Notification.objects.create(
            user=expert.user,
            title=f"🔔 Réunion CTM {norme.ctm.number} convoquée",
            body=(
                f"La norme '{norme.title}' a atteint la majorité dans {norme.wg.name}.
"
                f"Résultats WG: {vote_summary}
"
                f"Réunion CTM prévue le {meeting_date.strftime('%d/%m/%Y à %Hh%M')}."
            ),
            notification_type='REUNION_INVITE',
            priority='HIGH',
            data={
                'reunion_id': reunion.id,
                'norme_id': norme.id,
                'norme_title': norme.title,
                'vote_summary': vote_summary,
                'meeting_date': meeting_date.isoformat(),
            }
        )
        dispatch_notification.delay(str(notif.id))
```

### Étape 3 : Enregistrer le signal — `apps/norms/apps.py` (MODIFIÉ)

```python
class NormsConfig(AppConfig):
    ...
    def ready(self):
        import apps.norms.signals  # Enregistre les signaux
```

### Étape 4 : Corriger `_sync_vote_progression()` — `api/v1/validation_views.py` (MODIFIÉ)

Empêcher l'auto-promotion de INTERNAL_REVIEW → LEGISTIC_REVIEW directement. Le signal se charge désormais du passage INTERNAL_REVIEW → CTM_REVIEW.

```python
def _sync_vote_progression(self):
    normes = Norme.objects.filter(status__in=['INTERNAL_REVIEW'])
    for norme in normes:
        summary = self._vote_summary(norme)
        # NE PLUS auto-promouvoir ici : le signal NormeVote s'en charge
        # Conserver uniquement la logique CTM_REVIEW → LEGISTIC_REVIEW
    
    # CTM_REVIEW → LEGISTIC_REVIEW (après vote CTM via ReunionVote)
    normes_ctm = Norme.objects.filter(status='CTM_REVIEW')
    for norme in normes_ctm:
        # Vérifier vote CTM dans la Reunion associée
        reunion = Reunion.objects.filter(
            type='CTM', ctm=norme.ctm,
            ordre_jour__icontains=f'norme:{norme.id}',
            status='COMPLETED'
        ).first()
        if reunion:
            votes = reunion.votes.all()
            total = votes.count()
            for_v = votes.filter(choix='POUR').count()
            if total > 0 and (for_v / total) > 0.5:
                norme.status = 'LEGISTIC_REVIEW'
                norme.legistic_review_date = timezone.now().date()
                norme.save(update_fields=['status', 'legistic_review_date'])
                # Envoyer la norme et le PV au CTC
                send_norme_to_ctc.delay(norme.id, reunion.id)
```

### Étape 5 : Tâche d'envoi au CTC — ajout dans `apps/norms/tasks.py`

```python
@shared_task
def send_norme_to_ctc(norme_id, reunion_id):
    """Envoie la norme approuvée par le CTM au CTC (Cellule Technique de Coordination)"""
    from apps.meetings.models import Reunion, ProcessusVerbaux
    from apps.governance.models import TechnicalCell, CTCMembership
    from apps.mobileapp.models import Notification
    from apps.mobileapp.tasks import dispatch_notification

    norme = Norme.objects.get(id=norme_id)
    reunion = Reunion.objects.get(id=reunion_id)

    # Récupérer PV existant ou le créer
    pv, _ = ProcessusVerbaux.objects.get_or_create(
        reunion=reunion,
        defaults={
            'titre': f"PV Réunion CTM {norme.ctm.number} - {norme.reference_number}",
            'contenu': _generate_pv_content(reunion, norme),
            'nombre_presents': reunion.presences.filter(status='PRESENT').count(),
            'nombre_absents': reunion.presences.filter(status='ABSENT').count(),
            'quorum_atteint': True,
        }
    )

    # Notifier tous les membres du CTC
    ctc_members = CTCMembership.objects.select_related('expert__user').all()
    for membership in ctc_members:
        notif = Notification.objects.create(
            user=membership.expert.user,
            title=f"📋 Norme approuvée par CTM {norme.ctm.number}",
            body=f"La norme '{norme.title}' ({norme.reference_number}) a été approuvée par le CTM et est transmise au CTC pour toilettage légistique.",
            notification_type='NORM_UPDATE',
            priority='HIGH',
            data={'norme_id': norme.id, 'pv_id': pv.id}
        )
        dispatch_notification.delay(str(notif.id))
```

---

## Fichiers à créer / modifier

| Fichier | Action | Contenu |
|---------|--------|---------|
| `apps/norms/signals.py` | **CRÉER** | Signal `post_save` sur `NormeVote` |
| `apps/norms/tasks.py` | **CRÉER** | `trigger_ctm_meeting_if_majority`, `send_norme_to_ctc` |
| `apps/norms/apps.py` | **MODIFIER** | Ajouter `import apps.norms.signals` dans `ready()` |
| `api/v1/validation_views.py` | **MODIFIER** | Corriger `_sync_vote_progression()` pour gérer CTM_REVIEW |

---

## Points d'attention

1. **Anti-doublon** : Le marqueur `norme:{norme.id}` dans `ordre_jour` évite de créer plusieurs réunions CTM pour la même norme.
2. **Majorité WG vs majorité générale** : Le signal filtre uniquement les votes des experts de `norme.wg` (via `Affectation`), pas tous les votes.
3. **Celery requis** : Vérifier que Celery est actif (`config/settings.py` lignes 169-173 décommentées). En dev, utiliser `CELERY_TASK_ALWAYS_EAGER = True`.
4. **Statut Norme** : Ne déclencher que si `status in ('DRAFT', 'INTERNAL_REVIEW')` — évite les re-déclenchements.
5. **Signals mobileapp** : Les fonctions `notify_meeting_invite()` existent dans `apps/mobileapp/signals.py` mais ne sont pas câblées — notre tâche Celery s'occupe directement des notifications.

---

## Vérification / Tests

1. Créer une norme liée à un WG avec 3 experts
2. Voter FOR avec 2 experts (>50%) → vérifier :
   - `norme.status == 'CTM_REVIEW'`
   - `Reunion` créée avec `type='CTM'` et `ctm=norme.ctm`
   - `Notification` créée pour chaque expert du CTM (pas seulement du WG)
3. Marquer la réunion CTM comme `COMPLETED` + voter POUR via `ReunionVote`
4. Appeler `_sync_vote_progression()` → vérifier `norme.status == 'LEGISTIC_REVIEW'`
5. Vérifier `ProcessusVerbaux` créé et notifications envoyées aux membres CTC

```bash
# Lancer Celery en dev (eager mode)
CELERY_TASK_ALWAYS_EAGER=True python manage.py test tests/ -v 2
```