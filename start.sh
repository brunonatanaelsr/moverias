#!/bin/bash
# Script simples para iniciar o servidor MoveMarias

echo "=== MoveMarias - Iniciando Servidor ==="

# Verificar se o banco existe
if [ ! -f "db.sqlite3" ]; then
    echo "Criando banco de dados..."
    ./venv/bin/python manage.py migrate
    echo "Criando usuário administrador..."
    ./venv/bin/python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@movemarias.org', 'admin@movemarias.org', 'admin123') if not User.objects.filter(email='admin@movemarias.org').exists() else print('Admin user already exists')"
fi

# Verificar se o sistema está funcionando
echo "Verificando sistema..."
./venv/bin/python manage.py check

# Iniciar servidor
echo "Iniciando servidor Django..."
echo "Acesse: http://127.0.0.1:8000/dashboard/"
echo "Admin: http://127.0.0.1:8000/admin/"
echo "Login: admin@movemarias.org / admin123"
echo ""
./venv/bin/python manage.py runserver
