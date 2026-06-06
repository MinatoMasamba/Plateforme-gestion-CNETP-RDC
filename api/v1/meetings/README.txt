Module: meetings
================
Gestion des réunions, présences, votes électroniques et procès-verbaux.

Contenu:
- serializers.py : ReunionBasicSerializer, ReunionDetailSerializer, ReunionCreateUpdateSerializer,
                   ReunionStatusUpdateSerializer, PresenceSerializer, PresenceCheckInSerializer,
                   ProcessusVerbauxSerializer, ReunionVoteSerializer, ReunionSummarySerializer, ReunionStatsSerializer.
- views.py       : ReunionViewSet (CRUD + checkin_presence/vote/close/generate_pv/presences/upcoming/past/stats),
                   PresenceViewSet, ReunionVoteViewSet, ProcessusVerbauxViewSet.

Endpoints principaux:
  GET/POST   /api/v1/reunions/
  GET        /api/v1/reunions/{id}/details/
  POST       /api/v1/reunions/{id}/checkin_presence/
  POST       /api/v1/reunions/{id}/vote/
  POST       /api/v1/reunions/{id}/close/
  POST       /api/v1/reunions/{id}/generate_pv/
  GET        /api/v1/presences/
  GET        /api/v1/reunion-votes/
  GET        /api/v1/pv/
