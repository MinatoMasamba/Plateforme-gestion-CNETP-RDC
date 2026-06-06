Module: governance
==================
Gestion des Comités Techniques Miroirs (CTM), Groupes de Travail (WG),
affectations d'experts et comité de pilotage.

Contenu:
- serializers.py : CTMBasicSerializer, CTMDetailSerializer, WGBasicSerializer, WGDetailSerializer,
                   AffectationSerializer, AffectationCreateSerializer, AffectationBulkSerializer,
                   RoleCTMSerializer, ComitePilotageSerializer, CTMCreateUpdateSerializer, WGCreateUpdateSerializer.
- views.py       : CTMViewSet, WGViewSet, AffectationViewSet, RoleCTMViewSet, ComitePilotageViewSet.

Endpoints principaux:
  GET/POST   /api/v1/ctm/
  GET        /api/v1/ctm/{id}/experts/
  GET        /api/v1/ctm/{id}/working_groups/
  GET/POST   /api/v1/wg/
  GET/POST   /api/v1/affectations/
  GET/POST   /api/v1/role-ctm/
  GET/POST   /api/v1/comite-pilotage/
