# Implémentation Phoenix — 14 octobre 2026

## État du déploiement

Le socle logiciel de la migration Phoenix est implémenté. La base principale porte l’organisation `phoenix-2026-10` et ses sept sous-commissions techniques au statut **Validé**. Le circuit reste inactif : aucun GT officiel, titulaire, mandat, pouvoir ou circuit institutionnel n’a été inventé.

### Reprise des experts appliquée le 14 octobre 2026

La base historique utilisée comme source contient 149 experts, 8 CTM, 30 WG et 7 affectations formelles. La sauvegarde source est conservée sous `.local_backups/phoenix-20261013T124504554097Z/`. Une nouvelle sauvegarde SQLite et médias, suivie d'une restauration de contrôle, a été créée juste avant la correction sous `.local_backups/phoenix-20261013T235035198874Z/`. La migration additive `governance.0021` et la reprise nominative ont été appliquées à la base active. Les lignes historiques présentes dans cette sauvegarde sont inchangées.

| Destination | Effectif rattaché |
|---|---:|
| SC-BAT | 31 |
| SC-OH | 27 |
| SC-IT | 22 |
| SC-GF | 17 |
| SC-SOCLE | 12 |
| **Total rattaché** | **109** |

La file d'examen contient **40 profils** : 11 issus du CTM 2, 28 sans CTM et un profil CTM 1 encore en statut `PENDING`. L’expert historique n° 6 est classé dans SC-GF parce que son affectation formelle CTM 1 / WG 1.1 est plus précise que le CTM 3 déclaré sur son profil. Cette priorité est enregistrée dans la provenance. La reprise ne crée aucun mandat ni droit.

Les sept SC, dont SC-ESS et SC-SE·GEO·RS sans rattachement direct, ainsi que la version d'organisation sont au statut `VALIDATED`. Les correspondances certaines effectivement utilisées sont validées ; CTM 2 et les hypothèses conditionnelles restent à examiner. SC-SOCLE conserve son intitulé provisoire. Aucun circuit Phoenix n'est activé. Les 8 CTM, leurs 7 affectations formelles, les 30 WG, les dossiers, pièces et historiques restent dans leurs tables d'origine. `/pilotage/organisation/` affiche, sous chaque SC, le nom complet, le CTM d’origine, le WG d’origine et la provenance de chaque classement.

Les écrans sont disponibles dans Pilotage :

- `/pilotage/organisation/` : référentiel 22/24, sept SC validées, experts nommés et correspondances historiques ;
- `/pilotage/organisation/gestion/` : organes, postes, GT, mandats, habilitations, rattachements et circuits ;
- `/pilotage/organisation/mise-en-service/` : contrôle de préparation, activation et suspension ;
- `/phoenix/` : dossiers, supervision, filtres, graphiques, journal et exports ;
- `/phoenix/dossiers/<id>/` : texte versionné, comparaison colorée, pièces, décisions, enquête et réunions.

L’ancien circuit reste accessible par ses routes habituelles. Les 30 WG, les 8 CTM, les postes historiques, les dossiers et leur historique ne sont ni renommés ni supprimés.

## Référentiel et coexistence

Les migrations additives `governance.0013` à `0017` et `norms.0012` ajoutent les versions d’organisation, organes, postes, GT, correspondances, mandats, délégations, habilitations, circuits, rattachements, dossiers, pièces, décisions, enquêtes, réunions et participations.

`Norme.circuit_version` vaut `LEGACY` pour les dossiers existants. Les gestionnaires historiques et l’API v1 continuent de ne voir que ces dossiers et exigent toujours CTM/WG. Un dossier `PHOENIX` peut avoir ces deux champs vides, mais sa création exige une organisation active, un circuit validé correspondant à cette organisation et un GT confirmé avec un rattachement documentaire daté. Aucun faux CTM/WG n’est utilisé.

Le référentiel chargé contient :

- 22 postes COPIL répartis en 4 présidence, 2 secrétariat, 7 membres, 3 invités et 6 appoints ;
- 24 postes ST, dont 4 de coordination et cinq pôles de 4 ;
- sept SC validées, avec SC-SOCLE conservée comme appellation provisoire ;
- 15 correspondances CTM et 24 correspondances WG vers des domaines candidats.

## Autorisations et circuit

Une action Phoenix est autorisée selon l’utilisateur actif, l’expert, le mandat daté, sa capacité, l’habilitation, le périmètre, l’organisation, le circuit, l’étape, le rattachement du dossier et l’état de suspension. Les anciens flags et rôles CTC/Pilotage ne deviennent pas automatiquement des droits Phoenix.

Les services vérifient côté serveur :

