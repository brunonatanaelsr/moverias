#!/usr/bin/env python3
"""
Otimizador de Performance - Sistema Move Marias
Identifica e corrige problemas de performance N+1 queries
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('/workspaces/moverias')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.apps import apps
from django.db import models
from django.core.management.color import make_style

class PerformanceOptimizer:
    """Otimizador de performance do sistema"""
    
    def __init__(self):
        self.style = make_style()
        self.optimizations = []
        
    def run_optimization(self):
        """Executa otimização de performance"""
        print(self.style.SUCCESS("🚀 INICIANDO OTIMIZAÇÃO DE PERFORMANCE"))
        print("=" * 60)
        
        # 1. Analisar models para relacionamentos sem otimização
        self.analyze_model_relationships()
        
        # 2. Sugerir índices
        self.suggest_database_indexes()
        
        # 3. Verificar managers otimizados
        self.check_optimized_managers()
        
        # 4. Gerar relatório
        self.generate_optimization_report()
        
    def analyze_model_relationships(self):
        """Analisa relacionamentos dos modelos"""
        print(self.style.WARNING("\n📊 ANALISANDO RELACIONAMENTOS DOS MODELOS"))
        print("-" * 50)
        
        for model in apps.get_models():
            model_name = f"{model._meta.app_label}.{model.__name__}"
            
            # Verificar ForeignKeys
            foreign_keys = [f for f in model._meta.fields if isinstance(f, models.ForeignKey)]
            many_to_many = [f for f in model._meta.many_to_many]
            
            if foreign_keys or many_to_many:
                # Verificar se model tem manager otimizado
                has_optimized_manager = hasattr(model, 'optimized_objects')
                
                if not has_optimized_manager:
                    self.optimizations.append({
                        'type': 'Manager Optimization',
                        'model': model_name,
                        'issue': f'Modelo {model_name} tem relacionamentos mas não tem manager otimizado',
                        'solution': 'Adicionar manager com select_related/prefetch_related',
                        'priority': 'MÉDIO',
                        'code_suggestion': self.generate_manager_code(model, foreign_keys, many_to_many)
                    })
                    
                # Verificar se campos FK têm db_index
                for fk_field in foreign_keys:
                    if not fk_field.db_index:
                        self.optimizations.append({
                            'type': 'Database Index',
                            'model': model_name,
                            'issue': f'Campo FK {fk_field.name} sem índice',
                            'solution': f'Adicionar db_index=True no campo {fk_field.name}',
                            'priority': 'ALTO',
                            'field': fk_field.name
                        })
                        
        print(self.style.SUCCESS("✅ Análise de relacionamentos concluída"))
        
    def generate_manager_code(self, model, foreign_keys, many_to_many):
        """Gera código para manager otimizado"""
        select_related_fields = [fk.name for fk in foreign_keys]
        prefetch_related_fields = [m2m.name for m2m in many_to_many]
        
        code = f"""
class {model.__name__}OptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()"""
        
        if select_related_fields:
            fields_str = "', '".join(select_related_fields)
            code += f"\n        queryset = queryset.select_related('{fields_str}')"
            
        if prefetch_related_fields:
            fields_str = "', '".join(prefetch_related_fields)
            code += f"\n        queryset = queryset.prefetch_related('{fields_str}')"
            
        code += f"""
        return queryset

