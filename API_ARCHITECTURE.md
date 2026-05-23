# 🏗️ Architecture API REST CNETP

## 📊 Vue d'Ensemble

```
┌────────────────────────────────────────────────────────────────┐
│                     CLIENTS (Mobile + Web)                     │
├────────────────────────────────────────────────────────────────┤
│                     REST API (HTTP/JSON)                       │
│                   Django REST Framework v1                     │
├────────────────────────────────────────────────────────────────┤
│                     Couche Métier (Apps)                       │
│  ┌──────────┬──────────┬────────────┬──────────┬────────────┐  │
│  │  Core    │ Experts  │ Governance │  Norms   │ Amendments │  │
│  │ (Auth)   │(Struct)  │ (CTM/WG)   │(Versions)│  (Votes)   │  │
│  └──────────┴──────────┴────────────┴──────────┴────────────┘  │
│  ┌──────────┬──────────┬────────────┬──────────┬────────────┐  │
│  │ Meetings │ Payments │ Validation │  Public  │ Logging    │  │
│  │  (PV)    │ (Cotis)  │ (CTC WF)   │(Publish) │  (Audit)   │  │
│  └──────────┴──────────┴────────────┴──────────┴────────────┘  │
├────────────────────────────────────────────────────────────────┤
│                        ORM Django                              │
│           ┌─────────────────────────────────┐                  │
│           │  PostgreSQL / SQLite            │                  │
│           │  (11 Models, Audit Log)         │                  │
│           └─────────────────────────────────┘                  │
├────────────────────────────────────────────────────────────────┤
│              Cache (Redis) + Tasks (Celery)                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Couche d'Authentification & Sécurité

```
┌──────────────────────────────────────────────────────┐
│             REQUEST HTTP (GET/POST/PUT...)           │
├──────────────────────────────────────────────────────┤
│  1. Django Middleware (CSRF, Sessions)               │
│  2. REST Framework Auth Backend                      │
│     ├─ Session Authentication                        │
│     └─ (JWT préparé pour phase 3)                    │
├──────────────────────────────────────────────────────┤
│  3. Permission Classes (Granulaires)                 │
│     ├─ IsAuthenticated (Tous les utilisateurs)      │
│     ├─ IsExpert (Experts validés)                    │
│     ├─ IsCTCCoordinator (CTC Staff)                  │
│     ├─ IsMinister (Signature)                        │
│     └─ Custom (IsExpertOfCTM, IsOwnerOrCTC, etc)    │
├──────────────────────────────────────────────────────┤
│  4. View/ViewSet Processing                          │
│  5. Response Serialization                           │
├──────────────────────────────────────────────────────┤
│             RESPONSE JSON (200/401/403...)           │
└──────────────────────────────────────────────────────┘
```

---

## 🛣️ Router & URLs

```
config/urls.py (Routing Principal)
    ↓
config/
├── admin/ → Django Admin
├── api-auth/ → Login/Logout DRF
└── api/v1/ ← POINT D'ENTRÉE API
    ↓
api/v1/urls.py (DefaultRouter)
    ↓
    ├─ auth/ → AuthViewSet (Register, Login, Logout, Profile)
    ├─ users/ → UserListViewSet
    ├─ structures/ → StructureViewSet
    ├─ experts/ → ExpertViewSet
    ├─ ctm/ → CTMViewSet
    ├─ wg/ → WGViewSet
    ├─ affectations/ → AffectationViewSet
    ├─ roles-ctm/ → RoleCTMViewSet
    └─ comite-pilotage/ → ComitePilotageViewSet
```

---

## 🔄 Flow Authentification Complet

```
┌─────────────────────────────────────────────────────────────────┐
│                    1️⃣ REGISTRATION (Public)                      │
├─────────────────────────────────────────────────────────────────┤
│ POST /auth/register/                                             │
│ {username, email, password, first_name, last_name, phone, ...}  │
│              ↓                                                    │
│ UserRegistrationSerializer.create()                              │
│   - Validate email unique                                        │
│   - Validate password match                                      │
│   - Create User model                                            │
│              ↓                                                    │
│ RESPONSE 201: {id, username, email, ...}                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    2️⃣ LOGIN (Public)                             │
├─────────────────────────────────────────────────────────────────┤
│ POST /auth/login/ {username, password}                           │
│              ↓                                                    │
│ authenticate(username, password)  [Django Auth]                  │
│              ↓                                                    │
│ login(request, user)  [Django Sessions]                          │
│              ↓                                                    │
│ RESPONSE 200 + SET-COOKIE sessionid=xyz                          │
│ {id, username, email, is_expert, is_ctc_staff, message}         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              3️⃣ SUBSEQUENT REQUESTS (Authenticated)              │
├─────────────────────────────────────────────────────────────────┤
│ GET /auth/me/  -b "sessionid=xyz"                                │
│              ↓                                                    │
│ SessionAuthentication                                            │
│   - Read sessionid cookie                                        │
│   - Load User from session                                       │
│   - Set request.user = User                                      │
│              ↓                                                    │
│ Permission Check (IsAuthenticated)                               │
│   - request.user.is_authenticated == True?                       │
│              ↓                                                    │
│ ViewSet.retrieve()/get_serializer_class()/perform_action()       │
│              ↓                                                    │
│ UserDetailSerializer.data → Response JSON                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    4️⃣ LOGOUT (Authenticated)                     │
├─────────────────────────────────────────────────────────────────┤
│ POST /auth/logout/ -b "sessionid=xyz"                            │
│              ↓                                                    │
│ logout(request)  [Django Sessions]                               │
│   - Delete session from database                                 │
│   - Invalidate sessionid                                         │
│              ↓                                                    │
│ RESPONSE 200: {message: "Logged out"}                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👥 Expert Registration Flow (Détaillé)

