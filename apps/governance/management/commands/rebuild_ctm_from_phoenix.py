"""
Reconstruit les CTM à partir du référentiel Phoenix (unification CTM == SC).

Le Manuel Organisationnel CNE-ITP 2026 traite les « Comités Techniques Miroirs »
(CTM) et les « Sous-Commissions » (SC) comme une seule et même entité. Cette
commande :

  1. supprime les 8 CTM historiques (et leurs rattachements obsolètes) ;
  2. crée les CTM unifiés depuis les 7 SC Phoenix (Organe type='SC') ;
  3. récupère les groupes de travail (WG) existants et les rattache au bon CTM
     en fonction de leur nom ;
  4. reporte les normes, affectations, experts et réunions sur les nouvelles
     entités.

Sans l'option ``--apply``, la commande n'écrit rien : elle affiche le plan de
migration (mapping WG -> SC) pour validation.
"""

import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.governance.models import CTM, WG, Affectation, Demande, Tache
from apps.governance.phoenix_models import (
    OrganisationVersion, Organe, CorrespondanceStructure, CorrespondanceGroupe,
    AffectationSousCommission, ChoixOrganisationExpert,
)
from apps.experts.models import Expert
from apps.norms.models import Norme


def _fold(text):
    """Minuscule sans accents pour un matching de noms tolérant."""
    normalized = unicodedata.normalize('NFKD', text or '')
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


# Description institutionnelle de chaque SC (utilisée pour remplir CTM.description).
SC_DESCRIPTIONS = {
    'SC-BAT': (
        "Bâtiments courants et spéciaux : conception structurelle, habitabilité, "
        "sécurité incendie, performance énergétique, confort et urbanisme."
    ),
    'SC-ENV': (
        "Environnement, santé et sécurité : gestion des déchets solides, "
        "assainissement, prévention des pollutions et protection des travailleurs."
    ),
    'SC-GF': (
        "Géotechnique et fondations : reconnaissance des sols, géomécanique, "
        "stabilité des talus, soutènements et prévention des risques naturels."
    ),
    'SC-IT': (
        "Infrastructures de transport : routes, voies ferrées, aéroports, "
        "ouvrages portuaires et équipements associés."
    ),
    'SC-OH': (
        "Ouvrages hydrauliques : adduction d'eau, irrigation, drainage, barrages, "
        "assainissement et gestion des eaux pluviales."
    ),
    'SC-VRD': (
        "Réseaux divers, équipements et fluides : signalisation, géomatique, "
        "réseaux secs, télécommunications, cartographie et équipements d'infrastructures."
    ),
    'SC-SOCLE': (
        "Domaine technique transversal : calcul structural, matériaux locaux, "
        "métrologie, essais, simulation, recherche et normalisation appliquée."
    ),
}

# Règles de rattachement par nom (première correspondance gagnante, ordre
# significatif). Les mots-clés sont comparés en minuscules sans accents.
SC_KEYWORDS = [
    ('SC-GF', ['geotechnique', 'geomecanique', 'fondation', 'sols', 'stabilite',
               'erosion', 'risques naturels', 'talus', 'soutenement', 'geomateriau']),
    ('SC-OH', ['hydraulique', 'adduction', 'irrigation', 'drainage', 'forage',
               'captage', 'barrage', 'assainissement', 'epuration', 'pluviale', 'egout', 'eau']),
    ('SC-IT', ['transport', 'routiere', 'routier', 'ferree', 'ferroviaire', 'aeroport',
               'oaci', 'terminaux', 'portuaire', 'voie']),
    ('SC-BAT', ['batiment', 'habitabilite', 'securite', 'energetique', 'incendie',
                'bim', 'urbanisme', 'structure', 'construction']),
    ('SC-ENV', ['environnement', 'dechet', 'cet', 'sante', 'pollution']),
    ('SC-VRD', ['signalisation', 'equipement', 'geomatique', 'reseaux secs',
                'telecommunication', 'cartographie', 'numerique', 'vrd', 'fluide']),
    ('SC-SOCLE', ['materiau', 'metrologie', 'essai', 'calcul', 'mecanique', 'eurocode',
                  'parasismique', 'simulation', 'recherche', 'certification',
                  'normalisation', 'cout', 'circuit', 'composant', 'transversal']),
]

# Correctifs manuels pour les noms ambigus (clé = nom nettoyé, sans accents).
WG_OVERRIDES = {
    'materiaux de construction locaux': 'SC-SOCLE',
    'materiaux de construction': 'SC-BAT',
    'structures et securite': 'SC-BAT',
    'simulation et recherche': 'SC-SOCLE',
    'simulation, recherche & certification': 'SC-SOCLE',
    'composants et circuits': 'SC-SOCLE',
    'calcul mecanique': 'SC-SOCLE',
    'essais et metrologie': 'SC-SOCLE',
    'normalisation appliquee': 'SC-SOCLE',
}


