# SCRIPTS E COMANDOS PARA IMPLEMENTAÇÃO DOS AJUSTES

## Documento Técnico Complementar ao Plano de Ajustes
**Data:** 28 de Julho de 2025  
**Versão:** 1.0  

---

## 1. SCRIPTS DE AUDITORIA E DIAGNÓSTICO

### 1.1 Auditoria de URLs

```bash
#!/bin/bash
# audit_urls.sh - Script para identificar inconsistências de URLs

echo "=== AUDITORIA DE URLs DO SISTEMA MOVE MARIAS ==="
echo "Data: $(date)"
echo ""

echo "1. URLs definidas em arquivos urls.py:"
echo "----------------------------------------"
find . -name "urls.py" -exec echo "=== {} ===" \; -exec grep -n "name=" {} \;

echo ""
echo "2. URLs referenciadas em templates:"
echo "-----------------------------------"
find templates/ -name "*.html" -exec grep -l "{% url" {} \; | while read file; do
    echo "=== $file ==="
    grep -n "{% url" "$file"
done

echo ""
echo "3. Possíveis inconsistências:"
echo "-----------------------------"
# Extrair nomes de URLs dos templates
grep -r "{% url" templates/ | sed "s/.*{% url ['\"]//g" | sed "s/['\"].*//g" | sort | uniq > /tmp/template_urls.txt

# Extrair nomes de URLs dos arquivos urls.py
find . -name "urls.py" -exec grep -h "name=" {} \; | sed "s/.*name=['\"]//g" | sed "s/['\"].*//g" | sort | uniq > /tmp/defined_urls.txt

echo "URLs usadas em templates mas não definidas:"
comm -23 /tmp/template_urls.txt /tmp/defined_urls.txt

echo ""
echo "URLs definidas mas não usadas:"
comm -13 /tmp/template_urls.txt /tmp/defined_urls.txt

# Cleanup
rm -f /tmp/template_urls.txt /tmp/defined_urls.txt
```

### 1.2 Identificação de Arquivos Duplicados

```python
#!/usr/bin/env python3
# find_duplicates.py - Identifica arquivos duplicados/redundantes

import os
import glob
import hashlib

def get_file_hash(filepath):
    """Calcula hash MD5 de um arquivo"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicate_files():
    """Encontra arquivos duplicados por conteúdo"""
    files_hash = {}
    duplicates = []
    
    patterns = ['**/*.py', '**/*.html', '**/*.css', '**/*.js']
    
    for pattern in patterns:
        for filepath in glob.glob(pattern, recursive=True):
            if os.path.isfile(filepath):
                file_hash = get_file_hash(filepath)
                if file_hash in files_hash:
                    duplicates.append((files_hash[file_hash], filepath))
                else:
                    files_hash[file_hash] = filepath
    
    return duplicates

def find_similar_names():
    """Encontra arquivos com nomes similares que podem ser duplicatas"""
    similar_files = {}
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.html')):
                base_name = file.split('.')[0]
                if '_' in base_name:
                    key = base_name.split('_')[0]
                    if key not in similar_files:
                        similar_files[key] = []
                    similar_files[key].append(os.path.join(root, file))
    
    return {k: v for k, v in similar_files.items() if len(v) > 1}

if __name__ == "__main__":
    print("=== ANÁLISE DE ARQUIVOS DUPLICADOS ===")
    print()
    
    print("1. Arquivos com conteúdo idêntico:")
    print("-" * 40)
    duplicates = find_duplicate_files()
    for original, duplicate in duplicates:
        print(f"Original: {original}")
        print(f"Duplicata: {duplicate}")
        print()
    
    print("2. Arquivos com nomes similares:")
    print("-" * 40)
    similar = find_similar_names()
    for base_name, files in similar.items():
        print(f"Base: {base_name}")
        for file in files:
            print(f"  - {file}")
        print()
```

---

## 2. SCRIPTS DE CORREÇÃO

### 2.1 Correção Automática de URLs

