# Move Marias - Production Deployment Checklist

## 📋 PRÉ-PRODUÇÃO - CHECKLIST DE SEGURANÇA

### ✅ **STATUS ATUAL DO SISTEMA**

**🔧 FUNCIONALIDADES IMPLEMENTADAS:**
- ✅ Django 5.0.6 com todas as dependências atualizadas
- ✅ Sistema de autenticação com django-allauth
- ✅ Módulos principais: Beneficiárias, Projetos, Social, Coaching, Evolution, Workshops
- ✅ Dashboard com métricas e relatórios
- ✅ Interface responsiva com Tailwind CSS e HTMX
- ✅ Sistema de cache configurado (Redis/MemCache)
- ✅ Templates otimizados e corrigidos
- ✅ Views otimizadas com select_related e prefetch_related
- ✅ Middleware de segurança configurado

**⚠️ AJUSTES NECESSÁRIOS PARA PRODUÇÃO:**

### 🔐 **1. SEGURANÇA CRÍTICA**
```bash
# AÇÕES OBRIGATÓRIAS:
□ Gerar SECRET_KEY forte (50+ caracteres)
□ Definir DEBUG=False
□ Configurar ALLOWED_HOSTS
□ Configurar HTTPS obrigatório
□ Configurar CSRF_TRUSTED_ORIGINS
□ Gerar DJANGO_CRYPTOGRAPHY_KEY segura
```

### 🗄️ **2. BANCO DE DADOS**
```bash
# RECOMENDADO:
□ Migrar de SQLite para PostgreSQL
□ Configurar backup automático
□ Testar todas as migrações
```

### 🚀 **3. INFRAESTRUTURA**
```bash
# NECESSÁRIO:
□ Configurar servidor web (Nginx/Apache)
□ Configurar Gunicorn para WSGI
□ Configurar Redis para cache
□ Configurar logs de produção
□ Configurar monitoramento
```

---

## 🚀 **DEPLOY RÁPIDO PARA TESTE**

Para um deploy rápido de teste (não recomendado para produção real):

### **1. Configurar Variáveis de Ambiente**
```bash
# Criar arquivo .env
cp .env.production .env

# Editar com seus valores:
nano .env
```

### **2. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **3. Preparar Banco**
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### **4. Executar com Gunicorn**
```bash
gunicorn movemarias.wsgi:application --bind 0.0.0.0:8000
```

---

## 🔒 **CONFIGURAÇÃO DE PRODUÇÃO COMPLETA**

### **1. Servidor (Ubuntu/Debian)**
```bash
# Instalar dependências do sistema
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql redis-server

# Configurar PostgreSQL
sudo -u postgres createdb movemarias_prod
sudo -u postgres createuser movemarias_user
```

### **2. Configurar Nginx**
```nginx
# /etc/nginx/sites-available/movemarias
server {
    listen 80;
    server_name movemarias.org www.movemarias.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name movemarias.org www.movemarias.org;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/movemarias/staticfiles/;
    }
}
```

### **3. Configurar Systemd Service**
```ini
# /etc/systemd/system/movemarias.service
[Unit]
Description=Move Marias Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/movemarias
Environment=PATH=/path/to/movemarias/venv/bin
EnvironmentFile=/path/to/movemarias/.env
ExecStart=/path/to/movemarias/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 movemarias.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📊 **MONITORAMENTO E LOGS**

### **Logs de Aplicação**
```python
# Já configurado em logging_config.py
- Logs de erro em /var/log/movemarias/
- Logs de segurança
- Logs de performance
```

### **Monitoramento Básico**
```bash
# Verificar status
systemctl status movemarias
systemctl status nginx
systemctl status redis

# Verificar logs
tail -f /var/log/movemarias/django.log
tail -f /var/log/nginx/access.log
```

---

## 🔧 **MANUTENÇÃO**

### **Backup Regular**
```bash
# Backup do banco
python manage.py backup_database

# Backup de arquivos
tar -czf backup_$(date +%Y%m%d).tar.gz staticfiles/ media/
```

### **Atualizações**
```bash
# Atualizar código
git pull origin main

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviço
sudo systemctl restart movemarias
```

---

## 🏁 **CONCLUSÃO**

### **✅ O SISTEMA ESTÁ PRONTO PARA:**
- Deploy de desenvolvimento/teste
- Funcionalidades básicas de produção
- Interface de usuário completa
- Gestão de beneficiárias e projetos

### **⚠️ ANTES DA PRODUÇÃO REAL, CONFIGURE:**
- Certificado SSL
- Banco PostgreSQL
- Backup automático
- Monitoramento
- DNS e domínio

### **🚀 PRÓXIMOS PASSOS RECOMENDADOS:**
1. Configurar ambiente de staging
2. Testes de carga
3. Backup e restore
4. Documentação de usuário
5. Treinamento da equipe

---

**💡 DICA:** Para um MVP rápido, o sistema atual pode rodar com SQLite e Gunicorn, mas para produção séria, siga o checklist completo acima.
