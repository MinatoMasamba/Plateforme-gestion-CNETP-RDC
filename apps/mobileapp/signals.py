"""
Signaux pour créer des notifications automatiquement à partir des événements du système
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import logging
import time

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


@receiver(post_save, sender='mobileapp.NotificationPreference', dispatch_uid='init_notification_prefs')
def init_notification_preferences(sender, instance, created, **kwargs):
    """Initialiser les préférences de notification par défaut pour un nouveau utilisateur"""
    if created:
        logger.info(f'Notification preferences created for user {instance.user.email}')


# ========== SIGNAUX POUR NORMES ==========

def notify_norm_published(sender, instance, **kwargs):
    """Notifier quand une norme est publiée"""
    if hasattr(instance, 'status') and instance.status == 'PUBLISHED':
        # Récupérer tous les experts du WG et du CTM
        try:
            from apps.governance.models import WorkingGroup, CommissionTechnique
            
            # Récupérer les experts associés
            if hasattr(instance, 'working_group'):
                experts = instance.working_group.expert_set.all()
            elif hasattr(instance, 'wg'):
                experts = instance.wg.expert_set.all()
            else:
                experts = []
            
            title = f'Norme publiée: {instance.reference_number}'
            body = f'La norme "{instance.title}" a été publiée.'
            
            for expert in experts:
                create_notification_for_user(
                    expert.user,
                    title,
                    body,
                    'NORM_PUBLISHED',
                    priority='HIGH',
                    data={
                        'norm_id': instance.id,
                        'norm_title': instance.title,
                        'ctm_id': instance.ctm_id if hasattr(instance, 'ctm_id') else None,
                    }
                )
        except Exception as e:
            logger.exception(f'Error notifying norm published: {e}')


# ========== SIGNAUX POUR PAIEMENTS ==========

def notify_payment_due(sender, instance, **kwargs):
    """Notifier quand une cotisation est due"""
    try:
        from apps.payments.models import Payment
        
        if hasattr(instance, 'status') and instance.status == 'DUE':
            expert = instance.expert if hasattr(instance, 'expert') else instance.user
            if expert:
                title = f'Cotisation due: {instance.amount}'
                body = f'Vous devez payer une cotisation de {instance.amount}. Date d\'échéance: {instance.due_date}'
                
                user = expert.user if hasattr(expert, 'user') else expert
                create_notification_for_user(
                    user,
                    title,
                    body,
                    'PAYMENT_DUE',
                    priority='HIGH',
                    data={
                        'payment_id': instance.id,
                        'amount': str(instance.amount),
                        'due_date': instance.due_date.isoformat() if hasattr(instance, 'due_date') else None,
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying payment due: {e}')


def notify_payment_received(sender, instance, **kwargs):
    """Notifier quand un paiement est reçu"""
    try:
        if hasattr(instance, 'status') and instance.status == 'PAID':
            expert = instance.expert if hasattr(instance, 'expert') else instance.user
            if expert:
                user = expert.user if hasattr(expert, 'user') else expert
                title = f'Paiement reçu: {instance.amount}'
                body = f'Votre cotisation de {instance.amount} a été reçue. Merci!'
                
                create_notification_for_user(
                    user,
                    title,
                    body,
                    'PAYMENT_RECEIVED',
                    priority='NORMAL',
                    data={
                        'payment_id': instance.id,
                        'amount': str(instance.amount),
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying payment received: {e}')


# ========== SIGNAUX POUR RÉUNIONS/MEETINGS ==========

def notify_meeting_invite(sender, instance, **kwargs):
    """Notifier quand un expert est invité à une réunion"""
    try:
        if hasattr(instance, 'status') and instance.status == 'SCHEDULED':
            # Récupérer les experts invités
            if hasattr(instance, 'participants'):
                participants = instance.participants.all()
            elif hasattr(instance, 'experts'):
                participants = instance.experts.all()
            else:
                participants = []
            
            title = f'Réunion prévue: {instance.title}'
            body = f'Vous êtes invité à la réunion "{instance.title}" le {instance.scheduled_date}'
            
            for participant in participants:
                user = participant.user if hasattr(participant, 'user') else participant
                create_notification_for_user(
                    user,
                    title,
                    body,
                    'REUNION_INVITE',
                    priority='HIGH',
                    data={
                        'meeting_id': instance.id,
                        'meeting_title': instance.title,
                        'scheduled_date': instance.scheduled_date.isoformat() if hasattr(instance, 'scheduled_date') else None,
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying meeting invite: {e}')


# ========== SIGNAUX POUR EXPERTS ==========

def notify_expert_invited(sender, instance, **kwargs):
    """Notifier quand un expert est invité à rejoindre un WG"""
    try:
        if created := kwargs.get('created'):
            # instance est une invitation ou une relation expert-wg
            expert = instance.expert if hasattr(instance, 'expert') else instance
            
            if expert and hasattr(expert, 'user'):
                title = 'Vous avez été invité à un groupe de travail'
                
                if hasattr(instance, 'working_group'):
                    wg = instance.working_group
                    body = f'Vous avez été invité à rejoindre le groupe "{wg.title}"'
                    wg_id = wg.id
                elif hasattr(instance, 'wg'):
                    wg = instance.wg
                    body = f'Vous avez été invité à rejoindre le groupe "{wg.title}"'
                    wg_id = wg.id
                else:
                    body = 'Vous avez été invité à rejoindre un groupe de travail'
                    wg_id = None
                
                create_notification_for_user(
                    expert.user,
                    title,
                    body,
                    'EXPERT_INVITE',
                    priority='HIGH',
                    data={
                        'expert_id': expert.id,
                        'wg_id': wg_id,
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying expert invited: {e}')


# ========== SIGNAUX POUR MESSAGES ==========

def notify_new_message(sender, instance, **kwargs):
    """Notifier quand un nouveau message est reçu"""
    try:
        if created := kwargs.get('created'):
            if hasattr(instance, 'recipient'):
                recipient = instance.recipient
                title = f'Nouveau message de {instance.sender.get_full_name()}'
                body = instance.body[:100] if hasattr(instance, 'body') else 'Vous avez reçu un message'
                
                create_notification_for_user(
                    recipient,
                    title,
                    body,
                    'MESSAGE',
                    priority='NORMAL',
                    data={
                        'message_id': instance.id,
                        'sender_id': instance.sender.id,
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying new message: {e}')


def notify_votes_open(sender, instance, **kwargs):
    """Notifier quand un vote est ouvert"""
    try:
        if hasattr(instance, 'status') and instance.status == 'OPEN':
            # Récupérer les votants éligibles
            if hasattr(instance, 'eligible_voters'):
                voters = instance.eligible_voters.all()
            else:
                voters = []
            
            title = f'Vote ouvert: {instance.title}'
            body = f'Un vote pour "{instance.title}" est maintenant ouvert jusqu\'au {instance.end_date}'
            
            for voter in voters:
                user = voter if isinstance(voter, type(instance._meta.get_field('eligible_voters').related_model)) else voter.user
                create_notification_for_user(
                    user,
                    title,
                    body,
                    'VOTE_OPEN',
                    priority='HIGH',
                    data={
                        'vote_id': instance.id,
                        'vote_title': instance.title,
                        'end_date': instance.end_date.isoformat() if hasattr(instance, 'end_date') else None,
                    }
                )
    except Exception as e:
        logger.exception(f'Error notifying vote open: {e}')


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


# Enregistrer les signaux (à appeler depuis apps.py)
def register_notification_signals():
    """Enregistrer tous les signaux de notification"""
    logger.info('Registering notification signals...')
    # Les signaux spécifiques aux apps seront enregistrés depuis leurs apps.py respectifs
    # Ce module fournit les fonctions d'aide
