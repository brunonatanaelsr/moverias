#!/bin/bash
# filepath: /Users/brunonatanael/Desktop/02/install.sh

#########################################################
# Script de Instalação Completa do Move Marias
# Sistema de Gestão para o projeto Move Marias
# Domínio: move.squadsolucoes.com.br
# Repositório: https://github.com/brunonatanaelsr/02
#########################################################

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

# Função para verificar resultado do comando
check_result() {
    if [ $? -ne 0 ]; then
        error_log "$1"
        exit 1
    else
        log "$2"
    fi
}

# Banner de início
display_banner() {
    echo -e "${BOLD}"
    echo "======================================================================"
    echo "                    INSTALAÇÃO MOVE MARIAS                            "
    echo "======================================================================"
    echo -e "${NC}"
    echo -e "Este script instalará o sistema Move Marias em seu servidor."
    echo -e "Domínio: ${BOLD}$DOMAIN${NC}"
    echo -e "Repositório: ${BOLD}$REPO_URL${NC}"
    echo 
    echo -e "O processo inclui:"
    echo -e " - Instalação de dependências do sistema"
    echo -e " - Configuração do PostgreSQL"
    echo -e " - Deploy da aplicação Django"
    echo -e " - Configuração de Nginx com SSL"
    echo -e " - Configuração de monitoramento e backup"
    echo
    echo -e "Pressione ENTER para continuar ou CTRL+C para cancelar..."
    read -r
}

# Verifica se está rodando como root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        error_log "Este script precisa ser executado como root (sudo $0)"
        exit 1
    fi
}

# Função para atualizar o sistema
update_system() {
    log "Atualizando sistema..."
    apt-get update
    check_result "Falha ao atualizar pacotes" "Pacotes atualizados com sucesso"
    
    apt-get upgrade -y
    check_result "Falha ao fazer upgrade do sistema" "Sistema atualizado com sucesso"
}

# Instalação das dependências do sistema
install_dependencies() {
    log "Instalando dependências do sistema..."
    apt-get install -y curl build-essential libssl-dev libffi-dev python3-dev \
                      python3-pip python3-venv git nginx postgresql postgresql-contrib \
                      certbot python3-certbot-nginx libpq-dev supervisor redis-server \
                      libpangocairo-1.0-0 libcairo2 libpango-1.0-0 libmagickwand-dev \
                      libxml2-dev libxslt1-dev ufw fail2ban
                      
    check_result "Falha ao instalar dependências" "Dependências instaladas com sucesso"
    
    # Configurar timezone
    timedatectl set-timezone America/Sao_Paulo
    check_result "Falha ao configurar timezone" "Timezone configurada para America/Sao_Paulo"
}

# Configurar firewall
configure_firewall() {
    log "Configurando firewall..."
    ufw allow 'Nginx Full'
    ufw allow OpenSSH
    ufw --force enable
    check_result "Falha ao configurar firewall" "Firewall configurado com sucesso"
}

# Configurar PostgreSQL
setup_database() {
    log "Configurando PostgreSQL..."
    
    # Criar banco de dados
    sudo -u postgres psql -c "CREATE DATABASE $APP_NAME;" || {
        warning_log "Banco de dados '$APP_NAME' pode já existir, verificando..."
        DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$APP_NAME'")
        if [ "$DB_EXISTS" != "1" ]; then
            error_log "Falha ao criar banco de dados"
            exit 1
        else
            warning_log "Banco de dados já existe, continuando..."
        fi
    }

    # Criar usuário
    sudo -u postgres psql -c "CREATE USER $APP_NAME WITH PASSWORD '$POSTGRES_PASSWORD';" || {
        warning_log "Usuário '$APP_NAME' pode já existir, verificando..."
        USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$APP_NAME'")
        if [ "$USER_EXISTS" != "1" ]; then
            # Tentar atualizar senha se o usuário existe
            sudo -u postgres psql -c "ALTER USER $APP_NAME WITH PASSWORD '$POSTGRES_PASSWORD';" || {
                error_log "Falha ao configurar usuário do banco de dados"
                exit 1
            }
        fi
    }

    # Configurar usuário
    sudo -u postgres psql -c "ALTER ROLE $APP_NAME SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE $APP_NAME SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE $APP_NAME SET timezone TO 'America/Sao_Paulo';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $APP_NAME TO $APP_NAME;"
    
    log "Banco de dados PostgreSQL configurado com sucesso"
}

