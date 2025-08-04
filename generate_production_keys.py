#!/usr/bin/env python3
"""
Gerador de Chaves Secretas para Produção - Move Marias
Gera todas as chaves necessárias para deploy em produção
"""

import secrets
import string
import os
from cryptography.fernet import Fernet

def generate_secret_key(length=50):
    """Gera SECRET_KEY segura para Django"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_django_cryptography_key():
    """Gera chave para django-cryptography"""
    return Fernet.generate_key().decode()

def generate_database_password(length=32):
    """Gera senha segura para banco de dados"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_email_password(length=24):
    """Gera senha para email"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🔐 GERADOR DE CHAVES SECRETAS - MOVE MARIAS")
    print("=" * 60)
    print()
    
    # Gerar todas as chaves
    secret_key = generate_secret_key()
    crypto_key = generate_django_cryptography_key()
    db_password = generate_database_password()
    email_password = generate_email_password()
    
    # Gerar chaves adicionais
    jwt_secret = secrets.token_urlsafe(32)
    redis_password = generate_database_password(16)
    
    print("📋 CHAVES GERADAS PARA PRODUÇÃO:")
    print("-" * 40)
    print()
    
    print("🔑 Django SECRET_KEY:")
    print(f"SECRET_KEY={secret_key}")
    print()
    
    print("🔐 Django Cryptography Key:")
    print(f"DJANGO_CRYPTOGRAPHY_KEY={crypto_key}")
    print()
    
    print("💾 Senha do Banco de Dados:")
    print(f"DB_PASSWORD={db_password}")
    print()
    
    print("📧 Senha do Email:")
    print(f"EMAIL_HOST_PASSWORD={email_password}")
    print()
    
    print("🎟️ JWT Secret (se usar):")
    print(f"JWT_SECRET={jwt_secret}")
    print()
    
    print("💭 Redis Password (se necessário):")
    print(f"REDIS_PASSWORD={redis_password}")
    print()
    
    # Salvar em arquivo
    try:
        with open('/workspaces/moverias/production_keys.txt', 'w') as f:
            f.write("# CHAVES SECRETAS PARA PRODUÇÃO - MOVE MARIAS\n")
            f.write("# Data de Geração: " + secrets.token_hex(8) + "\n")
            f.write("# ATENÇÃO: Mantenha este arquivo seguro e delete após uso!\n\n")
            
            f.write("# Django Configuration\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"DJANGO_CRYPTOGRAPHY_KEY={crypto_key}\n\n")
            
            f.write("# Database Configuration\n")
            f.write(f"DB_PASSWORD={db_password}\n\n")
            
            f.write("# Email Configuration\n")
            f.write(f"EMAIL_HOST_PASSWORD={email_password}\n\n")
            
            f.write("# Additional Keys\n")
            f.write(f"JWT_SECRET={jwt_secret}\n")
            f.write(f"REDIS_PASSWORD={redis_password}\n\n")
            
            f.write("# Usage Instructions:\n")
            f.write("# 1. Copy these values to your .env.production file\n")
            f.write("# 2. Replace placeholder values in .env.production\n")
            f.write("# 3. Delete this file after copying keys\n")
            f.write("# 4. Never commit these keys to version control\n")
            
        print("✅ Chaves salvas em: production_keys.txt")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        print()
    
    print("⚠️  INSTRUÇÕES DE SEGURANÇA:")
    print("1. Copie estas chaves para o arquivo .env no servidor")
    print("2. Delete o arquivo production_keys.txt após usar")
    print("3. Nunca commit estas chaves no git")
    print("4. Mantenha as chaves seguras e privadas")
    print("5. Gere novas chaves se houver comprometimento")
    print()
    
    print("🚀 PRONTO PARA DEPLOY EM PRODUÇÃO!")

if __name__ == '__main__':
    main()
