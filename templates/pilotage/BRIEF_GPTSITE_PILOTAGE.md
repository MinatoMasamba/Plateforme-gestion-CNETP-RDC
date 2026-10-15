# Brief à transmettre à GPTSite — cinq interfaces de pilotage CNE-ITP

Lecture du code effectuée le 12 octobre 2026. Ce document décrit les fonctions présentes dans les vues, modèles, routes et templates ; il ne constitue pas une vérification en navigateur ni un inventaire des dossiers effectivement présents en base.

Organisation UI/UX retenue : une seule application de pilotage, cinq interfaces fonctionnelles, 27 profils de poste et quatre collèges institutionnels conservés. Cette organisation définit la refonte à concevoir ; les cinq interfaces ne sont pas encore implémentées dans l'application.

## Réponse à ta première question

Je souhaite concevoir l'UI/UX de mon logiciel de gestion : l'espace du Comité de Pilotage Élargi de la plateforme CNE-ITP, consacrée à l'élaboration des normes de construction, des infrastructures et des travaux publics en République démocratique du Congo.

Il s'agit d'une application institutionnelle connectée à un logiciel Django existant. Les utilisateurs pilotent les chantiers normatifs, suivent les comités techniques et leurs groupes de travail, valident les mandats des experts, fixent les échéances, réceptionnent les dossiers de la Cellule Technique de Coordination, donnent les quitus techniques et assurent la validation finale avant transmission ministérielle. Ils supervisent aussi les accès, les examens spécialisés, les consultations et les documents. Un assistant IA les aide à analyser les données et à préparer des graphiques, propositions et brouillons.

Je veux une interface professionnelle en français, organisée en cinq espaces fonctionnels : Direction et validation, Coordination institutionnelle, Conformité et réglementation, Contrôle technique et financier, Partenaires et expertise. Ces espaces partagent les mêmes composants et dossiers, avec des écrans et des actions adaptés au poste de l'utilisateur. Le brief ci-dessous définit le périmètre complet à représenter et distingue les fonctions déjà reliées au serveur des fonctions à compléter.

## 1. Objet métier et limites du périmètre

Le pilotage est l'organe d'orientation, de supervision et de validation du travail normatif. Les experts des Groupes de Travail rédigent les textes ; les membres du pilotage les consultent et les supervisent. Dans le contexte pilotage actuel, la lecture des brouillons WG est prévue pour les membres, et leur édition est interdite.

Les objets suivis sont les normes nationales congolaises, codes applicatifs, directives techniques et recommandations techniques. Les familles de référentiels sont NCD, ISO, ARSO et autres. Chaque dossier appartient à un CTM et à un WG.

Ne pas confondre trois niveaux de suivi : le statut global de la norme, les étapes du traitement CTC et les étapes du cadrage du Bureau Directoire. Une résolution finale de cadrage enregistrée n'est pas, à elle seule, une publication au Journal Officiel.

Le périmètre comprend les relations avec la CTC, les CTM/WG, les experts, les examens spécialisés, l'enquête publique et la transmission ministérielle. Les opérations de rédaction, de consultation publique et de publication peuvent relever d'autres espaces de la plateforme : le pilotage doit en permettre la supervision sans attribuer automatiquement leurs pouvoirs à tous ses membres.

## 2. Les 27 postes et les quatre collèges

Le nombre de sièges prévu est 27. Le nombre de membres inscrits et de postes occupés doit venir des données réelles ; un siège vacant doit rester identifiable.