# Configurar diretórios da aplicação
setup_directories() {
    log "Configurando diretórios..."
    
    # Criar diretórios principais
    mkdir -p $APP_PATH
    mkdir -p /var/log/$APP_NAME
    mkdir -p $APP_PATH/backups
    
    # Configurar permissões iniciais
    chown -R www-data:www-data /var/log/$APP_NAME
    chmod -R 755 $APP_PATH
    
    log "Diretórios configurados com sucesso"
}

# Clonar repositório
clone_repository() {
    log "Clonando repositório $REPO_URL..."
    # Remover diretório se já existir (para reinstalação limpa)
    if [ -d "$APP_PATH/.git" ]; then
        warning_log "Repositório já existe. Atualizando..."
        # Corrigir problema de ownership para git safe.directory
        git config --global --add safe.directory $APP_PATH
        cd "$APP_PATH" || exit 1
        git fetch --all
        git reset --hard origin/main
    else
        git clone $REPO_URL $APP_PATH
        check_result "Falha ao clonar repositório" "Repositório clonado com sucesso"
    fi
    cd $APP_PATH || {
        error_log "Falha ao acessar diretório da aplicação"
        exit 1
    }
}

# Configurar ambiente virtual Python
setup_virtualenv() {
    log "Configurando ambiente virtual Python..."
    cd $APP_PATH || exit 1
    # Remover venv quebrada se existir
    if [ -d "venv" ]; then
        warning_log "Removendo venv existente para reinstalação limpa..."
        rm -rf venv
    fi
    # Checar se python3 está disponível
    if ! command -v python3 >/dev/null 2>&1; then
        error_log "Python3 não encontrado. Instale python3 antes de continuar."
        exit 1
    fi
    # Criar ambiente virtual
    python3 -m venv venv
    check_result "Falha ao criar ambiente virtual" "Ambiente virtual criado com sucesso"
    # Ativar ambiente virtual explicitamente
    source "$APP_PATH/venv/bin/activate"
    check_result "Falha ao ativar ambiente virtual" "Ambiente virtual ativado"
    # Atualizar pip
    "$APP_PATH/venv/bin/pip" install --upgrade pip
    check_result "Falha ao atualizar pip" "Pip atualizado com sucesso"
}

# Instalar dependências Python
install_python_dependencies() {
    log "Instalando dependências Python..."
    
    # Instalar do requirements.txt usando pip da venv
    $APP_PATH/venv/bin/pip install -r requirements.txt
    check_result "Falha ao instalar dependências do requirements.txt" "Dependências do requirements.txt instaladas"
    
    # Instalar pacotes adicionais
    log "Instalando pacotes Python adicionais..."
    $APP_PATH/venv/bin/pip install gunicorn psycopg2-binary redis django-redis
    check_result "Falha ao instalar pacotes adicionais" "Pacotes adicionais instalados"
}

# Configurar variáveis de ambiente
setup_environment() {
    log "Configurando variáveis de ambiente..."
    
    cat > $APP_PATH/.env << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=production

# Allowed Hosts
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Database 
DATABASE_URL=postgresql://$APP_NAME:$POSTGRES_PASSWORD@localhost:5432/$APP_NAME

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# Django Cryptography
DJANGO_CRYPTOGRAPHY_KEY=$CRYPTO_KEY

# S3 Storage (desabilitado por padrão)
USE_S3="False"

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=sistemainovax@gmail.com
EMAIL_HOST_PASSWORD=qnqwjdjiiuphlwoq

# Default email addresses
DEFAULT_FROM_EMAIL=Move Marias <noreply@squadsolucoes.com.br>
SERVER_EMAIL=Move Marias <server@squadsolucoes.com.br>
EOF

    log "Arquivo .env configurado com sucesso"
}

# Executar migrações Django
setup_django() {
    log "Configurando Django..."
    
    # Coletar arquivos estáticos
    $APP_PATH/venv/bin/python manage.py collectstatic --noinput
    check_result "Falha ao coletar arquivos estáticos" "Arquivos estáticos coletados com sucesso"
    
    # Aplicar migrações
    $APP_PATH/venv/bin/python manage.py migrate
    check_result "Falha ao aplicar migrações" "Migrações aplicadas com sucesso"
    
    # Criar superuser (admin)
    log "Criando superuser..."
    cat > create_superuser.py << EOF
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='$ADMIN_EMAIL').exists():
    User.objects.create_superuser('admin', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print("Superuser criado com sucesso!")
else:
    print("Superuser já existe!")
EOF

    $APP_PATH/venv/bin/python create_superuser.py
    check_result "Falha ao criar superuser" "Superuser criado/verificado com sucesso"
    rm create_superuser.py
}

