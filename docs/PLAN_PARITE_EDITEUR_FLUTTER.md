# Plan de parité de l’éditeur Flutter / Web

Référence : `templates/app/app.html`. Périmètre : espace expert, éditeur et messagerie.

## Diagnostic

- Clic dans le texte : masquer vote et IA/partage, élargir la saisie et permettre leur réouverture indépendante.
- Sélection souris/clavier/tactile : préremplir un extrait modifiable à droite, choisir un expert, envoyer et ouvrir le chat.
- Sauvegarde : remplacer le simple rechargement par une création réelle de version avec commentaire obligatoire ; conserver la saisie si erreur.
- Votes : charger les choix réels, permettre POUR/CONTRE/ABS, afficher répartition, taux, statut et émargement.
- IA : analyser, afficher résumé et changements avant/après, appliquer/ignorer ; rejeter les résultats devenus obsolètes.
- Groupes : afficher les groupes réels de la CTM ; identité et dates réelles.
- Responsive : supprimer les Expanded dans les colonnes non bornées, adapter en-tête, navigation et panneaux aux petits écrans.
- Brouillons : conserver texte/commentaire par document pendant la session et les changements d’onglet ; actualiser l’historique après sauvegarde.
- Ressources : liens Drive/Meet, références et pièces liées. Le web simule ces actions en mémoire ; stockage local explicite côté Flutter en attendant une API métier dédiée.

## Étapes

- [x] Éditeur adaptatif et mode saisie/lecture élargi.
- [x] Création de version réelle, validation, erreurs et conservation des brouillons.
- [x] Votes réels et registre d’émargement.
- [x] Analyse IA, détails, application et invalidation des réponses anciennes.
- [x] Sélection/extrait, destinataires et partage réel.
- [x] Messagerie : conversations, réponses, rafraîchissement et non-lus.
- [x] Groupes CTM, identité et dates.
- [x] Ressources locales persistantes et ouverture des liens.
- [x] Tests significatifs des parcours et analyse statique Flutter.

## Contrats API

- `POST /api/v1/norms/{id}/create_version/` : title, content, comment.
- `GET /api/v1/norms/{id}/votes/`, `POST /api/v1/norms/{id}/vote/` : FOR, AGAINST, ABSTAIN.
- `POST /api/v1/ia-agent/sessions/regulatory-advice/` : texte et contexte normatif.
- `GET /api/v1/messages/contacts/` : identifiant destinataire = user_id (pas identifiant expert).
- `GET/POST /api/v1/messages/`, `POST /api/v1/messages/mark_conversation_as_read/`.
- `GET /api/v1/experts/me/`, `GET /api/v1/wg/?ctm={id}`.

## Vérification attendue

Saisie → sauvegarde → rechargement ; conservation après erreur et changement de document ; sélection → extrait → partage → chat ; vote et compteurs ; IA et texte modifié pendant l’analyse ; affichage étroit et large.

## Implémentation et résultats — 26 octobre 2026

- `expert_editor_tab.dart` : saisie élargie au focus (souris ou clavier), réouverture indépendante des panneaux, extrait de sélection modifiable, sauvegarde HTTP réelle, vote et registre, IA détaillée, groupes CTM.
- `expert_screen.dart` : brouillons texte/commentaire conservés par document pendant la session, rechargement après sauvegarde/vote, protection contre les réponses de chargement arrivées dans le désordre. Un échec de chargement conserve le document actuel. Navigation documents en tiroir sur mobile et messagerie accessible aux petites largeurs.
- `expert_messaging.dart` : partage de clause vers `user_id`, ouverture du destinataire, conversations paginées, réponses, marquage lu, compteur des non-lus et rafraîchissement toutes les 8 secondes ; arrêt du rafraîchissement à la fermeture.
- `expert_resources.dart` : liens Drive/Meet et index de pièces accessibles par URL HTTP(S), persistés localement par compte et par document. Ouverture des liens dans une application externe. Il ne s’agit pas d’un téléversement de fichier ni d’une synchronisation cloud ; aucun endpoint dédié n’a été identifié dans l’API de normes.
- Le seuil de 75 % affiché reproduit l’indicateur web ; la promotion métier reste décidée par le serveur lors du vote.
- Les brouillons sont conservés en mémoire pendant la session de l’espace expert ; les ressources sont conservées sur l’appareil. Un brouillon propre ne masque pas une version serveur plus récente lors de la réouverture.

### Vérifications exécutées

- `flutter analyze` : **aucun problème** sur l’état final.
- `flutter test test/expert_editor_test.dart` : **12 tests réussis** sur l’état final : largeurs 390/704/1400, focus/réouverture, contrat de sauvegarde et erreur, brouillons multi-documents et démontage, vote réel, application IA, texte modifié pendant analyse, réponse IA après changement de document, groupes CTM, persistance locale isolée par compte, sélection → partage → conversation → réponse.
- `flutter test` : exécution élargie réalisée avant les trois derniers tests ajoutés, **43 réussis / 3 échecs**. Les trois échecs concernent `expert_data_smoke_test.dart:195` (profil aux trois dimensions) : attente de `CTM 1 — Normes électriques`, alors que le profil utilise les noms fournis par `my-affiliation` (`Sous-commission initiale` dans cette fixture). Le profil et ces tests existants n’ont pas été modifiés dans cette intervention.
- Tests réseau réalisés avec un adaptateur Dio simulant les réponses de l’API ; le parcours sur serveur authentifié et l’ouverture d’une application externe restent à vérifier manuellement.

### Correction des erreurs restantes

- Tests du profil : attente explicite du chargement de l’affiliation, puis vérification de l’identifiant CTM sélectionné et du libellé fourni par `my-affiliation`, au lieu de l’ancien `ctm_name`.
- Tests de thème du pilotage : vérification du passage du thème clair initial au thème sombre.
- Correction d’un crochet de liste mal placé dans la barre supérieure du pilotage et des problèmes d’analyse statique signalés lors de la relance.
- Résultat final après ces corrections : **`flutter test` — 49 tests réussis, aucun échec** ; **`flutter analyze` — aucun problème**. Ce résultat remplace le bilan partiel précédent.
