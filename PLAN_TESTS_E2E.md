# Plan — Campagne de tests E2E CNETP + assistant IA ciblé

> Statut : plan validé (mode build). Décisions retenues :
> 1. **Implémenter** l'assistant IA de correction ciblée (ligne/colonne) puis le tester.
> 2. Tests d'interface via **navigateur réel Playwright**.
> 3. Tunnel **cloudflared via npx**.
> 4. Charge : **dataset cible (§1) ET stress (§5)**.

---

## Constats bloquants (issus de l'exploration)

1. **Base vide** : 0 user, 0 expert, 0 CTM/WG → tout doit être seedé.
2. **Assistant IA ciblé non implémenté** : le front (`templates/app/app.html:1466`) attend `edits[]` (`find`/`replace`/`reason`/`applied_text`) mais le backend (`api/v1/ia_agent/views.py:59`) ne renvoie que `explanation`/`proposal` → bouton « Appliquer » inerte.
3. **Aucun outil de tunnel installé** (ngrok/cloudflared/localtunnel absents).
4. **`runserver` ne sert pas les WebSockets** : utiliser `daphne config.asgi:application` (Redis actif, Celery *eager*, email SMTP réel dans `.env`).
5. **UI partiellement factices** : upload de documents et « Drive CTC » = maquettes ; `generate_pv_pdf` et le diagramme graphviz non branchés.
6. **Pas de seed** pour paiements/messages → à créer par script.
7. **Concurrence** : cookies partagés par host → 3 sessions = 3 profils navigateur ou hosts distincts ; charge = JWT API.

---

## 0. Préparation & sécurité
- Sauvegarde `db.sqlite3` → `db.sqlite3.bak`.
- Overrides **dev uniquement** dans `.env` (jamais committé) : `ALLOWED_HOSTS=*`, `CSRF_TRUSTED_ORIGINS=https://<tunnel>`, `SITE_URL=https://<tunnel>`, `EMAIL_BACKEND=console`. DeepSeek/Twilio laissés tels quels (activation à la demande).
- `requirements-dev.txt` (nouveau) : `playwright`, `pytest-playwright`, `locust` — séparé des deps de prod.

## 1. Jeu de données & comptes (nouvelle commande `seed_e2e`)
`apps/core/management/commands/seed_e2e.py`, idempotent, qui :
1. Orchestre les seeds existants : `seed_official_structures`, `create_ctm_structure`, `seed_ctm_working_groups`, `init_pilotage_and_ctc`, `seed_pilotage_postes`, `seed_ctc_postes`.
2. Crée les comptes (mot de passe connu, `status='ACTIVE'`) :
   - `expert1@cnetp.cd` → **Expert `/app/`** + `Affectation` (CTM 1 / WG 1).
   - `ctc1@cnetp.cd` → `is_ctc_staff=True` + `CTCMembership(role=COORDINATOR)` → `/ctc/`.
   - `pilote1@cnetp.cd` → `PilotageMembreship(role=PRESIDENT)` → `/pilotage/bureau-directoire/`.
   - `ministre1@cnetp.cd` → `is_minister=True` (publication JO).
   - + 10 experts supplémentaires dans le **même CTM** (messagerie).
3. Crée 5 normes, 1 norme « historique » (base des 20 éditions), cotisations, 2 réunions, jetons, et 10 conversations (CRUD `Message`).
- Sortie : récap des identifiants et URLs.

## 2. Assistant IA — correction ciblée « ligne/colonne »
- **Backend** `apps/ia_agent/services/targeted_edits.py` (nouveau) : à partir du texte original et de la proposition LLM, génère un diff minimal (via `difflib.SequenceMatcher`) → liste `edits[] = {line, column/find, replace, reason}` ne ciblant **que** les lignes/cellules modifiées.
- `apps/ia_agent/services/regulatory_advice.py` : renvoyer `{summary, edits[], applied_text, provider, raw}`.
- `api/v1/ia_agent/views.py` : exposer ces champs (+ action optionnelle `apply-edits` créant une `NormeVersion` ciblée).
- **Front** `templates/app/app.html` : brancher `applyAiAdvice` sur `edits[]` (application unitaire par edit, surlignage `diff_segments` déjà géré).
- **Tests unitaires** `tests/test_targeted_edits.py` : 1 seule ligne modifiée → 1 seul edit ; insensible aux espaces ; pas de réécriture globale.

