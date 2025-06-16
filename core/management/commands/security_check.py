"""
Comando para verificar e corrigir problemas de segurança
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import models
from core.audit import AuditLog
import os
import secrets

User = get_user_model()


class Command(BaseCommand):
    help = 'Verifica e corrige problemas de segurança do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-keys',
            action='store_true',
            help='Verifica se as chaves de segurança são adequadas',
        )
        parser.add_argument(
            '--generate-key',
            action='store_true',
            help='Gera uma nova SECRET_KEY segura',
        )
        parser.add_argument(
            '--audit-summary',
            action='store_true',
            help='Mostra resumo das atividades auditadas',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Limpa o cache do sistema',
        )

    def handle(self, *args, **options):
        if options['check_keys']:
            self.check_security_keys()
        
        if options['generate_key']:
            self.generate_secret_key()
        
        if options['audit_summary']:
            self.show_audit_summary()
        
        if options['clear_cache']:
            self.clear_system_cache()

    def check_security_keys(self):
        """Verifica se as chaves de segurança são adequadas"""
        self.stdout.write(self.style.WARNING('Verificando chaves de segurança...'))
        
        # Verificar SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key:
            self.stdout.write(self.style.ERROR('SECRET_KEY não configurada!'))
        elif len(secret_key) < 50:
            self.stdout.write(self.style.ERROR('SECRET_KEY muito curta (< 50 caracteres)'))
        elif secret_key.startswith('django-insecure-'):
            self.stdout.write(self.style.ERROR('SECRET_KEY de desenvolvimento detectada!'))
        else:
            self.stdout.write(self.style.SUCCESS('SECRET_KEY OK'))
        
        # Verificar DJANGO_CRYPTOGRAPHY_KEY
        crypto_key = getattr(settings, 'DJANGO_CRYPTOGRAPHY_KEY', '')
        if not crypto_key:
            self.stdout.write(self.style.ERROR('DJANGO_CRYPTOGRAPHY_KEY não configurada!'))
        elif crypto_key in ['test-key-for-development', 'change-me-in-production']:
            self.stdout.write(self.style.ERROR('DJANGO_CRYPTOGRAPHY_KEY de desenvolvimento detectada!'))
        else:
            self.stdout.write(self.style.SUCCESS('DJANGO_CRYPTOGRAPHY_KEY OK'))
        
        # Verificar DEBUG em produção
        if getattr(settings, 'DEBUG', False):
            self.stdout.write(self.style.WARNING('DEBUG=True (apenas para desenvolvimento)'))
        else:
            self.stdout.write(self.style.SUCCESS('DEBUG=False (produção)'))

    def generate_secret_key(self):
        """Gera uma nova SECRET_KEY segura"""
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)'
        new_key = ''.join(secrets.choice(alphabet) for i in range(50))
        
        self.stdout.write(self.style.SUCCESS('Nova SECRET_KEY gerada:'))
        self.stdout.write(f'SECRET_KEY={new_key}')
        self.stdout.write('')
        self.stdout.write('Adicione esta chave ao seu arquivo .env')

    def show_audit_summary(self):
        """Mostra resumo das atividades auditadas"""
        self.stdout.write(self.style.WARNING('Resumo da Auditoria:'))
        
        try:
            # Total de logs de auditoria
            total_logs = AuditLog.objects.count()
            self.stdout.write(f'Total de eventos auditados: {total_logs}')
            
            # Eventos por ação
            actions = AuditLog.objects.values('action').distinct()
            for action in actions:
                count = AuditLog.objects.filter(action=action['action']).count()
                self.stdout.write(f'  {action["action"]}: {count}')
            
            # Usuários mais ativos
            active_users = AuditLog.objects.values('user__username').annotate(
                count=models.Count('id')
            ).order_by('-count')[:5]
            
            self.stdout.write('\nUsuários mais ativos:')
            for user in active_users:
                self.stdout.write(f'  {user["user__username"]}: {user["count"]} ações')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao gerar resumo: {e}'))

    def clear_system_cache(self):
        """Limpa o cache do sistema"""
        self.stdout.write(self.style.WARNING('Limpando cache do sistema...'))
        
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Cache limpo com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao limpar cache: {e}'))
