#!/usr/bin/env python3
# consolidate_views.py - Consolida arquivos de views duplicados

import os
import shutil
import ast
import argparse
from datetime import datetime

def backup_files(files_to_backup):
    """Cria backup dos arquivos antes da consolidação"""
    backup_dir = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, file_path.replace('/', '_'))
            shutil.copy2(file_path, backup_path)
            print(f"Backup criado: {backup_path}")
    
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
        
        # Copiar arquivo principal para views.py
        target_file = f"{base_path}/views.py"
        if os.path.exists(target_file):
            shutil.copy2(target_file, f"{backup_dir}/views_original.py")
        
        shutil.copy2(main_file, target_file)
        print(f"Copiado {main_file} para {target_file}")
        
        # Mover outros arquivos para legacy
        legacy_dir = f"{base_path}/legacy"
        os.makedirs(legacy_dir, exist_ok=True)
        
        for file_path in view_files:
            if file_path != main_file and file_path != target_file and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                legacy_path = os.path.join(legacy_dir, filename)
                shutil.move(file_path, legacy_path)
                print(f"Movido {file_path} para {legacy_path}")
        
        return True
    else:
        print(f"Arquivo principal {main_file} não encontrado")
        return False

def consolidate_models():
    """Consolida arquivos de models duplicados"""
    modules_to_check = ['communication', 'social', 'projects']
    
    for module in modules_to_check:
        if not os.path.exists(module):
            continue
            
        print(f"\n=== CONSOLIDAÇÃO DE MODELS - {module.upper()} ===")
        
        models_files = [
            f"{module}/models.py",
            f"{module}/models_refactored.py",
            f"{module}/models_integrated.py"
        ]
        
        existing_files = [f for f in models_files if os.path.exists(f)]
        
        if len(existing_files) > 1:
            print(f"Encontrados {len(existing_files)} arquivos de models:")
            for f in existing_files:
                print(f"  - {f}")
            
            # Criar backup
            backup_dir = backup_files(existing_files)
            
            # Mover arquivos extras para legacy
            legacy_dir = f"{module}/legacy"
            os.makedirs(legacy_dir, exist_ok=True)
            
            main_models = f"{module}/models.py"
            for file_path in existing_files:
                if file_path != main_models:
                    filename = os.path.basename(file_path)
                    legacy_path = os.path.join(legacy_dir, filename)
                    if os.path.exists(file_path):
                        shutil.move(file_path, legacy_path)
                        print(f"Movido {file_path} para {legacy_path}")

def create_changelog():
    """Cria changelog das mudanças"""
    changelog_content = f"""# CHANGELOG - CONSOLIDAÇÃO DE CÓDIGO

## Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Mudanças Realizadas:

#### Views Consolidadas:
- `communication/views_simple.py` → `communication/views.py` (arquivo principal)
- Arquivos antigos movidos para `communication/legacy/`

#### Models Consolidados:
- Arquivos duplicados movidos para pastas `legacy/` respectivas

#### Backups:
- Todos os arquivos originais foram copiados para `backups/backup_YYYYMMDD_HHMMSS/`

### Próximos Passos:
1. Verificar se todas as funcionalidades continuam funcionando
2. Atualizar imports se necessário
3. Remover arquivos legacy após confirmação de estabilidade

### Rollback:
Em caso de problemas, restaurar arquivos do backup mais recente.
"""
    
    with open('CHANGELOG_CONSOLIDACAO.md', 'w', encoding='utf-8') as f:
        f.write(changelog_content)
    
    print("Changelog criado: CHANGELOG_CONSOLIDACAO.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Consolida arquivos de views e models duplicados')
    parser.add_argument('--dry-run', action='store_true', help='Simula a consolidação sem executar')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("=== MODO DRY-RUN - SIMULAÇÃO ===")
        print("Nenhuma mudança será feita aos arquivos")
        exit(0)
    
    print("=== INICIANDO CONSOLIDAÇÃO DE CÓDIGO ===")
    print()
    
    # Consolidar views
    success = consolidate_communication_views()
    
    # Consolidar models
    consolidate_models()
    
    # Criar changelog
    create_changelog()
    
    if success:
        print("\n✅ Consolidação concluída com sucesso!")
        print("⚠️  IMPORTANTE: Teste todas as funcionalidades antes de remover os backups")
    else:
        print("\n❌ Consolidação falhou parcialmente")
        print("Verifique os logs acima para mais detalhes")
