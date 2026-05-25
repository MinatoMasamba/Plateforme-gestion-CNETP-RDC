#!/bin/bash
# Démarrage de l'application intégrée Django + React

set -e

echo "🚀 Démarrage de l'application CNETP (Django + React Hybride)"
echo "=================================================="

# Configuration
PROJECT_DIR="/home/minato/project"
VENV_PYTHON="$PROJECT_DIR/mon_env/bin/python"

# Vérifier que le frontend est compilé
if [ ! -d "$PROJECT_DIR/web/static/dist" ]; then
    echo "❌ Erreur: Frontend non compilé!"
    echo "   Exécutez d'abord:"
    echo "   cd $PROJECT_DIR/frontend && npm run build"
    exit 1
fi

echo "✅ Frontend compilé trouvé"
echo ""
echo "🔧 Démarrage de Django sur http://127.0.0.1:8000"
echo "   - App: http://127.0.0.1:8000/"
echo "   - Admin: http://127.0.0.1:8000/admin/"
echo "   - Appuyez sur CTRL+C pour arrêter"
echo ""

# Démarrer Django
cd "$PROJECT_DIR"

if [ -x "$VENV_PYTHON" ]; then
    $VENV_PYTHON manage.py runserver 0.0.0.0:8000
else
    python manage.py runserver 0.0.0.0:8000
fi
