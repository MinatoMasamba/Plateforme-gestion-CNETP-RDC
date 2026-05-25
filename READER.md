# 📜 READER.md - Plan d'Implémentation de la Plateforme CNETP

Ce document sert de guide de référence pour l'implémentation de la plateforme de gestion des activités de la commission d'élaboration des normes de construction (CNETP). Il synthétise les instructions des documents PDF ('AFFECTATION mise en place_Phoenix.pdf', 'Manuel ORGA AMELIORE.pdf') et les besoins fonctionnels spécifiés.

---

## 🛠 Objectifs de la Plateforme

### 1. Inscription et Affectation des Experts
- **Fonctionnalité :** Inscription des experts via un portail dédié.
- **Affectation :** Choix obligatoire d'une sous-commission technique (CTM - Comité Miroir Technique) ou d'un groupe de travail (WG).
- **Données :** Structure de provenance (girons), expertise, coordonnées.
- **Référence :** `AFFECTATION mise en place_Phoenix.pdf` pour la liste des structures et experts.

### 2. Élaboration Collaborative des Normes
- **Espace de travail :** Un éditeur par secteur d'activité (lié au CTM).
- **Processus :** Rédaction par étapes (Avant-projet, Projet de norme).
- **Outils :** Intégration de l'IA pour l'analyse réglementaire et la comparaison avec les normes internationales (ISO/Eurocodes).

### 3. Traçabilité et Suivi des Modifications
- **Historique :** Suivi version par version de chaque modification.
- **Visualisation :** Différentiel (mode révision) pour identifier qui a modifié quoi et quand.
- **Commentaires :** Justification technique des amendements.

### 4. Sessions de Validation et Scrutins (Votes)
- **Réunions :** Planification des sessions d'adoption ou d'harmonisation.
- **Quorum :** Vérification automatique du quorum selon les règles du Manuel d'Organisation.
- **Votes :** Système de vote sécurisé (Oui, Non, Abstention).
- **PV :** Génération automatique du Procès-Verbal (PV) avec calcul des pourcentages de décision.

### 5. Gestion Financière : Cotisations
- **Structures :** Suivi des structures participantes (ONIC, Universités, Entreprises).
- **Paiements :** Interface de suivi des cotisations annuelles ou par projet.
- **Relances :** Système d'alerte pour les retards de paiement.

### 6. Gestion Financière : Indemnités (Jetons de présence)
- **Calcul :** Génération automatique des jetons de présence basée sur les listes d'émargement des réunions.
- **Suivi :** Historique des paiements effectués aux experts (Per diems).

### 7. Validation Supérieure (Secrétariat Technique)
- **Workflow :** Une fois validée par le CTM, la norme est transmise au Secrétariat Technique (CTC).
- **Bureau Légistique :** Toilettage juridique et conformité réglementaire avant sanction finale.

### 8. Publication et Diffusion
- **Publication :** Mise à disposition de la norme homologuée sur la Bibliothèque Publique.
- **Enquête Publique :** Phase optionnelle de consultation du public avant la publication finale.

---

## 🏗 Architecture des Rôles (RBAC)

Se référer au Manuel d'Organisation pour les permissions précises :
- **ADMIN :** Gestion totale du système.
- **EXPERT :** Rédaction, vote (si membre du CTM), accès aux documents de son CTM.
- **RAPPORTEUR :** Gestion des réunions, des votes et des PV.
- **GESTIONNAIRE COMPTABLE :** Suivi des cotisations et des jetons de présence.
- **SECRETARIAT TECHNIQUE (CTC) :** Validation finale et légistique.
- **PUBLIC :** Consultation des normes publiées et participation aux enquêtes.

---

## 📋 Plan de Développement à suivre

1.  **[ ] Phase Auth & Profils :** Finaliser l'auto-login et la redirection intelligente selon `is_expert` (En cours).
2.  **[ ] Phase Gouvernance :** Implémenter la structure CTM / WG et l'affectation des experts.
3.  **[ ] Phase Édition :** Connecter l'éditeur au backend pour la sauvegarde et l'historique des versions.
4.  **[ ] Phase Réunions :** Développer le module de vote et de génération de PV.
5.  **[ ] Phase Finance :** Créer les tables de suivi des cotisations et des jetons.
6.  **[ ] Phase Publication :** Finaliser la bibliothèque publique.

---

## 📌 Notes Importantes (NB)
- **Zéro omission :** Chaque point des documents PDF doit être reflété dans les permissions et les workflows.
- **Interface :** L'UI doit rester moderne (Tailwind) tout en respectant la rigueur administrative du CNETP.
- **Sécurité :** Utilisation stricte du CSRF et des sessions Django pour toutes les actions sensibles (votes, paiements).
