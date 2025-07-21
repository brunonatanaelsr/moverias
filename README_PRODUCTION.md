# MoveMarias System - Production Deployment Guide

## 🚀 Sistema Modernizado e Otimizado

### Resumo das Implementações

O sistema MoveMarias foi completamente modernizado com as seguintes funcionalidades principais:

#### 1. **Sistema de Design Unificado**
- **Tailwind CSS**: Framework CSS moderno e responsivo
- **Componentes Reutilizáveis**: Templates base modernos
- **Design System**: Cores, tipografia e componentes padronizados
- **Responsividade**: Totalmente adaptável a diferentes dispositivos

#### 2. **Sistema de Monitoramento Avançado**
- **Dashboard de Monitoramento**: Interface administrativa completa
- **Widgets de Monitoramento**: Status do sistema, performance, jobs
- **Alertas em Tempo Real**: Notificações por email e dashboard
- **Métricas de Performance**: CPU, memória, disco, database
- **Logs Estruturados**: Sistema de logging avançado

#### 3. **Sistema de Cache Inteligente**
- **Cache Multi-nível**: Página, view, modelo e query
- **Cache Optimizer**: Otimização automática baseada em padrões
- **Cache Warmup**: Pré-carregamento de dados frequentes
- **Invalidação Inteligente**: Limpeza automática quando necessário

#### 4. **Sistema de Jobs em Background**
- **Jobs Personalizados**: Tarefas específicas do negócio
- **Agendamento Automático**: Execução programada
- **Monitoramento de Jobs**: Status e logs detalhados
- **Otimização de Performance**: Ajustes automáticos

#### 5. **Sistema de Validação Avançado**
- **Validação de CPF/CNPJ**: Formatação automática e validação
- **Validação de Telefone**: Máscaras e formatos brasileiros
- **Validação de CEP**: Integração com APIs de endereço
- **Validação de Email**: Verificação de formato e domínio

#### 6. **Integração de Dashboards**
- **Widgets Integrados**: Monitoramento em todos os dashboards
- **HR Dashboard**: Métricas de recursos humanos
- **Projects Dashboard**: Status de projetos
- **Workshops Dashboard**: Acompanhamento de workshops
- **Coaching Dashboard**: Planos de ação e rodas
- **Evolution Dashboard**: Métricas de evolução
- **Social Dashboard**: Anamnese social
- **Notifications Dashboard**: Central de notificações
- **Members Dashboard**: Gestão de beneficiários
- **Users Dashboard**: Administração de usuários

### Arquivos Principais

#### Templates Modernos
```
templates/
├── base_modern.html                    # Template base moderno
├── components/                         # Componentes reutilizáveis
│   ├── form_field.html
│   ├── status_card.html
│   └── metric_card.html
├── monitoring/                         # Templates de monitoramento
│   ├── dashboard.html                  # Dashboard principal
│   ├── widget.html                     # Widget genérico
│   ├── config.html                     # Configuração
│   └── widgets/                        # Widgets específicos
│       ├── system_status_compact.html
│       ├── performance_metrics_compact.html
│       ├── background_jobs_compact.html
│       └── alerts_compact.html
└── dashboards/                         # Dashboards modernizados
    ├── home_modern.html
    ├── hr/dashboard_modern.html
    ├── projects/project_list.html
    ├── workshops/workshop_list.html
    ├── coaching/action_plan_list.html
    ├── evolution/evolution_list.html
    ├── social/anamnesis_list.html
    ├── notifications/list.html
    ├── members/beneficiary_list.html
    └── users/user_list.html
```

#### Core System
```
core/
├── monitoring.py                       # Sistema de monitoramento
├── background_jobs.py                  # Jobs em background
├── cache_system.py                     # Sistema de cache
├── cache_optimizer.py                  # Otimizador de cache
├── validation.py                       # Sistema de validação
├── custom_jobs.py                      # Jobs personalizados
├── threshold_manager.py                # Gerenciador de thresholds
├── models.py                           # Modelos do sistema
├── monitoring_views.py                 # Views de monitoramento
├── monitoring_urls.py                  # URLs de monitoramento
├── templatetags/
│   └── monitoring_tags.py              # Tags de template
└── management/
    └── commands/
        ├── run_monitoring.py           # Comando de monitoramento
        ├── configure_email_alerts.py   # Configuração de emails
        ├── run_custom_jobs.py          # Execução de jobs
        └── finalize_system.py          # Finalização do sistema
```