```python
#!/usr/bin/env python3
# fix_urls.py - Corrige inconsistências de URLs automaticamente

import os
import re
import argparse

# Mapeamento de URLs incorretas para corretas
URL_CORRECTIONS = {
    'communication:announcement_list': 'communication:announcements_list',
    'communication:message_list': 'communication:messages_list',
    'communication:memo_list': 'communication:memos_list',
    'social:anamnese_list': 'social:anamnesis_list',
    'hr:position_list': 'hr:positions_list',
    # Adicionar mais correções conforme necessário
}

def fix_template_urls(file_path, dry_run=True):
    """Corrige URLs em templates"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    for incorrect, correct in URL_CORRECTIONS.items():
        pattern = r"{% url ['\"]" + re.escape(incorrect) + r"['\"]"
        replacement = "{% url '" + correct + "'"
        
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes_made.append(f"{incorrect} -> {correct}")
            content = new_content
    
    if changes_made and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes_made

def process_templates(dry_run=True):
    """Processa todos os templates"""
    print(f"=== CORREÇÃO DE URLs {'(DRY RUN)' if dry_run else '(EXECUTANDO)'} ===")
    print()
    
    total_files = 0
    total_changes = 0
    
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                changes = fix_template_urls(file_path, dry_run)
                
                if changes:
                    total_files += 1
                    total_changes += len(changes)
                    print(f"Arquivo: {file_path}")
                    for change in changes:
                        print(f"  - {change}")
                    print()
    
    print(f"Resumo: {total_changes} mudanças em {total_files} arquivos")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Corrige URLs em templates')
    parser.add_argument('--execute', action='store_true', 
                       help='Executa as correções (padrão é dry-run)')
    
    args = parser.parse_args()
    process_templates(dry_run=not args.execute)
```

### 2.2 Script de População de Dados

```python
#!/usr/bin/env python3
# populate_demo_data.py - Command Django para popular dados de demonstração

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o sistema com dados de demonstração'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                          help='Limpa dados existentes antes de popular')
        parser.add_argument('--module', type=str, choices=['all', 'social', 'communication', 'certificates', 'hr'],
                          default='all', help='Módulo específico para popular')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_demo_data()
        
        module = options['module']
        
        if module in ['all', 'social']:
            self.populate_social_data()
        
        if module in ['all', 'communication']:
            self.populate_communication_data()
        
        if module in ['all', 'certificates']:
            self.populate_certificates_data()
        
        if module in ['all', 'hr']:
            self.populate_hr_data()
        
        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados com sucesso!'))

    def clear_demo_data(self):
        """Remove dados de demonstração existentes"""
        from members.models import Member
        from social.models import Anamnesis
        from communication.models import Announcement
        # Adicionar outros modelos conforme necessário
        
        self.stdout.write('Limpando dados existentes...')
        
        # Limpar apenas dados de demo (com flag específica ou criados pelo script)
        Member.objects.filter(is_demo=True).delete()
        Anamnesis.objects.filter(is_demo=True).delete()
        Announcement.objects.filter(is_demo=True).delete()

    def populate_social_data(self):
        """Popula dados do módulo social"""
        from members.models import Member
        from social.models import Anamnesis
        
        self.stdout.write('Criando dados do módulo social...')
        
        # Criar beneficiárias de exemplo
        beneficiaries = [
            {
                'name': 'Maria da Silva Santos',
                'email': 'maria.santos@email.com',
                'cpf': '123.456.789-10',
                'birth_date': '1985-03-15',
                'phone': '(11) 98765-4321'
            },
            {
                'name': 'Ana Carolina Oliveira',
                'email': 'ana.oliveira@email.com',
                'cpf': '987.654.321-09',
                'birth_date': '1992-07-22',
                'phone': '(11) 99876-5432'
            },
            # Adicionar mais exemplos...
        ]
        
        created_members = []
        for data in beneficiaries:
            member, created = Member.objects.get_or_create(
                cpf=data['cpf'],
                defaults={
                    **data,
                    'is_demo': True,
                    'status': 'active'
                }
            )
            if created:
                created_members.append(member)
        
        # Criar anamneses de exemplo
        for member in created_members:
            Anamnesis.objects.create(
                member=member,
                personal_data={
                    'marital_status': random.choice(['single', 'married', 'divorced']),
                    'education': random.choice(['elementary', 'high_school', 'college']),
                    'children_count': random.randint(0, 4)
                },
                economic_data={
                    'monthly_income': random.randint(1000, 5000),
                    'income_sources': ['job', 'government_aid'],
                    'expenses': random.randint(800, 4500)
                },
                vulnerabilities={
                    'domestic_violence': random.choice([True, False]),
                    'unemployment': random.choice([True, False]),
                    'health_issues': random.choice([True, False])
                },
                is_demo=True,
                created_at=timezone.now() - timedelta(days=random.randint(1, 60))
            )
        
        self.stdout.write(f'Criados {len(created_members)} beneficiárias e anamneses')

    def populate_communication_data(self):
        """Popula dados do módulo de comunicação"""
        from communication.models import Announcement
        
        self.stdout.write('Criando dados do módulo de comunicação...')
        
        announcements = [
            {
                'title': 'Novo Workshop de Empreendedorismo',
                'content': 'Participe do nosso workshop sobre empreendedorismo feminino...',
                'category': 'workshop',
                'priority': 'high'
            },
            {
                'title': 'Alteração no Horário de Atendimento',
                'content': 'Informamos que o horário de atendimento foi alterado...',
                'category': 'general',
                'priority': 'medium'
            },
            # Adicionar mais exemplos...
        ]
        
        for data in announcements:
            Announcement.objects.create(
                **data,
                author=User.objects.filter(is_staff=True).first(),
                is_demo=True,
                publish_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                is_active=True
            )
        
        self.stdout.write(f'Criados {len(announcements)} comunicados')

    def populate_certificates_data(self):
        """Popula dados do módulo de certificados"""
        # Implementar criação de certificados de exemplo
        pass

    def populate_hr_data(self):
        """Popula dados do módulo de RH"""
        # Implementar criação de dados de RH de exemplo
        pass
```

