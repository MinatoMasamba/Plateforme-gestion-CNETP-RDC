from django.db import transaction
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from api.v1.meetings.views import ReunionViewSet
from api.v1.norms.views import NormeViewSet
from apps.norms.models import ExpertResource


class MobileExpertActivityViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def heartbeat(self, request):
        from apps.governance.activity_supervision import record_heartbeat
        from apps.experts.models import Expert
        if not Expert.objects.filter(user=request.user, status='ACTIVE').exists():
            return Response({'detail': 'Profil expert actif requis.'}, status=403)
        try:
            with transaction.atomic():
                session, credited = record_heartbeat(
                    user=request.user, device_id=str(request.data.get('device_id', '')),
                    visible=request.data.get('visible') is True,
                    interacted=request.data.get('interacted') is True,
                    current_path='/expert', norme_id=request.data.get('norme_id'),
                )
        except (ValueError, TypeError) as exc:
            return Response({'detail': str(exc)}, status=400)
        return Response({'session': str(session.pk), 'credited_seconds': credited, 'server_time': timezone.now().isoformat()})


class MobileExpertMeetingsViewSet(ReunionViewSet):
    """Contrat mobile, mêmes contrôles et actions que le circuit existant."""


class ResourceDataSerializer(serializers.Serializer):
    drive = serializers.URLField(allow_blank=True, required=False)
    meet = serializers.URLField(allow_blank=True, required=False)
    references = serializers.ListField(child=serializers.DictField(), max_length=100, required=False)

    def validate_references(self, values):
        for value in values:
            serializers.URLField().run_validation(value.get('url'))
            if not str(value.get('title', '')).strip():
                raise serializers.ValidationError('Titre obligatoire.')
        return values


class MobileExpertResourcesViewSet(NormeViewSet):
    http_method_names = ['get', 'put', 'head', 'options']

    @action(detail=True, methods=['get', 'put'])
    def resources(self, request, pk=None):
        norme = self.get_object()
        if request.method == 'GET':
            resource = ExpertResource.objects.filter(user=request.user, norme=norme).first()
            return Response({'revision': resource.revision if resource else 0, 'data': resource.data if resource else {}})
        validator = ResourceDataSerializer(data=request.data.get('data', {}))
        validator.is_valid(raise_exception=True)
        with transaction.atomic():
            # Sérialiser aussi la première création pour ce document.
            type(norme).objects.select_for_update().get(pk=norme.pk)
            resource, _ = ExpertResource.objects.get_or_create(user=request.user, norme=norme)
            if request.data.get('revision') != resource.revision:
                return Response({'detail': 'Les ressources ont changé sur un autre appareil. Rechargez avant de réessayer.'}, status=status.HTTP_409_CONFLICT)
            resource.data = validator.validated_data
            resource.revision += 1
            resource.save()
        return Response({'revision': resource.revision, 'data': resource.data})
