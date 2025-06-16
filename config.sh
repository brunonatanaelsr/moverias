#!/bin/bash
# filepath: /Users/brunonatanael/Desktop/02/config.sh

#########################################################
# Arquivo de Configuração do Move Marias
# Edite este arquivo conforme suas necessidades
#########################################################

# CONFIGURAÇÕES PRINCIPAIS
DOMAIN="${DOMAIN:-move.squadsolucoes.com.br}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@squadsolucoes.com.br}"
SSL_EMAIL="${SSL_EMAIL:-admin@squadsolucoes.com.br}"

# CONFIGURAÇÕES DO SISTEMA
PROJECT_NAME="movemarias"
REPO_URL="https://github.com/brunonatanaelsr/02.git"
BRANCH="main"
PROJECT_DIR="/var/www/${PROJECT_NAME}"

# CONFIGURAÇÕES DO BANCO DE DADOS
DB_NAME="${PROJECT_NAME}_db"
DB_USER="${PROJECT_NAME}_user"
# Senhas serão geradas automaticamente para segurança
DB_PASS=""
REDIS_PASS=""
SECRET_KEY=""
CRYPTO_KEY=""

# CONFIGURAÇÕES DE USUÁRIO ADMIN PADRÃO
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin@$(date +%Y)!}"
ADMIN_FIRST_NAME="${ADMIN_FIRST_NAME:-Admin}"
ADMIN_LAST_NAME="${ADMIN_LAST_NAME:-MoveMarias}"
ADMIN_EMAIL_ACCOUNT="${ADMIN_EMAIL_ACCOUNT:-admin@squadsolucoes.com.br}"

# CONFIGURAÇÕES DE EMAIL (SMTP)
EMAIL_HOST="${EMAIL_HOST:-smtp.gmail.com}"
EMAIL_PORT="${EMAIL_PORT:-587}"
EMAIL_USE_TLS="${EMAIL_USE_TLS:-True}"
EMAIL_HOST_USER="${EMAIL_HOST_USER:-sistemainovax@gmail.com}"
EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD:-qnqwjdjiiuphlwoq}"

# CONFIGURAÇÕES DE MONITORAMENTO
MONITORING_ENABLED="${MONITORING_ENABLED:-true}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# CONFIGURAÇÕES DE PERFORMANCE
GUNICORN_WORKERS="${GUNICORN_WORKERS:-auto}"  # 'auto' calculará automaticamente
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
NGINX_CLIENT_MAX_BODY_SIZE="${NGINX_CLIENT_MAX_BODY_SIZE:-10M}"

# CONFIGURAÇÕES DE SEGURANÇA
FAIL2BAN_ENABLED="${FAIL2BAN_ENABLED:-true}"
UFW_ENABLED="${UFW_ENABLED:-true}"
SSL_REDIRECT="${SSL_REDIRECT:-true}"

# AMBIENTE DE DESENVOLVIMENTO/PRODUÇÃO
ENVIRONMENT="${ENVIRONMENT:-production}"
DEBUG_MODE="${DEBUG_MODE:-False}"

# TIMEZONE
SYSTEM_TIMEZONE="${SYSTEM_TIMEZONE:-America/Sao_Paulo}"

echo "Configurações carregadas para ${PROJECT_NAME} em ${ENVIRONMENT}"
