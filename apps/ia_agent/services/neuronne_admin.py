"""Opérations d'administration réservées à l'assistant Neuronne.

Chaque fonction écrit une trace ``AuditLog`` et laisse les signaux métier
envoyer les courriels de nomination. Aucun outil n'est exposé hors de
l'assistant IA aux comptes de la console.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.models import AuditLog, PasswordResetCode
from apps.dashboard.console_permissions import console_group_name, has_console_access
from apps.experts.models import Expert, Structure

User = get_user_model()


# ─── Garde et audit ─────────────────────────────────────────────────────────

def is_neuronne_admin(user):
    """Compte autorisé à utiliser les outils d'administration de Neuronne."""
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.is_staff
        and has_console_access(user)
    )


def require_neuronne_admin(user):
    if not is_neuronne_admin(user):
        raise PermissionDenied(
            "Action réservée à Neuronne, l'assistant d'administration de la console."
        )
    return user


def record_action(user, action, instance, *, tool, changes=None, message=''):
    """Tracer une action Neuronne dans le journal d'audit applicatif."""
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=instance._meta.label,
        object_id=instance.pk,
        object_repr=str(instance)[:200],
        changes=changes or {},
        ip_address=None,
        user_agent=f'Neuronne IA · {tool}'[:200],
    )


def _audit_user(user, action, target_user, *, changes=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type='core.User',
        object_id=target_user.pk,
        object_repr=str(target_user)[:200],
        changes=changes or {},
        ip_address=None,
        user_agent='Neuronne IA · administration',
    )


# ─── Résolution des comptes et entités ──────────────────────────────────────

def _resolve_user(identifier):
    value = str(identifier or '').strip()
    if not value:
        raise ValidationError('Identifiant utilisateur requis (email ou identifiant numérique).')
    if value.isdigit():
        user = User.objects.filter(pk=int(value)).first()
    else:
        user = User.objects.filter(email__iexact=value).first()
    if user is None:
        raise ValidationError('Aucun compte ne correspond à cet email ou identifiant.')
    return user


def _resolve_expert(user):
    return Expert.objects.select_related('user', 'structure').filter(user=user).first()


def _resolve_ctc(ctc_id=None, ctc_name=None):
    from apps.governance.models import TechnicalCell

    if ctc_id:
        return TechnicalCell.objects.get(pk=ctc_id)
    if ctc_name:
        matches = list(TechnicalCell.objects.filter(name__icontains=ctc_name)[:2])
        if len(matches) == 1:
            return matches[0]
    raise ValidationError('Cellule technique introuvable ; fournir ctc_id ou un nom exact.')


def _resolve_copil(comite_id=None, comite_name=None):
    from apps.governance.models import ComitePilotage

    if comite_id:
        return ComitePilotage.objects.get(pk=comite_id)
    if comite_name:
        matches = list(ComitePilotage.objects.filter(name__icontains=comite_name)[:2])
        if len(matches) == 1:
            return matches[0]
    raise ValidationError('Comité de pilotage introuvable ; fournir comite_id ou un nom exact.')


def _resolve_sc(sc_id=None, sc_code=None):
    from apps.governance.phoenix_models import Organe
    from apps.governance.phoenix_runtime import current_organisation_version

    version = current_organisation_version()
    if version is None:
        raise ValidationError("Aucune version d'organisation courante.")
    qs = Organe.objects.filter(version=version, type='SC')
    if sc_id:
        sc = qs.filter(pk=sc_id).first()
    elif sc_code:
        sc = qs.filter(code__iexact=sc_code.strip()).first()
    else:
        sc = None
    if sc is None:
        raise ValidationError('Sous-commission introuvable dans la version courante.')
    return sc, version


