# Auth Flow — Simple users vs Experts

Résumé des décisions et des endpoints pour l'authentification

- Public registration
  - Endpoint: `POST /api/v1/auth/register/`
  - But: crée uniquement des comptes `simple user` (champ `is_expert` forcé à `false`).
  - UI: Frontend page: `frontend/src/pages/Register.tsx`

- Login
  - Endpoint: `POST /api/v1/auth/login/`
  - UI: Frontend page: `frontend/src/pages/Login.tsx`

- Experts
  - Les experts ne doivent pas s'inscrire via `/auth/register/`.
  - Endpoint public pour inscription experts: `POST /api/v1/experts/inscription/` (géré par `api/v1/experts_views.py`).
  - Experts ont un flux d'activation spécifique et des champs supplémentaires (structure, specialties, décret de nomination, etc.).

- Notes de sécurité
  - Auth basée sur Session Django (cookie `sessionid`).
  - CSRF token géré côté frontend via `frontend/src/utils/api/django-csrf.ts`.

- Fichiers modifiés / ajoutés
  - Backend: `api/v1/auth_views.py` (vérifie et bloque l'inscription d'expert)
  - Backend: `api/v1/auth_serializers.py` (force `is_expert=False` à la création)
  - Frontend: `frontend/src/pages/Login.tsx` (nouvelle page login)
  - Frontend: `frontend/src/pages/Register.tsx` (nouvelle page register)
  - Frontend: `frontend/src/RouteSwitch.tsx` (routes `/auth/login/` et `/auth/register/` ajoutées)
  - Docs: `API_DOCUMENTATION.md` (note ajoutée sur restriction d'inscription)
  - Docs: `docs/AUTH_FLOW.md` (ce fichier)

- Prochaines étapes recommandées
  1. Ajouter tests unitaires pour `UserRegistrationSerializer.create()`.
  2. Ajouter e2e tests frontend pour le flux inscription/connexion.
  3. Mettre à jour la Landing page pour afficher clairement les liens `Se connecter` / `S'inscrire` selon le public.


