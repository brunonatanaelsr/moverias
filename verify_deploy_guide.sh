#!/bin/bash
# Script para verificar se o guia de deploy está correto
# Verifica configurações, scripts e estrutura

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
warning() { echo -e "${YELLOW}!${NC} $1"; }

echo "=== Verificação do Guia de Deploy - Move Marias ==="
echo

# Verificar se scripts existem
echo "1. Verificando scripts de deploy..."
if [ -f "quick_deploy.sh" ]; then
    log "quick_deploy.sh existe"
    if [ -x "quick_deploy.sh" ]; then
        log "quick_deploy.sh é executável"
    else
        warning "quick_deploy.sh não é executável (chmod +x quick_deploy.sh)"
    fi
else
    error "quick_deploy.sh não encontrado"
fi

if [ -f "deploy_update.sh" ]; then
    log "deploy_update.sh existe"
    if [ -x "deploy_update.sh" ]; then
        log "deploy_update.sh é executável"
    else
        warning "deploy_update.sh não é executável (chmod +x deploy_update.sh)"
    fi
else
    error "deploy_update.sh não encontrado"
fi

echo
echo "2. Verificando configurações nos scripts..."

# Verificar VPS_HOST em quick_deploy.sh
if grep -q 'VPS_HOST=""' quick_deploy.sh; then
    warning "VPS_HOST não configurado em quick_deploy.sh"
else
    log "VPS_HOST configurado em quick_deploy.sh"
fi

# Verificar VPS_HOST em deploy_update.sh
if grep -q 'VPS_HOST=""' deploy_update.sh; then
    warning "VPS_HOST não configurado em deploy_update.sh"
else
    log "VPS_HOST configurado em deploy_update.sh"
fi

echo
echo "3. Verificando estrutura de deploy..."

if [ -d "deploy" ]; then
    log "Pasta deploy/ existe"
    
    files=("movemarias.service" "gunicorn.conf.py" "nginx.conf" "manage_services.sh")
    for file in "${files[@]}"; do
        if [ -f "deploy/$file" ]; then
            log "deploy/$file existe"
        else
            warning "deploy/$file não encontrado"
        fi
    done
else
    warning "Pasta deploy/ não encontrada"
fi

echo
echo "4. Verificando arquivos essenciais..."

essentials=("requirements.txt" "manage.py" "DEPLOY_GUIDE.md")
for file in "${essentials[@]}"; do
    if [ -f "$file" ]; then
        log "$file existe"
    else
        error "$file não encontrado"
    fi
done

echo
echo "5. Verificando configurações Django..."

if [ -f "movemarias/settings.py" ]; then
    log "settings.py encontrado"
    
    # Verificar ALLOWED_HOSTS
    if grep -q "ALLOWED_HOSTS" movemarias/settings.py; then
        log "ALLOWED_HOSTS configurado"
    else
        warning "ALLOWED_HOSTS pode não estar configurado"
    fi
    
    # Verificar STATIC_ROOT
    if grep -q "STATIC_ROOT" movemarias/settings.py; then
        log "STATIC_ROOT configurado"
    else
        warning "STATIC_ROOT pode não estar configurado"
    fi
else
    error "movemarias/settings.py não encontrado"
fi

echo
echo "6. Verificando Git..."

if [ -d ".git" ]; then
    log "Repositório Git inicializado"
    
    # Verificar remote origin
    if git remote get-url origin > /dev/null 2>&1; then
        origin=$(git remote get-url origin)
        log "Remote origin configurado: $origin"
    else
        warning "Remote origin não configurado"
    fi
    
    # Verificar branch
    branch=$(git branch --show-current)
    if [ "$branch" = "main" ]; then
        log "Branch atual: main ✓"
    else
        warning "Branch atual: $branch (recomendado: main)"
    fi
else
    error "Não é um repositório Git"
fi

echo
echo "7. Resumo das recomendações:"
echo

if grep -q 'VPS_HOST=""' quick_deploy.sh || grep -q 'VPS_HOST=""' deploy_update.sh; then
    echo "   • Configure VPS_HOST nos scripts antes do primeiro deploy"
fi

if [ ! -x "quick_deploy.sh" ] || [ ! -x "deploy_update.sh" ]; then
    echo "   • Torne os scripts executáveis: chmod +x *.sh"
fi

if ! git remote get-url origin > /dev/null 2>&1; then
    echo "   • Configure o remote Git: git remote add origin URL_DO_REPO"
fi

echo
echo "=== Verificação concluída ==="
echo "📖 Consulte DEPLOY_GUIDE.md para instruções detalhadas"