def _resolve_gt(gt_id=None, gt_code=None, sc_code=None):
    from apps.governance.phoenix_models import GroupeCible
    from apps.governance.phoenix_runtime import current_organisation_version

    version = current_organisation_version()
    if version is None:
        raise ValidationError("Aucune version d'organisation courante.")
    qs = GroupeCible.objects.select_related('sc').filter(sc__version=version)
    if gt_id:
        gt = qs.filter(pk=gt_id).first()
    elif gt_code:
        qs = qs.filter(code__iexact=gt_code.strip())
        if sc_code:
            qs = qs.filter(sc__code__iexact=sc_code.strip())
        matches = list(qs[:2])
        gt = matches[0] if len(matches) == 1 else None
    else:
        gt = None
    if gt is None:
        raise ValidationError('Groupe de travail introuvable ou ambigu ; fournir gt_id.')
    return gt, version


def _resolve_ctm(ctm_id=None, ctm_number=None):
    from apps.governance.models import CTM

    if ctm_id:
        return CTM.objects.get(pk=ctm_id)
    if ctm_number:
        return CTM.objects.get(number=ctm_number)
    raise ValidationError('CTM introuvable ; fournir ctm_id ou ctm_number.')


def _resolve_wg(wg_id=None, wg_number=None, ctm=None):
    from apps.governance.models import WG

    if wg_id:
        return WG.objects.get(pk=wg_id)
    if ctm is not None and wg_number:
        return WG.objects.get(ctm=ctm, number=wg_number)
    raise ValidationError('Groupe de travail historique introuvable.')


# ─── Création de compte ─────────────────────────────────────────────────────

def _unique_username(email):
    base = (email.split('@')[0] or 'utilisateur').lower()
    base = ''.join(c for c in base if c.isalnum() or c in '._-')[:140] or 'utilisateur'
    candidate, index = base, 1
    while User.objects.filter(username=candidate).exists():
        index += 1
        candidate = f'{base}{index}'
    return candidate


def _send_account_email(user_obj, code):
    url = settings.SITE_URL.rstrip('/') + reverse('web:password_reset_confirm')
    body = (
        f"Bonjour {user_obj.get_full_name() or user_obj.username},\n\n"
        "Votre compte CNE-ITP a été créé par l'administration.\n"
        f"Identifiant : {user_obj.username}\n"
        f"Code de définition du mot de passe : {code} (valable 15 minutes)\n"
        f"Page de réinitialisation : {url}\n\n"
        "Le Secrétariat technique CNE-ITP"
    )
    send_mail(
        '[CNE-ITP] Votre compte a été créé',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user_obj.email],
        fail_silently=False,
    )


@transaction.atomic
def create_platform_user(
    actor, *, email, first_name='', last_name='', username=None,
    phone='', province='', is_expert=False, structure_id=None,
    expert_status='PENDING', send_email=True,
):
    """Créer un compte ; un expert exige une structure d'origine."""
    require_neuronne_admin(actor)
    email = str(email or '').strip().lower()
    if not email or '@' not in email:
        raise ValidationError('Email valide obligatoire.')
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError('Un compte utilise déjà cet email.')

    username = (username or _unique_username(email)).strip()
    if User.objects.filter(username=username).exists():
        raise ValidationError('Ce nom d’utilisateur existe déjà.')

    user_obj = User(
        username=username,
        email=email,
        first_name=str(first_name or '').strip()[:150],
        last_name=str(last_name or '').strip()[:150],
        phone=str(phone or '').strip()[:20],
        province=str(province or '').strip()[:100],
        is_expert=bool(is_expert),
        is_active=True,
    )
    user_obj.set_unusable_password()
    user_obj.save()

    expert = None
    if is_expert:
        structure = Structure.objects.filter(pk=structure_id).first() if structure_id else None
        if structure is None:
            raise ValidationError('structure_id est obligatoire pour créer une fiche expert.')
        if expert_status not in dict(Expert.STATUS_CHOICES):
            raise ValidationError('Statut expert invalide.')
        expert = Expert.objects.create(
            user=user_obj, structure=structure, status=expert_status,
        )

    email_sent = False
    if send_email:
        code = PasswordResetCode.generate_for(user_obj)
        try:
            _send_account_email(user_obj, code.code)
            email_sent = True
        except Exception:
            # Le compte reste créé ; l'échec est signalé à l'outil.
            email_sent = False

    _audit_user(actor, 'CREATE', user_obj, changes={
        'email': email,
        'is_expert': bool(is_expert),
        'expert_id': expert.pk if expert else None,
    })
    return {
        'user_id': user_obj.pk,
        'username': user_obj.username,
        'email': user_obj.email,
        'expert_id': expert.pk if expert else None,
        'email_sent': email_sent,
    }


