# Paramètres CTC : état des services

Le module d'origine affichait des contrôles locaux sans lecture ni écriture serveur.
L'interface actuelle ne présente une action que lorsqu'un service est réellement raccordé.

| Réglage d'origine | État | Service ou décision nécessaire |
| --- | --- | --- |
| Mode sombre | Actif | Préférence locale du navigateur, persistante |
| Notifications de pôle | Partiel | Les catégories de notifications serveur sont réglables et appliquées. Un flux « toute activité du pôle » n'existe pas. |
| Synchronisation Drive | Service serveur prêt, désactivé par défaut | Le poste IT peut activer la copie des fichiers liés aux normes adoptées, homologuées ou publiées ; chaque essai est journalisé |
| Délégation de signature temporaire | Non disponible | Autorité délégante, délégataire, actes et durée autorisés, contrôle serveur du mandat |
| Alertes Chronogramme Strict | Non disponible | Source d'échéance, destinataires, fréquence et règle de déduplication, tâche planifiée |
| Clé d'homologation | Non disponible | Service de signature officiel, gestion et rotation des clés, poste habilité |
| Synchronisation ISO automatique | Non disponible | Source ISO autorisée/licenciée, identifiants, fréquence et politique de mise à jour |
| Correcteur de structure | Non disponible | Règles et point de validation serveur |
| Modèle de rapport | Non disponible | Générateur serveur et modèles approuvés |
| Filtre anti-spam enquêtes | Non disponible | Modèle d'avis, critères de rejet et procédure de révision |
| Visibilité budgétaire | Non disponible | Source comptable du solde trimestriel et droits de lecture |
| Canal externe | Non disponible | Canaux approuvés et routeur d'envoi avec preuve de remise |
| Mode Debug Actif | Non disponible | Aucun contrôle utilisateur de `DEBUG` serveur |
| Rendu cartographique 3D | Non disponible | Moteur SIG 3D et couches accessibles |
| Sauvegarde globale | Actif pour les postes IT sur SQLite | Copie des données et documents, contrôle de restauration, audit. PostgreSQL requiert une routine dédiée. |

Le 14 octobre 2026, les trois identifiants OAuth Drive ont été copiés depuis
`/home/minato/source_academique_server/.env` dans le `.env` local CNE-ITP,
avec permission 0600. Le 15 octobre 2026, un dossier racine distinct
`CNE-ITP_Documents` a été créé et vérifié par l'API Google Drive ; son
identifiant est enregistré dans le `.env` CNE-ITP. Le service de transfert
utilise exclusivement ce dossier et les statuts ADOPTED, HOMOLOGATED et
PUBLISHED. Il garde le fichier local et une trace de chaque tentative.
L'activation est réservée aux postes IT CTC et reste désactivée par défaut.
Au moment de la mise en place, aucun fichier n'était éligible et aucun
document n'a été transféré. La migration additive `documents.0003` a été
précédée d'une sauvegarde avec restauration vérifiée ; le contrôle SQLite
après migration a confirmé `integrity_check=ok`, aucune clé étrangère invalide
et un manifeste historique inchangé. Les fichiers
d'environnement ne contiennent toujours aucune source ISO ni infrastructure
de signature d'homologation. Aucune valeur secrète ne figure dans ce document.
