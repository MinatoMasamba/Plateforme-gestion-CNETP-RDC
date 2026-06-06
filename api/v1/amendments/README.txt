Module: amendments
==================
Gestion des amendements proposés sur les normes, des votes et des résultats de vote.

Contenu:
- serializers.py : AmendementBasicSerializer, AmendementDetailSerializer, AmendementCreateUpdateSerializer,
                   AmendementStatusUpdateSerializer, VoteSerializer, VoteCreateSerializer,
                   ResultatVoteSerializer, AmendementSummarySerializer, AmendementStatsSerializer.
- views.py       : AmendementViewSet (CRUD + vote/votes/results/update_status/by_norme/pending/stats),
                   VoteViewSet, ResultatVoteViewSet.

Endpoints principaux:
  GET/POST   /api/v1/amendments/
  POST       /api/v1/amendments/{id}/vote/
  GET        /api/v1/amendments/{id}/votes/
  GET        /api/v1/amendments/{id}/results/
  POST       /api/v1/amendments/{id}/update_status/
  GET        /api/v1/votes/
  GET        /api/v1/resultats-vote/
