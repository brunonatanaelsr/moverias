# Deployment com Armazenamento Local - Move Marias

## Configuração Completa para VPS Ubuntu 22

Este documento descreve como fazer o deploy do sistema Move Marias usando **apenas armazenamento local** (sem AWS S3).

### ✅ Configurações Aplicadas

#### 1. Settings.py
- **USE_S3 = False** forçado no código
- **django-storages** e **boto3** removidos das dependências
- Configuração de armazenamento local:
  ```python
  STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
  DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
  ```

#### 2. Requirements.txt
- **Django 4.2.13 LTS** para compatibilidade com django-cryptography
- Removido `django-storages` e `boto3`
- Adicionado `psycopg2-binary` para PostgreSQL

#### 3. Script de Instalação (install.sh)
- Criação automática dos diretórios `staticfiles` e `media`
- Configuração de permissões corretas para www-data
- Configuração do Nginx para servir arquivos estáticos e media localmente

### 🚀 Instruções de Deployment

#### Passo 1: Conectar na VPS
```bash
ssh root@145.79.6.36
```

#### Passo 2: Fazer upload do repositório
```bash
# Opção 1: Clonar do GitHub (se já estiver commitado)
git clone https://github.com/seu-usuario/move-marias.git /var/www/movemarias

# Opção 2: Fazer upload via SCP
scp -r /Users/brunonatanael/Desktop/02/* root@145.79.6.36:/var/www/movemarias/
```

#### Passo 3: Executar o script de instalação
```bash
cd /var/www/movemarias
chmod +x install.sh
./install.sh
```

### 📁 Estrutura de Diretórios (Armazenamento Local)

```
/var/www/movemarias/
├── staticfiles/          # Arquivos estáticos (CSS, JS, imagens)
├── media/               # Uploads de usuários
├── backups/             # Backups automáticos
├── logs/                # Logs da aplicação
└── venv/                # Ambiente virtual Python
```

### 🔧 Configurações do Nginx

O script configura automaticamente o Nginx para servir:
- **Arquivos estáticos**: `/static/` → `/var/www/movemarias/staticfiles/`
- **Arquivos de media**: `/media/` → `/var/www/movemarias/media/`

### 📊 Monitoramento

O sistema inclui:
- **Supervisor** para gerenciar processos
- **Fail2ban** para segurança
- **Backup automático** diário (banco + media)
- **Monitoramento** de recursos

### 🔒 Segurança

- SSL/TLS automático via Let's Encrypt
- Firewall configurado (UFW)
- Logs de segurança
- Backup automático com retenção de 7 dias

### 📝 Checklist Pós-Deploy

1. ✅ Verificar se o site está acessível
2. ✅ Testar upload de arquivos (funcionalidade media)
3. ✅ Verificar coleta de arquivos estáticos
4. ✅ Testar login de administrador
5. ✅ Verificar SSL/HTTPS
6. ✅ Testar backup automático

### 🚨 Importantes

1. **Não usar AWS S3** - Sistema configurado para armazenamento local
2. **Django 4.2 LTS** - Versão compatível com django-cryptography
3. **Backup local** - Arquivos media incluídos no backup diário
4. **Permissões** - www-data tem acesso aos diretórios necessários

### 💡 Vantagens do Armazenamento Local

- **Simplicidade**: Sem configurações AWS
- **Custo**: Sem custos adicionais de S3
- **Performance**: Acesso direto aos arquivos
- **Controle**: Total controle sobre os dados
- **Backup**: Incluído no sistema de backup

### 🔧 Solução de Problemas

#### Problema: Arquivos estáticos não carregam
```bash
sudo -u www-data python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

#### Problema: Uploads não funcionam
```bash
sudo chown -R www-data:www-data /var/www/movemarias/media
sudo chmod -R 755 /var/www/movemarias/media
```

#### Problema: Permissões incorretas
```bash
sudo chown -R www-data:www-data /var/www/movemarias
sudo chmod -R 755 /var/www/movemarias
```

### 📞 Suporte

Para problemas técnicos, verificar:
1. Logs do Nginx: `/var/log/nginx/error.log`
2. Logs do Django: `/var/log/movemarias/django.log`
3. Status dos serviços: `systemctl status nginx supervisor postgresql redis`