---

## 3. SCRIPTS DE CONSOLIDAÇÃO

### 3.1 Consolidação de Views

```python
#!/usr/bin/env python3
# consolidate_views.py - Consolida arquivos de views duplicados

import os
import shutil
import ast
import argparse
from datetime import datetime

def backup_files(files_to_backup):
    """Cria backup dos arquivos antes da consolidação"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, file_path.replace('/', '_'))
            shutil.copy2(file_path, backup_path)
    
    return backup_dir

def analyze_view_functions(file_path):
    """Analisa funções em um arquivo de views"""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            print(f"Erro de sintaxe em {file_path}")
            return []
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                'name': node.name,
                'line': node.lineno,
                'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
            })
    
    return functions

def consolidate_communication_views():
    """Consolida views do módulo de comunicação"""
    base_path = "communication"
    view_files = [
        f"{base_path}/views.py",
        f"{base_path}/views_simple.py",
        f"{base_path}/views_integrated.py",
        f"{base_path}/views_refactored.py"
    ]
    
    print("=== CONSOLIDAÇÃO DE VIEWS - COMUNICAÇÃO ===")
    print()
    
    # Análise dos arquivos
    all_functions = {}
    for file_path in view_files:
        if os.path.exists(file_path):
            functions = analyze_view_functions(file_path)
            all_functions[file_path] = functions
            print(f"{file_path}: {len(functions)} funções")
            for func in functions:
                print(f"  - {func['name']} (linha {func['line']})")
            print()
    
    # Identificar função principal (views_simple.py parece ser a versão ativa)
    main_file = f"{base_path}/views_simple.py"
    if os.path.exists(main_file):
        print(f"Usando {main_file} como arquivo principal")
        
        # Criar backup
        backup_dir = backup_files(view_files)
        print(f"Backup criado em: {backup_dir}")
        
        # Renomear arquivo principal
        shutil.copy2(main_file, f"{base_path}/views.py")
        print(f"Copiado {main_file} para views.py")
        
        # Mover outros arquivos para legacy
        legacy_dir = f"{base_path}/legacy"
        os.makedirs(legacy_dir, exist_ok=True)
        
        for file_path in view_files:
            if file_path != main_file and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                legacy_path = os.path.join(legacy_dir, filename)
                shutil.move(file_path, legacy_path)
                print(f"Movido {file_path} para {legacy_path}")

def consolidate_all_modules():
    """Consolida views de todos os módulos"""
    modules = ['communication', 'social', 'projects']  # Adicionar conforme necessário
    
    for module in modules:
        if os.path.exists(module):
            print(f"\n=== PROCESSANDO MÓDULO: {module.upper()} ===")
            # Implementar lógica específica para cada módulo
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Consolida arquivos de views duplicados')
    parser.add_argument('--module', type=str, choices=['all', 'communication', 'social', 'projects'],
                       default='communication', help='Módulo para consolidar')
    parser.add_argument('--dry-run', action='store_true', help='Simula a consolidação sem executar')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("=== MODO DRY-RUN - SIMULAÇÃO ===")
    
    if args.module == 'communication':
        consolidate_communication_views()
    elif args.module == 'all':
        consolidate_all_modules()
```