# Configurar Gunicorn
setup_gunicorn() {
    log "Configurando Gunicorn..."
    
    cat > $APP_PATH/gunicorn_config.py << EOF
# Configuração do Gunicorn para Move Marias
bind = "unix:/var/run/$APP_NAME.sock"
workers = $(( 2 * $(nproc) + 1 ))
worker_class = "gthread"
threads = 2
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
errorlog = '/var/log/$APP_NAME/gunicorn-error.log'
accesslog = '/var/log/$APP_NAME/gunicorn-access.log'
capture_output = True
loglevel = 'info'
EOF

    log "Gunicorn configurado com sucesso"
}

# Configurar Supervisor
setup_supervisor() {
    log "Configurando Supervisor..."
    
    cat > /etc/supervisor/conf.d/$APP_NAME.conf << EOF
[program:$APP_NAME]
command=/var/www/$APP_NAME/venv/bin/gunicorn movemarias.wsgi:application -c /var/www/$APP_NAME/gunicorn_config.py
directory=/var/www/$APP_NAME
user=www-data
autostart=true
autorestart=true
startretries=5
redirect_stderr=true
stdout_logfile=/var/log/$APP_NAME/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=LANG=pt_BR.UTF-8,LC_ALL=pt_BR.UTF-8,LC_LANG=pt_BR.UTF-8

[program:$APP_NAME-worker]
command=/var/www/$APP_NAME/venv/bin/python manage.py rqworker default
directory=/var/www/$APP_NAME
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/$APP_NAME/worker.log
stopwaitsecs=60
EOF

    # Recarregar supervisor
    supervisorctl reread
    supervisorctl update
    
    log "Supervisor configurado com sucesso"
}

# Configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    # Criar arquivo de configuração
    cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Logs
    access_log /var/log/$APP_NAME/nginx-access.log;
    error_log /var/log/$APP_NAME/nginx-error.log;
    
    # Aumentar tamanho máximo de upload
    client_max_body_size 10M;
    
    # Favicon
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    # Arquivos estáticos
    location /static/ {
        alias /var/www/$APP_NAME/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Arquivos de mídia
    location /media/ {
        alias /var/www/$APP_NAME/media/;
    }
    
    # Proxy para Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/run/$APP_NAME.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 16k;
    }
    
    # Configurações de segurança
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
EOF

    # Ativar o site
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Verificar configuração
    nginx -t
    check_result "Configuração do Nginx está incorreta" "Configuração do Nginx verificada com sucesso"
}

# Configurar SSL com Certbot
setup_ssl() {
    log "Configurando SSL com Certbot..."
    
    # Reiniciar Nginx para aplicar configuração inicial
    systemctl restart nginx
    
    # Obter certificado SSL
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $SSL_EMAIL --redirect || {
        warning_log "Falha ao configurar SSL automaticamente. Você pode configurar manualmente depois."
    }
    
    log "Configuração SSL concluída"
}

