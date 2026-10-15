"""Actions réelles des paramètres CTC, limitées aux services disponibles."""

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.models import AuditLog
from apps.experts.models import Expert
from apps.mobileapp.models import NotificationPreference
from apps.governance.phoenix_backup import prepare_backup
from apps.documents.models import DriveSyncSettings
from apps.documents.drive_sync import candidate_count, configured, sync_backlog
from apps.documents.tasks import sync_drive_backlog
from .ctc_views import get_ctc_context


def _membership_context(request):
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    return get_ctc_context(expert) if expert else None


def _audit(request, key, before, after):
    AuditLog.objects.create(
        user=request.user, action='UPDATE', content_type='CTCSettings',
        object_id=request.user.pk, object_repr=key,
        changes={'before': before, 'after': after},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
    )


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCNotificationSettingsView(View):
    """Modifie les préférences effectivement lues par le dispatch de notifications."""

    fields = {
        'enable_system', 'enable_norm_updates', 'enable_reunion_invites',
        'enable_votes', 'enable_amendments', 'enable_payments',
    }

    def post(self, request):
        if _membership_context(request) is None:
            return JsonResponse({'ok': False, 'error': 'Accès CTC requis.'}, status=403)
        try:
            payload = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'ok': False, 'error': 'Données invalides.'}, status=400)
        key, value = payload.get('key'), payload.get('enabled')
        if key not in self.fields or type(value) is not bool:
            return JsonResponse({'ok': False, 'error': 'Réglage invalide.'}, status=400)
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
        old = getattr(preference, key)
        if old != value:
            setattr(preference, key, value)
            preference.save(update_fields=[key, 'updated_at'])
            _audit(request, key, old, value)
        return JsonResponse({'ok': True, 'enabled': value})


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCBackupView(View):
    """Lance une vraie copie locale vérifiée, seulement pour le poste IT CTC."""

    def post(self, request):
        context = _membership_context(request)
        if context is None or not context.get('can_admin_system'):
            return JsonResponse({'ok': False, 'error': 'Poste IT CTC requis.'}, status=403)
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
            return JsonResponse({'ok': False, 'error': 'Sauvegarde PostgreSQL non configurée.'}, status=503)
        try:
            destination = prepare_backup()
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Échec de la sauvegarde ou de sa vérification.'}, status=500)
        _audit(request, 'backup', None, {'location': str(destination), 'restore_verified': True})
        return JsonResponse({'ok': True, 'message': 'Sauvegarde créée et restauration vérifiée.'})


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCDriveSettingsView(View):
    """Active le transfert des normes validées vers le dossier CNE-ITP dédié."""

    def post(self, request):
        context = _membership_context(request)
        if context is None or not context.get('can_admin_system'):
            return JsonResponse({'ok': False, 'error': 'Poste IT CTC requis.'}, status=403)
        try:
            payload = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'ok': False, 'error': 'Données invalides.'}, status=400)
        value = payload.get('enabled')
        if type(value) is not bool:
            return JsonResponse({'ok': False, 'error': 'Réglage invalide.'}, status=400)
        if value and not configured():
            return JsonResponse({'ok': False, 'error': 'Compte ou dossier Drive non configuré.'}, status=503)
        config, _ = DriveSyncSettings.objects.get_or_create(pk=1, defaults={'include_adopted': True})
        old = config.enabled
        if old != value:
            config.enabled = value
            config.updated_by = request.user
            config.save(update_fields=['enabled', 'updated_by', 'updated_at'])
            _audit(request, 'drive_sync', old, value)
            if value:
                try:
                    sync_drive_backlog.delay()
                except Exception:
                    sync_backlog()
        return JsonResponse({'ok': True, 'enabled': value, 'eligible_files': candidate_count()})
