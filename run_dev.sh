#!/bin/bash
set -e

# Activate venv
source mon_env/bin/activate

# Create test data (admin user)
echo "Creating test data..."
python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
from apps.experts.models import Expert
from apps.documents.models import DocumentFile
import os

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
    expert = Expert.objects.create(
        user=admin,
        role='Expert',
        phone='+243999999999',
        is_active=True
    )
    print("✓ Test expert created")
else:
    expert = Expert.objects.get(user=admin)
    print("✓ Expert already exists")

print("\nTest credentials:")
print("Username: admin")
print("Password: admin123")
PYEOF

echo ""
echo "🚀 Starting Django backend on port 8000..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Wait for Django to start
sleep 3

cd frontend
echo "🚀 Starting Vite frontend on port 5173..."
npm run dev &
VITE_PID=$!

echo ""
echo "✅ Servers started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   Swagger:  http://localhost:8000/api/v1/schema/swagger/"
echo ""
echo "Press Ctrl+C to stop"

# Wait for both processes
wait $DJANGO_PID $VITE_PID
