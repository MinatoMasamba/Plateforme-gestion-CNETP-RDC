# ARCHITECTURE API : MODULE NORMES (apps/norms)

## 📌 Rôle Hybride 
Ce module contrôle le composant React `EditorArea`. Les décisions de verrouillage concurrent (qui a le droit d'éditer le texte à un instant T) se font via le backend.

---

## 1. Machine à États Rigoureuse - Circuit de Validation en "Boucle Fermée" (Chapitre VI)

Pour qu'un projet de norme devienne obligatoire et intégré au Référentiel National, le backend Django impose une transition d'états stricte dont le statut est exposé au frontend React via `ui_state.allowed_state_transitions` :

```
[DRAFT_WG] ──(Soumission Rapporteur WG)──> [VOTE_CTM] ──(Vote Majorité Qualifiée)──> [PUBLIC_INQUIRY]
                                                                                           │
                                                                                 (Enquête Publique Web)
                                                                                           │
                                                                                           ▼
[MINISTERIAL_HOMOLOGATION] <──(Signature Arrêté)── [PLENARY_ADOPTION] <──(Vote Consensus)──┘
```

### 📋 Mappage Technique des États (`status`) :
1. **`DRAFT_WG` (Conception Spécialisée) :** Le Groupe de Travail (WG) rédige ou transpose le premier jet. Seuls les experts affectés à ce WG ont les droits de modification.
2. **`VOTE_CTM` (Validation Sectorielle) :** Le projet est examiné, amendé, et voté à la majorité qualifiée par les 20 membres permanents du CTM parent.
3. **`PUBLIC_INQUIRY` (Toilettage et Enquête) :** La Cellule Technique de Coordination (CTC) prend le relai, met en forme le texte, et lance l'enquête publique numérique (Article 12) sur le portail web. Les citoyens et experts des provinces soumettent leurs amendements en ligne. Le WG réintègre ensuite les retours valides.
4. **`PLENARY_ADOPTION` (Adoption Souveraine) :** Le projet final est soumis à l'Assemblée Plénière des 200 experts pour adoption par consensus.
5. **`MINISTERIAL_HOMOLOGATION` (Sanction Légale) :** Transmis au Ministre des ITP pour signature de l'Arrêté d'Homologation, rendant la norme exécutoire sur toute l'étendue du territoire national et ordonnant sa publication au Journal Officiel.

---

## 2. `NormeViewSet`

**Classe :** `apps.norms.views.NormeViewSet`
**Héritage :** `viewsets.ModelViewSet`

### `GET /api/v1/norms/`
* **Description :** Récupération de la liste des normes pour la Sidebar React.
* **Méthode à surcharger :** `get_queryset(self)`
  * *Règle :* `return Norme.objects.filter(ctm__in=self.request.user.expert.ctm_set.all())`
* **Réponse attendue de DRF :**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "title": "Eurocode 8",
      "status": "DRAFT_WG",
      "ui_state": {
        "can_open_editor": true,
        "is_locked_by_other": false,
        "lock_owner": null
      }
    }
  ]
}
```

### `POST /api/v1/norms/{id}/lock/`
* **Description :** Prend le contrôle exclusif de la norme avant de commencer à taper dans React.
* **Méthode:** `@action(detail=True, methods=['post']) def lock(self, request, pk=None)`
* **Vérification :** S'assure que le champ `locked_by` est en base de données.
* **Impact Frontend :** Les autres utilisateurs qui ont la page ouverte recevront un événement WebSocket ou via polling, et React "disabled" l'attribut du `<textarea>`.

### `POST /api/v1/norms/{id}/submit_to_legistique/`
* **Description :** Transmet le texte au bureau de révision légale.
* **Permissions :** `IsRapporteurCTM`
* **Action interne :** Modifie le statut, horodate, ajoute un `AuditLog`, notifie le coordonnateur CTC.
* **Impact Frontend :** La norme disparaît de la vue d'édition des experts, et apparaît dans la DataGrid du rôle `LEGISTE`.
