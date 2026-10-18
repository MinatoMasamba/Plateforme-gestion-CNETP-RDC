"""Courriels envoyés après une nomination enregistrée, quel que soit son écran de saisie."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.template.loader import render_to_string
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.urls import reverse

from apps.experts.models import Expert
from .models import (
    CTM, WG, CTCMembership, ComitePilotage, ExecutiveLevel, MandatOrganisation,
    PilotageMembreship, PosteNominatif, PosteNominatifCTC, TechnicalCell,
)

logger = logging.getLogger(__name__)

LEADERS = {
    ComitePilotage: {
        'president_id': ('Président du Comité de pilotage', 'PRESIDENT'),
        'vice_president_id': ('Vice-président du Comité de pilotage', 'VICE_PRESIDENT'),
        'secretary_id': ('Secrétaire du Comité de pilotage', 'SECRETARY'),
        'rapporteur_id': ('Rapporteur général du Comité de pilotage', 'RAPPORTEUR'),
    },
    TechnicalCell: {
        'coordinator_id': ('Coordonnateur de la Cellule technique de coordination', 'COORDINATOR'),
        'vice_coordinator_id': ('Vice-coordonnateur de la Cellule technique de coordination', 'VICE_COORDINATOR'),
    },
    CTM: {
        'scientific_president_id': ('Président scientifique', None),
        'rapporteur_id': ('Rapporteur', None),
        'secretary_id': ('Secrétaire', None),
    },
    WG: {
        'president_id': ('Président', None),
        'rapporteur_id': ('Rapporteur', None),
        'secretary_id': ('Secrétaire', None),
    },
}

TRACKED = {
    Expert: ('appointment_decree_number', 'appointment_date'),
    PilotageMembreship: ('expert_id', 'comite_id', 'role'),
    CTCMembership: ('expert_id', 'ctc_id', 'role'),
    ExecutiveLevel: ('expert_id', 'position'),
    PosteNominatif: ('holder_id', 'role'),
    PosteNominatifCTC: ('holder_id', 'role'),
    MandatOrganisation: ('expert_id', 'status', 'poste_id', 'groupe_id'),
    **{model: tuple(fields) for model, fields in LEADERS.items()},
}


def _capture_previous(sender, instance, using, raw=False, **kwargs):
    if raw:
        return
    fields = TRACKED[sender]
    instance._nomination_previous = (
        sender.objects.using(using).filter(pk=instance.pk).values(*fields).first()
        if instance.pk else None
    )


def _send_mail(expert_id, title, organisation, path, reference='', start_date=None):
    expert = Expert.objects.select_related('user').filter(pk=expert_id).first()
    if not expert or not expert.user.email:
        logger.warning('Nomination sans adresse de courriel : expert %s', expert_id)
        return
    name = expert.full_name or expert.user.username
    site_url = settings.SITE_URL.rstrip('/') + path
    details = [
        f'Bonjour {name},', '',
        'Votre nomination a été enregistrée sur la plateforme CNE-ITP.', '',
        f'Fonction : {title}',
        f'Instance : {organisation}',
    ]
    if reference:
        details.append(f'Référence de nomination : {reference}')
    if start_date:
        details.append(f'Date de prise d’effet : {start_date:%d/%m/%Y}')
    details.extend(['', f'Consultez votre espace : {site_url}', '', 'Le Secrétariat technique CNE-ITP'])
    try:
        sent = send_mail(
            subject=f'[CNE-ITP] Votre nomination — {title}',
            message='\n'.join(details),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[expert.user.email],
            fail_silently=False,
            connection=get_connection(timeout=getattr(settings, 'EMAIL_TIMEOUT', 10)),
        )
        if not sent:
            logger.error('Aucun courriel de nomination envoyé pour expert %s', expert_id)
    except Exception:
        logger.exception('Échec du courriel de nomination pour expert %s', expert_id)


def _send_sc_nomination_mail(expert_id, mandat, organ, title):
    expert = Expert.objects.select_related('user').filter(pk=expert_id).first()
    if not expert or not expert.user.email:
        logger.warning('Nomination SC sans adresse de courriel : expert %s', expert_id)
        return
    path = reverse('web:expert_subcommission', args=[organ.pk])
    context = {
        'expert_name': expert.full_name or expert.user.username,
        'fonction': title,
        'sc_code': organ.code,
        'sc_name': organ.official_name or organ.name,
        'tome': organ.composition.get('tome', '—'),
        'reference': mandat.appointment_reference or (
            'Annexe 1 du rapport de réorganisation de la CNE-ITP, version adoptée du 15 octobre 2026.'
        ),
        'date_effet': mandat.start_date.strftime('%d/%m/%Y') if mandat.start_date else 'À confirmer',
        'sc_url': settings.SITE_URL.rstrip('/') + path,
    }
    subject = (
        "CNE-ITP | Notification officielle d’enregistrement de votre fonction "
        f"au sein de la {organ.code}"
    )
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=render_to_string('emails/nomination_sc.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[expert.user.email],
            connection=get_connection(timeout=getattr(settings, 'EMAIL_TIMEOUT', 10)),
        )
        message.attach_alternative(render_to_string('emails/nomination_sc.html', context), 'text/html')
        message.send(fail_silently=False)
    except Exception:
        logger.exception('Échec du courriel de nomination SC pour expert %s', expert_id)


def _covered_by_poste(item):
    if isinstance(item, PilotageMembreship):
        return PosteNominatif.objects.filter(comite_id=item.comite_id, holder_id=item.expert_id, role=item.role).exists()
    if isinstance(item, CTCMembership):
        return PosteNominatifCTC.objects.filter(ctc_id=item.ctc_id, holder_id=item.expert_id, role=item.role).exists()
    return False


def _covered_leader(model, item, expert_id, role):
    if model is ComitePilotage:
        return (
            PosteNominatif.objects.filter(comite_id=item.pk, holder_id=expert_id, role=role).exists()
            or PilotageMembreship.objects.filter(comite_id=item.pk, expert_id=expert_id, role=role).exists()
        )
    if model is TechnicalCell:
        return (
            PosteNominatifCTC.objects.filter(ctc_id=item.pk, holder_id=expert_id, role=role).exists()
            or CTCMembership.objects.filter(ctc_id=item.pk, expert_id=expert_id, role=role).exists()
        )
    return False


def _deliver(model, pk, expert_id, expected):
    item = model.objects.filter(pk=pk).first()
    if not item or any(getattr(item, field) != value for field, value in expected.items()):
        return
    if model is Expert:
        _send_mail(
            expert_id, 'Expert nommé', 'CNE-ITP', reverse('web:expert_profile'),
            reference=item.appointment_decree_number, start_date=item.appointment_date,
        )
    elif model is PilotageMembreship:
        if _covered_by_poste(item):
            return
        _send_mail(expert_id, item.get_role_display(), item.comite.name, reverse('web:pilotage_dashboard'))
    elif model is CTCMembership:
        if _covered_by_poste(item):
            return
        _send_mail(expert_id, item.get_role_display(), item.ctc.name, reverse('web:ctc_dashboard'))
    elif model is PosteNominatif:
        _send_mail(expert_id, item.title, item.comite.name, reverse('web:pilotage_dashboard'))
    elif model is PosteNominatifCTC:
        _send_mail(expert_id, item.title, item.ctc.name, reverse('web:ctc_dashboard'))
    elif model is MandatOrganisation:
        if item.status != 'ACTIVE':
            return
        if item.poste_id:
            organ = item.poste.organe
            title = item.poste.title or item.function
            if organ.type == 'SC':
                _send_sc_nomination_mail(expert_id, item, organ, title)
                return
            organisation = organ.official_name or organ.name
        else:
            title = item.function or 'Membre du groupe de travail'
            organisation = item.groupe.name
            if item.groupe and item.groupe.sc_id:
                _send_mail(
                    expert_id, title, organisation,
                    reverse('web:expert_subcommission', args=[item.groupe.sc_id]),
                    reference=item.appointment_reference, start_date=item.start_date,
                )
                return
        _send_mail(
            expert_id, title, organisation, reverse('web:phoenix_organisation'),
            reference=item.appointment_reference, start_date=item.start_date,
        )
    elif model is ExecutiveLevel:
        _send_mail(expert_id, item.get_position_display(), 'Tutelle institutionnelle', reverse('web:expert_profile'))
    else:
        for field, (title, role) in LEADERS[model].items():
            if field not in expected:
                continue
            if _covered_leader(model, item, expert_id, role):
                continue
            if model is CTM:
                organisation, path = str(item), reverse('web:app')
            elif model is WG:
                organisation, path = str(item), reverse('web:app')
            elif model is TechnicalCell:
                organisation, path = item.name, reverse('web:ctc_dashboard')
            else:
                organisation, path = item.name, reverse('web:pilotage_dashboard')
            _send_mail(expert_id, title, organisation, path)


def _on_saved(sender, instance, created, using, raw=False, **kwargs):
    if raw:
        return
    old = getattr(instance, '_nomination_previous', None) or {}
    if sender in LEADERS:
        changes = [
            (field, getattr(instance, field))
            for field in LEADERS[sender]
            if getattr(instance, field) and old.get(field) != getattr(instance, field)
        ]
        for field, expert_id in changes:
            transaction.on_commit(
                lambda model=sender, pk=instance.pk, eid=expert_id, key=field: _deliver(model, pk, eid, {key: eid}),
                using=using, robust=True,
            )
        return
    if sender is MandatOrganisation:
        if instance.status != 'ACTIVE' or (old.get('status') == 'ACTIVE' and old.get('expert_id') == instance.expert_id):
            return
        expected = {'expert_id': instance.expert_id, 'status': 'ACTIVE'}
        expert_id = instance.expert_id
    elif sender is Expert:
        if not instance.appointment_decree_number or old.get('appointment_decree_number') == instance.appointment_decree_number:
            return
        expected = {'appointment_decree_number': instance.appointment_decree_number}
        expert_id = instance.pk
    elif sender is ExecutiveLevel:
        if not instance.expert_id or (old.get('expert_id') == instance.expert_id and old.get('position') == instance.position):
            return
        expected = {'expert_id': instance.expert_id, 'position': instance.position}
        expert_id = instance.expert_id
    elif sender in (PosteNominatif, PosteNominatifCTC):
        if not instance.holder_id or (old.get('holder_id') == instance.holder_id and old.get('role') == instance.role):
            return
        expected = {'holder_id': instance.holder_id, 'role': instance.role}
        expert_id = instance.holder_id
    else:
        if not created and all(old.get(field) == getattr(instance, field) for field in TRACKED[sender]):
            return
        expected = {field: getattr(instance, field) for field in TRACKED[sender]}
        expert_id = instance.expert_id
    transaction.on_commit(
        lambda model=sender, pk=instance.pk, eid=expert_id, values=expected: _deliver(model, pk, eid, values),
        using=using, robust=True,
    )


for _model in TRACKED:
    pre_save.connect(_capture_previous, sender=_model, dispatch_uid=f'governance.nomination.before.{_model.__name__}')
    post_save.connect(_on_saved, sender=_model, dispatch_uid=f'governance.nomination.after.{_model.__name__}')
