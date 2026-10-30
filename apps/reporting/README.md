# Rapports CNE-ITP — mise en service

L’interface est accessible à `/ctc/rapports/`. Elle comprend les modèles N1–N4, M1–M3, F1–F4, C1–C3, ITP-01–04, les rapports de pôles P1–P9 et les examens spécialisés S-*. Le catalogue est défini dans `catalog.py` ; ces intitulés sont des modèles de travail, pas des actes institutionnels.

Après un déploiement avec `DEBUG=False`, exécuter `python manage.py collectstatic --noinput` puis redémarrer le processus Django/Daphne : WhiteNoise charge l’inventaire des fichiers statiques au démarrage. Le style des rapports est fourni par `templates/static/css/reporting.css`.

## Activation des droits

Les rapports restent indisponibles sans `OrganisationVersion` en vigueur. Aucun mandat ou poste proposé ne donne accès. Pour chaque agent :

1. Confirmer son `MandatOrganisation` du Secrétariat technique et sa référence d’acte.
2. Enregistrer une `HabilitationAction` explicite, datée et activée, sur le périmètre ST ou ST_POLE : `rapport.consulter`, `rapport.rediger`, `rapport.controler`, `rapport.approuver` ou `rapport.transmettre` selon les responsabilités confirmées. Le formulaire Phoenix de gestion des habilitations permet de le faire.
3. Dans l’administration Django, associer à chaque habilitation les `ReportTypePermission` nécessaires et les activer. L’administration de ce modèle exige `governance.manage_phoenix` ; chaque changement est consigné dans `JournalMigration`.

Les droits sont vérifiés à chaque requête. Les droits de contrôle exigent un poste `POLE_HEAD` distinct du préparateur. L’approbation exige `ST-COORD-01`. Un rapport central requiert une habilitation de périmètre ST. Un rapport de pôle reste limité au pôle ou au périmètre ST. L’approbation par le préparateur principal est signalée dans le journal et l’export.

## Saisie et validation

Le préparateur choisit un modèle et renseigne chaque rubrique par saisie manuelle avec sa source, ou sélectionne explicitement une proposition issue des objets enregistrés. Les propositions ne constituent pas une validation métier. Une pièce justificative est exigée ; les rapports financiers exigent une ligne liée à une norme ou une tâche et à une pièce. Les montants du tableau de démonstration CTC ne sont jamais lus.

Le circuit est `brouillon → soumis → contrôlé → approuvé`, avec renvoi et rejet. Chaque changement produit un `ReportEvent`. Une approbation fige les champs et les références utilisées ; une nouvelle version est créée séparément. Les exports PDF et Word sont disponibles après approbation. La remise à un destinataire externe est manuelle et son bordereau est consigné, sans envoi automatique.

Les fichiers justificatifs sont privés dans `.report_documents` et accessibles par une route contrôlée. Taille maximale : 20 Mo ; formats admis : PDF, DOC, DOCX, XLSX, PNG et JPEG.

## Conditions avant une formation sur données réelles

- Valider officiellement les mandats, les habilitations par modèle et les destinataires ; la base locale du 28 octobre 2026 possède un référentiel Phoenix `VALIDATED` et un référentiel `PROPOSED`, mais aucun `ACTIVE`, donc l’interface affiche son indisponibilité.
- Vérifier les sources proposées rubrique par rubrique. Les rubriques sans source systémique doivent être saisies et justifiées.
- Faire approuver les modèles et la couverture PDF/Word par la coordination. Leur mise en page s’inspire de `doc/Fiche_formation_formateur_Eddy_Masamba_CNE-ITP(2).pdf` ; aucun chiffre ou texte de cette fiche n’est repris comme donnée actuelle.
- Raccorder une source comptable certifiée avant d’utiliser F3/S-GAF pour un état financier officiel. Pour l’instant, les lignes financières sont des saisies justifiées par des pièces et ne prouvent aucun paiement.
