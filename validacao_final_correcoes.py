#!/usr/bin/env python
"""
🔍 VALIDAÇÃO FINAL DA ESTRATÉGIA DE CORREÇÃO
Sistema Move Marias - Teste de URLs Implementadas

Data: 1º de agosto de 2025
Objetivo: Validar que todas as correções críticas foram implementadas com sucesso
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

def print_header():
    print("🔍 VALIDAÇÃO FINAL - ESTRATÉGIA DE CORREÇÃO MOVE MARIAS")
    print("=" * 60)
    print("📅 Data: 1º de agosto de 2025")
    print("🎯 Objetivo: Verificar todas as URLs críticas implementadas")
    print("=" * 60)

def test_url_resolution():
    """Testa se todas as URLs podem ser resolvidas"""
    print("\n📋 TESTE 1: RESOLUÇÃO DE URLs")
    print("-" * 40)
    
    urls_criticas = [
        ('members:import', 'Importação de Beneficiárias'),
        ('members:reports', 'Relatórios de Beneficiárias'),
        ('projects:reports', 'Relatórios de Projetos'),
        ('coaching:sessions', 'Sessões de Coaching'),
        ('coaching:reports', 'Relatórios de Coaching'),
        ('social:anamnesis-create', 'Nova Anamnese Social'),
        ('social:social_reports', 'Relatórios de Anamnese'),
        ('projects:project-list', 'Lista de Projetos'),
        ('projects:project-create', 'Criar Projeto'),
        ('projects:enrollment-list', 'Lista de Inscrições'),
        ('coaching:action-plan-list', 'Lista de Planos de Ação'),
        ('coaching:wheel-list', 'Lista Roda da Vida'),
    ]
    
    success_count = 0
    total_count = len(urls_criticas)
    
    for url_name, description in urls_criticas:
        try:
            url_path = reverse(url_name)
            print(f"✅ {url_name:<30} → {url_path:<25} ({description})")
            success_count += 1
        except NoReverseMatch as e:
            print(f"❌ {url_name:<30} → ERRO: {str(e)[:40]}...")
    
    print("-" * 40)
    percentage = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"📊 RESULTADO: {success_count}/{total_count} URLs resolvidas ({percentage:.1f}%)")
    
    return success_count == total_count

def test_http_access():
    """Testa se as URLs são acessíveis via HTTP"""
    print("\n🌐 TESTE 2: ACESSO HTTP")
    print("-" * 40)
    
    # Criar usuário de teste se não existir
    User = get_user_model()
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print("👤 Usuário admin criado para testes")
    
    client = Client()
    client.force_login(admin_user)
    
    urls_teste = [
        ('members:import', 'GET'),
        ('members:reports', 'GET'),
        ('projects:reports', 'GET'),
        ('coaching:sessions', 'GET'),
        ('coaching:reports', 'GET'),
    ]
    
    success_count = 0
    total_count = len(urls_teste)
    
    for url_name, method in urls_teste:
        try:
            url_path = reverse(url_name)
            response = client.get(url_path)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {url_name:<25} → HTTP {status} (OK)")
                success_count += 1
            elif status in [301, 302]:
                print(f"🔄 {url_name:<25} → HTTP {status} (Redirect)")
                success_count += 1
            else:
                print(f"⚠️  {url_name:<25} → HTTP {status} (Atenção)")
        except Exception as e:
            print(f"❌ {url_name:<25} → ERRO: {str(e)[:40]}...")
    
    print("-" * 40)
    percentage = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"📊 RESULTADO: {success_count}/{total_count} URLs acessíveis ({percentage:.1f}%)")
    
    return success_count == total_count

def test_navigation_system():
    """Testa se o sistema de navegação não gera erros"""
    print("\n🧭 TESTE 3: SISTEMA DE NAVEGAÇÃO")
    print("-" * 40)
    
    try:
        from core.context_processors_enhanced import enhanced_sidebar_context
        from django.http import HttpRequest
        from django.contrib.auth import get_user_model
        
        # Simular request
        request = HttpRequest()
        User = get_user_model()
        request.user = User.objects.get(username='admin')
        
        # Testar context processor
        context = enhanced_sidebar_context(request)
        modules = context.get('sidebar_modules', [])
        
        print(f"📁 Módulos de navegação encontrados: {len(modules)}")
        
        error_count = 0
        for module in modules:
            for child in module.get('children', []):
                if not child.get('url_exists', True):
                    print(f"❌ URL não existe: {child.get('name')} ({child.get('url_name')})")
                    error_count += 1
        
        if error_count == 0:
            print("✅ Sistema de navegação sem erros!")
            return True
        else:
            print(f"⚠️  {error_count} erros encontrados no sistema de navegação")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar navegação: {e}")
        return False

def print_final_report(url_test, http_test, nav_test):
    """Imprime o relatório final"""
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO FINAL DA VALIDAÇÃO")
    print("=" * 60)
    
    tests = [
        ("Resolução de URLs", url_test),
        ("Acesso HTTP", http_test),
        ("Sistema de Navegação", nav_test)
    ]
    
    passed_tests = sum(1 for _, result in tests if result)
    total_tests = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<25} → {status}")
    
    print("-" * 60)
    percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"📊 RESULTADO GERAL: {passed_tests}/{total_tests} testes passaram ({percentage:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 PARABÉNS! TODOS OS TESTES PASSARAM!")
        print("✅ A Fase Crítica foi implementada com SUCESSO TOTAL!")
        print("🚀 O sistema Move Marias está 100% funcional para navegação!")
        return True
    else:
        print("\n⚠️  ATENÇÃO: Alguns testes falharam")
        print("🔧 Revise as implementações que falharam")
        return False

def main():
    """Função principal"""
    print_header()
    
    # Executar testes
    url_test = test_url_resolution()
    http_test = test_http_access()
    nav_test = test_navigation_system()
    
    # Relatório final
    success = print_final_report(url_test, http_test, nav_test)
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