def clean_wg_name(name):
    """Retire le préfixe 'SURPLUS - ' et les espaces parasites."""
    cleaned = (name or '').strip()
    upper = cleaned.upper()
    if upper.startswith('SURPLUS - '):
        cleaned = cleaned[len('SURPLUS - '):].strip()
    elif upper.startswith('SURPLUS-'):
        cleaned = cleaned[len('SURPLUS-'):].strip()
    return cleaned


def match_sc(wg_name):
    """Détermine le code SC cible à partir du nom nettoyé du groupe."""
    key = _fold(wg_name)
    if key in WG_OVERRIDES:
        return WG_OVERRIDES[key]
    for sc_code, keywords in SC_KEYWORDS:
        for keyword in keywords:
            if keyword in key:
                return sc_code
    return 'SC-SOCLE'


class Command(BaseCommand):
    help = "Reconstruit les CTM depuis le référentiel Phoenix (unification CTM == SC)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help="Exécute réellement la migration (sans ce drapeau : dry-run)."
        )
        parser.add_argument(
            '--code', default=None,
            help="Code de la version d'organisation (défaut : la plus récente).",
        )

    def handle(self, *args, **options):
        apply = options['apply']

        if options.get('code'):
            version = OrganisationVersion.objects.filter(code=options['code']).first()
        else:
            version = OrganisationVersion.objects.order_by('-created_at', '-id').first()
        if not version:
            raise SystemExit("Aucune version d'organisation trouvée : impossible de reconstruire.")

        scs = list(Organe.objects.filter(
            version=version, type=Organe.Type.SC,
        ).order_by('code'))
        if len(scs) != 7 or len({sc.code for sc in scs}) != 7:
            raise SystemExit(
                f"La version {version.code} doit contenir exactement 7 SC distinctes "
                f"(trouvées : {len(scs)}). Utilisez --code pour choisir la bonne version."
            )
        scs_by_code = {sc.code: sc for sc in scs}

        old_ctms = list(CTM.objects.order_by('number'))

        # ── Mapping SC -> (number, description, iso, arso) ────────────────────
        # Héritage ISO/ARSO depuis le CTM historique via CorrespondanceStructure.
        ctm_to_sc = {
            cs.ctm_id: cs.sc.code
            for cs in CorrespondanceStructure.objects.filter(
                version=version, sc__isnull=False, nature='PRIMARY', status='VALIDATED'
            ).select_related('sc')
            if cs.sc.code in scs_by_code
        }
        sc_iso = {}
        sc_arso = {}
        for ctm in old_ctms:
            code = ctm_to_sc.get(ctm.pk)
            if not code:
                candidate = match_sc(ctm.name)
                code = candidate if candidate in scs_by_code else None
            if code:
                ctm_to_sc[ctm.pk] = code
                sc_iso.setdefault(code, ctm.iso_reference)
                sc_arso.setdefault(code, ctm.arso_reference)

        new_ctms = []
        for idx, sc in enumerate(scs, start=1):
            new_ctms.append({
                'number': idx,
                'code': sc.code,
                'name': sc.official_name or sc.name,
                'description': SC_DESCRIPTIONS.get(sc.code, sc.domain),
                'iso_reference': sc_iso.get(sc.code, ''),
                'arso_reference': sc_arso.get(sc.code, ''),
            })

        # ── Mapping WG -> SC cible (par nom) ─────────────────────────────────
        wg_plan = []
        for ctm in old_ctms:
            for wg in ctm.working_groups.order_by('number'):
                cleaned = clean_wg_name(wg.name)
                target_sc = match_sc(cleaned)
                if target_sc not in scs_by_code:
                    target_sc = 'SC-SOCLE'
                wg_plan.append({
                    'id': wg.pk,
                    'old_ctm': ctm.number,
                    'old_number': wg.number,
                    'cleaned_name': cleaned,
                    'target_sc': target_sc,
                    'description': wg.description,
                    'president_id': wg.president_id,
                    'rapporteur_id': wg.rapporteur_id,
                    'secretary_id': wg.secretary_id,
                })

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Plan de migration CTM/SC — version {version.code} ({version.get_status_display()})"
        ))
        for ctm in new_ctms:
            self.stdout.write(
                f"  CTM {ctm['number']} ({ctm['code']}) : {ctm['name']}"
            )
        self.stdout.write("\nRattachement des groupes de travail :")
        for item in wg_plan:
            self.stdout.write(
                f"  CTM{item['old_ctm']}.{item['old_number']} « {item['cleaned_name']} » -> {item['target_sc']}"
            )

        if not apply:
            self.stdout.write(
                self.style.WARNING("\nDry-run : aucune écriture. Relancez avec --apply pour appliquer.")
            )
            return

        # ── Application réelle ───────────────────────────────────────────────
        with transaction.atomic():
            # 1. Capture des références à préserver.
            norme_refs = list(Norme.all_objects.filter(
                Q(ctm__isnull=False) | Q(wg__isnull=False)
            ).values_list('id', 'ctm_id', 'wg_id', 'circuit_version'))
            affectation_refs = list(Affectation.objects.values_list(
                'expert_id', 'ctm_id', 'wg_id', 'is_primary_ctm', 'is_primary_wg'
            ))
            expert_refs = list(Expert.objects.filter(ctm__isnull=False).values_list('id', 'ctm_id'))
            reunion_refs = []
            try:
                from apps.meetings.models import Reunion
                reunion_refs = list(Reunion.objects.filter(
                    Q(ctm__isnull=False) | Q(wg__isnull=False)
                ).values_list('id', 'ctm_id', 'wg_id'))
            except ImportError:
                pass

            # 2. Purge des correspondances obsolètes (PROTECT sur CTM/WG).
            AffectationSousCommission.objects.update(
                source_ctm=None, source_wg=None, source_affectation=None,
                structure_mapping=None, group_mapping=None,
            )
            ChoixOrganisationExpert.objects.update(source_wg=None)
            CorrespondanceStructure.objects.all().delete()
            CorrespondanceGroupe.objects.all().delete()

            # 3. Neutralisation des FK PROTECT vers CTM/WG avant suppression.
            #    La contrainte CHECK exige ctm ET wg sur les normes LEGACY :
            #    on bascule temporairement en PHOENIX pour autoriser la nullité.
            Norme.all_objects.filter(circuit_version='LEGACY').update(circuit_version='PHOENIX')
            Norme.all_objects.filter(ctm__isnull=False).update(ctm=None)
            Norme.all_objects.filter(wg__isnull=False).update(wg=None)
            Demande.objects.update(groupe=None, sous_commission=None)
            Tache.objects.update(working_group=None)
            Affectation.objects.all().delete()

            # 4. Suppression des anciens CTM (cascade : WG + affectations).
            CTM.objects.all().delete()

            # 5. Création des nouveaux CTM.
            created_ctms = {}
            for item in new_ctms:
                created_ctms[item['code']] = CTM.objects.create(
                    number=item['number'],
                    name=item['name'],
                    description=item['description'],
                    iso_reference=item['iso_reference'],
                    arso_reference=item['arso_reference'],
                )

            # 6. Recréation des WG sous les nouveaux CTM (renumérotation + fusion).
            old_wg_to_new = {}
            counters = {}
            seen = {}
            for item in sorted(wg_plan, key=lambda x: (x['target_sc'], x['id'])):
                dedup_key = (item['target_sc'], _fold(item['cleaned_name']))
                if dedup_key in seen:
                    old_wg_to_new[item['id']] = seen[dedup_key]
                    continue
                ctm = created_ctms[item['target_sc']]
                counters[item['target_sc']] = counters.get(item['target_sc'], 0) + 1
                new_wg = WG.objects.create(
                    ctm=ctm,
                    number=counters[item['target_sc']],
                    name=item['cleaned_name'],
                    description=item['description'],
                    president_id=item['president_id'],
                    rapporteur_id=item['rapporteur_id'],
                    secretary_id=item['secretary_id'],
                )
                seen[dedup_key] = new_wg
                old_wg_to_new[item['id']] = new_wg

            # 7. Report des références.
            for norme_id, ctm_id, wg_id, circuit_version in norme_refs:
                new_wg = old_wg_to_new.get(wg_id) if wg_id else None
                new_ctm = new_wg.ctm if new_wg else (
                    created_ctms.get(ctm_to_sc.get(ctm_id)) if ctm_id else None
                )
                Norme.all_objects.filter(pk=norme_id).update(
                    ctm=new_ctm, wg=new_wg, circuit_version=circuit_version
                )

            for expert_id, ctm_id in expert_refs:
                code = ctm_to_sc.get(ctm_id)
                new_ctm = created_ctms.get(code) if code else None
                Expert.objects.filter(pk=expert_id).update(ctm=new_ctm)

            for reunion_id, ctm_id, wg_id in reunion_refs:
                new_wg = old_wg_to_new.get(wg_id) if wg_id else None
                new_ctm = new_wg.ctm if new_wg else (
                    created_ctms.get(ctm_to_sc.get(ctm_id)) if ctm_id else None
                )
                try:
                    from apps.meetings.models import Reunion
                    Reunion.objects.filter(pk=reunion_id).update(ctm=new_ctm, wg=new_wg)
                except ImportError:
                    pass

            # 8. Recréation des affectations.
            for expert_id, old_ctm_id, old_wg_id, prim_ctm, prim_wg in affectation_refs:
                new_wg = old_wg_to_new.get(old_wg_id)
                code = ctm_to_sc.get(old_ctm_id)
                new_ctm = created_ctms.get(code)
                if new_ctm is None and new_wg is not None:
                    new_ctm = new_wg.ctm
                if new_ctm is None:
                    continue
                Affectation.objects.create(
                    expert_id=expert_id,
                    ctm=new_ctm,
                    wg=new_wg,
                    is_primary_ctm=prim_ctm,
                    is_primary_wg=prim_wg,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Migration terminée : {len(created_ctms)} CTM créés, "
            f"{len(old_wg_to_new)} groupes de travail réattachés."
        ))
