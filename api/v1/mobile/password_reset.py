"""Code-based recovery for the public Flutter authentication screens."""
import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response

from apps.core.models import PasswordResetCode

logger = logging.getLogger(__name__)


class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetConfirmSerializer(ResetRequestSerializer):
    code = serializers.RegexField(r'^\d{6}$')
    password = serializers.CharField(min_length=8, trim_whitespace=False)
    password2 = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('Les mots de passe ne correspondent pas.')
        return attrs


def request_reset(data):
    form = ResetRequestSerializer(data=data)
    form.is_valid(raise_exception=True)
    user = get_user_model().objects.filter(email__iexact=form.validated_data['email']).first()
    if user is None:
        return Response({'ok': True})
    with transaction.atomic():
        # Serialize issuance and consumption for this account.
        user = get_user_model().objects.select_for_update().get(pk=user.pk)
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)
        reset = PasswordResetCode.objects.create(
            user=user,
            code=f'{secrets.randbelow(1_000_000):06d}',
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
    try:
        send_mail(
            '[CNETP] Code de réinitialisation de mot de passe',
            f'Votre code : {reset.code} (valable 15 min)',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception:
        PasswordResetCode.objects.filter(pk=reset.pk).update(is_used=True)
        logger.exception('Password reset email delivery failed for user %s', user.pk)
        return Response({'error': "Impossible d'envoyer l'email. Réessayez."}, status=503)
    return Response({'ok': True})


@transaction.atomic
def confirm_reset(data):
    form = ResetConfirmSerializer(data=data)
    form.is_valid(raise_exception=True)
    values = form.validated_data
    user = get_user_model().objects.select_for_update().filter(email__iexact=values['email']).first()
    reset = (
        PasswordResetCode.objects.select_for_update().filter(user=user, is_used=False)
        .order_by('-created_at', '-pk').first()
        if user else None
    )
    if not reset or not reset.is_valid:
        return Response({'error': 'Code invalide ou expiré.'}, status=400)
    if not secrets.compare_digest(reset.code, values['code']):
        reset.attempts += 1
        reset.save(update_fields=['attempts'])
        return Response({'error': 'Code incorrect.'}, status=400)
    user.set_password(values['password'])
    user.save(update_fields=['password'])
    reset.is_used = True
    reset.save(update_fields=['is_used'])
    return Response({'ok': True})