```
┌──────────────────────────────────────────────────────────────┐
│                  INSCRIPTION EXPERT (Public)                  │
├──────────────────────────────────────────────────────────────┤
│ POST /experts/inscription/                                    │
│ {                                                             │
│   "username": "marie_expert",                                │
│   "email": "marie@example.com",                             │
│   "password": "secure!",                                     │
│   "first_name": "Marie",                                     │
│   "structure_id": 1,                                         │
│   "specialties": "Géotechnique"                             │
│ }                                                             │
│              ↓                                                │
│ ExpertInscriptionSerializer.validate()                        │
│   ✓ Email unique?                                            │
│   ✓ Username unique?                                         │
│   ✓ Passwords match?                                         │
│   ✓ Structure exists?                                        │
│              ↓                                                │
│ User.objects.create_user()                                    │
│   - Set is_expert = True                                      │
│              ↓                                                │
│ Expert.objects.create()                                       │
│   - status = PENDING                                         │
│   - inscription_date = now()                                 │
│              ↓                                                │
│ RESPONSE 201: Expert created (needs CTC validation)           │
│              ↓                                                │
│ ⏳ CTC Reviews: POST /experts/{id}/activate/                  │
│   → status = ACTIVE                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Governance (CTM/WG) Architecture

```
┌─────────────────────────────────────────────────────┐
│  COMITÉ TECHNIQUE MIROIR (CTM) - 8 au total         │
├─────────────────────────────────────────────────────┤
│ CTM (model)                                         │
│  ├─ number: 1-8                                     │
│  ├─ name: "Géotechnique & Risques Naturels"        │
│  ├─ scientific_president: Expert (FK)              │
│  ├─ rapporteur: Expert (FK)                        │
│  ├─ secretary: Expert (FK)                         │
│  ├─ working_groups: WG[] (reverse FK)              │
│  └─ affectations: Affectation[] (reverse FK)       │
│              ↓                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ GROUPE DE TRAVAIL (WG) - 2-3 par CTM        │   │
│  ├─────────────────────────────────────────────┤   │
│  │ WG (model)                                  │   │
│  │  ├─ ctm: CTM (FK)                           │   │
│  │  ├─ number: 1-3                             │   │
│  │  ├─ name: "Reconnaissance & Essais"         │   │
│  │  ├─ president: Expert (FK)                  │   │
│  │  ├─ rapporteur: Expert (FK)                 │   │
│  │  ├─ secretary: Expert (FK)                  │   │
│  │  └─ affectations: Affectation[]             │   │
│  │              ↓                              │   │
│  │  ┌─────────────────────────────────────┐    │   │
│  │  │ AFFECTATION (Expert → CTM/WG)        │    │   │
│  │  ├─────────────────────────────────────┤    │   │
│  │  │ Affectation (model)                  │    │   │
│  │  │  ├─ expert: Expert (FK)              │    │   │
│  │  │  ├─ ctm: CTM (FK)                    │    │   │
│  │  │  ├─ wg: WG (FK)                      │    │   │
│  │  │  ├─ is_primary_ctm: Boolean          │    │   │
│  │  │  ├─ is_primary_wg: Boolean           │    │   │
│  │  │  └─ affectation_date: DateTime       │    │   │
│  │  │              ↓                       │    │   │
│  │  │  ┌─────────────────────────────┐     │    │   │
│  │  │  │ 4-5 EXPERTS par WG           │     │    │   │
│  │  │  │ (Expert model)                │     │    │   │
│  │  │  │  ├─ user: User (FK)          │     │    │   │
│  │  │  │  ├─ structure: Structure (FK) │     │    │   │
│  │  │  │  ├─ status: ACTIVE            │     │    │   │
│  │  │  │  └─ specialties: str          │     │    │   │
│  │  │  └─────────────────────────────┘     │    │   │
│  │  └─────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Request-Response Lifecycle

