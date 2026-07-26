# Référentiels externes étendus (Eurocodes, AASHTO, SADC/COMESA)

Ce dossier est le réceptacle des référentiels normatifs internationaux/régionaux
mentionnés dans le prompt système de l'agent IA (`apps/ia_agent/services/prompts.py`)
mais qui ne sont pas fournis avec le dépôt : **Eurocodes** (CEN), **AASHTO** (normes
routières américaines) et **SADC/COMESA** (normes régionales australes/est-africaines).

Ces documents sont commerciaux et/ou sous licence : ils ne peuvent pas être générés
ou récupérés automatiquement. Ils doivent être déposés manuellement par un
administrateur de la plateforme.

## Où déposer les fichiers

| Référentiel | Dossier | Clé utilisée par le tool IA |
|---|---|---|
| Eurocodes | `referentiels_externes/eurocodes/` | `eurocodes` |
| AASHTO | `referentiels_externes/aashto/` | `aashto` |
| SADC / COMESA | `referentiels_externes/sadc/` | `sadc` |

## Format attendu

- Fichiers **PDF texte** (le texte doit être sélectionnable, pas un scan image sans OCR).
- Un fichier par norme ou par recueil, nommé de façon explicite
  (ex. `Eurocode-2-Beton-Arme.pdf`).
- Aucune limite de nombre de fichiers par dossier : le tool `search_extended_referentials`
  scanne tous les `*.pdf` présents au moment de l'appel.

## Comportement tant que les fichiers sont absents

Le tool IA `search_extended_referentials` (voir
`apps/ia_agent/tools/referential_tools.py`) répond explicitement
`{"available": false, "message": "..."}` pour un référentiel dont le dossier est
vide, plutôt que de renvoyer silencieusement une liste vide. Dès qu'un ou plusieurs
PDF sont déposés dans le bon dossier, la recherche devient automatiquement
disponible (pas de redéploiement ni de configuration supplémentaire nécessaire,
mais un redémarrage du processus Django est requis pour vider le cache mémoire de
la fonction de chargement).
