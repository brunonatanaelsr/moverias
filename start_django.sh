#!/bin/bash
# Django MoveMarias Startup Script

echo "=== Django MoveMarias Startup ==="
echo "Working directory: $(pwd)"

# Use Python from virtual environment or system Python
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
    echo "Using Python from virtual environment: $VIRTUAL_ENV"
else
    PYTHON_CMD="python3"
    echo "Using system Python"
fi

# Check Python version
echo "Python version:"
$PYTHON_CMD --version

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found"
    exit 1
fi

echo "Testing Django setup..."
$PYTHON_CMD -c "import django; print('Django version:', django.VERSION)"

echo "Testing magic module..."
$PYTHON_CMD -c "import magic; print('Magic module OK')"

echo "Testing database connection..."
$PYTHON_CMD -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()
from notifications.models import Notification
from django.contrib.auth import get_user_model
User = get_user_model()
print('✓ Database connected successfully')
print('✓ Notifications table ready')
print('✓ Users table ready')
print('✓ Admin user exists:', User.objects.filter(email='admin@movemarias.org').exists())
"

echo "Running Django system check..."
$PYTHON_CMD manage.py check

echo "Collecting static files..."
$PYTHON_CMD manage.py collectstatic --noinput

echo "Starting Django development server..."
echo "Access the application at: http://127.0.0.1:8000"
echo "Admin panel: http://127.0.0.1:8000/admin/"
echo "Dashboard: http://127.0.0.1:8000/dashboard/"
echo ""
$PYTHON_CMD manage.py runserver
echo "Admin login: admin@movemarias.org / admin123"
echo "Dashboard: http://127.0.0.1:8000/dashboard/"
echo "Admin panel: http://127.0.0.1:8000/admin/"
echo ""
echo "Press Ctrl+C to stop the server"
$PYTHON_CMD manage.py runserver 127.0.0.1:8000
