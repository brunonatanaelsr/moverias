#!/usr/bin/env python3
"""
Análise Crítica Completa do Sistema Move Marias
Identifica problemas, vulnerabilidades e oportunidades de melhoria
"""

import os
import sys
import django
import sqlite3
from pathlib import Path
from collections import defaultdict
import re

# Setup Django
sys.path.append('/workspaces/moverias')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.conf import settings
from django.core.checks import run_checks
from django.apps import apps
from django.db import connection, models
from django.contrib.auth.models import Permission, Group
from users.models import CustomUser


class SystemCriticalAnalysis:
    """Análise crítica completa do sistema"""
    
    def __init__(self):
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'optimization': []
        }
        
    def run_analysis(self):
        """Executa análise completa"""
        print("🔍 INICIANDO ANÁLISE CRÍTICA DO SISTEMA MOVE MARIAS")
        print("=" * 60)
        
        # 1. Análise de Segurança
        self.analyze_security()
        
        # 2. Análise de Banco de Dados
        self.analyze_database()
        
        # 3. Análise de Modelos
        self.analyze_models()
        
        # 4. Análise de Performance
        self.analyze_performance()
        
        # 5. Análise de Código
        self.analyze_code_quality()
        
        # 6. Análise de Configurações
        self.analyze_configurations()
        
        # 7. Análise de Testes
        self.analyze_testing()
        
        # 8. Análise de Dependências
        self.analyze_dependencies()
        
        # Gerar relatório
        self.generate_report()
        
    def analyze_security(self):
        """Análise de segurança"""
        print("\n🔐 ANÁLISE DE SEGURANÇA")
        print("-" * 30)
        
        # Verificar configurações de produção
        if settings.DEBUG:
            self.issues['critical'].append({
                'category': 'Security',
                'issue': 'DEBUG ativado',
                'description': 'DEBUG=True em produção expõe informações sensíveis',
                'solution': 'Definir DEBUG=False em produção',
                'priority': 'CRÍTICO'
            })
            
        # Verificar SECRET_KEY
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 50:
            self.issues['critical'].append({
                'category': 'Security',
                'issue': 'SECRET_KEY fraca',
                'description': 'SECRET_KEY muito curta ou insegura',
                'solution': 'Gerar SECRET_KEY com pelo menos 50 caracteres aleatórios',
                'priority': 'CRÍTICO'
            })
            
        # Verificar HTTPS
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            self.issues['high'].append({
                'category': 'Security',
                'issue': 'HTTPS não obrigatório',
                'description': 'SECURE_SSL_REDIRECT não configurado',
                'solution': 'Configurar SECURE_SSL_REDIRECT=True em produção',
                'priority': 'ALTO'
            })
            
        # Verificar headers de segurança
        if not getattr(settings, 'SECURE_HSTS_SECONDS', 0):
            self.issues['medium'].append({
                'category': 'Security',
                'issue': 'HSTS não configurado',
                'description': 'HTTP Strict Transport Security não habilitado',
                'solution': 'Configurar SECURE_HSTS_SECONDS',
                'priority': 'MÉDIO'
            })
            
        print("✅ Análise de segurança concluída")
        
    def analyze_database(self):
        """Análise do banco de dados"""
        print("\n🗄️ ANÁLISE DO BANCO DE DADOS")
        print("-" * 30)
        
        # Verificar índices faltantes
        with connection.cursor() as cursor:
            # Verificar tabelas sem índices
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Verificar se tabela tem índices
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                
                if not indexes:
                    self.issues['medium'].append({
                        'category': 'Database',
                        'issue': f'Tabela {table_name} sem índices',
                        'description': 'Tabela pode ter performance ruim em consultas',
                        'solution': 'Adicionar índices nas colunas mais consultadas',
                        'priority': 'MÉDIO'
                    })
                    
        # Verificar constraints
        self.check_database_constraints()
        
        print("✅ Análise do banco de dados concluída")
        
    def check_database_constraints(self):
        """Verificar constraints do banco"""
        with connection.cursor() as cursor:
            # Verificar foreign keys
            cursor.execute("PRAGMA foreign_keys")
            fk_status = cursor.fetchone()
            
            if not fk_status or fk_status[0] == 0:
                self.issues['high'].append({
                    'category': 'Database',
                    'issue': 'Foreign Keys desabilitadas',
                    'description': 'Integridade referencial não está sendo aplicada',
                    'solution': 'Habilitar PRAGMA foreign_keys=ON',
                    'priority': 'ALTO'
                })
                
    def analyze_models(self):
        """Análise dos modelos Django"""
        print("\n📊 ANÁLISE DOS MODELOS")
        print("-" * 30)
        
        for model in apps.get_models():
            # Verificar Meta class
            if not hasattr(model, '_meta'):
                continue
                
            # Verificar verbose_name
            if not model._meta.verbose_name or model._meta.verbose_name == model.__name__.lower():
                self.issues['low'].append({
                    'category': 'Models',
                    'issue': f'Modelo {model.__name__} sem verbose_name',
                    'description': 'Interface admin menos amigável',
                    'solution': 'Adicionar verbose_name na Meta class',
                    'priority': 'BAIXO'
                })
                
            # Verificar campos sem help_text
            for field in model._meta.fields:
                if isinstance(field, (models.CharField, models.TextField)) and not field.help_text:
                    self.issues['low'].append({
                        'category': 'Models',
                        'issue': f'Campo {model.__name__}.{field.name} sem help_text',
                        'description': 'Documentação insuficiente do campo',
                        'solution': 'Adicionar help_text ao campo',
                        'priority': 'BAIXO'
                    })
                    
            # Verificar campos de data sem auto_now
            for field in model._meta.fields:
                if isinstance(field, models.DateTimeField):
                    if field.name in ['created_at', 'updated_at'] and not (field.auto_now or field.auto_now_add):
                        self.issues['medium'].append({
                            'category': 'Models',
                            'issue': f'Campo de timestamp {model.__name__}.{field.name} sem auto_now',
                            'description': 'Campo de timestamp não é preenchido automaticamente',
                            'solution': 'Adicionar auto_now_add=True ou auto_now=True',
                            'priority': 'MÉDIO'
                        })
                        
        print("✅ Análise dos modelos concluída")
        
    def analyze_performance(self):
        """Análise de performance"""
        print("\n⚡ ANÁLISE DE PERFORMANCE")
        print("-" * 30)
        
        # Verificar cache
        if not settings.CACHES or settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.dummy.DummyCache':
            self.issues['medium'].append({
                'category': 'Performance',
                'issue': 'Cache não configurado',
                'description': 'Sistema pode ter performance ruim sem cache',
                'solution': 'Configurar Redis ou Memcached',
                'priority': 'MÉDIO'
            })
            
        # Verificar configurações de database
        if 'CONN_MAX_AGE' not in settings.DATABASES['default']:
            self.issues['optimization'].append({
                'category': 'Performance',
                'issue': 'Connection pooling não configurado',
                'description': 'Conexões de banco não são reutilizadas',
                'solution': 'Adicionar CONN_MAX_AGE nas configurações do banco',
                'priority': 'OTIMIZAÇÃO'
            })
            
        # Verificar compressão de static files
        if not getattr(settings, 'STATICFILES_STORAGE', '').endswith('ManifestStaticFilesStorage'):
            self.issues['optimization'].append({
                'category': 'Performance',
                'issue': 'Static files não comprimidos',
                'description': 'Arquivos estáticos não estão sendo comprimidos',
                'solution': 'Usar ManifestStaticFilesStorage',
                'priority': 'OTIMIZAÇÃO'
            })
            
        print("✅ Análise de performance concluída")
        
    def analyze_code_quality(self):
        """Análise da qualidade do código"""
        print("\n🧹 ANÁLISE DE QUALIDADE DO CÓDIGO")
        print("-" * 30)
        
        # Verificar arquivos Python
        python_files = []
        for root, dirs, files in os.walk('/workspaces/moverias'):
            # Ignorar diretórios específicos
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'staticfiles', 'media']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
                    
        # Verificar imports não utilizados e outros problemas
        for file_path in python_files[:20]:  # Limitar para não sobrecarregar
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Verificar linhas muito longas
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if len(line) > 120:
                            self.issues['low'].append({
                                'category': 'Code Quality',
                                'issue': f'Linha muito longa em {file_path}:{i}',
                                'description': f'Linha com {len(line)} caracteres',
                                'solution': 'Quebrar linha em múltiplas linhas',
                                'priority': 'BAIXO'
                            })
                            break  # Evitar spam
                            
                    # Verificar TODO/FIXME
                    if 'TODO' in content or 'FIXME' in content:
                        self.issues['low'].append({
                            'category': 'Code Quality',
                            'issue': f'TODO/FIXME encontrado em {file_path}',
                            'description': 'Código com pendências',
                            'solution': 'Resolver ou documentar pendências',
                            'priority': 'BAIXO'
                        })
                        
            except Exception as e:
                continue
                
        print("✅ Análise de qualidade do código concluída")
        
    def analyze_configurations(self):
        """Análise das configurações"""
        print("\n⚙️ ANÁLISE DAS CONFIGURAÇÕES")
        print("-" * 30)
        
        # Verificar middleware em ordem correta
        middleware = settings.MIDDLEWARE
        security_middleware_pos = -1
        session_middleware_pos = -1
        
        for i, mw in enumerate(middleware):
            if 'SecurityMiddleware' in mw:
                security_middleware_pos = i
            if 'SessionMiddleware' in mw:
                session_middleware_pos = i
                
        if security_middleware_pos > session_middleware_pos and session_middleware_pos != -1:
            self.issues['medium'].append({
                'category': 'Configuration',
                'issue': 'Middleware em ordem incorreta',
                'description': 'SecurityMiddleware deve vir antes do SessionMiddleware',
                'solution': 'Reordenar MIDDLEWARE em settings.py',
                'priority': 'MÉDIO'
            })
            
        # Verificar configurações de email
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            self.issues['medium'].append({
                'category': 'Configuration',
                'issue': 'Email backend para desenvolvimento',
                'description': 'Emails não são enviados em produção',
                'solution': 'Configurar email backend SMTP em produção',
                'priority': 'MÉDIO'
            })
            
        print("✅ Análise das configurações concluída")
        
    def analyze_testing(self):
        """Análise dos testes"""
        print("\n🧪 ANÁLISE DOS TESTES")
        print("-" * 30)
        
        # Verificar se existem testes
        test_files = []
        for root, dirs, files in os.walk('/workspaces/moverias'):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))
                    
        if len(test_files) < 10:
            self.issues['medium'].append({
                'category': 'Testing',
                'issue': 'Poucos arquivos de teste',
                'description': f'Apenas {len(test_files)} arquivos de teste encontrados',
                'solution': 'Adicionar mais testes unitários e de integração',
                'priority': 'MÉDIO'
            })
            
        print("✅ Análise dos testes concluída")
        
    def analyze_dependencies(self):
        """Análise das dependências"""
        print("\n📦 ANÁLISE DAS DEPENDÊNCIAS")
        print("-" * 30)
        
        try:
            with open('/workspaces/moverias/requirements.txt', 'r') as f:
                requirements = f.read()
                
            # Verificar versões pinadas
            lines = [line.strip() for line in requirements.split('\n') if line.strip()]
            unpinned = [line for line in lines if '==' not in line and line and not line.startswith('#')]
            
            if unpinned:
                self.issues['medium'].append({
                    'category': 'Dependencies',
                    'issue': f'Dependências sem versão fixa: {len(unpinned)}',
                    'description': 'Dependências podem quebrar com atualizações',
                    'solution': 'Fixar versões das dependências com ==',
                    'priority': 'MÉDIO'
                })
                
        except FileNotFoundError:
            self.issues['high'].append({
                'category': 'Dependencies',
                'issue': 'requirements.txt não encontrado',
                'description': 'Dependências não documentadas',
                'solution': 'Criar requirements.txt com todas as dependências',
                'priority': 'ALTO'
            })
            
        print("✅ Análise das dependências concluída")
        
    def generate_report(self):
        """Gera relatório final"""
        print("\n📋 RELATÓRIO FINAL - ANÁLISE CRÍTICA")
        print("=" * 60)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"  • Total de problemas encontrados: {total_issues}")
        print(f"  • Críticos: {len(self.issues['critical'])}")
        print(f"  • Altos: {len(self.issues['high'])}")
        print(f"  • Médios: {len(self.issues['medium'])}")
        print(f"  • Baixos: {len(self.issues['low'])}")
        print(f"  • Otimizações: {len(self.issues['optimization'])}")
        
        # Problemas críticos
        if self.issues['critical']:
            print(f"\n🚨 PROBLEMAS CRÍTICOS ({len(self.issues['critical'])}):")
            for i, issue in enumerate(self.issues['critical'], 1):
                print(f"  {i}. {issue['issue']}")
                print(f"     Descrição: {issue['description']}")
                print(f"     Solução: {issue['solution']}")
                print()
                
        # Problemas altos
        if self.issues['high']:
            print(f"\n⚠️ PROBLEMAS ALTOS ({len(self.issues['high'])}):")
            for i, issue in enumerate(self.issues['high'], 1):
                print(f"  {i}. {issue['issue']}")
                print(f"     Descrição: {issue['description']}")
                print(f"     Solução: {issue['solution']}")
                print()
                
        # Problemas médios (primeiros 5)
        if self.issues['medium']:
            print(f"\n⚡ PROBLEMAS MÉDIOS (primeiros 5 de {len(self.issues['medium'])}):")
            for i, issue in enumerate(self.issues['medium'][:5], 1):
                print(f"  {i}. {issue['issue']}")
                print(f"     Solução: {issue['solution']}")
                print()
                
        # Oportunidades de otimização
        if self.issues['optimization']:
            print(f"\n🚀 OPORTUNIDADES DE OTIMIZAÇÃO ({len(self.issues['optimization'])}):")
            for i, issue in enumerate(self.issues['optimization'], 1):
                print(f"  {i}. {issue['issue']}")
                print(f"     Solução: {issue['solution']}")
                print()
                
        print("\n✅ ANÁLISE CRÍTICA CONCLUÍDA")
        print("💡 Priorize a correção dos problemas críticos e altos primeiro.")


if __name__ == '__main__':
    analyzer = SystemCriticalAnalysis()
    analyzer.run_analysis()