---

## 4. SCRIPTS DE VALIDAÇÃO

### 4.1 Teste de Navegação

```python
#!/usr/bin/env python3
# test_navigation.py - Testa todas as URLs do sistema

import requests
import time
import json
from urllib.parse import urljoin

class NavigationTester:
    def __init__(self, base_url="http://localhost:8000", session_cookie=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        if session_cookie:
            self.session.cookies.set('sessionid', session_cookie)
    
    def login(self, username, password):
        """Faz login no sistema"""
        login_url = urljoin(self.base_url, '/accounts/login/')
        
        # Obter CSRF token
        response = self.session.get(login_url)
        csrf_token = self.extract_csrf_token(response.text)
        
        # Fazer login
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = self.session.post(login_url, data=login_data)
        return response.status_code == 302  # Redirect após login bem-sucedido
    
    def extract_csrf_token(self, html):
        """Extrai CSRF token do HTML"""
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', html)
        return match.group(1) if match else None
    
    def test_urls(self, urls):
        """Testa uma lista de URLs"""
        results = []
        
        for url in urls:
            full_url = urljoin(self.base_url, url)
            
            try:
                start_time = time.time()
                response = self.session.get(full_url, timeout=10)
                end_time = time.time()
                
                results.append({
                    'url': url,
                    'status_code': response.status_code,
                    'response_time': round(end_time - start_time, 2),
                    'content_length': len(response.content),
                    'has_error': 'error' in response.text.lower() or 'exception' in response.text.lower()
                })
                
            except Exception as e:
                results.append({
                    'url': url,
                    'status_code': 'ERROR',
                    'response_time': 0,
                    'content_length': 0,
                    'error': str(e),
                    'has_error': True
                })
            
            time.sleep(0.1)  # Evitar sobrecarga
        
        return results
    
    def generate_report(self, results):
        """Gera relatório dos testes"""
        print("=== RELATÓRIO DE TESTES DE NAVEGAÇÃO ===")
        print(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total de URLs testadas: {len(results)}")
        print()
        
        success_count = len([r for r in results if r['status_code'] == 200])
        error_count = len([r for r in results if r['status_code'] != 200])
        
        print(f"✅ Sucessos: {success_count}")
        print(f"❌ Erros: {error_count}")
        print()
        
        if error_count > 0:
            print("URLS COM PROBLEMAS:")
            print("-" * 50)
            for result in results:
                if result['status_code'] != 200:
                    print(f"URL: {result['url']}")
                    print(f"Status: {result['status_code']}")
                    if 'error' in result:
                        print(f"Erro: {result['error']}")
                    print()
        
        print("PERFORMANCE:")
        print("-" * 20)
        response_times = [r['response_time'] for r in results if isinstance(r['response_time'], (int, float))]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"Tempo médio: {avg_time:.2f}s")
            print(f"Tempo máximo: {max_time:.2f}s")

# URLs principais para testar
MAIN_URLS = [
    '/',
    '/dashboard/',
    '/accounts/login/',
    '/social/',
    '/social/anamnesis/',
    '/communication/',
    '/communication/announcements/',
    '/certificates/',
    '/hr/',
    '/projects/',
    '/coaching/',
    '/activities/',
    '/api/docs/',
]

if __name__ == "__main__":
    tester = NavigationTester()
    
    # Login se necessário
    # if tester.login('admin', 'password'):
    #     print("Login realizado com sucesso")
    
    results = tester.test_urls(MAIN_URLS)
    tester.generate_report(results)
    
    # Salvar resultados em JSON
    with open('navigation_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
```

---

## 5. COMANDOS DE EXECUÇÃO

### 5.1 Sequência de Execução Recomendada

