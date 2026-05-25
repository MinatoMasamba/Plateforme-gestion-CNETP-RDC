# Architecture du Serveur Django et Intégration Hybride React

Ce document définit la structure complète du backend Django de la plateforme CNETP, ses modèles, ses vues et la méthodologie précise pour intégrer React en tant que moteur de template. Cette architecture "Hybride" permet de bénéficier de la puissance de traitement de Django tout en conservant la fluidité SPA (Single Page Application) de React.

---

## 1. Le Concept de l'Architecture Hybride (Django + React)

Plutôt que de séparer totalement le frontend (Node/Serveur HTTP) et le backend (Django/Gunicorn), l'approche hybride rassemble tout sous le parapluie de Django. 

**Comment ça marche ?**
1. **Compilation Vite (React) :** Le code React (TypeScript) est compilé via `npm run build`. Les fichiers minifiés (JS, CSS) sont générés directement dans le dossier `static/dist/` de Django.
2. **Template Catch-All Django :** Django intercepte toutes les requêtes URL qui ne sont pas des `/api/...` ou `/admin/...` et renvoie un unique template `base.html` (ou `index.html`).
3. **Session et CSRF unifiés :** React s'exécutant sur le même domaine et port que Django, aucune API clé n'est requise. React hérite automatiquement des *Cookies de Session* (`sessionid`) et lit le *CSRF Token* injecté dans le DOM par Django.

---

## 2. Configuration Exacte pour le Contrôle Total du Frontend

Pour que le frontend React (Widgets, Modals, Éditeur) puisse prendre le relai fluide de Django, il faut adapter certains points du serveur à la lettre :

### A. Le Routage Catch-All (config/urls.py et web/urls.py)
Django doit diriger les API vers DRF, et le reste vers React.

```python
# config/urls.py
from django.urls import path, re_path, include
from web.views import ReactAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.v1.urls')), # Le Frontend communiquera avec ces routes
    
    # ⚠️ Catch-All : Toute autre URL est envoyée à React
    re_path(r'^(?!api/|admin/).*$', ReactAppView.as_view(), name='react_app'),
]
```

### B. La Vue d'Injection (web/views.py)
La vue qui lance React doit injecter les métadonnées de l'utilisateur actif afin que React n'ait pas à faire une requête supplémentaire pour savoir qui est connecté (accélération extrême du rendu).

```python
# web/views.py
from django.views.generic import TemplateView
import json

class ReactAppView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Injecter le profil utilisateur dans window.APP_CONTEXT
        if self.request.user.is_authenticated:
            context['user_data'] = json.dumps({
                "id": self.request.user.id,
                "email": self.request.user.email,
                "is_expert": self.request.user.is_expert,
                # Tous attributs vitaux
            })
        else:
            context['user_data'] = "null"
        return context
```

### C. Adaptation du Client Sécurisé React (src/utils/api.ts)
Le frontend est obligé de renvoyer le jeton CSRF de Django pour sécuriser chaque action (`POST`, `PUT`, `DELETE`).

```typescript
// src/utils/api.ts
import axios from 'axios';

// 1. Récupération du jeton depuis les cookies de Django
function getCookie(name: string) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
        }
    }
  }
  return cookieValue;
}

const apiClient = axios.create({
  baseURL: '/api/v1/', // Relatif car hybride (même domaine)
  withCredentials: true, // Très important : transporte le cookie sessionid
});

// 2. Intercepteur : On attache toujours le CSRF token
apiClient.interceptors.request.use((config) => {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
});

export default apiClient;
```

---

## 3. Structure Détaillée de la Couche Métier (Modèles & Vues Django)

Pour que chaque page de React reçoive l'information nécessaire, voici le découpage détaillé base de données et endpoints (`ViewSets`).

### 3.1. App `core` (Sécurité & Utilisateurs)
**Modèles :**
- `User` : Héritage custom de `AbstractUser`. Ajoute les booléens `is_expert`, `is_ctc_staff`, `is_minister`.
- `AuditLog` : Enregistre qui a modifié quoi.

**ViewSets (api/v1/auth_views.py) :**
- `AuthViewSet` : Méthodes `/auth/login/`, `/auth/logout/`, `/auth/me/`. Fournit l'accès total à l'interface en vérifiant le couple email/password.

