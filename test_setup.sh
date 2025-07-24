#!/bin/bash
cd /workspaces/move
source .venv/bin/activate

echo "=== Verificando ambiente ==="
which python
python --version

echo "=== Testando Django setup ==="
python -c "import django; print('Django version:', django.get_version())"

echo "=== Testando imports ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()
print('Django setup: OK')

from core.models import FileUpload
print('FileUpload import: OK')

from users.models import UserProfile
print('UserProfile import: OK')
"

echo "=== Executando check ==="
python manage.py check
