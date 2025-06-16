#!/usr/bin/env python
"""
Script para gerar chaves seguras para o Move Marias
"""
import secrets
import string
import os
import sys


def generate_secret_key(length=50):
    """Gera uma SECRET_KEY segura para Django"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for i in range(length))


def generate_django_cryptography_key():
    """Gera uma chave para django-cryptography"""
    return secrets.token_urlsafe(32)


def generate_backup_encryption_key():
    """Gera uma chave para criptografia de backups"""
    return secrets.token_urlsafe(32)


def generate_env_file():
    """Gera um arquivo .env com chaves seguras"""
    env_content = f"""# SECURITY SETTINGS
DEBUG=False
SECRET_KEY={generate_secret_key()}
DJANGO_CRYPTOGRAPHY_KEY={generate_django_cryptography_key()}

# DATABASE
DATABASE_URL=postgresql://user:password@localhost:5432/movemarias_db

# ALLOWED HOSTS (comma separated)
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# ENVIRONMENT
ENVIRONMENT=production

# EMAIL CONFIGURATION
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=Move Marias <noreply@movemarias.org>
SERVER_EMAIL=Move Marias <server@movemarias.org>

# CACHE (Redis)
REDIS_URL=redis://localhost:6379/0

# FILE STORAGE
USE_S3=False
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# MONITORING
SENTRY_DSN=your-sentry-dsn-here

# BACKUP
BACKUP_ENCRYPTION_KEY={generate_backup_encryption_key()}
"""
    return env_content


def main():
    """Função principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'secret':
            print("SECRET_KEY:", generate_secret_key())
        elif command == 'crypto':
            print("DJANGO_CRYPTOGRAPHY_KEY:", generate_django_cryptography_key())
        elif command == 'backup':
            print("BACKUP_ENCRYPTION_KEY:", generate_backup_encryption_key())
        elif command == 'env':
            env_file = '.env.production'
            with open(env_file, 'w') as f:
                f.write(generate_env_file())
            print(f"Arquivo {env_file} criado com chaves seguras!")
            print("IMPORTANTE: Configure os valores específicos do seu ambiente.")
        else:
            print("Comando inválido. Use: secret, crypto, backup ou env")
    else:
        print("Move Marias - Gerador de Chaves Seguras")
        print("=====================================")
        print()
        print("SECRET_KEY:")
        print(generate_secret_key())
        print()
        print("DJANGO_CRYPTOGRAPHY_KEY:")
        print(generate_django_cryptography_key())
        print()
        print("BACKUP_ENCRYPTION_KEY:")
        print(generate_backup_encryption_key())
        print()
        print("Para gerar um arquivo .env: python generate_keys.py env")


if __name__ == "__main__":
    main()
