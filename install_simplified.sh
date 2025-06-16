#!/bin/bash
# filepath: /Users/brunonatanael/Desktop/02/install_simplified.sh

#########################################################
# Script de Instalação Simplificada do Move Marias
# Sistema de Gestão para o projeto Move Marias
# 
# COMO USAR:
# 1. Edite o arquivo config.sh com suas configurações
# 2. Execute: sudo ./install_simplified.sh
#########################################################

# Carregar configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/config.sh" ]; then
    source "$SCRIPT_DIR/config.sh"
else
    echo "ERRO: Arquivo config.sh não encontrado!"
    echo "Por favor, certifique-se de que o arquivo config.sh existe no mesmo diretório."
    exit 1
fi

# Cores para mensagens
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Funções de log
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error_log() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERRO: $1${NC}" >&2
}

warning_log() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] AVISO: $1${NC}"
}

info_log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificar se está rodando como root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        error_log "Este script precisa ser executado como root (sudo $0)"
        exit 1
    fi
}

# Gerar senhas seguras automaticamente
generate_passwords() {
    if [ -z "$DB_PASS" ]; then
        DB_PASS=$(openssl rand -base64 20 | tr -dc 'a-zA-Z0-9' | head -c 16)
    fi
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(openssl rand -base64 50 | tr -dc 'a-zA-Z0-9!@#$%^&*()-_=+' | head -c 50)
    fi
    if [ -z "$CRYPTO_KEY" ]; then
        CRYPTO_KEY=$(openssl rand -base64 32)
    fi
    if [ -z "$REDIS_PASS" ]; then
        REDIS_PASS=$(openssl rand -base64 20 | tr -dc 'a-zA-Z0-9' | head -c 16)
    fi
}

# Banner de início
display_banner() {
    echo -e "${BOLD}"
    echo "======================================================================"
    echo "              INSTALAÇÃO SIMPLIFICADA MOVE MARIAS                     "
    echo "======================================================================"
    echo -e "${NC}"
    echo -e "Configurações carregadas:"
    echo -e "Domínio: ${BOLD}$DOMAIN${NC}"
    echo -e "Email Admin: ${BOLD}$ADMIN_EMAIL${NC}"
    echo -e "Ambiente: ${BOLD}$ENVIRONMENT${NC}"
    echo -e "Repositório: ${BOLD}$REPO_URL${NC}"
    echo 
    echo -e "${YELLOW}Pressione ENTER para continuar ou CTRL+C para cancelar...${NC}"
    read -r
}

# Instalar pacotes essenciais
install_essentials() {
    log "Instalando pacotes essenciais..."
    apt-get update -y
    apt-get install -y curl wget git python3 python3-pip python3-venv \
                       postgresql postgresql-contrib nginx supervisor \
                       redis-server certbot python3-certbot-nginx \
                       ufw fail2ban build-essential libpq-dev
    
    # Configurar timezone
    timedatectl set-timezone "$SYSTEM_TIMEZONE"
    log "Pacotes essenciais instalados"
}

# Configuração automática do PostgreSQL
setup_database_auto() {
    log "Configurando PostgreSQL automaticamente..."
    
    # Criar banco e usuário
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
    
    # Configurações do usuário
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO '$SYSTEM_TIMEZONE';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    log "PostgreSQL configurado"
}

# Deploy da aplicação
deploy_application() {
    log "Fazendo deploy da aplicação..."
    
    # Criar diretórios
    mkdir -p "$PROJECT_DIR"
    mkdir -p "/var/log/$PROJECT_NAME"
    
    # Clonar ou atualizar repositório
    if [ -d "$PROJECT_DIR/.git" ]; then
        cd "$PROJECT_DIR"
        git pull origin "$BRANCH"
    else
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        git checkout "$BRANCH"
    fi
    
    # Criar ambiente virtual
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependências
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn psycopg2-binary redis django-redis
    
    # Criar diretórios de mídia
    mkdir -p staticfiles media
    chown -R www-data:www-data staticfiles media
    
    log "Aplicação deployada"
}

# Configurar ambiente
setup_environment_auto() {
    log "Configurando variáveis de ambiente..."
    
    cat > "$PROJECT_DIR/.env" << EOF
# Configurações automáticas do Move Marias
DEBUG=$DEBUG_MODE
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=$ENVIRONMENT

# Hosts permitidos
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Banco de dados
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME

# Redis
REDIS_URL=redis://localhost:6379/0

# Segurança
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
DJANGO_CRYPTOGRAPHY_KEY=$CRYPTO_KEY

# Armazenamento local (sem S3)
USE_S3=False

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT
EMAIL_USE_TLS=$EMAIL_USE_TLS
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL=Move Marias <noreply@squadsolucoes.com.br>
EOF
    
    chmod 600 "$PROJECT_DIR/.env"
    log "Ambiente configurado"
}

