#!/usr/bin/env python3
"""
Script para corrigir referências de managers nos testes
"""

import os
import re
from pathlib import Path

def fix_manager_references(file_path):
    """Corrige referências de .objects para usar managers otimizados quando disponível"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Modelos que têm optimized_objects
    models_with_optimized = [
        'Beneficiary',
        'Project', 
        'BeneficiaryActivity',
        'SocialAnamnesis',
        'EvolutionRecord'
    ]
    
    # Para cada modelo, substituir .objects por uma versão que usa optimized_objects
    for model in models_with_optimized:
        # Padrão: ModelName.objects.method(
        pattern = rf'{model}\.objects\.(\w+)\('
        
        # Substituição que usa optimized_objects se disponível
        replacement = rf'getattr({model}, "optimized_objects", {model}.objects).\1('
        
        content = re.sub(pattern, replacement, content)
    
    # Se houve mudanças, salvar o arquivo
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Corrigido: {file_path}")
        return True
    else:
        print(f"⏭️ Sem mudanças: {file_path}")
        return False

def main():
    """Processar todos os arquivos de teste"""
    test_dir = Path('/workspaces/move/tests')
    
    if not test_dir.exists():
        print("❌ Diretório de testes não encontrado")
        return
    
    files_changed = 0
    
    # Processar todos os arquivos .py no diretório de testes
    for test_file in test_dir.glob('*.py'):
        if test_file.name.startswith('test_'):
            if fix_manager_references(test_file):
                files_changed += 1
    
    print(f"\n📊 Resumo: {files_changed} arquivos corrigidos")

if __name__ == '__main__':
    main()
