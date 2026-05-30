# ✅ Authentification Hybride - Configuration Complète

## 🎯 Objectif
Système d'authentification où :
- **Landing + Normes publiques** = accessible à tous
- **Login/Register** = pour s'inscrire ou se connecter
- **Espace /app** = accessible uniquement aux **experts authentifiés**

---

## 🏗️ Architecture Implémentée

### Frontend (React - `/frontend/`)

#### `main.tsx` - Point d'entrée
- ✅ Utilise `AuthProvider` pour gérer l'état d'authentification globalement
- ✅ Affiche `LoadingScreen` pendant la vérification de session
- ✅ Routage conditionnel :
  - Routes publiques : Landing, Login, Register, /public/norms
  - Route protégée : /app (seulement si `isAuthenticated === true`)
- ✅ ErrorBoundary autour de App pour capturer les erreurs JS

#### `context/AuthContext.tsx` - Gestion d'authentification
- ✅ `useEffect` au montage : appelle `/api/v1/auth/me/`
  - Si 200 → utilisateur authentifié
  - Si 403 → utilisateur non-authentifié (normal)
- ✅ Méthodes :
  - `login(username, password)` → POST `/api/v1/auth/login/`
  - `logout()` → POST `/api/v1/auth/logout/`
  - `register(data)` → POST `/api/v1/auth/register/`
- ✅ Partage globalement : `isAuthenticated`, `user`, `error`, `isLoading`

#### `utils/api/client.ts` - Client API avec CSRF
- ✅ Gère automatiquement le CSRF token (pour POST/PUT/DELETE/PATCH)
- ✅ Envoie les cookies de session via `credentials: 'same-origin'`
- ✅ Redirige vers login si 401 (session expirée)

#### `components/ErrorBoundary.tsx` - Capture d'erreurs
- ✅ React Error Boundary pour capturer les erreurs JS
- ✅ Affiche l'erreur exacte pour debug
- ✅ Bouton "Réessayer" qui redirige vers Landing

---

### Backend (Django - `/api/v1/`)

#### `auth_views.py::AuthViewSet` - Endpoints d'authentification
```
POST /api/v1/auth/register/    (AllowAny)        → UserRegistrationSerializer
POST /api/v1/auth/login/       (AllowAny)        → Crée session Django
GET  /api/v1/auth/me/          (IsAuthenticated) → Retourne user courant
POST /api/v1/auth/logout/      (IsAuthenticated) → Détruit session
PATCH /api/v1/auth/profile/    (IsAuthenticated) → Met à jour profil
POST /api/v1/auth/change-password/ (IsAuthenticated) → Change mot de passe
```

#### Configuration Django (`config/settings.py`)
- ✅ `CORS_ALLOWED_ORIGINS` : localhost:3000, localhost:8000
- ✅ `SESSION_ENGINE` : django.contrib.sessions.backends.cache
- ✅ CSRF configuré : automatiquement géré par middleware

---

## 🧪 Comptes de Test

| Compte | Credentials | Type | Accès |
|--------|-------------|------|-------|
| Expert | `expert_test` / `Expert123!@#` | Expert (is_expert=True) | `/app` (workspace) |
| User | `user_test` / `User123!@#` | Simple (is_expert=False) | `/public/norms` (public norms) |

**Créés via** : `python manage.py shell` + `User.objects.create_user(...)`

---

## 🚀 Flux Utilisateur

### 1️⃣ Utilisateur Non-Connecté
```
http://localhost:8000/
↓ (AuthContext.checkAuth() → 403)
↓ isAuthenticated = false
↓
Landing Page (+ options Login/Register)
```

### 2️⃣ Login Expert
```
http://localhost:8000/auth/login/
↓ (Saisir expert_test / Expert123!@#)
↓ POST /api/v1/auth/login/
↓ (Django crée session)
↓ AuthContext.login() success
↓
Redirect to /app (espace de travail)
```

### 3️⃣ Expert dans /app
```
http://localhost:8000/app/
↓ (AuthContext.me() → 200, isAuthenticated = true)
↓
App Component (espace de travail avec éditeur, normes, etc.)
```

### 4️⃣ Logout
```
POST /api/v1/auth/logout/
↓ (Django supprime session)
↓ AuthContext.logout() success
↓
Redirect to /auth/login/
```

---

## 📝 Intégration Login/Register

### À faire dans `pages/Login.tsx`
```tsx
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      // Navigation automatique après login (à ajouter dans AuthContext)
      navigate('/app/');
    } catch (err) {
      // Erreur affichée dans useAuth hook
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Connexion...' : 'Se connecter'}
      </button>
      {error && <p className="text-red-500">{error}</p>}
    </form>
  );
}
```

### Redirection Post-Login
```tsx
// Dans AuthContext.tsx::login() - à ajouter
const login = async (username: string, password: string) => {
  // ... login call ...
  if (response.status === 200 && response.data?.user) {
    setUser(response.data.user)
    setIsAuthenticated(true)
    
    // Redirection basée sur le rôle
    if (response.data.user.is_expert) {
      window.location.href = '/app/' // expert → workspace
    } else {
      window.location.href = '/public/norms/' // user simple → normes publiques
    }
  }
}
```

---

## 🐛 Débogage

### Console Navigateur (F12)
- Erreurs JavaScript capturées par ErrorBoundary
- Network tab : vérifier les appels `/api/v1/auth/*`
- Application tab : vérifier le cookie `sessionid`

### Logs Django
```bash
# Si vous voyez "Forbidden: /api/v1/auth/me/"
→ Utilisateur non-connecté (attendu, AuthContext gère)

# Si you voyez une autre erreur
→ Vérifier CORS/CSRF ou permissions dans auth_views.py
```

### Test API Manual
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"expert_test","password":"Expert123!@#"}' \
  -c /tmp/cookies.txt

# Vérifier session
curl http://localhost:8000/api/v1/auth/me/ -b /tmp/cookies.txt
```

---

## ✅ Checklist d'Implémentation

- [x] AuthContext avec vérification d'auth au montage
- [x] main.tsx avec routage conditionnel
- [x] ErrorBoundary pour erreurs JS
- [x] Endpoints d'auth dans Django
- [x] CORS/CSRF configurés
- [x] Comptes de test créés
- [x] Build React réussi
- [ ] **À Faire** : Connecter Login.tsx à `useAuth().login()`
- [ ] **À Faire** : Ajouter redirection post-login vers /app ou /public/norms
- [ ] **À Faire** : Tester flux complet
- [ ] **À Faire** : Tester logout
- [ ] **À Faire** : Ajouter boutton logout dans App.tsx

---

## 📖 Voir Aussi

- `plan.md` - Plan structuré avec todos et dépendances
- `TEST_INSTRUCTIONS.md` - Guide de test détaillé
- `api/v1/auth_views.py` - Implémentation des endpoints
- `frontend/src/context/AuthContext.tsx` - Logique d'authentification
- `frontend/src/main.tsx` - Configuration des routes