# Configurar monitoramento e backup
setup_monitoring() {
    log "Configurando scripts de monitoramento e backup..."
    
    # Criar diretório para scripts
    mkdir -p $APP_PATH/deploy
    
    # Script de monitoramento
    cat > $APP_PATH/deploy/monitor.sh << EOF
#!/bin/bash
echo "=== Monitor Move Marias ==="
echo "Data: \$(date)"

# Cabeçalho colorido
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verifica status de um serviço
check_service() {
    local service=\$1
    local status=\$(systemctl is-active \$service)
    
    if [ "\$status" = "active" ]; then
        echo -e "- \$service: \${GREEN}ATIVO\${NC}"
    else
        echo -e "- \$service: \${RED}INATIVO\${NC}"
        systemctl status \$service | head -3
    fi
}

echo "Verificando serviços..."
check_service nginx
check_service supervisor
check_service postgresql
check_service redis-server

# Verificar uso de disco
echo -e "\nUso de disco:"
df -h / | grep -v "Filesystem"
DISK_USAGE=\$(df / | awk 'NR==2 {print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 85 ]; then
    echo -e "\${RED}ALERTA: Uso de disco acima de 85%\${NC}"
fi

# Verificar uso de memória
echo -e "\nUso de memória:"
free -m | grep "Mem:"
MEM_USAGE=\$(free | grep Mem | awk '{printf "%.0f", \$3/\$2 * 100.0}')
if [ \$MEM_USAGE -gt 90 ]; then
    echo -e "\${RED}ALERTA: Uso de memória acima de 90%\${NC}"
fi

# Verificar certificado SSL
echo -e "\nVerificação SSL:"
SSL_EXPIRY=\$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
echo "Certificado SSL expira em: \$SSL_EXPIRY"

# Verificar logs de erro
echo -e "\nÚltimos 5 erros nos logs:"
tail -5 /var/log/$APP_NAME/gunicorn-error.log

# Verificar se a aplicação está respondendo
echo -e "\nVerificação de saúde da aplicação:"
HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/)
if [ \$HTTP_CODE -eq 200 ]; then
    echo -e "Aplicação respondendo: \${GREEN}OK (\$HTTP_CODE)\${NC}"
else
    echo -e "Aplicação respondendo: \${RED}ERRO (\$HTTP_CODE)\${NC}"
fi

echo "Finalizado em \$(date)"
EOF

    chmod +x $APP_PATH/deploy/monitor.sh
    
    # Script de backup
    cat > $APP_PATH/deploy/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="$APP_PATH/backups"
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="\$BACKUP_DIR/backup_\$TIMESTAMP.sql"
MEDIA_BACKUP="\$BACKUP_DIR/media_\$TIMESTAMP.tar.gz"
CONFIG_BACKUP="\$BACKUP_DIR/config_\$TIMESTAMP.tar.gz"

# Criar diretório se não existir
mkdir -p \$BACKUP_DIR

# Backup do banco de dados
echo "Fazendo backup do banco de dados para \$BACKUP_FILE..."
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U $APP_NAME $APP_NAME > \$BACKUP_FILE
if [ \$? -ne 0 ]; then
    echo "ERRO: Falha ao fazer backup do banco de dados"
    exit 1
fi

# Compactar backup
gzip \$BACKUP_FILE
echo "Backup do banco compactado: \$BACKUP_FILE.gz"

# Backup dos arquivos de mídia
echo "Fazendo backup dos arquivos de mídia..."
tar -czf \$MEDIA_BACKUP -C $APP_PATH media
echo "Backup de mídia concluído: \$MEDIA_BACKUP"

# Backup das configurações
echo "Fazendo backup das configurações..."
tar -czf \$CONFIG_BACKUP /etc/nginx/sites-available/$DOMAIN /etc/supervisor/conf.d/$APP_NAME.conf $APP_PATH/.env
echo "Backup de configurações concluído: \$CONFIG_BACKUP"

# Manter apenas os últimos 7 backups diários
find \$BACKUP_DIR -name "backup_*.sql.gz" -type f -mtime +7 -delete
find \$BACKUP_DIR -name "media_*.tar.gz" -type f -mtime +7 -delete
find \$BACKUP_DIR -name "config_*.tar.gz" -type f -mtime +7 -delete

echo "Processo de backup concluído em \$(date)"

# Verificar espaço em disco após backup
DISK_USAGE=\$(df / | awk 'NR==2 {print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 85 ]; then
    echo "ALERTA: Uso de disco acima de 85% após backup. Considere limpar backups antigos."
fi
EOF

    chmod +x $APP_PATH/deploy/backup.sh
    
    # Adicionar cron jobs
    cat > /etc/cron.d/$APP_NAME << EOF
# Monitoramento a cada hora
0 * * * * root $APP_PATH/deploy/monitor.sh > /var/log/$APP_NAME/monitor.log 2>&1

# Backup diário às 2 da manhã
0 2 * * * root $APP_PATH/deploy/backup.sh > /var/log/$APP_NAME/backup.log 2>&1

# Health check a cada 5 minutos
*/5 * * * * root curl -s -o /dev/null https://$DOMAIN/ || echo "\$(date): Website não está respondendo" >> /var/log/$APP_NAME/health_check.log 2>&1

# Limpar logs antigos semanalmente
0 3 * * 0 root find /var/log/$APP_NAME -name "*.log" -type f -mtime +30 -delete

# Reiniciar serviços semanalmente para manter performance
0 4 * * 0 root systemctl restart nginx supervisor redis-server
EOF

    chmod 644 /etc/cron.d/$APP_NAME
    
    log "Scripts de monitoramento e backup configurados com sucesso"
}

# Configurar segurança adicional
setup_security() {
    log "Configurando segurança adicional..."
    
    # Configurar Fail2ban
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-botsearch]
enabled = true
EOF

    # Reiniciar Fail2ban
    systemctl restart fail2ban
    
    # Ajustar permissões
    chmod 600 $APP_PATH/.env
    chmod -R 755 $APP_PATH/staticfiles
    chmod -R 755 $APP_PATH/media
    chown -R www-data:www-data $APP_PATH
    
    log "Configurações de segurança adicionais aplicadas"
}

