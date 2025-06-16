#!/bin/bash
# Move Marias - Deploy Update Script
# Script para fazer deploy das atualizações na VPS

set -e

# Configurações
VPS_USER="root"  # ou seu usuário na VPS
VPS_HOST=""      # IP ou domínio da sua VPS
PROJECT_DIR="/var/www/movemarias"
BACKUP_DIR="/var/backups/movemarias"
SERVICE_NAME="movemarias"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções de log
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Verificar se o host da VPS foi configurado
check_vps_config() {
    if [ -z "$VPS_HOST" ]; then
        error "Configure o VPS_HOST no início do script"
    fi
    
    log "Verificando conexão com a VPS..."
    if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'Conexão OK'" > /dev/null 2>&1; then
        error "Não foi possível conectar à VPS. Verifique as configurações SSH."
    fi
    log "Conexão com VPS estabelecida ✓"
}

# Fazer backup local antes do deploy
create_local_backup() {
    log "Criando backup local..."
    
    # Criar diretório de backup se não existir
    mkdir -p ./backups
    
    # Backup do banco de dados
    if [ -f "db.sqlite3" ]; then
        cp db.sqlite3 "./backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
        log "Backup do banco de dados criado ✓"
    fi
    
    # Backup de arquivos estáticos se existirem
    if [ -d "media" ]; then
        tar -czf "./backups/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz" media/
        log "Backup de arquivos de media criado ✓"
    fi
}

# Fazer backup remoto
create_remote_backup() {
    log "Criando backup remoto na VPS..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        # Criar diretório de backup
        mkdir -p /var/backups/movemarias
        
        # Parar o serviço
        sudo systemctl stop movemarias || true
        
        # Backup do banco de dados
        if [ -f "/var/www/movemarias/db.sqlite3" ]; then
            cp /var/www/movemarias/db.sqlite3 "/var/backups/movemarias/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
            echo "Backup do banco remoto criado"
        fi
        
        # Backup de arquivos de media
        if [ -d "/var/www/movemarias/media" ]; then
            tar -czf "/var/backups/movemarias/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C /var/www/movemarias media/
            echo "Backup de media remoto criado"
        fi
        
        # Backup do código atual
        tar -czf "/var/backups/movemarias/code_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C /var/www movemarias/ --exclude=movemarias/__pycache__ --exclude=movemarias/*/__pycache__ --exclude=movemarias/venv
        echo "Backup do código remoto criado"
EOF
    
    log "Backup remoto criado ✓"
}

# Enviar arquivos para a VPS
sync_files() {
    log "Sincronizando arquivos com a VPS..."
    
    # Excluir arquivos desnecessários do sync
    rsync -avz --progress \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='.git/' \
        --exclude='venv/' \
        --exclude='env/' \
        --exclude='node_modules/' \
        --exclude='.DS_Store' \
        --exclude='*.log' \
        --exclude='backups/' \
        --exclude='db.sqlite3' \
        ./ $VPS_USER@$VPS_HOST:$PROJECT_DIR/
    
    log "Arquivos sincronizados ✓"
}

# Atualizar dependências e aplicar migrações
update_dependencies() {
    log "Atualizando dependências e aplicando migrações..."
    
    ssh $VPS_USER@$VPS_HOST << EOF
        cd $PROJECT_DIR
        
        # Ativar ambiente virtual
        source venv/bin/activate
        
        # Atualizar dependências
        pip install -r requirements.txt
        
        # Aplicar migrações
        python manage.py migrate
        
        # Coletar arquivos estáticos
        python manage.py collectstatic --noinput
        
        # Criar superusuário se não existir (opcional)
        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin', 'admin@movemarias.com', 'admin123')" | python manage.py shell
        
        echo "Dependências atualizadas e migrações aplicadas"
EOF
    
    log "Dependências e migrações atualizadas ✓"
}

# Reiniciar serviços
restart_services() {
    log "Reiniciando serviços..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        # Reiniciar o serviço da aplicação
        sudo systemctl restart movemarias
        
        # Verificar se o serviço está rodando
        sleep 5
        if sudo systemctl is-active movemarias > /dev/null; then
            echo "Serviço movemarias está rodando ✓"
        else
            echo "ERRO: Serviço movemarias não está rodando"
            sudo systemctl status movemarias
            exit 1
        fi
        
        # Reiniciar nginx
        sudo systemctl reload nginx
        echo "Nginx recarregado ✓"
EOF
    
    log "Serviços reiniciados ✓"
}

# Verificar se a aplicação está funcionando
health_check() {
    log "Verificando saúde da aplicação..."
    
    sleep 10  # Aguardar a aplicação inicializar
    
    # Verificar se a aplicação responde
    if ssh $VPS_USER@$VPS_HOST "curl -f http://localhost:8000 > /dev/null 2>&1"; then
        log "Aplicação está respondendo ✓"
    else
        warning "Aplicação pode não estar respondendo corretamente"
        log "Verificando logs..."
        ssh $VPS_USER@$VPS_HOST "sudo journalctl -u movemarias --lines=20"
    fi
}

# Limpeza de arquivos antigos
cleanup() {
    log "Executando limpeza..."
    
    ssh $VPS_USER@$VPS_HOST << 'EOF'
        cd /var/www/movemarias
        
        # Limpar cache do Python
        find . -name "*.pyc" -delete
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        
        # Limpar logs antigos (manter últimos 30 dias)
        find /var/log/movemarias -name "*.log" -mtime +30 -delete 2>/dev/null || true
        
        # Limpar backups antigos (manter últimos 7 dias)
        find /var/backups/movemarias -name "*backup*" -mtime +7 -delete 2>/dev/null || true
        
        echo "Limpeza concluída"
EOF
    
    log "Limpeza executada ✓"
}

# Função principal
main() {
    info "=== Move Marias - Deploy Update ==="
    info "Iniciando processo de deploy..."
    
    # Verificar se as configurações estão corretas
    if [ -z "$VPS_HOST" ]; then
        echo ""
        echo "CONFIGURAÇÃO NECESSÁRIA:"
        echo "1. Edite este script e configure o VPS_HOST (IP ou domínio da sua VPS)"
        echo "2. Configure o VPS_USER se necessário (padrão: root)"
        echo ""
        read -p "Digite o IP ou domínio da sua VPS: " vps_input
        if [ -n "$vps_input" ]; then
            VPS_HOST="$vps_input"
        else
            error "VPS_HOST é obrigatório"
        fi
    fi
    
    # Executar etapas do deploy
    check_vps_config
    create_local_backup
    create_remote_backup
    sync_files
    update_dependencies
    restart_services
    health_check
    cleanup
    
    log "=== Deploy concluído com sucesso! ==="
    log "Aplicação atualizada e rodando na VPS"
    log "Acesse: http://$VPS_HOST"
}

# Verificar argumentos
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "backup")
        check_vps_config
        create_remote_backup
        ;;
    "sync")
        check_vps_config
        sync_files
        ;;
    "restart")
        check_vps_config
        restart_services
        ;;
    "health")
        check_vps_config
        health_check
        ;;
    "help")
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  deploy   - Deploy completo (padrão)"
        echo "  backup   - Criar apenas backup remoto"
        echo "  sync     - Sincronizar apenas arquivos"
        echo "  restart  - Reiniciar apenas serviços"
        echo "  health   - Verificar saúde da aplicação"
        echo "  help     - Mostrar esta ajuda"
        ;;
    *)
        error "Comando inválido. Use '$0 help' para ver os comandos disponíveis."
        ;;
esac
