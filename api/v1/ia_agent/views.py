from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ia_agent.models import AgentArtifact, AgentSession
from apps.ia_agent.services.agent_runner import AgentRunner
from apps.ia_agent.services.permissions import user_can_access_scope
from apps.ia_agent.services.regulatory_advice import generate_regulatory_advice

from .serializers import AgentArtifactSerializer, AgentMessageSerializer, AgentSessionSerializer


class AgentSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AgentSessionSerializer

    def get_queryset(self):
        return AgentSession.objects.filter(user=self.request.user).order_by('-updated_at')

    def create(self, request, *args, **kwargs):
        scope = request.data.get('scope')
        if not user_can_access_scope(request.user, scope):
            return Response(
                {"error": "Accès non autorisé à ce contexte de l'agent IA."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        session = self.get_object()
        msgs = session.messages.exclude(role='tool').order_by('created_at')
        return Response(AgentMessageSerializer(msgs, many=True).data)

    @action(detail=True, methods=['post'])
    def init(self, request, pk=None):
        session = self.get_object()
        if session.messages.filter(role__in=['user', 'assistant']).exists():
            return Response({"detail": "Session déjà initialisée."}, status=status.HTTP_200_OK)
        started_at = timezone.now()
        msg = AgentRunner(session).run_greeting()
        if msg is None:
            return Response({"detail": "Greeting non disponible."}, status=status.HTTP_200_OK)
        session.save(update_fields=['updated_at'])
        new_artifacts = AgentArtifact.objects.filter(session=session, created_at__gte=started_at)
        session.refresh_from_db(fields=['title'])
        return Response({
            "assistant_message": AgentMessageSerializer(msg).data,
            "artifacts": AgentArtifactSerializer(new_artifacts, many=True).data,
            "session_title": session.title,
        })

    @action(detail=False, methods=['post'], url_path='regulatory-advice')
    def regulatory_advice(self, request):
        text = (request.data.get('text') or '').strip()
        if not text:
            return Response(
                {"error": "Aucun texte n’a été fourni pour l’analyse réglementaire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = generate_regulatory_advice(text)
        if not result.get('success'):
            return Response(
                {"error": result.get('error', 'Erreur IA.')},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'explanation': result['explanation'],
            'proposal': result['proposal'],
            'raw': result['raw'],
            'provider': result['provider'],
        })

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        session = self.get_object()
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({"error": "Message vide."}, status=status.HTTP_400_BAD_REQUEST)

        started_at = timezone.now()
        assistant_message = AgentRunner(session).run_turn(content)
        session.refresh_from_db(fields=['title', 'updated_at'])
        session.save(update_fields=['updated_at'])

        new_artifacts = AgentArtifact.objects.filter(session=session, created_at__gte=started_at)

        return Response({
            "assistant_message": AgentMessageSerializer(assistant_message).data,
            "artifacts": AgentArtifactSerializer(new_artifacts, many=True).data,
            "session_title": session.title,
        })


class AgentArtifactViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentArtifactSerializer

    def get_queryset(self):
        return AgentArtifact.objects.filter(session__user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        artifact = self.get_object()
        if artifact.status != 'DRAFT':
            return Response(
                {"error": "Seuls les brouillons peuvent être approuvés."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        artifact.status = 'APPROVED'
        artifact.save(update_fields=['status', 'updated_at'])
        return Response(AgentArtifactSerializer(artifact).data)

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        artifact = self.get_object()
        if artifact.artifact_type != 'WG_REQUEST':
            return Response(
                {"error": "Téléchargement PDF non disponible pour ce type d'artefact."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.ia_agent.services.pdf_artifacts import generate_wg_request_pdf_from_artifact

        pdf_bytes = generate_wg_request_pdf_from_artifact(artifact)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="demande_wg_{artifact.id}.pdf"'
        return response

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        artifact = self.get_object()
        if artifact.artifact_type != 'EMAIL_DRAFT':
            return Response(
                {"error": "Action 'send' réservée aux brouillons d'email."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if artifact.status == 'SENT':
            return Response({"error": "Cet email a déjà été envoyé."}, status=status.HTTP_400_BAD_REQUEST)

        payload = dict(artifact.payload)
        to_email = request.data.get('to', payload.get('to'))
        subject = request.data.get('subject', payload.get('subject'))
        body = request.data.get('body', payload.get('body'))

        try:
            validate_email(to_email or "")
        except ValidationError:
            return Response({"error": "Adresse email invalide."}, status=status.HTTP_400_BAD_REQUEST)

        payload.update({"to": to_email, "subject": subject, "body": body})
        artifact.payload = payload
        artifact.status = 'APPROVED'
        artifact.save(update_fields=['payload', 'status', 'updated_at'])

        from apps.ia_agent.tasks import send_artifact_email

        send_artifact_email.delay(artifact.id, request.user.id)

        return Response(AgentArtifactSerializer(artifact).data)
