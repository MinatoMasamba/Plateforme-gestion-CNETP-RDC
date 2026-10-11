"""
Signaux pour créer des notifications automatiquement à partir des événements du système.

Les notifications sont créées en base puis dispatchées de façon asynchrone
(email / FCM) via Celery (mode eager si aucun broker n'est configuré).
"""
import time

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from apps.mobileapp.models import Notification, NotificationPreference, ActivationToken
from apps.mobileapp.tasks import dispatch_notification

logger = logging.getLogger(__name__)


def _fire_task(task, *args):
    """Envoie la task en async ; si le broker est absent, exécution synchrone avec retry."""
    try:
        task.delay(*args)
    except Exception as exc:
        logger.warning('Broker indisponible (%s) — exécution synchrone de %s', exc.__class__.__name__, task.name)
        for attempt in range(3):
            try:
                task.apply(args=args)
                return
            except Exception as e:
                if attempt < 2:
                    wait = 10 * (attempt + 1)
                    logger.warning('Tentative synchrone %d/3 échouée pour %s: %s — retry dans %ds', attempt + 1, task.name, e, wait)
                    time.sleep(wait)
                else:
                    logger.exception('_fire_task: 3 tentatives synchrones échouées pour %s: %s', task.name, e)


def create_notification_for_user(user, title, body, notification_type, priority='NORMAL', data=None):
    """Utilitaire pour créer et dispatcher une notification"""
    try:
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            data=data or {}
        )

        # Dispatcher la notification de façon asynchrone
        _fire_task(dispatch_notification, str(notification.id))

        logger.info(f'Created notification {notification.id} for user {user.email}')
        return notification
    except Exception as e:
        logger.exception(f'Error creating notification: {e}')
        return None


def create_notification_for_users(users, title, body, notification_type, priority='NORMAL', data=None):
    """Créer une notification pour plusieurs utilisateurs"""
    for user in users:
        create_notification_for_user(user, title, body, notification_type, priority, data)


def _experts_for_ctm_or_wg(ctm_id=None, wg_id=None):
    """Experts affectés à un CTM ou un WG (via les affectations de gouvernance)."""
    from apps.experts.models import Expert

    experts = Expert.objects.select_related('user')
    if wg_id:
        return experts.filter(governance_affectations__wg_id=wg_id).distinct()
    if ctm_id:
        return experts.filter(governance_affectations__ctm_id=ctm_id).distinct()
    return experts.none()


@receiver(post_save, sender='mobileapp.NotificationPreference', dispatch_uid='init_notification_prefs')
def init_notification_preferences(sender, instance, created, **kwargs):
    """Initialiser les préférences de notification par défaut pour un nouveau utilisateur"""
    if created:
        logger.info(f'Notification preferences created for user {instance.user.email}')


# ========== NORMES ==========

@receiver(pre_save, sender='norms.Norme', dispatch_uid='track_norme_status_before_save')
def track_norme_previous_status(sender, instance, **kwargs):
    """Mémorise le statut précédent d'une norme avant sauvegarde."""
    if instance.pk:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    else:
        instance._previous_status = None


@receiver(post_save, sender='norms.Norme', dispatch_uid='notify_norm_published')
def notify_norm_published(sender, instance, created, **kwargs):
    """Notifier les experts du WG lorsque la norme passe au statut PUBLISHED."""
    previous = getattr(instance, '_previous_status', None)
    if instance.status != 'PUBLISHED' or previous == 'PUBLISHED':
        return
    try:
        for expert in _experts_for_ctm_or_wg(ctm_id=instance.ctm_id, wg_id=instance.wg_id):
            create_notification_for_user(
                expert.user,
                title=f'Norme publiée : {instance.reference_number}',
                body=f'La norme « {instance.title} » a été publiée au Journal Officiel.',
                notification_type='NORM_PUBLISHED',
                priority='HIGH',
                data={
                    'norme_id': instance.id,
                    'reference': instance.reference_number,
                    'ctm_id': instance.ctm_id,
                    'wg_id': instance.wg_id,
                },
            )
    except Exception as e:
        logger.exception(f'Error notifying norm published: {e}')


