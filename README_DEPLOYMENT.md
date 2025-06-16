# Move Marias - Sistema de Gestão

Sistema completo de gestão para o projeto Move Marias, desenvolvido em Django com deploy automatizado.

## 🚀 Instalação Rápida (Produção)

### Pré-requisitos
- Servidor Ubuntu 20.04+ ou Debian 11+
- Acesso root (sudo)
- Domínio configurado apontando para o servidor

### Instalação Automática

1. **Clone o repositório:**
```bash
git clone https://github.com/brunonatanaelsr/02.git
cd 02
```

2. **Configure suas preferências (opcional):**
```bash
nano config.sh
```
Edite as seguintes variáveis conforme necessário:
- `DOMAIN` - Seu domínio (ex: meusite.com.br)
- `ADMIN_EMAIL` - Email do administrador
- `ADMIN_PASSWORD` - Senha do admin (será gerada automaticamente se não definida)

3. **Execute a instalação:**
```bash
sudo chmod +x install_simplified.sh
sudo ./install_simplified.sh
```

4. **Acesse o sistema:**
- Site: https://seudominio.com.br
- Admin: https://seudominio.com.br/admin/

## 🛠 Comandos de Manutenção

Após a instalação, use o script de manutenção:

```bash
# Verificar status dos serviços
/var/www/movemarias/maintenance.sh status

# Ver logs de erro
/var/www/movemarias/maintenance.sh logs

# Reiniciar serviços
/var/www/movemarias/maintenance.sh restart

# Fazer backup do banco
/var/www/movemarias/maintenance.sh backup

# Atualizar aplicação
/var/www/movemarias/maintenance.sh update
```

## 📋 Recursos do Sistema

### 🏠 Dashboard
- Visão geral do sistema
- Métricas e estatísticas
- Acesso rápido a funcionalidades

### 👥 Gestão de Membros
- Cadastro de participantes
- Acompanhamento de progresso
- Histórico de atividades

### 🎯 Coaching
- Sessões de coaching
- Planos de desenvolvimento
- Acompanhamento de metas

### 📈 Evolução
- Tracking de progresso
- Relatórios de desenvolvimento
- Análise de resultados

### 👔 Recursos Humanos
- Gestão de equipe
- Controle de atividades
- Relatórios de performance

### 🛠 Projetos
- Gestão de projetos
- Controle de tarefas
- Timeline de atividades

### 💬 Social
- Interações sociais
- Comunidade
- Networking

### 🎪 Workshops
- Programação de eventos
- Gestão de participantes
- Materiais e recursos

## 🔧 Configurações Técnicas

### Tecnologias Utilizadas
- **Backend:** Django 4.2 LTS
- **Banco de Dados:** PostgreSQL
- **Cache:** Redis
- **Web Server:** Nginx
- **Application Server:** Gunicorn
- **Process Manager:** Supervisor
- **SSL:** Let's Encrypt (Certbot)

### Estrutura de Arquivos
```
/var/www/movemarias/
├── venv/                 # Ambiente virtual Python
├── staticfiles/         # Arquivos estáticos
├── media/              # Uploads de usuários
├── backups/            # Backups automáticos
├── .env               # Variáveis de ambiente
├── gunicorn_config.py # Configuração Gunicorn
└── maintenance.sh     # Script de manutenção
```

### Logs do Sistema
```
/var/log/movemarias/
├── nginx-access.log     # Logs de acesso Nginx
├── nginx-error.log      # Logs de erro Nginx
├── gunicorn-access.log  # Logs de acesso Gunicorn
├── gunicorn-error.log   # Logs de erro Gunicorn
└── supervisor.log       # Logs do Supervisor
```

## 🔒 Segurança

O sistema inclui as seguintes medidas de segurança:

- **SSL/TLS:** Certificado automático Let's Encrypt
- **Firewall:** UFW configurado automaticamente
- **Fail2ban:** Proteção contra ataques de força bruta
- **Headers de Segurança:** X-Frame-Options, X-Content-Type-Options, etc.
- **CSRF Protection:** Proteção contra ataques CSRF
- **Senhas Seguras:** Geração automática de senhas fortes

## 📊 Monitoramento

### Backup Automático
- Backup diário do banco de dados (2h da manhã)
- Backup de arquivos de mídia
- Backup de configurações
- Retenção de 7 dias por padrão

### Health Checks
- Verificação de saúde a cada 5 minutos
- Monitoramento de serviços
- Alertas automáticos em caso de problemas

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Site não carrega:**
```bash
# Verificar status dos serviços
/var/www/movemarias/maintenance.sh status

# Verificar logs
/var/www/movemarias/maintenance.sh logs

# Reiniciar serviços
/var/www/movemarias/maintenance.sh restart
```

2. **Erro 502 Bad Gateway:**
```bash
# Verificar se o Gunicorn está rodando
sudo supervisorctl status movemarias

# Reiniciar Gunicorn
sudo supervisorctl restart movemarias
```

3. **Problemas de SSL:**
```bash
# Renovar certificado
sudo certbot renew

# Verificar configuração Nginx
sudo nginx -t
```

### Logs Úteis
```bash
# Logs em tempo real
tail -f /var/log/movemarias/gunicorn-error.log

# Logs do Nginx
tail -f /var/log/movemarias/nginx-error.log

# Status do sistema
systemctl status nginx supervisor postgresql redis
```

## 🔄 Atualizações

Para atualizar o sistema:

```bash
# Método automático
/var/www/movemarias/maintenance.sh update

# Método manual
cd /var/www/movemarias
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart movemarias
```

## 📞 Suporte

Para suporte técnico:
- **Email:** admin@squadsolucoes.com.br
- **Repository:** https://github.com/brunonatanaelsr/02

## 📄 Licença

Este projeto é propriedade da Squad Soluções e está licenciado para uso interno.

---

**Move Marias** - Transformando vidas através da tecnologia 💜