#### Static Assets
```
static/
├── css/
│   ├── design-system.css               # Sistema de design
│   └── move-marias-contrast.css        # Tema de contraste
├── js/
│   ├── monitoring.js                   # JavaScript de monitoramento
│   └── dashboard.js                    # JavaScript de dashboard
└── img/
    └── logo-move-marias.png            # Logo do sistema
```

### Comandos de Gerenciamento

#### Monitoramento
```bash
# Executar monitoramento
python manage.py run_monitoring

# Monitoramento contínuo
python manage.py run_monitoring --continuous

# Teste do sistema
python manage.py run_monitoring --test
```

#### Jobs Personalizados
```bash
# Executar jobs de negócio
python manage.py run_custom_jobs --schedule-business-jobs

# Executar job específico
python manage.py run_custom_jobs --run-job beneficiary_follow_up

# Otimizar cache
python manage.py run_custom_jobs --optimize-cache

# Ajustar thresholds
python manage.py run_custom_jobs --adjust-thresholds

# Status do sistema
python manage.py run_custom_jobs --status
```

#### Configuração de Email
```bash
# Configurar alertas por email
python manage.py configure_email_alerts

# Testar configuração de email
python manage.py configure_email_alerts --test
```

### Deployment

#### Desenvolvimento
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Executar servidor de desenvolvimento
python manage.py runserver
```

#### Produção
```bash
# Usar configurações de produção
export DJANGO_SETTINGS_MODULE=movemarias.settings_production

# Executar deployment completo
sudo ./deploy/production_deploy_complete.sh

# Verificar status dos serviços
systemctl status movemarias
systemctl status nginx
```

### Configuração de Ambiente

#### Variáveis de Ambiente (Produção)
```bash
# Database
export DB_NAME=movemarias_prod
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432

# Cache
export REDIS_URL=redis://127.0.0.1:6379/1

# Email
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_HOST_USER=your_email@gmail.com
export EMAIL_HOST_PASSWORD=your_app_password

# Admin
export ADMIN_EMAIL=admin@movemarias.com
export SERVER_EMAIL=server@movemarias.com

# Celery
export CELERY_BROKER_URL=redis://127.0.0.1:6379/0
export CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

### Monitoramento e Logs

#### Logs do Sistema
```bash
# Logs de produção
tail -f logs/production.log

# Logs de erro
tail -f logs/errors.log

# Logs do sistema
journalctl -u movemarias -f
```

#### Métricas de Performance
- **CPU**: Monitoramento em tempo real
- **Memória**: Uso e disponibilidade
- **Disco**: Espaço livre e uso
- **Database**: Tempo de query e conexões
- **Cache**: Hit/miss ratio e performance

### Recursos Implementados

#### ✅ Funcionalidades Completadas
- [x] Sistema de design unificado com Tailwind
- [x] Templates modernos e responsivos
- [x] Sistema de monitoramento completo
- [x] Cache inteligente e otimizado
- [x] Jobs em background personalizados
- [x] Sistema de validação avançado
- [x] Integração de widgets em dashboards
- [x] Comandos de gerenciamento
- [x] Configuração de produção
- [x] Script de deployment
- [x] Documentação completa
- [x] Testes automatizados
- [x] Logs estruturados
- [x] Alertas por email
- [x] Métricas de performance
- [x] Otimização automática

#### 🔧 Configurações Pós-Deployment
1. **Configurar domínio** em `ALLOWED_HOSTS`
2. **Configurar SSL/TLS** com Let's Encrypt
3. **Configurar emails** com credenciais reais
4. **Configurar backups** automatizados
5. **Configurar monitoramento externo** (opcional)

### Suporte e Manutenção

#### Comandos Úteis
```bash
# Verificar saúde do sistema
python manage.py run_monitoring --test

# Limpar cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Reiniciar serviços
sudo systemctl restart movemarias
sudo systemctl restart nginx

# Backup do banco
python manage.py dumpdata > backup.json

# Restaurar banco
python manage.py loaddata backup.json
```

#### Troubleshooting
- **Erro 500**: Verificar logs em `logs/errors.log`
- **Performance baixa**: Executar `run_custom_jobs --optimize-cache`
- **Alerts não funcionando**: Verificar configuração de email
- **Cache não funcionando**: Verificar conexão Redis

### Contato e Suporte

Para suporte técnico ou questões sobre o sistema:
- **Email**: admin@movemarias.com
- **Logs**: `/opt/movemarias/logs/`
- **Documentação**: Este arquivo README
- **Monitoramento**: `/monitoring/` no sistema

---

**MoveMarias System v2.0**  
*Sistema modernizado e otimizado para produção*  
*Desenvolvido com Django, Tailwind CSS e tecnologias modernas*