| Poste | Fonction / structure | Intervention principale |
|---|---|---|
| 1 | Président, Cabinet du Ministre des ITP | Orientation, ouverture du chantier, réception CTC, validation finale, verrouillage de plateforme |
| 2 | 1er Vice-Président, ONIC | Validation des experts Ingénierie et quitus de conformité |
| 3 | 2nd Vice-Président, AIBTP / CNIRS-BTP | Validation du mandat des experts BTP et quitus de conformité |
| 4 | Secrétaire, institutions académiques et de recherche | Mandat opérationnel, méthodologie, vérification du PV |
| 5 | Rapporteur Général, SG-ITP | Chronogramme, ordre de service, réception CTC |
| 6–7 | Deux conseillers techniques du Cabinet du Ministre | Liaison politique, suivi de production, conformité stratégique, sanction et vulgarisation |
| 8 | Conseiller en planification du SG-ITP | Cohérence administrative et suivi du calendrier |
| 9–10 | Deux cadres du SG à la Reconstruction | Articulation avec les programmes de reconstruction |
| 11 | Urbanisme et Habitat | Urbanisme, habitat et contraintes d'application |
| 12 | Aménagement du Territoire | Cohérence territoriale |
| 13 | Environnement et Développement Durable | Impacts, durabilité et exigences environnementales |
| 14 | Affaires Foncières | Régime foncier et contraintes d'emprise |
| 15 | Division ITP / Ville de Kinshasa | Contraintes urbaines et retours des services municipaux |
| 16–17 | Deux conseillers juridiques spécialisés en légistique | Projets d'arrêtés d'homologation et relecture juridique |
| 18 | Office des Routes, OR | Audit technique, spécialité CTM 1 |
| 19 | Office des Voiries et Drainage, OVD | Audit technique, spécialité CTM 7 |
| 20 | Agence Congolaise des Grands Travaux, ACGT | Audit technique, spécialité CTM 1 à 3 |
| 21 | Bureau Technique de Contrôle, BTC | Contrôle des protocoles de laboratoire sur les huit CTM |
| 22 | FONER | Évaluation financière du cycle de vie des chaussées |
| 23 | Ordre National des Architectes, ONA | Contribution sectorielle consultative |
| 24 | Syndicats et organismes de régulation | Contribution sectorielle consultative |
| 25 | Bureau d'Études d'Aménagement Urbain, BEAU | Contribution sectorielle consultative |
| 26 | Fédération des Entreprises du Congo, FEC | Applicabilité économique et industrielle des normes |
| 27 | Office Congolais de Contrôle, OCC | Métrologie et certification des matériaux locaux |

Les collèges sont : Bureau Directoire, postes 1 à 5 ; Conseillers Institutionnels et Politiques, postes 6 à 17 ; Administrateurs Techniques et Financiers, postes 18 à 22 ; Partenaires Sectoriels et Société Civile, postes 23 à 27.

### Droits à respecter

- Directoire : supervision globale, gestion des accès experts, décision sur les demandes de permission. Chaque étape de cadrage appartient toutefois à un acteur précis, pas à n'importe quel membre du Directoire.
- Président et Rapporteur Général : chacun accuse personnellement réception du dossier CTC.
- Président seul : verrouillage et déverrouillage de la plateforme.
- Conseillers : supervision globale en consultation, suivi des chronogrammes et rapports institutionnels prévus. Le module légistique est réservé aux conseillers identifiés comme juridiques.
- ATF : accès à la supervision globale dans le code actuel, spécialités techniques distinctes, finance FONER et laboratoire BTC. La demande de permission pour les autres CTM est prévue dans l'interface spécialisée.
- Partenaires : rôle consultatif ; ils n'ont pas les décisions administratives internes. FEC et OCC ont des modules spécialisés. Aucun parcours administratif dédié équivalent au Directoire n'est actuellement routé pour ce collège.
- Les interfaces doivent afficher le poste, le collège, la structure et le titulaire connecté ; un sélecteur de rôle dans une maquette sert uniquement à prévisualiser les variantes.

### Organisation retenue : cinq interfaces fonctionnelles

Le regroupement porte sur l'interface affichée. Les quatre collèges restent les rattachements institutionnels des 27 postes. En particulier, les postes 6 à 17 demeurent tous membres du collège des Conseillers Institutionnels et Politiques, même si leurs écrans sont répartis entre les interfaces 2 et 3.

| Interface | Postes | Nombre de postes | Collège institutionnel |
|---|---|---|---|
| 01 — Direction et validation | 1 à 5 | 5 | Bureau Directoire |
| 02 — Coordination institutionnelle | 6 à 12 | 7 | Conseillers Institutionnels et Politiques |
| 03 — Conformité et réglementation | 13 à 17 | 5 | Conseillers Institutionnels et Politiques |
| 04 — Contrôle technique et financier | 18 à 22 | 5 | Administrateurs Techniques et Financiers |
| 05 — Partenaires et expertise | 23 à 27 | 5 | Partenaires Sectoriels et Société Civile |

Chaque poste appartient à une seule configuration d'interface. Les normes, CTM/WG, documents et décisions restent des objets communs de la plateforme, consultés selon les autorisations. Les regrouper visuellement ne fusionne ni leurs données ni leurs pouvoirs.

#### Interface 01 — Direction et validation

Accueil centré sur les dossiers à traiter, les actions du titulaire, les réceptions CTC et les demandes de permission en attente. Modules : supervision globale, cadrage, mandat, chronogramme, réception CTC, PV, quitus, résolution finale, gestion des experts et demandes d'accès.

Les cinq postes partagent l'espace et peuvent consulter les missions et files de leurs collègues du Directoire. Les boutons d'action restent propres au titulaire : ouverture et validation finale pour le Président ; validation des experts et quitus pour chacun des VP ; mandat et PV pour le Secrétaire du Comité de Pilotage ; calendrier et ordre de service pour le Rapporteur Général. Le Président et le Rapporteur disposent chacun de leur accusé de réception CTC. Le verrouillage est réservé au Président.

