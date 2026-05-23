# CNETP - Documentation de la Plateforme

## Vue d'ensemble

Cette plateforme est un système d'information complet pour le **Comité National d'Élaboration des Textes Publics (CNETP)**. Elle permet de gérer l'intégralité du cycle de vie des normes, de leur élaboration à leur publication publique, en passant par la gestion des experts, l'organisation des réunions, les systèmes de vote formels, et le suivi financier (cotisations, jetons de présence).

## Architecture et Navigation globale

L'application principale (`src/App.tsx`) est structurée autour de plusieurs éléments :
1. **La barre de navigation supérieure** qui donne accès aux différents modules (onglets).
2. **Une barre latérale (Sidebar)** pour la sélection des documents ou projets de norme en cours de rédaction.
3. **Un espace de travail dynamique (Main Area)** dont le contenu, les fonctionnalités et les permissions changent en fonction de l'onglet actif et du rôle de l'utilisateur simulé.
4. **Un module de messagerie flottant**, accessible partout.

### Simulateur de profil / Rôle
Un sélecteur situé en haut à droite (bouton "Simuler un autre profil") permet de basculer entre différents profils d'utilisateurs (Membre permanent, Président CTM, Rapporteur, Légiste, Gestionnaire comptable, etc.). Les droits, l'affichage et les boutons d'action dans les différents modules changent dynamiquement selon le rôle sélectionné, conformément au manuel d'organisation du CNETP.

---

## Les Modules (Onglets de navigation)

### 1. Édition & Rédaction (Éditeur Collaboratif)
**Fichier source:** `src/components/EditorArea.tsx`
- **Objectif:** Permettre la rédaction, l'amendement, et la co-création des projets de normes au sein d'un Groupe de Travail (WG) ou CTM.
- **Fonctionnalités:**
  - Éditeur de texte enrichi avec suivi de la présence des autres collaborateurs.
  - Espace de commentaires pour justifier les amendements ou poser des questions.
  - **Assistant IA Réglementaire:** Un outil d'IA capable d'analyser le texte, de le comparer avec des références (ex: normes ISO, Eurocodes), d'expliquer les recommandations et de générer une proposition de révision applicable en un clic. L'utilisateur peut étendre la vue IA pour modifier la proposition avant de l'appliquer.
  - **Pièces jointes & Documents annexes:** Interface pour le téléversement et la consultation de littérature grise (PDF, recherches techniques).
  - Intégration cloud (liens vers Google Drive et réunions Google Meet liés au document).

### 2. Historique (Traçabilité)
**Fichier source:** `src/components/HistoryArea.tsx`
- **Objectif:** Assurer une traçabilité totale (audit trail) de toutes les modifications apportées à un document.
- **Fonctionnalités:**
  - Ligne du temps (chronologie) montrant toutes les versions sauvegardées du projet de norme.
  - Visualisation différentielle (Diff) mettant en surbrillance les textes ajoutés (vert) et supprimés (rouge).
  - Indication de l'auteur de chaque changement et de la date.