# Reiniciar serviços
restart_services() {
    log "Reiniciando todos os serviços..."
    
    systemctl restart supervisor
    check_result "Falha ao reiniciar Supervisor" "Supervisor reiniciado"
    
    systemctl restart nginx
    check_result "Falha ao reiniciar Nginx" "Nginx reiniciado"
    
    systemctl restart postgresql
    check_result "Falha ao reiniciar PostgreSQL" "PostgreSQL reiniciado"
    
    systemctl restart redis-server
    check_result "Falha ao reiniciar Redis" "Redis reiniciado"
    
    systemctl restart fail2ban
    check_result "Falha ao reiniciar Fail2ban" "Fail2ban reiniciado"
}

# Exibir resumo da instalação
show_summary() {
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    echo
    echo -e "${BOLD}===================== INSTALAÇÃO CONCLUÍDA! =====================${NC}"
    echo
    echo -e "${GREEN}Website:${NC} https://$DOMAIN"
    echo -e "${GREEN}Painel Admin:${NC} https://$DOMAIN/admin/"
    echo -e "${GREEN}IP do Servidor:${NC} $IP_ADDRESS"
    echo
    echo -e "${YELLOW}Credenciais de Acesso:${NC}"
    echo -e "Usuario Admin: ${BOLD}$ADMIN_EMAIL${NC}"
    echo -e "Senha Admin: ${BOLD}$ADMIN_PASSWORD${NC} (ALTERE IMEDIATAMENTE!)"
    echo
    echo -e "${BLUE}Informações do Sistema:${NC}"
    echo -e "Caminho da Aplicação: $APP_PATH"
    echo -e "Banco de Dados: PostgreSQL ($APP_NAME)"
    echo -e "Logs: /var/log/$APP_NAME/"
    echo -e "Backups: $APP_PATH/backups/ (diários às 2h da manhã)"
    echo
    echo -e "${BOLD}Comandos Úteis:${NC}"
    echo -e "- Verificar status: ${YELLOW}supervisorctl status${NC}"
    echo -e "- Logs de erro: ${YELLOW}tail -f /var/log/$APP_NAME/gunicorn-error.log${NC}"
    echo -e "- Backup manual: ${YELLOW}$APP_PATH/deploy/backup.sh${NC}"
    echo -e "- Monitoramento: ${YELLOW}$APP_PATH/deploy/monitor.sh${NC}"
    echo
    echo -e "${RED}IMPORTANTE: Altere a senha do admin imediatamente após o primeiro login!${NC}"
    echo
    echo -e "${BOLD}=============================================================${NC}"
}

# Função principal
main() {
    # Configurações
    DOMAIN="move.squadsolucoes.com.br"
    APP_NAME="movemarias"
    REPO_URL="https://github.com/brunonatanaelsr/02.git"
    APP_PATH="/var/www/$APP_NAME"
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 16)
    SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9!@#$%^&*()-_=+' | head -c 50)
    CRYPTO_KEY=$(openssl rand -base64 24)
    ADMIN_EMAIL="admin@squadsolucoes.com.br"
    ADMIN_PASSWORD="Admin@$(date +%Y)!"
    SSL_EMAIL="admin@squadsolucoes.com.br"
    
    # Verificar se é root
    check_root
    
    # Exibir banner
    display_banner
    
    # Iniciar instalação
    log "Iniciando instalação do Move Marias..."
    
    # Executar etapas de instalação
    update_system
    install_dependencies
    configure_firewall
    setup_database
    setup_directories
    clone_repository
    setup_virtualenv
    install_python_dependencies
    setup_environment
    setup_django
    setup_gunicorn
    setup_supervisor
    setup_nginx
    setup_ssl
    setup_monitoring
    setup_security
    restart_services
    
    # Mostrar resumo
    show_summary
}

# Executar script principal
main