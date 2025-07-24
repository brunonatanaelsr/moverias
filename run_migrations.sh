#!/bin/bash
cd /workspaces/move
source .venv/bin/activate
echo "Ambiente virtual ativado"
which python
echo "Criando migrações..."
python manage.py makemigrations
echo "Aplicando migrações..."
python manage.py migrate
echo "Criando superusuário se necessário..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell
