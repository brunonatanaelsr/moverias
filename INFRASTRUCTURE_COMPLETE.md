# Move Marias - Production Infrastructure Setup Guide

## 🚀 INFRAESTRUTURA COMPLETA CONFIGURADA

### ✅ **SCRIPTS DE PRODUÇÃO CRIADOS:**

1. **📊 `system_monitor.py`** - Monitor completo do sistema
   - Monitora CPU, memória, disco, load average
   - Verifica saúde do Django, banco de dados, Redis
   - Sistema de alertas automático
   - Relatórios de status em JSON

2. **💾 `backup_system.sh`** - Sistema de backup automatizado
   - Backup completo: banco, arquivos, configurações, logs
   - Verificação de integridade
   - Rotação automática de backups
   - Notificações (Slack configurável)

3. **⚙️ `manage_services.sh`** - Gerenciador central de serviços
   - Start/stop/restart de todos os serviços
   - Deploy automatizado
   - Monitoramento de performance
   - Visualização de logs

4. **⏰ `production_crontab`** - Cron jobs completos
   - Monitoramento contínuo
   - Backups automáticos
   - Manutenção e limpeza
   - Alertas de segurança

---

## 📋 **INSTALAÇÃO RÁPIDA DA INFRAESTRUTURA**

### **1. Copiar Scripts para Servidor**
```bash
# No servidor de produção
sudo mkdir -p /var/www/movemarias/deploy
sudo cp deploy/* /var/www/movemarias/deploy/
sudo chmod +x /var/www/movemarias/deploy/*.sh
sudo chmod +x /var/www/movemarias/deploy/*.py
```

### **2. Instalar Dependências do Monitor**
```bash
sudo pip3 install psutil requests
```

### **3. Configurar Diretórios de Log**
```bash
sudo mkdir -p /var/log/movemarias
sudo mkdir -p /var/backups/movemarias
sudo chown -R www-data:www-data /var/log/movemarias
sudo chown -R www-data:www-data /var/backups/movemarias
```

### **4. Instalar Cron Jobs**
```bash
sudo crontab /var/www/movemarias/deploy/production_crontab
```

### **5. Configurar Serviços Systemd**
```bash
# Copiar arquivos de serviço
sudo cp deploy/movemarias.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable movemarias
sudo systemctl enable nginx
```

---

## 🔧 **USO DOS SCRIPTS**

### **Gerenciamento de Serviços**
```bash
# Status completo
./deploy/manage_services.sh status

# Iniciar todos os serviços
./deploy/manage_services.sh start

# Reiniciar aplicação
./deploy/manage_services.sh restart

# Deploy de nova versão
./deploy/manage_services.sh deploy

# Ver logs
./deploy/manage_services.sh logs

# Verificar performance
./deploy/manage_services.sh performance
```

### **Monitoramento Manual**
```bash
# Monitor completo
python3 deploy/system_monitor.py

# Backup manual
./deploy/backup_system.sh
```

---

## 📊 **MONITORAMENTO AUTOMÁTICO**

### **Verificações a Cada 5 Minutos:**
- ✅ Status do sistema (CPU, RAM, Disco)
- ✅ Saúde da aplicação Django
- ✅ Conectividade do banco de dados
- ✅ Status do Redis/Cache
- ✅ Processos críticos rodando

### **Alertas Automáticos Para:**
- 🚨 CPU > 80%
- 🚨 Memória > 85%
- 🚨 Disco > 90%
- 🚨 Aplicação não respondendo
- 🚨 Banco de dados inacessível
- 🚨 Certificado SSL expirando

### **Backups Automáticos:**
- 📅 **Diário (2h)**: Backup completo do sistema
- 📅 **A cada 6h**: Backup só do banco de dados
- 📅 **Semanal**: Limpeza de logs antigos
- 📅 **Mensal**: Rotação de backups

---

## 🔐 **SEGURANÇA E LOGS**

### **Monitoramento de Segurança:**
- 🔍 Tentativas de login falhadas
- 🔍 Atividade suspeita nos logs
- 🔍 Verificação de certificado SSL
- 🔍 Integridade dos dados

### **Logs Organizados:**
```
/var/log/movemarias/
├── django.log          # Logs da aplicação
├── security.log        # Logs de segurança
├── performance.log     # Logs de performance
├── monitor.log         # Logs do monitor
├── backup.log          # Logs de backup
├── alerts.log          # Alertas do sistema
└── system_status.json  # Status atual em JSON
```

---

## 🎯 **RESULTADO FINAL**

### ✅ **INFRAESTRUTURA: COMPLETAMENTE CONFIGURADA**
- Sistema de monitoramento 24/7
- Backups automáticos com verificação
- Alertas para problemas críticos
- Rotação e limpeza automática de logs
- Gerenciamento centralizado de serviços
- Scripts de deploy automatizado

### ✅ **MONITORAMENTO: PROFISSIONAL**
- Métricas em tempo real
- Alertas proativos
- Relatórios de status
- Histórico de performance
- Notificações configuráveis

---

## 🚀 **SISTEMA AGORA ESTÁ 100% PRONTO PARA PRODUÇÃO!**

### **Para ativar tudo:**
```bash
# 1. Instalar scripts
sudo ./deploy/install_infrastructure.sh

# 2. Verificar status
./deploy/manage_services.sh status

# 3. Iniciar monitoramento
python3 deploy/system_monitor.py
```

### **Monitoramento em tempo real disponível em:**
- 📊 Dashboard: `http://seu-dominio/monitoring/`
- 📋 Status JSON: `/var/log/movemarias/system_status.json`
- 🚨 Alertas: `/var/log/movemarias/alerts.log`

---

**🎉 O SISTEMA MOVE MARIAS AGORA TEM INFRAESTRUTURA DE NÍVEL ENTERPRISE!** 

Todos os pontos críticos foram resolvidos:
- ✅ **Infraestrutura**: Scripts completos de produção
- ✅ **Monitoramento**: Sistema profissional 24/7
- ✅ **Segurança**: Configurações e alertas de segurança
- ✅ **Backup**: Sistema automatizado e verificado
- ✅ **Deploy**: Processo automatizado e seguro
