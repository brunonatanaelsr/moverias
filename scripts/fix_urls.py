#!/usr/bin/env python3
# fix_urls.py - Corrige inconsistências de URLs automaticamente

import os
import re
import argparse

# Mapeamento de URLs incorretas para corretas baseado na auditoria
URL_CORRECTIONS = {
    # URLs que existem mas com nomes diferentes
    'dashboard:dashboard': 'dashboard:home',
    'dashboard:index': 'dashboard:home',
    'activities:activities_list': 'activities:activities_list',  # Manter como está
    'social:anamnesis_list': 'social:list',
    'social:anamnesis-create': 'social:anamnesis-create',
    'communication:memo_list': 'communication:messages_list',  # Aproximação
    'communication:memo_create': 'communication:create_message',  # Aproximação
    'communication:memo_detail': 'communication:message_detail',  # Aproximação
    'communication:memo_edit': 'communication:message_detail',  # Aproximação
    'hr:position_list': 'hr:job_position_list',
    'hr:position_create': 'hr:job_position_create',
    'hr:position_edit': 'hr:job_position_edit',
    'hr:position_delete': 'hr:job_position_delete',
    'hr:position_detail': 'hr:job_position_detail',
    'tasks:create': 'tasks:task_create',
    'tasks:list': 'tasks:task_list',
    # Adicionar mais correções conforme necessário
}

def fix_template_urls(file_path, dry_run=True):
    """Corrige URLs em templates"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Tentar com latin-1 se UTF-8 falhar
        with open(file_path, 'r', encoding='latin-1') as f:
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
                try:
                    changes = fix_template_urls(file_path, dry_run)
                    
                    if changes:
                        total_files += 1
                        total_changes += len(changes)
                        print(f"Arquivo: {file_path}")
                        for change in changes:
                            print(f"  - {change}")
                        print()
                except Exception as e:
                    print(f"Erro ao processar {file_path}: {e}")
    
    print(f"Resumo: {total_changes} mudanças em {total_files} arquivos")
    return total_changes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Corrige URLs em templates')
    parser.add_argument('--execute', action='store_true', 
                       help='Executa as correções (padrão é dry-run)')
    
    args = parser.parse_args()
    
    if not os.path.exists('templates'):
        print("Diretório 'templates' não encontrado. Execute este script na raiz do projeto Django.")
        exit(1)
    
    process_templates(dry_run=not args.execute)
