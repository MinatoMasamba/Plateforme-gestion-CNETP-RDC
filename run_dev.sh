#!/bin/bash
set -e

# Activate venv
source mon_env/bin/activate

# Create test data (admin user + expert)
echo "Creating test data..."
python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
from apps.experts.models import Expert, Structure

User = get_user_model()

# Create admin user
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print("✓ Admin user created")
else:
    admin = User.objects.get(username='admin')
    print("✓ Admin user already exists")

# Create test expert
if not Expert.objects.filter(user=admin).exists():
    structure = Structure.objects.first()
    if structure:
        Expert.objects.create(
            user=admin,
            structure=structure,
            status='ACTIVE',
            specialties='Administration, Pilotage',
        )
        print("✓ Test expert created")
    else:
        print("⚠ Aucune structure disponible — expert non créé")
else:
    print("✓ Expert already exists")

print("\nIdentifiants de test :")
print("  Username : admin")
print("  Password : admin123")
PYEOF

echo ""
echo "Démarrage du serveur Django sur http://localhost:8000 ..."
echo "Admin :   http://localhost:8000/admin/"
echo "Swagger : http://localhost:8000/api/v1/schema/swagger/"
echo ""
echo "Ctrl+C pour arrêter"
echo ""

python manage.py runserver 0.0.0.0:8000
