#!/usr/bin/env python
"""
Script para criar superusuário automaticamente
Move Marias v2.0.0
Email: bruno@move.com
Senha: 15002031
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    """Criar superusuário Bruno se não existir"""
    
    # Primeiro, verificar se as migrações estão aplicadas
    from django.core.management import execute_from_command_line
    
    try:
        print("🔄 Verificando migrações...")
        execute_from_command_line(['manage.py', 'migrate', '--check'])
    except SystemExit:
        print("⚠️  Aplicando migrações necessárias...")
        execute_from_command_line(['manage.py', 'migrate'])
    
    User = get_user_model()
    
    email = 'bruno@move.com'
    password = '15002031'
    
    # Verificar se o usuário já existe
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        print(f"✅ Superusuário já existe!")
        print(f"📧 Email: {user.email}")
        print(f"👤 Username: {user.username}")
        print(f"🔑 É superusuário: {user.is_superuser}")
        
        # Atualizar para superusuário se necessário
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"⬆️  Usuário promovido a superusuário!")
    else:
        try:
            # Criar novo superusuário
            user = User.objects.create_superuser(
                username=email,
                email=email,
                password=password
            )
            user.first_name = 'Bruno'
            user.last_name = 'Admin'
            user.save()
            
            print(f"🎉 Superusuário criado com sucesso!")
            print(f"📧 Email: {email}")
            print(f"👤 Username: {email}")
            print(f"🔑 Senha: {password}")
            print(f"✨ Nome: Bruno Admin")
            
        except Exception as e:
            print(f"❌ Erro ao criar superusuário: {e}")
            return False
    
    print(f"\n🚀 Login disponível em: https://move.squadsolucoes.com.br/admin/")
    return True

if __name__ == '__main__':
    success = create_superuser()
    if success:
        print("\n✅ Setup do superusuário concluído!")
    else:
        print("\n❌ Falha no setup do superusuário!")
        exit(1)