Les doubles validations, doubles réceptions et doubles quitus doivent être visibles séparément, avec prérequis, auteur et date. Le parcours complet est décrit à la section 3.

#### Interface 02 — Coordination institutionnelle

Accueil centré sur les normes suivies, les calendriers et les contraintes sectorielles. Modules : supervision globale CTM/WG, suivi des normes et programmes, chronogrammes, commentaires internes, documents, rapports institutionnels prévus et suivi personnel des demandes d'accès.

Les postes 6–7 mettent en avant la liaison politique et les phases production, contrôle stratégique, sanction et vulgarisation ; le poste 8 met en avant la planification et la cohérence administrative ; les postes 9–10 les programmes de reconstruction ; le poste 11 les contraintes d'urbanisme/habitat ; le poste 12 les contraintes d'aménagement territorial.

Les cartes sectorielles servent à organiser la consultation et les observations ; elles ne constituent pas de nouveaux circuits de validation enregistrés. Les décisions souveraines du Directoire restent hors des autorisations de ces postes.

#### Interface 03 — Conformité et réglementation

Accueil centré sur les normes à examiner et les contraintes environnementales, foncières, urbaines ou juridiques. Modules communs conservés pour les cinq postes : supervision globale CTM/WG, consultation des normes, commentaires, chronogrammes, documents, rapports institutionnels prévus et suivi des demandes d'accès.

Le poste 13 dispose d'une présentation des exigences environnementales ; le poste 14 des contraintes foncières ; le poste 15 des contraintes urbaines de Kinshasa. Les postes 16–17 disposent en plus du module légistique : dossiers juridiques et conception du parcours de rédaction/relecture d'arrêtés, dont les actions d'édition restent à connecter.

Ne pas attribuer aux postes 13–15 les outils d'édition légistique. Leurs observations restent distinctes d'une décision juridique et ne remplacent pas les examens spécialisés effectués par la CTC. Le changement d'interface ne retire aucune fonction commune du collège des Conseillers.

#### Interface 04 — Contrôle technique et financier

Accueil centré sur les dossiers d'expertise du poste connecté. Modules communs : supervision globale CTM/WG, consultation des normes, commentaires, documents et demandes d'accès. Mettre ensuite en avant les modules spécialisés OR, OVD, ACGT, BTC ou FONER selon le titulaire.

OR met en avant le CTM 1 ; OVD le CTM 7 ; ACGT les CTM 1 à 3 ; BTC les protocoles d'essais mécaniques, thermiques et hydrauliques sur les huit CTM ; FONER les évaluations du coût du cycle de vie. Distinguer la consultation globale actuellement autorisée des droits d'intervention spécialisée. FONER dispose d'un rôle financier transverse sans CTM de spécialité directement attribué.

BTC et FONER utilisent la même structure d'écran, avec des rubriques et champs métier différents. Les formulaires d'audit ou de décision financière encore absents doivent être conçus comme des intégrations à développer. Réutiliser les contenus ATF réels, en corrigeant l'incohérence de présentation signalée à la section 11.

#### Interface 05 — Partenaires et expertise

Accueil centré sur les dossiers accessibles et les consultations du partenaire connecté. Modules : consultation autorisée des dossiers et documents, contributions sectorielles à concevoir, suivi des consultations, demandes de permission et assistant IA selon les autorisations effectives.

ONA, syndicats/régulation et BEAU présentent leurs contributions sectorielles autorisées ; FEC ses consultations industrielles ; OCC son périmètre métrologie et certification. Prévoir les états sans dossier et les connexions manquantes. Aucun accès à la supervision globale ne doit être déduit du seul affichage de cet espace : les partenaires ne disposent pas de ce droit dans le moteur actuel.

Cet espace reste consultatif et ne propose pas les validations administratives, les actions de cadrage ou la gestion des experts du Directoire. La création d'un écran de contribution n'atteste pas l'existence de son action serveur.

#### Composants communs aux cinq interfaces

Une seule structure graphique : barre supérieure, navigation latérale, accueil personnalisé, liste de dossiers, fiche de norme, documents, calendrier, notifications, demandes personnelles, profil, paramètres et assistant IA. Les rubriques disponibles et les données visibles sont filtrées par les autorisations ; un composant partagé n'implique pas un accès partagé.

Conserver une fiche de dossier commune, les mêmes libellés de statut et les mêmes formulaires d'action autorisés. La configuration du poste choisit la page d'accueil, les priorités et les modules spécialisés. Un accès documentaire ou un outil IA doit être vérifié indépendamment de la navigation visuelle.

## 3. Parcours réel du Bureau Directoire

### Phase amont : cadrage et lancement

