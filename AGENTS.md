# AGENTS.md

## Structure du projet
- Django 6.0.5 + DRF + Channels/Daphne. SQLite est la base par défaut (WAL + IMMEDIATE) ; mettre `DB_ENGINE=postgresql` pour PostgreSQL. Redis est facultatif : sans `CELERY_BROKER_URL`, Celery s'exécute en mode eager et Channels utilise une couche en mémoire.
- `apps/<domain>/` contient les modèles, services métier et migrations. Les `apps/*/views.py` sont des stubs vides sauf `apps/dashboard` et `apps/gemini_drafts` ; les vrais endpoints REST sont dans `api/v1/<domain>/` (routeurs dans `api/v1/urls.py`).
- `api/v2/` est uniquement l'API Phoenix d'organisation, pas une version plus récente de l'API mobile. Flutter utilise `/api/v1/mobile/...`.
- `web/` est un simple package Python, absent de `INSTALLED_APPS`. Ses routes sont incluses depuis `config/urls.py` ; les templates/static partagés sont dans `templates/` et `templates/static/` à la racine.
- Surfaces UI : pages publiques/auth dans `templates/` ; SPA expert `/app/` dans `templates/app/app.html` (environ 7,5k lignes de JS inline) + `templates/static/js/components/` ; CTC/Pilotage/dashboard dans `templates/ctc/`, `templates/pilotage/`, `apps/dashboard/` ; clone Flutter dans `flutter_app/`.
- Aucune étape de build Node n'est nécessaire. Tailwind est chargé au runtime (`templates/static/vendor/tailwindcss.js` ; `/app/` utilise le CDN public) et `build_tailwind/` est vestigial. `templates/static/` est la source partagée ; `web/static/dist/` est un ancien build React suivi par git mais fournit encore les fichiers/icônes PWA ; `staticfiles/` est la sortie de collectstatic.
- `react_docs/`, `templates/index_old_react.html`, `docs/PLATFORM_DOCUMENTATION.md` et `docs/AUTH_FLOW.md` décrivent le front React/Vite supprimé (`frontend/src/...`) ; ne pas les utiliser comme cartographie actuelle.
- Phoenix (`apps/governance/phoenix_*`, `web/phoenix_views.py`, `api/v2/`) est un moteur de workflow distinct du circuit historique `Norme.circuit_version=LEGACY`. Ne pas faire passer les changements Phoenix par les services CTC/Pilotage historiques. Les écritures v2 exigent `mandate` + `revision` ; une révision obsolète renvoie 409. Les pièces Phoenix sont stockées dans le privé `.phoenix_documents`, pas dans `media/` public.
- L'app Flutter est un clone en cours : vérifier ce qui est réellement branché avant de supposer une parité web/Flutter (voir `AUDIT_PARITE_UI_UX.md` et `docs/PLAN_PARITE_EDITEUR_FLUTTER.md`).

## Exécution et installation (Windows PowerShell)
- Utiliser `.\mon_env\Scripts\python.exe` ; les chemins `mon_env/bin/...` de la doc sont pour Linux.
- Le `mon_env` existant est Python 3.11 + Django 5.2.18, alors que `requirements.txt` épingle Django 6.0.5 et que la CI utilise Python 3.12. Ne pas installer `requirements.txt` tel quel dans 3.11 ; utiliser un environnement 3.12 pour la parité quand on touche au code sensible à la version de Django.
- La CI installe `requirements.txt` ; `requirements-dev.txt` ajoute Playwright et Locust (`-r requirements.txt`).
- `.env` est chargé depuis la racine par python-decouple et n'est pas commité. Sans lui, `DEBUG=False` ; mettre `DEBUG=True` pour le `runserver` local, ou lancer `collectstatic` et compter sur WhiteNoise.
- `.\mon_env\Scripts\python.exe manage.py migrate`
- `.\mon_env\Scripts\python.exe manage.py seed_e2e` (idempotent ; crée `expert1@cnetp.cd`, `ctc1@cnetp.cd`, `pilote1@cnetp.cd`, `ministre1@cnetp.cd`, mot de passe `Cnetp2026!`).
- Dev web : `.\mon_env\Scripts\python.exe manage.py runserver 127.0.0.1:1111` (correspond au port API par défaut de Flutter).
- Live/WebSockets : `.\mon_env\Scripts\python.exe manage.py collectstatic --noinput`, puis `.\mon_env\Scripts\daphne.exe -b 0.0.0.0 -p 8000 config.asgi:application`. `runserver` ne sert pas les WebSockets Channels.
- Docker : `docker compose up --build` exige un `.env` à la racine (`env_file: .env`) ; lance Postgres + Redis + Daphne + Celery.
- Flutter : `cd flutter_app` ; `flutter run -d chrome --web-port 8082` ; l'API par défaut est `http://127.0.0.1:1111`, à surcharger avec `--dart-define=API_BASE_URL=http://127.0.0.1:8000`.

