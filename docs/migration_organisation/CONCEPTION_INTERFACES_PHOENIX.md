# Conception des interfaces de l’organisation CNE-ITP Phoenix

Date : 13 octobre 2026. Statut : proposition fonctionnelle, sans remplacement des écrans ou des droits actifs.

Cette conception s’appuie sur la [note Phoenix](<../../Cadrage_nouvelle_structure_CNE_ITP_Phoenix (4).docx>) et sur le [référentiel des postes et SC](REFERENTIEL_PHOENIX.md). Elle remplace, pour la cible nouvelle, le découpage des 27 anciens postes. [L’ancienne conception](CONCEPTION_INTERFACES.md) reste une archive historique.

Le choix de cinq compositions COPIL est une proposition de présentation fondée sur les cinq catégories décrites dans la note. Ce nombre d’interfaces n’est pas une règle institutionnelle et ne définit aucun droit de vote ou de décision.

## 1. Cinq compositions pour les 22 postes du COPIL

| Composition proposée | Catégorie Phoenix | Postes du catalogue | Modules métier à préparer | Limite d’autorisation |
|---|---|---|---|---|
| Présidence et orientation | Présidence, 4 postes | COPIL-PRES-01 à 04 | Orientations, arbitrages, dossiers soumis, avis consolidés et suites des décisions | Pouvoirs du président et des trois vice-présidents à confirmer séparément. |
| Secrétariat et coordination des travaux | Secrétariat, 2 postes | COPIL-SEC-01 à 02 | Calendrier, préparation des séances, pièces, synthèses et suivi des décisions | La préparation d’un dossier ne donne pas le pouvoir de le valider. |
| Membres et contributions | Membres, 7 postes | COPIL-MEM-01 à 07 | Dossiers confiés, avis sollicités, observations et suivi des réponses | Un directeur général n’obtient pas automatiquement tous les droits de son institution ou un accès financier global. |
| Invités et consultations | Invités, 3 postes | COPIL-INV-01 à 03 | Séances et pièces partagées, contributions expressément autorisées | Aucun vote, validation, homologation ou publication accordé par la seule qualité d’invité. |
| Appoints et missions d’appui | Appoints, 6 postes | COPIL-APP-01 à 06 | Missions et pièces autorisées, contributions et suivi à préciser | La note donne les origines et effectifs, pas les missions détaillées ; les actions restent sans habilitation tant qu’elles ne sont pas confirmées. |

Tous les postes sont couverts une fois par la présentation proposée : **4 + 2 + 7 + 3 + 6 = 22**. Une personne exerçant plusieurs mandats sélectionne explicitement son contexte ; les actions de deux compositions ne sont pas réunies par défaut.

## 2. Présentation commune et comportement attendu

Une même enveloppe de navigation dessert des compositions de modules, sans créer 22 applications ni recopier les droits dans cinq pages.

```text
Compte existant
  → Mandat sélectionné et organisation correspondante
  → Composition de présentation
  → Dossiers, pièces, indicateurs et actions filtrés par le serveur
```

Navigation à préparer selon le mandat : tableau de bord, dossiers confiés, documents et versions, contributions ou avis, calendrier, suites des décisions et historique. La supervision des équipes et le registre de correspondance apparaissent uniquement lorsqu’une habilitation spécifique autorise leur consultation.

L’écran présente l’organisation proposée ou en vigueur, la fonction exercée et le contexte du dossier. Les dossiers anciens conservent leur circuit et leurs responsables historiques. Un dossier consulté depuis une SC proposée ne devient pas un dossier de cette SC.

Une action disponible précise le dossier, la version examinée, l’effet attendu et les preuves exigées. Le serveur vérifie à nouveau le mandat, le périmètre, l’état, la validité, les délégations et le verrou avant écriture. Aucune composition ne donne implicitement accès à l’administration Django.

États à distinguer : poste non attribué, fonction à confirmer, mandat expiré, action sans habilitation, dossier hors périmètre, absence de données et information historique non enregistrée. Une adhésion historique sans poste n’est pas remplacée par une attribution au premier poste Phoenix.

## 3. Espace du Secrétariat technique

Le ST dispose d’un espace de coordination et de files de travail par pôle, distinct des cinq compositions COPIL. Le catalogue contient quatre postes de coordination et cinq pôles de quatre postes ; les quinze fonctions non renseignées ne sont pas inventées pour remplir une interface.

