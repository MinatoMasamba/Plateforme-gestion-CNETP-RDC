from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
import os
import json

from apps.mobileapp.models import Notification, NotificationLog, PushToken

logger = logging.getLogger(__name__)


# Optional: use firebase-admin if available and credentials provided
try:
    import firebase_admin
    from firebase_admin import messaging, credentials
    FIREBASE_AVAILABLE = True
except Exception:
    FIREBASE_AVAILABLE = False


def init_firebase_app():
    if not FIREBASE_AVAILABLE:
        return False
    try:
        if not firebase_admin._apps:
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH') or getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
            cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON') or getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '')
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            elif cred_json:
                cred = credentials.Certificate(json.loads(cred_json))
            else:
                # Try application default credentials
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        logger.exception('Firebase init failed: %s', e)
        return False


def send_email_notification(notification):
    """Envoyer une notification par email"""
    try:
        subject = notification.title
        user_email = notification.user.email
        
        # Template email par type
        template_name = f'mobileapp/emails/{notification.notification_type.lower()}.html'
        
        context = {
            'user': notification.user,
            'title': notification.title,
            'body': notification.body,
            'data': notification.data,
            'priority': notification.priority,
        }
        
        try:
            html_message = render_to_string(template_name, context)
        except Exception:
            # Fallback: template générique
            html_message = f"<h2>{notification.title}</h2><p>{notification.body}</p>"
        
        send_mail(
            subject,
            notification.body,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f'Email sent to {user_email} for notification {notification.id}')
        return True
    except Exception as e:
        logger.exception(f'Email send failed for notification {notification.id}: {e}')
        return False


@shared_task(bind=True, max_retries=3)
def dispatch_notification(self, notification_id):
    """Dispatcher une notification vers les tokens push actifs et par email.
    Utilise firebase-admin si configuré, sinon fallback simulé (création de NotificationLog).
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.exception(f"Notification {notification_id} introuvable")
        return False

    push_tokens = PushToken.objects.filter(user=notification.user, is_active=True)
    
    # Vérifier les préférences de l'utilisateur
    try:
        prefs = notification.user.notification_preferences
        # Map type to preference field
        pref_map = {
            'NORM_PUBLISHED': 'enable_norm_updates',
            'NORM_UPDATE': 'enable_norm_updates',
            'NORM_AMENDED': 'enable_amendments',
            'EXPERT_INVITE': 'enable_system',
            'EXPERT_ADDED_TO_WG': 'enable_system',
            'REUNION_INVITE': 'enable_reunion_invites',
            'MEETING_REMINDER': 'enable_reunion_invites',
            'VOTE_OPEN': 'enable_votes',
            'VOTE_REMINDER': 'enable_votes',
            'AMENDMENT': 'enable_amendments',
            'PAYMENT_DUE': 'enable_payments',
            'PAYMENT_RECEIVED': 'enable_payments',
            'PAYMENT_OVERDUE': 'enable_payments',
            'MESSAGE': True,
            'JETON': 'enable_system',
            'SYSTEM': 'enable_system',
        }
        
        pref_field = pref_map.get(notification.notification_type, True)
        if pref_field is not True and not getattr(prefs, pref_field, True):
            logger.info(f'Notification {notification.id} skipped due to user preferences')
            return True
        
        # Check quiet hours
        if prefs.quiet_hours_enabled:
            current_time = timezone.now().time()
            start = prefs.quiet_hours_start
            end = prefs.quiet_hours_end
            
            if start and end:
                if start < end:
                    in_quiet_hours = start <= current_time < end
                else:
                    in_quiet_hours = current_time >= start or current_time < end
                
                # Only skip LOW priority notifications during quiet hours
                if in_quiet_hours and notification.priority == 'LOW':
                    logger.info(f'Notification {notification.id} deferred due to quiet hours')
                    return True
    except Exception as e:
        logger.warning(f'Could not check notification preferences: {e}')

    # Init firebase if available
    firebase_ready = init_firebase_app() if FIREBASE_AVAILABLE else False
    fcm_enabled = getattr(settings, 'NOTIFICATION_SETTINGS', {}).get('FCM_ENABLED', True)

    if firebase_ready and fcm_enabled and push_tokens.exists():
        for token in push_tokens:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.body
                ),
                token=token.token,
                data={
                    'notification_id': str(notification.id),
                    'type': notification.notification_type,
                    'priority': notification.priority,
                    **(notification.data or {})
                },
                android=messaging.AndroidConfig(
                    priority='high' if notification.priority in ('HIGH', 'URGENT') else 'normal',
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': '10' if notification.priority in ('HIGH', 'URGENT') else '5'},
                ),
            )
            try:
                resp = messaging.send(message)
                NotificationLog.objects.create(
                    notification=notification,
                    push_token=token,
                    status='SENT',
                    provider='FCM',
                    provider_response={'message_id': resp},
                    sent_at=timezone.now()
                )
                logger.info(f'FCM sent to token {token.id} (msg id: {resp})')
            except Exception as e:
                NotificationLog.objects.create(
                    notification=notification,
                    push_token=token,
                    status='FAILED',
                    provider='FCM',
                    provider_response={'error': str(e)},
                    error_message=str(e),
                    sent_at=timezone.now()
                )
                logger.exception(f'FCM send failed for token {token.id}: {e}')
    elif not firebase_ready and push_tokens.exists():
        # Fallback: simulate and log
        for token in push_tokens:
            NotificationLog.objects.create(
                notification=notification,
                push_token=token,
                status='SENT',
                provider='SIMULATED',
                provider_response={'detail': 'simulated send'},
                sent_at=timezone.now()
            )
            logger.info(f"Simulated send to token {token.id} for notification {notification.id}")

    # Send email if enabled
    email_enabled = getattr(settings, 'NOTIFICATION_SETTINGS', {}).get('EMAIL_ENABLED', True)
    if email_enabled:
        send_email_notification(notification)

    return True


@shared_task
def send_notification_digest(user_id):
    """Envoyer un digest de notifications (quotidien/hebdomadaire)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f'User {user_id} not found for digest')
        return False
    
    # Récupérer les notifications non lues récentes
    if hasattr(user, 'notification_preferences'):
        prefs = user.notification_preferences
        if prefs.digest_enabled:
            from datetime import timedelta
            hours_back = 24 if prefs.digest_frequency == 'DAILY' else 168
            since = timezone.now() - timedelta(hours=hours_back)
            
            notifications = Notification.objects.filter(
                user=user,
                created_at__gte=since
            ).order_by('-created_at')[:10]
            
            if notifications:
                subject = f'Digest de notifications - {prefs.digest_frequency.lower()}'
                context = {
                    'user': user,
                    'notifications': notifications,
                    'frequency': prefs.digest_frequency,
                }
                try:
                    html_message = render_to_string('mobileapp/emails/digest.html', context)
                except Exception:
                    html_message = '<p>Vous avez de nouvelles notifications</p>'
                
                send_mail(
                    subject,
                    'Vous avez de nouvelles notifications',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False
                )
                logger.info(f'Digest sent to {user.email}')
    
    return True
