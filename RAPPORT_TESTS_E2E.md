# Rapport de campagne de tests E2E — Plateforme CNETP

- **Date** : 11/10/2026
- **Environnement** : local (Ubuntu, Python 3.12, Django 6.0.5, ASGI/Daphne)
- **URL publique (tunnel)** : https://saturn-worlds-ebook-mercy.trycloudflare.com
- **URL locale** : http://localhost:8000
- **Plan exécuté** : `PLAN_TESTS_E2E.md`

---

## 1. Synthèse

| Campagne | Résultat |
|---|---|
| Suite standard (`pytest`) | **86 / 86 réussis** |
| E2E API (nouveaux) | **9 / 9 réussis** |
| E2E UI Playwright (nouveaux) | **6 / 6 réussis** |
| Assistant IA ciblé (nouveaux tests unitaires) | **9 / 9 réussis** |
| Test de charge Locust | 424 req, **2,83 % d'échecs** (limite SQLite) |

Fonctionnalité majeure livrée : **assistant IA en correction ciblée « ligne / colonne »** (façon agent CLI), auparavant non implémenté côté serveur.

---

## 2. Environnement de test

- Serveur ASGI : `daphne -b 0.0.0.0 -p 8000 config.asgi:application` (HTTP + WebSocket).
- Base : **SQLite** (`db.sqlite3`, WAL activé, `timeout=30`) — PostgreSQL préparé mais non utilisé ici.
- Redis : actif (channel layer). Celery : **eager** (pas de worker requis).
- Email : `console` (les emails réels ne partent pas). DeepSeek : **activé** (appels réels pour l'IA).
- `.env` surchargé (dev uniquement, non committé) : `ALLOWED_HOSTS=*`, `CSRF_TRUSTED_ORIGINS=…trycloudflare.com,…`, `SITE_URL=<tunnel>`, `EMAIL_BACKEND=console`.

### Comptes de test
| Rôle | Email | Mot de passe | Espace |
|---|---|---|---|
| Expert | `expert1@cnetp.cd` | `Cnetp2026!` | `/app/` |
| Secrétariat technique (CTC) | `ctc1@cnetp.cd` | `Cnetp2026!` | `/ctc/` |
| Pilotage (Bureau Directoire) | `pilote1@cnetp.cd` | `Cnetp2026!` | `/pilotage/bureau-directoire/` |
| Ministre (tutelle) | `ministre1@cnetp.cd` | `Cnetp2026!` | publication JO |

### Jeu de données seedé (`python manage.py seed_e2e`)
14 utilisateurs/experts · 8 CTM + WGs · Comité de Pilotage + CTC + postes nominatifs · **17 normes**, **108 versions**, **121 messages (10 conversations expert1)**, 5 cotisations, 3 paiements, 2 réunions.

### Reproductibilité
```bash
mon_env/bin/python manage.py seed_e2e
mon_env/bin/daphne -b 0.0.0.0 -p 8000 config.asgi:application
mon_env/bin/pytest                       # 86 tests standard
mon_env/bin/pytest tests/e2e -m e2e      # 15 tests E2E (serveur live requis)
mon_env/bin/locust -f tests/load/locustfile.py --headless -u 15 -r 1 -t 120s \
    --host http://localhost:8000 --html reports/load_report.html
```

---

## 3. Tests E2E — résultats détaillés

### 3.1 API (sessions authentifiées par rôle) — 9/9 ✅
| Scénario | Vérifie | Résultat |
|---|---|---|
| `test_expert_creates_norme_and_20_versions` | Saisie + **20 éditions** → historique | ✅ |
| `test_norme_diff_and_rollback` | Diff v1↔v2 + **rollback** | ✅ |
| `test_norme_pdf_generation` | **Génération PDF** (reportlab) | ✅ |
| `test_document_upload_and_listing` | **Upload document** + listes (perso/publique) | ✅ |
| `test_messaging_10_conversations` | **10 conversations** + non-lus | ✅ |
| `test_payments_flow` | Cotisation → paiement → confirmation CTC | ✅ |
| `test_ia_targeted_advice` | **IA ciblée** : `edits[]` + `applied_text` | ✅ |
| `test_workflow_to_publication` | DRAFT→…→ADOPTED→**PUBLICATION au JO** | ✅ |
| `test_concurrent_edit_lock` | Verrou concurrent (423/409) | ✅ |

### 3.2 Interface (navigateur réel Playwright) — 6/6 ✅
| Test | Vérifie | Capture |
|---|---|---|
| `test_login_and_landing[expert]` | Connexion + atterrissage `/app/` | `reports/e2e/login_expert.png` |
| `test_login_and_landing[ctc]` | Connexion + `/ctc/` | `reports/e2e/login_ctc.png` |
| `test_login_and_landing[pilotage]` | Connexion + `/pilotage/bureau-directoire/` | `reports/e2e/login_pilotage.png` |
| `test_expert_app_renders_editor` | Éditeur SPA présent (`#ed-main-textarea`) | `reports/e2e/expert_app_editor.png` |
| `test_ctc_dashboard_renders` | Tableau de bord CTC | `reports/e2e/ctc_dashboard.png` |
| `test_pilotage_directoire_renders` | Espace Pilotage | `reports/e2e/pilotage_directoire.png` |

> Les flux lourds (20 versions, PDF, 10 conversations, paiements, publication, IA) sont exécutés via l'**API du serveur live** dans la même session authentifiée que l'UI, afin de garantir la reproductibilité (la SPA `app.html` de ~8 200 lignes est difficile à automatiser de bout en bout de façon fiable).

### 3.3 Assistant IA ciblé — 9/9 ✅
- `parse_targeted_json`, `build_edits_from_proposal`, `apply_edits` + génération via LLM mocké.
- Comportement : le serveur renvoie `{summary, edits:[{find,replace,reason,applied}], applied_text}` ; seules les lignes réellement modifiées sont ciblées.

---

## 4. Test de charge (Locust)

Configuration : 15 utilisateurs, montée 1/s, 90–120 s, contre localhost.

| Endpoint | Requêtes | Échecs | Médiane |
|---|---|---|---|
| `GET /api/v1/norms/` | 113 | 0 | 1 500 ms |
| `POST /api/v1/norms/{id}/create_version/` | 43 | **12 (27,9 %)** | 1 700 ms |
| `POST /api/v1/messages/` | 70 | 0 | 2 800 ms |
| `GET /api/v1/norms/{id}/pdf/` | 28 | 0 | 1 400 ms |
| `GET /api/v1/dashboard/kpis/kpis/` | 26 | 0 | 1 100 ms |
| `POST /se-connecter/` | 15 | 0 | **33 000 ms** |
| **Agrégé** | **424** | **12 (2,83 %)** | 1 700 ms |

Rapport HTML : `reports/load_report.html`.

---

## 5. Anomalies / enseignements

| # | Anomalie | Gravité | Statut |
|---|---|---|---|
| 1 | **`sqlite3.OperationalError: database is locked`** sur écritures concurrentes (`create_version`, login) | Élevée (env. prod) | Limite structurelle SQLite → **migration PostgreSQL** requise. `PRAGMA journal_mode=WAL` + `timeout=30` atténuent mais ne suffisent pas. |
| 2 | **Authentification très lente sous concurrence** (login médiane 33 s à 15 users) | Élevée | PBKDF2 + worker unique ASGI. Recommandé : hasher plus rapide, JWT, plusieurs workers. |
| 3 | **Course possible sur `version_number`** (`unique_together (norme, version_number)`) si deux écritures simultanées passent la barrière | Moyenne | Recommandé : `select_for_update()` sur la norme dans `create_version`. |
| 4 | **Assistant IA ciblé non implémenté** (le bouton « Appliquer » était inerte) | Corrigée | ✅ Implémenté (`targeted_edits.py` + `regulatory_advice.py` + `views.py`). |
| 5 | UI factices : upload documents & « Drive CTC » (pas de fetch) ; `generate_pv_pdf` et diagramme graphviz non branchés | Faible | Documenté. |
| 6 | `runserver` ne sert pas les WebSockets ; des `runserver` périmés occupaient `:8000` | Moyenne | Démarrer avec `daphne`. |
| 7 | Seuil de matching/limites : `Norme` exige `ctm`+`wg`; paiement create ne renvoie pas `id` (serializer) | Faible | Contournés dans les tests ; à normaliser. |

### Correctifs appliqués pendant la campagne
- **Assistant IA ciblé** (nouveau service + endpoint + tests).
- **SQLite** : WAL + `timeout` (configuration).
- **`config/settings_test.py`**, `pytest.ini` (marqueur `e2e`), `requirements-dev.txt`.

---

## 6. Recommandations

1. **Basculer en PostgreSQL** avant charge réelle (commande prête : `python manage.py migrate_to_postgres`).
2. **Sécuriser la création de version** (`select_for_update` / compteur atomique).
3. **Scaler l'authentification** (JWT côté API, hasher adapté, N workers daphne/gunicorn).
4. **Brancher les UI manquantes** (upload documents, Drive CTC, PV PDF) ou les retirer.
5. **Ajouter les tests E2E au CI** (job séparé avec serveur live + seed).

---

## 7. Livrables

| Fichier | Rôle |
|---|---|
| `RAPPORT_TESTS_E2E.md` | Ce rapport |
| `PLAN_TESTS_E2E.md` | Plan de campagne |
| `apps/core/management/commands/seed_e2e.py` | Jeu de données + comptes |
| `apps/ia_agent/services/targeted_edits.py` | Moteur de corrections ciblées IA |
| `tests/e2e/` | 15 tests E2E (API + UI) |
| `tests/test_targeted_edits.py` | 9 tests unitaires IA |
| `tests/load/locustfile.py` | Test de charge |
| `reports/e2e/*.png` | Captures navigateur |
| `reports/load_report.html` | Rapport de charge |
| `requirements-dev.txt` | Dépendances de test |
