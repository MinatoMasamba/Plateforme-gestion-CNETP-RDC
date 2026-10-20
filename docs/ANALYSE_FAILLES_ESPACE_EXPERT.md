# Analyse des failles et erreurs — Espace de travail Expert

> Périmètre : sidebar et endpoints consommés par l'espace de travail expert
> (`templates/app/app.html` + `api/v1/`).
> Statut : corrigé dans le même lot (voir « Corrections appliquées »).

## 1. Failles de sécurité

### F1 — Fuite des coordonnées bancaires de tous les experts (critique)
`ExpertViewSet.get_serializer_class` renvoyait `ExpertDetailSerializer` pour
`list` (`api/v1/experts/views.py:77-78`), serializer qui expose
`bank_account`, `bank_name`, `mobile_money_number`
(`api/v1/experts/serializers.py:45`). Le sidebar appelle `/api/v1/experts/`
sans filtre (`templates/app/app.html:7437`) : tout expert authentifié lisait
les données bancaires de l'ensemble des experts.

### F2 — Aucun contrôle d'objet sur les experts (critique)
`update/partial_update/destroy` = `[IsAuthenticated()]` seulement
(`api/v1/experts/views.py:92-94`) ; la permission `IsOwnerOrCTC` existait mais
n'était jamais branchée. N'importe quel expert pouvait modifier ou **supprimer**
n'importe quel autre expert (`DELETE /api/v1/experts/{id}/`). De plus `create`
avait `permission_classes=[]` (création publique).

### F3 — Le cloisonnement par SC est purement cosmétique (critique)
`NormeViewSet` utilisait un queryset global et `IsExpertOrCTC` sans test d'objet
(`api/v1/norms/views.py:43-51,143-149`) :
- `GET /api/v1/norms/` renvoyait les normes de **toutes** les SC ;
- `PATCH/PUT/DELETE`, `create_version`, `comments`, `lock/unlock` sur une norme
  d'une autre SC étaient permis. Seul `vote` vérifiait
  `expert.ctm_id == norme.ctm_id` (`api/v1/norms/views.py:447-451`).

Le filtrage visible dans la sidebar (`app.html:7467-7470`) n'existait que côté
navigateur.

### F4 — Tâches non contrôlées (moyenne)
`TaskDetailViewSet.update_task` modifiait n'importe quelle tâche sans vérifier
l'appartenance au WG (`api/v1/sidebar/views.py:190-206`).

### F5 — Endpoints sidebar globaux (moyenne)
`WorkingGroupSidebarViewSet`, `ExpertSidebarViewSet`, `DocumentSidebarViewSet`
= `IsAuthenticated` + queryset global (`api/v1/sidebar/views.py:89-225`) →
annuaire complet et normes complètes accessibles.

## 2. Erreurs / bugs (front)

| # | Description | Emplacement |
|---|-------------|-------------|
| B1 | Repli qui expose les autres SC : `documents = scopedDocs.length ? scopedDocs : mappedDocs` | `app.html:7470` |
| B2 | Pagination + filtrage client : si > 100 normes, celles de la SC peuvent tomber hors page → invisibles, puis repli sur les autres | `app.html:7435,7467-7470` |
| B3 | Mauvais auteur affiché : `updatedBy: n.ctm_name \|\| "Admin"` montre le nom du CTM, pas l'auteur de la dernière modification | `app.html:7463` |
| B4 | Comparaison number/string : sélection `'${doc.id}'` (string) mais surlignage `doc.id === selectedDocId` | `app.html:7653,7657,7723` |
| B5 | `roleId` jamais fourni : le front lit `profileData.role_id`, absent de `ExpertDetailSerializer` | `app.html:2521` |

## 3. Corrections appliquées

### Backend
1. **Périmètre CTM/SC partagé** — `api/v1/permissions.py` :
   - `user_ctm_scope(user)` : `None` = accès non restreint (superuser, staff,
     CTC, direction/pilotage), sinon `set` des IDs de CTM de l'expert (CTM
     principal + affectations).
   - `IsExpertOfCTM` durci (objet) : accepte CTC/superuser, sinon vérifie
     `obj.ctm_id` dans le périmètre de l'expert.
2. **Normes** (`api/v1/norms/views.py`) — `get_queryset` filtre par périmètre,
   `perform_create` interdit la création hors périmètre. Les actions
   `retrieve/update/destroy/create_version/comments/lock/unlock` passent par
   `get_object()` donc réutilisent le queryset scopé (404 hors SC).
3. **Experts** (`api/v1/experts/views.py`, `serializers.py`) —
   `update/partial_update` = `IsAuthenticated + IsOwnerOrCTC`, `destroy` =
   `IsCTCCoordinator`, `create` = `IsCTCCoordinator`. Nouveau
   `ExpertListSerializer` sans champs bancaires pour `list` ; `retrieve` ne
   renvoie les données bancaires qu'à l'intéressé / CTC / staff. `role_id`
   ajouté à `ExpertDetailSerializer` (corrige B5). Les actions `experts` de
   `CTMViewSet` et `WGViewSet` (annuaire) utilisent `ExpertListSerializer`.
4. **Versions & changements de normes** (`NormeVersionViewSet`,
   `ChangementVersionViewSet`) — `get_queryset` scopé au périmètre.
5. **Sidebar** (`api/v1/sidebar/views.py`) — WG, experts, documents scopés au
   CTM de l'expert ; `update_task` vérifie que le WG de la tâche est dans le
   périmètre.

### Frontend (`templates/app/app.html`)
1. Suppression du repli « toutes les normes » (B1/B2).
2. `updatedBy` alimenté par `updated_by_name` (B3).
3. Comparaisons d'ID normalisées via `String()` (B4).

## 4. Compteur d'activité (temps + éditions)

Nouveau endpoint `GET /api/v1/activity/my-counter/`
(`api/v1/sidebar/views.py` → `ActivityCounterViewSet`) :

- `active_seconds_total` / `active_seconds_today` : temps observé, calculé
  depuis `ActivitySession` / `ActivityPulse` (système existant de battements).
- `editions_total` / `editions_today` : nombre de versions de normes créées par
  l'expert (`NormeVersion.version_author`).
- `last_activity` : dernier battement enregistré.

Un widget est affiché dans le pied du sidebar de l'espace expert et rafraîchi
toutes les 60 secondes, en cohérence avec le heartbeat existant.
