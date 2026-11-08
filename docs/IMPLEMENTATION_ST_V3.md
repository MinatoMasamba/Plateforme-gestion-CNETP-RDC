# Backend ST v3 — nominations, PTN, finances et confirmations

## État en local

La bascule ST v3 a été appliquée par `reset_st_access --apply` : 32 anciennes
adhésions rendues inactives et 10 indicateurs `is_ctc_staff` retirés.
Les comptes et anciennes affectations sont conservés ; aucune attribution v3
n’a été effectuée en production locale. Le compte administrateur conserve ses
droits d’administration, sans nomination automatique au ST.

Les anciens postes et adhésions restent consultables dans l’admin mais ne
peuvent plus être attribués par les formulaires historiques. La sélection de
postes dans « Nominations CTC » utilise les 19 postes v3. Les mandats confirmés
et leurs dates déterminent l’accès au ST. Le changement ST est indépendant de
la version globale Phoenix : il n’active pas les circuits ou habilitations v2.

## Attributions

Dans l’admin Django : `/admin/governance/nominationctc/add/`.
Choisir l’expert, son poste v3, la capacité ORGANISATION, la référence officielle,
la date de début et le statut ACTIVE. Une personne sans compte certain reste
sans mandat. Les contrôles refusent un poste occupé et les doublons d’un lot.

Neuronne dispose de `list_st_posts` et `assign_st_posts`, exclusivement utilisables
par un administrateur staff autorisé aux nominations. Un compte admin sans
profil expert peut les utiliser dans le contexte Expert de l’assistant.
La liste doit indiquer email exact ou expert_id, post_code, start_date et
appointment_reference. `apply=false` vérifie ; `apply=true` active les mandats.
Les noms du référentiel ne sont jamais rapprochés automatiquement des comptes.
L’activation envoie l’e-mail de nomination via le signal post_save, comme toute nomination enregistrée dans l’admin ou la console.

Exemple de message à Neuronne, à compléter avec un compte réel :
« Attribue ST-V3-12 à [email exact], à compter du 2026-10-31, référence :
[référence officielle de nomination]. » Un nom seul est insuffisant.

## API serveur

Racine : `/api/v1/st/records/` ; session/CSRF ou authentification API configurée.

- GET/POST racine : travaux accessibles / préparation d’une première version.
- GET `/<id>/` : versions et décisions conservées.
- POST `/<id>/revise/` : nouvelle version, avec la révision courante.
- POST `/<id>/confirm/` : revision, decision CONFIRMED/REJECTED, comment obligatoire.
- GET `/posts/` et POST `/nominations/` : opérations administrateur uniquement.
- GET `/ptn-register/` : dernière version confirmée de chaque PTN.
- GET `/finance-summary/` : montants enregistrés, séparés par devise et mouvement.
- GET `/audit/` : journal ST réservé aux co-chefs juridiques, sans leurs propres actions.

Les contenus PTN et WORK sont conservés avec titre, contenu et référence source.
Un FINANCE ajoute amount décimal positif, currency (CDF/USD/EUR), movement
(ENGAGEMENT/DEPENSE), operation_date. Les données sont préparées par le membre
compétent et confirmées uniquement par le chef de son pôle ; chacun des deux
co-chefs du pôle 3 peut confirmer. Une révision obsolète ou une seconde décision
renvoie 409. Les versions et décisions ne sont pas éditables via l’API ou l’admin.

Les totaux du nouveau registre financier utilisent seulement la dernière version
confirmée de chaque écriture. Les cotisations, paiements et jetons historiques
sont lus depuis les tables existantes, séparément : leur devise n’étant pas
renseignée, ils ne sont jamais additionnés aux nouveaux montants par devise.
Leur provenance n’est pas certifiée par cette implémentation (`verified_for_st_v3=false`).
Aucun montant de démonstration n’est injecté dans la nouvelle API.

## Limites et vérification

Ce lot est backend uniquement : aucun nouveau template ou code Flutter modifié.
Les anciens écrans financiers ne consomment pas encore les nouvelles API.
La présence d’un PTN confirmé ne démontre pas à elle seule la complétude du registre.
Le dépôt binaire GED, les alertes à quatorze jours et la totalité des circuits SC
restent des travaux distincts de ce lot.

Migration additive : governance 0036. Tests dans `tests/test_st_backend_operations.py` :
retrait des accès sans suppression, nominations par admin et Neuronne, absence
d’envoi email, dates des mandats, PTN et historique, co-chefs, montants invalides,
conflits de révision, périmètres et audit. Les données des tests sont isolées.

## Résultats de vérification

100 tests de non-régression ont passé, puis 21 tests backend après les derniers
contrôles de périmètre, et les deux tests finaux de confirmation financière
(ensembles se recouvrant). Ruff, manage.py check et la vérification des migrations
governance passent. Le serveur local rechargé renvoie HTTP 403 à un ancien compte
CTC authentifié sur le tableau de bord API. La base confirme zéro mandat v3 actif,
zéro ancienne adhésion active, zéro indicateur CTC actif et 32 adhésions historiques
conservées. Rapport : reports/st_backend_verification.json. Aucun poste réel
n’a été attribué pendant ces vérifications.