1. Proposition en attente : le Président ouvre le chantier et saisit l'orientation stratégique.
2. Validation des experts : le VP ONIC et le VP BTP enregistrent chacun leur validation et leurs observations. Les deux validations sont nécessaires avant l'étape suivante.
3. Formalisation : le Secrétaire saisit le mandat opérationnel et la méthodologie scientifique destinés aux CTM.
4. Planification : le Rapporteur Général fixe les dates de remise des travaux CTM/WG, de transmission à la CTC et de retour devant le pilotage. L'action enregistre également la date de transmission de l'ordre de service.

Ces actions enregistrent l'acteur et la date. Le formulaire d'action doit reprendre les champs réellement attendus : orientation, notes ONIC/BTP, mandat, trois échéances.

### Traitement technique et retour CTC

La CTC suit son propre parcours : réception et numérisation, indexation et validation d'entrée ; traitement SIG si nécessaire ; examens parallèles ; consultation industrielle FEC ; certification de sortie et transmission au pilotage.

Les examens parallèles portent sur la légistique, l'harmonisation ISO, les sauvegardes écologiques, l'économie, le calendrier et la validation scientifique. Le calendrier exige les validations du planificateur et du scientifique. La consultation industrielle intervient après les examens requis.

Une fois transmis, le dossier apparaît dans la file de réception du Président et du Rapporteur Général. Afficher les deux accusés séparément, leur auteur et leur date. Une seule réception ne suffit pas à débloquer la vérification du PV.

### Phase aval : contrôle et validation finale

5. Le Secrétaire vérifie le Procès-Verbal de l'Assemblée Plénière et renseigne sa référence. Cette action reste bloquée tant que la double réception CTC n'est pas complète.
6. Les deux Vice-Présidents donnent chacun leur quitus de conformité technique. Les deux quitus sont nécessaires.
7. Le Président enregistre la validation finale et la référence de la résolution signée. Le cadrage passe à « Terminé — Transmis au Ministre » avec une date de transmission enregistrée.

L'interface doit montrer l'étape courante, les prérequis, les validations déjà effectuées, l'acteur attendu et la prochaine action autorisée. Les étapes avancent seulement après confirmation du serveur.

Le code actuel enregistre des textes, références et dates : il ne faut pas représenter ces opérations comme une signature électronique certifiée, une génération automatique de document ou un envoi effectif au ministère.

## 4. Statut global des normes

Prévoir les états : Brouillon ; Révision interne ; Soumis au CTM ; Toilettage légistique ; Enquête publique ; Validation Comité Pilotage ; Révision finale ; Adopté ; Homologué ; Publié au JO ; Archivé.

Les transitions comportent des retours pour correction. La CTC peut transmettre du toilettage légistique au pilotage sans passage préalable par l'enquête publique ; une décision ultérieure peut renvoyer le dossier vers l'enquête. Ne pas imposer une frise universelle qui contredit ces branches.

L'application possède des données et API pour les versions, l'historique, les différences entre versions, les votes, les commentaires et le PDF de norme. Leur présentation en lecture dans une fiche pilotage est à prévoir, avec vérification des droits des endpoints avant intégration. Les droits d'édition, de restauration, de vote et de changement de statut ne doivent pas être déduits d'un simple accès au tableau de bord.

La publication au JO est une opération distincte, réservée dans l'API au ministre ou au personnel CTC, et exige une référence JO sur une norme adoptée ou homologuée. Prévoir le suivi de la date, de la référence JO et du fichier de publication, sans donner le bouton de publication à tous les membres du pilotage.

## 5. Supervision des huit CTM et des WG

Les noms suivants proviennent de la commande de création de structure ; l'interface intégrée doit utiliser les noms présents dans le référentiel, certains textes de présentation utilisant d'autres formulations.

| CTM | Domaine | Groupes de travail prévus par la commande |
|---|---|---|
| 1 | Géotechnique et Risques Naturels | Sols & Géomécanique ; Risques Naturels ; Stabilité & Érosions |
| 2 | Ouvrages d'Art | Calcul Structural & Eurocodes ; Génie Parasismique ; Ouvrages Hydrauliques Lourds |
| 3 | Bâtiment, Urbanisme et Transition Numérique | Habitabilité & Sécurité ; BIM & Transition Numérique ; Performance Énergétique & Coûts |
| 4 | Aéroports et Transport Aérien | Infrastructure Aéroportuaire ; Terminaux et Équipements ; Conformité OACI |
| 5 | Infrastructures de Transport Linéaire et Maritimes | Ingénierie Routière ; Voies Ferrées ; Infrastructures Portuaires |
| 6 | Ressources en Eau et Hydraulique | Adduction d'Eau ; Irrigation et Drainage ; Forages et Captage |
| 7 | Assainissement et Gestion des Déchets | Macro-drainage & Eaux Pluviales ; Eaux Usées & Réseaux d'Égouts ; Déchets Solides & CET |
| 8 | Sciences des Matériaux, Métrologie et Valorisation Locale | Matériaux Géo-sourcés & Locaux ; Essais & Métrologie Légale ; Simulation, Recherche & Certification |

