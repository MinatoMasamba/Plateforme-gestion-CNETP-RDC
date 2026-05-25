# Manuel Détaillé : Navigation, Édition Collaborative et Messagerie (Plateforme CNETP)

Ce document fournit une explication exhaustive, dans les moindres détails (UI/UX et fonctionnels), des modules vitaux de la plateforme CNETP : la barre de navigation, l'espace d'édition des normes, et le widget de messagerie instantanée.

---

## 1. La Barre de Navigation (Système de Routage et Profils)

La barre de navigation globale (située en haut de l'interface principale dans `App.tsx`) est le centre de contrôle de la plateforme. Elle ne se contente pas de changer de page, elle maintient l'état global et s'adapte au profil de l'utilisateur.

### 1.1. Les Onglets de Navigation (Modules)
La barre présente une série de boutons représentant les différents modules. Lorsqu'un onglet est cliqué, l'état `activeTab` est mis à jour, ce qui change dynamiquement le composant rendu au centre de l'écran. 
- **Éditeur (EditorArea) :** L'espace de rédaction actif (sélectionné par défaut).
- **Historique (HistoryArea) :** La vue "Diff" chronologique des amendements.
- **Annuaire (ExpertsModule) :** La base de données des 200 experts.
- **Réunions & Votes (MeetingsVotesModule) :** La gestion des plénières, émargements et scrutins à majorité qualifiée.
- **Finances (FinancialModule) :** La gestion des cotisations et des jetons de présence.
- **Bibliothèque Publique (ValidationPublicModule) :** Le portail externe pour les enquêtes publiques et les normes publiées.
- **Bureau Légistique (LegistiqueModule) :** Un onglet conditionnel affiché uniquement si l'utilisateur a le rôle `LEGISTE`, `COORD_CTC` ou `ADMIN`.

**Feedback Visuel :** L'onglet actif bénéficie d'une mise en surbrillance (ex: bordure inférieure émeraude, fond subtil, icône accentuée) pour permettre à l'utilisateur de toujours savoir où il se trouve.

### 1.2. Le Simulateur de Profil (Role Switcher)
En haut à droite de la barre se trouve un bouton crucial : le sélecteur de rôle. 
- **Fonctionnement :** Il permet de basculer instantanément le `userRole` (ex: de "Membre Permanent" à "Président CTM" ou "Rapporteur"). 
- **Impact :** Ce changement réévalue les permissions sur *toute* la plateforme. Par exemple, un bouton "Soumettre au vote" dans l'éditeur n'apparaîtra que pour le Rapporteur. Cela permet de tester les Workflows (flux de validation) de bout en bout sans avoir à se reconnecter.

---

## 2. Le Module d'Édition des Normes (L'Éditeur Collaboratif)

Géré par le composant `EditorArea.tsx`, cet espace est le cœur du réacteur où les ingénieurs et experts rédigent le contenu technique des normes de la RDC. L'interface se divise en plusieurs zones fonctionnelles riches.

### 2.1. La Vue Centrale : L'Espace de Rédaction
C'est ici que la norme prend vie.
- **En-tête du Document :** Affiche le code strict de la norme (ex: `CNETP-EC8-1`), son titre long, le Comité Technique Miroir (CTM) responsable, et son statut de progression (ex: "En cours de rédaction").
- **Indicateurs de Présence (Co-édition) :** En haut à droite de l'éditeur, de petites pastilles colorées avec les initiales des collaborateurs s'affichent. Cela indique en temps réel qui d'autre consulte ou édite le même projet de norme, évitant ainsi les conflits d'écrasement.
- **Zone de Texte (Textarea) :** Une zone de saisie optimisée pour les textes normatifs (typographie monospace ou lisible, espacements généreux). Le texte est sauvegardé automatiquement.

### 2.2. Le Panneau Latéral Droit : Les Outils d'Assistance
Sur la droite de la zone de rédaction se trouve un panneau polyvalent articulé autour de plusieurs sous-onglets :

#### A. L'Assistant IA Réglementaire
La fonctionnalité la plus innovante de l'éditeur. L'IA est entraînée/promptée avec les référentiels internationaux (ISO, Eurocodes).
- **Analyse du Texte :** L'utilisateur peut demander à l'IA d'analyser le paragraphe en cours.
- **Recommandations :** L'IA génère un rapport expliquant si la clause respecte l'état de l'art. Elle fournit une explication textuelle (le "Pourquoi").
- **Proposition d'Amendement :** L'IA génère un bloc de code/texte de remplacement. Un bouton vert "Appliquer la révision" permet de remplacer le texte original par la proposition de l'IA en un seul clic.

#### B. Les Commentaires et Amendements
La norme ne s'écrit pas seule ; elle requiert un consensus.
- **Fil de Discussion :** Les experts peuvent ajouter des commentaires liés au document global ou à un article spécifique.
- **Justification Technique :** Chaque commentaire enregistre l'identité de l'auteur, l'horodatage, et le contenu. C'est ici que les ingénieurs défendent leurs "amendements" avant qu'ils ne soient fusionnés par le président du WG (Working Group).

#### C. Les Documents Annexes (Littérature grise)
Pour rédiger une norme, les experts s'appuient sur des recherches externes.
- **Liste des Pièces Jointes :** Affiche les PDF, études de sols, rapports SBR, etc.
- Chaque document annexe affiche son nom, son extension, sa taille et un bouton de téléchargement.

#### D. Intégrations Cloud (Workspace)
- **Dossier Drive :** Un bouton permet d'ouvrir directement le Google Drive associé (où les brouillons bruts ou fichiers lourds sont stockés).
- **Salle Meet :** Un bouton génère ou rejoint une salle Google Meet synchrone dédiée au CTM pour débattre de vive voix d'un point de blocage.

---

## 3. La Messagerie Instantanée (Messaging Widget)

Pour éviter que les experts ne quittent la plateforme pour utiliser WhatsApp ou Slack, un widget de messagerie asynchrone / temps réel, géré par `MessagingWidget.tsx`, est superposé sur toutes les pages.

### 3.1. Bouton Flottant (FAB) et Interface
- Situé en bas à droite de l'écran, le bouton affiche une icône de bulle de discussion avec éventuellement un badge rouge (notifications de messages non lus).
- En cliquant dessus, le widget se déploie. Il se comporte comme une fenêtre modale flottante persistante. L'utilisateur peut naviguer sur le reste de la plateforme (modifier une norme, voter) tout en gardant le chat ouvert.

### 3.2. Liste des Contacts et Annuaire
- Le panneau principal de la messagerie affiche la liste des collègues (experts de la plateforme).
- **Indicateurs d'État :** Des points verts signalent les utilisateurs actuellement en ligne (connectés à la plateforme).
- La liste est souvent triée pour afficher en premier les membres du même *CTM* ou du même *WG*, facilitant les interactions contextuelles.

### 3.3. Fil de Chat et Envoi de Messages
- **Zone de Dialogue :** Affichage classique sous forme de bulles (à droite pour les vôtres, à gauche pour les collègues), incluant le nom, l'horodatage précis, et une indication de lecture.
- **Barre de saisie :** L'utilisateur peut taper son texte, appuyer sur `Entrée` ou cliquer sur l'icône d'envoi.

### 3.4. Le Partage Contextuel de Clauses (La Fonctionnalité Clé)
C'est la fonction experte du widget. Dans une discussion technique, il est fastidieux de dire "Regarde l'article 2.4.1 de l'Eurocode 8".
- **Intégration avec l'Éditeur :** Lorsqu'un expert travaille dans l'éditeur, il peut sélectionner un fragment du texte normatif et l'injecter directement dans le chat (`isClauseShare`).
- **Affichage Enrichi :** Le message reçu côté messagerie n'est pas qu'un simple texte. Il apparaît sous forme de bloc de citation mis en évidence, incluant le code de la norme, l'article précis, et l'extrait de texte.
- **Avantage :** Le destinataire comprend immédiatement le contexte de la réflexion technique. Un clic sur ce bloc pourrait le reconduire directement vers la clause concernée dans l'interface de lecture ou d'édition, accélérant ainsi la levée des "blocages techniques" (Bugs normatifs) avant le passage au vote formel.