| Ensemble ST | File et modules à spécifier | Point de validation |
|---|---|---|
| Coordination | Réception, complétude, échéances, affectations, contrôle et suivi de l’équipe | Partage des actions entre coordonnateur, adjoint et deux assistants ; conditions de transmission. |
| Analyse documentaire | Pièces et examens documentaires affectés, observations et versions | Contrôles requis et fonctions des trois postes non renseignés. |
| Appui technique et formation | Besoins d’appui, ressources et formations autorisées | Nature des interventions et délégations. |
| Logistique et communication | Calendrier, préparation logistique et informations à communiquer | Destinataires et périmètre de diffusion ; aucune publication officielle implicite. |
| Relations extérieures et ARM | Sollicitations et pièces de coopération autorisées | Sens détaillé d’ARM et pouvoirs de représentation. |
| Coordination des sous-commissions | Suivi des sept SC, relances, contributions et consolidations | Périmètre de coordination et distinction avec les avis ou décisions des SC. |

Le suivi peut réutiliser les composants de graphiques, journal, équipe, documents et dossiers déjà présents dans l’activité CTC. Leurs données doivent être filtrées par organisation, pôle et mandat ; les routes, les permissions et les traces historiques CTC sont conservées. La réutilisation d’une présentation ne migre pas les 20 anciens postes CTC vers les 24 postes ST.

## 4. Espaces SC et GT

Prévoir une composition d’encadrement technique configurable pour chacune des sept SC proposées : bureau, contributions affectées, dossiers, pièces, avis, retours et historique, selon habilitation. Membres, observateurs et appoints sont des catégories distinctes. Les effectifs, titulaires et droits absents de la source restent non renseignés.

L’espace GT sera centré sur la production de versions et la soumission d’un dossier selon mandat validé. Son catalogue et ses rattachements aux SC doivent être reçus avant peuplement ; ne pas générer des groupes pour reproduire les anciens nombres ou contourner `Norme.ctm`/`Norme.wg`.

Le parcours fonctionnel proposé et les possibilités de retour figurent dans le [plan principal](../../PLAN_MIGRATION_ORGANISATION.md). Ils ne doivent pas être implantés comme un nouvel enchaînement d’états avant validation des règles d’approbation.

## 5. Supervision des équipes et des documents

Pour chaque ressource autorisée, présenter qui a fait quoi, quand, sur quelle version ou pièce et depuis quel espace. L’IP source et le navigateur ne sont affichés que s’ils ont été enregistrés et si l’habilitation permet ces données ; ne pas les convertir en localisation géographique certaine.

Graphiques proposés : répartition des opérations, contributions par collaborateur, état des dossiers et évolution quotidienne. Filtres : période, organe/pôle/SC, mandat, collaborateur, action et document. Les totaux sont calculés sur le même périmètre que le journal ; préciser quand un graphique représente l’état actuel plutôt que l’activité de la période.

Distinguer les nouvelles traces des traces historiques, les actions réussies des refus et les modifications persistées des opérations annulées. Conserver un document supprimé dans son historique d’opérations. Ne pas remplir les informations anciennes manquantes par déduction depuis la personne actuellement affectée.

Le nombre d’opérations ne constitue pas une mesure de durée, de présence ou de performance individuelle. Les écritures automatiques déclenchées par une action doivent être distinguées des contributions manuelles lorsque leur regroupement est présenté.

## 6. Contrôle de cohérence des interfaces

- Les cinq compositions COPIL couvrent les 22 postes du catalogue Phoenix, et non les anciennes plages 1–5/6–12/13–17/18–22/23–27.
- Les quatre postes de coordination ST et les cinq pôles restent identifiables sans inventer les quinze fonctions manquantes.
- Invités, appoints et membres ne reçoivent aucun pouvoir par leur seule catégorie ; un poste vacant ne donne aucun droit.
- Les comptes existants peuvent porter plusieurs mandats, sélectionnés explicitement, sans fusion des autorisations.
- Une action interdite reste refusée via URL directe, paramètres POST, API et assistant IA, même si un composant est visible.
- Les indicateurs, recherches, pièces et journaux n’exposent aucune ressource hors périmètre ; absence d’activité et absence d’enregistrement restent distinctes.
- Les espaces CTC/Pilotage historiques restent utilisables pour les dossiers anciens ; aucune transition ne dépend d’un libellé de navigation.
- Aucun nouveau GT, pouvoir, quorum ou titulaire n’est déduit du choix de présentation.
