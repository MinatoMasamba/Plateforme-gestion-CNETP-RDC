# Migration progressive de l’organisation CNE-ITP Phoenix

Mise à jour : 14 octobre 2026. Statut : **les sept sous-commissions techniques et la version d’organisation sont validées dans la base active ; 109 experts sont classés directement et nominativement, 40 profils sans correspondance certaine restent à examiner ; l’ancien circuit, ses CTM, ses WG et ses affectations sont conservés**. Le nouveau circuit n’est pas activé faute de catalogue GT, mandats et habilitations officiels. Le [rapport d’implémentation](docs/migration_organisation/IMPLEMENTATION_PHOENIX.md) détaille la reprise.

## 1. Conclusion et décisions retenues

La plateforme peut accueillir la nouvelle organisation en ajoutant un référentiel versionné et des correspondances autour du système existant. Remplacer directement CTM par SC et WG par GT serait incorrect : plusieurs périmètres se divisent ou fusionnent, les droits sont distribués entre plusieurs couches, et les dossiers ont plusieurs états de suivi indépendants.

L’objectif de conservation porte sur les données **et leur sens** : identité des auteurs, origine des dossiers, rattachements historiques, décisions, dates, pièces, mandats et autorisations. Conserver les lignes de base tout en réécrivant leur appartenance ou en élargissant leurs droits ne satisferait pas cet objectif.

Périmètre retenu, selon la note de cadrage Phoenix fournie :

- Conserver CTM/WG, leurs identifiants, les relations actuelles de Norme et toutes les données associées.
- Maintenir les circuits CTC/Pilotage et leurs permissions actuelles jusqu’à validation de leur évolution.
- Préparer un nouveau **COPIL de 22 postes**, un **ST de 24 postes** et **sept SC**. Les 46 postes COPIL/ST ne comprennent pas les postes des SC et ne correspondent pas nécessairement à 46 personnes distinctes.
- Préparer les sept domaines **proposés**, y compris SC-SE·GEO·RS, sans activer « Infrastructure qualité » ; conserver SC-SOCLE comme appellation provisoire, SC-RTN restant une proposition.
- Les dossiers existants terminent leur ancien circuit. Les nouveaux dossiers ne pourront utiliser le nouveau circuit qu’après sa validation et son activation explicite.
- Reconcevoir les interfaces du COPIL autour des catégories Phoenix : présidence, secrétariat, membres, invités et appoints. Les cinq anciennes compositions pour 27 postes restent une archive de conception, pas un découpage cible.
- Conserver les 27 postes du Pilotage historique et les 20 postes de la CTC historique. Aucun poste, compte, mandat ou droit n’est automatiquement déplacé vers les 22/24 postes cibles.
- Les nouveaux GT, titulaires manquants, pouvoirs et règles de validation restent à confirmer dans les documents et décisions officiels.

**Livrables :** ce plan et ses matrices ; [l’inventaire historique](docs/migration_organisation/INVENTAIRE_EXISTANT.md) ; [le référentiel Phoenix](docs/migration_organisation/REFERENTIEL_PHOENIX.md) ; [la conception des interfaces Phoenix](docs/migration_organisation/CONCEPTION_INTERFACES_PHOENIX.md) ; [le rapport d’implémentation](docs/migration_organisation/IMPLEMENTATION_PHOENIX.md). Le référentiel, les correspondances et leur journal sont consultables dans `/pilotage/organisation/`. Les corrections de propositions exigent la permission explicite `governance.prepare_phoenix`. [L’ancienne conception pour 27 postes](docs/migration_organisation/CONCEPTION_INTERFACES.md) reste consultable.

### Schéma de la cible à préparer

```text
Version d’organisation Phoenix validée
├── COPIL : 22 postes
│   ├── Présidence : 4
│   ├── Secrétariat : 2
│   ├── Membres : 7
│   ├── Invités : 3
│   └── Appoints : 6
├── Secrétariat technique : 24 postes
│   ├── Coordination : 4
│   └── Cinq pôles : 4 postes chacun, soit 20
└── Sept sous-commissions techniques validées
    └── GT : catalogue et rattachements à confirmer
```

Ce schéma regroupe les objets du référentiel ; il ne fixe ni une chaîne d’approbation ni une subordination juridique non documentée. Un poste existe indépendamment de son titulaire. Une même personne peut avoir plusieurs mandats explicites, sans duplication de son compte et sans cumul implicite de pouvoirs entre organes.

## 2. Sources, preuves et limites

Source de cadrage utilisée pour cette mise à jour : [Cadrage_nouvelle_structure_CNE_ITP_Phoenix (4).docx](<Cadrage_nouvelle_structure_CNE_ITP_Phoenix (4).docx>), sections 1 à 6. La note rapporte la composition figurant dans « MATRICE CNE-ITP_Phoenix.pdf », annoncée sur 14 pages, et distingue cette composition des recommandations de conception logicielle. Le PDF portant ce nom n’a pas été trouvé dans le projet : aucune page de cette matrice n’a été vérifiée directement.

Les notes comparatives présentes dans `mis a jour/`, notamment celle du 11 octobre 2026, restent des sources de travail pour les correspondances historiques. Leurs hypothèses de composition et de regroupement d’interfaces ne définissent plus la cible Phoenix. Les manuels de mai et du 7 octobre cités par ces notes n’ont pas été vérifiés directement.

| Niveau de preuve | Informations | Usage dans le plan |
|---|---|---|
| Composition rapportée par la note Phoenix | 22 postes COPIL, 24 postes ST, sept SC ; fonctions et origines décrites | Préparer le catalogue, en citant la note et en laissant les titulaires non renseignés. |
| Domaines de préparation | Les sept codes et domaines SC, dont SC-SOCLE et SC-SE·GEO·RS | Structure validée le 14 octobre 2026 ; SC-SOCLE conserve son intitulé provisoire. |
| Conception logicielle proposée | Correspondances, modèles additifs, cinq compositions d’interface et capacités fonctionnelles | Spécifier et tester ; aucune attribution institutionnelle de pouvoir par ces propositions. |
| Informations absentes | Liste des GT, titulaires manquants, pouvoirs, quorum et circuit cible | Champs non renseignés et décisions à obtenir ; aucune valeur inventée. |