# ========== PAIEMENTS ==========

@receiver(pre_save, sender='payments.Paiement', dispatch_uid='track_paiement_status_before_save')
def track_paiement_previous_status(sender, instance, **kwargs):
    """Mémorise le statut précédent d'un paiement avant sauvegarde."""
    if instance.pk:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    else:
        instance._previous_status = None


@receiver(post_save, sender='payments.Paiement', dispatch_uid='notify_payment_received')
def notify_payment_received(sender, instance, created, **kwargs):
    """Notifier les experts de la structure lorsqu'un paiement est confirmé."""
    previous = getattr(instance, '_previous_status', None)
    if instance.status != 'CONFIRMED' or previous == 'CONFIRMED':
        return
    try:
        cotisation = instance.cotisation
        for expert in cotisation.structure.experts.select_related('user'):
            create_notification_for_user(
                expert.user,
                title=f'Paiement confirmé — cotisation {cotisation.annee}',
                body=f"Le paiement de {instance.montant} pour la cotisation {cotisation.annee} a été confirmé.",
                notification_type='PAYMENT_RECEIVED',
                priority='NORMAL',
                data={
                    'paiement_id': instance.id,
                    'cotisation_id': cotisation.id,
                    'montant': str(instance.montant),
                },
            )
    except Exception as e:
        logger.exception(f'Error notifying payment received: {e}')


# ========== RÉUNIONS ==========

@receiver(post_save, sender='meetings.Reunion', dispatch_uid='notify_reunion_created')
def notify_reunion_created(sender, instance, created, **kwargs):
    """Notifier les experts concernés lors de la création d'une réunion."""
    if not created:
        return
    try:
        for expert in _experts_for_ctm_or_wg(ctm_id=instance.ctm_id, wg_id=instance.wg_id):
            create_notification_for_user(
                expert.user,
                title=f'Réunion planifiée : {instance.titre}',
                body=f"Vous êtes invité à la réunion « {instance.titre} » le {instance.date:%d/%m/%Y %H:%M}.",
                notification_type='REUNION_INVITE',
                priority='HIGH',
                data={
                    'reunion_id': instance.id,
                    'titre': instance.titre,
                    'date': instance.date.isoformat() if instance.date else None,
                },
            )
    except Exception as e:
        logger.exception(f'Error notifying meeting: {e}')


# ========== MESSAGES ==========

@receiver(post_save, sender='messaging.Message', dispatch_uid='notify_new_message')
def notify_new_message(sender, instance, created, **kwargs):
    """Notifier le destinataire d'un nouveau message."""
    if not created or not instance.recipient_id:
        return
    try:
        author = instance.sender.get_full_name() or instance.sender.username
        create_notification_for_user(
            instance.recipient,
            title=f'Nouveau message de {author}',
            body=(instance.content or '')[:100],
            notification_type='MESSAGE',
            priority='NORMAL',
            data={'message_id': instance.id, 'sender_id': instance.sender_id},
        )
    except Exception as e:
        logger.exception(f'Error notifying new message: {e}')


# ========== SIGNAL INSCRIPTION EXPERT → NOTIFICATION LEADERS CTM ==========