La console actuelle présente les CTM, le nombre de WG et les effectifs d'affectations. Le détail CTM expose son bureau, les groupes de travail et leurs responsables, les experts et structures, les normes en cours et les normes publiées.

La fiche de norme expose notamment référence, titre, description, CTM/WG, statut, références ISO/ARSO et commentaires internes avec auteur/date. Les normes publiées présentent aussi la date et la référence JO.

Un modèle de tâches WG existe : titre, description, norme liée, responsable, échéance, progression 0–100 %, états planifiée/en cours/complétée/bloquée/en attente. Sa supervision peut être prévue comme extension, mais le tableau de bord pilotage actuel ne charge pas ces tâches.

Les effectifs, pourcentages, retards et taux de présence doivent être calculés à partir des données ; les 27 sièges et huit CTM prévus ne sont pas des indicateurs d'activité.

## 6. Outils spécialisés à conserver dans le design

- Légistique : suivi des dossiers juridiques et de leurs statuts ; rôle métier de rédaction/relecture des arrêtés pour les deux juristes. L'écran actuel liste les revues mais ne propose pas d'éditeur d'arrêté relié au serveur.
- Planification : lecture des chronogrammes, statut planificateur et scientifique, début/fin de revue ; jalons de l'enquête publique dans le périmètre métier. Le dépôt de rapports institutionnels est annoncé mais explicitement non connecté dans le template.
- Audit technique : visibilité sur les CTM de spécialité et demandes d'accès aux autres périmètres. Ne pas inventer une décision d'audit sauvegardée là où seule la consultation existe.
- FONER : évaluation du coût du cycle de vie ; le modèle comprend coût de construction par km, entretien annuel, durée, taux d'actualisation, coût global et observations. Le widget pilotage actuel affiche les évaluations et leur statut, sans formulaire de décision financière.
- BTC : protocoles d'essais mécaniques, thermiques et hydrauliques par CTM. Le template comporte actuellement des boutons sans action et un badge « Vérifié » fixe : ce badge n'est pas une preuve enregistrée et ne doit pas être repris comme résultat réel.
- FEC : consultation industrielle, retours des entreprises, entreprises consultées, faisabilité marché, observations et statut. Le widget pilotage montre les consultations affectées au compte, sans formulaire de décision.
- OCC : métrologie légale et certification des matériaux locaux. Le composant actuel est un état vide fixe ; aucun dossier de certification n'est alimenté dans cette vue.
- ONA, BEAU, syndicats/régulation : participation consultative et consultation autorisée ; ne pas créer des pouvoirs administratifs pour compléter visuellement leur écran.

## 7. Accès, permissions et maîtrise de la plateforme

### Demandes de permission

Une ressource restreinte affiche la raison du blocage et permet une demande motivée. La demande comprend ressource, motif, demandeur, statut, dates, décideur et commentaire de décision. Une seule demande en attente par compte/ressource est créée. Le membre reçoit un accusé et le Directoire est notifié.

Le Directoire approuve ou refuse ; la décision et le commentaire sont persistés, puis le demandeur est notifié. Les autres membres suivent leurs propres demandes.

Attention : dans le moteur de droits lu, une demande approuvée ne modifie pas automatiquement les privilèges. La maquette doit distinguer « demande approuvée » et « accès effectivement accordé », dont la connexion reste à finaliser.

### Gestion des experts

Liste des experts avec recherche/filtrage, structure, statut et affectations CTM/WG. Le Directoire peut activer/rétablir ou suspendre un expert, et retirer une affectation CTM/WG. Le retrait supprime l'affectation ciblée, pas le dossier de l'expert.

### Verrouillage

Le Président dispose d'un verrou global avec indicateur visible, auteur et date. Les vues CTC et certaines actions pilotage consultées refusent les opérations lorsque le verrou est actif. Ne pas promettre que tous les endpoints du logiciel sont gelés sans vérifier leur couverture ; concevoir un retour clair lorsqu'une action est refusée pour verrouillage.

## 8. Assistant IA : ce qu'il analyse, génère et suit

Prévoir un accès rapide depuis les écrans et une console dédiée avec historique des conversations, nouveau dialogue, choix du fournisseur disponible, conversation centrale et panneau des productions associées. Les sessions et messages sont enregistrés et les productions restent attachées à leur session.

### Analyse et recherche disponibles dans le scope pilotage

