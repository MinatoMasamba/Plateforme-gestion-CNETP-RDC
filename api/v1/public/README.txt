Module: public
==============
Amendements soumis par le public lors des phases d'enquête publique sur les normes.

Contenu:
- serializers.py : PublicAmendementSerializer, PublicAmendementDetailSerializer,
                   PublicAmendementReviewSerializer.
- views.py       : PublicAmendementViewSet (CRUD + submit_for_norm/review/by_norm/
                   pending_review/statistics).

Endpoints principaux:
  GET/POST   /api/v1/public-amendments/
  POST       /api/v1/public-amendments/submit_for_norm/
  GET        /api/v1/public-amendments/by_norm/?norme_id=1
  GET        /api/v1/public-amendments/pending_review/
  GET        /api/v1/public-amendments/statistics/
  POST       /api/v1/public-amendments/{id}/review/

Permissions:
  - create/list/retrieve : AllowAny (soumission publique)
  - review/update/destroy : IsAuthenticated + IsCTCCoordinator
