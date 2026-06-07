import datetime

from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def trigger_ctm_meeting_if_majority(self, norme_id):
    """Convoque automatiquement le CTM quand le WG porteur atteint la majorité FOR."""
    from .models import Norme, NormeVote
    from apps.governance.models import Affectation
    from apps.meetings.models import Reunion
    from apps.mobileapp.models import Notification
    from apps.mobileapp.tasks import dispatch_notification

    norme = Norme.objects.select_related('ctm', 'wg').get(id=norme_id)

    wg_expert_ids = Affectation.objects.filter(wg=norme.wg).values_list('expert_id', flat=True)

    votes = NormeVote.objects.filter(norme=norme, voter_id__in=wg_expert_ids)
    total = votes.count()
    for_votes = votes.filter(vote='FOR').count()

    if total == 0 or (for_votes / total) <= 0.5:
        return

    marker = f'norme:{norme.id}'
    if Reunion.objects.filter(type='CTM', ctm=norme.ctm, ordre_jour__icontains=marker).exists():
        return

    norme.status = 'CTM_REVIEW'
    norme.ctm_submission_date = timezone.now().date()
    norme.save(update_fields=['status', 'ctm_submission_date'])

    meeting_date = timezone.now() + datetime.timedelta(days=3)
    vote_summary = (
        f"{for_votes} POUR / {votes.filter(vote='AGAINST').count()} CONTRE / "
        f"{votes.filter(vote='ABSTAIN').count()} ABSTENTION"
    )

    reunion = Reunion.objects.create(
        type='CTM',
        titre=f"Réunion CTM {norme.ctm.number} - Examen norme {norme.reference_number}",
        description=(
            f"Examen et harmonisation de la norme '{norme.title}' proposée par {norme.wg.name}."
        ),
        ctm=norme.ctm,
        wg=norme.wg,
        date=meeting_date,
        status='PLANNED',
        ordre_jour=(
            f"1. Présentation de la norme '{norme.title}'\n"
            f"2. Résultats vote WG: {vote_summary}\n"
            f"3. Vérification cohérence inter-WG\n"
            f"4. Vote au niveau CTM\n"
            f"5. Divers\n"
            f"{marker}"
        ),
    )

    ctm_expert_ids = Affectation.objects.filter(ctm=norme.ctm).values_list('expert_id', flat=True).distinct()

    from apps.experts.models import Expert

    for expert in Expert.objects.filter(id__in=ctm_expert_ids).select_related('user'):
        notif = Notification.objects.create(
            user=expert.user,
            title=f"Réunion CTM {norme.ctm.number} convoquée",
            body=(
                f"La norme '{norme.title}' a atteint la majorité dans {norme.wg.name}.\n"
                f"Résultats WG: {vote_summary}\n"
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
            },
        )
        dispatch_notification.delay(str(notif.id))


def _generate_pv_content(reunion, norme):
    presents = reunion.presences.filter(status='PRESENT').count()
    absents = reunion.presences.filter(status='ABSENT').count()
    votes = reunion.votes.all()
    total = votes.count()
    for_v = votes.filter(choix='POUR').count()
    against_v = votes.filter(choix='CONTRE').count()
    abstain_v = votes.filter(choix='ABSTENTION').count()
    return (
        f"Procès-verbal de la réunion CTM '{reunion.titre}' du "
        f"{reunion.date.strftime('%d/%m/%Y')}.\n\n"
        f"Norme examinée : {norme.title} ({norme.reference_number})\n"
        f"Présents : {presents} / Absents : {absents}\n\n"
        f"Résultat du vote CTM : {for_v} POUR / {against_v} CONTRE / {abstain_v} ABSTENTION "
        f"(total {total})\n\n"
        f"Décision : la norme est transmise à la Cellule Technique de Coordination (CTC) "
        f"pour toilettage légistique."
    )


@shared_task
def send_norme_to_ctc(norme_id, reunion_id):
    """Transmet la norme approuvée par le CTM au CTC pour toilettage légistique."""
    from .models import Norme
    from apps.meetings.models import Reunion, ProcessusVerbaux
    from apps.governance.models import CTCMembership
    from apps.mobileapp.models import Notification
    from apps.mobileapp.tasks import dispatch_notification

    norme = Norme.objects.select_related('ctm', 'wg').get(id=norme_id)
    reunion = Reunion.objects.get(id=reunion_id)

    pv, _ = ProcessusVerbaux.objects.get_or_create(
        reunion=reunion,
        defaults={
            'titre': f"PV Réunion CTM {norme.ctm.number} - {norme.reference_number}",
            'contenu': _generate_pv_content(reunion, norme),
            'nombre_presents': reunion.presences.filter(status='PRESENT').count(),
            'nombre_absents': reunion.presences.filter(status='ABSENT').count(),
            'quorum_atteint': True,
        },
    )

    for membership in CTCMembership.objects.select_related('expert__user'):
        notif = Notification.objects.create(
            user=membership.expert.user,
            title=f"Norme approuvée par CTM {norme.ctm.number}",
            body=(
                f"La norme '{norme.title}' ({norme.reference_number}) a été approuvée par le CTM "
                f"et est transmise au CTC pour toilettage légistique."
            ),
            notification_type='NORM_UPDATE',
            priority='HIGH',
            data={'norme_id': norme.id, 'pv_id': pv.id},
        )
        dispatch_notification.delay(str(notif.id))
