# 🚀 MoveMarias VPS Installation Guide

## 📋 Pré-requisitos

- VPS Ubuntu 20.04+ ou Debian 11+
- Acesso root via SSH
- Domínio configurado apontando para o IP da VPS
- Mínimo 2GB RAM, 20GB disco
- **Armazenamento Local**: Todos os arquivos estáticos e media ficam na VPS (sem AWS S3)

## 🧪 Teste Local (Antes da VPS)

### Configurar ambiente local
```bash
# Clone o repositório
git clone https://github.com/brunonatanaelsr/02.git
cd 02

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente local
cp .env.local .env

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### Verificar funcionamento local
- **Site:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/
- **Arquivos estáticos:** Servidos pelo Django localmente

---

## 🔧 Instalação Automática na VPS (Recomendada)

### 1. Conectar na VPS
```bash
ssh root@SEU_IP_VPS
```

### 2. Baixar e executar o script de instalação
```bash
wget https://raw.githubusercontent.com/brunonatanaelsr/02/main/vps_install.sh
chmod +x vps_install.sh
./vps_install.sh
```

### 3. Aguardar a instalação completa
O script irá:
- Atualizar o sistema
- Instalar Python 3.10, PostgreSQL, Redis, Nginx
- Configurar o projeto Django
- Configurar SSL com Let's Encrypt
- Configurar firewall e monitoramento
- **Configurar armazenamento local** para arquivos estáticos e media

### 4. Acessar o sistema
- **Site:** https://move.squadsolucoes.com.br
- **Admin:** https://move.squadsolucoes.com.br/admin/
- **Usuário:** admin
- **Senha:** MoveMarias2025!

---

## 📁 Configuração de Arquivos Estáticos (Local)

### Estrutura de Diretórios
```
/var/www/movemarias/
├── staticfiles/          # Arquivos CSS, JS, imagens estáticas
├── media/               # Uploads de usuários
├── venv/               # Ambiente virtual Python
├── manage.py           # Django management
└── ...                 # Código da aplicação
```

### Verificar Configuração
```bash
# Script automático de verificação
cd /var/www/movemarias
wget https://raw.githubusercontent.com/brunonatanaelsr/02/main/check_static_files.sh
chmod +x check_static_files.sh
sudo ./check_static_files.sh
```

### Comandos Manuais
```bash
# Verificar diretórios
ls -la /var/www/movemarias/staticfiles/
ls -la /var/www/movemarias/media/

# Verificar permissões
sudo chown -R www-data:www-data /var/www/movemarias/staticfiles
sudo chown -R www-data:www-data /var/www/movemarias/media
sudo chmod -R 755 /var/www/movemarias/staticfiles
sudo chmod -R 755 /var/www/movemarias/media

# Recoletar arquivos estáticos
cd /var/www/movemarias
source venv/bin/activate
python manage.py collectstatic --noinput
```

### Nginx Serve Arquivos Localmente
O Nginx está configurado para servir arquivos diretamente do sistema de arquivos:
- **Static files**: `/static/` → `/var/www/movemarias/staticfiles/`
- **Media files**: `/media/` → `/var/www/movemarias/media/`
- **Cache headers**: Configurados para performance otimizada

---

## ⚙️ Instalação Manual

### 1. Atualizar Sistema
```bash
apt update && apt upgrade -y
apt install -y software-properties-common curl wget gnupg2
```

### 2. Instalar Python 3.10
```bash
apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
apt install -y build-essential libssl-dev libffi-dev libpq-dev
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

### 3. Instalar Dependências do Sistema
```bash
apt install -y \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    redis-server \
    supervisor \
    postgresql \
    postgresql-contrib \
    fail2ban \
    ufw \
    htop \
    unzip
```

### 4. Configurar PostgreSQL
```bash
# Conectar como usuário postgres
sudo -u postgres psql

# Criar database e usuário
CREATE DATABASE movemarias_prod;
CREATE USER movemarias_user WITH ENCRYPTED PASSWORD 'SUA_SENHA_SEGURA';
GRANT ALL PRIVILEGES ON DATABASE movemarias_prod TO movemarias_user;
ALTER USER movemarias_user CREATEDB;
\q
```

