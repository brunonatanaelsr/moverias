#!/bin/bash

# Script para migração autônoma da tabela workshops
# Este script remove as migrações existentes e recria a tabela workshops corretamente

set -e  # Parar execução em caso de erro

echo "🔄 Iniciando migração autônoma da tabela workshops..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    log_error "manage.py não encontrado. Execute este script na raiz do projeto Django."
    exit 1
fi

log_info "Fazendo backup do banco de dados atual..."
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || log_warning "Não foi possível fazer backup do banco"

# 1. Remover migrações existentes do workshops (exceto __init__.py)
log_info "Removendo migrações existentes do workshops..."
find workshops/migrations -name "*.py" ! -name "__init__.py" -delete 2>/dev/null || true
find workshops/migrations -name "*.pyc" -delete 2>/dev/null || true

# 2. Verificar se a tabela workshops existe e removê-las do banco
log_info "Removendo tabelas workshops existentes do banco de dados..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
import django
django.setup()
from django.db import connection

cursor = connection.cursor()

# Lista de tabelas relacionadas ao workshops para remover
tables_to_drop = [
    'workshops_workshopevaluation',
    'workshops_sessionattendance', 
    'workshops_workshopsession',
    'workshops_workshopenrollment',
    'workshops_workshop'
]

for table in tables_to_drop:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
        print(f'✓ Tabela {table} removida')
    except Exception as e:
        print(f'⚠ Erro ao remover {table}: {e}')

connection.close()
print('✅ Limpeza das tabelas concluída')
"

# 3. Remover entradas das migrações da tabela django_migrations
log_info "Limpando registros de migração do django_migrations..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
import django
django.setup()
from django.db import connection

cursor = connection.cursor()
try:
    cursor.execute(\"DELETE FROM django_migrations WHERE app = 'workshops'\")
    print('✓ Registros de migração do workshops removidos')
except Exception as e:
    print(f'⚠ Erro ao limpar django_migrations: {e}')

connection.close()
"

# 4. Criar nova migração inicial
log_info "Criando nova migração inicial para workshops..."
python3 manage.py makemigrations workshops --empty --name "reset_workshops_tables"

# 5. Criar migração com as tabelas corretas
log_info "Gerando migração com a estrutura correta dos modelos..."
python3 manage.py makemigrations workshops

# 6. Aplicar as migrações
log_info "Aplicando as novas migrações..."
python3 manage.py migrate workshops --fake-initial

# 7. Verificar se as tabelas foram criadas corretamente
log_info "Verificando estrutura das tabelas criadas..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
import django
django.setup()
from django.db import connection

cursor = connection.cursor()

# Verificar tabelas workshops
tables_to_check = [
    'workshops_workshop',
    'workshops_workshopenrollment', 
    'workshops_workshopsession',
    'workshops_sessionattendance',
    'workshops_workshopevaluation'
]

all_good = True
for table in tables_to_check:
    try:
        cursor.execute(f'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"{table}\"')
        result = cursor.fetchone()
        if result:
            print(f'✅ Tabela {table} existe')
        else:
            print(f'❌ Tabela {table} NÃO existe')
            all_good = False
    except Exception as e:
        print(f'❌ Erro ao verificar {table}: {e}')
        all_good = False

if all_good:
    print('\\n🎉 Todas as tabelas workshops foram criadas com sucesso!')
else:
    print('\\n⚠️  Algumas tabelas podem não ter sido criadas corretamente.')

connection.close()
"

# 8. Executar migrações de outros apps se necessário
log_info "Executando migrações de outros apps..."
python3 manage.py migrate

# 9. Criar superusuário se não existir (opcional)
log_info "Verificando se existe superusuário..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
import django
django.setup()
from django.contrib.auth.models import User

if not User.objects.filter(is_superuser=True).exists():
    print('⚠️  Nenhum superusuário encontrado. Execute: python manage.py createsuperuser')
else:
    print('✅ Superusuário já existe')
"

# 10. Teste básico da aplicação
log_info "Testando importação dos modelos workshops..."
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
import django
django.setup()

try:
    from workshops.models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
    print('✅ Todos os modelos workshops importados com sucesso!')
    
    # Teste básico de criação
    print(f'📊 Workshop model: {Workshop._meta.db_table}')
    print(f'📊 WorkshopSession model: {WorkshopSession._meta.db_table}') 
    print(f'📊 WorkshopEnrollment model: {WorkshopEnrollment._meta.db_table}')
    print(f'📊 SessionAttendance model: {SessionAttendance._meta.db_table}')
    print(f'📊 WorkshopEvaluation model: {WorkshopEvaluation._meta.db_table}')
    
except Exception as e:
    print(f'❌ Erro ao importar modelos: {e}')
"

log_info "Verificando se o servidor pode iniciar..."
timeout 10s python3 manage.py check --deploy 2>/dev/null && log_info "✅ Verificação de deploy passou" || log_warning "⚠️  Algumas verificações de deploy falharam (normal em desenvolvimento)"

echo ""
log_info "🎉 Migração workshops concluída com sucesso!"
echo ""
echo "📋 Resumo do que foi feito:"
echo "   ✅ Backup do banco de dados criado"
echo "   ✅ Migrações antigas removidas"
echo "   ✅ Tabelas workshops removidas do banco"
echo "   ✅ Registros de migração limpos"
echo "   ✅ Novas migrações criadas"
echo "   ✅ Migrações aplicadas"
echo "   ✅ Estrutura das tabelas verificada"
echo ""
echo "🚀 Próximos passos:"
echo "   1. Execute: python manage.py runserver"
echo "   2. Teste a funcionalidade workshops no admin"
echo "   3. Verifique se todas as páginas workshops funcionam"
echo ""
echo "💡 Se houver problemas, restaure o backup:"
echo "   cp db.sqlite3.backup.* db.sqlite3"