# ─── Ajout à une instance ───────────────────────────────────────────────────

def _ensure_expert(user_obj, *, structure_id=None, ctm_id=None, status='ACTIVE'):
    expert = _resolve_expert(user_obj)
    if expert is None:
        structure = Structure.objects.filter(pk=structure_id).first() if structure_id else None
        if structure is None:
            raise ValidationError(
                "Ce compte n'a pas de fiche expert ; fournir structure_id pour la créer."
            )
        # Créer en PENDING puis activer : le signal mobileapp envoie alors
        # l'e-mail d'acceptation à l'expert.
        expert = Expert.objects.create(
            user=user_obj, structure=structure, status='PENDING',
            ctm_id=ctm_id or None,
        )
        if status and status != 'PENDING':
            expert.status = status
            expert.save(update_fields=['status'])
        user_obj.is_expert = True
        user_obj.save(update_fields=['is_expert', 'updated_at'])
    else:
        update_fields = []
        if status and expert.status != status:
            expert.status = status
            update_fields.append('status')
        if ctm_id and expert.ctm_id != ctm_id:
            expert.ctm_id = ctm_id
            update_fields.append('ctm')
        if update_fields:
            expert.save(update_fields=update_fields)
    return expert


def _validate_role(model, role, default):
    choice = role or default
    allowed = dict(model._meta.get_field('role').choices)
    if choice not in allowed:
        raise ValidationError(
            f'Rôle invalide. Valeurs autorisées : {", ".join(sorted(allowed))}.'
        )
    return choice