L’inventaire technique conserve l’état du checkout examiné le 12 octobre 2026, avec ses modifications locales d’alors. Les repères de lignes et comportements de cette annexe sont ceux de cet instantané et doivent être revérifiés avant développement. Les ajouts de supervision CTC réalisés ensuite sont distingués ci-dessous ; cette mise à jour ne les remplace pas.

Lors de l’inventaire du 12 octobre, la base `db.sqlite3` a été ouverte explicitement en lecture seule (`mode=ro`, `query_only=ON`). Les chiffres conservés dans ce plan décrivent cet instantané local ; ils n’ont pas été actualisés lors de la présente mise à jour documentaire. La configuration permet une autre base SQLite ou PostgreSQL : cet inventaire ne certifie pas l’état courant du serveur ni celui de la production.

### Écarts à résoudre avant toute exécution

| Sujet | Cadrage ou source historique | Code / instantané local | Conséquence |
|---|---|---|---|
| COPIL Phoenix | 22 postes : 4 + 2 + 7 + 3 + 6 | Pilotage historique : 27 postes | Ajouter le COPIL cible ; conserver les 27 postes historiques sans les renuméroter. |
| ST Phoenix | 24 postes : 4 de coordination + 5 pôles de 4 | CTC historique : 20 postes | Préparer un nouveau référentiel de postes ; pas de transfert automatique depuis la CTC. |
| Groupes historiques | 23 WG | 24 WG, dont WG 4.3 « Conformité OACI » | La matrice doit couvrir les 24, y compris le groupe absent de la note. |
| Intitulés des WG | Reconnaissance/essais, sols tropicaux, etc. | Plusieurs intitulés et périmètres différents | Croiser identifiant, intitulé, description et livrables ; ne pas appliquer une table par numéro seul. |
| Hydraulique | 6.2 = rurale/forages ; 6.3 = agricole | 6.2 = irrigation/drainage ; 6.3 = forages/captage | Inversion sémantique : les deux correspondances doivent être revues séparément. |
| SC cibles | Sept domaines listés dans la note Phoenix, dont SC-SE·GEO·RS | Huit CTM conservés | Sept fiches validées ; SC-SOCLE garde son intitulé provisoire et les futurs GT restent à confirmer. |
| GT | Catalogue officiel expressément laissé à confirmer par Phoenix | 24 WG historiques ; pas de liste officielle cible complète | Conserver des domaines candidats. Les chiffres de GT cités par les anciennes notes ne sont pas un catalogue Phoenix validé. |
| Interfaces COPIL | Nouveau regroupement fonctionnel des 22 postes | Ancienne conception pour 27 postes | Remplacer le découpage cible ; archiver la conception historique sans recycler ses permissions. |

Ces écarts ne prouvent pas que l’une des sources est erronée : il peut s’agir de versions, d’interprétations ou de données de préparation différentes. Ils interdisent cependant une conversion automatique non vérifiée.

## 3. Inventaire fonctionnel et dépendances

L’annexe technique recense tous les champs déclarés dans `apps/*/models.py`, les relations et politiques de suppression, ainsi que les points de contrôle API et les routes Pilotage/CTC. Les dépendances qui gouvernent la migration sont les suivantes.

| Ensemble | Modèles principaux et liens | Conservation nécessaire |
|---|---|---|
| Identité | User → Expert en un-à-un ; Expert → Structure ; Expert.ctm facultatif | Comptes, statut, institution d’origine, informations de nomination et choix initial de CTM. |
| Production | CTM → WG ; Affectation → Expert/CTM/WG ; dirigeants CTM/WG → Expert | Identifiants, appartenance historique et responsabilités. WG et affectations utilisent des suppressions en cascade ; Norme protège ses liens CTM/WG. |
| Pilotage | ComitePilotage, PilotageMembreship, PosteNominatif | Distinguer un poste défini, son titulaire et l’adhésion réelle ; ces objets ne sont pas interchangeables. |
| Coordination | TechnicalCell, CTCMembership, PosteNominatifCTC | Conserver la CTC active et ses 20 postes définis ; préparer séparément les 24 postes du futur ST. |
| Normes | Norme → CTM/WG ; versions, commentaires, votes, blocs, changements et imports | Conserver dossier, texte, référence publique, auteurs, versions, pièces et contenu structuré. |
| Validation | CTCProcessus et NormeCadrage en un-à-un avec Norme ; six types d’examen | Préserver étapes internes, responsables, résultats et dates ; ne pas les déduire du seul statut de Norme. |
| Documents et réunions | DocumentFile → utilisateur/expert/norme/réunion ; Reunion → CTM/WG ; PV, présences et votes | Préserver les fichiers hors base, contexte des réunions, signatures et participations. |
| Finances | Cotisation → Structure ; Paiement → Cotisation ; JetonPresence → Expert/Reunion | Ne pas remapper les institutions d’origine ou recalculer les droits financiers à partir des futures SC. |
| Accès exceptionnels | PermissionRequest, CTCOperationalRequest ; PlatformFreeze | Préserver demandes, décisions et verrou global ; ne pas confondre demande approuvée et habilitation effective. |
| Communication | Message, notifications, push, sessions et préférences | Préserver les destinataires et anciens liens embarqués ; adapter les futures notifications selon la version du dossier. |
| Assistant IA | AgentSession/Message/Artifact, AgentPosteContext, configurations et RAG | Liens génériques, métadonnées JSON, identifiants de poste et références CTM/WG doivent rester interprétables ; l’IA suit les mêmes droits que le serveur. |
| Autres référentiels | ExecutiveLevel, OriginStructure, Draft | OriginStructure et experts.Structure sont distincts ; Draft conserve des libellés CTM/WG en texte, sans FK. Aucun rapprochement implicite. |