- nomination, délégation et habilitation en vigueur ;
- appartenance au bon GT, à la bonne SC ou à l’organe attendu ;
- version documentaire et numéro de révision attendus ;
- preuves exigées, enquête terminée et quorum d’acteurs distincts ;
- indépendance entre rédaction et contrôle ;
- capacités distinctes pour adoption, homologation et publication ;
- clé d’idempotence et unicité d’une décision par personne et étape.

Les retours créent une nouvelle étape sans effacer les décisions ni versions précédentes. La suspension bloque les écritures et conserve la consultation. Les notifications internes sont créées uniquement après validation de la transaction.

## Documents, supervision et traçabilité

Chaque modification produit un journal avec acteur, rôle, date, adresse IP, canal, cible et état avant/après. La supervision filtre les données avant de calculer les graphiques et permet de suivre qui a travaillé, sur quoi, quand et depuis quel contexte. Les pages d’historique montrent les changements de texte avec couleurs et échappement HTML.

Les pièces Phoenix sont stockées dans `.phoenix_documents`, hors du répertoire public des médias, avec permissions privées et empreinte SHA-256. Leur téléchargement repasse par le contrôle d’accès. Les versions documentaires, pièces et décisions sont immuables ; un changement produit un nouvel objet lié au dossier.

L’assistant IA ne reçoit que les dossiers accessibles à l’utilisateur. Son outil Phoenix prépare un lien de revue humaine et les exigences de la transition ; il ne signe aucune décision et ne peut ni activer une organisation ni contourner le service d’autorisation.

## API v2

`/api/v2/organisation/` fournit un contrat séparé de l’API v1 : référentiel, configuration, mise en service, liste et détail des dossiers, opérations, téléchargement protégé et exports CSV/PDF. L’interface web, l’API et les outils IA utilisent les mêmes services métier. Une transition envoyée par le client est toujours recalculée et contrôlée côté serveur.

## Sauvegarde et conservation

La commande `mon_env/bin/python manage.py backup_phoenix` produit une copie SQLite cohérente, une archive des médias et documents Phoenix privés, un manifeste d’empreintes et une restauration de contrôle. Le lot précédant l’application corrigée se trouve sous `.local_backups/phoenix-20261013T235035198874Z/`.
La sauvegarde finale de la structure appliquée et sa restauration vérifiée se trouvent sous `.local_backups/phoenix-20261014T000032480684Z/`.

La comparaison de référence porte sur 16 tables historiques. Le contrôle effectué juste avant et après la reprise confirme la conservation des identifiants et des valeurs historiques, en excluant seulement les colonnes additives de schéma et les champs de connexion volatils. Les 30 WG historiques restent présents.

La recette d’activation utilise uniquement la restauration isolée. Des comptes, nominations, GT et références marqués comme données de recette y ont permis de tester la chaîne complète, puis la suspension. Ils n’ont jamais été introduits dans la base principale.

## Validation

Les **33 tests ciblés Phoenix, sauvegarde, organisation et reprise d’experts** passent. Ils couvrent notamment la conservation du circuit historique, l’idempotence, la clôture sans suppression, la priorité de l’affectation formelle, l’exclusion d’un profil non actif, l’absence de droits créés et l’affichage nominatif avec CTM/WG d’origine.

Une recette avec navigateur réel a validé sur la copie isolée : configuration, activation avec quatre références, création d’un dossier sans CTM/WG, édition et comparaison colorée, refus d’une décision sans preuve, transition GT vers SC, graphiques et journal, affichage mobile, suspension et maintien de la lecture. Aucune erreur JavaScript n’a été relevée.

Commandes de contrôle :

```bash
mon_env/bin/python manage.py check
mon_env/bin/python manage.py makemigrations core norms governance --check --dry-run
mon_env/bin/python -m pytest tests/test_phoenix_operations.py tests/test_phoenix_backup.py tests/test_phoenix.py tests/test_supervision_history.py tests/test_ctc_supervision.py tests/test_pilotage_activity.py --no-migrations -q
```

## Informations requises pour la mise en service réelle

Le logiciel est prêt à recevoir les décisions, mais l’activation de la base principale doit attendre :

- le catalogue officiel des GT et leurs rattachements ;
- les titulaires, actes et périodes de nomination ;
- les fonctions encore inconnues des pôles ST ;
- les pouvoirs par poste, délégations et quorums ;
- le circuit approuvé, ses retours, preuves, enquêtes et références de décision ;
- les références d’adoption, d’homologation, de publication et de mise en service.

À réception, ces informations peuvent être saisies dans l’écran de gestion, contrôlées par le rapport de préparation, puis activées avec une trace complète. Jusqu’à cette étape, l’ancien circuit est le seul circuit réellement en vigueur.