```bash
#!/bin/bash
# execute_fixes.sh - Script principal para executar todas as correções

set -e  # Parar em caso de erro

echo "=== INICIANDO CORREÇÕES DO SISTEMA MOVE MARIAS ==="
echo "Data: $(date)"
echo ""

# 1. Backup completo
echo "1. Criando backup completo..."
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r . backups/$(date +%Y%m%d_%H%M%S)/

# 2. Auditoria inicial
echo "2. Executando auditoria inicial..."
bash scripts/audit_urls.sh > reports/audit_initial.txt
python3 scripts/find_duplicates.py > reports/duplicates_analysis.txt

# 3. Correções de URLs
echo "3. Corrigindo URLs..."
python3 scripts/fix_urls.py --execute

# 4. Consolidação de código
echo "4. Consolidando código duplicado..."
python3 scripts/consolidate_views.py --module communication

# 5. População de dados
echo "5. Criando dados de demonstração..."
python3 manage.py populate_demo_data --clear --module all

# 6. Testes de validação
echo "6. Executando testes de validação..."
python3 scripts/test_navigation.py

# 7. Coleta de arquivos estáticos
echo "7. Coletando arquivos estáticos..."
python3 manage.py collectstatic --noinput

# 8. Verificação final
echo "8. Verificação final..."
python3 manage.py check
python3 scripts/audit_urls.sh > reports/audit_final.txt

echo ""
echo "=== CORREÇÕES CONCLUÍDAS ==="
echo "Verifique os relatórios em: reports/"
echo "Backup disponível em: backups/"
```

### 5.2 Comandos Individuais

```bash
# Auditoria rápida
bash scripts/audit_urls.sh

# Correção de URLs (simulação)
python3 scripts/fix_urls.py

# Correção de URLs (execução)
python3 scripts/fix_urls.py --execute

# População de dados específicos
python3 manage.py populate_demo_data --module social
python3 manage.py populate_demo_data --module communication

# Consolidação de módulo específico
python3 scripts/consolidate_views.py --module communication

# Teste de navegação
python3 scripts/test_navigation.py

# Verificação de sistema
python3 manage.py check --deploy
```

---

## 6. MONITORAMENTO PÓS-IMPLEMENTAÇÃO

### 6.1 Script de Monitoramento

```python
#!/usr/bin/env python3
# monitor_system.py - Monitora saúde do sistema após correções

import requests
import time
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class SystemMonitor:
    def __init__(self, config_file="monitor_config.json"):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
    
    def check_urls(self):
        """Verifica se URLs principais estão funcionando"""
        results = []
        
        for url in self.config['urls_to_monitor']:
            try:
                response = requests.get(url, timeout=10)
                results.append({
                    'url': url,
                    'status': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def check_database(self):
        """Verifica conexão com banco de dados"""
        # Implementar verificação de DB
        pass
    
    def send_alert(self, message):
        """Envia alerta por email"""
        if not self.config.get('email_alerts', {}).get('enabled', False):
            return
        
        # Implementar envio de email
        pass
    
    def run_monitoring_cycle(self):
        """Executa um ciclo completo de monitoramento"""
        print(f"Iniciando monitoramento - {datetime.now()}")
        
        url_results = self.check_urls()
        
        # Verificar se há problemas
        errors = [r for r in url_results if r['status'] != 200]
        
        if errors:
            print(f"ALERTA: {len(errors)} URLs com problemas")
            for error in errors:
                print(f"  - {error['url']}: {error['status']}")
        else:
            print("✅ Todas as URLs estão funcionando")
        
        # Salvar resultados
        with open(f"monitoring_results_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
            json.dump(url_results, f, indent=2)

# Configuração de exemplo
MONITOR_CONFIG = {
    "urls_to_monitor": [
        "http://localhost:8000/",
        "http://localhost:8000/dashboard/",
        "http://localhost:8000/communication/announcements/",
        "http://localhost:8000/social/anamnesis/"
    ],
    "email_alerts": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "recipients": ["admin@movemarias.org"]
    }
}

if __name__ == "__main__":
    # Criar arquivo de configuração se não existir
    if not os.path.exists("monitor_config.json"):
        with open("monitor_config.json", 'w') as f:
            json.dump(MONITOR_CONFIG, f, indent=2)
    
    monitor = SystemMonitor()
    monitor.run_monitoring_cycle()
```

