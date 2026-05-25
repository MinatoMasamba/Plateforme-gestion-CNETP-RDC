# ARCHITECTURE API : MODULE FINANCES (apps/payments)

## 📌 Rôle Hybride
Connecté avec les comptables FONER. Contrôle conditionnel ultra-strict garantissant que personne ne peut manipuler les Jetons de présence en dehors des algorithmes de présence ou des virements manuels comptables.

---

## 1. `CotisationViewSet`

**Classe :** `apps.payments.views.CotisationViewSet`

### `GET /api/v1/finances/cotisations/`
* **Rôle :** Vue globale pour le `FinancialModule` React (Côté Administrateur).
* **Permissions :** Rôle `COMPTABLE_FONER` ou `COORD_CTC`.
* **Réponse JSON Enrichie (Agrégation) :**
  Implémenter un `get_queryset()` avec `annotate()` pour renvoyer directement au frontend la somme des dettes sans que React ait à faire des mathématiques complexes.
```json
{
  "results": [
    {
      "structure_name": "Office des Routes",
      "du_total": 5000.00,
      "paye_total": 2000.00,
      "reste_a_payer": 3000.00,
      "statut_alerte": "DANGER"
    }
  ],
  "ui_state": {
    "can_send_reminder": true
  }
}
```

### `POST /api/v1/finances/cotisations/{id}/send_reminder/`
* **Rôle :** Émet une tâche en File d'attente (Celery) pour générer l'email formel de relance au point focal de l'entreprise.

---

## 2. `JetonPresenceViewSet`

### `GET /api/v1/finances/jetons/my_jetons/`
* **Rôle :** Liste le portefeuille d'un expert.
* **Méthode :** `@action` dédiée pour filtrer stricto sensu sur `request.user.expert`.
* **UI Controls :**
```json
{
  "total_acquis": 1500,
  "historique": [
    {
       "reunion": "CTM 1 - Session Ordinaire",
       "date": "2026-05-18",
       "montant": 150,
       "est_paye_en_banque": false
    }
  ],
  "ui_state": {
    "can_download_receipt": true
  }
}
```

### `GET /api/v1/finances/jetons/{id}/download_receipt/`
* **Rôle :** Indique au serveur Django de générer un PDF de reçu via un utilitaire comme Rapportlab ou WeasyPrint. Retourne le lien pré-signé ou le `binary stream`.
