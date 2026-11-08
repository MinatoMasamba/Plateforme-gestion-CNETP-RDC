# Rapport d’implémentation — première passe des 5 espaces ST

Date : 31 octobre 2026.
Périmètre : socle commun, architecture des 5 espaces, Coordination et Pôle 2.
Référence : `prompt` (v2) et `docs/PLAN_CINQ_ESPACES_ST.md`.

## 1. Livré

### Socle
- `apps/governance/st_spaces.py` : espaces, rattachement des 19 postes, menus de 5 à 7 entrées, supervision, périmètres d’audit.
- `apps/governance/st_permissions.py` : lecture filtrée des dossiers, tâches, réunions et journal.
- `apps/governance/st_status.py` : 8 statuts + « Bloquée », dérivés de `CTCProcessus` sans réécrire `Norme.status`.
- `apps/governance/st_workday.py` : quatre blocs « Mon travail du jour », alertes et indicateurs réels.
- Migration `0039_st_validation_decisions` : consolidation, validation et renvoi tracés.
- Migrations `0037` à `0040` appliquées sur la base locale et la base de captures.

### Shell et navigation
- Un seul conteneur d’accueil pour les cinq espaces, routage `espace_p1` à `espace_p4` et `coordination`.
- Menu serveur de 5 à 7 entrées, sans duplication du filtre côté navigateur.
- Barre de recherche globale, notifications, colonne alertes/échéances, bandeau bas aide/contact.
- Accès direct aux modules non autorisés : redirection vers l’accueil ; route `/ctc/espace/<vue>/` renvoie 403 hors périmètre.
- Captures PC et mobile pour 19 postes.

### Coordination
- File de validation avec boutons « Valider » et « Renvoyer », commentaire obligatoire.
- Réception et rapport de SC, demandes à traiter, arbitrage des retards.
- Audit croisé selon la matrice A.9, actions propres exclues.
- Réunions administratives : liste réelle, création de convocation, émargement ; LiveKit reste hors périmètre.

### Pôle 2
- Registre des PTN : création, versions conservées, confirmation par le chef de pôle.
- Dossiers à indexer, GED (versions documentaires réelles), codification, versions et historique.
- Consolidation des avis par le chef du pôle 2, sans décision de faire monter ou redescendre la norme.

## 2. Vérifications

| Contrôle | Résultat |
|---|---|
| `manage.py check` | OK |
| `makemigrations --check --dry-run` | Aucun changement |
| `ruff` sur les fichiers modifiés | OK |
| `pytest tests/test_st_spaces.py --reuse-db` | 5 tests PASS |
| `pytest tests/test_st_matrix_v3.py tests/test_st_backend_operations.py` | 45 PASS, 2 échecs corrigés (audit croisé, formulaires legacy) |
| Captures ST — 7 postes, PC/mobile | 14/14 PASS |
| Captures Pôle 2 — 3 postes, PC/mobile | 5/6 PASS puis poste 12 rejoué : 2/2 PASS |

Les captures et manifestes sont dans `reports/5_espaces_st_final/`, `reports/5_espaces_p2_final/` et `reports/5_espaces_p2_final_12/`.
La revue UX est dans `docs/REVUE_UX_5_ESPACES.md`.

## 3. Limites explicites

- Les modules métier des Pôles 1, 3 et 4 restent des écrans « Module à venir » : plan de travail, livrables, avis juridiques, budget réel, jetons, comptes, sauvegardes, formation, communication et relations usagers.
- LiveKit et la transcription assistée ne sont pas développés.
- La parité Flutter n’est pas incluse dans cette passe.
- La règle de calcul des jetons reste provisoire et configurable.
- Les captures sombres et certains états vides restent à revoir visuellement dans une passe dédiée.

## 4. État de la base

La base locale a reçu les migrations jusqu’à `governance.0040` et `ia_agent.0012`. Une sauvegarde a été prise dans `.local_backups/` avant migration. Aucun commit n’a été effectué.