# Configurar Django
setup_django_auto() {
    log "Configurando Django..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Coletar arquivos estáticos e aplicar migrações
    python manage.py collectstatic --noinput
    python manage.py migrate
    
    # Criar superuser automaticamente
    cat > create_admin.py << 'EOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admin_email = os.getenv('ADMIN_EMAIL_ACCOUNT', 'admin@squadsolucoes.com.br')
admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@2025!')

if not User.objects.filter(email=admin_email).exists():
    user = User.objects.create_superuser(
        username='admin',
        email=admin_email,
        password=admin_password,
        first_name='Admin',
        last_name='MoveMarias'
    )
    print(f"Superuser criado: {admin_email}")
else:
    # Atualizar senha do usuário existente
    user = User.objects.get(email=admin_email)
    user.set_password(admin_password)
    user.save()
    print(f"Senha do superuser atualizada: {admin_email}")
EOF
    
    ADMIN_EMAIL_ACCOUNT="$ADMIN_EMAIL_ACCOUNT" ADMIN_PASSWORD="$ADMIN_PASSWORD" python create_admin.py
    rm create_admin.py
    
    log "Django configurado"
}

# Configurar serviços
setup_services_auto() {
    log "Configurando serviços (Gunicorn + Supervisor)..."
    
    # Calcular workers automaticamente
    if [ "$GUNICORN_WORKERS" = "auto" ]; then
        CALCULATED_WORKERS=$((2 * $(nproc) + 1))
    else
        CALCULATED_WORKERS="$GUNICORN_WORKERS"
    fi
    
    # Configuração do Gunicorn
    cat > "$PROJECT_DIR/gunicorn_config.py" << EOF
bind = "127.0.0.1:8000"
workers = $CALCULATED_WORKERS
worker_class = "sync"
timeout = $GUNICORN_TIMEOUT
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
errorlog = '/var/log/$PROJECT_NAME/gunicorn-error.log'
accesslog = '/var/log/$PROJECT_NAME/gunicorn-access.log'
capture_output = True
loglevel = 'info'
EOF
    
    # Configuração do Supervisor
    cat > "/etc/supervisor/conf.d/$PROJECT_NAME.conf" << EOF
[program:$PROJECT_NAME]
command=$PROJECT_DIR/venv/bin/gunicorn movemarias.wsgi:application -c $PROJECT_DIR/gunicorn_config.py
directory=$PROJECT_DIR
user=www-data
autostart=true
autorestart=true
startretries=5
redirect_stderr=true
stdout_logfile=/var/log/$PROJECT_NAME/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=LANG=pt_BR.UTF-8,LC_ALL=pt_BR.UTF-8
EOF
    
    # Recarregar supervisor
    supervisorctl reread
    supervisorctl update
    supervisorctl restart "$PROJECT_NAME"
    
    log "Serviços configurados"
}

# Configurar Nginx
setup_nginx_auto() {
    log "Configurando Nginx..."
    
    cat > "/etc/nginx/sites-available/$DOMAIN" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Logs
    access_log /var/log/$PROJECT_NAME/nginx-access.log;
    error_log /var/log/$PROJECT_NAME/nginx-error.log;
    
    # Upload size
    client_max_body_size $NGINX_CLIENT_MAX_BODY_SIZE;
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
    }
    
    # Application proxy
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_redirect off;
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 16k;
    }
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
}
EOF
    
    # Ativar site
    ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/"
    rm -f /etc/nginx/sites-enabled/default
    
    # Testar e recarregar
    nginx -t && systemctl reload nginx
    
    log "Nginx configurado"
}

# Configurar SSL
setup_ssl_auto() {
    log "Configurando SSL..."
    
    if [ "$SSL_REDIRECT" = "true" ]; then
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$SSL_EMAIL" --redirect || {
            warning_log "SSL falhou. Configuração manual necessária."
        }
    fi
    
    log "SSL processado"
}