## 3. Serveur + tunnel
- `python manage.py collectstatic --noinput`.
- `daphne -b 0.0.0.0 -p 8000 config.asgi:application` (HTTP + WebSocket, Redis déjà actif).
- Tunnel : `npx --yes cloudflared tunnel --url http://localhost:8000` → reporter l'URL dans `.env` → relancer daphne.
- Processus laissés en tâche de fond ; URL publique fournie dans le rapport.

## 4. Tests E2E Playwright (vrai navigateur, 3 sessions parallèles)
- `tests/e2e/` : fixtures Playwright, 3 `browser_context` simultanés (expert / CTC / pilotage), captures dans `reports/e2e/`.
- **Expert `/app/`** : saisie manuelle + import/extraction (`.txt/.docx/.pdf`), verrouillage, **20 éditions** d'une norme existante (historique + diff + rollback, captures), vote, **génération PDF**, **upload documents** (`POST /documents/`), **messagerie 10 conversations**, module financier (paiement partiel/solde).
- **CTC `/ctc/`** : réception de dossier, méthodologie, revues (ISO/légal/éco), consultation industrielle, **confirmation des paiements**, **transmission au Pilotage**, **publication au JO** (`publish_to_jo`) → DRAFT→…→ADOPTED→PUBLISHED.
- **Pilotage `/pilotage/...`** : cadrage phase 1 & 2, réception, validation finale, verrou plateforme, console IA (`/pilotage/ia-agent/`) + artefact (email draft → approve → PDF).
- **IA éditeur** : « Analyser & optimiser » → appliquer des edits ciblés (ligne/colonne).
- **Simultané** : 2 experts éditent la même norme → vérification du **lock 423** ; en parallèle poussée de doc + PDF + messagerie.
- Intégration à `pytest.ini` : marqueur `e2e` exclu du run par défaut.

## 5. Charge / stress (Locust)
- `tests/load/locustfile.py` : login JWT par utilisateur (stateless), scénarios `login → lister normes → create_version → PDF → messages → paiements`, pondérés.
- Run headless contre **localhost** (pas le tunnel) : ex. 30 users, spawn 5/s, 2 min → export `reports/load_report.html` + stats.
- Les deux niveaux : dataset cible (§1) **et** stress (§5).

## 6. Rapport
- `RAPPORT_TESTS_E2E.md` à la racine : environnement, comptes, URL tunnel, procédure par module, résultats (OK/KO), captures (chemins), stats de charge, **anomalies/gaps** (ex. upload UI factice, `generate_pv_pdf` non branché), et correctifs appliqués.

## 7. Correctifs
- Corriger les bugs découverts au fil des tests (déjà 6 corrigés aux tours précédents) ; consigner chaque correction dans le rapport.

---

## Livrables
- `RAPPORT_TESTS_E2E.md`, `reports/e2e/*` (captures), `reports/load_report.html`.
- Nouveaux fichiers : `seed_e2e.py`, `targeted_edits.py`, `requirements-dev.txt`, `tests/e2e/*`, `tests/load/locustfile.py`, `scripts/run_e2e.sh`.
- Modifs : `regulatory_advice.py`, `api/v1/ia_agent/views.py`, `templates/app/app.html`, `pytest.ini`, `.env` (local).

## Risques / replis
- **cloudflared** : téléchargement du binaire bloqué possible → repli `ssh -R 80:localhost:8000 nokey@localhost.run`.
- **Playwright** : `playwright install-deps` peut exiger `sudo`/apt ; sinon `--with-deps`.
- Serveur **sans display** → Playwright headless + captures ; **URL publique** fournie pour observer les 3 instances en direct.
- **DeepSeek** : coût/appels réels pour les tests IA (limiter le nombre d'appels).
- Overrides `.env` réversibles et non committés.
