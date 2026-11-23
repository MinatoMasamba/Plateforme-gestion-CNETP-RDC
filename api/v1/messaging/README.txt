Module: messaging
=================
Messagerie directe entre experts appartenant au même CTM.

Contenu:
- serializers.py : MessageSerializer + ConversationSerializer.
- views.py       : MessageViewSet (CRUD + conversations/contacts/unread_count/lecture).

Endpoints principaux:
  GET/POST   /api/v1/messages/
  GET        /api/v1/messages/conversations/
  GET        /api/v1/messages/contacts/
  GET        /api/v1/messages/unread_count/
  POST       /api/v1/messages/mark_conversation_as_read/
  POST       /api/v1/messages/{id}/mark_as_read/

Permissions:
  - IsAuthenticated + IsMemberOfAnySharedCTM pour accéder à la messagerie.
  - Seuls les experts partageant un CTM peuvent échanger des messages.
