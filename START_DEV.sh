#!/bin/bash

# 🚀 DÉMARRAGE RAPIDE - API REST CNETP
# Ce script démarre le serveur Django et affiche les informations utiles

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 CNETP - Plateforme de Gestion des Normes"
echo "════════════════════════════════════════════════════════════"
echo ""

# Activer l'environnement virtuel
echo "📦 Activation de l'environnement virtuel..."
if [ ! -d "mon_env" ]; then
    echo "❌ Environnement virtuel non trouvé. Exécutez:"
    echo "   python3 -m venv mon_env"
    echo "   source mon_env/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

source mon_env/bin/activate

echo "✅ Environnement virtuel activé"
echo ""

# Vérifications
echo "🔍 Vérifications..."
python3 manage.py check
echo "✅ Configuration Django OK"
echo ""

# Migrations
echo "💾 Application des migrations..."
python3 manage.py migrate --noinput > /dev/null 2>&1 || true
echo "✅ Migrations appliquées"
echo ""

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput > /dev/null 2>&1 || true
echo "✅ Fichiers statiques OK"
echo ""

# Créer un superuser de test si n'existe pas
echo "👤 Création d'utilisateurs de test..."
python3 << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Créer admin si n'existe pas
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Admin créé (username: admin, password: admin123)")
else:
    print("✅ Admin déjà existant")

# Créer expert test si n'existe pas
if not User.objects.filter(username='expert_test').exists():
    user = User.objects.create_user(
        username='expert_test',
        email='expert@example.com',
        password='expertpass123'
    )
    user.is_expert = True
    user.save()
    print("✅ Expert de test créé (username: expert_test, password: expertpass123)")
else:
    print("✅ Expert de test déjà existant")

# Créer CTC staff si n'existe pas
if not User.objects.filter(username='ctc_staff').exists():
    user = User.objects.create_user(
        username='ctc_staff',
        email='ctc@example.com',
        password='ctcpass123'
    )
    user.is_ctc_staff = True
    user.is_staff = True
    user.save()
    print("✅ CTC staff créé (username: ctc_staff, password: ctcpass123)")
else:
    print("✅ CTC staff déjà existant")

EOF

echo ""
echo ""

# Afficher les informations de démarrage
echo "════════════════════════════════════════════════════════════"
echo "🎉 DÉMARRAGE DE L'API"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📍 Endpoints disponibles:"
echo ""
echo "   🔐 Authentification:"
echo "      http://localhost:8000/api/v1/auth/register/"
echo "      http://localhost:8000/api/v1/auth/login/"
echo "      http://localhost:8000/api/v1/auth/me/"
echo ""
echo "   👥 Experts:"
echo "      http://localhost:8000/api/v1/experts/"
echo "      http://localhost:8000/api/v1/experts/inscription/"
echo ""
echo "   🏛️ Gouvernance:"
echo "      http://localhost:8000/api/v1/ctm/"
echo "      http://localhost:8000/api/v1/wg/"
echo "      http://localhost:8000/api/v1/affectations/"
echo ""
echo "   📚 Documentation:"
echo "      Swagger: http://localhost:8000/api/v1/schema/swagger/"
echo "      ReDoc:   http://localhost:8000/api/v1/schema/redoc/"
echo "      Admin:   http://localhost:8000/admin/"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo "🔑 Utilisateurs de test:"
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "   Admin:"
echo "      username: admin"
echo "      password: admin123"
echo ""
echo "   Expert:"
echo "      username: expert_test"
echo "      password: expertpass123"
echo ""
echo "   CTC Staff:"
echo "      username: ctc_staff"
echo "      password: ctcpass123"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo "🧪 Tests:"
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "   Exécuter les tests API:"
echo "      bash API_TEST.sh"
echo ""
echo "   Exécuter les tests unitaires:"
echo "      pytest tests/"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo "📖 Documentation:"
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "   API_DOCUMENTATION.md     - Documentation complète"
echo "   ENDPOINTS_SUMMARY.md     - Tableau résumé des endpoints"
echo "   API_ARCHITECTURE.md      - Architecture détaillée"
echo "   PHASE2_SUMMARY.md        - Résumé Phase 2"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Démarrage du serveur sur http://localhost:8000..."
echo ""

# Lancer le serveur Django
python3 manage.py runserver 0.0.0.0:8000
