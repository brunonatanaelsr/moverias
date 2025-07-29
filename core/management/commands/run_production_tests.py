"""
Comando Django para executar testes de produção
"""
from django.core.management.base import BaseCommand
from django.test.utils import get_runner
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = 'Executa suite completa de testes para validação de produção'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--unit',
            action='store_true',
            help='Executar apenas testes unitários'
        )
        parser.add_argument(
            '--integration', 
            action='store_true',
            help='Executar apenas testes de integração'
        )
        parser.add_argument(
            '--security',
            action='store_true', 
            help='Executar apenas testes de segurança'
        )
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Executar apenas testes de performance'
        )
        parser.add_argument(
            '--smoke',
            action='store_true',
            help='Executar apenas testes smoke'
        )
        parser.add_argument(
            '--coverage',
            action='store_true',
            help='Gerar relatório de cobertura'
        )
        parser.add_argument(
            '--failfast',
            action='store_true',
            help='Parar no primeiro erro'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Iniciando Suite de Testes Django')
        )
        
        # Verificar se pytest está instalado
        try:
            import pytest
        except ImportError:
            self.stdout.write(
                self.style.ERROR('❌ pytest não está instalado. Execute: pip install pytest pytest-django')
            )
            return
        
        # Construir comando pytest
        cmd = ['python', '-m', 'pytest']
        
        # Adicionar opções
        if options['failfast']:
            cmd.append('-x')
        
        cmd.extend(['-v', '--tb=short'])
        
        # Determinar quais testes executar
        if options['unit']:
            cmd.extend(['-m', 'unit'])
            test_type = 'Testes Unitários'
        elif options['integration']:
            cmd.extend(['-m', 'integration'])
            test_type = 'Testes de Integração'
        elif options['security']:
            cmd.extend(['-m', 'security'])
            test_type = 'Testes de Segurança'
        elif options['performance']:
            cmd.extend(['-m', 'performance and not slow'])
            test_type = 'Testes de Performance'
        elif options['smoke']:
            cmd.extend(['-m', 'smoke'])
            test_type = 'Testes Smoke'
        else:
            test_type = 'Todos os Testes'
        
        # Adicionar cobertura se solicitado
        if options['coverage']:
            cmd.extend([
                '--cov=.',
                '--cov-report=html',
                '--cov-report=term-missing'
            ])
        
        self.stdout.write(f'📋 Executando: {test_type}')
        self.stdout.write(f'🔧 Comando: {" ".join(cmd)}')
        
        # Executar testes
        try:
            result = subprocess.run(cmd, check=False)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS('✅ Todos os testes passaram!')
                )
                
                # Executar verificações adicionais se todos os testes passaram
                self._run_additional_checks()
                
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Alguns testes falharam!')
                )
                sys.exit(1)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('⚠️ Testes interrompidos pelo usuário')
            )
            sys.exit(1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'💥 Erro ao executar testes: {e}')
            )
            sys.exit(1)
    
    def _run_additional_checks(self):
        """Executar verificações adicionais"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('🔍 Executando verificações adicionais...')
        self.stdout.write('='*50)
        
        checks = [
            (['python', 'manage.py', 'check'], 'Django System Check'),
            (['python', 'manage.py', 'check', '--deploy'], 'Django Deploy Check'),
        ]
        
        all_passed = True
        
        for cmd, description in checks:
            self.stdout.write(f'\n📋 {description}...')
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
                if result.returncode == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {description} - OK')
                    )
                    if result.stdout.strip():
                        self.stdout.write(result.stdout)
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {description} - FAILED')
                    )
                    if result.stderr:
                        self.stdout.write(result.stderr)
                    all_passed = False
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'💥 Erro em {description}: {e}')
                )
                all_passed = False
        
        # Verificar configurações de segurança
        self._check_security_settings()
        
        if all_passed:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS('🎉 TODAS AS VERIFICAÇÕES PASSARAM! 🎉')
            )
            self.stdout.write('✨ Sistema pronto para produção!')
            self.stdout.write('='*50)
        else:
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.ERROR('💥 ALGUMAS VERIFICAÇÕES FALHARAM 💥')
            )
            self.stdout.write('⚠️ Revise as configurações antes do deploy!')
            self.stdout.write('='*50)
    
    def _check_security_settings(self):
        """Verificar configurações de segurança"""
        self.stdout.write('\n🔒 Verificando configurações de segurança...')
        
        warnings = []
        
        # DEBUG em produção
        if settings.DEBUG:
            warnings.append('DEBUG=True em produção é inseguro')
        
        # SECRET_KEY
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 50:
            warnings.append('SECRET_KEY muito fraca ou ausente')
        
        if settings.SECRET_KEY.startswith('django-insecure-'):
            warnings.append('SECRET_KEY de desenvolvimento detectada')
        
        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
            warnings.append('ALLOWED_HOSTS não configurado adequadamente')
        
        # Configurações HTTPS
        https_settings = [
            ('SECURE_SSL_REDIRECT', 'Redirecionamento HTTPS'),
            ('SECURE_HSTS_SECONDS', 'HSTS'),
            ('SESSION_COOKIE_SECURE', 'Cookies de sessão seguras'),
            ('CSRF_COOKIE_SECURE', 'Cookies CSRF seguras')
        ]
        
        for setting_name, description in https_settings:
            if not getattr(settings, setting_name, False):
                warnings.append(f'{description} não configurado')
        
        if warnings:
            self.stdout.write(
                self.style.WARNING('⚠️ Avisos de segurança encontrados:')
            )
            for warning in warnings:
                self.stdout.write(f'  • {warning}')
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Configurações de segurança OK')
            )
    
    def _check_database_performance(self):
        """Verificar performance do banco de dados"""
        from django.db import connection
        import time
        
        self.stdout.write('\n📊 Testando performance do banco...')
        
        # Query simples para testar latência
        start_time = time.time()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            result = cursor.fetchone()
        
        query_time = time.time() - start_time
        
        if query_time < 0.1:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Latência do banco OK: {query_time:.3f}s')
            )
        elif query_time < 0.5:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Latência do banco aceitável: {query_time:.3f}s')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Latência do banco alta: {query_time:.3f}s')
            )
