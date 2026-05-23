# Liste des Tâches Restantes pour l'Application Web Hybride

Cette liste détaille les prochaines étapes nécessaires pour finaliser l'intégration et le développement de l'application web. **Il est impératif de vérifier chaque étape** pour s'assurer du bon fonctionnement et de la stabilité du système.

## 1. Vérification Cruciale de l'Environnement et de l'Intégration

*   **Vérifier que le serveur Django fonctionne correctement :**
    *   S'assurer que `python manage.py runserver` (ou sur un port alternatif comme `8001`) démarre sans erreurs.
    *   **Vérifier** l'accès aux URLs de l'API Django (par exemple, `/api/v1/schema/swagger/`) pour confirmer que le backend est opérationnel.
*   **Vérifier la compilation de l'application React :**
    *   S'assurer que `cd frontend && npm run build` s'exécute sans erreurs et que les fichiers sont bien générés dans `web/static/dist/`.
    *   **Vérifier** la présence de `index.html` et du dossier `assets` dans `web/static/dist/`.
*   **Vérifier le chargement de l'application React dans le navigateur :**
    *   Ouvrir le navigateur sur `http://127.0.0.1:8000/` (ou le port utilisé).
    *   Ouvrir les **outils de développement du navigateur (F12)**.
    *   **Vérifier l'onglet "Console"** pour toute erreur JavaScript (erreurs de syntaxe, objets non définis, etc.).
    *   **Vérifier l'onglet "Réseau"** pour s'assurer que tous les fichiers (HTML, CSS, JS du bundle React) sont chargés avec un statut HTTP 200 OK. Chercher les erreurs 404 (fichiers non trouvés) ou 500.
    *   **Vérifier** que `window.__INITIAL_STATE__` est bien injecté et accessible dans la console JavaScript du navigateur.

## 2. Développement du Frontend (React)

*   **Consommer `window.__INITIAL_STATE__` dans React :**
    *   Modifier `frontend/src/main.tsx` ou `frontend/src/App.tsx` pour lire les données de `window.__INITIAL_STATE__` et les passer au contexte de l'application ou à un store d'état (par exemple, Zustand, Redux).
    *   **Vérifier** que l'état initial (informations utilisateur, CSRF, stats) est correctement utilisé par les composants React.
*   **Implémenter la logique d'authentification/redirection :**
    *   Utiliser les données `initialState.user` pour gérer l'affichage conditionnel (boutons de connexion/déconnexion, accès aux routes protégées).
    *   **Vérifier** que les utilisateurs non authentifiés sont redirigés vers la page de connexion si nécessaire.
*   **Développer les composants React pour chaque page et section :**
    *   **Landing.tsx :** Mettre à jour pour afficher les statistiques du backend (`initialState.stats`).
    *   **Login.tsx et Register.tsx :** Implémenter les formulaires de connexion et d'inscription qui interagiront avec les APIs Django (`/api/v1/auth/login/`, etc.) en utilisant le jeton CSRF.
    *   **App.tsx et ses sous-composants (`Dashboard`, `Normes`, `Experts`, etc.) :** Développer la logique et l'UI pour afficher les données provenant des APIs Django.

## 3. Améliorations du Backend (Django)

*   **Implémenter les endpoints d'API REST nécessaires :**
    *   S'assurer que les APIs pour l'authentification, la récupération des normes, des experts, etc., sont pleinement fonctionnelles et sécurisées.
    *   **Vérifier** la documentation de l'API (`/api/v1/schema/swagger/`) pour confirmer la disponibilité des endpoints.
*   **Ajouter la gestion des sessions ou des tokens (si non déjà configuré) :**
    *   Confirmer que les utilisateurs peuvent se connecter via l'API et maintenir leur session.
    *   **Vérifier** la gestion du jeton CSRF pour les requêtes `POST`, `PUT`, `DELETE`.

## 4. Tests

*   **Tests unitaires et d'intégration frontend :**
    *   Écrire des tests pour les composants React, la logique de routage et les interactions avec l'API.
    *   **Vérifier** la couverture des tests.
*   **Tests API backend :**
    *   Écrire des tests pour les vues API Django pour s'assurer de leur bon fonctionnement et de leur sécurité.
    *   **Vérifier** la conformité des réponses API.

## 5. Déploiement

*   **Configuration des fichiers statiques pour la production :**
    *   Mettre en place un serveur web (Nginx, Apache) pour servir efficacement les fichiers statiques de Django.
    *   **Vérifier** le bon fonctionnement du déploiement en production.
