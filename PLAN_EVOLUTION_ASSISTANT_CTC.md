# Plan d'évolution de l'assistant IA de la plateforme

## 1. Positionnement et périmètre

L'assistant IA est actuellement un assistant d'analyse connecté à DeepSeek. Il fonctionne dans plusieurs contextes de la plateforme et conserve les conversations par session.

Le CTC constitue un premier domaine métier important, mais l'ambition est de couvrir progressivement toute la plateforme : experts, CTM et groupes de travail, normes, gouvernance, pilotage, réunions, enquêtes publiques, documents, notifications et données administratives autorisées.

L'assistant est un prototype d'analyse et de préparation d'actions. Il ne doit pas encore être considéré comme un opérateur autonome ni comme une source officielle de décision.

Il sait notamment :

- rechercher des experts, leurs coordonnées, CV, affectations, présences et votes ;
- lister les CTM, les groupes de travail et les normes ;
- détecter des chevauchements potentiels entre groupes de travail ;
- rechercher dans quelques référentiels locaux ISO/ARSO ;
- préparer une synthèse des amendements de l'enquête publique à partir d'un sous-ensemble de données ;
- produire des graphiques pour le pilotage ;
- préparer des brouillons d'emails ;
- créer des brouillons de signalements, de propositions de normes et de demandes d'affectation ;
- afficher les résultats dans l'interface sous forme d'artefacts.

Les outils sont enregistrés dans `apps/ia_agent/tools/` et exécutés par `apps/ia_agent/services/agent_runner.py`. Ils sont actuellement organisés par périmètre `expert`, `ctc` et `pilotage`.

## 2. Limites fonctionnelles actuelles

L'assistant ne peut pas encore :

- chercher dans toute la bibliothèque documentaire et les données métier de la plateforme ;
- lire correctement tous les PDF, DOCX, XLSX, PPTX et documents scannés ;
- comprendre le contexte de l'écran actuellement ouvert par l'utilisateur ;
- ouvrir automatiquement un dossier ou une norme précise dans l'interface ;
- exécuter de manière unifiée les opérations métier des différents modules ;
- déclencher les étapes CTC existantes avec contrôle complet du rôle, de l'objet et de l'état du processus ;
- affecter réellement un expert ou une revue ;
- valider un examen, une consultation industrielle ou une transmission ;
- créer et gérer de bout en bout les réunions, convocations, notifications et calendriers ;
- modifier directement une norme, un expert, une affectation, une réunion ou un processus ;
- consulter réellement les espaces Drive et les documents associés ;
- effectuer des recherches Internet ou réglementaires actualisées ;
- garantir des réponses avec des citations précises vers les sources utilisées.

Les actions sensibles sont encore principalement préparées sous forme de brouillons. Un envoi d'email, une modification de donnée ou une transition de workflow doivent nécessiter une confirmation explicite et un contrôle côté serveur.

## 3. Risques et limites transversaux

- Les droits sont principalement contrôlés par le contexte fonctionnel, et pas toujours par une permission détaillée sur chaque objet, champ et opération.
- Certains outils peuvent retourner des informations sensibles : coordonnées, données personnelles ou informations financières.
- Les recherches reposent souvent sur des mots-clés et une similarité lexicale ; elles peuvent donc produire des faux positifs, manquer des résultats ou confondre des versions.
- L'assistant dépend actuellement de DeepSeek. Le modèle, sa version, sa disponibilité et ses conditions de traitement doivent être gouvernés.
- Des CV, coordonnées, informations financières ou documents internes peuvent être transmis au fournisseur LLM si les données ne sont pas filtrées en amont.
- Les documents importés peuvent contenir des instructions malveillantes destinées à influencer l'assistant ; leur contenu ne doit jamais être traité comme une instruction système.
- Il ne possède pas encore de véritable mémoire métier durable en dehors de l'historique de session.
- Les actions complexes ne sont pas encore entièrement transactionnelles ni auditées de bout en bout.
- Les résultats sont parfois limités en nombre et ne couvrent pas nécessairement tout le corpus.
- La conservation des conversations, des sorties d'outils et des données sensibles doit être encadrée par une politique de rétention.
- Un score de confiance ne doit pas être présenté comme une garantie ; les sources, extraits et incertitudes sont prioritaires.

