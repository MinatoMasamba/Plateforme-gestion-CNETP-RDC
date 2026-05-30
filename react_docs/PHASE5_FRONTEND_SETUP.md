# 🎯 Phase 5 - Django-React Hybrid Frontend

## ✅ Tâches Complétées Phase 1

### 1. ✅ Copie du Projet React
- Source: `/home/minato/Téléchargements/cntp-main`
- Destination: `/home/minato/projet/frontend`
- Status: **COPIÉ ET ADAPTÉ**

### 2. ✅ Adaptation pour Django 100%
- ❌ Supprimé: `server.ts`, Express, esbuild
- ✅ Adapté: `package.json` (dev: Vite uniquement)
- ✅ Adapté: `vite.config.ts` (build vers `web/static/dist`)

### 3. ✅ Services API Django-Compatibles
Créés :
- `frontend/src/utils/api/django-csrf.ts` - Gestion du CSRF token Django
- `frontend/src/utils/api/client.ts` - Wrapper fetch avec CSRF + session
- `frontend/src/hooks/useAuth.ts` - Hook React pour l'authentification

### 4. ✅ Template Django
- Créé: `templates/base.html`
  - Include CSRF token dans meta tag
  - Include token dans window.DJANGO_CSRF_TOKEN
  - Div pour React root
  - Chargement du bundle Vite

### 5. ✅ Vue Django pour React
- Créé: `web/views.py`
  - `index()` - Serve React avec context Django
  - `current_user()` - API pour récupérer user courant
  - `user_permissions()` - API pour les permissions
  - `health_check()` - Santé de l'app

### 6. ✅ Routing Django
- Créé: `web/urls.py`
- Modifié: `config/urls.py` (inclus `web.urls`)
- Modifié: `config/settings.py` (TEMPLATES + csrf context processor)

---

## 📱 Architecture Finale

```
Django (100%) + React (Frontend)
├── Django Serve HTML avec React root
│   └── `templates/base.html` ← Vue pour React
├── Django API Endpoints
│   └── `/api/v1/*` (DRF)
└── React App
    ├── Authentification (Django sessions)
    ├── CSRF (token Django)
    └── Appels API (via djangoFetch)
```

---

## 🔐 Authentification

### Flow
1. Utilisateur login → Django crée session (sessionid cookie)
2. React récupère CSRF token → `getCsrfToken()`
3. React appel API → `djangoFetch()` inclut:
   - CSRF token dans header `X-CSRFToken`
   - sessionid dans cookies (automatique)

### Hooks React
```tsx
import { useCurrentUser, useRole, usePermission } from '@/hooks/useAuth'

function MyComponent() {
  const { user, isAuthenticated } = useCurrentUser()
  const isExpert = useRole('expert')
  const canVote = usePermission('can_vote')
  
  if (!isAuthenticated) return <Redirect to="/login" />
  return <div>{user?.full_name}</div>
}
```

---

## 🚀 Prochaines Étapes (Phase 2-5)

### Phase 2: Installer & Build React
```bash
cd frontend
npm install
npm run build  # Génère /web/static/dist
```

### Phase 3: Adapter les Composants React
1. Importer les rôles CNETP (voir spec)
2. Adapter `ProfileSimulationModal` → `AuthContext`
3. Modifier les calls API → utiliser `djangoFetch`
4. Remplacer mock data → vraies données Django

### Phase 4: Intégration Complète
1. Django serve `/` → React
2. Django serve API `/api/v1/*`
3. Tests E2E (login, navigation, votes)

### Phase 5: Production Ready
1. Build production: `npm run build`
2. Django `collectstatic`
3. Deployment

---

## 📋 Architecture des Rôles CNETP (Intégrée)

Hiérarchie complète avec 6 niveaux:

### Niveau 1: Haute Tutelle
- **Ministre des ITP** - Signe arrêtés d'homologation
- **Secrétaire Général** - Supervise la CTC
- **Directeur Cabinet** - Coordination politique

### Niveau 2: Comité de Pilotage (24 experts)
- **Président** - Anime le pilotage
- **Vice-Président** - Suppléant
- **Secrétaire** - Rédaction PV
- **Rapporteur Général** - Synthèse travaux
- **20 Conseillers** - Orientation & arbitrage

### Niveau 3: CTC (20 experts)
- **Coordonnateur Principal** - Pilote CTC
- **Coordonnateur Adjoint** - Appui
- **Experts CTC** - Veille, légiste, comptable, etc.

### Niveau 4: CTM (8 × 19-20 experts)
- **Président Scientifique** - Arbitrage scientifique
- **Rapporteur Technique** - Gestion réunions/votes
- **Secrétaire Permanent** - Admin
- **Membres permanents** - Rédaction normes

### Niveau 5: WG (24 × 4-5 experts)
- **Président WG** - Anime rédaction
- **Membres rédacteurs** - Proposent amendements
- **Observateurs** - Consultation

### Niveau 6: Structures (16 girons)
- Admin, Offices, Ordres, Académiques, Société civile, Privé

---

## 🛠️ Fichiers-Clés

| Fichier | Rôle |
|---------|------|
| `/frontend` | React App (Vite build) |
| `templates/base.html` | Template Django pour React |
| `web/views.py` | Vues Django |
| `web/urls.py` | Routing web |
| `frontend/src/utils/api/client.ts` | API client avec CSRF |
| `frontend/src/hooks/useAuth.ts` | Auth hook React |

---

## 📚 Documentation

- `DOCUMENTATION.md` - Specs React complets
- `PHASE4_MOBILE_SUMMARY.md` - API mobile
- `MOBILE_API_REFERENCE.md` - Endpoints API
- `PHASE5_FRONTEND_PLAN.md` - (À créer) Intégration complète

---

## ✨ Status

- ✅ Phase 1: React copié et adapté
- ⏳ Phase 2: Installation et build
- ⏳ Phase 3: Adaptation des composants
- ⏳ Phase 4: Intégration complète
- ⏳ Phase 5: Production ready

**Prochaine action:** Installer npm et builder React → `/web/static/dist`

