#!/usr/bin/env bash
#
# Mise à jour sécurisée de la plateforme CNETP en PRODUCTION.
#
# Ce script ne fait AUCUNE opération destructive :
#   - refuse de tourner si des modifications locales non commitées existent
#   - avance uniquement en fast-forward (pas de merge/rébase surprise)
#   - sauvegarde la base AVANT toute migration
#   - applique les migrations (additives) et collectstatic
#
# Usage :
#   bash deploy/update_prod.sh
#
# Variables optionnelles :
#   APP_DIR       chemin du projet (défaut : racine du dépôt)
#   PYTHON        interpréteur (défaut : $APP_DIR/mon_env/bin/python sinon python)
#   BACKUP_DIR    dossier des sauvegardes (défaut : $APP_DIR/backups)
#   BRANCH        branche à déployer (défaut : main)
#   RESTART_CMD   commande de redémarrage (ex: "touch /var/www/x_wsgi.py")
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
BRANCH="${BRANCH:-main}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"

cd "$APP_DIR"

if [ -x "$APP_DIR/mon_env/bin/python" ]; then
  PYTHON="${PYTHON:-$APP_DIR/mon_env/bin/python}"
else
  PYTHON="${PYTHON:-python}"
fi

echo "==> CNETP — mise à jour production"
echo "    dossier : $APP_DIR"
echo "    python  : $PYTHON"
echo "    branche : $BRANCH"

# ── 0. Garde-fou : pas de modifications locales ────────────────────────────
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Des modifications locales non commitées existent — pull annulé pour éviter toute perte :"
  git status --short
  echo "   ➜ commit ou 'git stash' d'abord, puis relance."
  exit 1
fi

# ── 1. Sauvegarde de la base ───────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
echo "==> [1/6] Sauvegarde de la base"

DB_ENGINE_VALUE="$(grep -E '^DB_ENGINE=' "$APP_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '[:space:]' || true)"
if [ -n "$DB_ENGINE_VALUE" ] && echo "$DB_ENGINE_VALUE" | grep -qiE 'postgres'; then
  if command -v pg_dump >/dev/null 2>&1; then
    # shellcheck disable=SC1090
    set -a; . "$APP_DIR/.env"; set +a
    PGPASSWORD="${DB_PASSWORD:-}" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" \
      -U "${DB_USER:-postgres}" "${DB_NAME:-cnetp_db}" > "$BACKUP_DIR/db_${STAMP}.sql"
    echo "    -> $BACKUP_DIR/db_${STAMP}.sql (PostgreSQL)"
  else
    echo "    ⚠️  pg_dump absent — sauvegarde PostgreSQL ignorée. Installe postgresql-client."
  fi
elif [ -f "$APP_DIR/db.sqlite3" ]; then
  cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db_${STAMP}.sqlite3"
  echo "    -> $BACKUP_DIR/db_${STAMP}.sqlite3 (SQLite)"
else
  echo "    ⚠️  Aucune base détectée (ni DB_ENGINE=postgresql, ni db.sqlite3)."
fi

# ── 2. Récupération du code (fast-forward uniquement) ──────────────────────
echo "==> [2/6] git fetch + avance rapide sur origin/$BRANCH"
git fetch origin
BEFORE="$(git rev-parse --short HEAD)"
git merge --ff-only "origin/$BRANCH"
AFTER="$(git rev-parse --short HEAD)"
echo "    $BEFORE -> $AFTER"

# ── 3. Dépendances ─────────────────────────────────────────────────────────
echo "==> [3/6] Installation des dépendances"
"$PYTHON" -m pip install -r "$APP_DIR/requirements.txt"

# ── 4. Migrations ──────────────────────────────────────────────────────────
echo "==> [4/6] Migrations"
"$PYTHON" "$APP_DIR/manage.py" migrate --noinput

# ── 5. Fichiers statiques ──────────────────────────────────────────────────
echo "==> [5/6] collectstatic"
"$PYTHON" "$APP_DIR/manage.py" collectstatic --noinput

# ── 6. Redémarrage du service ──────────────────────────────────────────────
echo "==> [6/6] Redémarrage"
if [ -n "${RESTART_CMD:-}" ]; then
  eval "$RESTART_CMD"
  echo "    service redémarré"
else
  echo "    ⚠️  RESTART_CMD non défini."
  echo "       Ex : RESTART_CMD='touch /var/www/monapp_wsgi.py' bash deploy/update_prod.sh"
  echo "       Ex : RESTART_CMD='sudo systemctl restart cnetp' bash deploy/update_prod.sh"
fi

echo
echo "✅ Mise à jour terminée ($BEFORE -> $AFTER)."
echo "   Sauvegarde : $BACKUP_DIR"
