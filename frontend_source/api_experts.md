# ARCHITECTURE API : EXPERTS ET STRUCTURES (apps/experts)

## 📌 Rôle Hybride
Le module qui gère la gouvernance "humaine". Les vues sont très restrictives quant à la modification, car seuls certains membres de l'administration ont le droit de requalifier (`Patch`) l'intégrité d'un expert.

---

## 1. `ExpertViewSet`

**Classe :** `apps.experts.views.ExpertViewSet`

### `GET /api/v1/experts/` (Annuaire)
* **Description :** Recherche et liste des experts.
* **Mécanismes DRF requis :** Intégration de `SearchFilter` (sur noms) et `DjangoFilterBackend` (pour menus déroulants de filtrage React sur le composant Annuaire).
* **Réponse avec Méta-données UI (`ui_state`) :**
```json
{
  "results": [
    {
      "id": 144,
      "full_name": "Dr. Kasongo",
      "specialty": "Géotechnique",
      "structure": "Université de Kinshasa",
      "ui_state": {
        "can_edit_profile": false,
        "can_change_affectation": true, 
        "can_deactivate_account": true 
      }
    }
  ]
}
```
*Ici, les 2 derniers champs sont `true` car l'API détecte que l'appelant est Secrétaire Permanent.*

### `PATCH /api/v1/experts/{id}/`
* **Description :** Modifier le statut de l'expert ou changer son groupe.
* **Permissions :** Override de `check_object_permissions(self, request, obj)`.
  * La modification n'est permise que si le `request.user` appartient au board d'administration, sinon lève une `PermissionDenied` exception.
* **Comportement Réaliste Frontend :** Si la requête échoue à cause du backend (ex: tentative de Bypass React), le client React global affiche "Accès refusé par le serveur."

### `GET /api/v1/structures/ddl_options/`
* **Description :** Fournit les options pour les Dropdowns React (ex: Modals d'inscription ou d'affectation).
* **Optimisation :** L'API doit renvoyer uniquement `id` et `name`. Il ne faut pas renvoyer le JSON complet d'une entité pour une liste de choix UI.
```json
[
  {"value": 1, "label": "Ordre des Ingénieurs Civils"},
  {"value": 2, "label": "Université de Kinshasa"}
]
```
