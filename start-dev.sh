#!/bin/bash
# Lance l'environnement de dev CNETP : Redis + Daphne (ASGI + WebSockets)

cd "$(dirname "$0")"
source mon_env/bin/activate

# ── Redis ──────────────────────────────────────────────────────────────────
if ! redis-cli ping &>/dev/null; then
    echo "Redis absent — démarrage..."
    sudo systemctl start redis-server 2>/dev/null || redis-server --daemonize yes
fi
echo "Redis OK"

# ── Port 8000 ──────────────────────────────────────────────────────────────
PID=$(lsof -t -i:8000 2>/dev/null)
[ -n "$PID" ] && kill "$PID" && echo "Ancien serveur tué (PID $PID)"

# ── Migrations ─────────────────────────────────────────────────────────────
python manage.py migrate --noinput

# ── Daphne (ASGI) ──────────────────────────────────────────────────────────
echo ""
echo "Serveur sur http://localhost:8000"
echo "Ctrl+C pour arrêter"
echo ""
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