### État de la base locale dans l’instantané du 12 octobre

14 utilisateurs, 14 experts, 17 institutions `Structure`, 8 CTM, 24 WG, 11 affectations, 18 normes, 109 versions, 163 blocs de contenu et 61 changements de version. La base contient également 27 postes Pilotage et 20 postes CTC, **tous vacants**, mais une adhésion Pilotage et une adhésion CTC. Une adhésion ne prouve donc pas l’occupation d’un poste numéroté.

Les 18 normes et les 11 affectations pointent toutes vers WG 1.1. Cette concentration peut venir de données de démonstration ou de valeurs de repli ; elle ne permet pas d’inférer le domaine technique réel des dossiers. Une classification documentaire sera nécessaire avant d’attribuer un propriétaire cible.

Contrôles effectués : intégrité SQLite `ok`, aucune violation de clé étrangère, aucun couple CTM/WG incohérent sur normes ou affectations. Deux références de fichiers `DocumentFile` existent sous `media/` ; aucun fichier n’est référencé dans les champs version, JO, CV, photo ou justificatif de paiement inspectés. Cela ne constitue pas un audit intégral du stockage ni une validation du contenu des pièces.

Anomalies métier à examiner, sans correction dans cette phase :

- Trois experts ont un `Expert.ctm` sans affectation correspondante : distinguer choix d’inscription et affectation effective avant de conclure à une erreur.
- Trois processus `SIGNED_OUT` n’ont pas de date `signed_out_at`.
- Trois normes `PUBLISHED` ont un processus CTC à une étape différente de `SIGNED_OUT`.
- Aucun `NormeCadrage` et aucun `AuditLog` dans l’instantané inspecté : ce comptage historique ne prouve pas leur absence actuelle. Ne pas reconstruire de validations ou traces absentes par supposition.

Depuis cet inventaire, un suivi CTC a été ajouté dans `apps/core/ctc_audit.py`, `apps/governance/ctc_supervision.py` et les composants de supervision Pilotage. Il enregistre les modifications de modèles suivis réalisées pendant une requête authentifiée, avec auteur, date, document/contexte, espace, IP source et navigateur. Les traces anciennes disponibles sont distinguées des nouvelles traces ; les auteurs et origines manquants ne sont pas inventés. Cette instrumentation doit être conservée et évaluée pour le futur ST ; elle ne constitue ni une nomination Phoenix ni une migration de données. Les traitements hors requête et les écritures en lot nécessitent une couverture explicite lors du futur développement.

## 4. Inventaire critique des permissions

Les droits actuels proviennent de plusieurs sources : flags User, rôle des adhésions, dirigeants CTM/WG, institution d’origine, titre des postes, filtrage des vues, permissions DRF, état du dossier et verrou de plateforme. Les groupes Django ne suffisent pas à décrire les autorisations réelles ; les tables locales d’appartenance aux groupes et de permissions utilisateur sont vides.

| Mécanisme | Comportement observé | Point à traiter lors de la future évolution |
|---|---|---|
| IsCTCCoordinator | Vérifie `is_ctc_staff` | Le nom laisse entendre une fonction de coordinateur que le flag seul ne vérifie pas. Ne pas en faire automatiquement une permission ST. |
| IsLegist | Vérifie un expert ACTIVE | Ne vérifie pas la fonction juridique ; certaines actions API légistiques sont plus larges que leur libellé. |
| IsExpertOfCTM | Vérifie l’affectation à obj.ctm, lorsqu’il existe | Vérifier son emploi effectif, le filtrage des listes et les actions de création ; une déclaration de classe seule ne suffit pas. |
| IsExpertOrCTC / IsOwnerOrCTC | Flags larges ; la seconde peut autoriser tout staff CTC sur un objet | Conserver les règles actives dans cette phase, mesurer leur portée avant d’en concevoir les équivalents. |
| Pilotage | Sous-rôle issu du rôle, de l’acronyme ou du titre du poste ; sélection par `.first()` | Ne pas identifier un nouveau pouvoir par un texte libre ou une institution ; traiter les mandats multiples explicitement. |
| CTC | Sous-rôle issu du rôle et de l’acronyme | Exemple ISO : l’interface autorise les deux veilleurs, mais CTCReviewActionView exige `veille_acgt` et l’expert assigné. À caractériser avant toute consolidation. |
| Actions Pilotage | Rôle et étape contrôlés dans les handlers de cadrage | Garder les doubles quitus, signatures et accusés de réception jusqu’à décision sur le nouveau circuit. |
| Dérogations | Les handlers d’approbation enregistrent décision et notification | Ces handlers ne créent pas à eux seuls une habilitation avec actions, périmètre et expiration. Vérifier les consommateurs des décisions avant d’afficher « accès accordé ». |
| Verrou global | Plusieurs actions web contrôlent PlatformFreeze | Ne pas présumer que toutes les écritures API, outils IA et tâches appliquent le même verrou ; vérifier chaque chemin concerné. |
| Audit | AuditLog, traces IA et suivi CTC par contexte de requête/signaux | Étendre explicitement la couverture au futur ST, aux lots et aux transitions ; conserver les traces CTC historiques et distinguer le journal de migration. |

La recherche trouve aussi des incohérences de référentiel : `CTM.get_member_count()` utilise des chemins d’affectation qui ne correspondent pas aux champs déclarés ; `OriginStructure` est interrogé comme s’il portait les experts alors qu’Expert référence `experts.Structure` ; l’action `CTMViewSet.roles` vise `ctm.roles`, relation absente du modèle examiné. Ce sont des risques issus de lecture statique, pas des pannes reproduites par des appels mutateurs.

