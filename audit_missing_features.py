#!/usr/bin/env python3
"""
Auditoria de Funcionalidades Não Exibidas na Interface
Identifica módulos, URLs e templates que não estão acessíveis via navegação
"""

import os
import re
from pathlib import Path

def extract_urls_from_file(file_path):
    """Extrai URLs de um arquivo urls.py"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair URLs usando regex
        url_patterns = re.findall(r"path\(['\"]([^'\"]*)['\"],.*name=['\"]([^'\"]*)['\"]", content)
        return url_patterns
    except Exception as e:
        return []

def extract_navigation_urls():
    """Extrai URLs referenciadas na navegação"""
    nav_file = "/workspaces/move/templates/layouts/includes/navigation.html"
    urls_in_nav = set()
    
    try:
        with open(nav_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair URLs do template usando regex
        urls = re.findall(r"{% url ['\"]([^'\"]*)['\"]", content)
        urls_in_nav.update(urls)
        
    except Exception as e:
        print(f"Erro ao ler navegação: {e}")
    
    return urls_in_nav

def audit_missing_functionalities():
    """Auditoria completa de funcionalidades ausentes"""
    print("=== AUDITORIA DE FUNCIONALIDADES NÃO EXIBIDAS ===")
    print()
    
    # URLs na navegação
    nav_urls = extract_navigation_urls()
    print(f"URLs encontradas na navegação: {len(nav_urls)}")
    
    # Mapear todos os módulos
    modules = [
        'activities', 'api', 'certificates', 'chat', 'coaching', 
        'communication', 'core', 'dashboard', 'evolution', 'hr',
        'members', 'notifications', 'projects', 'reports', 'social', 
        'tasks', 'users', 'workshops'
    ]
    
    all_module_urls = {}
    missing_from_nav = {}
    
    for module in modules:
        urls_file = f"/workspaces/move/{module}/urls.py"
        if os.path.exists(urls_file):
            urls = extract_urls_from_file(urls_file)
            all_module_urls[module] = urls
            
            # Verificar quais URLs não estão na navegação
            module_missing = []
            for path, name in urls:
                full_name = f"{module}:{name}"
                if full_name not in nav_urls and name not in nav_urls:
                    module_missing.append((path, name, full_name))
            
            if module_missing:
                missing_from_nav[module] = module_missing
    
    # Relatório de funcionalidades ausentes
    print("=== FUNCIONALIDADES NÃO EXIBIDAS NA INTERFACE ===")
    print()
    
    total_missing = 0
    
    for module, missing_urls in missing_from_nav.items():
        if missing_urls:
            print(f"📂 **{module.upper()}** - {len(missing_urls)} funcionalidades ausentes:")
            for path, name, full_name in missing_urls:
                total_missing += 1
                print(f"   • /{path} (name: {name})")
            print()
    
    print(f"🔴 **TOTAL DE FUNCIONALIDADES AUSENTES: {total_missing}**")
    print()
    
    # Análise por categoria
    print("=== ANÁLISE POR CATEGORIA ===")
    print()
    
    critical_missing = []
    
    # CHAT - Sistema de Chat Interno
    if 'chat' in missing_from_nav:
        print("🗨️  **CHAT INTERNO** - Sistema não acessível via navegação")
        for _, name, full_name in missing_from_nav['chat']:
            critical_missing.append(f"Chat: {name}")
        print("   - Impacto: ALTO - Comunicação interna prejudicada")
        print()
    
    # HR - Recursos Humanos
    if 'hr' in missing_from_nav:
        print("👥 **RECURSOS HUMANOS** - Funcionalidades limitadas")
        hr_missing = missing_from_nav['hr']
        if len(hr_missing) > 4:  # Navegação tem apenas 4 URLs de HR
            print(f"   - {len(hr_missing)} funcionalidades de HR não exibidas")
            critical_missing.extend([f"HR: {name}" for _, name, _ in hr_missing])
        print()
    
    # REPORTS - Sistema de Relatórios
    if 'reports' in missing_from_nav or not any('reports' in module for module in modules):
        print("📊 **RELATÓRIOS** - Sistema de relatórios não implementado")
        print("   - Impacto: ALTO - Análise de dados comprometida")
        critical_missing.append("Reports: Sistema completo")
        print()
    
    # ACTIVITIES - Sistema de Atividades
    if 'activities' in missing_from_nav:
        print("🎯 **ATIVIDADES** - Funcionalidades não exibidas")
        activities_missing = missing_from_nav['activities']
        for _, name, full_name in activities_missing:
            if name not in ['activities_list', 'dashboard']:  # Estas estão na navegação
                critical_missing.append(f"Activities: {name}")
        print()
    
    # API - Endpoints da API
    if 'api' in missing_from_nav:
        print("🔌 **API ENDPOINTS** - Documentação não acessível")
        print("   - Documentação Swagger/OpenAPI pode não estar disponível")
        print("   - Impacto: MÉDIO - Desenvolvimento de integrações dificultado")
        print()
    
    # CORE - Funcionalidades centrais
    if 'core' in missing_from_nav:
        print("⚙️  **FUNCIONALIDADES CENTRAIS** - Recursos do sistema não exibidos")
        core_missing = missing_from_nav['core']
        for _, name, full_name in core_missing:
            if 'upload' in name.lower():
                critical_missing.append(f"Core: {name}")
        print()
    
    # Resumo de impacto
    print("=== RESUMO DE IMPACTO ===")
    print()
    print(f"🔴 **CRÍTICAS**: {len([x for x in critical_missing if 'Chat:' in x or 'Reports:' in x])}")
    print(f"🟡 **ALTAS**: {len([x for x in critical_missing if 'HR:' in x or 'Activities:' in x])}")
    print(f"🟢 **MÉDIAS**: {len([x for x in critical_missing if 'API:' in x or 'Core:' in x])}")
    
    return {
        'total_missing': total_missing,
        'missing_by_module': missing_from_nav,
        'critical_missing': critical_missing,
        'nav_urls': nav_urls,
        'all_urls': all_module_urls
    }

def generate_priority_recommendations():
    """Gera recomendações de prioridade para implementação"""
    print()
    print("=== RECOMENDAÇÕES DE IMPLEMENTAÇÃO ===")
    print()
    
    print("🚨 **PRIORIDADE MÁXIMA:**")
    print("1. Sistema de Chat Interno - Comunicação entre equipes")
    print("2. Sistema de Relatórios - Análise de dados e métricas")
    print("3. Dashboard completo de HR - Gestão de recursos humanos")
    print()
    
    print("⚡ **PRIORIDADE ALTA:**")
    print("4. Funcionalidades completas de Atividades")
    print("5. Sistema de Uploads centralizado")
    print("6. Documentação da API (Swagger)")
    print()
    
    print("📋 **PRIORIDADE MÉDIA:**")
    print("7. Funcionalidades avançadas de Certificados")
    print("8. Sistema de Notificações completo")
    print("9. Relatórios personalizados por módulo")
    print()

if __name__ == "__main__":
    results = audit_missing_functionalities()
    generate_priority_recommendations()
    
    print()
    print("=== PRÓXIMOS PASSOS ===")
    print("1. Implementar navegação para funcionalidades críticas")
    print("2. Criar templates para URLs não acessíveis")
    print("3. Testar todas as funcionalidades após implementação")
    print("4. Documentar URLs e funcionalidades disponíveis")
