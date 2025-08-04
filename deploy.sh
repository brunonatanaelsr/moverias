#!/bin/bash

# =============================================================================
# SCRIPT DE DEPLOY AUTOMÁTICO - MOVE MARIAS
# Versão: 2.0.0
# Servidor: move.squadsolucoes.com.br
# Data: 04 de Agosto de 2025
# =============================================================================

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_NAME="movemarias"
APP_DIR="/var/www/movemarias"
REPO_URL="https://github.com/brunonatanaelsr/moverias.git"
DOMAIN="move.squadsolucoes.com.br"
USER="movemarias"

# Funções de utilidade
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script deve ser executado como root (use sudo)"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Sistema operacional não suportado"
        exit 1
    fi
    
    . /etc/os-release
    if [[ $ID != "ubuntu" ]]; then
        log_warning "Sistema testado apenas no Ubuntu. Prosseguindo..."
    fi
}

# Função principal de setup
setup_system() {
    log_info "🚀 Iniciando setup do sistema..."
    
    # Atualizar sistema
    log_info "Atualizando sistema..."
    apt update && apt upgrade -y
    
    # Instalar dependências
    log_info "Instalando dependências..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        supervisor \
        git \
        curl \
        wget \
        unzip \
        certbot \
        python3-certbot-nginx \
        htop \
        iotop \
        apache2-utils
    
    log_success "Sistema atualizado e dependências instaladas!"
}

create_user() {
    log_info "🏗️ Criando usuário da aplicação..."
    
    if id "$USER" &>/dev/null; then
        log_warning "Usuário $USER já existe"
    else
        adduser --disabled-password --gecos "" $USER
        usermod -aG sudo $USER
        log_success "Usuário $USER criado!"
    fi
    
    # Criar diretórios
    mkdir -p $APP_DIR
    mkdir -p /var/log/$APP_NAME
    mkdir -p /var/backups/$APP_NAME
    
    chown -R $USER:$USER $APP_DIR
    chown -R $USER:$USER /var/log/$APP_NAME
    chown -R $USER:$USER /var/backups/$APP_NAME
    
    log_success "Diretórios criados e permissões configuradas!"
}

setup_database() {
    log_info "🗄️ Configurando PostgreSQL..."
    
    systemctl start postgresql
    systemctl enable postgresql
    
    # Criar banco e usuário
    sudo -u postgres psql -c "CREATE DATABASE ${APP_NAME}_prod;" 2>/dev/null || log_warning "Banco já existe"
    sudo -u postgres psql -c "CREATE USER ${APP_NAME}_user WITH PASSWORD 'changeme123';" 2>/dev/null || log_warning "Usuário já existe"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${APP_NAME}_prod TO ${APP_NAME}_user;"
    sudo -u postgres psql -c "ALTER USER ${APP_NAME}_user CREATEDB;"
    
    log_success "PostgreSQL configurado!"
}

setup_redis() {
    log_info "💭 Configurando Redis..."
    
    systemctl start redis-server
    systemctl enable redis-server
    
    # Configurar Redis
    sed -i 's/# requirepass foobared/requirepass redis123pass/' /etc/redis/redis.conf
    sed -i 's/daemonize no/daemonize yes/' /etc/redis/redis.conf
    
    systemctl restart redis-server
    
    log_success "Redis configurado!"
}

deploy_application() {
    log_info "📦 Fazendo deploy da aplicação..."
    
    # Mudar para usuário da aplicação
    sudo -u $USER bash << EOF
cd $APP_DIR

# Clone ou pull do repositório
if [ -d ".git" ]; then
    log_info "Atualizando código existente..."
    git pull origin main
else
    log_info "Clonando repositório..."
    git clone $REPO_URL .
fi

# Criar ambiente virtual
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Ativar ambiente virtual e instalar dependências
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn==21.2.0

# Configurar arquivo .env
if [ ! -f ".env" ]; then
    cp .env.production .env
    log_warning "Arquivo .env criado. EDITE AS CHAVES SECRETAS!"
fi

# Aplicar migrações
python manage.py migrate
python manage.py collectstatic --noinput

EOF

    log_success "Aplicação deployada!"
}