**Principe futur proposé :** autoriser une action selon `(utilisateur, mandat/fonction, action, ressource, périmètre, version d’organisation, version de circuit, état, validité temporelle)`. L’interface choisie, le nom d’une SC, un acronyme et une correspondance ne confèrent jamais un droit. Les règles nouvelles seront refusées par défaut tant que leur mandat n’est pas confirmé ; les règles anciennes continueront à être évaluées par leur système actuel.

### Matrice de capacités Phoenix à instruire

Les fonctions et effectifs ci-dessous sont rapportés par la note ; les capacités sont des propositions de conception. **Aucun droit opérationnel Phoenix n’est accordé par cette matrice.** Toute action nouvelle reste désactivée tant que l’organisation, le mandat, le périmètre et la règle d’action ne sont pas validés. Même la consultation doit être accordée sur un périmètre explicite ; les indicateurs ne doivent pas révéler les dossiers hors périmètre.

| Fonction ou catégorie | Effectif rapporté | Consultation et suivi à préparer | Contribution à préparer | Décision, vote, homologation et publication |
|---|---|---|---|---|
| Présidence COPIL | 4 | Orientations, dossiers soumis et avis consolidés | Propositions d’orientation et d’arbitrage | Répartition entre président et trois vice-présidents à confirmer ; aucun pouvoir transféré depuis les anciens rôles. |
| Secrétariat COPIL | 2 | Calendrier, pièces, dossiers et suites des réunions autorisées | Préparation de séances, synthèses et suivi des décisions | Ne déduire aucun droit de décision de la fonction de secrétariat. |
| Membres COPIL | 7 | Dossiers relevant du mandat | Avis et réponses aux sollicitations | Quorum, vote, signatures et portée des avis à confirmer. |
| Invités COPIL | 3 | Séances et documents explicitement partagés | Contributions demandées, si habilitées | Aucun droit automatique de vote, validation ou publication. |
| Appoints COPIL | 6 | Périmètre d’appui à définir | Appui aux travaux selon mission confirmée | Missions précises à obtenir ; aucun pouvoir décisionnel automatique. |
| Coordination ST | 4 | Files, échéances et activité de l’équipe selon fonction | Réception, contrôle et coordination documentaire à spécifier | Répartition entre coordonnateur, adjoint et assistants ; conditions de transmission à confirmer. |
| Analyse documentaire ST | 4, dont un chef de pôle | Documents et contrôles affectés | Analyse documentaire et observations proposées | Avis techniques distincts d’une validation COPIL. Les fonctions des trois autres postes restent inconnues. |
| Appui technique et formation ST | 4, dont un chef de pôle | Besoins d’appui et pièces autorisées | Appui technique et formation proposés | Actions précises et délégations à confirmer. |
| Logistique et communication ST | 4, dont un chef de pôle | Calendrier et informations nécessaires à la mission | Logistique et communication proposées | Ne pas assimiler communication et publication officielle. |
| Relations extérieures et ARM ST | 4, dont un chef de pôle | Relations et pièces autorisées | Coordination des relations extérieures proposée | Sens détaillé d’ARM, pouvoirs de représentation et engagements à confirmer. |
| Coordination des SC ST | 4, dont un chef de pôle | SC et dossiers relevant du périmètre | Coordination, relances et consolidations proposées | Ne pas attribuer les décisions des SC au pôle ST. |
| Bureau, membres, observateurs et appoints SC | Effectifs non renseignés | Dossiers de la SC après habilitation | Encadrement, examens et contributions selon fonction | Composition détaillée, quorum, avis et signatures à confirmer ; observateur et membre ne sont pas équivalents. |
| GT | Catalogue et effectifs inconnus | Dossiers confiés au GT validé | Production et soumission de versions selon mandat | Ni pouvoir SC/ST/COPIL ni publication déduits de l’appartenance au GT. |

Prévoir des habilitations distinctes pour consulter un dossier, déposer une pièce, rédiger un avis, transmettre, décider, homologuer et publier. L’administration des comptes, l’attribution des mandats et l’activation d’une version d’organisation nécessitent aussi des habilitations dédiées ; aucune présidence, interface ou institution ne doit donner implicitement accès à l’administration Django.

Le Ministre apparaît comme président du COPIL dans la note. Cette identité de fonction ne fusionne pas la validation COPIL, l’homologation et la publication : chaque opération doit conserver son mandat, son état, ses preuves et sa trace.

## 5. Matrice CTM → SC proposée

Toutes les lignes suivantes sont des propositions analytiques. Les IDs sont ceux de la base locale et doivent être résolus à nouveau sur la base cible ; les numéros affichés ne sont pas des clés primaires.

| CTM / ID local | Cible principale proposée | Relations complémentaires / arbitrages |
|---|---|---|
| 1 / 14 — Géotechnique et risques naturels | SC-GF | Sols et stabilité vers GF ; risques/essais vers SOCLE ; interface ESS. |
| 2 / 15 — Ouvrages d’art | Plusieurs SC | IT/BAT/OH pour les applications ; SOCLE pour calcul/sismicité. Aucun successeur unique à imposer. |
| 3 / 16 — Bâtiment, urbanisme et transition numérique | SC-BAT | BIM transversal vers SOCLE ; géomatique vers SE·GEO·RS si le contenu le justifie ; interfaces ESS ; urbanisme à arbitrer. |
| 4 / 17 — Aéroports et transport aérien | SC-IT | Veille issue de l’ancienne note à confirmer pour Phoenix ; équipements et éventuelle contribution SE·GEO·RS à préciser ; conserver la conformité OACI. |
| 5 / 18 — Transports linéaires et maritimes | SC-IT | Activités de production/veille issues de l’ancienne note à confirmer ; contribution SE·GEO·RS candidate pour signalisation, géomatique et réseaux secs. |
| 6 / 19 — Eau et hydraulique | SC-OH | Réseaux, captage ; irrigation à arbitrer ; interfaces matériaux SOCLE. |
| 7 / 20 — Assainissement et déchets | SC-OH partiellement | Drainage et eaux usées ; déchets sans successeur explicite, interface ESS candidate. |
| 8 / 21 — Matériaux, métrologie et valorisation | SC-SOCLE | Recherche/simulation à ventiler ; certification en attente d’arbitrage et d’Infrastructure qualité. |

