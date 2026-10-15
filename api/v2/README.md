# API v2 Organisation Phoenix

Cette API authentifiée partage les services d’autorisation et de workflow de l’interface web. Les endpoints v1 restent réservés au circuit historique CTM/WG.

## Endpoints

| Méthode | Route | Usage |
|---|---|---|
| GET | `/api/v2/organisation/` | Référentiel et état de préparation |
| GET/POST | `/api/v2/organisation/configuration/<type>/[<id>/]` | Configuration contrôlée |
| POST | `/api/v2/organisation/mise-en-service/` | Activation ou suspension |
| GET/POST | `/api/v2/organisation/dossiers/` | Liste filtrée ou création |
| GET | `/api/v2/organisation/dossiers/<id>/` | Détail, versions, pièces, décisions et transitions autorisées |
| POST | `/api/v2/organisation/dossiers/<id>/operation/` | Édition, pièce, décision, enquête, verrou, réunion ou présence |
| GET | `/api/v2/organisation/pieces/<id>/` | Téléchargement protégé |
| GET | `/api/v2/organisation/export/` | Export du périmètre accessible |

## Règles du client

Chaque opération fournit `mandate` et `revision`. Une décision fournit aussi `transition`, `decision_reference`, `reason` et une `request_key` stable pour les répétitions réseau. Un conflit de révision renvoie `409` et oblige le client à recharger le dossier.

Les transitions retournées par le détail sont informatives : le serveur recalcule toujours l’autorisation, le quorum, les preuves et l’étape au moment de l’écriture. Les identifiants de mandat ou de pièce provenant d’un autre utilisateur, dossier ou périmètre sont refusés.

L’authentification de session respecte CSRF. Les téléchargements ne révèlent aucun chemin public et restent soumis au même périmètre de lecture que le dossier.
