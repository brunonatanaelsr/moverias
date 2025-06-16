# 🚀 Guia de Deploy - Move Marias

## Scripts Disponíveis

### 1. `quick_deploy.sh` - Deploy Rápido
**Recomendado para atualizações frequentes**

```bash
./quick_deploy.sh
```

**O que faz:**
- Commit automático das mudanças locais
- Atualiza código via Git na VPS
- Aplica migrações
- Reinicia serviços
- Deploy em ~30 segundos

### 2. `deploy_update.sh` - Deploy Completo
**Para atualizações grandes ou primeiro deploy**

```bash
./deploy_update.sh
```

**O que faz:**
- Backup completo (local + remoto)
- Sincronização completa de arquivos
- Atualização de dependências
- Migrações e coleta de estáticos
- Verificação de saúde
- Limpeza de arquivos

## ⚙️ Configuração Inicial

### 1. Configure os Scripts

Edite os arquivos e configure:

```bash
# Em quick_deploy.sh e deploy_update.sh
VPS_USER="root"                    # Seu usuário na VPS
VPS_HOST="SEU_IP_OU_DOMINIO"      # IP ou domínio da VPS
PROJECT_DIR="/var/www/movemarias"  # Diretório do projeto na VPS
```

### 2. Configure SSH (se ainda não fez)

```bash
# Gerar chave SSH (se não tiver)
ssh-keygen -t rsa -b 4096 -C "seu@email.com"

# Copiar chave para VPS
ssh-copy-id root@SEU_IP_VPS
```

### 3. Configurar Git na VPS (primeira vez)

```bash
ssh root@SEU_IP_VPS

# No servidor
cd /var/www/movemarias
git remote add origin https://github.com/SEU_USUARIO/movemarias.git
git branch --set-upstream-to=origin/main main
```

## 🎯 Fluxo de Deploy Recomendado

### Para mudanças pequenas (dia a dia):
```bash
# 1. Faça suas mudanças no código
# 2. Execute o deploy rápido
./quick_deploy.sh
```

### Para mudanças grandes:
```bash
# 1. Teste localmente
python manage.py runserver

# 2. Commit suas mudanças
git add .
git commit -m "Descrição das mudanças"
git push origin main

# 3. Deploy completo
./deploy_update.sh
```

## 📋 Comandos Úteis

### Verificar status na VPS:
```bash
ssh root@SEU_IP "sudo systemctl status movemarias"
```

### Ver logs da aplicação:
```bash
ssh root@SEU_IP "sudo journalctl -u movemarias -f"
```

### Backup manual:
```bash
./deploy_update.sh backup
```

### Reiniciar apenas os serviços:
```bash
./deploy_update.sh restart
```

## 🔧 Solução de Problemas

### Erro de permissão SSH:
```bash
chmod 600 ~/.ssh/id_rsa
ssh-add ~/.ssh/id_rsa
```

### Serviço não inicia:
```bash
ssh root@SEU_IP
sudo journalctl -u movemarias --lines=50
```

### Banco de dados com problema:
```bash
# Restaurar backup
ssh root@SEU_IP
cd /var/www/movemarias
cp db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
sudo systemctl restart movemarias
```

### Limpar cache:
```bash
ssh root@SEU_IP
cd /var/www/movemarias
source venv/bin/activate
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## 📝 Checklist Pré-Deploy

- [ ] Mudanças testadas localmente
- [ ] Migrações criadas se necessário
- [ ] Requirements.txt atualizado
- [ ] Arquivos estáticos atualizados
- [ ] Backup feito (automático nos scripts)
- [ ] VPS_HOST configurado nos scripts

## 🚨 Em Caso de Emergência

### Rollback rápido:
```bash
ssh root@SEU_IP
cd /var/www/movemarias
git reset --hard HEAD~1  # Volta 1 commit
sudo systemctl restart movemarias
```

### Restaurar backup:
```bash
ssh root@SEU_IP
cd /var/www/movemarias
# Listar backups
ls -la db_backup_*
# Restaurar
cp db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
sudo systemctl restart movemarias
```

## 📊 Monitoramento

Após o deploy, verifique:
- [ ] Site acessível
- [ ] Login funcionando
- [ ] Funcionalidades principais OK
- [ ] Logs sem erros críticos

---

## 🔄 Exemplo de Deploy Completo

```bash
# 1. Configurar (primeira vez)
vim quick_deploy.sh  # Configure VPS_HOST

# 2. Deploy
./quick_deploy.sh

# 3. Verificar
curl http://SEU_IP
```

**Pronto! Sua aplicação estará atualizada na VPS.**