SC-SE·GEO·RS est désormais décrite dans la note Phoenix ; elle n’a pas pour autant un CTM prédécesseur unique confirmé. Les contributions candidates ci-dessus sont des hypothèses à arbitrer par contenu documentaire. La fusion est une convergence de plusieurs sources vers une cible, jamais la fusion destructive de leurs lignes. La scission est une source avec plusieurs liens de destination ; chaque lien précise son périmètre et sa nature : rattachement principal candidat ou interface de contribution. Un rattachement principal doit être établi **par dossier**, pas déduit mécaniquement du CTM.

### Matrice WG → domaines candidats de GT

La cible est volontairement un **domaine**, pas un GT officiel inventé. Le code GT et son identifiant resteront non renseignés jusqu’à réception du catalogue validé. Le rattachement des domaines aux SC et leur statut restent proposés.

| WG / ID local | Intitulé de la base locale | Domaine cible candidat | Qualification / vigilance |
|---|---|---|---|
| 1.1 / 36 | Sols & Géomécanique | GF sols/roches ; SOCLE essais | Périmètre différent de « Reconnaissance et essais » dans la note ; ventiler selon livrables. |
| 1.2 / 37 | Risques Naturels | SOCLE risques ; GF selon livrables | La note décrit 1.2 comme sols tropicaux : ne pas reprendre sa correspondance par numéro. |
| 1.3 / 38 | Stabilité & Érosions | GF fondations/soutènements ; SOCLE risques | Contribution multiple à confirmer. |
| 2.1 / 39 | Calcul Structural & Eurocodes | SOCLE bases de calcul ; IT/BAT applications | Scission fonctionnelle. |
| 2.2 / 40 | Génie Parasismique | SOCLE sismicité ; IT/BAT applications | Scission fonctionnelle. |
| 2.3 / 41 | Ouvrages Hydrauliques Lourds | OH ouvrages/barrages | Transfert proposé. |
| 3.1 / 42 | Habitabilité & Sécurité | BAT bâtiments ; ESS sécurité | Correspondance partielle. |
| 3.2 / 43 | BIM & Transition Numérique | SOCLE BIM transversal ; SE·GEO·RS pour géomatique si applicable | Correspondance multiple candidate ; contenu et rattachements à confirmer. |
| 3.3 / 44 | Performance Énergétique & Coûts | BAT ; ESS climat | Volet coûts absent de la correspondance documentaire : à préciser. |
| 4.1 / 45 | Infrastructure Aéroportuaire | IT aéroports, veille | Ne pas convertir la veille en production par défaut. |
| 4.2 / 46 | Terminaux et Équipements | IT aéroports ; SE·GEO·RS équipements si applicable | Diffère de l’ancienne note ; contribution Phoenix à confirmer. |
| 4.3 / 47 | Conformité OACI | IT aéroports ; conformité à préciser | Absent des 23 WG de la note : conserver, rattachement en attente. |
| 5.1 / 48 | Ingénierie Routière | IT routes/chaussées ; SE·GEO·RS pour signalisation/réseaux secs si applicable | Correspondance IT forte ; contribution complémentaire proposée. |
| 5.2 / 49 | Voies Ferrées | IT ferroviaire, veille | Activité et mandat à confirmer. |
| 5.3 / 50 | Infrastructures Portuaires | IT ports, veille | Activité et mandat à confirmer. |
| 6.1 / 51 | Adduction d’Eau | OH réseaux hydrauliques | SOCLE matériaux si le contenu le justifie. |
| 6.2 / 52 | Irrigation et Drainage | OH candidat ; drainage à préciser | À arbitrer ; correspond au volet agricole et non aux forages 6.2 de la note. |
| 6.3 / 53 | Forages et Captage | OH réseaux/captage | À préciser ; ne pas lui appliquer le volet agricole 6.3 de la note. |
| 7.1 / 54 | Macro-drainage & Eaux Pluviales | OH assainissement/drainage | Correspondance forte. |
| 7.2 / 55 | Eaux Usées & Réseaux d’Égouts | OH assainissement/drainage | Correspondance forte. |
| 7.3 / 56 | Déchets Solides & CET | Aucun successeur confirmé ; ESS candidate | Conserver « à rattacher » avec propriétaire historique. |
| 8.1 / 57 | Matériaux Géo-sourcés & Locaux | SOCLE matériaux locaux | La note parle de biosourcés : vérifier la portée exacte. |
| 8.2 / 58 | Essais & Métrologie Légale | SOCLE essais/métrologie | Volet métrologie légale à confirmer. |
| 8.3 / 59 | Simulation, Recherche & Certification | SOCLE candidat pour recherche/simulation ; certification en attente | Périmètre plus large que la certification seule ; ne pas transférer l’ensemble vers qualité. |

Chaque source reste présente, même sans cible. À réception des GT définitifs, chaque ligne donnera un ou plusieurs liens source/cible assortis de la source documentaire, du périmètre couvert, du responsable d’arbitrage et de la décision. Aucun lien « proposé » ne changera une affectation, un accès ou une norme.

## 6. Architecture de coexistence proposée

### Couche additive, indépendante du fonctionnement actif

Les modèles et tables historiques sont conservés. Les objets suivants ont été introduits par migrations additives ; ils restent sans effet sur le circuit historique tant qu’une version et un circuit Phoenix ne sont pas explicitement activés :

