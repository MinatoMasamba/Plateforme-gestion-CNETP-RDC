import logging
import re

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.mobileapp.diagnostics import redact, write_diagnostic
from apps.mobileapp.models import ClientDiagnostic

logger = logging.getLogger(__name__)


class DiagnosticThrottle(UserRateThrottle):
    rate = '20/minute'
    scope = 'client_diagnostic'


class DiagnosticDailyThrottle(UserRateThrottle):
    rate = '100/day'
    scope = 'client_diagnostic_daily'


class DiagnosticSerializer(serializers.Serializer):
    event_id = serializers.RegexField(r'^[a-zA-Z0-9_-]{8,64}$')
    category = serializers.ChoiceField(choices=['flutter', 'network', 'slow_request'])
    app_version = serializers.CharField(max_length=64)
    platform = serializers.CharField(max_length=20)
    message = serializers.CharField(max_length=2000)
    stack = serializers.CharField(max_length=12000, required=False, allow_blank=True)
    path = serializers.CharField(max_length=240, required=False, allow_blank=True)
    method = serializers.ChoiceField(choices=['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'], required=False)
    route = serializers.ChoiceField(choices=['direct', 'relay', 'localProxy'], required=False)
    duration_ms = serializers.IntegerField(min_value=0, max_value=3600000, required=False)
    status_code = serializers.IntegerField(min_value=100, max_value=599, required=False)

    def validate_path(self, value):
        # Ne conserver ni paramètres, ni IDs, ni nom de document/utilisateur.
        if not value.startswith('/api/'):
            return ''
        segments = value.split('?')[0].split('/')
        return '/'.join(segment if not segment or re.fullmatch(r'[a-z_-]+|v[12]', segment) else ':id' for segment in segments)


class ClientDiagnosticView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [DiagnosticThrottle, DiagnosticDailyThrottle]

    def post(self, request):
        # L'authentification/CSRF peut avoir déjà consommé le flux DRF.
        # Ne pas relire request.body après request.data.
        try:
            content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        except (TypeError, ValueError):
            return Response({'detail': 'Taille du diagnostic invalide.'}, status=400)
        if content_length > 20000:
            return Response({'detail': 'Diagnostic trop volumineux.'}, status=413)
        data = DiagnosticSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        event_id = values.pop('event_id')
        category = values.pop('category')
        version = values.pop('app_version')
        platform = values.pop('platform')
        message = redact(values.pop('message'))
        details = {key: redact(value) if isinstance(value, str) else value for key, value in values.items()}
        with transaction.atomic():
            incident, created = ClientDiagnostic.objects.get_or_create(
                user=request.user, event_id=event_id,
                defaults={'category': category, 'app_version': redact(version),
                          'platform': redact(platform), 'message': message, 'details': details},
            )
        with transaction.atomic():
            incident = ClientDiagnostic.objects.select_for_update().get(pk=incident.pk)
            if not incident.journal_written:
                try:
                    write_diagnostic(incident)
                except OSError:
                    logger.exception('Écriture du journal diagnostic impossible, incident %s', incident.pk)
                    return Response({'detail': 'Journal temporairement indisponible.'}, status=503)
                incident.journal_written = True
                incident.save(update_fields=['journal_written'])
        return Response({'id': str(incident.pk)}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
