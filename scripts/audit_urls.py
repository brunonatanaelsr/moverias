#!/usr/bin/env python3
"""
Script de auditoria completa de URLs do sistema Move Marias
Identifica inconsistências entre URLs definidas e referenciadas
"""

import os
import re
import glob
from collections import defaultdict

def extract_url_patterns():
    """Extrai todos os padrões de URL definidos nos arquivos urls.py"""
    url_patterns = {}
    
    # Encontrar todos os arquivos urls.py
    urls_files = glob.glob('**/urls.py', recursive=True)
    
    for file_path in urls_files:
        module_name = os.path.dirname(file_path)
        if module_name == '':
            module_name = 'root'
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extrair app_name se existir
            app_name_match = re.search(r"app_name\s*=\s*['\"](\w+)['\"]", content)
            app_name = app_name_match.group(1) if app_name_match else None
            
            # Extrair padrões de URL com name
            pattern = r"path\([^,]+,\s*[^,]+,\s*name=['\"]([^'\"]+)['\"]"
            url_names = re.findall(pattern, content)
            
            if app_name:
                full_names = [f"{app_name}:{name}" for name in url_names]
            else:
                full_names = url_names
                
            url_patterns[module_name] = {
                'app_name': app_name,
                'file_path': file_path,
                'url_names': url_names,
                'full_names': full_names
            }
            
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
    
    return url_patterns

def extract_url_references():
    """Extrai todas as referências a URLs nos templates"""
    url_references = defaultdict(list)
    
    # Encontrar todos os templates HTML
    template_files = glob.glob('**/templates/**/*.html', recursive=True)
    
    for file_path in template_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extrair {% url 'name' %}
            url_refs = re.findall(r"{%\s*url\s+['\"]([^'\"]+)['\"]", content)
            
            for url_ref in url_refs:
                url_references[url_ref].append(file_path)
                
        except Exception as e:
            print(f"Erro ao processar template {file_path}: {e}")
    
    return url_references

def find_inconsistencies(url_patterns, url_references):
    """Encontra inconsistências entre URLs definidas e referenciadas"""
    
    # Criar lista de todas as URLs definidas
    all_defined_urls = set()
    for module_data in url_patterns.values():
        all_defined_urls.update(module_data['full_names'])
        all_defined_urls.update(module_data['url_names'])
    
    # Encontrar URLs referenciadas mas não definidas
    undefined_refs = []
    for url_ref, files in url_references.items():
        if url_ref not in all_defined_urls:
            undefined_refs.append({
                'url': url_ref,
                'files': files
            })
    
    # Encontrar URLs definidas mas nunca referenciadas
    unused_urls = []
    for url in all_defined_urls:
        if url not in url_references:
            unused_urls.append(url)
    
    return undefined_refs, unused_urls

def suggest_url_standardization():
    """Sugere padronização de nomenclatura de URLs"""
    suggestions = {
        'list_patterns': [
            'announcements_list', 'messages_list', 'newsletters_list',
            'policies_list', 'feedback_list', 'surveys_list', 'resources_list'
        ],
        'detail_patterns': [
            'announcement_detail', 'message_detail', 'newsletter_detail',
            'policy_detail', 'survey_detail', 'resource_detail'
        ],
        'action_patterns': [
            'create_announcement', 'edit_announcement', 'delete_announcement',
            'create_message', 'create_feedback'
        ]
    }
    return suggestions

def generate_report(url_patterns, url_references, undefined_refs, unused_urls):
    """Gera relatório completo da auditoria"""
    
    report = []
    report.append("=" * 60)
    report.append("RELATÓRIO DE AUDITORIA DE URLs")
    report.append("=" * 60)
    report.append("")
    
    # Resumo
    total_defined = sum(len(data['full_names']) for data in url_patterns.values())
    total_referenced = len(url_references)
    
    report.append("📊 RESUMO:")
    report.append(f"- URLs definidas: {total_defined}")
    report.append(f"- URLs referenciadas: {total_referenced}")
    report.append(f"- URLs não definidas: {len(undefined_refs)}")
    report.append(f"- URLs não utilizadas: {len(unused_urls)}")
    report.append("")
    
    # URLs por módulo
    report.append("📁 URLs POR MÓDULO:")
    for module, data in url_patterns.items():
        report.append(f"\n{module.upper()}:")
        report.append(f"  App name: {data['app_name']}")
        report.append(f"  Arquivo: {data['file_path']}")
        report.append(f"  URLs ({len(data['url_names'])}):")
        for url in data['url_names']:
            full_name = f"{data['app_name']}:{url}" if data['app_name'] else url
            usage_count = len(url_references.get(full_name, []))
            status = "✅" if usage_count > 0 else "⚠️"
            report.append(f"    {status} {url} (usado {usage_count}x)")
    
    # Problemas encontrados
    if undefined_refs:
        report.append("\n🚨 URLs REFERENCIADAS MAS NÃO DEFINIDAS:")
        for item in undefined_refs:
            report.append(f"\n❌ {item['url']}")
            report.append("   Usado em:")
            for file in item['files']:
                report.append(f"     - {file}")
    
    if unused_urls:
        report.append("\n⚠️  URLs DEFINIDAS MAS NÃO UTILIZADAS:")
        for url in unused_urls:
            report.append(f"   - {url}")
    
    # Sugestões de padronização
    report.append("\n💡 SUGESTÕES DE PADRONIZAÇÃO:")
    report.append("- Usar plural para listas: announcements_list, messages_list")
    report.append("- Usar singular para detalhes: announcement_detail, message_detail")
    report.append("- Usar padrão: <action>_<entity> para ações")
    report.append("- Sempre usar app_name:url_name em templates")
    
    return "\n".join(report)

def main():
    """Executa auditoria completa das URLs"""
    print("🔍 Iniciando auditoria de URLs...")
    print()
    
    # Extrair dados
    url_patterns = extract_url_patterns()
    url_references = extract_url_references()
    
    # Encontrar inconsistências
    undefined_refs, unused_urls = find_inconsistencies(url_patterns, url_references)
    
    # Gerar relatório
    report = generate_report(url_patterns, url_references, undefined_refs, unused_urls)
    
    # Salvar relatório
    with open('reports/url_audit_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Auditoria concluída!")
    print("📄 Relatório salvo em: reports/url_audit_report.txt")
    print()
    
    # Mostrar problemas críticos
    if undefined_refs:
        print("🚨 PROBLEMAS CRÍTICOS ENCONTRADOS:")
        for item in undefined_refs[:5]:  # Mostrar apenas os primeiros 5
            print(f"❌ URL '{item['url']}' não definida")
        
        if len(undefined_refs) > 5:
            print(f"... e mais {len(undefined_refs) - 5} problemas")
        print()
    
    if not undefined_refs and not unused_urls:
        print("🎉 Nenhuma inconsistência crítica encontrada!")
    
    return len(undefined_refs) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
