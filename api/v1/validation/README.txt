Module: validation
==================
Toilettage légistique des normes par les membres CTC avant publication.

Contenu:
- serializers.py : LegisticReviewBasicSerializer, LegisticReviewDetailSerializer,
                   LegisticReviewStartSerializer, LegisticReviewCompleteSerializer,
                   LegisticReviewRejectSerializer.
- views.py       : LegisticReviewViewSet (CRUD + workspace/legistique-workspace/assign-self/
                   validate-ctc/set-step/pending/in_review/start_review/complete_review/
                   reject_review/my_reviews).

Endpoints principaux:
  GET        /api/v1/legistic-reviews/workspace/
  GET        /api/v1/legistic-reviews/legistique-workspace/
  POST       /api/v1/legistic-reviews/{id}/assign-self/
  POST       /api/v1/legistic-reviews/{id}/validate-ctc/
  POST       /api/v1/legistic-reviews/set-step/
  GET        /api/v1/legistic-reviews/pending/
  GET        /api/v1/legistic-reviews/my_reviews/