---

## 7. CHECKLIST DE VALIDAÇÃO

### 7.1 Checklist Pós-Correções

```bash
#!/bin/bash
# validation_checklist.sh - Checklist de validação pós-correções

echo "=== CHECKLIST DE VALIDAÇÃO - SISTEMA MOVE MARIAS ==="
echo ""

# Função para verificar URL
check_url() {
    local url=$1
    local expected_status=${2:-200}
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "ERROR")
    
    if [ "$status" = "$expected_status" ]; then
        echo "✅ $url - Status: $status"
        return 0
    else
        echo "❌ $url - Status: $status (esperado: $expected_status)"
        return 1
    fi
}

# Verificações de URL
echo "1. VERIFICAÇÃO DE URLs:"
echo "----------------------"

BASE_URL="http://localhost:8000"
URLS=(
    "/"
    "/dashboard/"
    "/communication/"
    "/communication/announcements/"
    "/social/"
    "/social/anamnesis/"
    "/certificates/"
    "/hr/"
    "/projects/"
    "/api/docs/"
)

url_failures=0
for url in "${URLS[@]}"; do
    if ! check_url "$BASE_URL$url"; then
        ((url_failures++))
    fi
done

echo ""
echo "2. VERIFICAÇÃO DE DADOS DE DEMONSTRAÇÃO:"
echo "----------------------------------------"

# Verificar se dados de demo foram criados
python3 -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from members.models import Member
from communication.models import Announcement

demo_members = Member.objects.filter(is_demo=True).count()
demo_announcements = Announcement.objects.filter(is_demo=True).count()

print(f'Membros demo: {demo_members}')
print(f'Comunicados demo: {demo_announcements}')

if demo_members > 0:
    print('✅ Dados de demonstração - Membros criados')
else:
    print('❌ Dados de demonstração - Membros não encontrados')

if demo_announcements > 0:
    print('✅ Dados de demonstração - Comunicados criados')
else:
    print('❌ Dados de demonstração - Comunicados não encontrados')
"

echo ""
echo "3. VERIFICAÇÃO DE ARQUIVOS CONSOLIDADOS:"
echo "---------------------------------------"

# Verificar se arquivos foram consolidados
if [ -d "communication/legacy" ]; then
    echo "✅ Arquivos legacy movidos para communication/legacy/"
else
    echo "❌ Pasta legacy não encontrada"
fi

# Verificar se views principal existe
if [ -f "communication/views.py" ]; then
    echo "✅ Views principal existe: communication/views.py"
else
    echo "❌ Views principal não encontrado"
fi

echo ""
echo "4. VERIFICAÇÃO DE SISTEMA:"
echo "-------------------------"

# Django check
if python3 manage.py check --quiet; then
    echo "✅ Django system check passou"
else
    echo "❌ Django system check falhou"
fi

# Verificar migrações
if python3 manage.py showmigrations --plan | grep -q "No migrations"; then
    echo "✅ Todas as migrações aplicadas"
else
    echo "⚠️  Verificar migrações pendentes"
fi

echo ""
echo "=== RESUMO DA VALIDAÇÃO ==="

if [ $url_failures -eq 0 ]; then
    echo "✅ URLs: Todas funcionando"
else
    echo "❌ URLs: $url_failures com problemas"
fi

echo ""
echo "Para mais detalhes, verifique os logs em:"
echo "- reports/audit_final.txt"
echo "- navigation_test_results.json"
echo "- monitoring_results_$(date +%Y%m%d).json"
```

---

## 8. DOCUMENTAÇÃO DE EXECUÇÃO

Para executar o plano completo:

1. **Preparação:**
   ```bash
   chmod +x scripts/*.sh
   mkdir -p reports backups
   ```

2. **Execução completa:**
   ```bash
   bash scripts/execute_fixes.sh
   ```

3. **Validação:**
   ```bash
   bash scripts/validation_checklist.sh
   ```

4. **Monitoramento contínuo:**
   ```bash
   python3 scripts/monitor_system.py
   ```

Este documento fornece todas as ferramentas necessárias para implementar as correções identificadas no plano de ajustes do sistema.
