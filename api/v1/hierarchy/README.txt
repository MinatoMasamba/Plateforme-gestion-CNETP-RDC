Module: hierarchy
=================
Vue d'ensemble de la hiérarchie organisationnelle du CNETP :
Niveau Exécutif, Comité de Pilotage, Cellule Technique CTC, Structures d'Origine (Girons).

Contenu:
- serializers.py : ExecutiveLevelSerializer, SteeringCommitteeSerializer, TechnicalCellSerializer,
                   OriginStructureSerializer, HierarchyOverviewSerializer, CTCMembershipSerializer,
                   PilotageMembershipSerializer.
- views.py       : ExecutiveLevelViewSet, SteeringCommitteeViewSet, TechnicalCellViewSet,
                   OriginStructureViewSet, HierarchyViewSet (overview/ctm/wg/structures).

Endpoints principaux:
  GET   /api/v1/executive-level/
  GET   /api/v1/steering-committee/
  GET   /api/v1/technical-cell/
  GET   /api/v1/origin-structures/
  GET   /api/v1/hierarchy/overview/
  GET   /api/v1/hierarchy/ctm/
  GET   /api/v1/hierarchy/wg/
  GET   /api/v1/hierarchy/structures/
