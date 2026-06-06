Module: norms
=============
Gestion du cycle de vie des normes CNETP : création, versioning, votes, publication JO.

Contenu:
- serializers.py : NormeBasicSerializer, NormeDetailSerializer, NormeCreateUpdateSerializer,
                   NormeStatusUpdateSerializer, NormeVersionSerializer, NormeVersionCreateSerializer,
                   NormeFullHistorySerializer, ChangementVersionSerializer, NormeVoteSerializer.
- views.py       : NormeViewSet (CRUD + create_version/history/votes/vote/versions/diff/rollback-version/publish_to_jo),
                   NormeVersionViewSet, ChangementVersionViewSet.

Endpoints principaux:
  GET/POST   /api/v1/norms/
  POST       /api/v1/norms/{id}/create_version/
  GET        /api/v1/norms/{id}/history/
  GET        /api/v1/norms/{id}/votes/
  POST       /api/v1/norms/{id}/vote/
  GET        /api/v1/norms/{id}/versions/
  GET        /api/v1/norms/{id}/diff/?v1=X&v2=Y
  POST       /api/v1/norms/{id}/rollback-version/
  POST       /api/v1/norms/extract_document/
  GET/POST   /api/v1/norm-versions/
  GET/POST   /api/v1/changements-version/