- Vue d'ensemble de la plateforme : experts, actifs/en attente/inactifs, CV présents/absents, présences et normes/votes.
- Liste des normes par CTM ou statut et lecture de leurs métadonnées.
- Recherche d'experts par nom, spécialité, structure, statut, CTM et disponibilité de CV ; consultation des dossiers, compétences, affectations et contacts selon les accès applicables.
- Liste des membres d'un CTM, responsables et options de WG.
- Recherche documentaire dans les documents, normes, versions et CV indexés ; affichage des sources citées, page/section et lien contrôlé.
- Recherche dans les catalogues et corpus de référentiels externes ISO/ARSO.
- Détection de chevauchements possibles entre travaux de WG, à examiner humainement.
- Récupération des amendements publics d'une norme pour synthèse thématique. L'outil actuel limite sa récupération à 50 amendements : ne pas présenter systématiquement le résultat comme exhaustif.

### Productions réellement prévues pour le pilotage

1. Graphiques : normes par statut, normes par CTM, participation aux votes, amendements d'enquête publique par statut, experts actifs par structure, synthèse des chevauchements WG.
2. Signalements de chevauchement normatif : groupes concernés, analyse et recommandation, en brouillon.
3. Propositions fondées sur un référentiel externe : proposition de nouvelle norme ou commentaire sur une norme existante, CTM cible, justification et extrait de référence, en brouillon.
4. Brouillons d'e-mails : destinataire, objet, corps modifiables ; une pièce liée peut être prévue lorsqu'un artefact compatible existe. L'envoi est déclenché séparément par l'utilisateur.
5. Réponses et synthèses documentées dans la conversation, avec sources. Cela ne signifie pas qu'un export PDF de rapport de pilotage existe.

Les statuts des productions sont Brouillon, Approuvé et Envoyé selon le type. L'approbation d'une proposition dans l'API actuelle change le statut de l'artefact ; elle ne crée pas automatiquement une norme et ne fusionne pas des WG.

Le type « demande d'attribution WG » et son téléchargement PDF existent dans le système IA, mais l'outil de génération est réservé au scope expert. Ne pas le présenter comme une génération disponible au pilotage par défaut.

Une API d'analyse réglementaire de texte existe également : explication, proposition, modifications ciblées et texte résultant. Elle n'est pas un parcours dédié visible dans la console pilotage lue ; son ajout au design est une intégration à prévoir.

Les résolutions, mandats, ordres de service, PV et arrêtés sont des pièces métier à représenter. Le pilotage actuel saisit leurs textes ou références ; leur génération automatique, export et signature ne sont pas implémentés par ces actions.

## 9. Écrans et navigation attendus dans les cinq interfaces

1. Accueil personnalisé : identité/poste/collège, état de plateforme, dossiers et actions qui attendent l'utilisateur.
2. Supervision globale CTM/WG : liste ou grille, effectifs, accès aux détails.
3. Détail CTM : bureau, WG, experts, normes en cours et publiées.
4. Fiche de norme/dossier : métadonnées, documents, commentaires, étapes de norme/CTC/cadrage séparées, échéances et décisions. Les versions et votes peuvent être reliés aux API existantes après vérification des droits.
5. Interface 01 — Direction et validation : cinq postes du Directoire, missions et files d'actions ; le titulaire agit sur son poste, les autres membres du Directoire consultent.
6. Cadrage et validations : formulaires adaptés à l'action, validations doubles visibles, prérequis expliqués.
7. Réception CTC : dossier transmis, date/auteur de sortie, accusés Président/Rapporteur et attente restante.
8. Interfaces 02 et 03 — Coordination institutionnelle / Conformité et réglementation : deux accueils distincts pour les postes 6–12 et 13–17, avec les fonctions communes du collège des Conseillers conservées. Parcours production/contrôle/sanction pour les conseillers Cabinet, vues sectorielles pour les autres, planification pour tous et légistique pour les postes 16–17.
9. Interface 04 — Contrôle technique et financier : missions et outils OR/OVD/ACGT/BTC/FONER, avec vrai contenu spécialisé et consultation globale selon les droits existants.
10. Interface 05 — Partenaires et expertise : FEC/OCC et contributions autorisées ONA/BEAU/syndicats, à concevoir car aucun espace dédié équivalent n'est routé.
11. Gestion des demandes d'accès : file Directoire et suivi personnel des demandes.
12. Gestion des experts : recherche, statuts, affectations et actions autorisées.
13. Assistant IA : sessions, messages, sources, graphiques, propositions, brouillons et suivi de leurs statuts.
14. Documents/rapports et calendrier : vues à concevoir en distinguant les flux déjà disponibles des dépôts, exports ou agrégations à connecter.
15. Profil et paramètres, retour à l'espace de travail, thèmes clair/sombre et navigation mobile.

Une page d'accueil publique éventuellement demandée ensuite doit rester séparée de ce périmètre applicatif. Le besoin principal est l'espace de travail.

