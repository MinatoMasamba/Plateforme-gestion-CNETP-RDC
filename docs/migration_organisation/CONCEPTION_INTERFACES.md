# Conception des cinq interfaces du Comité de pilotage

Date : 12 octobre 2026. Statut : spécification fonctionnelle et technique, sans modification des écrans actifs.

**Archive de conception historique :** ce document décrit les 27 anciens postes. Pour la cible Phoenix à 22 postes COPIL, consulter la [nouvelle conception Phoenix](CONCEPTION_INTERFACES_PHOENIX.md) et le [plan mis à jour](../../PLAN_MIGRATION_ORGANISATION.md). Les regroupements ci-dessous ne sont pas repris automatiquement comme interfaces ou permissions cibles ; leur contenu est conservé pour préserver le contexte de préparation.

Cette conception applique le regroupement demandé pour les 27 postes du référentiel actuel. Les intitulés proviennent du référentiel local et de sa commande de peuplement ; ils ne certifient pas la composition officielle d’octobre. La nouvelle organisation restera indiquée comme proposée tant qu’elle n’est pas adoptée.

## 1. Architecture commune de présentation

Une enveloppe partagée dessert cinq compositions de modules. Il n’est pas prévu de reproduire 27 applications ni cinq copies de la navigation. Les différences portent sur le contenu utile, les files de travail et les actions effectivement autorisées pour chaque mandat.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Comité de pilotage   [Poste et mandat sélectionnés]   Recherche Profil │
├───────────────────┬──────────────────────────────────────────────────┤
│ Tableau de bord   │ Intitulé de l’interface                           │
│ Mes dossiers      │ Fonction et périmètre du poste                     │
│ Documents         │ [À examiner] [Échéances] [Demandes]                │
│ Avis / décisions  ├──────────────────────────────────────────────────┤
│ Instances         │ File de travail filtrée par droits                │
│ Correspondances*  │ Référence | Objet | Étape réelle | Échéance        │
│ Historique        ├──────────────────────────────────────────────────┤
│                   │ Dossier sélectionné                               │
│                   │ Pièces | Versions | Avis | Parcours | Historique   │
│                   │ Action autorisée, si elle existe pour ce mandat   │
└───────────────────┴──────────────────────────────────────────────────┘
```

`*` Le registre de migration relève d’une habilitation dédiée, pas de l’interface seule. Les noms techniques des versions d’organisation et des moteurs restent dans les vues d’administration ; les écrans métier utilisent « Organisation en vigueur », « Organisation proposée » et « Origine du dossier ».

Composants partagés à prévoir : barre d’identité et mandat, navigation, recherche, indicateurs, liste de dossiers, lecteur documentaire, historique de versions, fil des avis, parcours daté, formulaire de décision, dépôt de pièce, demandes d’accès, états vides et notifications. Les indicateurs et résultats sont calculés sur le périmètre consultable, sans exposer les dossiers inaccessibles par leurs nombres ou titres.

Une action sensible présente le dossier, sa version examinée et la portée de la décision ; elle demande le motif et la référence justificative quand la règle métier l’exige. Les composants utilisent les actions permises calculées par le serveur. Le handler recontrôle ces permissions avant toute écriture.

## 2. Les cinq interfaces

| Interface | Postes | Question métier principale | Modules prioritaires |
|---|---|---|---|
| Direction et validation | 1–5 | Que dois-je orienter, arbitrer ou valider maintenant ? | Cadrages, mandats, réception des dossiers transmis, avis consolidés, décisions et suivi des résolutions. |
| Coordination institutionnelle | 6–12 | Quelles contributions et échéances dois-je coordonner ? | Contributions institutionnelles, calendrier, rapports, suivi des sollicitations et observations. |
| Conformité et réglementation | 13–17 | Quelles obligations et réserves restent à examiner ? | Pièces de conformité, avis spécialisés, réserves, références réglementaires et suivi des corrections. |
| Contrôle technique et financier | 18–22 | Quels contrôles relèvent de mon mandat et de mon domaine ? | Dossiers de spécialité, avis techniques, essais, réserves et contrôles financiers autorisés. |
| Partenaires et expertise | 23–27 | Quel avis spécialisé dois-je apporter ? | Consultations assignées, contributions sectorielles, pièces, réponses et suivi des observations. |

### Direction et validation — postes 1 à 5

Accueil : dossiers nécessitant une action du poste connecté, échéances et réceptions à effectuer. La supervision globale et les demandes d’accès sont des modules partagés, affichés selon les droits actuels. La file distingue « à réceptionner », « à examiner » et « décision enregistrée ».

Pour les dossiers historiques, conserver la distribution actuelle : le Président ouvre et valide en fin de cadrage ; les deux Vice-Présidents traitent leurs validations et quitus respectifs ; le Secrétaire formalise le mandat et vérifie le PV ; le Rapporteur programme les échéances. Président et Rapporteur accusent chacun réception de la transmission CTC. Les étapes du cadrage et les deux signatures ne sont pas remplacées par un bouton générique « Valider ».

Le verrou de plateforme reste réservé au Président selon la règle actuelle. L’appartenance à cette interface ne rend pas cette action accessible aux quatre autres postes. Les futurs pouvoirs COPIL restent désactivés jusqu’à confirmation.

### Coordination institutionnelle — postes 6 à 12

Accueil : contributions attendues de l’institution du mandat, dossiers suivis et jalons à venir. Modules : fiche de contribution, dépôt de rapport, observations datées et suivi de réponse. Les postes 6 et 7 restent distincts même s’ils partagent une institution et un rôle.

La planification et le suivi institutionnel ne constituent pas la programmation souveraine du Rapporteur. Les éventuelles actions nouvelles de dépôt ou d’avis ne seront activées que si leur contrat serveur et leurs habilitations sont confirmés. Préserver les accès de supervision existants sans déduire une permission de signature.

### Conformité et réglementation — postes 13 à 17

Accueil : réserves et pièces à examiner dans le périmètre du poste. Le poste 13 suit les sujets environnementaux, le 14 les sujets fonciers, le 15 les enjeux territoriaux/ITP de Kinshasa ; ces domaines sont des axes de présentation proposés, pas de nouveaux pouvoirs. Les postes 16 et 17 reçoivent les modules juridiques et légistiques compatibles avec leurs droits confirmés.

Partager lecteur, avis et registre de réserves. Séparer clairement une observation sectorielle, un contrôle documentaire et une validation réglementaire. Le déplacement des postes 13–17 depuis l’ancien espace commun des conseillers ne donne pas aux postes 13–15 les actions des juristes.

### Contrôle technique et financier — postes 18 à 22

Accueil : dossiers de spécialité, examens et réserves. OR, OVD et ACGT disposent de vues techniques contextualisées ; BTC reçoit les modules d’essais et de contrôle ; FONER reçoit le module financier selon ses permissions. Le domaine d’affichage est issu du mandat confirmé, avec l’ancien mapping de spécialités conservé pour l’ancien circuit jusqu’à sa révision.

Le code actuel possède `templates/pilotage/app_atf/app.html`, mais ce fichier porte encore le titre Bureau Directoire et inclut ses composants 1–5. Lors de la réalisation, remplacer cette composition par les modules de contrôle appropriés et une enveloppe réellement partagée. Cette constatation porte sur les inclusions du template ; elle ne prouve pas que les handlers accordent les droits du Directoire aux ATF.

### Partenaires et expertise — postes 23 à 27

Accueil : consultations auxquelles le poste est associé, date attendue et statut de la contribution. Modules : avis spécialisé, justificatifs et suivi des réponses. ONA : expertise architecturale ; poste 24 : sujets de représentation/régulation selon mandat ; BEAU : aménagement ; FEC : contribution privée/industrielle ; OCC : contribution de contrôle/métrologie selon mandat.

Préserver les restrictions actuelles sur les décisions administratives. Un avis industriel FEC au COPIL reste distinct d’un examen `IndustrialConsultation` assigné à un membre CTC ; partager l’identité d’institution ne permet pas de traiter l’examen à sa place. L’ancien alias SCOT → OCC peut aider à interpréter le référentiel historique, mais il ne doit pas devenir une preuve d’habilitation future.

## 3. Couverture des 27 postes

Cette table définit l’interface d’accueil, pas une matrice d’octroi de droits. Les actions historiques indiquées sont celles identifiées dans le code ; les modules proposés demeurent sans nouveau pouvoir de validation tant que les mandats ne sont pas confirmés.

| Poste | Fonction du référentiel actuel | Interface | Particularité à préserver |
|---:|---|---|---|
| 1 | Président | Direction et validation | Orientation, validation finale, réception et verrou selon règles actuelles. |
| 2 | Vice-Président ONIC | Direction et validation | Validation et quitus ONIC distincts du deuxième VP. |
| 3 | Vice-Président AIBTP | Direction et validation | Validation et quitus BTP distincts du premier VP. |
| 4 | Secrétaire | Direction et validation | Formalisation du mandat et vérification du PV. |
| 5 | Rapporteur général | Direction et validation | Chronogramme et accusé de réception propre. |
| 6 | Conseiller technique Cabinet ITP 1/2 | Coordination institutionnelle | Mandat individuel malgré institution commune avec 7. |
| 7 | Conseiller technique Cabinet ITP 2/2 | Coordination institutionnelle | Mandat individuel malgré institution commune avec 6. |
| 8 | Conseiller planification SG ITP | Coordination institutionnelle | Contribution de planification, distincte des actes du Rapporteur. |
| 9 | Cadre supérieur SG Reconstruction 1/2 | Coordination institutionnelle | Poste et contributions individuels. |
| 10 | Cadre supérieur SG Reconstruction 2/2 | Coordination institutionnelle | Poste et contributions individuels. |
| 11 | Représentant Urbanisme et Habitat | Coordination institutionnelle | Périmètre institutionnel ; urbanisme cible encore à arbitrer. |
| 12 | Représentant Aménagement du territoire | Coordination institutionnelle | Contribution territoriale selon mandat. |
| 13 | Représentant Environnement | Conformité et réglementation | Observation environnementale ; pas de pouvoir juridique automatique. |
| 14 | Représentant Affaires foncières | Conformité et réglementation | Observation foncière ; pas de pouvoir juridique automatique. |
| 15 | Représentant Division ITP / Kinshasa | Conformité et réglementation | Contribution territoriale selon mandat. |
| 16 | Conseiller juridique légistique 1/2 | Conformité et réglementation | Dossier juridique assigné et fonction explicite. |
| 17 | Conseiller juridique légistique 2/2 | Conformité et réglementation | Dossier juridique assigné et fonction explicite. |
| 18 | Directeur technique OR | Contrôle technique et financier | Domaine technique OR, selon règles de périmètre. |
| 19 | Directeur technique OVD | Contrôle technique et financier | Domaine technique OVD, selon règles de périmètre. |
| 20 | Directeur normes/innovation ACGT | Contrôle technique et financier | Domaine ACGT, sans droit issu du seul acronyme. |
| 21 | Directeur expertise BTC | Contrôle technique et financier | Contrôle/essais selon mandat. |
| 22 | Directeur études financières FONER | Contrôle technique et financier | Module financier propre ; pas de droit financier partagé par 18–21. |
| 23 | Représentant ONA | Partenaires et expertise | Avis spécialisé selon mandat. |
| 24 | Représentant syndicats/régulation | Partenaires et expertise | Fonction à préciser sans attribuer un régulateur par supposition. |
| 25 | Administrateur technique BEAU | Partenaires et expertise | Contribution aménagement selon mandat. |
| 26 | Représentant patronat/BTP privé FEC | Partenaires et expertise | Avis privé ; distinguer le rôle de liaison industrielle CTC. |
| 27 | Directeur technique OCC | Partenaires et expertise | Avis contrôle/métrologie ; ne pas activer une nouvelle compétence de certification. |

La correspondance utilise le poste réellement occupé et son numéro d’ordre métier dans le comité concerné ; jamais l’ID du poste ni une plage de PK. La base locale a 27 postes vacants : une adhésion seule ne permet pas de choisir un numéro par défaut. L’espace historique reste disponible ; la future interface indique « Poste non attribué » tant que l’affectation n’est pas confirmée.

## 4. Contrat du futur contexte serveur

Prévoir un service de présentation distinct du service d’autorisation. Son résultat contiendra : identité du mandat sélectionné, référence de poste, interface, périmètre consultable, organisation affichée, modules visibles et actions autorisées **par ressource**. Les anciens contextes Pilotage/CTC seront servis par un adaptateur de leurs règles actuelles, sans ajout de droits.

Les cinq clés de composition proposées sont `direction_validation`, `coordination_institutionnelle`, `conformite_reglementation`, `controle_technique_financier`, `partenaires_expertise`. Ce sont des clés de présentation, jamais des rôles d’autorisation.

Règles d’interaction :

- Si un expert possède plusieurs mandats, le sélecteur n’affiche que ses mandats valides. Le périmètre est recalculé pour celui qu’il choisit ; aucun cumul implicite de pouvoirs de mandats différents.
- Si aucun poste n’est attribué, ne pas deviner le poste via l’acronyme ou `.first()` ; proposer la consultation autorisée et le chemin de demande d’attribution.
- Si une action est interdite, les modules peuvent expliquer l’absence de mandat sans exposer le contenu du dossier. Le serveur retourne 403 ou masque l’existence de la ressource selon le contrat retenu.
- Si une pièce manque ou si l’étape ne permet pas l’action, afficher une cause métier précise. Une erreur d’état est distincte d’un refus de permission.
- Après décision, afficher le résultat enregistré et rafraîchir le parcours depuis le serveur. Aucun changement de stade calculé uniquement par le navigateur.
- La navigation vers une organisation proposée affiche les correspondances comme propositions ; les boutons de migration et de nouvelle validation restent inactifs.

## 5. Ergonomie et critères de recette

Réutiliser les composants institutionnels existants quand ils conviennent ; regrouper navigation et formulaires partagés plutôt que copier un écran complet. Conserver une hiérarchie sobre : fonction du poste, actions attendues, liste de dossiers, puis détail. Les indicateurs de la nouvelle organisation ne doivent pas être mélangés aux volumes de l’ancienne.

Sur petit écran, la navigation devient escamotable, les tableaux restent lisibles et les actions sensibles affichent la référence du dossier. Conserver les préférences de thème existantes et toute largeur persistante de sidebar lors du futur refactoring. Prévoir focus clavier, labels, contraste et messages d’erreur accessibles.

Recette lors du développement :

- Les 27 postes conduisent exactement aux cinq compositions demandées ; les postes vacants n’attribuent aucun pouvoir.
- Les deux VP conservent leurs actions et quitus distincts ; les deux juristes restent deux mandats individuels.
- Les postes 13–15 ne reçoivent pas les actions juridiques 16–17 ; les postes 18–21 ne reçoivent pas les actions financières propres au 22.
- Tous les composants partagés affichent les données du dossier et de la version sélectionnés, sans contexte résiduel après changement de mandat.
- Modifier l’URL, la clé d’interface ou un paramètre POST n’accorde pas une action ; vérifier des appels serveur directs.
- Les dossiers historiques conservent leurs parcours et acteurs, même lorsqu’une correspondance SC est affichée.
- Vérifier au navigateur la navigation, les formulaires, les erreurs, les changements de mandat, le clavier, le mobile et la persistance des préférences ; une vérification de HTML seule ne suffit pas.

Le présent document livre la conception. Aucun de ces nouveaux écrans ou contrôles n’est déclaré implémenté ou testé par un navigateur dans cette première phase.