### 3. Annuaire & Experts
**Fichier source:** `src/components/ExpertsModule.tsx`
- **Objectif:** Gérer la base de données des membres de l'organisation et faciliter le réseautage.
- **Fonctionnalités:**
  - Liste interactive des experts, filtrable par CTM (Comité Technique Miroir), WG (Working Group) et Structure de provenance (ONIC, Universités, Entreprises, etc.).
  - Fiches détaillées contenant les coordonnées et les rôles de chacun.
  - Outils administratifs : les membres avec des rôles adéquats (ex: Coordonnateur CTC, Secrétaire permanent) peuvent modifier les affectations (transférer un expert d'un WG à un autre).

### 4. Réunions & Votes
**Fichier source:** `src/components/MeetingsVotesModule.tsx`
- **Objectif:** Structurer le travail collégial, documenter les rassemblements et enregistrer les décisions formelles.
- **Fonctionnalités:**
  - **Calendrier & Convocation:** Les secrétaires/rapporteurs peuvent organiser des réunions, planifier des ordres du jour, confirmer le quorum (présences) et générer/archiver des Procès-Verbaux (PV).
  - **Plateforme de Scrutin:** 
    - Paramétrage et ouverture de votes par le Rapporteur CTM (ex: vote pour l'adoption d'un texte avant envoi).
    - Vote numérique sécurisé pour les membres du comité (Pour, Contre, Abstention).
    - Affichage en temps réel ou final des résultats, et vérification des seuils de majorité qualifiée.

### 5. Cotisations & Indemnités (Module Financier)
**Fichier source:** `src/components/FinancialModule.tsx`
- **Objectif:** Gérer la trésorerie liée aux cotisations des structures membres et à la rémunération (jetons) des experts.
- **Fonctionnalités:**
  - **Cotisations institutionnelles:** Tableau de suivi des montants dus et des paiements versés par les structures (entreprises, organismes).
  - **Jetons de présence des experts:** Système d'accumulation automatique d'indemnités (jetons) basé sur le registre des présences aux réunions. Téléchargement des reçus individuels pour les experts.
  - Interface d'administration financière réservée au profil **Gestionnaire Comptable (FONER)** pour saisir les paiements.

### 6. Bureau Légistique
**Fichier source:** `src/components/LegistiqueModule.tsx`
- **Objectif:** Réaliser le toilettage législatif et réglementaire (mise en forme juridique) d'une norme une fois qu'elle est techniquement validée par les ingénieurs.
- **Fonctionnalités:**
  - Files d'attente des projets de normes en attente de conformité juridique, envoyées par les CTM.
  - **Éditeur restreint:** espace de rédaction pour les experts légistes permettant de formater les articles, alinéas et références croisées sans altérer le fond scientifique.
  - Boutons de flux de travail (ex: "S'assigner", "Valider pour Enquête Publique").
  - Accessible uniquement par les membres du module de pilotage (Coord CTC) ou les "Experts Légistes".

### 7. Bibliothèque Publique
**Fichier source:** `src/components/ValidationPublicModule.tsx`
- **Objectif:** Le point de chute final d'une norme, exposant les textes au grand public ou organisant la phase d'enquête.
- **Fonctionnalités:**
  - Liste des normes officiellement publiées et homologuées (téléchargeables au format PDF).
  - Portail pour **l'Enquête Publique**, permettant au public ou aux industriels tiers de lire un projet et de formuler des amendements avant l'homologation finale.
  - Indicateur visuel du "Cycle de Vie" de la norme (depuis sa conception au sein d'un WG jusqu'à la "Sanction Ministérielle" finale et sa parution).

### 8. Messagerie Interne (Widget)
**Fichier source:** `src/components/MessagingWidget.tsx`
- **Objectif:** Permettre une communication asynchrone rapide sans quitter la plateforme.
- **Fonctionnalités:**
  - Bouton flottant disponible sur toutes les pages.
  - Liste des contacts (experts connectés, membres du même comité).
  - Interface de chat en temps réel pour coordonner les travaux de normalisation.

---

## Structures de Données et Formats (JSON / TypeScript)

La plateforme manipule différentes entités pour son fonctionnement. Dans le contexte de l'application (basée sur React et TypeScript), ces données sont représentées sous forme d'objets (JSON ou dictionnaires). 

Voici les formats attendus pour alimenter les différents modules et la manière de les utiliser.

### 1. Structure d'un Document (Norme ou Projet)

Ce format est utilisé par la **Sidebar** (pour lister les normes en cours) et par l**'EditorArea** (pour charger le contenu).

```json
{
  "id": "doc-1",
  "title": "Eurocode 8 - Conception pour la résistance aux séismes",
  "code": "CNETP-EC8-1",
  "description": "Règles générales pour la conception parasismique en RDC.",
  "content": "Article 1.\\nLa présente norme définit...\\n\\nArticle 2.\\nSpécifications liées...",
  "category": "CTM 2 - Ouvrages",
  "updatedAt": "2026-05-19T10:00:00Z",
  "updatedBy": "Dr. Kasongo",
  "updatedByEmail": "expert@cnetp.cd",
  "driveFolderUrl": "https://drive.google.com/...",
  "meetMeetingUrl": "https://meet.google.com/...",
  "references": [
    {
      "id": "ref-1",
      "name": "Rapport Synthèse SBR",
      "type": "PDF",
      "size": "2.1 MB"
    }
  ]
}
```
**Comment l'utiliser :** Lorsque vous basculez vers l'onglet `editor`, le document actif est transmis en prop `document={activeDocument}` au composant `EditorArea`. Les champs `content` dictent le texte affiché dans la zone de rédaction, et `references` peuple la section "Documents Annexes".

### 2. Structure d'une Version de Document (Historique)

Appelée par le composant `HistoryArea`, cette structure permet de tracer l'évolution d'une norme au fil des révisions.

```json
{
  "id": "v-2",
  "documentId": "doc-1",
  "versionNumber": 2,
  "content": "Contenu mis à jour de l'Article 1...",
  "author": "Dr. Mbuyi",
  "email": "mbuyi@cnetp.cd",
  "timestamp": "2026-05-20T08:30:00Z",
  "comment": "Ajout des spécifications de contrainte thermique",
  "isRollback": false
}
```
**Comment l'utiliser :** Utilisée principalement dans `HistoryArea`, elle permet de concevoir le *Diff* (comparaison de texte). L'interface compare à la volée le champ `content` de la version *n* et de la version *n-1* pour faire ressortir les mots ajoutés (vert) et supprimés (rouge).

### 3. Structure d'un Collaborateur ou Expert

Utilisée pour l'annuaire (`ExpertsModule`), la gestion des présences et la messagerie (`MessagingWidget`).

```json
{
  "id": "exp-144",
  "name": "Prof. Tshimanga",
  "role": "Membre Permanent",
  "email": "tshimanga@unikin.ac.cd",
  "avatarColor": "bg-indigo-500",
  "isActive": true,
  "structure": "Université de Kinshasa",
  "province": "Kinshasa"
}
```
**Comment l'utiliser :** Sous forme de tableau (array d'objets), cela propulse le tableau de l'annuaire. Dans le contexte de l'éditeur collaboratif, la propriété `avatarColor` et `name` permettent d'afficher une pastille (avatar) indiquant que la personne édite le document.