@transaction.atomic
def add_user_to_organisation(
    actor, *, user_identifier, target, role=None, reference='', start_date=None,
    ctc_id=None, ctc_name=None, comite_id=None, comite_name=None,
    sc_id=None, sc_code=None, gt_id=None, gt_code=None,
    ctm_id=None, ctm_number=None, wg_id=None, wg_number=None,
    structure_id=None,
):
    """Ajouter un compte à CTC, COPIL, EXPERT, SC, GT (ou CTM/WG historique)."""
    require_neuronne_admin(actor)
    target = str(target or '').upper().strip()
    if target == 'PILOTAGE':
        target = 'COPIL'
    if target not in {'CTC', 'COPIL', 'EXPERT', 'SC', 'GT', 'CTM', 'WG'}:
        raise ValidationError('Cible attendue : CTC, COPIL, EXPERT, SC, GT, CTM ou WG.')

    user_obj = _resolve_user(user_identifier)
    expert = _ensure_expert(user_obj, structure_id=structure_id)

    if target == 'EXPERT':
        _audit_user(actor, 'APPROVE', user_obj, changes={
            'expert_id': expert.pk, 'status': expert.status,
        })
        return {
            'target': target, 'user_id': user_obj.pk, 'expert_id': expert.pk,
            'status': expert.status,
        }

    from apps.governance.models import (
        Affectation, CTCMembership, ComitePilotage, PilotageMembreship,
    )
    from apps.governance.phoenix_models import (
        AffectationSousCommission, MandatOrganisation,
    )

    today = timezone.localdate()
    if isinstance(start_date, str) and start_date:
        try:
            today = date.fromisoformat(start_date)
        except ValueError:
            raise ValidationError('start_date doit être au format AAAA-MM-JJ.')

    if target == 'CTC':
        ctc = _resolve_ctc(ctc_id=ctc_id, ctc_name=ctc_name)
        chosen_role = _validate_role(CTCMembership, role, 'EXECUTIVE')
        membership, created = CTCMembership.objects.update_or_create(
            ctc=ctc, expert=expert,
            defaults={'role': chosen_role, 'is_active': True},
        )
        _audit_user(actor, 'CREATE' if created else 'UPDATE', user_obj, changes={
            'target': 'CTC', 'target_id': ctc.pk, 'role': chosen_role,
        })
        return {
            'target': target, 'membership_id': membership.pk, 'created': created,
            'user_id': user_obj.pk, 'expert_id': expert.pk,
        }

    if target == 'COPIL':
        comite = _resolve_copil(comite_id=comite_id, comite_name=comite_name)
        chosen_role = _validate_role(PilotageMembreship, role, 'CONSEILLER')
        membership, created = PilotageMembreship.objects.update_or_create(
            comite=comite, expert=expert, defaults={'role': chosen_role},
        )
        _audit_user(actor, 'CREATE' if created else 'UPDATE', user_obj, changes={
            'target': 'COPIL', 'target_id': comite.pk, 'role': chosen_role,
        })
        return {
            'target': target, 'membership_id': membership.pk, 'created': created,
            'user_id': user_obj.pk, 'expert_id': expert.pk,
        }

    if target == 'SC':
        sc, version = _resolve_sc(sc_id=sc_id, sc_code=sc_code)
        existing = AffectationSousCommission.objects.filter(
            version=version, expert=expert, sc=sc,
            status=AffectationSousCommission.Status.MIGRATED,
        ).first()
        if existing:
            return {
                'target': target, 'assignment_id': existing.pk, 'created': False,
                'user_id': user_obj.pk, 'expert_id': expert.pk,
            }
        reference = str(reference or '').strip() or f'Neuronne {timezone.localdate():%d/%m/%Y}'
        assignment = AffectationSousCommission(
            version=version, expert=expert, sc=sc,
            source_key=f'NEURONNE-{uuid.uuid4().hex}',
            batch_reference=f'NEURONNE-{timezone.localdate():%Y%m%d}',
            source_kind='NEURONNE_ASSIGNMENT',
            status=AffectationSousCommission.Status.MIGRATED,
            is_primary=False,
            migration_reference=reference,
            source_database_sha256=hashlib.sha256(reference.encode()).hexdigest(),
            source_snapshot={'source': 'NEURONNE_ASSIGNMENT', 'reference': reference},
            effective_from=today,
            rationale='Ajout administratif demandé à Neuronne.',
        )
        assignment.full_clean()
        assignment.save()
        _audit_user(actor, 'CREATE', user_obj, changes={
            'target': 'SC', 'target_id': sc.pk, 'assignment_id': assignment.pk,
        })
        return {
            'target': target, 'assignment_id': assignment.pk, 'created': True,
            'user_id': user_obj.pk, 'expert_id': expert.pk,
        }

    if target == 'GT':
        gt, version = _resolve_gt(gt_id=gt_id, gt_code=gt_code, sc_code=sc_code)
        existing = MandatOrganisation.objects.filter(
            expert=expert, groupe=gt, status='ACTIVE', capacity='ORGANISATION',
        ).first()
        if existing:
            return {
                'target': target, 'mandate_id': existing.pk, 'created': False,
                'user_id': user_obj.pk, 'expert_id': expert.pk,
            }
        reference = str(reference or '').strip() or f'Neuronne {timezone.localdate():%d/%m/%Y}'
        mandate = MandatOrganisation(
            expert=expert, groupe=gt, function=role or 'Membre',
            capacity='ORGANISATION', appointment_reference=reference,
            start_date=today, status='ACTIVE',
        )
        mandate.full_clean()
        mandate.save()
        _audit_user(actor, 'CREATE', user_obj, changes={
            'target': 'GT', 'target_id': gt.pk, 'mandate_id': mandate.pk,
        })
        return {
            'target': target, 'mandate_id': mandate.pk, 'created': True,
            'user_id': user_obj.pk, 'expert_id': expert.pk,
        }

    if target in {'CTM', 'WG'}:
        ctm = _resolve_ctm(ctm_id=ctm_id, ctm_number=ctm_number)
        wg = _resolve_wg(wg_id=wg_id, wg_number=wg_number, ctm=ctm) if target == 'WG' else None
        affectation, created = Affectation.objects.update_or_create(
            expert=expert, ctm=ctm, wg=wg,
            defaults={'is_primary_ctm': True, 'is_primary_wg': True},
        )
        _audit_user(actor, 'CREATE' if created else 'UPDATE', user_obj, changes={
            'target': target, 'target_id': (wg or ctm).pk, 'role': role or '',
        })
        return {
            'target': target, 'affectation_id': affectation.pk, 'created': created,
            'user_id': user_obj.pk, 'expert_id': expert.pk,
        }

    raise ValidationError('Cible non prise en charge.')