| Objet proposé | Rôle et informations minimales |
|---|---|
| OrganisationVersion | Édition, source documentaire, statut proposé/validé/actif, référence de décision et dates. Une organisation proposée peut être consultée sans être active. |
| Organe | Version, type COPIL/ST/pôle ST/SC, code et libellé, parent éventuel, statut et période ; cinq pôles ST distincts ; liens historiques uniquement quand la continuité est confirmée. |
| PosteOrganisation | Organe, catégorie, fonction rapportée ou non renseignée, origine requise si connue, source et statut. Préparer 22 postes COPIL et 24 postes ST ; les postes SC restent configurables, sans effectif inventé. |
| GroupeCible | Organe SC, code officiel, intitulé, activité production/veille, statut et période. Aucun enregistrement officiel sans catalogue ; les domaines candidats restent dans le registre de correspondance. |
| CorrespondanceStructure / CorrespondanceGroupe | FK protégée CTM/WG source, cible candidate ou cible officielle, domaine, nature du lien, justification, statut, source et décision. Multiples liens autorisés ; pas de FK générique pour les liens structurants. |
| MandatOrganisation | Expert, poste ou groupe validé, fonction, acte, début/fin et statut. Mandats multiples explicites ; aucun titulaire fictif ni compte créé automatiquement depuis le catalogue. |
| HabilitationAction | Mandat, action, périmètre et validité ; délégation éventuelle tracée. Composition et pouvoirs doivent être confirmés avant attribution. |
| RattachementDocumentaire | Norme, version d’organisation, propriétaire cible proposé/validé et interfaces contributrices. Préserve Norme.ctm/wg comme origine ; historique daté des rattachements. |
| JournalMigration | Acteur, cible, opération, ancien/nouveau rattachement, date, motif, décision et identifiant de lot. Les décisions antérieures ne sont pas réécrites. |

La structure d’origine d’un poste cible est un critère documentaire, pas une preuve d’identité : « Directeur DRN » ne suffit pas à sélectionner un utilisateur. Une origine inconnue reste vide. Les référentiels `experts.Structure` et `OriginStructure` ne sont pas fusionnés automatiquement pour accueillir ECOSYS ou une autre institution mentionnée par Phoenix.

Les codes de postes proposés dans le référentiel annexe sont des identifiants de conception. Ils ne sont ni des numéros officiels de la matrice ni les anciennes PK. Les fonctions non renseignées des pôles ST ne sont pas remplacées par les anciens rôles CTC supposés équivalents.

L’approbation d’une correspondance, sa prise d’effet et l’activation d’un circuit sont trois opérations différentes. Le système doit les distinguer. Un organe proposé peut apparaître dans une prévisualisation sans participer aux décisions actives.

### Résolution du contexte

```text
Compte existant + adhésions + flags ──→ évaluateur actuel ──→ dossier ancien
                                              │
                                              └──→ composants communs d’interface
Manuel confirmé + mandats + habilitations ──→ évaluateur futur ──→ dossier nouveau
                    ↑
      référentiel cible + correspondances validées
```

Le contexte d’organisation affiché et le circuit opérationnel d’un dossier sont distincts. Consulter une SC cible ne fait pas entrer une ancienne norme dans le nouveau workflow. Une correspondance multiple ne duplique ni dossier ni autorisation.

Les anciens dossiers restent attachés à leur circuit historique. `Norme.circuit_version` distingue désormais `LEGACY` de `PHOENIX`. Les FK CTM/WG restent obligatoires pour l’ancien circuit et peuvent être absentes uniquement pour un nouveau dossier Phoenix possédant un rattachement SC/GT validé. Tous les liens historiques restent intacts et aucun faux CTM/WG n’est créé. Les gestionnaires de modèles, serializers v1, filtres, exports, notifications, réunions et outils IA appliquent cette séparation.

### Compatibilité des interfaces publiques

- Maintenir les routes, payloads et champs CTM/WG des API `/api/v1/` existantes pour les consommateurs actuels.
- Le contrat séparé `/api/v2/organisation/` expose le référentiel, sa configuration, sa mise en service contrôlée, les dossiers, opérations, pièces protégées et exports, sans renommer les endpoints v1 existants.
- Les contextes d’interface et l’API v2 exposent les transitions calculées par le serveur et le mandat sélectionné ; les droits fournis par le navigateur ne servent jamais de preuve d’autorisation.
- Les dossiers du nouveau circuit resteront hors des endpoints v1 supposant CTM/WG jusqu’à adaptation explicite de leur contrat. Documenter cette limite pour les clients mobiles avant l’activation.
- Conserver références publiques, anciens liens et exports archivés. Adapter les nouvelles références dans les futurs exports sans modifier les fichiers déjà signés.

## 7. Évolution nécessaire du circuit de validation

Il existe trois niveaux de suivi distincts dans le code :

1. `Norme.status` : DRAFT, INTERNAL_REVIEW, CTM_REVIEW, LEGISTIC_REVIEW, PUBLIC_INQUIRY, PILOTAGE_REVIEW, FINAL_REVIEW, ADOPTED, HOMOLOGATED, PUBLISHED, ARCHIVED ; transitions contrôlées par `workflow_transitions()`.
2. `CTCProcessus` : RECEPTION → GEOSPATIAL si nécessaire → MULTI_REVIEW → INDUSTRIAL → SIGNED_OUT. Réception, indexation et validation d’entrée précèdent l’initialisation des examens. La signature/transmission avance le statut macro vers PILOTAGE_REVIEW.
3. `NormeCadrage` : PROPOSED → EXPERTS_REVIEW avec deux validateurs → MANDATE_FORMALIZATION → SCHEDULED ; la méthode de programmation avance ensuite vers PV_VERIFICATION. Le retour CTC et les deux accusés de réception conditionnent la vérification du PV, puis viennent CONFORMITY_QUITUS, FINAL_VALIDATION et COMPLETED.

Les cinq sous-étapes internes de la CTC ne sont pas les cinq niveaux GT → SC → ST → COPIL → Ministre. Les assimiler supprimerait des contrôles documentaires et confondrait traitement technique, décision et sanction ministérielle.