### 3.2. App `experts` (Réseau et Structures)
**Modèles :**
- `Expert` : Lié 1-1 à User. Contient validation `status` (PENDING/ACTIVE), `specialties`.
- `Structure` : Les "Girons" (16 instances - Administration, Ordre professionnel...).

**ViewSets (api/v1/experts_views.py) :**
- `ExpertViewSet` : Alimente le composant React `ExpertsModule`. Liste, permissions et activation de rôles.

### 3.3. App `governance` (Hiérarchie CNETP)
**Modèles :**
- `CTM` : Les 8 Comités miroirs principaux.
- `WG` : Les 24 Groupes de travail rattachés aux CTM.
- `Affectation` : Table de jointure (Expert <-> CTM/WG + Rôle comme Président).
- `ComitePilotage` : Les membres exécutifs.

**ViewSets (api/v1/governance_views.py) :**
- `CTMViewSet`, `WGViewSet` : Utilisé dans React pour populer les menus déroulants et hiérarchies de classement documentaire.

### 3.4. App `norms` (Rédaction et Édition)
**Modèles :**
- `Norme` : Les métadonnées du document.
- `NormeVersion` : Sauvegarde absolue des états complets et validés.
- `ChangementVersion` : "Tracking" (Différences).

**ViewSets (api/v1/norms_views.py) :**
- `NormeViewSet` : Alimente `EditorArea`. Contient des `@action` spécifiques pour verrouiller un document (`lock_document`) lors de la rédaction simultanée afin d'éviter les écrasements asynchrones.

### 3.5. App `meetings` (Réunions, Présence)
**Modèles :**
- `Reunion` : Les rendez-vous planifiés.
- `Presence` : Pour les émargements.
- `ProcessusVerbaux` : Le PV généré et signé.

**ViewSets (api/v1/meetings_views.py) :**
- `ReunionViewSet` : Alimente `MeetingsVotesModule`. Fournit l'état en temps réel pour valider les quorums de l'interface en React.

### 3.6. App `amendments` (Système de Vote)
**Modèles :**
- `Amendement` : Une proposition de révision d'article.
- `Vote` : (POUR, CONTRE, ABSTENTION) lié à un ammendement/norme.

**ViewSets :**
- `AmendementViewSet` : Récupéré par `EditorArea` de React pour les vues collaboratives et fil de commentaires.

### 3.7. App `payments` (Finances)
**Modèles :**
- `Cotisation` : Pour les institutions du giron.
- `Paiement` : Les justificatifs.
- `JetonPresence` : Calculé automatiquement si l'Expert était _Present_ à une Réunion.

**ViewSets :**
- `JetonPresenceViewSet` : Alimente `FinancialModule` dans la vue de type "Expert" ou "Comptable Foner".

### 3.8. App `public`
Les points d'arrêt REST ne requièrent aucune authentification (`AllowAny`). Alimentent le composant React `ValidationPublicModule` pour les industriels non connectés.

---

## 4. Adaptations Critiques pour React 

Afin de servir l'application correctement avec des composants réactifs, le backend subit des contraintes strictes :

1. **La Pagination Standardisée :** Chaque `ViewSet` utilise une pagination Django `StandardResultsSetPagination`. Le composant React doit s'y adapter en lisant `response.data.results` (Tableaux de données) et `response.data.count` (Total pour paginer).
2. **Permissions au Niveau Objet (Object-Level Permissions) :** Le backend ne doit pas se contenter de filtrer les requêtes HTTP, il filtre les "QuerySets". Ex: Dans `NormeViewSet.get_queryset()`, on retourne uniquement les normes du `request.user.ctm_affectation`. Ainsi, le frontend *ne reçoit que* ce que l'utilisateur a le droit de voir, évitant tout faille d'affichage.
3. **Transmission Mobile et Hybride:** La mise en place de l'app `mobileapp` (Phase 4) avec DRF SimpleJWT ne change pas le workflow web. Le Web utilise `SessionAuthentication` avec Cookes, le Mobile utilise `JWTAuthentication` dans le `Authorization: Bearer`. Le serveur supporte les deux conjointement de manière transparente.

### Résumé de l'Approche Hybride
1. Vite compile React `dist/` vers `static/dist/`.
2. Lancer : `python manage.py collectstatic`.
3. Lancer : `python manage.py runserver`.
4. Accédez à la page React à partir de votre routeur Django ! Aucun gestionnaire Node/Express n'est nécessaire.