# ─── Messages et diffusion ──────────────────────────────────────────────────

@transaction.atomic
def send_message_to_sc_gt(
    actor, *, subject, body, sc_id=None, gt_id=None, sc_code=None, gt_code=None,
):
    """Diffuser un message aux membres actifs d'une SC ou d'un GT."""
    require_neuronne_admin(actor)
    from apps.messaging.dispatch_services import send_dispatch

    if not sc_id and not gt_id:
        if sc_code:
            sc, _version = _resolve_sc(sc_code=sc_code)
            sc_id = sc.pk
        elif gt_code:
            gt, _version = _resolve_gt(gt_code=gt_code, sc_code=sc_code)
            gt_id = gt.pk
    dispatch, created = send_dispatch(
        actor, subject=subject, body=body, sc_id=sc_id, gt_id=gt_id,
        allow_admin=True,
    )
    AuditLog.objects.create(
        user=actor, action='CREATE', content_type='messaging.InstitutionalDispatch',
        object_id=dispatch.pk, object_repr=str(dispatch)[:200],
        changes={'target': dispatch.target_code, 'recipients': dispatch.recipients.count()},
        ip_address=None, user_agent='Neuronne IA · diffusion SC/GT',
    )
    return {
        'dispatch_id': dispatch.pk, 'created': created,
        'target': dispatch.target_code,
        'recipient_count': dispatch.recipients.count(),
    }


@transaction.atomic
def send_message_to_user(actor, *, user_identifier, subject, body):
    """Envoyer un email et une notification interne à une personne précise."""
    require_neuronne_admin(actor)
    from apps.mobileapp.models import Notification

    target_user = _resolve_user(user_identifier)
    subject = str(subject or '').strip()[:250]
    body = str(body or '').strip()
    if not subject or not body:
        raise ValidationError('Objet et message obligatoires.')

    notification = Notification.objects.create(
        user=target_user, title=subject, body=body[:4000],
        notification_type='MESSAGE', priority='NORMAL',
        data={'source': 'Neuronne', 'direct_message': True},
    )
    email_sent = False
    if target_user.email:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[target_user.email],
        )
        try:
            message.send(fail_silently=False)
            email_sent = True
        except Exception:
            email_sent = False

    AuditLog.objects.create(
        user=actor, action='CREATE', content_type='mobileapp.Notification',
        object_id=0, object_repr=subject[:200],
        changes={
            'notification_id': str(notification.pk),
            'target_user_id': target_user.pk,
            'email_sent': email_sent,
        },
        ip_address=None, user_agent='Neuronne IA · message direct',
    )
    return {
        'notification_id': str(notification.pk),
        'user_id': target_user.pk,
        'email_sent': email_sent,
    }


# ─── Rapport quotidien ──────────────────────────────────────────────────────

def _daily_actions(day):
    start = timezone.make_aware(
        datetime.combine(day, time.min), timezone.get_current_timezone(),
    )
    end = start + timedelta(days=1)
    return list(
        AuditLog.objects.filter(
            timestamp__gte=start,
            timestamp__lt=end,
            user_agent__startswith='Neuronne IA',
        ).select_related('user').order_by('timestamp')
    )