class {model.__name__}(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = {model.__name__}OptimizedManager()
    
    class Meta:
        # ... Meta existente ...
"""
        return code
        
    def suggest_database_indexes(self):
        """Sugere índices para campos comuns"""
        print(self.style.WARNING("\n💾 SUGERINDO ÍNDICES DE BANCO DE DADOS"))
        print("-" * 50)
        
        common_search_fields = [
            'name', 'full_name', 'email', 'cpf', 'phone', 'title',
            'status', 'created_at', 'updated_at', 'date', 'start_date'
        ]
        
        for model in apps.get_models():
            model_name = f"{model._meta.app_label}.{model.__name__}"
            
            for field in model._meta.fields:
                if field.name in common_search_fields and not field.db_index:
                    # Evitar duplicatas para ForeignKeys (já checadas)
                    if not isinstance(field, models.ForeignKey):
                        self.optimizations.append({
                            'type': 'Database Index',
                            'model': model_name,
                            'issue': f'Campo comum {field.name} sem índice',
                            'solution': f'Adicionar db_index=True no campo {field.name}',
                            'priority': 'MÉDIO',
                            'field': field.name
                        })
                        
        print(self.style.SUCCESS("✅ Sugestões de índice concluídas"))
        
    def check_optimized_managers(self):
        """Verifica managers otimizados existentes"""
        print(self.style.WARNING("\n⚡ VERIFICANDO MANAGERS OTIMIZADOS"))
        print("-" * 50)
        
        optimized_models = []
        non_optimized_models = []
        
        for model in apps.get_models():
            model_name = f"{model._meta.app_label}.{model.__name__}"
            
            if hasattr(model, 'optimized_objects'):
                optimized_models.append(model_name)
            else:
                # Verificar se modelo tem relacionamentos
                has_relationships = (
                    any(isinstance(f, models.ForeignKey) for f in model._meta.fields) or
                    model._meta.many_to_many
                )
                
                if has_relationships:
                    non_optimized_models.append(model_name)
                    
        print(f"✅ Modelos com managers otimizados: {len(optimized_models)}")
        print(f"⚠️  Modelos que precisam de otimização: {len(non_optimized_models)}")
        
        if non_optimized_models:
            print("\nModelos que precisam de otimização:")
            for model in non_optimized_models[:10]:  # Primeiros 10
                print(f"  • {model}")
                
    def generate_optimization_report(self):
        """Gera relatório de otimização"""
        print(self.style.SUCCESS("\n📋 RELATÓRIO DE OTIMIZAÇÃO"))
        print("=" * 60)
        
        total_optimizations = len(self.optimizations)
        high_priority = len([o for o in self.optimizations if o['priority'] == 'ALTO'])
        medium_priority = len([o for o in self.optimizations if o['priority'] == 'MÉDIO'])
        
        print(f"\n📊 RESUMO:")
        print(f"  • Total de otimizações sugeridas: {total_optimizations}")
        print(f"  • Prioridade alta: {high_priority}")
        print(f"  • Prioridade média: {medium_priority}")
        
        # Otimizações por tipo
        optimizations_by_type = {}
        for opt in self.optimizations:
            opt_type = opt['type']
            if opt_type not in optimizations_by_type:
                optimizations_by_type[opt_type] = []
            optimizations_by_type[opt_type].append(opt)
            
        for opt_type, opts in optimizations_by_type.items():
            print(f"\n🔧 {opt_type.upper()} ({len(opts)} otimizações):")
            
            for i, opt in enumerate(opts[:5], 1):  # Primeiras 5
                print(f"  {i}. {opt['issue']}")
                print(f"     Solução: {opt['solution']}")
                print(f"     Prioridade: {opt['priority']}")
                
                if 'code_suggestion' in opt:
                    print(f"     📝 Código sugerido disponível")
                print()
                
        # Salvar detalhes em arquivo
        self.save_optimization_details()
        
        print(self.style.SUCCESS("✅ RELATÓRIO DE OTIMIZAÇÃO CONCLUÍDO"))
        print("💡 Execute as otimizações de alta prioridade primeiro.")
        
    def save_optimization_details(self):
        """Salva detalhes das otimizações em arquivo"""
        try:
            with open('/workspaces/moverias/performance_optimizations.md', 'w', encoding='utf-8') as f:
                f.write("# 🚀 OTIMIZAÇÕES DE PERFORMANCE - MOVE MARIAS\n\n")
                f.write("Este arquivo contém sugestões detalhadas de otimização.\n\n")
                
                # Agrupar por tipo
                optimizations_by_type = {}
                for opt in self.optimizations:
                    opt_type = opt['type']
                    if opt_type not in optimizations_by_type:
                        optimizations_by_type[opt_type] = []
                    optimizations_by_type[opt_type].append(opt)
                    
                for opt_type, opts in optimizations_by_type.items():
                    f.write(f"## {opt_type}\n\n")
                    
                    for i, opt in enumerate(opts, 1):
                        f.write(f"### {i}. {opt['model']}\n\n")
                        f.write(f"**Problema:** {opt['issue']}\n\n")
                        f.write(f"**Solução:** {opt['solution']}\n\n")
                        f.write(f"**Prioridade:** {opt['priority']}\n\n")
                        
                        if 'code_suggestion' in opt:
                            f.write("**Código sugerido:**\n\n")
                            f.write("```python\n")
                            f.write(opt['code_suggestion'])
                            f.write("\n```\n\n")
                            
                        f.write("---\n\n")
                        
            print(f"📄 Detalhes salvos em: performance_optimizations.md")
            
        except Exception as e:
            print(f"❌ Erro ao salvar detalhes: {e}")


if __name__ == '__main__':
    optimizer = PerformanceOptimizer()
    optimizer.run_optimization()
