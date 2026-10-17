# Alignement de la CNE-ITP sur le rapport adopté du 15 octobre 2026

## Source et méthode

Source prioritaire : `RAPPORT DES RAVAUX DE RÉORGANISATION DE LA CNE-ITP 15-10-2026 VERSION ADOPTEE.docx`, SHA-256 `8e38cb2e68dd147650999b4072d782cf90227556f0f57c7e8aee7d8269d25ec6`. Les sections 2, 3, 4, l'annexe 1 et la déclinaison opérationnelle des tomes 0 à 6 ont été lues avant les changements. Le communiqué n°002 du 16 octobre 2026 n'était pas présent dans le projet et n'a pas été utilisé comme source de données.

Le catalogue JSON vérifié est livré avec le code. Le DOCX original reste archivé séparément ; lorsqu'il est présent à la racine, son empreinte est contrôlée avant toute préparation ou affectation.

La base inspectée est le fichier SQLite local `db.sqlite3` au 17 octobre 2026. Ses chiffres ne sont pas présentés comme ceux de la production. Les identifiants CTM/WG, les documents, les décisions et les affectations antérieures sont conservés.

## Écarts relevés avant adaptation

| Sujet | Rapport adopté | Application locale avant adaptation | Suite donnée |
| --- | --- | --- | --- |
| Gouvernance centrale | 22 postes COPIL ; 24 postes du Secrétariat technique, dont cinq pôles de quatre | Ancien référentiel Phoenix : 22 et 24 postes, mais application de coordination encore fondée sur les 20 postes CTC historiques ; page publique à 27/20 | Nouvelle version séparée à 22/24 ; page publique et en-tête corrigés. Les autorisations historiques restent à revoir poste par poste. |
| Sous-commissions | Sept tomes 0 à 6 | Ancienne version Phoenix à sept SC aux domaines partiellement différents, notamment SC-ESS et SC-SE·GEO·RS ; base CTM courante à sept enregistrements déjà remaniés | Sept SC créées dans une nouvelle version, avec les noms du rapport. Aucun CTM historique n'a été renommé ou supprimé. |
| Groupes de travail | Cinq GT par tome, 35 au total | Aucun `GroupeCible` dans l'ancienne version | 35 GT créés avec leur mission issue de la déclinaison opérationnelle. Le tome 4 est pris dans cette partie détaillée, bien qu'il manque dans la première énumération de la section 4. |
| Bureaux des SC | Fonctions et certains noms proposés dans l'annexe 1 | Pas de postes de bureau SC dans le référentiel cible | 30 postes de bureau préparés. Quatorze titulaires uniques ont ensuite été placés sur leurs postes par confirmation utilisateur, sans habilitation ni activation de circuit. |
| Experts | Le texte cite 143 fiches ; le tableau totalise 145 | 149 fiches locales, cinq groupes de noms identiques ; 298 lignes d'affectation de l'ancienne version, dont des lignes clôturées ou annulées | Audit nominatif en lecture seule. Aucun rattachement définitif à la nouvelle version n'est déduit d'un nom ou d'un CTM remanié. |
| Circuit | Orientation COPIL, organisation ST, élaboration GT/SC, contrôle ST, retour éventuel, soumission COPIL, suite institutionnelle | Circuits historiques CTC/Pilotage opérationnels et circuit Phoenix distinct | Parcours public mis à jour ; les transitions serveur historiques sont conservées. Le circuit cible reste à paramétrer, vérifier et autoriser avant activation. |

Le rapport ne précise pas dans les passages examinés la fréquence des réunions du COPIL ; la mention « deux fois par an ou en cas de besoin » provient de la consigne de mise à jour. L'annexe 1 se présente elle-même comme une **proposition d'affectation**. Le tome 4 porte encore la mention « Proposition d'expert » et ses fonctions nominatives restent vacantes.

## Référentiel intégré