# Configurar segurança básica
setup_security_auto() {
    log "Configurando segurança básica..."
    
    if [ "$UFW_ENABLED" = "true" ]; then
        ufw allow 'Nginx Full'
        ufw allow OpenSSH
        ufw --force enable
    fi
    
    if [ "$FAIL2BAN_ENABLED" = "true" ]; then
        systemctl enable fail2ban
        systemctl start fail2ban
    fi
    
    # Permissões
    chown -R www-data:www-data "$PROJECT_DIR"
    chmod 600 "$PROJECT_DIR/.env"
    
    log "Segurança configurada"
}

# Criar script de manutenção
create_maintenance_script() {
    log "Criando script de manutenção..."
    
    cat > "$PROJECT_DIR/maintenance.sh" << 'EOF'
#!/bin/bash
# Script de manutenção do Move Marias

case "$1" in
    status)
        echo "=== Status dos Serviços ==="
        systemctl status nginx --no-pager -l
        systemctl status supervisor --no-pager -l
        systemctl status postgresql --no-pager -l
        supervisorctl status
        ;;
    logs)
        echo "=== Últimos logs de erro ==="
        tail -20 /var/log/movemarias/gunicorn-error.log
        ;;
    restart)
        echo "=== Reiniciando serviços ==="
        supervisorctl restart movemarias
        systemctl reload nginx
        echo "Serviços reiniciados"
        ;;
    backup)
        echo "=== Fazendo backup ==="
        BACKUP_DIR="/var/www/movemarias/backups"
        mkdir -p "$BACKUP_DIR"
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        PGPASSWORD="DB_PASSWORD_HERE" pg_dump -U movemarias_user movemarias_db > "$BACKUP_DIR/backup_$TIMESTAMP.sql"
        echo "Backup salvo em: $BACKUP_DIR/backup_$TIMESTAMP.sql"
        ;;
    update)
        echo "=== Atualizando aplicação ==="
        cd /var/www/movemarias
        git pull origin main
        source venv/bin/activate
        pip install -r requirements.txt
        python manage.py migrate
        python manage.py collectstatic --noinput
        supervisorctl restart movemarias
        echo "Aplicação atualizada"
        ;;
    *)
        echo "Uso: $0 {status|logs|restart|backup|update}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  status  - Verificar status dos serviços"
        echo "  logs    - Mostrar últimos logs de erro"
        echo "  restart - Reiniciar serviços"
        echo "  backup  - Fazer backup do banco de dados"
        echo "  update  - Atualizar aplicação do repositório"
        ;;
esac
EOF
    
    chmod +x "$PROJECT_DIR/maintenance.sh"
    log "Script de manutenção criado em $PROJECT_DIR/maintenance.sh"
}

# Mostrar resumo final
show_final_summary() {
    echo
    echo -e "${BOLD}===================== INSTALAÇÃO CONCLUÍDA! =====================${NC}"
    echo
    echo -e "${GREEN}🌐 Website:${NC} https://$DOMAIN"
    echo -e "${GREEN}👤 Admin:${NC} https://$DOMAIN/admin/"
    echo
    echo -e "${YELLOW}📋 Credenciais de Acesso:${NC}"
    echo -e "Email: ${BOLD}$ADMIN_EMAIL_ACCOUNT${NC}"
    echo -e "Senha: ${BOLD}$ADMIN_PASSWORD${NC}"
    echo
    echo -e "${BLUE}🛠 Manutenção:${NC}"
    echo -e "Status: ${YELLOW}$PROJECT_DIR/maintenance.sh status${NC}"
    echo -e "Logs: ${YELLOW}$PROJECT_DIR/maintenance.sh logs${NC}"
    echo -e "Reiniciar: ${YELLOW}$PROJECT_DIR/maintenance.sh restart${NC}"
    echo -e "Backup: ${YELLOW}$PROJECT_DIR/maintenance.sh backup${NC}"
    echo -e "Atualizar: ${YELLOW}$PROJECT_DIR/maintenance.sh update${NC}"
    echo
    echo -e "${RED}⚠️  IMPORTANTE: Altere a senha do admin após o primeiro login!${NC}"
    echo
    echo -e "${BOLD}=============================================================${NC}"
}

# Função principal
main() {
    check_root
    generate_passwords
    display_banner
    
    log "Iniciando instalação simplificada do Move Marias..."
    
    install_essentials
    setup_database_auto
    deploy_application
    setup_environment_auto
    setup_django_auto
    setup_services_auto
    setup_nginx_auto
    setup_ssl_auto
    setup_security_auto
    create_maintenance_script
    
    show_final_summary
    
    log "Instalação concluída com sucesso!"
}

# Executar
main "$@"