## Tests et vérifications
- Suite standard : `.\mon_env\Scripts\python.exe -m pytest` (utilise `config.settings_test` ; collecte `tests/` et `apps/` ; e2e exclu par `pytest.ini`). Utiliser pytest, pas `manage.py test`. Test unique : `... -m pytest tests/test_phoenix.py::TestClass::test_name -q`.
- E2E : seed, lancer Daphne sur 8000, puis `... -m pytest tests/e2e -m e2e`. Ces tests tapent le serveur live et modifient la vraie base locale ; `E2E_BASE_URL` permet de changer l'URL. La CI ne lance ni e2e ni Flutter.
- Ordre CI : `python manage.py check` -> `ruff check .` -> `pytest -q`. `ruff` n'est pas dans `requirements*.txt` ; l'installer séparément. `ruff.toml` ne sélectionne que les vraies erreurs, pas le formatage.
- Après un changement de modèle, lancer `manage.py makemigrations --check --dry-run` ; la CI ne détecte pas les migrations manquantes. Créer les migrations dans l'app propriétaire ; ne jamais réinitialiser ou écraser l'historique existant.
- Les réglages de test désactivent email/FCM/Twilio/DeepSeek/Redis/Celery ; ne pas écrire de tests qui dépendent de ces services. SQLite se verrouille en écriture concurrente ; utiliser PostgreSQL pour la concurrence/charge.
- Flutter : `flutter analyze` et `flutter test` ; les tests mockent Dio et n'ont pas besoin du backend. `flutter analyze` signale actuellement 2 warnings préexistants de symboles inutilisés dans `expert_financial_tab.dart`.
- Les scripts Playwright de `scripts/` codent en dur les ports (web 1111/8001, Flutter 8082) et le canal Chrome ; installer les navigateurs avec `playwright install chromium`. Tests/captures écrivent dans `reports/`.
- Charge : `... locust.exe -f tests/load/locustfile.py --headless -u 15 -r 1 -t 120s --host http://localhost:8000 --html reports/load_report.html` (nécessite `requirements-dev.txt`).

## Conventions et pièges
- Garder les textes utilisateur, routes et libellés métier en français ; conserver les termes CTM, WG/GT, SC, CTC, Copil, Phoenix, NCD et JO. Palette officielle : `#0095c9`, `#fff24b`, `#db3832` ; tokens partagés dans `templates/static/css/institutional-ui.css`.
- Auth : session + CSRF pour les pages Django, JWT pour le mobile. `AUTH_USER_MODEL=core.User` ; flags de rôle `is_expert`, `is_ctc_staff`, `is_minister`, plus les adhésions de gouvernance. Les POST de session scriptés ont besoin de `X-CSRFToken` ; les tests ajoutent aussi `Referer`, sinon 403.
- Ne jamais éditer `staticfiles/` à la main. Ne pas supprimer `web/static/dist/` (le manifeste/SW/icônes PWA y sont encore résolus) ; ne pas éditer son ancien bundle `assets/index-*`.
- `templates/app/app.html` est énorme ; faire des recherches grep/select au lieu de le lire en entier.
- `/app/` charge Tailwind et Lucide depuis des CDN publics ; les exécutions UI/captures hors ligne seront non stylées si le réseau est absent.
- Déploiement : `deploy/update_prod.sh` est un script bash/Linux, refuse un worktree sale, avance `main` en fast-forward, sauvegarde la base, migre, lance collectstatic et nécessite `RESTART_CMD`.
