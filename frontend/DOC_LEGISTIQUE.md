# Module : Bureau Légistique et Textes Juridiques (LegistiqueModule)

## 1. Objectif du Module
L'interface de la Légistique marque la transition purement technique de la plateforme à sa traduction Juridique réglementaire. Une norme est soumise à ce module exclusif seulement après son acceptation en vote formel (`MeetingsVotesModule`). Ce module assure "Le Toilettage Légal" qui purge les ambiguïtés textuelles avant qu'un arrêté ministériel ne donne la sanction finale et opposable du document.

## 2. Outils, Flux, et Accès Sécurisés (Workflows)
Ce module est très restrictif.

### 2.1. Protection et Accessibilité 
- **Sécurité RBA :** Ce module refuse l'accès et cache son IHM intégrale ("Accès Interdit") pour tous les utilisateurs autres que les rôles `LEGISTE`, `COORD_CTC`, ou `ADMIN`. Une couche logique garantit l'interdiction de modification de fond technique par le secrétariat qui n'a de compétence que linguistique et légale.

### 2.2. La File d'Attente ("Inbox" des Textes)
- Affiche sous forme d'une table "Kanban" ou tableau de bord les Normes adoptées au sein du CTM qui attendent le "sceau de conformité juridique".
- Indique à quel instant chaque document a été soumis au bureau juridique, le nom du ministère de tutelle et le code du texte.

### 2.3. L'Interface Restreinte d'Édition Formelle (Formatting Editor)
L'éditeur ici est plus strict que l'éditeur général de la rubrique CTM :
- Il autorise la modification de la forme : Formatage des alinéas, structuration des articles et mise en en-tête des titres de chapitres conforment à la standardisation du Journal Officiel de la RDC.
- L'auditeur (Legal Officer) peut intégrer les références croisées nécessaires aux autres lois constitutionnelles existantes (ex: Loi sur l'environnement, Droit coutumier).
- Permet la révision linguistique (grammaticale et orthographique) avant enquête publique. Le texte validé par le légiste porte l'empreinte finale d'"Homologué prélancement".

### 2.4. Bouton de Clôture (Certification "Bon Pour Publication")
- La mission finale du bureau légistique est de libérer le texte validé et purgé de dysfonctionnements legistiques à travers un indicateur "Soumettre pour phase Enquête Publique / Edition Définitive". Ce bouton notifie automatiquement l’administration, transférant le texte à la Bibliothèque Publique ou au portail public via les endpoints connectés au frontend React.