### 5. Configurar Redis
```bash
# Editar configuração do Redis
nano /etc/redis/redis.conf

# Adicionar/modificar:
maxmemory 256mb
maxmemory-policy allkeys-lru

# Reiniciar Redis
systemctl restart redis-server
systemctl enable redis-server
```

### 6. Clonar e Configurar Projeto
```bash
# Clonar repositório
git clone https://github.com/brunonatanaelsr/02.git /var/www/movemarias
cd /var/www/movemarias

# Criar ambiente virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Configurar ambiente
cp .env.vps .env
nano .env  # Editar com suas configurações
```

### 7. Configurar Django
```bash
cd /var/www/movemarias
source venv/bin/activate

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário
python manage.py createsuperuser

# Configurar permissões
chown -R www-data:www-data /var/www/movemarias
chmod 755 /var/www/movemarias
chmod 600 /var/www/movemarias/.env
```

### 8. Configurar Gunicorn
```bash
# Criar diretório de logs
mkdir -p /var/log/movemarias
chown www-data:www-data /var/log/movemarias

# Copiar arquivo de serviço
cp /var/www/movemarias/deploy/movemarias.service /etc/systemd/system/

# Ativar serviço
systemctl daemon-reload
systemctl enable movemarias
systemctl start movemarias
systemctl status movemarias
```

### 9. Configurar Nginx
```bash
# Copiar configuração
cp /var/www/movemarias/deploy/nginx.conf /etc/nginx/sites-available/movemarias

# Ativar site
ln -sf /etc/nginx/sites-available/movemarias /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx
```

### 10. Configurar SSL
```bash
# Obter certificado SSL
certbot --nginx -d move.squadsolucoes.com.br -d www.move.squadsolucoes.com.br

# Configurar renovação automática
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 11. Configurar Firewall
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

---

## 🔍 Verificação da Instalação

### Verificar Serviços
```bash
systemctl status nginx
systemctl status movemarias
systemctl status postgresql
systemctl status redis-server
```

### Verificar Logs
```bash
# Logs da aplicação
journalctl -u movemarias -f

# Logs do Nginx
tail -f /var/log/nginx/error.log

# Logs do sistema
tail -f /var/log/syslog
```

### Testar Conectividade
```bash
curl -I https://move.squadsolucoes.com.br
```

---

## 🛠️ Manutenção

### Atualizar Aplicação
```bash
cd /var/www/movemarias
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart movemarias
```

### Backup do Banco de Dados
```bash
pg_dump -U movemarias_user movemarias_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Monitoramento
```bash
# CPU e Memória
htop

# Espaço em disco
df -h

# Status dos serviços
systemctl status nginx movemarias postgresql redis-server
```

---

## 🚨 Troubleshooting

### Serviço não inicia
```bash
# Verificar logs detalhados
journalctl -u movemarias -l --no-pager

# Verificar configuração
python manage.py check --deploy
```

### Erro 502 Bad Gateway
```bash
# Verificar se Gunicorn está rodando
systemctl status movemarias

# Verificar logs do Nginx
tail -f /var/log/nginx/error.log
```

### Problemas de permissão
```bash
chown -R www-data:www-data /var/www/movemarias
chmod 755 /var/www/movemarias
chmod 600 /var/www/movemarias/.env
```

---

## 📞 Suporte

Para problemas ou dúvidas:
- Verificar logs primeiro
- Consultar documentação do Django
- Criar issue no repositório do projeto

---

## 🔒 Segurança

### Configurações Importantes
- ✅ Firewall configurado
- ✅ SSL/HTTPS obrigatório
- ✅ Headers de segurança
- ✅ Rate limiting
- ✅ Fail2ban ativo
- ✅ Senhas seguras
- ✅ Atualizações automáticas

### Recomendações
1. Alterar senha padrão do admin
2. Configurar backups automáticos
3. Monitorar logs regularmente
4. Manter sistema atualizado
5. Usar autenticação por chave SSH
