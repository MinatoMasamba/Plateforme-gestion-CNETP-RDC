# Module : Historique et Traçabilité (HistoryArea)

## 1. Objectif du Module
Le module d'Historique répond à une exigence légale stricte : la transparence absolue. Dans l'évolution des normes de la CNETP, chaque modification apportée à un texte ayant une vocation réglementaire nationale doit pouvoir être retracée, sourcée, et justifiée afin d'en comprendre l'intention initiale ou les concessions faites lors des négociations des différents groupes d'intérêt.

## 2. Les Composants Fonctionnels

### 2.1. La Vue Chronologique (Timeline of Versions)
- Affiche une ligne du temps listant toutes les versions successives sauvegardées pour une norme donnée.
- Chaque version comporte le "Version Number" (V1, V2.1, etc.).
- Comprend les métadonnées de révision complètes :
  - L'Auteur (Nom de l'expert ayant validé la sauvegarde).
  - L'Adresse Email de l'auteur.
  - L'Horodatage (Date et heure précises UTC).
  - La note de version (Le "Commit Message" expliquant très brièvement la raison de la mise à jour).

### 2.2. La Visionneuse des Changements (Algorithme "Diff")
- Lorsque l'utilisateur sélectionne l'outil de comparaison, l'écran scinde le texte ou affiche des marqueurs visuels très précis reflétant une architecture de système de contrôle de version (comme Git) orientée vers le texte normatif.
- **Les suppressions** (Le formatage d'un texte retiré par rapport à la version précédente est marqué en strié ou surbrillance rouge pâle).
- **Les insertions** (Le nouveau texte ajouté figure dans une surbrillance vert vif).

## 3. Garantir l'Intégrité (Rollback et Audit)
- Contrairement à un traitement de texte classique où "Annuler" se limite à la session en cours, l'historique enregistre des points de restauration absolus.
- Si une modification est jugée litigieuse post-plénière, le Président ou l'Administration technique (Back-Office) peut solliciter le "Rollback" (Restauration) sur la base d'un PV justifiant un retour en arrière.
- Ce processus d'audit permanent garantit qu'aucun changement clandestin (fraude) n'intègre le code de la norme entre la rédaction technique et la publication finale.