## 10. Exigences UI/UX proposées pour la refonte

Ces exigences sont des objectifs de conception, pas une affirmation de fonctions déjà implémentées.

- Style institutionnel sobre, français naturel, typographie lisible, hiérarchie nette et densité adaptée aux tableaux de travail.
- Vue initiale centrée sur le poste connecté et ses actions en attente ; navigation stable, retour évident vers la supervision et le dossier source.
- Cinq accueils fonctionnels issus d'une structure commune, puis variantes de contenu pour chaque poste. Le nom de l'interface et le collège institutionnel doivent rester identifiables séparément.
- Recherche et filtres cohérents : CTM, WG, type de norme, statut, acteur attendu, échéance et structure lorsque les données existent.
- Détail de dossier permettant de comprendre qui a fait quoi, quand, ce qui bloque et ce qui reste à faire, à partir des traces enregistrées.
- Calendrier et alertes de retard calculés sur les échéances réelles ; aucun pourcentage ou graphique inventé hors données de démonstration explicitement identifiées.
- Boutons d'action visibles selon le rôle et l'étape ; consultation clairement identifiable lorsque l'utilisateur ne peut pas agir.
- États chargement, vide, erreur, accès refusé, attente du second validateur, plateforme verrouillée et succès confirmé par le serveur.
- Confirmations compréhensibles avant suspension, retrait d'affectation ou verrouillage ; éviter les doubles soumissions.
- Thèmes clair/sombre persistants, navigation latérale utilisable et persistante lorsqu'elle est redimensionnable, adaptation ordinateur/tablette/mobile.
- Accessibilité : contraste, libellés lisibles, navigation clavier, focus visible ; ne pas dépendre seulement de couleurs ou d'icônes.
- Maquette interactive : navigation, ouverture de dossier, formulaire de validation, double réception, demande de permission et productions IA doivent pouvoir être parcourus. Les données de démonstration doivent être identifiées et remplacées par le serveur lors de l'intégration.

## 11. Points du code actuel à ne pas reproduire comme règles métier

- L'espace ATF charge actuellement les composants du Bureau Directoire, alors que la vue fournit les postes 18 à 22 : reprendre le contenu ATF réel dans la refonte, pas cette incohérence.
- Des accès CTM globaux sont actuellement ouverts aux conseillers et ATF ; certains textes les décrivent comme réservés au Directoire, et le module ATF parle de permissions pour les CTM tiers. La conception doit présenter clairement consultation globale et intervention spécialisée ; une restriction supplémentaire exige un alignement serveur.
- Les widgets juridiques, financiers et FEC affichent des données, mais leurs mandats descriptifs ne prouvent pas l'existence de formulaires d'édition ou de décision pilotage.
- Le contrôle BTC contient un état « Vérifié » fixe ; OCC contient un état vide fixe ; les rapports institutionnels sont explicitement à connecter.
- Les droits sont calculés depuis l'adhésion, la structure et le poste. Une demande d'accès approuvée n'est pas consommée par ce calcul.
- Les prompts IA et commentaires contiennent des compositions et numérotations contradictoires ou anciennes. Pour le roster ci-dessus, utiliser la commande de peuplement des 27 postes et les métadonnées des vues plutôt que recopier les prompts.
- Le statut global de norme, le cadrage et la CTC ne doivent pas être fusionnés en un seul indicateur. Les champs auteur/date ne constituent pas un journal d'audit exhaustif.
- La validation finale du cadrage enregistre une référence et une date ; elle ne fait pas automatiquement passer la norme à Adopté/Homologué/Publié et n'atteste pas d'une signature ministérielle.

## 12. Livrable demandé à GPTSite

Conçois une proposition UI/UX complète fondée sur les cinq interfaces retenues à la section 2. Livre une architecture commune de navigation, cinq accueils fonctionnels, les variantes de contenu et d'action des 27 postes, les écrans détaillés, des composants réutilisables et les parcours interactifs sur ordinateur et mobile. Couvre tous les modules du brief et indique, dans tes notes de livraison, les connexions serveur requises. Pour les fonctions incomplètes, propose un écran cohérent sans les faire passer pour opérationnelles. Le vocabulaire visible doit rester métier ; les détails d'intégration appartiennent aux notes techniques.

Ordre de livraison : architecture des cinq interfaces et navigation commune ; cinq accueils personnalisés ; fiche de dossier partagée et écrans détaillés ; parcours métier et états d'attente ; adaptation mobile et notes d'intégration.

Priorité de démonstration : interface 01, accueil du Président → ouverture d'un dossier → validations des deux VP → mandat du Secrétaire → calendrier du Rapporteur → suivi du traitement CTC → double réception → PV → double quitus → résolution finale. Montrer ensuite l'interface 02 avec un conseiller Cabinet ; l'interface 03 avec un représentant sectoriel puis un juriste ; l'interface 04 avec BTC puis FONER ; l'interface 05 avec FEC puis OCC. Couvrir également les variantes des autres postes, les permissions, les accès experts et l'assistant IA.

