Module: documents
=================
Gestion des documents déposés par les experts, et bridge API pour la compatibilité frontend.

Contenu:
- serializers.py  : DocumentFileSerializer.
- views.py        : DocumentFileViewSet (CRUD avec upload multipart).
- bridge_views.py : DocumentsAPIView (bridge /api/documents → /api/v1/documents),
                    CollaboratorsAPIView (bridge /api/collaborators → /api/v1/experts).

Endpoints principaux:
  GET/POST   /api/v1/documents/          (DocumentFileViewSet)
  GET        /api/v1/collaborators/      (CollaboratorsAPIView)
  GET        /api/documents/             (DocumentsAPIView — bridge)
