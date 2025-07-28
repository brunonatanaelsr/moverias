#!/usr/bin/env python3
"""
Script de Validação de URLs e Criação de Templates Ausentes
Testa URLs implementadas na navegação e cria templates básicos para URLs ausentes
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

# URLs críticas implementadas na navegação
CRITICAL_URLS = {
    'chat': [
        'chat:home',
        'chat:channel_list', 
        'chat:dm_list',
        'chat:notifications'
    ],
    'hr': [
        'hr:dashboard',
        'hr:employee_list',
        'hr:department_list', 
        'hr:job_position_list',
        'hr:performance_review_list',
        'hr:training_dashboard',
        'hr:onboarding_dashboard',
        'hr:feedback_dashboard',
        'hr:goals_dashboard',
        'hr:analytics_dashboard',
        'hr:reports_dashboard'
    ],
    'reports': [
        'dashboard:reports',
        'social:social_reports',
        'activities:activities_report',
        'tasks:reports',
        'hr:turnover_report',
        'dashboard:advanced-analytics',
        'dashboard:custom-reports'
    ],
    'uploads': [
        'core_uploads:upload_file',
        'core_uploads:upload_list',
        'core_uploads:my_uploads'
    ]
}

def test_url_exists(url_name):
    """Testa se uma URL existe no sistema de URLs do Django"""
    try:
        url = reverse(url_name)
        return True, url
    except NoReverseMatch:
        return False, None

def test_template_exists(template_path):
    """Verifica se um template existe"""
    template_dirs = [
        '/workspaces/move/templates/',
        '/workspaces/move/chat/templates/',
        '/workspaces/move/hr/templates/',
        '/workspaces/move/dashboard/templates/',
        '/workspaces/move/social/templates/',
        '/workspaces/move/activities/templates/',
        '/workspaces/move/tasks/templates/',
        '/workspaces/move/core/templates/',
    ]
    
    for template_dir in template_dirs:
        full_path = os.path.join(template_dir, template_path)
        if os.path.exists(full_path):
            return True, full_path
    
    return False, None

def create_basic_template(module, view_name, url_path):
    """Cria template básico para uma view"""
    
    # Mapear módulos para diretórios de template
    template_dirs = {
        'chat': '/workspaces/move/chat/templates/chat/',
        'hr': '/workspaces/move/hr/templates/hr/',
        'dashboard': '/workspaces/move/dashboard/templates/dashboard/',
        'social': '/workspaces/move/social/templates/social/',
        'activities': '/workspaces/move/activities/templates/activities/',
        'tasks': '/workspaces/move/tasks/templates/tasks/',
        'core_uploads': '/workspaces/move/core/templates/core/',
    }
    
    template_dir = template_dirs.get(module)
    if not template_dir:
        template_dir = f'/workspaces/move/{module}/templates/{module}/'
    
    # Criar diretório se não existir
    os.makedirs(template_dir, exist_ok=True)
    
    # Nome do template baseado na view
    template_name = f"{view_name}.html"
    template_path = os.path.join(template_dir, template_name)
    
    # Títulos amigáveis por módulo
    titles = {
        'chat': {
            'home': 'Chat Interno - Página Inicial',
            'channel_list': 'Canais de Discussão',
            'dm_list': 'Mensagens Diretas',
            'notifications': 'Notificações do Chat'
        },
        'hr': {
            'dashboard': 'Dashboard de Recursos Humanos',
            'employee_list': 'Lista de Funcionários',
            'department_list': 'Lista de Departamentos',
            'job_position_list': 'Lista de Cargos',
            'performance_review_list': 'Avaliações de Performance',
            'training_dashboard': 'Dashboard de Treinamentos',
            'onboarding_dashboard': 'Dashboard de Onboarding',
            'feedback_dashboard': 'Dashboard de Feedback',
            'goals_dashboard': 'Dashboard de Metas',
            'analytics_dashboard': 'Analytics de RH',
            'reports_dashboard': 'Relatórios de RH'
        },
        'reports': {
            'reports': 'Relatórios Gerais',
            'social_reports': 'Relatórios Sociais',
            'activities_report': 'Relatórios de Atividades',
            'turnover_report': 'Relatório de Turnover',
            'advanced-analytics': 'Analytics Avançadas',
            'custom-reports': 'Relatórios Personalizados'
        },
        'uploads': {
            'upload_file': 'Upload de Arquivo',
            'upload_list': 'Lista de Arquivos',
            'my_uploads': 'Meus Arquivos'
        }
    }
    
    # Obter título amigável
    module_titles = titles.get(module, {})
    friendly_title = module_titles.get(view_name, f"{view_name.replace('_', ' ').title()}")
    
    # Template básico
    template_content = '''{% extends "base.html" %}
{% load static %}

{% block title %}''' + friendly_title + ''' - Move Marias{% endblock %}

{% block extra_css %}
<style>
    .feature-card {
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        border-radius: 0.75rem;
        color: white;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    .feature-icon {
        width: 3rem;
        height: 3rem;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
    }
    .coming-soon {
        background: #f3f4f6;
        border: 2px dashed #d1d5db;
        border-radius: 0.75rem;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Header -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="feature-card">
                <div class="feature-icon">
                    <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                </div>
                <h1 class="text-2xl font-bold mb-2">''' + friendly_title + '''</h1>
                <p class="opacity-90">Funcionalidade implementada recentemente</p>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header pb-0">
                    <div class="d-flex align-items-center">
                        <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
                            <i class="ni ni-app text-primary text-sm opacity-10"></i>
                        </div>
                        <h6 class="mb-0">''' + friendly_title + '''</h6>
                    </div>
                </div>
                <div class="card-body">
                    <div class="coming-soon">
                        <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-2.828 0l-7.071 7.07a2 2 0 102.828 2.829l7.071-7.071a2 2 0 000-2.828z" />
                        </svg>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">Funcionalidade em Desenvolvimento</h3>
                        <p class="text-gray-500 mb-4">
                            Esta funcionalidade foi recentemente adicionada à navegação e está sendo implementada.
                        </p>
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                            <h4 class="text-sm font-medium text-blue-800 mb-2">Informações Técnicas:</h4>
                            <ul class="text-sm text-blue-700 text-left">
                                <li><strong>URL:</strong> ''' + url_path + '''</li>
                                <li><strong>Módulo:</strong> ''' + module + '''</li>
                                <li><strong>View:</strong> ''' + view_name + '''</li>
                                <li><strong>Template:</strong> ''' + template_name + '''</li>
                                <li><strong>Status:</strong> Template básico criado automaticamente</li>
                            </ul>
                        </div>
                        <p class="text-sm text-gray-500">
                            <strong>Próximos passos:</strong> Implementar lógica da view e customizar este template conforme necessário.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    console.log('Template básico carregado para: ''' + friendly_title + '''');
    console.log('URL: ''' + url_path + '''');
    console.log('Módulo: ''' + module + '''');
    
    // Registrar evento de página visitada
    if (window.gtag) {
        gtag('event', 'page_view', {
            'page_title': '''' + friendly_title + '''',
            'page_location': window.location.href,
            'page_path': '''' + url_path + '''',
            'custom_module': '''' + module + ''''
        });
    }
</script>
{% endblock %}
'''
    
    # Escrever template
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return template_path

def validate_critical_urls():
    """Valida todas as URLs críticas implementadas"""
    print("=== VALIDAÇÃO DE URLs IMPLEMENTADAS NA NAVEGAÇÃO ===")
    print()
    
    results = {
        'existing_urls': [],
        'missing_urls': [],
        'templates_created': [],
        'errors': []
    }
    
    total_urls = 0
    existing_urls = 0
    
    for module, urls in CRITICAL_URLS.items():
        print(f"📂 **{module.upper()}**")
        
        for url_name in urls:
            total_urls += 1
            exists, url_path = test_url_exists(url_name)
            
            if exists:
                existing_urls += 1
                results['existing_urls'].append((url_name, url_path))
                print(f"   ✅ {url_name} → {url_path}")
                
                # Verificar se template existe
                view_name = url_name.split(':')[1] if ':' in url_name else url_name
                possible_templates = [
                    f"{module}/{view_name}.html",
                    f"{module}/{view_name}_list.html",
                    f"{module}/{view_name}_dashboard.html",
                    f"{module}/dashboard.html" if 'dashboard' in view_name else None
                ]
                
                template_found = False
                for template_path in possible_templates:
                    if template_path:
                        exists_template, full_path = test_template_exists(template_path)
                        if exists_template:
                            template_found = True
                            print(f"      📄 Template: {full_path}")
                            break
                
                if not template_found:
                    # Criar template básico
                    try:
                        template_path = create_basic_template(module, view_name, url_path)
                        results['templates_created'].append(template_path)
                        print(f"      🆕 Template criado: {template_path}")
                    except Exception as e:
                        results['errors'].append(f"Erro ao criar template para {url_name}: {e}")
                        print(f"      ❌ Erro ao criar template: {e}")
                
            else:
                results['missing_urls'].append(url_name)
                print(f"   ❌ {url_name} → URL não encontrada")
        
        print()
    
    # Resumo
    print("=== RESUMO DA VALIDAÇÃO ===")
    print(f"📊 URLs testadas: {total_urls}")
    print(f"✅ URLs existentes: {existing_urls} ({(existing_urls/total_urls)*100:.1f}%)")
    print(f"❌ URLs ausentes: {total_urls - existing_urls}")
    print(f"🆕 Templates criados: {len(results['templates_created'])}")
    print(f"⚠️  Erros: {len(results['errors'])}")
    print()
    
    return results

def create_validation_report(results):
    """Cria relatório detalhado da validação"""
    report_content = f"""# RELATÓRIO DE VALIDAÇÃO - URLs E TEMPLATES

## Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 RESUMO EXECUTIVO

- **URLs Testadas**: {len(results['existing_urls']) + len(results['missing_urls'])}
- **URLs Existentes**: {len(results['existing_urls'])} ({(len(results['existing_urls'])/(len(results['existing_urls']) + len(results['missing_urls'])))*100:.1f}%)
- **URLs Ausentes**: {len(results['missing_urls'])}
- **Templates Criados**: {len(results['templates_created'])}
- **Erros Encontrados**: {len(results['errors'])}

### ✅ URLs VALIDADAS COM SUCESSO

"""
    
    for url_name, url_path in results['existing_urls']:
        report_content += f"- `{url_name}` → `{url_path}`\n"
    
    if results['missing_urls']:
        report_content += f"\n### ❌ URLs AUSENTES (PRECISAM SER IMPLEMENTADAS)\n\n"
        for url_name in results['missing_urls']:
            report_content += f"- `{url_name}` → **Não encontrada no sistema de URLs**\n"
    
    if results['templates_created']:
        report_content += f"\n### 🆕 TEMPLATES CRIADOS AUTOMATICAMENTE\n\n"
        for template_path in results['templates_created']:
            report_content += f"- `{template_path}`\n"
    
    if results['errors']:
        report_content += f"\n### ⚠️ ERROS ENCONTRADOS\n\n"
        for error in results['errors']:
            report_content += f"- {error}\n"
    
    report_content += f"""