## 4. Feuille de route pour un assistant de plateforme

### Priorité 0 — Sécurité et contrat d'action

Avant l'ouverture d'actions sensibles, mettre en place :

- une autorisation au niveau objet, champ et opération ;
- un filtrage des données avant tout envoi au LLM ;
- une politique de conservation et de suppression des conversations et sorties d'outils ;
- un audit des consultations, validations, envois et transitions ;
- des contrôles d'état côté serveur et une protection contre les doubles exécutions ;
- une confirmation serveur obligatoire pour les actions importantes ;
- une séparation stricte entre le contenu d'un document et les instructions de l'assistant.

L'assistant ne doit jamais approuver, transmettre, supprimer ou envoyer un élément important sans confirmation de l'utilisateur autorisé.

### Priorité 1 — RAG documentaire et métier global

Mettre en place un RAG hybride, versionné et soumis aux permissions, couvrant progressivement :

- les normes et leurs versions ;
- les dossiers CTC et leurs étapes ;
- les documents déposés et leurs métadonnées ;
- les CV et pièces des experts ;
- les procès-verbaux, réunions et amendements ;
- les référentiels ISO/ARSO validés ;
- les espaces Drive lorsque leur accès est autorisé ;
- les procédures internes, décisions, notifications et données de pilotage autorisées.

Le RAG devra intégrer :

- l'extraction structurée des PDF, DOCX, XLSX et PPTX ;
- l'OCR pour les documents scannés ;
- la conservation des pages, titres, articles, tableaux, annexes et versions ;
- un découpage par sections et articles avec conservation du contexte parent ;
- une recherche hybride plein texte et sémantique ;
- un reranking des passages pertinents ;
- des filtres par rôle, objet, module, dossier, statut et version ;
- des citations précises : source, version, page, section et lien ;
- la comparaison de versions et la synthèse de documents longs.

Le RAG ne doit pas envoyer un document entier au modèle par défaut. Il doit fournir uniquement les passages autorisés et nécessaires à la réponse. Les index et embeddings devraient rester internes lorsque cela est possible.

La première version doit rester limitée à un périmètre pilote : un type de document normatif, quelques dossiers et documents de la plateforme, la recherche sourcée, la synthèse d'un document long et la comparaison de deux versions.

### Priorité 2 — Contexte de l'interface

Transmettre à l'assistant :

- l'écran courant ;
- le module et le dossier, la norme ou l'objet sélectionné ;
- le rôle exact de l'utilisateur ;
- l'étape actuelle du processus ;
- les documents liés ;
- les actions disponibles pour ce rôle et cet objet.

L'utilisateur devrait pouvoir dire « analyse ce dossier » ou « prépare la réponse à ce document » sans fournir manuellement un identifiant.

### Priorité 3 — Actions métier de la plateforme

Les opérations existantes de la plateforme doivent être exposées progressivement par des services métier communs au web, à l'API et à l'assistant. L'assistant ne doit pas modifier directement les modèles.

Les premiers domaines à couvrir sont :

- réception, indexation, validation et transmission des dossiers CTC ;
- affectation des experts et attribution des revues ;
- consultation et suivi des normes ;
- réunions, convocations, calendriers et notifications ;
- enquêtes publiques et traitement des amendements ;
- classement, liaison et circulation des documents ;
- pilotage, indicateurs et alertes ;
- demandes administratives ou financières autorisées.

Chaque opération devra suivre un cycle explicite : aperçu, confirmation, contrôle serveur, exécution, résultat et journal d'audit. Les transitions de workflow doivent toujours être confirmées par le serveur.

### Priorité 4 — Réponses traçables et prudentes

Chaque réponse factuelle issue d'un document ou d'une donnée métier devrait pouvoir afficher :

- la source utilisée ;
- le nom et la version du document ;
- la page ou la section ;
- un extrait justificatif ;
- un lien direct vers l'objet ;
- la date de mise à jour ;
- une indication claire d'incertitude ou d'absence de preuve.

