# Connexion des onglets expert et adhésions

## Diagnostic

Les onglets Experts & Groupes, Réunions & Votes, Cotisations & Indemnités,
Processus ISO, Bureau légistique et Notifications étaient des écrans statiques.
Le bouton d’adhésion et son compteur étaient absents. Les API d’adhésion
reconnaissaient les anciens responsables CTM mais pas les mandats SC utilisés
par le profil.

## Travaux

- Bouton Adhésions permanent dans la navigation et depuis Experts & Groupes,
  compteur serveur, demandes, affectation WG obligatoire, acceptation, refus motivé.
- Autorisations d’adhésion alignées sur `ctm_bureau_ids` : mandats SC confirmés et
  correspondance CTM existante, anciens responsables CTM, secrétariat technique.
  Vérification du groupe et de la CTM de candidature avant activation.
- Experts & Groupes : annuaire et groupes réels, recherche, membres, responsables,
  dernières normes, fiche expert et messagerie pour les contacts autorisés.
- Réunions : liste réelle, planification par le bureau, détails, lien Meet,
  présences, émargement, votes, clôture et lecture du PV.
- Finances : tableau de bord, cotisations, paiements, reçus, indemnités ; déclaration
  de paiement ; confirmation/refus et liquidation pour les profils CTC autorisés.
- ISO : phases serveur, votes, suivi CTC, consultation des normes publiques,
  ouverture dans l’éditeur, PDF authentifié, changement de phase réservé au CTC.
- Légistique : autorisation serveur, dossiers réels, texte, prise en charge,
  validation avec texte et commentaire.
- Notifications : liste réelle et marquage individuel/global comme lu.
- Reçus PDF : téléchargement authentifié depuis la fiche d’un paiement, limité au
  personnel CTC ou à la structure concernée.
- Reçus d’indemnités : PDF accessible au bénéficiaire et au personnel CTC, avec
  statut de paiement et état de la contestation ; un jeton non payé est explicitement
  distingué d’un virement effectué.
- Indemnités : le bénéficiaire peut contester un jeton avec un motif ; le bureau CTC
  instruit la contestation (acceptation ou refus motivé), avec horodatage et auteur.
- Mandatement : export ISO 20022 `pain.001.001.03` des jetons en attente, réservé
  au personnel CTC, avec contrôle préalable des coordonnées bancaires.
- Chargement, pagination, erreurs et réessai dans chaque module. Les formulaires
  restent ouverts avec leur saisie en cas de refus serveur.

## Configuration du mandatement

### Endpoints financiers

- `GET /api/v1/paiements/{id}/receipt/` : reçu PDF du paiement.
- `GET /api/v1/jetons/{id}/receipt/` : reçu PDF de l’indemnité.
- `POST /api/v1/jetons/{id}/contest/` : `{motif}` (10 caractères minimum).
- `POST /api/v1/jetons/{id}/resolve_contestation/` :
  `{decision: ACCEPTED|REJECTED, resolution}`.
- `GET /api/v1/jetons/sepa_export/?ids=1,2&execution_date=2026-10-27` :
  export XML ; les paramètres sont facultatifs.

Les champs de contestation sont en lecture seule dans les serializers : les
changements d’état passent par les actions métier dédiées.

### Compte débiteur

Renseigner dans `.env` avant d’utiliser l’export bancaire :

```text
CNETP_SEPA_DEBTOR_NAME=CNETP
CNETP_SEPA_DEBTOR_IBAN=<IBAN du compte CNETP>
CNETP_SEPA_DEBTOR_BIC=<BIC 8 ou 11 caractères>
CNETP_SEPA_CURRENCY=USD
```

Sans ces valeurs, l’API répond explicitement que le mandatement n’est pas configuré.
Chaque expert concerné doit aussi avoir une banque et un compte renseignés dans son
profil ; sinon l’export liste les dossiers incomplets et n’émet aucun fichier partiel.

## Limites restantes

- La reconnaissance des mandats SC utilise le même rapprochement SC/CTM que le
  profil ; une SC sans correspondance CTM ne donne pas accès aux candidatures
  historiques CTM. Aucun nouveau droit n’est accordé par le seul affichage du bouton.
- Les règles de transition ISO et les permissions finales restent celles du serveur.

## Vérification

- `flutter analyze` : **aucun problème**.
- `flutter test` : **67 tests réussis** sur l’état final.
- `flutter test test/expert_modules_test.dart` : **12 tests réussis**, dont l’accès
  au bouton d’adhésion sur une largeur de 390 pixels sans défilement des onglets.
  Couverture : WG obligatoire, échec d’acceptation et conservation du formulaire,
  acceptation, refus motivé, droits d’un membre ordinaire, annuaire, émargement/vote,
  paiement, contestation et instruction d’une indemnité, présence des exports PDF et
  pain.001, notifications, changement de phase ISO et prise en charge légistique.
- `mon_env/Scripts/python.exe -m pytest tests/test_expert_admissions_api.py tests/test_mobile_affiliation.py -q` :
  **13 tests réussis**. Couverture des quatre fonctions du bureau SC avec mandat
  actif, retrait des droits après fin du mandat, séparation entre CTM, validation
  du WG et activation unique, traçabilité du refus et non-régression des affiliations.
- `mon_env/Scripts/python.exe -m pytest tests/test_payments_exports.py -q` :
  **11 tests réussis**. Couverture des reçus PDF de paiement et d’indemnité, des
  restrictions par structure ou bénéficiaire, des champs de contestation en lecture
  seule, de la contestation par le bénéficiaire, de l’instruction CTC, de l’export pain.001,
  des identifiants sélectionnés, des coordonnées manquantes et de la configuration
  incomplète du compte débiteur.
- `manage.py check` et `makemigrations --check --dry-run` : aucun problème, aucune
  migration manquante après l’ajout des champs de contestation.
- Exécution élargie avec `tests/test_president_sc.py` : **15 réussites et un échec
  d’environnement** dans le test navigateur existant, qui tente de lancer
  `/usr/bin/google-chrome` sur Windows. Les assertions serveur SC passent.
- Les parcours Flutter sont testés avec un adaptateur HTTP simulé ; les tests Django
  exécutent réellement les vues et les mutations sur la base de test.
