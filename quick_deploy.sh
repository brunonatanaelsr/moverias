#!/bin/bash
# Move Marias - Deploy Rápido via Git
# Script simplificado para deploy usando Git

set -e

# Configurações (CONFIGURE AQUI)
VPS_USER="root"                    # Usuário da VPS
VPS_HOST=""                        # IP ou domínio da VPS (OBRIGATÓRIO)
PROJECT_DIR="/var/www/movemarias"  # Diretório do projeto na VPS
GIT_BRANCH="main"                  # Branch para deploy

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
warning() { echo -e "${YELLOW}!${NC} $1"; }

# Verificar configuração
if [ -z "$VPS_HOST" ]; then
    echo "Configure o VPS_HOST no script antes de executar"
    read -p "Digite o IP/domínio da VPS agora: " VPS_HOST
    [ -z "$VPS_HOST" ] && error "VPS_HOST é obrigatório"
fi

echo "=== Move Marias - Deploy Rápido ==="
echo "VPS: $VPS_USER@$VPS_HOST"
echo "Diretório: $PROJECT_DIR"
echo ""

# Fazer commit local das mudanças
if [ -n "$(git status --porcelain)" ]; then
    echo "Há mudanças não commitadas. Fazendo commit automático..."
    git add .
    git commit -m "Deploy automático - $(date '+%Y-%m-%d %H:%M:%S')" || true
    log "Commit local realizado"
fi

# Deploy na VPS
log "Conectando à VPS e fazendo deploy..."

ssh $VPS_USER@$VPS_HOST << EOF
    set -e
    
    echo "=== Deploy na VPS ==="
    cd $PROJECT_DIR
    
    # Backup rápido
    echo "Criando backup..."
    cp db.sqlite3 "db_backup_\$(date +%Y%m%d_%H%M%S).sqlite3" 2>/dev/null || true
    
    # Parar serviço
    echo "Parando serviço..."
    sudo systemctl stop movemarias 2>/dev/null || true
    
    # Atualizar código
    echo "Atualizando código..."
    git fetch origin
    git reset --hard origin/$GIT_BRANCH
    
    # Ativar ambiente virtual e atualizar
    echo "Atualizando dependências..."
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    # Migrações e static
    echo "Aplicando migrações..."
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    
    # Reiniciar serviços
    echo "Reiniciando serviços..."
    sudo systemctl start movemarias
    sudo systemctl reload nginx
    
    # Verificar status
    sleep 3
    if sudo systemctl is-active movemarias > /dev/null; then
        echo "✓ Serviço movemarias rodando"
    else
        echo "✗ Problema com o serviço"
        sudo systemctl status movemarias --no-pager
    fi
    
    echo "=== Deploy concluído ==="
EOF

log "Deploy concluído com sucesso!"
log "Acesse: http://$VPS_HOST"
