# ⚡ QUICKSTART - CNETP Platform Django

## ✅ Statut Actuel

**Phase 1 : Fondations** ✅ COMPLÉTÉE

### Ce qui a été fait :

1. **✅ Structure Django modulaire**
   - 9 applications Django : `core`, `experts`, `governance`, `norms`, `amendments`, `meetings`, `payments`, `validation`, `public`
   - Configuration centralisée dans `config/settings.py`
   - Support PostgreSQL (production) et SQLite (dev)

2. **✅ Modèles de données complets**
   - `core/models.py` : User custom + AuditLog
   - `experts/models.py` : Expert, Structure (16 structures)
   - `governance/models.py` : CTM (8), WG (24), Affectation, ComitePilotage
   - `norms/models.py` : Norme, NormeVersion, ChangementVersion
   - Migrations créées et testées ✓

3. **✅ Infrastructure DevOps**
   - `docker-compose.yml` : PostgreSQL + Redis + Django + Celery
   - `Dockerfile` : Image de production
   - `requirements.txt` : Dépendances Python
   - `.env.example` : Configuration d'environnement

4. **✅ Framework de test**
   - `pytest.ini` : Configuration pytest
   - `tests/conftest.py` : Fixtures et factories
   - `tests/test_models.py` : Tests de base (validation modèles)

5. **✅ Documentation**
   - `README.md` : Guide complet
   - Plans architecture détaillés
   - Commentaires de code

---

## 🚀 Démarrage Rapide

### Option 1 : Installation locale (SQLite)
```bash
cd /home/minato/projet
source mon_env/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Accès : http://localhost:8000/admin (identifiants : admin/admin123)

### Option 2 : Docker Compose (PostgreSQL + Redis)
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
# Accès : http://localhost:8000
```

---

## 📊 État des Modèles

| Modèle | Status | Notes |
|--------|--------|-------|
| User (custom) | ✅ READY | Avec champs CNETP (expert, ctc_staff, minister) |
| AuditLog | ✅ READY | Traçabilité complète |
| Structure | ✅ READY | 16 structures d'origine |
| Expert | ✅ READY | 200 experts + infos bancaires |
| CTM | ✅ READY | 8 Comités Techniques Miroir |
| WG | ✅ READY | 24 Groupes de Travail |
| Affectation | ✅ READY | Expert → CTM/WG |
| ComitePilotage | ✅ READY | 24 membres comité stratégique |
| Norme | ✅ READY | Projet de norme + statuts |
| NormeVersion | ✅ READY | Historique complet versions |
| ChangementVersion | ✅ READY | Suivi détaillé modifications |

## ⏳ À Faire (Phase 2-5)

### Phase 2 : API REST (PROCHAINE)
- [ ] Serializers pour tous les modèles
- [ ] ViewSets & DRF routers
- [ ] Permissions personnalisées (IsExpert, IsCTCCoordinator, etc.)
- [ ] Filtrage & recherche full-text
- [ ] Documentation OpenAPI/Swagger

### Phase 3 : Web Templates
- [ ] Base templates + Bootstrap 5
- [ ] Inscription experts (formulaires)
- [ ] Tableau de bord expert
- [ ] Éditeur collaboratif normes
- [ ] Interface de vote électronique

### Phase 4 : Modules Avancés
- [ ] Système de vote (Amendement + Vote models)
- [ ] Gestion paiements (Cotisation + JetonPresence)
- [ ] Workflow validation CTC (EtapeValidation state machine)
- [ ] Génération PDF (normes + procès-verbaux)
- [ ] Réunions & présences

### Phase 5 : Production
- [ ] Tests d'intégration complets
- [ ] Optimisations performance
- [ ] Déploiement production
- [ ] Formation utilisateurs

---

## 📂 Structure Fichiers Clés

```
cnetp_project/
├── config/
│   ├── settings.py          ← Configuration Django (BASE)
│   ├── urls.py              ← Routing principal
│   └── celery.py            ← Config Celery
│
├── apps/
│   ├── core/models.py       ← User + AuditLog
│   ├── experts/models.py    ← Expert + Structure
│   ├── governance/models.py ← CTM + WG
│   ├── norms/models.py      ← Norme + Versions
│   ├── amendments/          ← À implémenter
│   ├── meetings/            ← À implémenter
│   ├── payments/            ← À implémenter
│   ├── validation/          ← À implémenter
│   └── public/              ← À implémenter
│
├── api/v1/
│   ├── pagination.py        ← Pagination DRF
│   ├── permissions.py       ← Permissions custom (à créer)
│   ├── urls.py              ← Routes API (à créer)
│   └── serializers/         ← Serializers (à créer)
│
├── web/
│   ├── templates/           ← HTML templates (à créer)
│   └── static/              ← CSS, JS (à créer)
│
├── tests/
│   ├── conftest.py          ← Pytest fixtures
│   ├── test_models.py       ← Tests modèles de base
│   └── test_*/              ← Tests par app (à créer)
│
├── manage.py                ← CLI Django
├── requirements.txt         ← Dépendances Python
├── docker-compose.yml       ← Infrastructure conteneurs
├── Dockerfile               ← Image Docker
├── pytest.ini               ← Config pytest
├── README.md                ← Documentation complète
└── .env.example             ← Template variables d'env
```

---

## 🔧 Commandes Essentielles

```bash
# Migration de la BD
python manage.py makemigrations
python manage.py migrate

# Créer superutilisateur
python manage.py createsuperuser

# Accéder à Django shell
python manage.py shell_plus

# Lancer tests
pytest tests/
pytest tests/test_models.py -v

# Linter & formatter
black .
flake8 .
isort .

# Dump données pour backup
python manage.py dumpdata > backup.json

# Charger données
python manage.py loaddata backup.json

# Serveur de développement
python manage.py runserver

# Collecter assets statiques (pour production)
python manage.py collectstatic --noinput
```

---

## 🔐 Sécurité & Configuration

### Variables d'environnement (.env)
```
SECRET_KEY=votre-clé-secrète-ici
DEBUG=False  # Pour production
DB_NAME=cnetp_db
DB_USER=cnetp_user
DB_PASSWORD=secure_password
DB_HOST=localhost
REDIS_URL=redis://localhost:6379/1
```

### Comptes par défaut (DEV ONLY)
- Admin : `admin` / `admin123`
- À changer en production !

---

## 📞 Prochaines Étapes

1. **Immédiat** : Créer API serializers & viewsets
   ```bash
   # apps/experts/serializers.py
   # apps/experts/views.py
   # api/v1/urls.py
   ```

2. **Court terme** : Templates web
   ```bash
   # web/templates/base.html
   # web/templates/experts/
   # web/templates/norms/
   ```

3. **Moyen terme** : Systèmes avancés (votes, paiements)

4. **Long terme** : Production & déploiement

---

## 📚 Ressources

- **Django Docs** : https://docs.djangoproject.com/en/4.2/
- **DRF** : https://www.django-rest-framework.org/
- **PostgreSQL** : https://www.postgresql.org/docs/
- **Redis** : https://redis.io/docs/
- **Docker** : https://docs.docker.com/

---

**Last Updated** : 19 mai 2026 - 04:10 UTC+2
**Maintainers** : Équipe Développement CNETP
