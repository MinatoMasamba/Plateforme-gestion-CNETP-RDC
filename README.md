# PLATEFORME CNETP - Gestion des Activités de la Commission Nationale pour l'Élaboration des Normes de Construction

## 🎯 Aperçu du Projet

Plateforme web complète pour gérer l'ensemble des activités de la **Commission Nationale pour l'Élaboration des Normes de Construction des Infrastructures et des Travaux Publics (CNETP)** en République Démocratique du Congo.

### Fonctionnalités principales
- ✅ Inscription et gestion de 200 experts
- ✅ Organisation en 8 Comités Techniques Miroir (CTM) et 24 Groupes de Travail (WG)
- ✅ Élaboration collaborative de normes
- ✅ Système de vote électronique
- ✅ Gestion des cotisations (structures) et jetons (experts)
- ✅ Workflow de validation multi-étapes
- ✅ Publication et consultation publique des normes

---

## 🏗️ Architecture Technique

### Stack Utilisé
- **Backend** : Django 4.2 + Django REST Framework
- **Frontend Web** : Django Templates + Bootstrap 5
- **Base de Données** : PostgreSQL (production) / SQLite (développement)
- **Cache/Async** : Redis + Celery
- **Documentation API** : drf-spectacular (OpenAPI 3.0)

### Structure du Projet
```
cnetp_project/
├── config/              # Configurations Django centrales
├── apps/                # Applications réutilisables
│   ├── core/           # User model + audit logging
│   ├── experts/        # Experts & structures
│   ├── governance/     # CTM, WG, Comités
│   ├── norms/          # Normes & versions
│   ├── amendments/     # Amendements & votes
│   ├── meetings/       # Réunions & PV
│   ├── payments/       # Cotisations & jetons
│   ├── validation/     # Workflow CTC
│   └── public/         # Consultation publique
├── api/v1/             # API REST layer
├── web/                # Frontend templates & static
├── tests/              # Tests unitaires & intégration
└── docs/               # Documentation
```

---

## 🚀 Installation & Démarrage Rapide

### Prérequis
- Python 3.12+
- PostgreSQL 13+ (production)
- Redis (pour async tasks)
- Git

### 1. Clone et configuration
```bash
git clone <repo>
cd cnetp_project
python -m venv mon_env
source mon_env/bin/activate  # Windows: mon_env\Scripts\activate
```

### 2. Installation dépendances
```bash
pip install -r requirements.txt
```

### 3. Variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 4. Base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Lancer le serveur
```bash
python manage.py runserver
```

Accédez à :
- **Admin Django** : http://localhost:8000/admin
- **API Swagger** : http://localhost:8000/api/v1/schema/swagger-ui/

---

## 🐳 Déploiement avec Docker Compose

### Démarrage
```bash
docker-compose up -d
```

Services :
- **PostgreSQL** : localhost:5432
- **Redis** : localhost:6379
- **Django** : localhost:8000
- **Celery Worker** : Actif en arrière-plan
- **Celery Beat** : Scheduler pour tâches programmées

### Arrêt
```bash
docker-compose down
```

---

## 📊 Modèles de Données (Vue d'ensemble)

### Core
- **User** (custom) : Avec champs CNETP (expert, ctc_staff, minister)
- **AuditLog** : Traçabilité complète des actions

### Experts & Gouvernance
- **Expert** : Les 200 experts + infos bancaires
- **Structure** : Les 16 structures d'origine
- **CTM** : Les 8 Comités Techniques Miroir
- **WG** : Les 24 Groupes de Travail
- **Affectation** : Lien expert → CTM/WG
- **ComitePilotage** : Pilotage stratégique (24 membres)

### Normes
- **Norme** : Projet de norme avec statuts (DRAFT → PUBLISHED)
- **NormeVersion** : Historique complet des versions
- **ChangementVersion** : Suivi détaillé par section

### (À implémenter - Phase 3-5)
- **Amendement** : Propositions de modification
- **Vote** : Système de vote électronique
- **Reunion** : Réunions CTM & Assemblée plénière
- **Cotisation** : Cotisations structures
- **JetonPresence** : Paiements experts
- **EtapeValidation** : Workflow CTC

---

## 🔐 Authentification & Permissions

### Types d'utilisateurs
1. **Utilisateur public** : Consultation normes (sans authentification)
2. **Expert** : Vote, élaboration collaborative
3. **Responsable WG/CTM** : Animation groupes
4. **CTC Coordinator** : Validation workflow, gestion paiements
5. **Ministre** : Homologation normes

