Module: experts
===============
Gestion des experts et des structures membresau CNETP.

Contenu:
- serializers.py        : StructureSerializer, ExpertBasicSerializer, ExpertDetailSerializer,
                          ExpertCreateUpdateSerializer, ExpertInscriptionSerializer, ExpertPublicRegistrationSerializer.
- views.py              : ExpertViewSet (CRUD + activate/deactivate/me/inscription/admit-to-ctm)
                          et StructureViewSet (lecture seule).
- registration_views.py : ExpertPublicRegistrationViewSet et ExpertPublicRegistrationView
                          (inscription publique via QR Code).

Endpoints principaux:
  GET/POST   /api/v1/experts/
  GET        /api/v1/experts/me/
  POST       /api/v1/experts/{id}/activate/
  POST       /api/v1/experts/{id}/deactivate/
  POST       /api/v1/experts/{id}/admit-to-ctm/
  POST       /api/v1/experts/inscription/
  POST       /api/v1/experts/public-register/public_register/
  GET        /api/v1/structures/
