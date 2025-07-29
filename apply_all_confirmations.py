"""
Script para aplicar confirmações CRUD em todos os módulos do sistema
"""

import os
import re
from pathlib import Path


def find_crud_views_in_file(file_path):
    """Encontra views CRUD em um arquivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        crud_views = []
        
        # Padrões para encontrar views CRUD
        patterns = {
            'create': r'class\s+(\w*Create\w*View)\s*\([^)]*CreateView[^)]*\):',
            'update': r'class\s+(\w*Update\w*View)\s*\([^)]*UpdateView[^)]*\):',
            'delete': r'class\s+(\w*Delete\w*View)\s*\([^)]*DeleteView[^)]*\):'
        }
        
        for view_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                crud_views.append({
                    'type': view_type,
                    'class_name': match,
                    'file': file_path
                })
        
        return crud_views
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return []


def scan_all_modules():
    """Escaneia todos os módulos em busca de views CRUD"""
    base_path = Path('/workspaces/move')
    modules = []
    
    # Encontrar todos os diretórios que são módulos Django
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
            views_file = item / 'views.py'
            if views_file.exists():
                modules.append(str(item))
    
    all_crud_views = []
    
    for module_path in modules:
        views_file = Path(module_path) / 'views.py'
        module_name = Path(module_path).name
        
        crud_views = find_crud_views_in_file(views_file)
        if crud_views:
            print(f"\n📁 Módulo: {module_name}")
            for view in crud_views:
                print(f"  {view['type'].upper()}: {view['class_name']}")
                all_crud_views.append({**view, 'module': module_name})
    
    return all_crud_views


def check_confirmation_imports(file_path):
    """Verifica se o arquivo já tem imports de confirmação"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return 'CreateConfirmationMixin' in content or 'EditConfirmationMixin' in content or 'DeleteConfirmationMixin' in content
    except:
        return False


def add_confirmation_imports(file_path):
    """Adiciona imports de confirmação se necessário"""
    if check_confirmation_imports(file_path):
        return True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Encontrar local para inserir import
        insert_line = -1
        for i, line in enumerate(lines):
            if 'from django.views.generic' in line or 'from django.contrib.auth.mixins' in line:
                insert_line = i + 1
                break
        
        if insert_line == -1:
            # Se não encontrou local específico, adicionar após os imports do Django
            for i, line in enumerate(lines):
                if line.startswith('from django.') and i < len(lines) - 1:
                    if not lines[i + 1].startswith('from django.'):
                        insert_line = i + 1
                        break
        
        if insert_line == -1:
            insert_line = 0
        
        # Inserir import
        import_line = "from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin\n"
        lines.insert(insert_line, import_line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"❌ Erro ao adicionar imports em {file_path}: {e}")
        return False


def apply_confirmation_to_view(file_path, view_info):
    """Aplica confirmação a uma view específica"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        class_name = view_info['class_name']
        view_type = view_info['type']
        
        # Determinar mixin apropriado
        if view_type == 'create':
            mixin = 'CreateConfirmationMixin'
            entity = view_info.get('entity', 'item')
            message = f"Confirma o cadastro deste novo {entity}?"
        elif view_type == 'update':
            mixin = 'EditConfirmationMixin'
            entity = view_info.get('entity', 'item')
            message = f"Confirma as alterações neste {entity}?"
        elif view_type == 'delete':
            mixin = 'DeleteConfirmationMixin'
            entity = view_info.get('entity', 'item')
            message = f"Tem certeza que deseja excluir este {entity}?"
        
        # Padrão para encontrar e substituir a definição da classe
        pattern = rf'class\s+{class_name}\s*\(([^)]+)\):'
        
        def replacement(match):
            existing_mixins = match.group(1)
            if mixin not in existing_mixins:
                return f'class {class_name}({mixin}, {existing_mixins}):'
            return match.group(0)
        
        new_content = re.sub(pattern, replacement, content)
        
        # Adicionar configurações de confirmação se não existirem
        if f'confirmation_message = "{message}"' not in new_content:
            # Encontrar a classe e adicionar configurações
            class_pattern = rf'(class\s+{class_name}\s*\([^)]+\):\s*(?:\n\s*"""[^"]*"""\s*)?(?:\n\s*.*\s*=\s*.*)*)'
            
            config_lines = f'''
    
    # Configurações da confirmação
    confirmation_message = "{message}"
    confirmation_entity = "{entity}"'''
            
            if view_type == 'delete':
                config_lines += '\n    dangerous_operation = True'
            
            new_content = re.sub(
                class_pattern,
                rf'\1{config_lines}',
                new_content,
                flags=re.MULTILINE
            )
        
        # Salvar apenas se houve mudanças
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Erro ao aplicar confirmação em {class_name}: {e}")
        return False


def main():
    """Aplicar confirmações em todo o sistema"""
    print("🚀 Escaneando sistema para aplicar confirmações CRUD...")
    
    # Configurações de entidades por módulo
    entity_config = {
        'members': 'beneficiária',
        'projects': 'projeto',
        'activities': 'atividade',
        'workshops': 'oficina',
        'social': 'anamnese social',
        'evolution': 'evolução',
        'tasks': 'tarefa',
        'hr': 'recurso humano',
        'coaching': 'coaching',
        'communication': 'comunicação',
        'certificates': 'certificado',
        'chat': 'chat',
        'notifications': 'notificação',
        'reports': 'relatório',
        'users': 'usuário'
    }
    
    # Escanear todos os módulos
    all_views = scan_all_modules()
    
    applied_count = 0
    
    for view_info in all_views:
        module = view_info['module']
        file_path = view_info['file']
        
        # Adicionar configuração de entidade
        view_info['entity'] = entity_config.get(module, 'item')
        
        # Adicionar imports se necessário
        if not check_confirmation_imports(file_path):
            if add_confirmation_imports(file_path):
                print(f"✅ Imports adicionados em {module}/views.py")
        
        # Aplicar confirmação
        if apply_confirmation_to_view(file_path, view_info):
            print(f"✅ Confirmação aplicada: {view_info['class_name']} ({view_info['type']})")
            applied_count += 1
        else:
            print(f"⚠️  Já configurado: {view_info['class_name']} ({view_info['type']})")
    
    print(f"\n🎉 Processo concluído!")
    print(f"📊 {applied_count} confirmações aplicadas")
    print(f"📋 {len(all_views)} views CRUD encontradas no total")


if __name__ == '__main__':
    main()
