"""
Comando para gerar chaves de segurança
"""
import secrets
import string
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Gera chaves de segurança para o sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['secret', 'crypto', 'backup', 'all'],
            default='all',
            help='Tipo de chave a gerar'
        )
        
        parser.add_argument(
            '--length',
            type=int,
            default=50,
            help='Comprimento da chave (padrão: 50)'
        )
    
    def handle(self, *args, **options):
        key_type = options['type']
        length = options['length']
        
        if key_type in ['secret', 'all']:
            self.generate_secret_key()
        
        if key_type in ['crypto', 'all']:
            self.generate_crypto_key(length)
        
        if key_type in ['backup', 'all']:
            self.generate_backup_key(length)
    
    def generate_secret_key(self):
        """Gerar SECRET_KEY do Django"""
        secret_key = get_random_secret_key()
        
        self.stdout.write(
            self.style.SUCCESS(f'SECRET_KEY={secret_key}')
        )
        
        self.stdout.write(
            self.style.WARNING(
                'IMPORTANTE: Adicione esta chave ao seu arquivo .env e '
                'mantenha-a segura!'
            )
        )
    
    def generate_crypto_key(self, length):
        """Gerar chave de criptografia"""
        crypto_key = secrets.token_urlsafe(length)
        
        self.stdout.write(
            self.style.SUCCESS(f'DJANGO_CRYPTOGRAPHY_KEY={crypto_key}')
        )
        
        self.stdout.write(
            self.style.WARNING(
                'Esta chave é usada para criptografar dados sensíveis (CPF, RG). '
                'Não altere após ter dados criptografados!'
            )
        )
    
    def generate_backup_key(self, length):
        """Gerar chave de backup"""
        backup_key = secrets.token_urlsafe(length)
        
        self.stdout.write(
            self.style.SUCCESS(f'BACKUP_ENCRYPTION_KEY={backup_key}')
        )
        
        self.stdout.write(
            self.style.WARNING(
                'Esta chave é usada para criptografar backups. '
                'Mantenha-a segura e separada dos backups!'
            )
        )
    
    def generate_strong_password(self, length=16):
        """Gerar senha forte"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        self.stdout.write(
            self.style.SUCCESS(f'Senha gerada: {password}')
        )
        
        return password