```
HTTP REQUEST
    ↓
URL Router (api/v1/urls.py)
    ↓
ViewSet Class (e.g., ExpertViewSet)
    ↓
get_permissions() → Check permission
    ↓
get_serializer_class() → Select serializer
    ↓
Action Method (list/retrieve/create/update/destroy)
    ↓
QuerySet filtering & pagination
    ↓
Serializer.data → Convert to JSON
    ↓
HTTP RESPONSE (200/201/401/403/404/etc)
```

---

## 📋 Serializers Hierarchy

```
Serializers (api/v1/):

1. AUTH
   ├─ UserRegistrationSerializer
   ├─ UserLoginSerializer
   ├─ UserDetailSerializer
   ├─ UpdateProfileSerializer
   └─ ChangePasswordSerializer

2. EXPERTS
   ├─ StructureSerializer
   ├─ ExpertBasicSerializer
   ├─ ExpertDetailSerializer
   ├─ ExpertCreateUpdateSerializer
   └─ ExpertInscriptionSerializer

3. GOVERNANCE
   ├─ CTMBasicSerializer
   ├─ CTMDetailSerializer
   ├─ CTMCreateUpdateSerializer
   ├─ WGBasicSerializer
   ├─ WGDetailSerializer
   ├─ WGCreateUpdateSerializer
   ├─ AffectationSerializer
   ├─ AffectationCreateSerializer
   ├─ AffectationBulkSerializer
   ├─ RoleCTMSerializer
   └─ ComitePilotageSerializer
```

---

## 🎯 Permission Matrix

```
                 │ Public │ Expert │ CTC │ Minister │
─────────────────┼────────┼────────┼─────┼──────────┤
/auth/register   │   ✅   │   ✅   │ ✅  │    ✅    │
/auth/login      │   ✅   │   ✅   │ ✅  │    ✅    │
/auth/logout     │   ❌   │   ✅   │ ✅  │    ✅    │
/experts/        │   ❌   │   ✅   │ ✅  │    ✅    │
/experts/{id}/activate │ ❌ │ ❌  │ ✅  │    ✅    │
/ctm/            │   ❌   │   ✅   │ ✅  │    ✅    │
/ctm/ (create)   │   ❌   │   ❌   │ ✅  │    ✅    │
/norms/          │   ❌   │   ✅   │ ✅  │    ✅    │
/norms/ (publish)│   ❌   │   ❌   │ ❌  │    ✅    │
/normes/ (public)│   ✅   │   ✅   │ ✅  │    ✅    │
```

---

## 🚀 Déploiement Architecture

```
┌─────────────────────────────────────────────────────┐
│              NGINX Reverse Proxy                    │
│              (Port 80/443)                          │
├─────────────────────────────────────────────────────┤
│  Load Balancer / SSL Termination                    │
├─────────────────────────────────────────────────────┤
│  Django Application Servers (Gunicorn/uWSGI)        │
│  (Multiple instances for high availability)         │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┬──────────────┬──────────────┐     │
│  │ PostgreSQL   │ Redis Cache  │ Celery Task  │     │
│  │ (Persistent) │ (Sessions)   │ (Async Jobs) │     │
│  └──────────────┴──────────────┴──────────────┘     │
├─────────────────────────────────────────────────────┤
│  Static Files CDN + Media Uploads                   │
│  (S3/MinIO compatible storage)                      │
└─────────────────────────────────────────────────────┘
```

---

## 💾 Database Schema (Simplified)

```
User (Django)
├─ username, email, password_hash
├─ first_name, last_name, phone, province
├─ is_expert, is_ctc_staff, is_minister
└─ created_at, updated_at

Expert
├─ user_id (FK)
├─ structure_id (FK)
├─ status (PENDING/ACTIVE/INACTIVE)
├─ specialties, cv, bank_account
└─ inscription_date, activation_date

Structure
├─ name, acronym, category
├─ email, phone, contact_person
└─ created_at, updated_at

CTM
├─ number (1-8), name, description
├─ scientific_president_id (FK Expert)
├─ rapporteur_id (FK Expert)
├─ secretary_id (FK Expert)
└─ iso_reference, arso_reference

WG
├─ ctm_id (FK)
├─ number, name, description, scope
├─ president_id (FK Expert)
├─ rapporteur_id (FK Expert)
├─ secretary_id (FK Expert)
└─ created_at, updated_at

Affectation
├─ expert_id (FK)
├─ ctm_id (FK)
├─ wg_id (FK)
├─ is_primary_ctm, is_primary_wg
└─ affectation_date

ComitePilotage + PilotageMembreship
├─ expert_id (FK)
├─ role (PRESIDENT/VICE_PRESIDENT/SECRETARY/RAPPORTEUR/CONSEILLER)
└─ created_at

AuditLog
├─ action (CREATE/UPDATE/DELETE)
├─ content_type, object_id
├─ user_id, ip_address
├─ changes (JSON)
└─ timestamp
```

---

**Architecture complète et fonctionnelle** ✅  
**Prêt pour Phase 3** 🚀