### Permissions API
- `IsAuthenticated` : Authentifié
- `IsExpert` : Expert inscrit
- `IsExpertOfCTM` : Expert du CTM X
- `IsCTCCoordinator` : Coordinateur CTC
- `IsMinister` : Ministre
- `IsPublic` : Pas d'authentification

---

## 📝 API REST Endpoints

### Authentication
```
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
```

### Experts
```
GET    /api/v1/experts/
POST   /api/v1/experts/                 # Inscription
GET    /api/v1/experts/{id}/
PATCH  /api/v1/experts/{id}/
GET    /api/v1/structures/
```

### Governance (À implémenter)
```
GET    /api/v1/ctm/
GET    /api/v1/ctm/{id}/wg/
GET    /api/v1/affectations/
```

### Normes (À implémenter)
```
GET    /api/v1/normes/
POST   /api/v1/normes/
GET    /api/v1/normes/{id}/versions/
POST   /api/v1/normes/{id}/versions/    # Nouvelle version
```

Documentation complète : http://localhost:8000/api/v1/schema/swagger-ui/

---

## ✅ État du Projet

### Phase 1 : ✅ Fondations (COMPLÉTÉE)
- [x] Configuration Django + apps modulaires
- [x] Modèles Core (User, AuditLog)
- [x] Modèles Experts & Structures
- [x] Modèles Governance (CTM, WG, Affectations)
- [x] Modèles Normes & Versions
- [x] Migrations & Base de données
- [x] Docker Compose setup

### Phase 2 : ⏳ API & Serializers (EN COURS)
- [ ] Serializers pour tous les modèles
- [ ] ViewSets & Routers API
- [ ] Permissions personnalisées
- [ ] Filtrage & recherche

### Phase 3 : ⏳ Web Templates
- [ ] Base templates + layout
- [ ] Inscription experts
- [ ] Tableau de bord expert
- [ ] Éditeur collaboratif normes

### Phase 4 : ⏳ Modules Avancés
- [ ] Système de vote électronique
- [ ] Gestion paiements (cotisations + jetons)
- [ ] Workflow validation CTC
- [ ] Génération PDF (normes + PV)

### Phase 5 : ⏳ Production & Tests
- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Optimisations performance
- [ ] Documentation utilisateur
- [ ] Déploiement production

---

## 📚 Documentation Complémentaire

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** : Détails architecture modulaire
- **[MODELS.md](docs/MODELS.md)** : Schéma données complet
- **[API.md](docs/API.md)** : Endpoints API detaillés
- **[INSTALL.md](docs/INSTALLATION.md)** : Installation avancée
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** : Guide utilisateur (EN COURS)

---

## 🛠️ Développement

### Commandes utiles
```bash
# Créer une migration
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Créer superutilisateur
python manage.py createsuperuser

# Lancer tests
pytest tests/

# Linter + formatter
black .
flake8 .
isort .

# Shell Django
python manage.py shell_plus

# Dump données
python manage.py dumpdata > data.json

# Load données
python manage.py loaddata data.json
```

### Ajouter une nouvelle feature
1. **Créer le modèle** dans `apps/module/models.py`
2. **Créer migrations** : `python manage.py makemigrations`
3. **Créer serializer** dans `apps/module/serializers.py`
4. **Créer ViewSet** dans `apps/module/views.py`
5. **Ajouter routes** dans `apps/module/urls.py`
6. **Enregistrer dans admin** : `apps/module/admin.py`
7. **Écrire tests** dans `tests/test_module/`

---

## 👥 Contributeurs

- **Développement** : Équipe Backend Django
- **Architecture** : Conception modulaire CNETP

---

## 📄 Licence

Propriété exclusive de l'État Congolais / Ministère ITP

---

## 📞 Support

Pour questions ou issues :
- 📧 Email : support@cnetp.cd
- 📱 Tél : +243 8X XXX XXXX
- 🐛 Issues : [GitHub Issues](https://github.com/cnetp/cnetp-platform/issues)

---

**Last Updated** : 19 mai 2026
**Version** : 0.1.0 (Phase Fondations)
# Plateforme-gestion-CNETP-RDC
# Plateforme-gestion-CNETP-RDC
# Plateforme-gestion-CNETP-RDC
