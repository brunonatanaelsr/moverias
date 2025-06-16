#!/usr/bin/env python3
"""
Teste do sistema de autenticação do Move Marias
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/brunonatanael/Desktop/MoveMarias/02')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from users.models import CustomUser

def test_password_hashing():
    """Testa o sistema de hash de senhas"""
    print("🔐 Testando sistema de hash de senhas...")
    
    # Teste de criação de hash
    password = "15002031"
    hashed = make_password(password)
    print(f"✅ Hash criado: {hashed[:50]}...")
    
    # Teste de verificação
    is_valid = check_password(password, hashed)
    print(f"✅ Verificação de senha: {'OK' if is_valid else 'ERRO'}")
    
    return is_valid

def test_user_authentication():
    """Testa autenticação de usuário"""
    print("\n👤 Testando autenticação de usuário...")
    
    try:
        # Verificar se usuário admin existe
        user = CustomUser.objects.get(email='admin@movemarias.org')
        print(f"✅ Usuário encontrado: {user.email}")
        
        # Testar autenticação
        auth_user = authenticate(username='admin@movemarias.org', password='15002031')
        if auth_user:
            print(f"✅ Autenticação bem-sucedida: {auth_user.email}")
            return True
        else:
            print("❌ Falha na autenticação")
            return False
            
    except CustomUser.DoesNotExist:
        print("❌ Usuário admin não encontrado")
        return False
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return False

def test_argon2_availability():
    """Testa se Argon2 está disponível"""
    print("\n🔒 Testando disponibilidade do Argon2...")
    
    try:
        import argon2
        print("✅ Biblioteca argon2 disponível")
        
        from django.contrib.auth.hashers import Argon2PasswordHasher
        hasher = Argon2PasswordHasher()
        test_hash = hasher.encode("test123", "salt123")
        print(f"✅ Argon2PasswordHasher funcionando: {test_hash[:50]}...")
        return True
        
    except ImportError as e:
        print(f"❌ Biblioteca argon2 não disponível: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no Argon2PasswordHasher: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando testes do sistema de autenticação Move Marias")
    print("=" * 60)
    
    results = []
    
    # Teste 1: Argon2
    results.append(test_argon2_availability())
    
    # Teste 2: Hash de senhas
    results.append(test_password_hashing())
    
    # Teste 3: Autenticação
    results.append(test_user_authentication())
    
    # Resultado final
    print("\n" + "=" * 60)
    success_count = sum(results)
    total_tests = len(results)
    
    if success_count == total_tests:
        print(f"🎉 TODOS OS TESTES PASSARAM! ({success_count}/{total_tests})")
        print("✅ Sistema de autenticação funcionando corretamente")
        sys.exit(0)
    else:
        print(f"⚠️  ALGUNS TESTES FALHARAM ({success_count}/{total_tests})")
        print("❌ Verifique os erros acima")
        sys.exit(1)

if __name__ == "__main__":
    main()
