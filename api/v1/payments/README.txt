Module: payments
================
Gestion des cotisations des structures, des paiements et des jetons de présence des experts.

Contenu:
- serializers.py : CotisationBasicSerializer, CotisationDetailSerializer, CotisationCreateUpdateSerializer,
                   PaiementBasicSerializer, PaiementDetailSerializer, PaiementCreateSerializer,
                   JetonPresenceBasicSerializer, JetonPresenceDetailSerializer, JetonPresenceCreateSerializer,
                   PaymentDashboardSerializer, JetonSummarySerializer, PaymentStatsSerializer.
- views.py       : CotisationViewSet (CRUD + send_reminder/pending/by_structure/dashboard),
                   PaiementViewSet (CRUD + confirm/reject/by_cotisation/pending_confirmations),
                   JetonPresenceViewSet (CRUD + by_expert/pending_payment/mark_as_paid/stats).

Endpoints principaux:
  GET/POST   /api/v1/cotisations/
  GET        /api/v1/cotisations/dashboard/
  GET        /api/v1/cotisations/pending/
  POST       /api/v1/cotisations/{id}/send_reminder/
  GET/POST   /api/v1/paiements/
  POST       /api/v1/paiements/{id}/confirm/
  POST       /api/v1/paiements/{id}/reject/
  GET/POST   /api/v1/jetons/
  GET        /api/v1/jetons/by_expert/
  POST       /api/v1/jetons/{id}/mark_as_paid/