@receiver(post_save, sender='experts.Expert', dispatch_uid='notify_ctm_leaders_new_expert')
def notify_ctm_leaders_on_registration(sender, instance, created, **kwargs):
    """Quand un expert s'inscrit (PENDING), notifier le Président, Rapporteur
    et Secrétaire du CTM choisi — sur mobile ET web."""
    if not created or instance.status != 'PENDING' or not instance.ctm:
        return
    try:
        ctm = instance.ctm
        leaders = [ctm.scientific_president, ctm.rapporteur, ctm.secretary]
        full_name = instance.user.get_full_name() or instance.user.email
        structure_acronym = instance.structure.acronym if instance.structure else ''
        for leader in leaders:
            if leader and leader.user_id:
                create_notification_for_user(
                    user=leader.user,
                    title=f'Nouvelle demande CTM {ctm.number}',
                    body=f'{full_name} ({structure_acronym}) demande à rejoindre votre CTM.',
                    notification_type='EXPERT_INVITE',
                    priority='HIGH',
                    data={
                        'expert_id': instance.id,
                        'ctm_id': ctm.id,
                        'ctm_number': ctm.number,
                        'expert_name': full_name,
                    },
                )
    except Exception as e:
        logger.exception(f'Erreur notification leaders CTM inscription: {e}')


# ========== SIGNAL ACCEPTATION EXPERT → EMAIL DE CONFIRMATION ==========

@receiver(pre_save, sender='experts.Expert', dispatch_uid='track_expert_status_before_save')
def track_expert_previous_status(sender, instance, **kwargs):
    """Mémorise le statut précédent de l'expert avant sauvegarde, pour permettre
    à `notify_expert_on_acceptance` de détecter un passage au statut ACTIVE."""
    if instance.pk:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    else:
        instance._previous_status = None


@receiver(post_save, sender='experts.Expert', dispatch_uid='notify_expert_on_acceptance')
def notify_expert_on_acceptance(sender, instance, created, **kwargs):
    """Quand un expert passe au statut ACTIVE (acceptation par le Président/CTM),
    que ce soit via l'admin Django ou via l'application, lui envoyer un email
    de confirmation."""
    if created:
        return
    previous_status = getattr(instance, '_previous_status', None)
    if instance.status == 'ACTIVE' and previous_status != 'ACTIVE':
        try:
            from apps.mobileapp.tasks import send_expert_acceptance_email
            _fire_task(send_expert_acceptance_email, instance.id)
        except Exception as e:
            logger.exception(f'Erreur déclenchement email acceptation expert {instance.id}: {e}')


# ========== SIGNAL TOKEN D'ACTIVATION EXPERT ==========

@receiver(post_save, sender=ActivationToken, dispatch_uid='send_expert_activation_email')
def on_activation_token_created(sender, instance, created, **kwargs):
    """Quand un token d'activation est créé pour un expert :
    1. Envoyer l'email d'invitation avec le lien de confirmation + deep link Flutter
    2. Créer une notification in-app si l'expert a déjà un compte User actif
    """
    if not created:
        return

    try:
        from apps.mobileapp.tasks import send_activation_email
        _fire_task(send_activation_email, instance.expert.id)
        logger.info(f'Task send_activation_email déclenchée pour expert {instance.expert.id}')
    except Exception as e:
        logger.exception(f'Erreur déclenchement send_activation_email: {e}')

    # Notification in-app (si l'expert a déjà un compte connecté)
    try:
        user = instance.expert.user
        if user and user.is_active:
            create_notification_for_user(
                user=user,
                title='Votre compte CNETP a été activé',
                body=(
                    'Bienvenue ! Votre invitation a été envoyée par email. '
                    'Confirmez votre adresse et activez votre compte.'
                ),
                notification_type='EXPERT_INVITE',
                priority='HIGH',
                data={
                    'expert_id': instance.expert.id,
                    'token': instance.token,
                    'expires_at': instance.expires_at.isoformat(),
                }
            )
    except Exception as e:
        logger.exception(f'Erreur notification in-app activation expert: {e}')


def register_notification_signals():
    """Les signaux sont déclarés au niveau module via @receiver.

    Cette fonction est conservée pour compatibilité (appelée depuis apps.py) et
    se contente de journaliser que l'enregistrement a bien eu lieu.
    """
    logger.info('Notification signals registered')
