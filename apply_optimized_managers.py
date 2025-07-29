#!/usr/bin/env python3
"""
Script para aplicar os managers otimizados aos modelos existentes
Parte da Fase 1 do Plano de Melhorias Incrementais
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.db import models
from core.optimized_managers import (
    BeneficiaryManager,
    ProjectManager,
    WorkshopManager,
    EvolutionManager,
    SocialAnamnesisManager
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManagerIntegrator:
    """Classe para integrar os managers otimizados aos modelos"""
    
    def __init__(self):
        self.changes_made = []
        self.errors = []
    
    def backup_model_file(self, model_path):
        """Cria backup do arquivo antes das modificações"""
        backup_path = model_path.with_suffix('.py.backup')
        if not backup_path.exists():
            backup_path.write_text(model_path.read_text())
            logger.info(f"Backup criado: {backup_path}")
    
    def add_manager_import(self, content, manager_class):
        """Adiciona import do manager otimizado"""
        import_line = f"from core.optimized_managers import {manager_class}"
        
        if import_line in content:
            return content
        
        # Procurar onde inserir o import
        lines = content.split('\n')
        insert_index = 0
        
        # Encontrar local apropriado (após outros imports)
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                break
        
        lines.insert(insert_index, import_line)
        return '\n'.join(lines)
    
    def add_manager_to_model(self, content, model_name, manager_name, manager_class):
        """Adiciona manager otimizado ao modelo"""
        lines = content.split('\n')
        model_found = False
        insert_index = -1
        
        for i, line in enumerate(lines):
            if f"class {model_name}" in line and "Model" in line:
                model_found = True
                continue
            
            if model_found:
                # Procurar primeiro campo ou método para inserir o manager
                if (line.strip().startswith('def ') or 
                    line.strip().startswith('class ') or
                    ('=' in line and not line.strip().startswith('#'))):
                    insert_index = i
                    break
        
        if insert_index > -1:
            # Verificar se já existe um manager
            manager_line = f"    {manager_name} = {manager_class}()"
            
            # Verificar se já existe
            for line in lines[insert_index-10:insert_index+10]:
                if manager_name in line and manager_class in line:
                    logger.info(f"Manager {manager_name} já existe em {model_name}")
                    return content
            
            lines.insert(insert_index, "")
            lines.insert(insert_index + 1, manager_line)
            lines.insert(insert_index + 2, "")
            
            logger.info(f"Manager {manager_name} adicionado ao modelo {model_name}")
            self.changes_made.append(f"{model_name}.{manager_name}")
            
            return '\n'.join(lines)
        
        logger.warning(f"Não foi possível encontrar local para inserir manager em {model_name}")
        return content
    
    def integrate_beneficiary_manager(self):
        """Integra manager otimizado ao modelo Beneficiary"""
        model_path = BASE_DIR / 'members' / 'models.py'
        
        if not model_path.exists():
            self.errors.append(f"Arquivo não encontrado: {model_path}")
            return
        
        try:
            self.backup_model_file(model_path)
            content = model_path.read_text()
            
            # Adicionar import
            content = self.add_manager_import(content, 'BeneficiaryManager')
            
            # Adicionar manager ao modelo
            content = self.add_manager_to_model(
                content, 
                'Beneficiary', 
                'optimized_objects', 
                'BeneficiaryManager'
            )
            
            model_path.write_text(content)
            logger.info("Manager integrado ao modelo Beneficiary")
            
        except Exception as e:
            self.errors.append(f"Erro ao integrar Beneficiary manager: {str(e)}")
            logger.error(f"Erro: {e}")
    
    def integrate_project_manager(self):
        """Integra manager otimizado ao modelo Project"""
        model_path = BASE_DIR / 'projects' / 'models.py'
        
        if not model_path.exists():
            self.errors.append(f"Arquivo não encontrado: {model_path}")
            return
        
        try:
            self.backup_model_file(model_path)
            content = model_path.read_text()
            
            content = self.add_manager_import(content, 'ProjectManager')
            content = self.add_manager_to_model(
                content, 
                'Project', 
                'optimized_objects', 
                'ProjectManager'
            )
            
            model_path.write_text(content)
            logger.info("Manager integrado ao modelo Project")
            
        except Exception as e:
            self.errors.append(f"Erro ao integrar Project manager: {str(e)}")
            logger.error(f"Erro: {e}")
    
    def integrate_workshop_manager(self):
        """Integra manager otimizado ao modelo Workshop"""
        model_path = BASE_DIR / 'workshops' / 'models.py'
        
        if not model_path.exists():
            self.errors.append(f"Arquivo não encontrado: {model_path}")
            return
        
        try:
            self.backup_model_file(model_path)
            content = model_path.read_text()
            
            content = self.add_manager_import(content, 'WorkshopManager')
            content = self.add_manager_to_model(
                content, 
                'Workshop', 
                'optimized_objects', 
                'WorkshopManager'
            )
            
            model_path.write_text(content)
            logger.info("Manager integrado ao modelo Workshop")
            
        except Exception as e:
            self.errors.append(f"Erro ao integrar Workshop manager: {str(e)}")
            logger.error(f"Erro: {e}")
    
    def integrate_evolution_manager(self):
        """Integra manager otimizado ao modelo EvolutionRecord"""
        model_path = BASE_DIR / 'evolution' / 'models.py'
        
        if not model_path.exists():
            self.errors.append(f"Arquivo não encontrado: {model_path}")
            return
        
        try:
            self.backup_model_file(model_path)
            content = model_path.read_text()
            
            content = self.add_manager_import(content, 'EvolutionManager')
            content = self.add_manager_to_model(
                content, 
                'EvolutionRecord', 
                'optimized_objects', 
                'EvolutionManager'
            )
            
            model_path.write_text(content)
            logger.info("Manager integrado ao modelo EvolutionRecord")
            
        except Exception as e:
            self.errors.append(f"Erro ao integrar Evolution manager: {str(e)}")
            logger.error(f"Erro: {e}")
    
    def integrate_social_manager(self):
        """Integra manager otimizado ao modelo SocialAnamnesis"""
        model_path = BASE_DIR / 'social' / 'models.py'
        
        if not model_path.exists():
            self.errors.append(f"Arquivo não encontrado: {model_path}")
            return
        
        try:
            self.backup_model_file(model_path)
            content = model_path.read_text()
            
            content = self.add_manager_import(content, 'SocialAnamnesisManager')
            content = self.add_manager_to_model(
                content, 
                'SocialAnamnesis', 
                'optimized_objects', 
                'SocialAnamnesisManager'
            )
            
            model_path.write_text(content)
            logger.info("Manager integrado ao modelo SocialAnamnesis")
            
        except Exception as e:
            self.errors.append(f"Erro ao integrar Social manager: {str(e)}")
            logger.error(f"Erro: {e}")
    
    def run_integration(self):
        """Executa integração completa"""
        logger.info("=== INICIANDO INTEGRAÇÃO DOS MANAGERS OTIMIZADOS ===")
        
        self.integrate_beneficiary_manager()
        self.integrate_project_manager()
        self.integrate_workshop_manager()
        self.integrate_evolution_manager()
        self.integrate_social_manager()
        
        # Relatório final
        logger.info("\n=== RELATÓRIO DE INTEGRAÇÃO ===")
        logger.info(f"Managers integrados: {len(self.changes_made)}")
        for change in self.changes_made:
            logger.info(f"  ✓ {change}")
        
        if self.errors:
            logger.error(f"\nErros encontrados: {len(self.errors)}")
            for error in self.errors:
                logger.error(f"  ✗ {error}")
        
        logger.info("\n=== PRÓXIMOS PASSOS ===")
        logger.info("1. Verificar se as integrações funcionaram corretamente")
        logger.info("2. Atualizar views para usar os managers otimizados")
        logger.info("3. Executar testes para validar performance")
        logger.info("4. Executar: python manage.py migrate (se necessário)")


class ViewUpdater:
    """Atualiza views para usar os managers otimizados"""
    
    def __init__(self):
        self.updated_views = []
    
    def update_members_views(self):
        """Atualiza views do módulo members"""
        view_path = BASE_DIR / 'members' / 'views.py'
        
        if not view_path.exists():
            return
        
        try:
            content = view_path.read_text()
            
            # Substituir queries básicas por otimizadas
            replacements = [
                ('Beneficiary.objects.all()', 'Beneficiary.optimized_objects.with_statistics()'),
                ('Beneficiary.objects.filter(', 'Beneficiary.optimized_objects.filter('),
                ('Beneficiary.objects.get(', 'Beneficiary.optimized_objects.get('),
            ]
            
            original_content = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original_content:
                # Backup
                backup_path = view_path.with_suffix('.py.backup')
                if not backup_path.exists():
                    backup_path.write_text(original_content)
                
                view_path.write_text(content)
                self.updated_views.append('members/views.py')
                logger.info("Views do módulo members atualizadas")
        
        except Exception as e:
            logger.error(f"Erro ao atualizar members views: {e}")
    
    def update_projects_views(self):
        """Atualiza views do módulo projects"""
        view_path = BASE_DIR / 'projects' / 'views.py'
        
        if not view_path.exists():
            return
        
        try:
            content = view_path.read_text()
            
            replacements = [
                ('Project.objects.all()', 'Project.optimized_objects.with_statistics()'),
                ('Project.objects.filter(', 'Project.optimized_objects.filter('),
                ('Project.objects.get(', 'Project.optimized_objects.get('),
            ]
            
            original_content = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original_content:
                backup_path = view_path.with_suffix('.py.backup')
                if not backup_path.exists():
                    backup_path.write_text(original_content)
                
                view_path.write_text(content)
                self.updated_views.append('projects/views.py')
                logger.info("Views do módulo projects atualizadas")
        
        except Exception as e:
            logger.error(f"Erro ao atualizar projects views: {e}")
    
    def run_view_updates(self):
        """Executa todas as atualizações de views"""
        logger.info("=== ATUALIZANDO VIEWS PARA USAR MANAGERS OTIMIZADOS ===")
        
        self.update_members_views()
        self.update_projects_views()
        
        logger.info(f"Views atualizadas: {len(self.updated_views)}")
        for view in self.updated_views:
            logger.info(f"  ✓ {view}")


def main():
    """Função principal"""
    print("🚀 APLICANDO MANAGERS OTIMIZADOS - FASE 1 DO PLANO DE MELHORIAS")
    print("=" * 70)
    
    # Integrar managers
    integrator = ManagerIntegrator()
    integrator.run_integration()
    
    # Atualizar views
    updater = ViewUpdater()
    updater.run_view_updates()
    
    print("\n" + "=" * 70)
    print("✅ INTEGRAÇÃO CONCLUÍDA!")
    
    if integrator.errors:
        print("⚠️  Alguns erros foram encontrados. Verifique os logs acima.")
        return 1
    
    print("\n📋 CHECKLIST PÓS-INTEGRAÇÃO:")
    print("□ Executar testes: python manage.py test")
    print("□ Verificar performance das queries no Django Debug Toolbar")
    print("□ Monitorar logs de cache após implementação")
    print("□ Testar funcionalidades críticas manualmente")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
