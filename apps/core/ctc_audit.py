"""Journal des modifications CTC réalisées pendant une requête authentifiée."""
from contextvars import ContextVar
from hashlib import sha256
from ipaddress import ip_address
from pathlib import PurePosixPath
from uuid import uuid4

from django.apps import apps
from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete

_request_context = ContextVar('ctc_audit_request', default=None)


def current_audit_request():
    context = _request_context.get()
    return context[0] if context else None

TRACKED_MODELS = (
    'governance.CTCProcessus', 'governance.CTCOperationalRequest',
    'validation.ISOReview', 'validation.EcologicalReview',
    'validation.EconomicReview', 'validation.LegisticReview',
    'validation.ScheduleReview', 'validation.IndustrialConsultation',
    'norms.Norme', 'norms.NormeVersion', 'norms.NormeComment',
    'norms.NormeDocumentImport', 'documents.DocumentFile',
)
IGNORED_FIELDS = {'id', 'created_at', 'updated_at', 'created_by', 'updated_by'}
TEXT_FIELDS = {'content', 'body', 'comments', 'planner_notes', 'scientist_notes',
               'harmonization_notes', 'fec_feedback', 'summary', 'description'}


class CTCAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request_context.set((request, uuid4().hex))
        try:
            return self.get_response(request)
        finally:
            _request_context.reset(token)


def _context(instance):
    context = _request_context.get()
    if not context:
        return None
    request, request_id = context
    user = request.user
    if not user.is_authenticated:
        return None
    norme = instance if instance._meta.label == 'norms.Norme' else getattr(instance, 'norme', None)
    if norme and norme.circuit_version != 'LEGACY':
        return None
    intrinsic = instance._meta.label.startswith('governance.CTC')
    has_process = norme and apps.get_model('governance', 'CTCProcessus').objects.filter(norme_id=norme.pk).exists()
    membership = apps.get_model('governance', 'CTCMembership').objects.filter(
        expert__user_id=user.pk,
    ).select_related('expert__structure').first()
    ctc_actor = membership is not None
    if not (intrinsic or has_process or ctc_actor or norme or request.path.startswith('/ctc/')):
        return None
    try:
        address = str(ip_address(request.META.get('REMOTE_ADDR', '')))
    except ValueError:
        address = None
    channel = 'CTC' if request.path.startswith('/ctc/') else (
        'API' if request.path.startswith('/api/') else (
            'Administration' if request.path.startswith('/admin/') else 'Plateforme'
        )
    )
    document = getattr(instance, 'document', None) or getattr(instance, 'file', None)
    metadata = {
        'scope': 'ctc' if intrinsic or has_process or ctc_actor or request.path.startswith('/ctc/') else 'ctm',
        'request_id': request_id,
        'path': request.path, 'channel': channel,
        'norme_id': norme.pk if norme else None,
        'reference': norme.reference_number if norme else '',
        'ctm_number': norme.ctm.number if norme else None,
        'title': getattr(instance, 'title', '') or (norme.title if norme else str(instance)),
        'document': PurePosixPath(str(document)).name if document else '',
        'model_label': str(instance._meta.verbose_name),
        'summary': str(getattr(instance, 'summary', '') or '')[:1000],
        'actor_structure': membership.expert.structure.name if membership else '',
        'actor_role': membership.get_role_display() if membership else '',
        'version_id': instance.pk if instance._meta.label == 'norms.NormeVersion' else None,
    }
    return request, metadata, address


def _value(field, value):
    if value is None:
        return None
    # Le journal décrit l'édition sans recopier le contenu des documents et notes.
    if isinstance(field, (models.TextField, models.JSONField)):
        text = str(value)
        return {'length': len(text), 'sha256': sha256(text.encode()).hexdigest()}
    return str(value)[:250]


def _snapshot(instance):
    return {
        field.name: _value(field, getattr(instance, field.attname))
        for field in instance._meta.concrete_fields
        if field.name not in IGNORED_FIELDS
    }


def _before_save(sender, instance, raw=False, using='default', **kwargs):
    if raw:
        return
    context = _context(instance)
    instance._ctc_audit_context = context
    if context:
        previous = sender.objects.using(using).filter(pk=instance.pk).first() if instance.pk else None
        instance._ctc_audit_before = _snapshot(previous) if previous else {}
        instance._ctc_audit_text_before = {
            field.name: str(getattr(previous, field.name) or '') if previous else ''
            for field in instance._meta.concrete_fields
            if field.name in TEXT_FIELDS and isinstance(field, models.TextField)
        }


def _write(instance, action, fields, using):
    request, metadata, address = instance._ctc_audit_context
    metadata['fields'] = fields
    if instance._meta.label == 'norms.NormeVersion':
        metadata['version_id'] = instance.pk
    log = apps.get_model('core', 'AuditLog').objects.using(using).create(
        user=request.user, action=action,
        content_type=instance._meta.label,
        object_id=instance.pk,
        object_repr=str(instance)[:200], changes=metadata,
        ip_address=address, user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )
    for name, old_text in getattr(instance, '_ctc_audit_text_before', {}).items():
        if name in fields:
            apps.get_model('core', 'AuditTextChange').objects.using(using).create(
                audit_log=log, field_name=name, old_text=old_text,
                new_text=str(getattr(instance, name) or ''),
            )


def _after_save(sender, instance, created, raw=False, update_fields=None, using='default', **kwargs):
    if raw or not getattr(instance, '_ctc_audit_context', None):
        return
    before = getattr(instance, '_ctc_audit_before', {})
    after = _snapshot(instance)
    fields = {
        name: {'before': before.get(name), 'after': value,
               'label': str(sender._meta.get_field(name).verbose_name)}
        for name, value in after.items()
        if (created or before.get(name) != value)
        and (update_fields is None or name in update_fields or sender._meta.get_field(name).attname in update_fields)
    }
    if not fields:
        return
    action = 'CREATE' if created else 'UPDATE'
    statuses = [change['after'] for name, change in fields.items() if name.endswith('status') or name == 'status']
    if not created and 'REJECTED' in statuses:
        action = 'REJECT'
    elif not created and 'APPROVED' in statuses:
        action = 'APPROVE'
    elif not created and fields.get('status', {}).get('after') == 'PUBLISHED':
        action = 'PUBLISH'
    _write(instance, action, fields, using)


def _before_delete(sender, instance, using='default', **kwargs):
    instance._ctc_audit_context = _context(instance)


def _after_delete(sender, instance, using='default', **kwargs):
    if getattr(instance, '_ctc_audit_context', None):
        _write(instance, 'DELETE', {}, using)


def register_signals():
    for label in TRACKED_MODELS:
        model = apps.get_model(label)
        for signal, receiver in (
            (pre_save, _before_save), (post_save, _after_save),
            (pre_delete, _before_delete), (post_delete, _after_delete),
        ):
            signal.connect(receiver, sender=model, weak=False,
                           dispatch_uid=f'ctc_audit.{label}.{receiver.__name__}')