| Responsabilité future | Capacité à prévoir | Question laissée ouverte |
|---|---|---|
| GT | Production, rédaction et soumission d’un projet versionné | Mandat, responsable de soumission, validation interne et retours. |
| SC | Encadrement, examen et consolidation technique | Quorum, avis, signature, contributions multi-SC et renvoi vers GT. |
| ST | Coordination, complétude, traçabilité et contrôle documentaire | Examens conservés, indépendance des avis, enquête publique et pouvoirs de transmission. |
| COPIL | Orientation, supervision, arbitrage et validation | Nouveaux pouvoirs par poste, composition, signatures et portée de chaque décision. |
| Ministre | Décision finale selon texte applicable | Distinguer validation COPIL, adoption, homologation et publication officielle. |

### Parcours fonctionnel implémenté, à paramétrer par décision

Le moteur organise le parcours suivant. Le canevas livré reste inactif : il ne devient un circuit institutionnel qu’après saisie d’une configuration et d’une référence approuvées.

```text
GT : produire une version et ses pièces
  → SC : examiner et consolider les contributions techniques
  → ST : réceptionner, contrôler et coordonner les pièces et avis requis
  → COPIL : orienter, arbitrer ou prendre la décision expressément autorisée
  → Homologation et publication : opérations distinctes à spécifier
```

Chaque point de passage doit définir les conditions d’entrée, l’auteur habilité, la version examinée, les avis nécessaires, la décision, les pièces justificatives et les possibilités de retour. Prévoir des retours SC → GT, ST → SC/GT et COPIL → ST/SC **à faire confirmer**, sans écraser la version initiale ni un avis antérieur. Aucun état ancien ne sera converti par sa seule ressemblance avec une étape cible. L’enquête publique, les consultations et les signatures du circuit actuel restent en place tant que leurs équivalents ne sont pas validés.

### Suivi des équipes et des documents

Prévoir une supervision par organe, pôle, SC et mandat : acteur, opération, date, dossier, version ou document, origine de l’action et résultat. Les graphiques doivent être calculés sur les seules ressources consultables. Distinguer opérations enregistrées, traces historiques, auteurs inconnus et absence d’activité ; un nombre d’actions n’est pas une mesure de temps de travail.

Les composants de l’activité CTC peuvent être réutilisés pour la présentation du suivi ST, avec un nouveau contexte d’organisation et des permissions validées. Les routes et journaux CTC restent attachés au circuit historique. Conserver les empreintes et références documentaires ; ne pas réécrire une trace ancienne pour lui attribuer un nouveau poste, une SC ou une origine manquante.

Modifications techniques réalisées :

- Un identifiant de version de circuit par dossier ; l’historique est affecté explicitement à l’ancien circuit et n’est jamais recalculé d’après son propriétaire affiché.
- Un service de transition partagé entre web et API, également interrogé par l’IA sans lui permettre d’écrire une décision. Chaque action vérifie permission, état, preuves et version avant écriture.
- Des événements de transition datés et attribués, avec preuve documentaire et décision ; transactions atomiques, prévention des doubles signatures et notifications après validation de la transaction.
- Un nouveau circuit désactivé jusqu’à définition des règles officielles. Aucun rapprochement automatique entre anciens états et nouvelles étapes.
- Conservation des anciens avis et dates ; un nouvel examen éventuel ne remplace pas un avis historique et doit être rattaché à la version documentaire examinée.

Les chemins historiques ne sont pas réécrits par Phoenix : `set_step`, les mises à jour légistiques, la réception et `mark_signed_out` restent le moteur des seuls dossiers `LEGACY`. Les dossiers Phoenix utilisent leur service transactionnel séparé. Cette séparation évite qu’une nouvelle règle modifie rétroactivement le circuit CTC/Pilotage.

## 8. Conservation, recette et progression

« Ne rien perdre » doit être vérifiable. Les contrôles FK effectués aujourd’hui sont utiles mais ne prouvent ni l’exhaustivité documentaire ni une restauration possible.

### Sauvegarde appliquée avant les écritures de migration

- Identifier la base et le stockage réellement utilisés ; exporter une sauvegarde cohérente de base **et** média, ainsi que les paramètres nécessaires à leur restauration, dans un emplacement protégé.
- Tester la restauration sur un environnement isolé. Les pièces externes, imports, fichiers RAG et références JSON/textuelles entrent dans le périmètre ; une copie de db.sqlite3 seule ne suffit pas.
- Établir un manifeste : volumes par modèle, ensembles d’IDs, liens, statuts/dates, auteurs, mandats, références de fichiers et empreintes. Utiliser un instantané cohérent pour éviter de comparer des états séparés par des écritures métier légitimes.
- Qualifier les anomalies locales et celles de la copie cible ; proposer une correction distincte, attribuée et approuvée si nécessaire. Ne pas fabriquer une signature manquante.

### Recette exécutée lors du développement

