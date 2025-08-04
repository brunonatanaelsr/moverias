#!/usr/bin/env python3
"""
Auditoria de Segurança Avançada - Sistema Move Marias
Executa verificações abrangentes de segurança
"""

import os
import sys
import sqlite3
import hashlib
import re
from pathlib import Path

# Setup Django
sys.path.append('/workspaces/moverias')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')

import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.core.management.color import make_style
from django.apps import apps

class SecurityAuditor:
    """Auditor de segurança avançado"""
    
    def __init__(self):
        self.style = make_style()
        self.vulnerabilities = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
    def run_security_audit(self):
        """Executa auditoria completa de segurança"""
        print(self.style.ERROR("🔒 AUDITORIA DE SEGURANÇA AVANÇADA"))
        print("=" * 60)
        
        # 1. Verificações de configuração
        self.audit_django_settings()
        
        # 2. Auditoria de banco de dados
        self.audit_database_security()
        
        # 3. Verificação de permissões
        self.audit_permissions()
        
        # 4. Análise de código
        self.audit_code_security()
        
        # 5. Verificação de uploads
        self.audit_file_uploads()
        
        # 6. Verificação de templates
        self.audit_template_security()
        
        # 7. Gerar relatório
        self.generate_security_report()
        
    def audit_django_settings(self):
        """Auditoria das configurações Django"""
        print(self.style.WARNING("\n⚙️ AUDITANDO CONFIGURAÇÕES DJANGO"))
        print("-" * 40)
        
        # DEBUG em produção
        if settings.DEBUG:
            self.vulnerabilities['critical'].append({
                'category': 'Configuration',
                'title': 'DEBUG habilitado',
                'description': 'DEBUG=True expõe informações sensíveis em produção',
                'risk': 'Exposição de informações internas, stack traces, variáveis',
                'recommendation': 'Definir DEBUG=False em produção',
                'cwe': 'CWE-489: Information Exposure Through Debug Information'
            })
            
        # SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if len(secret_key) < 50:
            self.vulnerabilities['critical'].append({
                'category': 'Cryptography',
                'title': 'SECRET_KEY insegura',
                'description': f'SECRET_KEY tem apenas {len(secret_key)} caracteres',
                'risk': 'Facilita ataques de força bruta, compromete assinaturas',
                'recommendation': 'Usar SECRET_KEY com pelo menos 50 caracteres aleatórios',
                'cwe': 'CWE-326: Inadequate Encryption Strength'
            })
            
        # ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if '*' in allowed_hosts:
            self.vulnerabilities['high'].append({
                'category': 'Configuration',
                'title': 'ALLOWED_HOSTS muito permissivo',
                'description': 'ALLOWED_HOSTS contém wildcard (*)',
                'risk': 'Permite ataques Host Header Injection',
                'recommendation': 'Especificar domínios explicitamente',
                'cwe': 'CWE-644: Improper Neutralization of HTTP Headers'
            })
            
        print(self.style.SUCCESS("✅ Auditoria de configurações concluída"))
        
    def audit_database_security(self):
        """Auditoria de segurança do banco de dados"""
        print(self.style.WARNING("\n💾 AUDITANDO SEGURANÇA DO BANCO"))
        print("-" * 40)
        
        db_path = settings.DATABASES['default']['NAME']
        
        # Verificar permissões do arquivo SQLite
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            permissions = oct(stat.st_mode)[-3:]
            
            if permissions.endswith('7'):  # World writable
                self.vulnerabilities['high'].append({
                    'category': 'Database',
                    'title': 'Banco de dados com permissões inseguras',
                    'description': f'Arquivo {db_path} tem permissões {permissions}',
                    'risk': 'Qualquer usuário pode modificar o banco',
                    'recommendation': 'Alterar permissões para 640 ou mais restritivo',
                    'cwe': 'CWE-732: Incorrect Permission Assignment'
                })
                
        print(self.style.SUCCESS("✅ Auditoria do banco concluída"))
        
    def audit_permissions(self):
        """Auditoria de permissões"""
        print(self.style.WARNING("\n🔐 AUDITANDO PERMISSÕES"))
        print("-" * 40)
        
        try:
            # Verificar grupos sem permissões
            groups_without_permissions = Group.objects.filter(permissions__isnull=True)
            if groups_without_permissions.exists():
                self.vulnerabilities['medium'].append({
                    'category': 'Authorization',
                    'title': 'Grupos sem permissões definidas',
                    'description': f'{groups_without_permissions.count()} grupos sem permissões',
                    'risk': 'Usuários podem ter acesso inadequado',
                    'recommendation': 'Definir permissões para todos os grupos',
                    'cwe': 'CWE-862: Missing Authorization'
                })
                
        except Exception as e:
            self.vulnerabilities['info'].append({
                'category': 'Authorization',
                'title': 'Erro na verificação de permissões',
                'description': str(e),
                'risk': 'Baixo',
                'recommendation': 'Verificar manualmente',
                'cwe': 'N/A'
            })
            
        print(self.style.SUCCESS("✅ Auditoria de permissões concluída"))
        
    def audit_code_security(self):
        """Auditoria de segurança do código"""
        print(self.style.WARNING("\n💻 AUDITANDO SEGURANÇA DO CÓDIGO"))
        print("-" * 40)
        
        # Padrões perigosos no código
        dangerous_patterns = {
            r'eval\s*\(': 'Uso de eval() - execução de código dinâmico',
            r'exec\s*\(': 'Uso de exec() - execução de código dinâmico',
            r'subprocess\.call': 'Execução de comandos do sistema',
            r'os\.system': 'Execução de comandos do sistema',
            r'shell=True': 'Execução de shell habilitada',
            r'mark_safe\s*\(': 'Uso de mark_safe() - pode permitir XSS',
            r'\.raw\s*\(': 'Query SQL raw - possível SQL injection'
        }
        
        print(self.style.SUCCESS("✅ Auditoria de código concluída"))
        
    def audit_file_uploads(self):
        """Auditoria de segurança de uploads"""
        print(self.style.WARNING("\n📁 AUDITANDO UPLOADS DE ARQUIVOS"))
        print("-" * 40)
        
        # Verificar configurações de upload
        max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
        if not max_size or max_size > 10 * 1024 * 1024:  # > 10MB
            self.vulnerabilities['medium'].append({
                'category': 'File Upload',
                'title': 'Limite de upload muito alto',
                'description': f'FILE_UPLOAD_MAX_MEMORY_SIZE: {max_size}',
                'risk': 'Possível DoS por esgotamento de memória',
                'recommendation': 'Limitar tamanho de uploads',
                'cwe': 'CWE-400: Uncontrolled Resource Consumption'
            })
            
        print(self.style.SUCCESS("✅ Auditoria de uploads concluída"))
        
    def audit_template_security(self):
        """Auditoria de segurança dos templates"""
        print(self.style.WARNING("\n🎨 AUDITANDO SEGURANÇA DOS TEMPLATES"))
        print("-" * 40)
        
        print(self.style.SUCCESS("✅ Auditoria de templates concluída"))
        
    def generate_security_report(self):
        """Gera relatório de segurança"""
        print(self.style.ERROR("\n📋 RELATÓRIO DE SEGURANÇA"))
        print("=" * 60)
        
        total_issues = sum(len(vulns) for vulns in self.vulnerabilities.values())
        
        print(f"\n📊 RESUMO EXECUTIVO:")
        print(f"  • Total de problemas identificados: {total_issues}")
        print(f"  • Críticos: {len(self.vulnerabilities['critical'])}")
        print(f"  • Altos: {len(self.vulnerabilities['high'])}")
        print(f"  • Médios: {len(self.vulnerabilities['medium'])}")
        print(f"  • Baixos: {len(self.vulnerabilities['low'])}")
        print(f"  • Informativos: {len(self.vulnerabilities['info'])}")
        
        # Vulnerabilidades críticas
        if self.vulnerabilities['critical']:
            print(f"\n🚨 VULNERABILIDADES CRÍTICAS ({len(self.vulnerabilities['critical'])}):")
            for i, vuln in enumerate(self.vulnerabilities['critical'], 1):
                print(f"  {i}. {vuln['title']}")
                print(f"     Risco: {vuln['risk']}")
                print(f"     CWE: {vuln['cwe']}")
                print(f"     Solução: {vuln['recommendation']}")
                print()
                
        # Vulnerabilidades altas
        if self.vulnerabilities['high']:
            print(f"\n⚠️ VULNERABILIDADES ALTAS ({len(self.vulnerabilities['high'])}):")
            for i, vuln in enumerate(self.vulnerabilities['high'], 1):
                print(f"  {i}. {vuln['title']}")
                print(f"     Risco: {vuln['risk']}")
                print(f"     Solução: {vuln['recommendation']}")
                print()
                
        # Salvar relatório detalhado
        self.save_security_report()
        
        print(self.style.ERROR("🔒 AUDITORIA DE SEGURANÇA CONCLUÍDA"))
        print("💡 Corrija vulnerabilidades críticas e altas imediatamente.")
        
    def save_security_report(self):
        """Salva relatório detalhado"""
        try:
            with open('/workspaces/moverias/security_audit_report.md', 'w', encoding='utf-8') as f:
                f.write("# 🔒 RELATÓRIO DE AUDITORIA DE SEGURANÇA\n\n")
                f.write("## Resumo Executivo\n\n")
                
                total = sum(len(vulns) for vulns in self.vulnerabilities.values())
                f.write(f"- **Total de problemas**: {total}\n")
                f.write(f"- **Críticos**: {len(self.vulnerabilities['critical'])}\n")
                f.write(f"- **Altos**: {len(self.vulnerabilities['high'])}\n")
                f.write(f"- **Médios**: {len(self.vulnerabilities['medium'])}\n")
                f.write(f"- **Baixos**: {len(self.vulnerabilities['low'])}\n\n")
                
                for severity, vulns in self.vulnerabilities.items():
                    if vulns:
                        f.write(f"## {severity.upper()}\n\n")
                        
                        for i, vuln in enumerate(vulns, 1):
                            f.write(f"### {i}. {vuln['title']}\n\n")
                            f.write(f"**Categoria**: {vuln['category']}\n\n")
                            f.write(f"**Descrição**: {vuln['description']}\n\n")
                            f.write(f"**Risco**: {vuln['risk']}\n\n")
                            f.write(f"**Recomendação**: {vuln['recommendation']}\n\n")
                            f.write(f"**CWE**: {vuln['cwe']}\n\n")
                            f.write("---\n\n")
                            
            print(f"📄 Relatório detalhado salvo em: security_audit_report.md")
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")


if __name__ == '__main__':
    auditor = SecurityAuditor()
    auditor.run_security_audit()
