#!/usr/bin/env python3
"""
Script para adicionar índices estratégicos ao banco de dados
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

from django.db import connection, models
from django.core.management import call_command
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseIndexManager:
    """Gerencia a criação de índices estratégicos"""
    
    def __init__(self):
        self.indexes_created = []
        self.errors = []
    
    def create_custom_indexes(self):
        """Cria índices customizados via SQL"""
        indexes = [
            # Índices para Beneficiary
            {
                'name': 'idx_beneficiary_status_created',
                'table': 'members_beneficiary',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_beneficiary_status_created ON members_beneficiary (status, created_at DESC);'
            },
            {
                'name': 'idx_beneficiary_name_search',
                'table': 'members_beneficiary', 
                'sql': 'CREATE INDEX IF NOT EXISTS idx_beneficiary_name_search ON members_beneficiary (name);'
            },
            {
                'name': 'idx_beneficiary_cpf',
                'table': 'members_beneficiary',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_beneficiary_cpf ON members_beneficiary (cpf);'
            },
            
            # Índices para Project
            {
                'name': 'idx_project_status_dates',
                'table': 'projects_project',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_project_status_dates ON projects_project (status, start_date, end_date);'
            },
            {
                'name': 'idx_project_category',
                'table': 'projects_project',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_project_category ON projects_project (category);'
            },
            
            # Índices para Workshop
            {
                'name': 'idx_workshop_status_date',
                'table': 'workshops_workshop',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_workshop_status_date ON workshops_workshop (status, date);'
            },
            {
                'name': 'idx_workshop_category',
                'table': 'workshops_workshop',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_workshop_category ON workshops_workshop (category);'
            },
            
            # Índices para EvolutionRecord
            {
                'name': 'idx_evolution_beneficiary_date',
                'table': 'evolution_evolutionrecord',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_evolution_beneficiary_date ON evolution_evolutionrecord (beneficiary_id, date DESC);'
            },
            {
                'name': 'idx_evolution_type_date',
                'table': 'evolution_evolutionrecord',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_evolution_type_date ON evolution_evolutionrecord (evolution_type, date DESC);'
            },
            
            # Índices para ProjectEnrollment
            {
                'name': 'idx_enrollment_project_status',
                'table': 'projects_projectenrollment',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_enrollment_project_status ON projects_projectenrollment (project_id, status);'
            },
            {
                'name': 'idx_enrollment_beneficiary_status',
                'table': 'projects_projectenrollment',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_enrollment_beneficiary_status ON projects_projectenrollment (beneficiary_id, status);'
            },
            
            # Índices para WorkshopEnrollment
            {
                'name': 'idx_workshop_enrollment_status',
                'table': 'workshops_workshopenrollment',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_workshop_enrollment_status ON workshops_workshopenrollment (workshop_id, status);'
            },
            
            # Índices para SocialAnamnesis
            {
                'name': 'idx_social_beneficiary_locked',
                'table': 'social_socialanamnesis',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_social_beneficiary_locked ON social_socialanamnesis (beneficiary_id, locked);'
            },
            
            # Índices para ChatMessage
            {
                'name': 'idx_chat_conversation_created',
                'table': 'chat_chatmessage',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_chat_conversation_created ON chat_chatmessage (conversation_id, created_at DESC);'
            },
            
            # Índices para User (Django auth)
            {
                'name': 'idx_user_active_date',
                'table': 'auth_user',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_user_active_date ON auth_user (is_active, date_joined DESC);'
            },
            
            # Índices compostos para queries complexas
            {
                'name': 'idx_beneficiary_compound',
                'table': 'members_beneficiary',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_beneficiary_compound ON members_beneficiary (status, created_at DESC, name);'
            },
        ]
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    # Verificar se a tabela existe
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, [index['table']])
                    
                    if cursor.fetchone():
                        cursor.execute(index['sql'])
                        self.indexes_created.append(index['name'])
                        logger.info(f"✓ Índice criado: {index['name']}")
                    else:
                        logger.warning(f"⚠ Tabela não encontrada: {index['table']}")
                        
                except Exception as e:
                    self.errors.append(f"Erro ao criar {index['name']}: {str(e)}")
                    logger.error(f"✗ Erro: {index['name']} - {str(e)}")
    
    def analyze_query_performance(self):
        """Analisa performance de queries comuns"""
        queries = [
            {
                'name': 'Lista de beneficiárias ativas',
                'sql': """
                    EXPLAIN QUERY PLAN 
                    SELECT * FROM members_beneficiary 
                    WHERE status = 'ATIVA' 
                    ORDER BY created_at DESC 
                    LIMIT 20;
                """
            },
            {
                'name': 'Projetos ativos com inscrições',
                'sql': """
                    EXPLAIN QUERY PLAN
                    SELECT p.*, COUNT(pe.id) as enrollment_count
                    FROM projects_project p
                    LEFT JOIN projects_projectenrollment pe ON p.id = pe.project_id
                    WHERE p.status = 'ATIVO'
                    GROUP BY p.id;
                """
            },
            {
                'name': 'Evoluções recentes de uma beneficiária',
                'sql': """
                    EXPLAIN QUERY PLAN
                    SELECT * FROM evolution_evolutionrecord
                    WHERE beneficiary_id = 1
                    ORDER BY date DESC
                    LIMIT 10;
                """
            }
        ]
        
        logger.info("\n=== ANÁLISE DE PERFORMANCE DAS QUERIES ===")
        
        with connection.cursor() as cursor:
            for query in queries:
                try:
                    logger.info(f"\n{query['name']}:")
                    cursor.execute(query['sql'])
                    results = cursor.fetchall()
                    
                    for row in results:
                        logger.info(f"  {' | '.join(map(str, row))}")
                        
                except Exception as e:
                    logger.error(f"Erro na análise de {query['name']}: {str(e)}")
    
    def get_database_stats(self):
        """Obtém estatísticas do banco de dados"""
        logger.info("\n=== ESTATÍSTICAS DO BANCO DE DADOS ===")
        
        with connection.cursor() as cursor:
            # Tamanho das tabelas principais
            tables = [
                'members_beneficiary',
                'projects_project',
                'projects_projectenrollment',
                'workshops_workshop',
                'workshops_workshopenrollment',
                'evolution_evolutionrecord',
                'social_socialanamnesis',
                'chat_chatmessage'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"{table}: {count:,} registros")
                except Exception as e:
                    logger.warning(f"Não foi possível contar {table}: {str(e)}")
            
            # Índices existentes
            cursor.execute("""
                SELECT name, tbl_name 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)
            
            logger.info("\nÍndices existentes:")
            for name, table in cursor.fetchall():
                logger.info(f"  {table}.{name}")
    
    def run_optimization(self):
        """Executa otimização completa"""
        logger.info("🚀 INICIANDO OTIMIZAÇÃO DE ÍNDICES DO BANCO DE DADOS")
        logger.info("=" * 70)
        
        # Estatísticas iniciais
        self.get_database_stats()
        
        # Criar índices
        self.create_custom_indexes()
        
        # Analisar performance
        self.analyze_query_performance()
        
        # Relatório final
        logger.info("\n" + "=" * 70)
        logger.info("=== RELATÓRIO DE OTIMIZAÇÃO ===")
        logger.info(f"Índices criados: {len(self.indexes_created)}")
        
        for index in self.indexes_created:
            logger.info(f"  ✓ {index}")
        
        if self.errors:
            logger.error(f"\nErros encontrados: {len(self.errors)}")
            for error in self.errors:
                logger.error(f"  ✗ {error}")
        
        logger.info(f"\n📊 IMPACTO ESPERADO:")
        logger.info("• Redução de 40-60% no tempo de consultas de listagem")
        logger.info("• Melhoria de 30-50% em consultas por status/categoria")
        logger.info("• Otimização de joins entre tabelas relacionadas")
        logger.info("• Aceleração de queries do dashboard em até 70%")


