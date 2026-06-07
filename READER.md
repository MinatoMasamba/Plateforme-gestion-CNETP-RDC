# READER.md - Guide de référence — Plateforme CNETP

Plateforme Django de gestion des activités de la Commission Nationale d'Elaboration
des normes Techniques de construction (CNETP), République Démocratique du Congo.

Ce document reflète l'état réel du projet au 06 juin 2026 et sert de référence
rapide pour tout développeur rejoignant le projet.

---

## 1. Architecture Générale

### Stack technique
- Backend : Django 6.0.5 + Django REST Framework 3.17.1
- Auth : Session (web) + JWT SimpleJWT (mobile)
- API doc : drf-spectacular (Swagger/ReDoc)
- Base de données : SQLite (dev) / PostgreSQL 15 (production via Docker)
- Cache : LocMemCache (dev) / Redis 7 (production via Docker)
- Tâches asynchrones : Celery (broker Redis, commenté en dev)
- Notifications push : Firebase Admin SDK (framework en place, credentials non configurés)
- Frontend web : Templates Django + Tailwind CSS, avec dist React compilé dans /web/static/dist/
- Virtualenv : mon_env/

### Structure des répertoires
```
cnetp_project/
├── config/
│   ├── settings.py          -- Configuration centrale (SQLite dev, PostgreSQL prod)
│   ├── urls.py              -- Routing racine
│   ├── celery.py            -- Configuration Celery
│   └── wsgi.py / asgi.py
│
├── apps/                    -- 13 applications Django
│   ├── core/                -- User custom, BaseModel, AuditLog
│   ├── experts/             -- Expert, Structure
│   ├── governance/          -- CTM, WG, Affectation, hiérarchie complète
│   ├── norms/               -- Norme, NormeVersion, ChangementVersion, NormeVote
│   ├── amendments/          -- Amendement, Vote, ResultatVote
│   ├── meetings/            -- Reunion, Presence, ReunionVote, ProcessusVerbaux
│   ├── payments/            -- Cotisation, Paiement, JetonPresence
│   ├── validation/          -- LegisticReview
│   ├── public/              -- PublicAmendement
│   ├── documents/           -- DocumentFile
│   ├── messaging/           -- Message
│   ├── mobileapp/           -- ActivationToken, PublicUser, PushToken,
│   │                           Notification, NotificationLog,
│   │                           NotificationPreference, MobileSession
│   └── mobile/              -- Stub vide (ne pas confondre avec mobileapp)
│
├── api/
│   └── v1/                  -- 46 ViewSets, 100+ endpoints REST
│       ├── urls.py          -- Routeur principal
│       ├── permissions.py   -- 10 classes de permissions custom
│       ├── pagination.py    -- StandardResultsSetPagination
│       ├── filters.py       -- Filtres avancés
│       ├── pdf_utils.py     -- Génération PDF (normes + PV)
│       ├── *_serializers.py -- Serializers par domaine
│       └── *_views.py       -- ViewSets par domaine
│
├── web/                     -- Application web Django-template
│   ├── views.py             -- 8 vues (Home, App, About, Contact,
│   │                           ExpertRegistration, UserLogin,
│   │                           ExpertLogin, UserRegistration)
│   └── urls.py
│
├── templates/               -- 21 templates Django
│   ├── base.html
│   ├── index.html
│   ├── app/
│   │   ├── app.html         -- Dashboard principal (SPA Django-template)
│   │   └── composants/      -- 11 composants modulaires
│   ├── expert/              -- Auth expert (login, registration)
│   └── user_templates/      -- Auth utilisateur (login, registration)
│
├── tests/
│   ├── conftest.py          -- Fixtures pytest
│   ├── test_models.py       -- Tests modèles de base
│   └── test_norms/          -- Tests normes (documents, intégration, JO)
│
├── manage.py
├── requirements.txt
├── docker-compose.yml       -- PostgreSQL + Redis + Django + Celery + Celery-Beat
├── Dockerfile
└── pytest.ini
```

---

## 2. Modèles de données

### apps/core/
| Modèle    | Description                                              |
|-----------|----------------------------------------------------------|
| User      | AbstractUser étendu : is_expert, is_ctc_staff, is_minister, email_confirmed |
| BaseModel | Classe abstraite avec created_at, updated_at, created_by, updated_by |
| AuditLog  | Traçabilité : action, content_type, object_id, changes (JSONField), ip_address |

