#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    
    # Verificar se o usuário já existe
    if User.objects.filter(email='bruno@move.com').exists():
        user = User.objects.get(email='bruno@move.com')
        print(f"ℹ️  Usuário já existe!")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"É superusuário: {user.is_superuser}")
        print(f"É staff: {user.is_staff}")
        return user
    
    # Criar novo superusuário
    try:
        user = User.objects.create_superuser(
            username='bruno',
            email='bruno@move.com',
            password='15002031'
        )
        print("✅ Superusuário criado com sucesso!")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"É superusuário: {user.is_superuser}")
        print(f"É staff: {user.is_staff}")
        return user
    except Exception as e:
        print(f"❌ Erro ao criar superusuário: {e}")
        return None

if __name__ == '__main__':
    create_superuser()