setup_nginx() {
    log_info "🌐 Configurando Nginx..."
    
    cat > /etc/nginx/sites-available/$APP_NAME << 'EOF'
server {
    listen 80;
    server_name move.squadsolucoes.com.br www.move.squadsolucoes.com.br;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name move.squadsolucoes.com.br www.move.squadsolucoes.com.br;
    
    # SSL será configurado pelo Certbot
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    location /static/ {
        alias /var/www/movemarias/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    location /media/ {
        alias /var/www/movemarias/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
    
    location ~ /\. {
        deny all;
    }
}
EOF

    # Ativar site
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx configurado!"
}

setup_ssl() {
    log_info "🔒 Configurando SSL/TLS..."
    
    systemctl stop nginx
    
    # Obter certificado
    certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    systemctl start nginx
    
    # Configurar renovação automática
    (crontab -l 2>/dev/null; echo "30 2 * * * /usr/bin/certbot renew --quiet --nginx") | crontab -
    
    log_success "SSL/TLS configurado!"
}

setup_supervisor() {
    log_info "📊 Configurando Supervisor..."
    
    cat > /etc/supervisor/conf.d/$APP_NAME.conf << EOF
[program:$APP_NAME]
command=$APP_DIR/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 movemarias.wsgi:application
directory=$APP_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/$APP_NAME/gunicorn.log
stderr_logfile=/var/log/$APP_NAME/gunicorn_error.log
environment=PATH="$APP_DIR/venv/bin"
EOF

    supervisorctl reread
    supervisorctl update
    supervisorctl start $APP_NAME
    
    log_success "Supervisor configurado!"
}

setup_firewall() {
    log_info "🛡️ Configurando firewall..."
    
    ufw --force enable
    ufw allow ssh
    ufw allow 'Nginx Full'
    
    log_success "Firewall configurado!"
}

setup_monitoring() {
    log_info "📈 Configurando monitoramento..."
    
    cat > /usr/local/bin/monitor-$APP_NAME.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/movemarias/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Verificar Gunicorn
if ! pgrep -f "gunicorn.*movemarias" > /dev/null; then
    echo "$DATE - ERRO: Gunicorn não está rodando" >> $LOG_FILE
    supervisorctl restart movemarias
fi

# Verificar Redis
if ! redis-cli -a redis123pass ping > /dev/null 2>&1; then
    echo "$DATE - ERRO: Redis não está respondendo" >> $LOG_FILE
    systemctl restart redis-server
fi

# Verificar Nginx
if ! systemctl is-active --quiet nginx; then
    echo "$DATE - ERRO: Nginx não está ativo" >> $LOG_FILE
    systemctl restart nginx
fi

echo "$DATE - Monitoramento OK" >> $LOG_FILE
EOF

    chmod +x /usr/local/bin/monitor-$APP_NAME.sh
    
    # Configurar cron
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-$APP_NAME.sh") | crontab -
    
    log_success "Monitoramento configurado!"
}

setup_backup() {
    log_info "💾 Configurando backup..."
    
    cat > /usr/local/bin/backup-$APP_NAME.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/movemarias"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup do banco
pg_dump movemarias_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz -C /var/www/movemarias media/

# Remover backups antigos
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup concluído: $DATE"
EOF

    chmod +x /usr/local/bin/backup-$APP_NAME.sh
    
    # Configurar backup diário
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-$APP_NAME.sh >> /var/log/$APP_NAME/backup.log 2>&1") | crontab -
    
    log_success "Backup configurado!"
}

run_tests() {
    log_info "🧪 Executando testes..."
    
    # Testar Nginx
    nginx -t
    
    # Testar aplicação
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
        log_success "Aplicação respondendo!"
    else
        log_error "Aplicação não está respondendo"
    fi
    
    # Verificar serviços
    systemctl is-active --quiet nginx && log_success "Nginx ativo" || log_error "Nginx inativo"
    systemctl is-active --quiet redis-server && log_success "Redis ativo" || log_error "Redis inativo"
    supervisorctl status $APP_NAME | grep -q "RUNNING" && log_success "Gunicorn ativo" || log_error "Gunicorn inativo"
}

show_final_info() {
    echo ""
    log_success "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "=================================="
    echo "  INFORMAÇÕES DO SISTEMA"
    echo "=================================="
    echo "🌐 Site: https://$DOMAIN"
    echo "📁 Diretório: $APP_DIR"
    echo "👤 Usuário: $USER"
    echo "📊 Logs: /var/log/$APP_NAME/"
    echo "💾 Backups: /var/backups/$APP_NAME/"
    echo ""
    echo "=================================="
    echo "  COMANDOS ÚTEIS"
    echo "=================================="
    echo "📋 Status: sudo supervisorctl status"
    echo "🔄 Restart: sudo supervisorctl restart $APP_NAME"
    echo "📖 Logs: tail -f /var/log/$APP_NAME/gunicorn.log"
    echo "🔍 Monitor: systemctl status nginx redis-server"
    echo ""
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com as chaves secretas:"
    echo "   $APP_DIR/.env"
    echo ""
    log_warning "Não esqueça de configurar as chaves secretas no arquivo .env!"
}

# Menu principal
main() {
    echo "🚀 SCRIPT DE DEPLOY AUTOMÁTICO - MOVE MARIAS v2.0.0"
    echo "====================================================="
    echo ""
    echo "Este script irá configurar automaticamente:"
    echo "- Sistema operacional e dependências"
    echo "- Banco de dados PostgreSQL"
    echo "- Redis"
    echo "- Nginx com SSL"
    echo "- Supervisor"
    echo "- Firewall"
    echo "- Monitoramento e backup"
    echo ""
    
    read -p "Deseja continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    check_root
    check_os
    
    log_info "Iniciando deploy automático..."
    
    setup_system
    create_user
    setup_database
    setup_redis
    deploy_application
    setup_nginx
    setup_ssl
    setup_supervisor
    setup_firewall
    setup_monitoring
    setup_backup
    run_tests
    show_final_info
}

# Executar script
main "$@"