| Tome | Code interne | Intitulé repris du rapport | GT |
| --- | --- | --- | ---: |
| 0 | SC-SOCLE | Matériaux & Essais / Socle Commun | 5 |
| 1 | SC-IT | Infrastructures de Transport | 5 |
| 2 | SC-GF | Géotechnique & Fondations | 5 |
| 3 | SC-OH | Ouvrages Hydrauliques | 5 |
| 4 | SC-VRD | Réseaux Divers (VRD), Équipements & Fluides (Proposition d'expert) | 5 |
| 5 | SC-ENV | Environnement, Santé & Sécurité | 5 |
| 6 | SC-BAT | Bâtiments Courants & Spéciaux | 5 |

Le catalogue complet, avec les 35 dénominations et missions exactes, est dans `apps/governance/rapport_adopte_2026_reference.json`. Les codes internes servent à distinguer les enregistrements et ne remplacent pas les intitulés du rapport.

La version `reorganisation-2026-10-15` reste `PROPOSED`. Elle contient 22 postes COPIL, 24 postes ST, 30 postes de bureau SC, sept SC et 35 GT. Après confirmation explicite de l'utilisateur le 17 octobre 2026, les 14 titulaires retrouvés de façon unique et dont le compte est actif ont été affectés à leurs postes par `affecter_bureaux_sc_rapport`, avec cette instruction comme référence et le 17 octobre 2026 comme date d'effet. Les 7 noms absents de la base, le nom homonyme et les 8 postes sans nom restent vacants. Il s'agit d'une affectation applicative fondée sur la confirmation utilisateur, sans prétendre qu'un acte officiel distinct a été produit. La version contient zéro habilitation et zéro affectation SC d'expert confirmée. Les anciens circuits continuent donc à fonctionner sous leurs contrôles existants.

## Rapprochement des experts

L'annexe 1 contient 118 lignes nominatives exploitables : 101 lignes correspondent à une fiche unique par nom normalisé, 12 n'ont pas de correspondance exacte et cinq correspondent à deux fiches homonymes. Les 101 lignes appariées concernent 100 fiches distinctes ; une fiche est citée dans deux sous-commissions. Il reste 99 fiches candidates à une seule SC **pour examen**, sans affectation confirmée. Parmi les 30 postes de bureau, 14 titulaires sont retrouvés de manière unique, sept noms sont absents, un est ambigu et huit postes n'ont pas de titulaire indiqué.

Les cinq paires de noms identiques dans la base ne sont pas automatiquement fusionnées. Le passage de 149 fiches locales à 143 ou 145 personnes n'est donc pas démontré. Le tableau du rapport additionne 119 experts répartis et 26 sans CTM, soit 145, mais l'annexe détaillée contient 118 lignes réparties ; le tome 6 y compte 30 lignes contre 31 dans le tableau. Aucun effectif n'est retenu comme nombre définitif de personnes distinctes.

Les experts choisissent eux-mêmes leur GT dans le formulaire de mise à jour du profil. Ce choix est stocké en statut `REVIEW`, sans changement d'affectation ou de droit. L'inscription ne crée plus de mandat COPIL/ST ni d'affectation CTM/WG par simple déclaration.

## Sauvegarde, contrôle et retour arrière

Sauvegarde locale initiale : `.local_backups/phoenix-20261017T124722148808Z/`. Une seconde sauvegarde vérifiée avant l'affectation des postes est dans `.local_backups/phoenix-20261017T133425352535Z/`. La restauration isolée de la base et des médias a été vérifiée. Le manifeste des tables historiques était identique après le chargement initial. `PRAGMA integrity_check` retourne `ok` et `PRAGMA foreign_key_check` ne signale aucune violation.

Les migrations d'étiquettes `ia_agent.0009_coordination_labels` et `meetings.0005_alter_reunion_type` ont aussi été appliquées. `makemigrations --check --dry-run` signale encore la modification préexistante et sans rapport du fournisseur `AgentSession.provider` dans `ia_agent` ; elle n'a pas été incorporée à ce lot.

La commande `prepare_rapport_adopte` est idempotente et crée les 35 GT. `prepare_mandats_rapport` prépare les fonctions nominatives ; `affecter_bureaux_sc_rapport --decision-reference ... --effective-date ...` place les titulaires uniques et actifs directement sur leurs postes sans créer de droits. Elle est idempotente : une seconde exécution a retourné 14 `deja_affecte`. `audit_rapport_adopte` fournit les comptes de rapprochement sans écrire en base. Pour annuler les seules données nouvelles, conserver la base sauvegardée et utiliser une procédure de restauration contrôlée ; ne pas supprimer les lignes historiques ni appliquer un retour arrière SQL improvisé si d'autres écritures ont eu lieu depuis la sauvegarde.

Les contrôles ciblés passent : 35 tests Phoenix/organisation/expert existants, puis quatre tests sur le catalogue adopté et le choix expert ; un dernier test vérifie qu'une ancienne version activée n'empêche pas le formulaire d'utiliser les GT du rapport. `manage.py check` et `git diff --check` passent. La compilation du gabarit et l'interaction visuelle en navigateur restent à confirmer dans un environnement qui permet d'ouvrir l'application.

## Décisions et vérifications restantes

- Fournir un acte institutionnel si la référence de confirmation utilisateur doit être remplacée par une référence officielle ; résoudre les homonymes et les absences de la base sans rapprochement approximatif.
- Qualifier les correspondances entre les CTM remaniés de la base actuelle et les tomes officiels. Le rapport décrit huit CTM antérieurs, tandis que cette base locale en contient sept déjà renommés. Une égalité physique d'identifiants CTM/SC serait trompeuse ; l'équivalence de présentation « tome = SC = CTM courant » doit être vérifiée dossier par dossier sans réécrire l'historique.
- Définir et tester les habilitations des 22 postes COPIL et 24 postes ST, puis le circuit de dossiers cible et ses retours de correction. Aucun droit n'est accordé par le simple choix d'un GT ou la proposition d'un poste.
- Vérifier en navigateur les écrans Experts, Coordination et COPIL sur ordinateur et mobile. L'environnement de cette session ne fournit pas de navigateur pilotable.
- Obtenir le communiqué officiel n°002 du 16 octobre 2026 si une confrontation complémentaire de ses dispositions est nécessaire.

## Supervision Pilotage du 17 octobre 2026

`/pilotage/activites/` utilise désormais un en-tête de type Bureau Directoire, sans navigation publique « Accueil / À propos / Contact », avec une barre latérale accessible sur ordinateur et mobile. Le tableau « Avancement pondéré par semaine » reste visible même lorsque le graphique externe n'est pas disponible : semaines lisibles, défilement horizontal et absence de données indiquée explicitement. La vue affiche les sept SC du rapport et leurs cinq GT, sans doubler les sept anciennes SC Phoenix. Les mesures historiques sont associées à un CTM uniquement lorsque son numéro **et son nom exact dans cette base locale** correspondent à la table de lecture vérifiée ; elles portent alors le badge « Mesures historiques CTM ». Aucune tâche historique n'est réattribuée aux nouveaux GT.

La fiche `/pilotage/sous-commissions/courantes/28/activite/` a été vérifiée avec un client Django authentifié : HTTP 200, cinq GT affichés et titulaire du poste de président visible. Le gabarit n'essaie plus de lire le champ `number` sur un `GroupeCible`. Les trois tests ciblés du référentiel, de l'affectation et de la nouvelle navigation Activités passent. La suite Activités plus large a deux échecs préexistants distincts : une attente sur les minutes observées et un ancien lien `/phoenix/` devenu 404 ; ils ne sont pas présentés comme une validation complète de cette suite.

La page `/pilotage/activites/` présente maintenant l'identité « Ministère des Infrastructures et Travaux Publics / Comité de pilotage », un fil d'Ariane et des filtres de période alignés. Sa barre latérale commande cinq vues distinctes : vue globale, sous-commissions, tendance hebdomadaire, charge planifiée et données personnelles. Les cartes de la vue globale utilisent les anneaux de progression déjà présents dans la charte de la Coordination ; aucune valeur manquante n'est transformée en zéro. Le rendu serveur a confirmé une seule vue visible pour chaque sélection et le maintien du choix lors du filtrage. La vérification visuelle en navigateur reste impossible dans cette session, faute de surface pilotable.