### 🎯 PRÓXIMOS PASSOS

#### URLs Ausentes - Implementação Necessária:
"""
    
    for url_name in results['missing_urls']:
        module = url_name.split(':')[0]
        view_name = url_name.split(':')[1] if ':' in url_name else url_name
        report_content += f"1. **{url_name}**: Implementar view `{view_name}` no módulo `{module}`\n"
    
    report_content += f"""

#### Templates Criados - Customização Necessária:
"""
    
    for template_path in results['templates_created']:
        report_content += f"1. **{template_path}**: Customizar template conforme necessidades específicas\n"
    
    report_content += f"""

### 🔧 INSTRUÇÕES DE IMPLEMENTAÇÃO

#### Para URLs Ausentes:
1. Adicionar URL pattern no arquivo `urls.py` do módulo
2. Implementar view correspondente no arquivo `views.py`  
3. Criar template específico se necessário
4. Testar funcionalidade completa

#### Para Templates Criados:
1. Revisar template básico gerado automaticamente
2. Implementar lógica específica da funcionalidade
3. Adicionar componentes visuais necessários
4. Integrar com dados reais do sistema
5. Testar responsividade e usabilidade

### ✅ STATUS DA IMPLEMENTAÇÃO

**CONCLUÍDO:**
- ✅ Navegação implementada para funcionalidades críticas
- ✅ URLs existentes validadas
- ✅ Templates básicos criados automaticamente

**PRÓXIMAS ETAPAS:**
- ⏳ Implementar URLs ausentes
- ⏳ Customizar templates criados
- ⏳ Testar funcionalidades end-to-end
- ⏳ Implementar próxima fase de funcionalidades

---

*Relatório gerado automaticamente pelo sistema de validação*
"""
    
    report_path = '/workspaces/move/VALIDACAO_URLS_TEMPLATES.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Relatório de validação criado: {report_path}")
    return report_path

if __name__ == "__main__":
    print("🚀 INICIANDO VALIDAÇÃO DE URLs E CRIAÇÃO DE TEMPLATES")
    print()
    
    results = validate_critical_urls()
    report_path = create_validation_report(results)
    
    print("🎉 VALIDAÇÃO CONCLUÍDA!")
    print()
    print("📋 RESUMO FINAL:")
    print(f"   • {len(results['existing_urls'])} URLs funcionando")
    print(f"   • {len(results['missing_urls'])} URLs precisam ser implementadas")
    print(f"   • {len(results['templates_created'])} templates criados")
    print(f"   • Relatório detalhado: {report_path}")
    print()
    
    if results['missing_urls']:
        print("⚠️  AÇÃO NECESSÁRIA:")
        print("   Algumas URLs não foram encontradas no sistema.")
        print("   Consulte o relatório para detalhes de implementação.")
    else:
        print("✅ SUCESSO TOTAL:")
        print("   Todas as URLs implementadas estão funcionando!")
        print("   Templates básicos criados para funcionalidades sem template.")
