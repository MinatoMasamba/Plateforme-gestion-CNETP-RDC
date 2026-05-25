# Module : Éditeur de Normes (EditorArea)

## 1. Objectif du Module
L'Éditeur de Normes est l'espace de travail central de la plateforme CNETP. C'est ici que les experts techniques (ingénieurs, chercheurs) se réunissent virtuellement pour rédiger, débattre et finaliser le contenu des normes nationales de la RDC. Il remplace les échanges répétitifs de documents Word par un environnement de coédition en temps réel sécurisé et assisté.

## 2. Interface et Composantes

### 2.1. L'En-tête de la Norme (Header)
- **Identifiants :** Affiche le code unique de la norme (ex: CNETP-EC8-1), son titre complet et le CTM (Comité Technique Miroir) d'attachement.
- **Présence en temps réel :** Des avatars textuels en haut à droite indiquent quels autres experts sont actuellement connectés et consultent le même document.
- **Boutons d'Action Conditionnels :** Selon le rôle sélectionné, des boutons comme "Soumettre pour validation" s'affichent uniquement pour les responsables désignés (ex: Rapporteur ou Président du comité).

### 2.2. L'Espace d'Édition (Textarea)
- Permet la saisie fluide du texte brut ou enrichi de la norme.
- Inclut un système de sauvegarde automatique silencieuse rattaché au document consulté.

### 2.3. L'Intelligence Artificielle Réglementaire (Assistant IA)
Intégration d'un module "Assistant Réglementaire" (basé sur le modèle sémantique) qui permet de :
- Scanner un paragraphe spécifique.
- Le comparer avec les standards internationaux (Eurocode, ISO).
- Suggérer un amendement si le texte ne répond pas aux normes existantes.
- En un clic ("Appliquer la révision"), transposer la suggestion validée par l'expert dans le corps principal du texte.

### 2.4. Le Panneau des Commentaires et Amendements
- Un fil de discussion dédié spécifiquement aux clauses de la norme.
- Les experts justifient techniquement les ajouts ou retraits de paragraphes. C'est la base démocratique du consensus technique avant qu'un vote n'entérine les changements.

### 2.5. Espace Annexes et Littérature Grise
- Permet de lister, visualiser et télécharger les pièces justificatives, diagrammes techniques, et autres rapports qui fondent la décision technique.
- Connexions directes aux espaces de travail Google Workspace (Dossier Drive de la conception, Lancement d'une visio-conférence Google Meet d'urgence).

## 3. Gestion des Rôles et Workflow
- Les modifications de base sont rattachées au "Membre du WG".
- Seuls les administrateurs et présidents de sous-comités peuvent transformer une série d'amendements en une nouvelle version définitive.
