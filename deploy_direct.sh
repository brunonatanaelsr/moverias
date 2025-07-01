#!/bin/bash

# Script de Deploy Direto para VPS - MoveMarias
# Este script transfere os arquivos diretamente da máquina local para a VPS

set -e

# Configurações
VPS_IP="145.79.6.36"
VPS_USER="root"
VPS_PATH="/var/www/movemarias"
LOCAL_PATH="/Users/brunonatanael/Desktop/MoveMarias/02"
DOMAIN="move.squadsolucoes.com.br"

echo "🚀 Iniciando deploy direto para VPS..."
echo "VPS: $VPS_IP"
echo "Usuário: $VPS_USER"
echo "Caminho VPS: $VPS_PATH"
echo "Caminho Local: $LOCAL_PATH"
echo "Domínio: $DOMAIN"

# Função para executar comandos na VPS
execute_on_vps() {
    ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "$1"
}

# Passo 1: Testar conexão SSH
echo "📡 Testando conexão SSH..."
execute_on_vps "echo 'Conexão SSH estabelecida com sucesso!'"

# Passo 2: Criar estrutura de diretórios na VPS
echo "📁 Criando estrutura de diretórios na VPS..."
execute_on_vps "mkdir -p $VPS_PATH"
execute_on_vps "mkdir -p $VPS_PATH/logs"
execute_on_vps "mkdir -p $VPS_PATH/backups"
execute_on_vps "mkdir -p $VPS_PATH/media"
execute_on_vps "mkdir -p $VPS_PATH/staticfiles"

# Passo 3: Transferir arquivos usando rsync
echo "📤 Transferindo arquivos para VPS..."
rsync -avz --progress \
    --exclude-from="$LOCAL_PATH/.rsync-exclude" \
    --delete \
    "$LOCAL_PATH/" \
    "$VPS_USER@$VPS_IP:$VPS_PATH/"

# Passo 4: Configurar permissões
echo "🔐 Configurando permissões..."
execute_on_vps "chown -R www-data:www-data $VPS_PATH"
execute_on_vps "chmod -R 755 $VPS_PATH"
execute_on_vps "chmod +x $VPS_PATH/manage.py"

# Passo 5: Instalar dependências do sistema
echo "📦 Instalando dependências do sistema..."
execute_on_vps "apt-get update -y"
execute_on_vps "apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev python3-setuptools nginx supervisor"

# Passo 6: Criar ambiente virtual Python
echo "🐍 Criando ambiente virtual Python..."
execute_on_vps "cd $VPS_PATH && python3 -m venv venv"
execute_on_vps "cd $VPS_PATH && source venv/bin/activate && pip install --upgrade pip"

# Passo 7: Instalar dependências Python
echo "📚 Instalando dependências Python..."
execute_on_vps "cd $VPS_PATH && source venv/bin/activate && pip install -r requirements.txt"

# Passo 8: Criar arquivo de configuração de produção
echo "⚙️ Criando configuração de produção..."
execute_on_vps "cat > $VPS_PATH/.env << 'EOF'
# Configuração de Produção - MoveMarias
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this-in-production
ALLOWED_HOSTS=$DOMAIN,$VPS_IP,localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email (configure conforme necessário)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Storage
USE_S3=False
MEDIA_URL=/media/
STATIC_URL=/static/

# Security (ajustar após configurar SSL)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False

# Domain
DOMAIN=$DOMAIN
EOF"

# Passo 9: Executar migrações Django
echo "🗄️ Executando migrações Django..."
execute_on_vps "cd $VPS_PATH && source venv/bin/activate && python manage.py migrate"

# Passo 10: Coletar arquivos estáticos
echo "📋 Coletando arquivos estáticos..."
execute_on_vps "cd $VPS_PATH && source venv/bin/activate && python manage.py collectstatic --noinput"