La proposition finale doit permettre de retrouver chacun des 27 postes dans une des cinq interfaces, de comprendre ses modules et de vérifier ses actions autorisées. Tous les états de norme, CTC et cadrage, les prérequis doubles, les documents métier, les examens spécialisés et les productions IA décrits dans ce brief doivent rester représentés.

## Annexe technique pour l'intégration

### Configuration des interfaces à mettre en place

Conserver quatre informations distinctes dans le contexte envoyé au frontend : poste officiel, collège institutionnel, type d'interface et permissions effectives. Ce sont des informations de contexte ; elles n'imposent pas la création de quatre nouveaux champs en base.

Le type d'interface peut être calculé à partir de l'ordre du poste nominatif : 1–5 → Direction et validation ; 6–12 → Coordination institutionnelle ; 13–17 → Conformité et réglementation ; 18–22 → Contrôle technique et financier ; 23–27 → Partenaires et expertise. Le rattachement institutionnel et les permissions continuent à provenir de l'adhésion, de la structure, du poste et des contrôles serveur existants. Un membre dont le poste n'est pas attribué ou dont les données sont incohérentes doit avoir un état explicite d'affectation à compléter, sans attribution arbitraire d'une interface ou de droits.

Utiliser une seule application Django, une structure frontend commune et des configurations par poste. Les cinq interfaces ne nécessitent ni cinq bases de données ni cinq systèmes indépendants. Les routes existantes peuvent être conservées, adaptées ou redirigées progressivement après vérification de leurs contrôles d'accès. La séparation des interfaces 02 et 03 est une évolution de présentation du même collège, sans modification automatique de ses adhésions.

Pour l'assistant IA, conserver le contexte de pilotage, les conversations et les artefacts. Vérifier l'accès aux sources et aux outils côté serveur pour chaque utilisateur ; un module masqué à l'écran ou une instruction au modèle ne remplace pas un contrôle d'autorisation. Les éventuels écarts de filtrage par poste sont à traiter lors de l'intégration.

### Routes pilotage existantes

- `/pilotage/` : tableau de bord personnalisé.
- `/pilotage/bureau-directoire/`, `/pilotage/conseillers/`, `/pilotage/atf/` : espaces dédiés.
- `/pilotage/ctm/<number>/` : détail CTM.
- `/pilotage/norme/<pk>/commenter/` : commentaire interne.
- `/pilotage/demande-permission/`, `/pilotage/approuver-demande/<pk>/` : demande et décision.
- `/pilotage/processus/<pk>/receptionner/` : accusé de réception CTC.
- `/pilotage/cadrage/<pk>/action/` : ouverture, validations VP, mandat, calendrier, PV, quitus et validation finale.
- `/pilotage/gestion-acces/`, `/pilotage/gestion-acces/expert/<pk>/statut/`, `/pilotage/gestion-acces/affectation/<pk>/exclure/` : gestion des accès.
- `/pilotage/plateforme/verrouillage/` : verrou Président.
- `/pilotage/ia-agent/` : console IA.
- `/api/pilotage/contexte/` : contexte de privilèges ; vérifier sa sérialisation avant utilisation comme contrat front complet.
- `/ctc/dossiers/<pk>/transmettre-pilotage/` : transmission depuis la CTC.
- `/api/v1/ia-agent/` : sessions, messages, artefacts, approbation, envoi séparé d'e-mail et analyse réglementaire.

### Sources examinées

- `web/pilotage_views.py` et `web/urls.py` : rôles, données chargées, parcours et actions serveur.
- `apps/governance/models.py` : CTM, WG, affectations, adhésions, postes, permissions, tâches, processus CTC, cadrage et verrouillage.
- `apps/governance/management/commands/seed_pilotage_postes.py` : roster des 27 postes.
- `apps/governance/management/commands/create_ctm_structure.py` : huit domaines et WG de référence.
- `apps/norms/models.py`, `apps/validation/models.py`, `api/v1/norms/views.py` : normes, cycle de vie, versions, examens et publication.
- `templates/pilotage/` : dashboard, consoles, espaces Directoire/Conseillers/ATF, détails CTM, accès experts et formulaires.
- `web/ctc_views.py` : transmission, liens pilotage et contrôles de verrouillage.
- `apps/ia_agent/models.py`, `views_web.py`, `tools/`, `services/prompts.py`, `services/pdf_artifacts.py`, `api/v1/ia_agent/views.py`, `templates/ia_agent/pilotage_console/console.html` : assistant, sources, productions et limites.
