"""Journalisation des actions de la console."""
import ipaddress
import json
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils import timezone

from apps.core.models import AuditLog

ACTION_FLAGS = {
    'CREATE': ADDITION,
    'UPDATE': CHANGE,
    'DELETE': DELETION,
}
AUDIT_ACTIONS = {
    'CREATE': 'CREATE',
    'UPDATE': 'UPDATE',
    'DELETE': 'DELETE',
}


def _json_value(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, FieldFile):
        return value.name or ''
    if isinstance(value, models.Model):
        return str(value.pk)
    return value


SENSITIVE_FIELDS = {'password', 'code', 'token', 'secret'}


def snapshot(instance):
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in {'created_at', 'updated_at'} or field.name in SENSITIVE_FIELDS:
            continue
        try:
            value = getattr(instance, field.attname)
        except Exception:
            continue
        data[field.name] = _json_value(value)
    return data


def build_changes(old, new):
    changes = {}
    for key in sorted(set(old) | set(new)):
        before = old.get(key)
        after = new.get(key)
        if before != after:
            changes[key] = {'old': before, 'new': after}
    return changes


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    value = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    try:
        return str(ipaddress.ip_address(value)) if value else None
    except ValueError:
        return None


def record_admin_action(
    request,
    action,
    instance,
    message='',
    old_snapshot=None,
    object_repr=None,
):
    model = instance._meta.model
    content_type = ContentType.objects.get_for_model(model)
    pk = instance.pk
    object_repr = (object_repr or str(instance))[:200]
    flag = ACTION_FLAGS[action]

    LogEntry.objects.create(
        user_id=request.user.pk,
        content_type_id=content_type.pk,
        object_id=str(pk),
        object_repr=object_repr,
        action_flag=flag,
        change_message=message or action,
    )

    if type(pk) is not int:
        return
    if model._meta.label_lower in {'core.auditlog', 'core.audittextchange'}:
        return

    if action == 'CREATE':
        changes = build_changes({}, snapshot(instance))
    elif action == 'DELETE':
        changes = build_changes(old_snapshot or snapshot(instance), {})
    else:
        changes = build_changes(old_snapshot or {}, snapshot(instance))
    AuditLog.objects.create(
        user=request.user,
        action=AUDIT_ACTIONS[action],
        content_type=model._meta.label,
        object_id=pk,
        object_repr=object_repr,
        changes=changes,
        ip_address=client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:2000],
    )


def record_user_action(request, action, user, message='', old_snapshot=None):
    LogEntry.objects.create(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(user._meta.model).pk,
        object_id=str(user.pk),
        object_repr=str(user)[:200],
        action_flag=ACTION_FLAGS[action],
        change_message=message or action,
    )
    if action == 'CREATE':
        changes = build_changes({}, snapshot(user))
    elif action == 'DELETE':
        changes = build_changes(old_snapshot or snapshot(user), {})
    else:
        changes = build_changes(old_snapshot or {}, snapshot(user))
    AuditLog.objects.create(
        user=request.user,
        action=AUDIT_ACTIONS[action],
        content_type=user._meta.label,
        object_id=user.pk,
        object_repr=str(user)[:200],
        changes=changes,
        ip_address=client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:2000],
    )


def audit_changes_text(changes):
    if not changes:
        return ''
    return json.dumps(changes, ensure_ascii=False, default=str)


def recent_activity(limit=8):
    entries = []
    for log in LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:limit]:
        entries.append({
            'kind': 'admin',
            'when': log.action_time,
            'user': log.user,
            'label': log.object_repr,
            'action': log.get_action_flag_display(),
            'url': None,
        })
    for log in AuditLog.objects.select_related('user').order_by('-timestamp')[:limit]:
        entries.append({
            'kind': 'business',
            'when': log.timestamp,
            'user': log.user,
            'label': log.object_repr,
            'action': log.get_action_display(),
            'url': None,
        })
    entries.sort(key=lambda item: item['when'] or timezone.now(), reverse=True)
    return entries[:limit]