# Passo 11: Criar superusuário (opcional)
echo "👤 Para criar um superusuário, execute na VPS:"
echo "cd $VPS_PATH && source venv/bin/activate && python manage.py createsuperuser"

# Passo 12: Configurar Gunicorn
echo "🔧 Configurando Gunicorn..."
execute_on_vps "cat > $VPS_PATH/gunicorn_start.sh << 'EOF'
#!/bin/bash
NAME=\"movemarias\"
DJANGODIR=\"$VPS_PATH\"
SOCKFILE=\"$VPS_PATH/run/gunicorn.sock\"
USER=\"www-data\"
GROUP=\"www-data\"
NUM_WORKERS=3
DJANGO_SETTINGS_MODULE=\"movemarias.settings\"
DJANGO_WSGI_MODULE=\"movemarias.wsgi\"

echo \"Starting \$NAME as \`whoami\`\"

# Ativar ambiente virtual
cd \$DJANGODIR
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=\$DJANGO_SETTINGS_MODULE
export PYTHONPATH=\$DJANGODIR:\$PYTHONPATH

# Criar diretório de run se não existir
RUNDIR=\$(dirname \$SOCKFILE)
test -d \$RUNDIR || mkdir -p \$RUNDIR

# Iniciar Gunicorn
exec gunicorn \${DJANGO_WSGI_MODULE}:application \\
  --name \$NAME \\
  --workers \$NUM_WORKERS \\
  --user=\$USER --group=\$GROUP \\
  --bind=unix:\$SOCKFILE \\
  --log-level=info \\
  --log-file=-
EOF"

execute_on_vps "chmod +x $VPS_PATH/gunicorn_start.sh"
execute_on_vps "mkdir -p $VPS_PATH/run"

# Passo 13: Configurar serviço systemd
echo "🔧 Configurando serviço systemd..."
execute_on_vps "cat > /etc/systemd/system/movemarias.service << 'EOF'
[Unit]
Description=MoveMarias Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$VPS_PATH
ExecStart=$VPS_PATH/gunicorn_start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# Passo 14: Configurar Nginx
echo "🌐 Configurando Nginx..."
execute_on_vps "cat > /etc/nginx/sites-available/movemarias << 'EOF'
server {
    listen 80;
    server_name $DOMAIN $VPS_IP;
    
    client_max_body_size 20M;
    
    location /static/ {
        alias $VPS_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    
    location /media/ {
        alias $VPS_PATH/media/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    
    location / {
        proxy_pass http://unix:$VPS_PATH/run/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
}
EOF"

# Ativar site e remover default
execute_on_vps "ln -sf /etc/nginx/sites-available/movemarias /etc/nginx/sites-enabled/"
execute_on_vps "rm -f /etc/nginx/sites-enabled/default"

# Passo 15: Testar configuração Nginx
echo "🧪 Testando configuração Nginx..."
execute_on_vps "nginx -t"

# Passo 16: Iniciar serviços
echo "🚀 Iniciando serviços..."
execute_on_vps "systemctl daemon-reload"
execute_on_vps "systemctl enable movemarias"
execute_on_vps "systemctl start movemarias"
execute_on_vps "systemctl reload nginx"

# Passo 17: Verificar status dos serviços
echo "✅ Verificando status dos serviços..."
execute_on_vps "systemctl status movemarias --no-pager"
execute_on_vps "systemctl status nginx --no-pager"

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo ""
echo "📍 Próximos passos:"
echo "1. Acesse: http://$DOMAIN ou http://$VPS_IP"
echo "2. Crie um superusuário: cd $VPS_PATH && source venv/bin/activate && python manage.py createsuperuser"
echo "3. Configure SSL com Let's Encrypt (opcional)"
echo ""
echo "📊 Comandos úteis:"
echo "- Verificar logs: journalctl -u movemarias -f"
echo "- Reiniciar aplicação: systemctl restart movemarias"
echo "- Verificar aplicação: systemctl status movemarias"
echo ""
