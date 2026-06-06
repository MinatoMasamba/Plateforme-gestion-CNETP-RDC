from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .serializers import MessageSerializer
from apps.messaging.models import Message
from apps.experts.models import Expert
from ..permissions import IsMemberOfAnySharedCTM
from ..experts.serializers import ExpertBasicSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberOfAnySharedCTM]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'expert_profile'):
            return Message.objects.none()

        queryset = Message.objects.filter(Q(sender=user) | Q(recipient=user))

        reunion_id = self.request.query_params.get('reunion_id')
        if reunion_id:
            queryset = queryset.filter(reunion_id=reunion_id)

        participant_id = self.request.query_params.get('participant_id')
        if participant_id:
            queryset = queryset.filter(
                Q(sender_id=participant_id, recipient=user) |
                Q(sender=user, recipient_id=participant_id)
            )

        return queryset.order_by('timestamp')

    @staticmethod
    def _expert_ctm_ids(expert):
        ids = set()
        if getattr(expert, 'ctm_id', None):
            ids.add(expert.ctm_id)
        ids.update(
            expert.governance_affectations
            .filter(ctm__isnull=False)
            .values_list('ctm_id', flat=True)
        )
        return ids

    def perform_create(self, serializer):
        sender = self.request.user

        if not hasattr(sender, 'expert_profile'):
            raise permissions.PermissionDenied("Seuls les experts peuvent envoyer des messages.")

        recipient = serializer.validated_data.get('recipient')
        if recipient:
            if not hasattr(recipient, 'expert_profile'):
                raise permissions.PermissionDenied("Le destinataire doit être un expert.")

            sender_ctm_ids = self._expert_ctm_ids(sender.expert_profile)
            recipient_ctm_ids = self._expert_ctm_ids(recipient.expert_profile)

            if not sender_ctm_ids.intersection(recipient_ctm_ids):
                raise permissions.PermissionDenied("L'expéditeur et le destinataire doivent appartenir au même CTM.")

        message = serializer.save(sender=sender)

        if recipient:
            try:
                from apps.mobileapp.models import Notification
                Notification.objects.create(
                    user=recipient,
                    title="Nouveau message",
                    body=f"{sender.get_full_name() or sender.username}: {message.content[:120]}",
                    notification_type="MESSAGE",
                    priority="NORMAL",
                    data={"message_id": message.id, "sender_id": sender.id}
                )
            except Exception:
                pass

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def contacts(self, request):
        """Liste les experts appartenant au même CTM que l'utilisateur actuel."""
        user = request.user
        if not hasattr(user, 'expert_profile'):
            return Response([], status=status.HTTP_200_OK)

        current_ctm_ids = self._expert_ctm_ids(user.expert_profile)
        if not current_ctm_ids:
            return Response([], status=status.HTTP_200_OK)

        shared_ctm_experts = Expert.objects.filter(
            Q(ctm_id__in=current_ctm_ids) |
            Q(governance_affectations__ctm_id__in=current_ctm_ids)
        ).exclude(user=user).distinct()

        serializer = ExpertBasicSerializer(shared_ctm_experts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def unread_count(self, request):
        """Nombre exact de messages directs non lus."""
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_conversation_as_read(self, request):
        """Marquer comme lus les messages reçus d'un participant."""
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return Response({'participant_id': 'Ce champ est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        updated = Message.objects.filter(
            sender_id=participant_id,
            recipient=request.user,
            is_read=False
        ).update(is_read=True, updated_at=timezone.now())
        return Response({'marked_read': updated})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMemberOfAnySharedCTM])
    def mark_as_read(self, request, pk=None):
        """Marque un message comme lu."""
        try:
            message = self.get_queryset().get(pk=pk, recipient=request.user)
            message.is_read = True
            message.save()
            return Response({'status': 'message marked as read'}, status=status.HTTP_200_OK)
        except Message.DoesNotExist:
            return Response({'detail': 'Message non trouvé ou non autorisé.'}, status=status.HTTP_404_NOT_FOUND)