| Scénario | Résultat attendu |
|---|---|
| Ajout d’une organisation proposée | Aucune modification des comptes, FK historiques, droits ou états actifs. |
| CTM 2 vers plusieurs SC ; CTM 4/5 vers IT | Toutes les origines restent consultables ; aucun dossier dupliqué. |
| WG 4.3, déchets, irrigation, certification | Cas « à rattacher » visibles avec source et arbitrage ; aucun groupe perdu ou cible inventée. |
| Numéro métier différent de l’ID | La résolution s’appuie sur les objets et leur source ; aucune hypothèse ID = numéro. |
| Ancien dossier vu sous une SC candidate | Son circuit, ses acteurs et ses permissions restent historiques. |
| Changement d’interface ou de paramètre POST | Aucun pouvoir supplémentaire ; refus serveur pour action hors mandat/périmètre/étape. |
| Même institution, deux fonctions différentes | Habilitations distinctes ; pas de déduction automatique depuis l’acronyme. |
| Poste vacant ou adhésion sans poste | Aucun pouvoir de poste attribué par défaut ; état explicite. |
| Catalogue Phoenix | Exactement 22 postes COPIL et 24 postes ST ; catégories 4/2/7/3/6 ; coordination 4 et cinq pôles de 4 ; aucun nouveau compte ni ancien poste supprimé. |
| Quinze fonctions non renseignées des pôles ST | Trois emplacements par pôle restent sans intitulé ni titulaire inventé. |
| Sept fiches SC, dont SC-SE·GEO·RS | Codes et domaines proposés conservés ; noms officiels, effectifs et GT inconnus restent non renseignés. |
| Invité, membre et appoint | Catégories distinctes ; aucun droit de vote, validation, homologation ou publication accordé par défaut. |
| Ministre également président COPIL | Mandats et preuves distincts pour décision COPIL, homologation et publication. |
| Même personne au COPIL et au ST | Compte unique, mandats séparés, sélection explicite du contexte et absence de cumul implicite des droits. |
| Supervision ST et historique CTC | Filtrage avant graphiques et journal ; traces CTC conservées ; pas de réattribution des anciennes actions. |
| Délégation expirée, expert suspendu, dossier verrouillé | Règles applicables vérifiées côté serveur et via API/IA. |
| Double clic ou deux signatures simultanées | Une seule transition valide, trace unique, pas de notification fantôme. |
| Régression ancien circuit | Réception/indexation, SIG, examens, consultation, transmission, doubles accusés et cadrage restent utilisables. |
| Retour à l’ancien affichage | Désactivation des écrans cibles sans effacement des propositions ou traces ; dossiers anciens toujours accessibles. |

### Progression et critères de passage

| Phase | Travail et livrables | Critère de passage |
|---|---|---|
| 0 — Cadrage documentaire Phoenix | Inventaire daté, catalogue 22/24, sept fiches SC, correspondances pour les huit CTM et 24 WG locaux, matrice de capacités, nouvelles interfaces, parcours proposé et tests | Dossier de conception relu ; chaque hypothèse et information manquante identifiée. Aucun organe activé. |
| 1 — Référentiel proposé en environnement isolé | Schéma additif, version Phoenix proposée, postes sans titulaires fictifs, fiches SC, registre de correspondance ; aucun GT inventé | Recette de conservation des données et accès anciens ; sauvegarde restaurée et ajouts désactivables. |
| 2 — Mandats et habilitations | Nomination explicite, périmètres, délégations, fonctions des pôles et règles par action ; essais des interfaces selon droits | Capacités approuvées et vérifiées côté serveur, API et IA ; catégories invités/appoints/membres distinctes. |
| 3 — Nouveau circuit en préproduction | États, retours, quorum, examens, enquête, signatures, adoption, homologation et publication spécifiés ; essais de concurrence et de traçabilité | Règles institutionnelles confirmées et recette complète ; aucune assimilation automatique au circuit actuel. |
| 4 — Activation contrôlée | Nouvelle version active et circuit validé pour les nouveaux dossiers seulement, avec journal d’activation et supervision | Décision de mise en service identifiée ; dossiers historiques inchangés et procédure de suspension testée. |

Les fonctions logicielles des phases 1 à 4 sont implémentées : mandats et délégations datés, habilitations par action et périmètre, circuit versionné, quorum et preuves, enquête, réunions, décisions séparées d’adoption/homologation/publication, concurrence optimiste, journal, supervision, API v2 et garde-fous IA. La base principale porte désormais la version et les sept SC au statut `VALIDATED`. Les 109 rattachements certains sont actifs dans ce référentiel ; les 40 autres sont explicitement en examen. Aucun GT officiel, mandat, habilitation ou circuit réel n’a été fabriqué, et le statut `ACTIVE` reste réservé à la future mise en service du circuit.

### Décisions encore requises

| Décision | Information disponible | Information à confirmer |
|---|---|---|
| Composition cible | COPIL 22, ST 24 et sept SC rapportés dans la note | Rapprochement avec la matrice source et acte applicable ; occupants et nominations. |
| Sous-commissions | Sept codes et domaines de préparation | Dénominations officielles, périmètres, composition détaillée et effectifs. |
| Groupes de travail | Rattachement futur aux SC | Catalogue officiel, codes, mandats, activité et rattachements ; aucun effectif cible imposé. |
| Pôles ST | Cinq pôles, quatre postes chacun et origine des chefs | Intitulés et fonctions des quinze autres postes, titulaires et délégations. |
| COPIL | Cinq catégories, dont invités et appoints | Répartition des pouvoirs entre les 22 postes ; vote, quorum, avis, signatures et droits des invités/appoints. |
| Circuit | Fonctions GT, SC, ST et COPIL décrites | Conditions d’entrée/sortie, retours, enquête publique, consultations et séparation des décisions finales. |
| Correspondances | Huit CTM et 24 WG conservés dans la matrice candidate | Sources et responsables des cas multiples ou sans successeur ; rôle exact de SC-SE·GEO·RS. |
| Dénominations particulières | SC-SOCLE reste provisoire | Éventuel SC-RTN ; aucune activation d’Infrastructure qualité. |

### Vérification de cette mise à jour documentaire

La recette automatisée vérifie les sommes 4 + 2 + 7 + 3 + 6 = 22 et 4 + 5 × 4 = 24, l’unicité des codes internes, les sept fiches SC et la conservation des 24 lignes WG historiques. Elle couvre aussi les droits serveur/API/IA, le quorum, l’idempotence, la concurrence, les fichiers privés, l’historique, les retours, les réunions, les délégations et la suspension. Les résultats courants et la procédure sont consignés dans le rapport d’implémentation.

**Limite de retour arrière :** avant activation, les ajouts peuvent être désactivés sans toucher au système historique. Après création de dossiers dans un nouveau circuit, un retour arrière ne doit ni supprimer ces dossiers ni tenter de les faire traiter par l’ancien moteur sans règle validée. Il devra préserver leur version, leurs preuves et leurs accès de consultation, et suspendre leurs nouvelles transitions si nécessaire.