### apps/experts/
| Modèle    | Description                                             |
|-----------|---------------------------------------------------------|
| Structure | Structures d'origine (16 types : ADMIN, PUBLIC, PROF…) |
| Expert    | Profil expert lié à User, coordonnées bancaires, cv     |

### apps/governance/
| Modèle              | Description                                      |
|---------------------|--------------------------------------------------|
| CTM                 | 8 Comités Techniques Miroir                      |
| WG                  | 24 Groupes de Travail (4-5 experts par WG)       |
| Affectation         | Lien Expert -> CTM/WG avec rôle                  |
| ComitePilotage      | Comité de pilotage stratégique (24 membres)      |
| PilotageMembreship  | Membres du comité de pilotage                    |
| OriginStructure     | Structures d'origine hiérarchique                |
| TechnicalCell       | Cellule technique CTC                            |
| CTCMembership       | Membres CTC                                      |
| ExecutiveLevel      | Niveau exécutif                                  |
| SteeringCommittee   | Comité directeur                                 |

### apps/norms/
| Modèle           | Description                                         |
|------------------|-----------------------------------------------------|
| Norme            | Projet de norme, cycle de vie 11 statuts, édition collaborative |
| NormeVersion     | Versions successives : numéro, contenu, auteur      |
| ChangementVersion| Détail des modifications par section et type        |
| NormeVote        | Vote expert sur une norme (FOR/AGAINST/ABSTAIN)     |

### apps/amendments/
| Modèle       | Description                                    |
|--------------|------------------------------------------------|
| Amendement   | Proposition d'amendement par un expert         |
| Vote         | Vote sur un amendement                         |
| ResultatVote | Résultat agrégé (quorum, % approbation)        |

### apps/meetings/
| Modèle           | Description                                    |
|------------------|------------------------------------------------|
| Reunion          | Session : CTM, WG, PILOTAGE, ASSEMBLEE, CTC    |
| ReunionVote      | Vote pendant une réunion                       |
| Presence         | Présence/émargement (PRESENT/ABSENT/EXCUSED)   |
| ProcessusVerbaux | PV généré automatiquement, suivi quorum        |

### apps/payments/
| Modèle        | Description                                     |
|---------------|-------------------------------------------------|
| Cotisation    | Cotisation annuelle par structure               |
| Paiement      | Paiement effectué (VIREMENT, CHEQUE, MM…)       |
| JetonPresence | Jeton de présence lié à une réunion             |

### apps/mobileapp/
| Modèle                 | Description                                      |
|------------------------|--------------------------------------------------|
| ActivationToken        | Token d'activation expert (7 jours, usage unique)|
| PublicUser             | Utilisateur public mobile                        |
| PushToken              | Token FCM/APNs pour push notifications           |
| Notification           | Notification persistée (16 types)                |
| NotificationLog        | Journal des envois par fournisseur               |
| NotificationPreference | Préférences par type, quiet hours, digest        |
| MobileSession          | Session mobile active avec device fingerprint    |

### Autres
| App        | Modèle            | Description                          |
|------------|-------------------|--------------------------------------|
| validation | LegisticReview    | Révision légistique avant publication|
| public     | PublicAmendement  | Amendement soumis par le public      |
| documents  | DocumentFile      | Fichiers joints avec métadonnées     |
| messaging  | Message           | Message direct ou contextuel réunion |

---

## 3. API REST — État des endpoints

Base URL : `/api/v1/`
Documentation interactive : `/api/v1/schema/swagger/`
ReDoc : `/api/v1/schema/redoc/`

### Authentification
- Session Django (web) : formulaires de login dans `web/views.py`
- JWT (mobile) : généré via MobileAuthViewSet (SimpleJWT RefreshToken)
- Note : JWTAuthentication est commenté dans DEFAULT_AUTHENTICATION_CLASSES
  pour le web — actif uniquement dans les vues mobiles.

### Groupes d'endpoints

