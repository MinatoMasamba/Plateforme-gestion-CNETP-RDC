# Revue UX des cinq espaces du Secrétariat technique

Date : 31 octobre 2026.
Périmètre : socle, architecture des cinq espaces, Coordination et Pôle 2.
Statut : revue appliquée à la première passe ; à compléter avec les Pôles 1, 3 et 4.

## 1. Références examinées

| Référence | Apport retenu | Limite ou écart |
|---|---|---|
| Nielsen Norman Group — principes des tableaux de bord | Un écran doit répondre à une question de travail, pas exposer tous les chiffres. Les quatre blocs et les alertes sont prioritaires. | Les tableaux de bord historiques de la plateforme sont plus chargés ; la nouvelle page d’accueil est volontairement plus courte. |
| WCAG 2.2 AA | Contraste du texte, focus visible, information jamais portée par la couleur seule, cibles tactiles suffisantes. | Le Soft Glassmorphism peut réduire le contraste : les surfaces translucides restent limitées aux cartes secondaires et les textes utilisent les jetons foncés. |
| GOV.UK Design System | Libellés en français simple, un verbe par action, erreurs explicites, parcours linéaire. | Les libellés métier CNE-ITP (SC, PTN, CTC, COPIL) sont conservés comme termes institutionnels. |
| Material 3 — densité et navigation | Navigation compacte, hiérarchie typographique nette, adaptation mobile par empilement. | Aucune dépendance Material n’est ajoutée : les composants restent CSS/Tailwind locaux. |
| Charte CNE-ITP existante (`institutional-ui.css`, `ctc-supervision.css`) | Palette officielle `#0095c9`, `#fff24b`, `#db3832`, cartes, tableaux et badges déjà utilisés. | Les graphiques restent en CSS/SVG, sans bibliothèque externe. |

## 2. Décisions appliquées

- **Accueil orienté travail** : « Mon travail du jour » ouvre chaque espace, avec quatre blocs et une colonne d’alertes. Les indicateurs généraux restent visibles mais passent après le travail immédiat.
- **Un menu de 5 à 7 entrées** par poste. Les accès transversaux (Mes demandes, Organisation du ST) complètent la liste sans dépasser sept entrées. Les modules secondaires restent accessibles depuis les liens du tableau de bord.
- **Chef et membre** : le chef voit le tableau de bord général, les membres du pôle, la répartition par statut et l’audit. Le membre voit ses dossiers et ses statistiques. La même page sert les deux, avec des requêtes filtrées côté serveur.
- **Statuts** : huit statuts métier et « Bloquée » sont affichés en texte et en couleur. Le motif de blocage est visible. La lecture ne modifie pas `Norme.status`.
- **Aucune valeur fictive** : les modules non raccordés affichent « Module à venir ». Le budget statique historique n’est pas présenté comme une donnée réelle.
- **Mobile** : les cartes s’empilent, la barre latérale devient un tiroir, la barre d’aide reste accessible en bas.
- **Recherche globale** : la barre du haut filtre les dossiers ; les autres recherches restent locales à leur module.

## 3. Points à vérifier lors des prochaines passes

- Contraste réel des surfaces translucides en mode sombre.
- Taille des cibles tactiles des boutons de confirmation et d’émargement.
- Gestion du focus dans les tiroirs et modales.
- Affichage des longues listes (pagination ou défilement) dans les files de validation.
- Cohérence des libellés entre les cinq espaces et les documents institutionnels.