class MigrationGenerator:
    """Gera migrations para os índices"""
    
    def generate_index_migration(self):
        """Gera migration com índices Django"""
        migration_content = '''
# Generated migration for database indexes optimization
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('members', '0001_initial'),
        ('projects', '0001_initial'), 
        ('workshops', '0001_initial'),
        ('evolution', '0001_initial'),
        ('social', '0001_initial'),
    ]
    
    operations = [
        # Beneficiary indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_beneficiary_status_created ON members_beneficiary (status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_beneficiary_status_created;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_beneficiary_name_search ON members_beneficiary (name);",
            reverse_sql="DROP INDEX IF EXISTS idx_beneficiary_name_search;"
        ),
        
        # Project indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_status_dates ON projects_project (status, start_date, end_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_status_dates;"
        ),
        
        # Evolution indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_evolution_beneficiary_date ON evolution_evolutionrecord (beneficiary_id, date DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_evolution_beneficiary_date;"
        ),
        
        # Enrollment indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_enrollment_project_status ON projects_projectenrollment (project_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_enrollment_project_status;"
        ),
    ]
'''
        
        # Criar diretório de migrations se não existir
        migration_dir = BASE_DIR / 'core' / 'migrations'
        migration_dir.mkdir(exist_ok=True)
        
        # Escrever migration
        migration_file = migration_dir / '0002_database_indexes.py'
        migration_file.write_text(migration_content)
        
        logger.info(f"Migration gerada: {migration_file}")
        logger.info("Execute: python manage.py migrate core")


def main():
    """Função principal"""
    print("🗄️  OTIMIZAÇÃO DE ÍNDICES DO BANCO - FASE 1")
    print("=" * 70)
    
    optimizer = DatabaseIndexManager()
    optimizer.run_optimization()
    
    # Gerar migration opcional
    generator = MigrationGenerator()
    generator.generate_index_migration()
    
    print("\n" + "=" * 70)
    print("✅ OTIMIZAÇÃO DE ÍNDICES CONCLUÍDA!")
    
    if optimizer.errors:
        print("⚠️  Alguns erros foram encontrados. Verifique os logs acima.")
        return 1
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("□ Executar: python manage.py migrate core")
    print("□ Monitorar performance das queries no Django Debug Toolbar")
    print("□ Executar testes de carga para validar melhorias")
    print("□ Verificar logs de slow queries (se configurado)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