def _report_payload(day, actions):
    lines = [
        f'RAPPORT QUOTIDIEN NEURONNE — {day:%d/%m/%Y}',
        '',
        f"Nombre d'actions auditées : {len(actions)}",
        '',
    ]
    rows = []
    for entry in actions:
        when = timezone.localtime(entry.timestamp).strftime('%H:%M')
        actor = entry.user.get_full_name() if entry.user else 'Système'
        line = f"[{when}] {actor} — {entry.get_action_display()} {entry.content_type} : {entry.object_repr}"
        lines.append(line)
        rows.append({
            'when': entry.timestamp.isoformat(),
            'actor': actor,
            'action': entry.action,
            'content_type': entry.content_type,
            'object_repr': entry.object_repr,
            'changes': entry.changes,
        })
    if not actions:
        lines.append('Aucune action Neuronne enregistrée pour cette journée.')
    text = '\n'.join(lines)
    html = '<html><body><h1>Rapport quotidien Neuronne</h1>'
    html += f'<p>{day:%d/%m/%Y} — {len(actions)} action(s)</p><ul>'
    from html import escape

    for row in rows:
        html += (
            f"<li><strong>{escape(row['actor'])}</strong> — "
            f"{escape(row['action'])} {escape(row['content_type'])} : "
            f"{escape(row['object_repr'])}</li>"
        )
    html += '</ul></body></html>'
    return text, html, rows


def _report_recipients():
    from django.db.models import Q

    configured = getattr(settings, 'NEURONNE_REPORT_RECIPIENTS', '')
    if configured:
        emails = [value.strip() for value in str(configured).split(',') if value.strip()]
        return list(User.objects.filter(email__in=emails, is_active=True))
    return list(
        User.objects.filter(is_active=True, email__isnull=False)
        .exclude(email='')
        .filter(Q(is_superuser=True) | Q(groups__name=console_group_name()))
        .distinct()
        .order_by('pk')
    )


@transaction.atomic
def send_daily_report(actor=None, day=None):
    """Construire, conserver et envoyer le rapport quotidien Neuronne."""
    from apps.ia_agent.models import NeuronneDailyReport
    from apps.mobileapp.models import Notification

    day = day or timezone.localdate()
    if isinstance(day, str):
        day = date.fromisoformat(day)
    report, created = NeuronneDailyReport.objects.get_or_create(
        report_date=day,
        defaults={'text': '', 'actions': []},
    )
    if not created:
        return {
            'report_id': report.pk,
            'already_generated': True,
            'action_count': report.action_count,
            'recipient_count': report.recipient_count,
        }

    actions = _daily_actions(day)
    text, html, rows = _report_payload(day, actions)
    report.text = text
    report.html = html
    report.actions = rows
    report.action_count = len(rows)
    report.save(update_fields=['text', 'html', 'actions', 'action_count', 'updated_at'])

    recipients = _report_recipients()
    sent = 0
    for recipient in recipients:
        if not recipient.email:
            continue
        try:
            message = EmailMultiAlternatives(
                subject=f'[CNE-ITP] Rapport quotidien Neuronne — {day:%d/%m/%Y}',
                body=text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient.email],
            )
            message.attach_alternative(html, 'text/html')
            message.send(fail_silently=False)
            sent += 1
        except Exception:
            continue
        Notification.objects.create(
            user=recipient,
            title=f'Rapport quotidien Neuronne — {day:%d/%m/%Y}',
            body=(text[:350] + ('…' if len(text) > 350 else '')),
            notification_type='SYSTEM',
            priority='NORMAL',
            data={'kind': 'neuronne_daily_report', 'report_id': report.pk},
        )

    report.recipient_count = sent
    report.save(update_fields=['recipient_count', 'updated_at'])
    return {
        'report_id': report.pk,
        'already_generated': False,
        'action_count': report.action_count,
        'recipient_count': sent,
    }