Une réponse sans source suffisante doit être présentée comme une hypothèse ou être refusée, et non formulée comme une décision officielle.

### Priorité 5 — Fiabilité, observabilité et évaluation

Prévoir :

- une gestion robuste des erreurs et des reprises ;
- l'exécution asynchrone des tâches longues ;
- le suivi de progression dans l'interface ;
- une mémoire de travail par dossier ou objet ;
- le résumé automatique des longues conversations ;
- des tests métier représentatifs de chaque module ;
- un jeu de questions-réponses de référence avec vérification des citations ;
- des tests de non-fuite entre utilisateurs, rôles, objets et modules ;
- des mesures de rappel documentaire, précision des passages et exactitude des pages citées.

## 5. Architecture cible simplifiée

```text
Donnée ou document de la plateforme
        ↓
Extraction / OCR / versionnage
        ↓
Index plein texte + index sémantique
        ↓
Recherche filtrée par permissions
        ↓
Passages sourcés et rerankés
        ↓
Synthèse contrôlée par le LLM
        ↓
Réponse citée ou proposition d'action
        ↓
Confirmation humaine + service métier sécurisé
```

Le RAG sert à rechercher, contextualiser et citer. Il ne remplace ni les règles métier, ni les permissions, ni les validations humaines.

## 6. Critères de passage en production

L'assistant ne pourra être étendu au-delà de l'analyse documentaire qu'après validation des conditions suivantes :

- aucune lecture d'objet ou de champ non autorisée dans les tests ;
- citations vérifiables sur les réponses documentaires ;
- refus explicite en cas de source absente, contradictoire ou insuffisante ;
- aucune transition métier exécutée sans contrôle serveur et confirmation ;
- audit complet des actions et des envois ;
- gestion des erreurs, reprises et doubles exécutions ;
- validation humaine sur un échantillon de scénarios réels de chaque module.

## 7. État de mise en œuvre initiale

Une première tranche RAG est implémentée dans `apps/ia_agent/` :

- index persistant des sources et passages avec page ou section ;
- indexation des documents déposés, fiches de normes et versions de normes ;
- extraction PDF, DOCX, XLSX, PPTX et texte lorsque le contenu est exploitable ;
- recherche documentaire filtrée par utilisateur et périmètre métier ;
- outil `search_platform_documents` disponible dans les sessions IA ;
- commande `manage.py index_rag` pour reconstruire l'index ;
- réindexation asynchrone déclenchée après modification d'un document, d'une norme, d'une version ou d'un CV ;
- administration Django et tests d'accès sur documents publics et privés ;
- indexation des CV disponible explicitement avec `--expert-cv`, non activée par défaut.

Sur la base locale actuelle, l'index initial contient 2 documents, 18 normes et 109 versions de normes. Ce volume est un instantané de développement et ne constitue pas une couverture complète de la plateforme.

Cette première tranche ne comprend pas encore :

- les embeddings et le reranking sémantique avancé ;
- un OCR complet pour les documents scannés ;
- la synchronisation automatique à chaque modification de document ;
- le contexte automatique de l'écran ;
- l'exécution d'actions métier CTC ou d'autres modules ;
- une politique de rétention et une autorisation fine par champ entièrement généralisées.

## 8. Conclusion

L'assistant actuel est un prototype utile d'analyse et de préparation. Il n'est pas encore un agent capable d'opérer toute la plateforme.

Les trois chantiers structurants sont :

1. un RAG documentaire et métier global, sourcé et soumis aux permissions ;
2. la compréhension du contexte de l'écran, de l'objet et du rôle courant ;
3. des services d'action sécurisés couvrant progressivement les modules de la plateforme.

Une fois ces fondations en place, l'assistant pourra rechercher, expliquer et préparer les opérations de la plateforme. Leur exécution devra rester contrôlée par les règles serveur, l'utilisateur autorisé et l'audit. Le RAG améliorera la recherche et la traçabilité, mais ne donnera pas à lui seul une valeur décisionnelle ou juridique aux réponses.