| Groupe             | Préfixe                                             | ViewSets |
|--------------------|-----------------------------------------------------|----------|
| Auth               | /auth/, /users/, /profile/                          | 3        |
| Experts            | /experts/, /structures/, /expert-registration/      | 3        |
| Gouvernance        | /ctm/, /wg/, /affectations/, /roles-ctm/, /comite-pilotage/ | 5  |
| Hiérarchie         | /hierarchy/*                                        | 5        |
| Normes             | /norms/, /norm-versions/, /norm-changes/            | 3        |
| Amendements        | /amendments/, /votes/, /vote-results/               | 3        |
| Réunions           | /reunions/, /presences/, /reunion-votes/, /pv/      | 4        |
| Paiements          | /cotisations/, /paiements/, /jetons/                | 3        |
| Validation         | /legistic-reviews/                                  | 1        |
| Documents          | /documents/, /collaborators/                        | 2        |
| Messagerie         | /messages/                                          | 1        |
| Public             | /public-amendments/                                 | 1        |
| Sidebar/Dashboard  | /working-groups/, /budgets/, /dashboard/kpis/, /tasks/ | 9     |
| Mobile             | /mobile/auth/, /mobile/push-tokens/, /mobile/notifications/, /mobile/notification-preferences/, /mobile/profile/, /mobile/public/ | 6 |

Total : 46 ViewSets, 100+ endpoints.

### Actions PDF (ajoutées en Phase 5)
- `GET /api/v1/norms/{id}/export-pdf/` — Export PDF d'une norme (+ `?version=N`)
- `GET /api/v1/pv/{id}/export-pdf/` — Export PDF d'un procès-verbal

### Permissions custom (/api/v1/permissions.py)
- IsExpert, IsCTCCoordinator, IsMinister, IsExpertOrCTC
- IsOwnerOrCTC, IsExpertOfCTM, ReadOnly, IsPublicOrAuthenticated
- IsLegist, IsMemberOfAnySharedCTM

---

## 4. Frontend Web

### Vues Django (web/views.py)
| Vue                    | URL                       |
|------------------------|---------------------------|
| HomeView               | /                         |
| App                    | /app/                     |
| AboutView              | /about/                   |
| ContactView            | /contact/                 |
| ExpertRegistrationView | /inscription-expert/      |
| UserRegistrationView   | /inscription-simple/      |
| ExpertLoginView        | /se-connecter/            |
| UserLoginView          | /se-connecter-user/       |

### Templates (templates/)
- base.html, index.html, about.html, contact.html
- app/app.html : Dashboard principal mono-page
- app/composants/ : editor_area, history_area, experts_groups_area,
  meetings_module, financial_module, sidebar, messaging_widget,
  legistique_module, validation_module, create_norm_modal, profil_expert
- expert/expert_auth/ : expert_login.html, expert_registration.html
- user_templates/ : user_login.html, user_registration.html

---

## 5. Système de notifications mobiles

### Signaux automatiques (apps/mobileapp/signals.py)
- `notify_norm_published` : à la publication d'une norme
- `notify_payment_due` / `notify_payment_received` : événements paiement
- `notify_meeting_invite` : invitation à une réunion
- `notify_expert_invited` : invitation d'un expert
- `notify_new_message` : nouveau message interne
- `notify_votes_open` : ouverture d'un scrutin

### Tâches Celery (apps/mobileapp/tasks.py)
- `dispatch_notification` : envoi FCM/email avec quiet hours et priorité
- `send_email_notification` : emails via templates HTML
- `send_notification_digest` : digest périodique DAILY/WEEKLY

### Templates email (apps/mobileapp/templates/mobileapp/emails/)
- norm_published.html, payment_due.html, reunion_invite.html,
  expert_invite.html, digest.html

---

## 6. Commandes clés

```bash
# Activer le virtualenv
source mon_env/bin/activate

# Migrations
python manage.py makemigrations
python manage.py migrate

# Superutilisateur
python manage.py createsuperuser

# Serveur de développement
python manage.py runserver

# Tests
pytest tests/ -v
pytest tests/test_norms/ -v
pytest apps/mobileapp/tests.py -v

# Charger la hiérarchie CNETP initiale (à faire avant les tests fonctionnels)
python manage.py create_ctm_structure
python manage.py init_pilotage_and_ctc
python manage.py load_cnetp_hierarchy
python manage.py verify_ctm_structure

# Générer QR code expert
python manage.py generer_qr_expert

# Docker (production)
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# Celery (production, après activation dans settings.py)
celery -A config worker -l info
celery -A config beat -l info

# Backup données
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

---

## 7. Configuration .env

```env
SECRET_KEY=votre_clé_secrète
DEBUG=True                           # False en production
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (production — décommenter dans settings.py)
DB_NAME=cnetp_db
DB_USER=cnetp_user
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Redis (production — décommenter dans settings.py)
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email (production : remplacer par SendGrid/Postmark)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# CORS (domaine de l'application mobile)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Firebase (notifications push)
FIREBASE_CREDENTIALS_PATH=/chemin/vers/firebase-credentials.json
NOTIFICATION_FCM_ENABLED=False       # True quand Firebase configuré
NOTIFICATION_EMAIL_ENABLED=False     # True quand SMTP configuré
```

---

## 8. État des phases de développement

### Phase 1 — Fondations
- [x] 13 applications Django structurées
- [x] 30+ modèles de données avec BaseModel + AuditLog
- [x] Migrations créées et appliquées
- [x] Docker Compose (PostgreSQL + Redis + Celery + Celery-Beat)
- [x] AUTH_USER_MODEL = 'core.User'
- [x] Management commands de chargement données initiales (CTM, WG, hiérarchie)

### Phase 2 — API REST
- [x] 46 ViewSets enregistrés dans api/v1/urls.py
- [x] 100+ endpoints REST documentés
- [x] 10 classes de permissions custom
- [x] Filtrage avancé (django-filter), pagination, tri
- [x] Authentification session (web) + JWT (mobile)
- [x] Swagger/OpenAPI via drf-spectacular

### Phase 3 — Modules métier avancés (API)
- [x] Amendements : AmendementViewSet, VoteViewSet, ResultatVoteViewSet (13 endpoints)
- [x] Réunions : ReunionViewSet, PresenceViewSet, ReunionVoteViewSet, PVViewSet (14 endpoints)
- [x] Paiements : CotisationViewSet, PaiementViewSet, JetonPresenceViewSet (20 endpoints)
- [x] Validation légistique : LegisticReviewViewSet

### Phase 4 — API Mobile
- [x] 7 modèles mobileapp (ActivationToken, PublicUser, PushToken, Notification, NotificationLog, NotificationPreference, MobileSession)
- [x] 6 ViewSets mobiles sous /api/v1/mobile/* (21 endpoints)
- [x] Signaux Django pour notifications automatiques
- [x] Tâches Celery (dispatch, digest, email)
- [x] Templates email (5 types)
- [ ] Credentials FCM/APNs réels (framework en place, attente configuration)
- [ ] Upload de fichiers mobile (POST /mobile/files/upload/)
- [ ] Support offline : ETag headers, SyncQueue

### Phase 5 — Frontend web + PDF
- [x] 21 templates Django
- [x] 8 vues Django (auth + dashboard + pages publiques)
- [x] Dashboard principal (app.html) avec 11 composants modulaires
- [x] Messagerie interne (juin 2026)
- [x] Génération PDF normes (GET /api/v1/norms/{id}/export-pdf/)
- [x] Génération PDF procès-verbaux (GET /api/v1/pv/{id}/export-pdf/)
- [ ] Éditeur collaboratif temps réel (WebSocket)

### Phase 6 — Tests
- [x] conftest.py avec fixtures (user_factory, expert_factory, ctm_factory, wg_factory, norme_factory)
- [x] test_models.py (modèles de base)
- [x] tests/test_norms/ : test_documents.py, test_integration_sprint1.py, test_publication_jo.py
- [x] apps/mobileapp/tests.py (partiel — 13 tests)
- [ ] Tests unitaires mobileapp complets (ActivationToken, flux activation expert)
- [ ] Tests intégration auth (registration → activation → login)
- [ ] Tests workflow vote et paiements
- [ ] Tests E2E

### Phase 7 — Infrastructure production
- [ ] PostgreSQL activé (SQLite actuellement)
- [ ] Redis pour cache/sessions (LocMemCache actuellement)
- [ ] Celery activé (CELERY_BROKER_URL commenté dans settings.py)
- [ ] SMTP réel (console backend actuellement)
- [ ] Rate limiting sur endpoints d'authentification
- [ ] CORS restreint au domaine mobile de production
- [ ] SSL/TLS configuration production
- [ ] Sentry error tracking
- [ ] CI/CD pipeline
- [ ] Backup automatisé base de données

---

## 9. Points d'attention pour les développeurs

**JWT et session** : Le web utilise la session Django ; le mobile utilise JWT
(SimpleJWT). La ligne `JWTAuthentication` est commentée dans
DEFAULT_AUTHENTICATION_CLASSES — ne pas l'activer globalement sans tester
l'impact sur les vues web (les formulaires de login web utilisent la session).

**Celery inactif en dev** : Les imports et tâches sont en place mais
CELERY_BROKER_URL est commenté dans settings.py. Pour activer : décommenter
les lignes Celery dans settings.py et démarrer Redis. En dev, les tâches
s'exécutent de manière synchrone.

**SQLite en dev** : db.sqlite3 est utilisé par défaut. Pour activer PostgreSQL,
décommenter le bloc DATABASES PostgreSQL dans settings.py et fournir les
variables d'environnement DB_*.

**Firebase sans credentials** : Le framework Firebase Admin est intégré
(firebase-admin dans requirements.txt), mais FIREBASE_CREDENTIALS_PATH n'est
pas configuré. Les envois push tombent silencieusement en dev. Mettre
NOTIFICATION_FCM_ENABLED=False pour éviter les erreurs.

**apps/mobile/ vs apps/mobileapp/** : apps/mobile/ est un répertoire stub vide,
distinct de apps/mobileapp/ qui contient toute la logique réelle des notifications
mobiles, sessions et tokens push. Ne pas modifier apps/mobile/.

**Données initiales obligatoires** : Avant tout test fonctionnel, charger la
structure organisationnelle CNETP avec les management commands de governance
(CTM x8, WG x24, hiérarchie). Sans ces données, les endpoints CTM/WG
retournent des listes vides.

---

## 10. Références documentaires internes

- [ENDPOINTS_SUMMARY.md](ENDPOINTS_SUMMARY.md) — Liste exhaustive des endpoints API
- [MOBILE_API_REFERENCE.md](MOBILE_API_REFERENCE.md) — Guide complet API mobile
- [NOTIFICATION_README.md](NOTIFICATION_README.md) — Système de notifications
- [API_ARCHITECTURE.md](API_ARCHITECTURE.md) — Architecture API globale
- [CTM_ORGANISATIONAL_STRUCTURE.md](CTM_ORGANISATIONAL_STRUCTURE.md) — Structure organisationnelle CNETP
- [PHASE4_IMPLEMENTATION_CHECKLIST.md](PHASE4_IMPLEMENTATION_CHECKLIST.md) — Checklist détaillée Phase 4
- [docs/](docs/) — Documentation complémentaire (architecture, modèles, guides)

---

## 11. Bokeseni ya ndenge nini na likambo ya kokonfirmisa adresi ya email (pour ba utilisateurs ya bato nioso)

Esika oyo tokopesa ndimbola ya misala ya sika oyo esalemaki mpo na kokonfirmisa adresi ya email ya ba utilisateurs ya bato nioso. Bolingi na biso ezali ete mobola nyonso akoki kokonfirmisa adresi na ye ya email liboso ya kokokoma na lisalisi ya biso.

1.  **Sima ya kokoma (register_public)**:
    *   Sima ya ko `register_public`, utilisateur akopata ba tokens ya kokoma te. Akopata kaka confirmation ya compte na ye mpe notification ete code ya confirmation etindamaki na email na ye.
    *   Flutter ekolakisa page ya ko saisir code, na esika ya kolakisa utilisateur ete akomi.

2.  **Sima ya ko confirmer email (confirm_email_code)**:
    *   Kokonfirmisa code ya email nde ezali nzela kaka moko oyo utilisateur akopata ba tokens na ye ya `access` mpe `refresh` ya JWT.
    *   Sima ya kokonfirmisa code na ndenge ya solo, système ekokonfirmisa adresi ya email mpe ekopesa utilisateur ba tokens mpo akoki kokoma na application. Session ya `MobileSession` ekosalema mpe.

3.  **Sima ya koluka kokoma (login) na email oyo ekonfirmami te**:
    *   Soki utilisateur alingi ko `login` na email oyo ekonfirmami naino te, système ekoboya kokoma na ye.
    *   Ekopesa message ya erreur mpe `error_code: 'EMAIL_NOT_CONFIRMED'`.
    *   Code ya confirmation ya sika ekotindama automatiquement na adresi ya email ya utilisateur.

4.  **Botekami ya likambo ya securite**:
    *   Bokomi na application ezali kosalema kaka soki adresi ya email ekonfirmami na code. Tokoboya Authentification nionso liboso ya confirmation.

---

**Dernière mise à jour** : 06 juin 2026
**Version** : 1.0.0 (Phase 5 — Production near-ready)
**Auteur** : Equipe dev CNETP (Eddy Masamba et équipe)
