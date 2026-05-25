# ARCHITECTURE GLOBALE API CNETP (HYBRIDE DJANGO-REACT)

## 1. PARADIGME : SERVER-DRIVEN UI
Dans notre architecture hybride, **le frontend React est un client passif**. Il ne code en dur **aucune règle métier** (qui a le droit de cliquer sur quoi, quel statut suit un autre). Django est le maître absolu et Dicte l'interface utilisateur.

### Mécanique d'interaction
Pour tout `ViewSet` Django, le `Serializer` associé inclut systématiquement un nœud de métadonnées `ui_state` ou `ui_permissions`. Le Frontend React lit cet objet et affiche, grise ou masque les widgets en conséquence.

**Exemple de surcharge du Serializer de base dans Django :**
```python
class ServerDrivenSerializer(serializers.ModelSerializer):
    ui_state = serializers.SerializerMethodField()

    def get_ui_state(self, obj):
        user = self.context['request'].user
        return {
            "is_editable": obj.is_editable_by(user),
            "is_deletable": obj.is_deletable_by(user),
            "allowed_state_transitions": obj.get_allowed_transitions(user), # Pour populer les menus déroulants
            "badges": obj.get_frontend_badges() # Ex: ["Urgent", "En attente CTC"]
        }
```

---

## 2. DÉTAIL ORGANIQUE PAR MODULE

### MODULE 1 : EXPERTS & STRUCTURES (apps/experts)
**Modèle central concerné :** `Expert`, `Structure`
**Vue cible :** `ExpertViewSet`, `StructureViewSet`

* **GET /api/v1/experts/**
  * **Rôle :** Alimenter la DataGrid du frontend React (Annuaire).
  * **Permissions :** `IsAuthenticated`.
  * **Méthodes internes :** `get_queryset()` filtre pour ne renvoyer que les experts approuvés, sauf si l'utilisateur est `IsCTCCoordinator`.
  * **Dépendance UI :** Le bouton "Changer d'affectation" sur la ligne d'un expert est fourni dynamiquement si `ui_state.can_reassign == true`.

* **POST /api/v1/experts/{id}/activate/**
  * **Permissions :** Uniquement `IsCTCCoordinator`.
  * **Action Vue :** Décorateur `@action(detail=True, methods=['post'])`. Change le statut et déclenche l'envoi d'email.

### MODULE 2 : NORMES (apps/norms)
**Modèle central concerné :** `Norme`, `NormeVersion`
**Vue cible :** `NormeViewSet`

* **GET /api/v1/norms/**
  * **Rôle :** Liste les projets de normes pour la Sidebar React.
  * **Permissions :** Rôle `Expert` lié au CTM de la norme.
  * **Méthodes internes :** `get_queryset()` filtre selon `request.user.expert.ctm_affectations`.
  * **UI Control :** La réponse inclut `ui_state.can_publish` (vrai seulement pour le Rapporteur CTM).

* **PUT /api/v1/norms/{id}/**
  * **Rôle :** Sauvegarde automatique depuis l'éditeur de texte React.
  * **Méthodes internes :** Surcharge de `perform_update()`. Vérifie qu'aucun autre expert n'est en mode édition exclusive.

### MODULE 3 : AMENDEMENTS & VOTES (apps/amendments)
**Modèle central concerné :** `Amendement`, `Vote`
**Vue cibles :** `AmendementViewSet`, `VoteViewSet`

* **GET /api/v1/norms/{id}/amendments/**
  * **Rôle :** Affiche le panneau latéral droit des commentaires/amendements dans l'Éditeur.
  * **UI Control :** Retourne un `dropdown_actions` avec ["Approuver", "Rejeter"] si l'utilisateur est Président du WG. Tableau vide `[]` pour un membre simple.

* **POST /api/v1/amendments/{id}/cast_vote/**
  * **Schema :** `{"choice": "POUR" | "CONTRE"}`
  * **Action Vue :** Valide via `has_permission` que le Scrutin est statut "OUVERT". Clôture automatiquement le scrutin si 100% des membres ont voté via signal.

### MODULE 4 : RÉUNIONS & PRÉSENCES (apps/meetings)
**Modèle central concerné :** `Reunion`, `Presence`
**Vue cible :** `ReunionViewSet`

* **GET /api/v1/meetings/pending_signatures/**
  * **Rôle :** Alimente le widget "Tâches à faire" du tableau de bord.
  * **UI Control :** Affiche des formulaires de signatures de PV (Procès Verbal) seulement pour les Rapporteurs.

* **POST /api/v1/meetings/{id}/checkin/**
  * **Rôle :** Émargement numérique.
  * **Validation :** Le `perform_create()` sur le serializer va créer automatiquement le crédit de Jetons de présence associé.

### MODULE 5 : FINANCES (apps/payments)
**Modèle central concerné :** `Cotisation`, `JetonPresence`
**Vue cible :** `FinanceViewSet`

* **GET /api/v1/finances/my_jetons/**
  * **Rôle :** Alimenter l'historique financier de l'Expert dans le frontend. Affiche un JSON brut, formaté par les composants Tailwind côté React.

---
Ce fichier maître garantit que les composants métier respectent l'isolation logique, en laissant le backend dicter non pas le HTML, mais le "JSON of Capabilities". Des fichiers `.md` détaillés ont été générés pour chaque entité séparée.
