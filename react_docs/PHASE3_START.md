# 🚀 PHASE 3 - HIÉRARCHIE CNETP & RÔLES

## Situation
- ✅ Phase 1: Infrastructure Django-React complète
- ⏳ Phase 2: npm/build (en attente)
- 🚀 Phase 3: **Implémentation de la hiérarchie CNETP** (MAINTENANT)

## Objectif Phase 3

Créer la **structure complète des rôles et hiérarchie CNETP** dans Django:

### 6 Niveaux de la Hiérarchie
```
Level 1: Executive (3)
  └─ Ministre, SG-ITP, Cabinet Director

Level 2: Comité de Pilotage (24)
  └─ Président, VP, Secrétaire, Rapporteur Général, 20 Conseillers

Level 3: CTC - Cellule Technique (20)
  └─ Coordonnateurs, Experts domaines

Level 4: CTM - 8 Comités Techniques (8 × 19-20)
  └─ Président Science, Rapporteur, Secrétaire, Members

Level 5: WG - Groupes de Travail (24 × 4-5)
  └─ Président WG, Membres, Observateurs

Level 6: Structures d'Origine (16 girons)
  └─ 200 experts total répartis par giron
```

### 16 Girons (Structures)
```
1. Administration publique (61)
2. Établissements publics (64)
3. Ordres professionnels (30)
4. Académiques (12)
5. Métrologie & Société civile (15)
6. Secteur privé (8)
+ 10 autres structures
```

## Plan Phase 3

### A. Créer les modèles Django
```
Models à créer:
✓ ExecutiveLevel (Minister, SG-ITP, Cabinet)
✓ SteeringCommittee (Comité Pilotage - 24)
✓ TechnicalCell (CTC - 20)
✓ TechnicalCommittee (CTM - 8)
✓ WorkingGroup (WG - 24)
✓ Structure (Giron - 16)
✓ Expert (User + hiérarchie)
✓ Role (Rôle spécialisé)
```

### B. Définir les permissions
```
Par niveau:
- Executive: Toutes les permissions
- Steering: Orientation + validation
- CTC: Gestion documentaire
- CTM: Validation sectorielle
- WG: Rédaction
- Observateur: Lecture seule
```

### C. Charger les données
```
1. Créer 200 experts (fixture ou command)
2. Affecter aux CTM/WG
3. Assigner les postes spécialisés
4. Mapper les structures
```

### D. Créer les endpoints API
```
GET /api/v1/hierarchy/executives/
GET /api/v1/hierarchy/steering/
GET /api/v1/hierarchy/ctc/
GET /api/v1/hierarchy/ctm/
GET /api/v1/hierarchy/wg/
GET /api/v1/hierarchy/structures/
GET /api/v1/users/{id}/hierarchy/
```

## Actions Immédiates

1. Créer les modèles Django
2. Créer les migrations
3. Charger les 200 experts
4. Créer les endpoints API
5. Tester avec Django admin


Prêt pour Phase 3? 🚀