### 4. Structure de Messagerie (Message Chat)

Utilisée par `MessagingWidget` pour échanger en temps réel.

```json
{
  "id": "msg-1",
  "senderId": "exp-12",
  "senderName": "Alice",
  "receiverId": "exp-144",
  "text": "L'article 2.4 de la norme nécessite une clarification technique.",
  "timestamp": "2026-05-20T10:45:00Z",
  "isClauseShare": true,
  "clauseCode": "2.4.1",
  "clauseExcerpt": "La température minimale tolérée est de..."
}
```
**Comment l'utiliser :** Le *Store* (ou l'état React) accumule ces objets. Si `isClauseShare` est activé, le widget applique un formatage spécial avec l'extrait du code de la clause mis en surbrillance, ce qui permet à deux experts de discuter précisément d'une ligne d'un texte normatif.

### Gestion d'État et Injection des Données
Dans `src/App.tsx`, ces structures de données sont typiquement stockées dans des états locaux via `useState` de React, ou proviennent du fichier de définition `src/types.ts`. Elles sont transmises de la racine de l'application vers les sous-modules via les *props*.

Exemple d'injection dans l'éditeur :
```tsx
<EditorArea
  document={activeDocument}
  activeCollaborator={activeCollaborator}
  userRole={userRole}
/>
```
Le changement du `userRole` (parmi 'ADMIN', 'MEMBRE_P', 'LEGISTE', etc.) déclenchera un changement d'interface asynchrone (disponibilité de certains boutons) au sein de la page.
