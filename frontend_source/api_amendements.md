# ARCHITECTURE API : MODULE AMENDEMENTS & VOTES (apps/amendments)

## 📌 Rôle Hybride
Contrôle le sous-panneau de discussion de `EditorArea` et l'interface de scrutin. Le backend interdit la modification d'un vote une fois soumis (même si React trafique la requête HTML).

---

## 1. `AmendementViewSet`

**Classe :** `apps.amendments.views.AmendementViewSet`

### `GET /api/v1/amendments/?norme_id={id}`
* **Rôle :** Liste itérative des propositions de textes.
* **UI Controls inclus :**
  * `ui_state.can_vote`: `true` si le statut d'enquête est ouvert ET que l'utilisateur n'a pas encore de record dans la table `Vote` associé.
  * `ui_state.can_resolve`: `true` si le user est modérateur (Rapporteur).
* **Code à intégrer (Serializer Django) :**
```python
def get_ui_state(self, obj):
    user = self.context['request'].user
    has_voted = Vote.objects.filter(amendement=obj, expert=user.expert).exists()
    return {
        "can_vote": not has_voted and obj.status == 'OUVERT',
        "can_resolve": user.expert.is_rapporteur_for(obj.norme.ctm)
    }
```

## 2. `VoteViewSet`

### `POST /api/v1/votes/`
* **Rôle :** Soumission stricte sécurisée d'un bulletin de vote.
* **Méthode :** `create(self, request)`
* **Schéma de soumission :**
```json
{
  "amendement_id": 12,
  "choice": "POUR",
  "comment": "Conforme aux recommandations."
}
```
* **Contraintes Backend :** 
  1. Si un `Vote` existe déjà pour ce couple (Expert, Amendement), l'API répond avec HTTP 403 Forbidden. (React l'intercepte via son hook `djangoFetch` et affiche un Toast d'erreur).
  2. Le serveur recompte à la volée le total des votes. Si le Quorum/Majorité est atteint, il déclenche une Tâche Celery ou Modifie l'état de l'amendement à "VALIDÉ".

### `GET /api/v1/votes/results/?amendement_id={id}`
* Rôle : Renvoie les datas formatées pour `Recharts` (la librairie de graphiques dans React). 
* Format de réponse structuré en pourcentages (Pie chart ready).
