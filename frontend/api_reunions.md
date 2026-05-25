# ARCHITECTURE API : MODULE RÉUNIONS & PV (apps/meetings)

## 📌 Rôle Hybride
Le module pilote le composant React `MeetingsVotesModule`. Il ne peut affiché l'ordre du jour ou le bouton "Émarger" que si le serveur lui dit que la réunion est dans le créneau horaire valide.

---

## 1. `ReunionViewSet`

**Classe :** `apps.meetings.views.ReunionViewSet`
**Héritage :** `viewsets.ModelViewSet`

### `GET /api/v1/meetings/`
* **Description :** Calendrier des réunions associées aux comités de l'utilisateur.
* **Méthode à implémenter :** `get_queryset()` + `Filters`
  * Prise en charge des paramètres querystring `?status=UPCOMING` ou `?status=PAST`.
* **DRF Serializer Response :**
```json
{
  "id": 42,
  "date": "2026-05-25T10:00:00Z",
  "title": "Adoption amendements finaux",
  "ctm_id": 1,
  "ui_state": {
    "can_checkin": false,  // (Car la date est > à now())
    "can_generate_pv": false,
    "can_manage_agenda": true // (Si le request.user est le Rapporteur)
  }
}
```

### `POST /api/v1/meetings/{id}/checkin/`
* **Description :** Enregistrement de la présence d'un expert.
* **Permission :** L'utilisateur cible doit faire partie du CTM invité.
* **Logique Django (`perform_create` ou `@action`) :**
  1. Chercher ou créer l'objet `Presence` lié à `request.user.expert`.
  2. Mettre le statut à `PRESENT`.
  3. **Trigger de Signal métier :** Créer instantanément une entrée dans `JetonPresence` (module Finances).

### `POST /api/v1/meetings/{id}/generate_pv/`
* **Description :** Demande au serveur de générer le document (Markdown ou PDF) des minutes de la réunion.
* **Permission :** Uniquement `Rapporteur` ou `Secretaire`.
* **Réponse JSON :** 
  Fournit une URL directe du fichier pré-signé généré sur S3/MinIO ou dans le dossier Média local, transmise à React pour lancer le download natif HTML5.
