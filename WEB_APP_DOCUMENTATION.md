# Documentation de l'Application Web Hybride (Django & React)

Ce document explique l'architecture et l'interaction entre l'application Django (`web` app) et le frontend React, conçu comme un système hybride où Django sert l'application React comme un template dynamique.

## 1. Introduction à l'Architecture Hybride

L'objectif est d'utiliser Django pour :
- Servir les fichiers statiques (HTML, CSS, JavaScript) compilés de l'application React.
- Injecter des données initiales dynamiques (état d'authentification de l'utilisateur, jeton CSRF, statistiques du backend) directement dans le `index.html` de React avant de le renvoyer au client.
- Gérer explicitement les points d'entrée principaux de l'application (par exemple, `/`, `/auth/login/`, `/app/`) avec des vues et des URLs Django dédiées.

Une fois le `index.html` chargé dans le navigateur, React prend le relais et utilise `react-router-dom` pour la navigation interne côté client sans recharger la page complète depuis le serveur Django.

## 2. Fichiers Clés de l'Application Django `web`

### `web/__init__.py`
Fichier d'initialisation standard pour un package Python. Aucune logique spécifique à l'intégration React ici.

### `web/urls.py`
Ce fichier définit les routes URL de Django qui servent l'application React. Il remplace le comportement "catch-all" par des mappings explicites pour les routes principales définies dans `frontend/src/RouteSwitch.tsx`.

**Contenu actuel :**
```python
from django.urls import path, re_path
from .views import ReactAppView

app_name = 'web'

urlpatterns = [
    path('', ReactAppView.as_view(), name='index'),
    path('auth/login/', ReactAppView.as_view(), name='login'),
    path('auth/register/', ReactAppView.as_view(), name='register'),
    re_path(r'^app/.*', ReactAppView.as_view(), name='app'),
]
```
- `path('', ReactAppView.as_view(), name='index')` : Sert la page d'accueil (`/`).
- `path('auth/login/', ReactAppView.as_view(), name='login')` : Sert la page de connexion.
- `path('auth/register/', ReactAppView.as_view(), name='register')` : Sert la page d'inscription.
- `re_path(r'^app/.*', ReactAppView.as_view(), name='app')` : Sert toutes les routes commençant par `/app/`, qui correspondent à la logique de l'application principale React.

Chacune de ces routes est un point d'entrée où Django livre le même `index.html` de React, mais avec la possibilité d'injecter un état initial différent si nécessaire (bien que dans la mise en œuvre actuelle, l'état initial soit global).

### `web/views.py`
Ce fichier contient la logique principale pour servir l'application React et injecter les données du backend.

**Fonctions et Classes Clés :**

1.  **`get_initial_state(request)` :**
    -   **Description :** Collecte les données pertinentes du backend (informations utilisateur authentifié, jeton CSRF, statistiques du projet, configurations) qui doivent être disponibles pour l'application React dès son démarrage.
    -   **Contenu :** Récupère l'utilisateur (`request.user`), le jeton CSRF (`get_token(request)`), les statistiques des modèles (`Norme`, `Expert`, `CTM`, `WG`) et les paramètres de configuration.
    -   **Utilisation :** Les données sont sérialisées en JSON et injectées dans `window.__INITIAL_STATE__` côté React.

2.  **`render_react(request)` :**
    -   **Description :** Lit le fichier `index.html` pré-compilé de l'application React et injecte le script `window.__INITIAL_STATE__` avant de renvoyer le HTML au client.
    -   **Chemin `index.html` :** Le fichier est attendu à `/home/minato/projet/web/static/dist/index.html`.
    -   **Gestion des erreurs :** Renvoie une page 404 si `index.html` n'est pas trouvé, indiquant que l'application React n'a pas été compilée.

3.  **`ReactAppView(View)` :**
    -   **Description :** Une vue basée sur les classes de Django (`django.views.View`) qui sert de contrôleur pour toutes les routes React principales. Sa méthode `get` appelle simplement `render_react(request)`.
    -   **Rôle :** C'est le point d'entrée générique pour toutes les pages React gérées par Django.

### `web/static/dist/`
Ce répertoire est la destination de la compilation (build) de l'application React.
- Il contient le `index.html` principal.
- Il contient un sous-répertoire `assets/` avec les fichiers JavaScript et CSS minifiés et "versionnés" (par exemple, `index-TcLQOM-r.js`, `index-BbTtYyhv.css`).
- Ces fichiers sont servis par Django via `STATIC_URL = '/static/'` et `STATICFILES_DIRS` configuré dans `config/settings.py`.

## 3. Fichiers Clés du Frontend React (Contexte pour Django)

### `frontend/src/RouteSwitch.tsx`
- **Description :** Ce fichier utilise `react-router-dom` pour définir le routage côté client de l'application React. Il contient la logique pour naviguer entre `Landing`, `Login`, `Register`, `App` et d'autres routes.
- **Interaction avec Django :** Les chemins définis ici (`/`, `/auth/login/`, `/auth/register/`, `/app/*`) sont ceux que Django mappe dans `web/urls.py` pour servir le `index.html` initial. Une fois le `index.html` chargé, React Router prend le relais pour la navigation au sein de ces sections.

### `frontend/src/App.tsx`
- **Description :** C'est le composant racine de l'application React principale, qui peut contenir plusieurs sections et sous-composants.
- **Interaction avec Django :** Il est rendu lorsque la route `/app/*` est activée par React Router. Il utilisera les données de `window.__INITIAL_STATE__` pour initialiser son état ou afficher des informations spécifiques à l'utilisateur.

### `frontend/vite.config.ts`
- **Description :** Fichier de configuration pour Vite, l'outil de build de React.
- **Configuration clé :**
    -   `base: '/static/'` : Indique à Vite de préfixer toutes les URLs des assets générés par `/static/`.
    -   `build.outDir: path.resolve(__dirname, '../web/static/dist')` : Définit le répertoire de sortie de la compilation de React, assurant que les fichiers sont placés là où Django s'attend à les trouver.

## 4. Flux d'Interaction (Synthèse)

1.  **Requête Navigateur :** L'utilisateur accède à une URL comme `http://127.0.0.1:8000/auth/login/`.
2.  **Django Intercepte :** Le `config/urls.py` de Django délègue la requête au `web/urls.py`.
3.  **Route Django Match :** Le `web/urls.py` trouve une correspondance pour `/auth/login/` et dirige la requête vers `ReactAppView.as_view()`.
4.  **`ReactAppView` Exécute `render_react` :**
    -   `get_initial_state` collecte les données du backend.
    -   `index.html` est lu depuis `web/static/dist/index.html`.
    -   Un script injecte les données `initial_state` (sérialisées en JSON) dans `window.__INITIAL_STATE__` de l'HTML.
    -   Le HTML modifié est renvoyé au navigateur.
5.  **Navigateur Charge React :** Le navigateur charge le `index.html` et exécute le JavaScript de React.
6.  **React S'Initialise :** L'application React démarre, lit `window.__INITIAL_STATE__`, et `RouteSwitch.tsx` (via `BrowserRouter`) détecte la route actuelle (`/auth/login/`) et rend le composant React `Login`.
7.  **Navigation Côté Client :** Si l'utilisateur clique sur un lien vers `/app/dashboard`, React Router intercepte la navigation et rend le composant `Dashboard` sans nouvelle requête à Django.

Ce système garantit que Django fournit la "coque" et les données initiales, et React gère l'interactivité et le routage interne.
