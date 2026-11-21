# Audit de la bêta Expert — 18 novembre 2026

## Défauts trouvés et corrigés

| Section | Constat | Correction |
|---|---|---|
| Navigation | CTC/Pilotage présents dans le client général | Routes Flutter bloquées, écrans exclus du routeur de la bêta |
| Navigation mobile | Sections hors champ dans une barre horizontale | Sélecteur de toutes les sections Expert |
| Barre latérale | Faux collaborateur et rôle de rapporteur systématique | Données de démonstration retirées, rôle non inféré |
| Documents | Erreur réseau présentée comme une liste vide | Message explicite et bouton Réessayer, liste conservée |
| Création | Bouton affichant un renvoi vers le portail web | Formulaire relié au POST existant, contrôles CTM/groupe |
| Ressources | Liens Drive/Meet uniquement locaux | Persistance serveur personnelle, isolation compte/norme et révision |
| Réunions | Liste descendante sans vue de semaine | Tri croissant, filtres semaine/jour, horaires locaux et ICS |
| Réunions | Consultation et émargement insuffisamment limités | Filtrage serveur, invitation obligatoire et fenêtre d’émargement |
| Notifications | Réunion sans navigation vers son contexte | Ouverture de la réunion sélectionnée |
| Rappels | Absence de tâche périodique dédiée | J-1/H-1, déduplication, contrôle des annulations/reports au dispatch |
| Finances | Listes et agrégats transverses pour l’expert | Périmètre serveur de sa structure et de ses indemnités |
| Activité | Lecture seule du compteur, sans battement Flutter | Battements reliés au service existant, visibilité/interactions observées |
| Thème sombre | Champs et filtres trop peu contrastés | Thème Material cohérent avec la palette Expert |
| Profil | Réglage de notifications uniquement visuel | Lecture et enregistrement de la préférence de réunions par API |
| Installation | Bouton sans action et promesse hors ligne | Aide d’ajout à l’écran d’accueil, connexion requise explicitée |
| Liens d’onglets | URL changée mais ancien écran conservé | Prise en compte des changements de paramètres du routeur |

## Ce qui est relié au serveur

Les routes de l’éditeur, de l’historique, des groupes/adhésions, des réunions,
des finances, du suivi ISO, du profil, de la messagerie et des notifications
existent. L’inventaire authentifié est sauvegardé dans
`reports/expert_beta/api_audit.json`. Un HTTP 200 ne prouve pas à lui seul qu’un
parcours d’écriture complet ou qu’une livraison externe fonctionne.

Le bureau légistique renvoie `can_access=false` pour un expert ordinaire :
c’est un refus métier attendu, pas une section à ouvrir en attribuant des droits.
Les mutations de circuit normatif restent réservées aux rôles autorisés.

## Reprise visuelle après revue des captures

La revue a confirmé que les premières captures ne suffisaient pas à valider
l’interface : couleurs Material violettes, profil trop centré, textes trop petits
et messagerie flottante devant les actions mobiles.

Corrections communes :

- Accent institutionnel `#0095c9`, boutons de contraste renforcé `#007ca7`,
  fonds neutres uniformes ; suppression des dégradés verts/noirs.
- Thème cohérent pour les champs, cartes, filtres, menus, dialogues,
  confirmations et pages secondaires de l’expert.
- Profil aligné à gauche et largeur utile augmentée ; marges de 24 px sur
  ordinateur et 16 px sur mobile.
- Corps de texte de 14 px et titres de cartes de 16 px ; textes de profil
  agrandis, retours à la ligne conservés.
- Navigation compacte donnant accès à toutes les sections quand la largeur
  disponible ne permet pas d’afficher les onglets.
- Messagerie placée dans une barre dédiée sous le contenu, sans superposition.
- Test ajouté à 390 px : le débordement de 24 px du titre d’installation du
  profil a été corrigé et le test correspondant passe.

## Limites avant diffusion réelle

- La livraison FCM/email, Celery Worker/Beat et les préférences doivent être
  vérifiés sur le serveur cible. Les tests désactivent les envois externes.
- L’assistant IA reste dépendant du fournisseur et de sa configuration ; les
  tests de l’éditeur utilisent un fournisseur simulé.
- La visioconférence Meet s’ouvre par lien externe. Le clic ne mesure pas la
  présence dans Meet ; aucun import automatique des présences n’est revendiqué.
- La cible Android, les icônes issues du logo de l'en-tête et la signature bêta
  dédiée ont été ajoutées. La recette sur appareil Android réel reste à faire.
  La version Windows est reportée à la demande de l'utilisateur.
- Les migrations sont créées et testées sur une base isolée. Leur application
  sur la base de production et la publication HTTPS restent à effectuer dans
  l’environnement de déploiement retenu.

Les captures sont produites dans `reports/expert_beta/` par
`scripts/check_expert_beta_browser.py`. Les données « Recette » sont des données
de test dans `/tmp/expert_beta_review.sqlite3`, jamais des chiffres de production.
