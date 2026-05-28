from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .messaging_serializers import MessageSerializer
from apps.messaging.models import Message
from apps.experts.models import Expert # To get CTM choices
from .permissions import IsMemberOfAnySharedCTM # Custom permission
from .experts_serializers import ExpertBasicSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-timestamp') # Default queryset
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberOfAnySharedCTM]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'expert_profile'):
            return Message.objects.none()

        # Filter messages where the current user is either the sender or the recipient.
        # This handles both direct messages and messages associated with a reunion (if they exist for the user).
        queryset = Message.objects.filter(Q(sender=user) | Q(recipient=user))

        # Optional: Filter by reunion_id if provided in query params
        reunion_id = self.request.query_params.get('reunion_id')
        if reunion_id:
            queryset = queryset.filter(reunion_id=reunion_id)

        return queryset.order_by('timestamp')

    def perform_create(self, serializer):
        sender = self.request.user

        # Check if the sender is an expert
        if not hasattr(sender, 'expert_profile'):
            raise permissions.PermissionDenied("Seuls les experts peuvent envoyer des messages.")

        # Automatically set the sender to the requesting user
        serializer.save(sender=sender)

        # Additional validation for recipient if provided
        recipient = serializer.validated_data.get('recipient')
        if recipient:
            if not hasattr(recipient, 'expert_profile'):
                raise permissions.PermissionDenied("Le destinataire doit être un expert.")

            # Check if sender and recipient share at least one CTM
            sender_ctms = set(sender.expert_profile.ctm_choices.values_list('id', flat=True))
            recipient_ctms = set(recipient.expert_profile.ctm_choices.values_list('id', flat=True))

            if not bool(sender_ctms.intersection(recipient_ctms)):
                raise permissions.PermissionDenied("L'expéditeur et le destinataire doivent partager au moins un CTM en commun.")
        
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsMemberOfAnySharedCTM])
    def contacts(self, request):
        """Liste les experts avec lesquels l'utilisateur actuel partage au moins un CTM."""
        user = request.user
        if not hasattr(user, 'expert_profile'):
            return Response([], status=status.HTTP_200_OK)
        
        current_expert_ctms = user.expert_profile.ctm_choices.all()
        
        # Find all experts who share at least one CTM with the current user
        # Exclude the current user themselves
        shared_ctm_experts = Expert.objects.filter(
            ctm_choices__in=current_expert_ctms
        ).exclude(user=user).distinct()
        
        serializer = ExpertBasicSerializer(shared_ctm_experts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMemberOfAnySharedCTM])
    def mark_as_read(self, request, pk=None):
        """Marque un message comme lu."""
        try:
            message = self.get_queryset().get(pk=pk, recipient=request.user) # Only recipient can mark as read
            message.is_read = True
            message.save()
            return Response({'status': 'message marked as read'}, status=status.HTTP_200_OK)
        except Message.DoesNotExist:
            return Response({'detail': 'Message non trouvé ou non autorisé.'}, status=status.HTTP_404_NOT_FOUND)
