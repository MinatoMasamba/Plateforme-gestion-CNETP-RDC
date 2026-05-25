# Module : Modèle Financier, Cotisations et Allocations (FinancialModule)

## 1. Objectif du Module
Le fonctionnement de la plateforme CNETP engendre des coûts structurels importants, liés au soutien aux experts participants, et est alimenté par les structures des entreprises ou institutions membres. Ce module transforme l'outil technique de rédaction en une entité ERP de gestion interne complète.

## 2. Gestions des Jetons de Présence pour les Experts
La participation aux CTM requiert que les réunions et travaux soient indemnisés avec un "Jeton de présence".
- **Règle d'Attribution Automatique :** La fonction centrale de ce module croise les bases de données du composant `MeetingsVotesModule`. Si le statut émargement de l’expert est marqué comme "Présent" validé et signé lors d'une session, le jeton lui est directement alloué sur son compteur.
- **Bilan Personnel :** En tant qu’Expert (Profil 1), vous voyez s’afficher un tableau de bord privé résumant l'historique complet de votre assiduité ainsi que l'accumulation budgétaire correspondante.
- **Documentation et Reçus :** Chaque expert a la possibilité de télécharger des fiches d'honoraires pour des fins d'administration et de taxation personnelle, ou pour attester son temps passé pour le compte de la République.

## 3. Gestions des Cotisations des Membres Structurels
Les entreprises du Bâtiment ou l'Etat allouent un budget.
- Les Gestionnaires rattachés au FONER (Comptables) sont les superviseurs de la vue panoramique budgétaire de chaque organisme membre.
- Visualisation pour l'état des encours : Montants dus et statuts des arriérés d'un établissement qui mandate ses représentants techniques.

## 4. Outils de Comptabilité pour l'Administration Centrale
Lorsqu'un profil `Gestionnaire Comptable (FONER)` ou l'administration s'y connecte, l'IHM s'enrichit de boutons d’action permettant des opérations d'écriture :
- Permet la création/saisie de virements, justifiant des preuves paiements des cotisations validées en compte en banque.
- Préparation de l'Export Bancaire XML : Autorise l'exportation des paiements globaux des jetons afin de l’exécuter informatiquement par l'API bancaire de la Banque Centrale du Congo ou d’institutions partenaires, supprimant la gestion monétaire "papier".
