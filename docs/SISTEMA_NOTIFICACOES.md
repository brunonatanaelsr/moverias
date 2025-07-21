# Sistema de Notificações - MoveMarias

## Visão Geral

O sistema de notificações do MoveMarias foi desenvolvido para fornecer comunicação em tempo real entre o sistema e os usuários, com suporte a múltiplos canais e tipos de notificação.

## Funcionalidades

### 1. Tipos de Notificação
- **welcome**: Boas-vindas para novos usuários
- **workshop_enrollment**: Confirmação de inscrição em workshops
- **workshop_reminder**: Lembretes de workshops próximos
- **certificate_ready**: Certificados prontos para download
- **project_invitation**: Convites para projetos
- **coaching_scheduled**: Agendamento de sessões de coaching
- **system_update**: Atualizações do sistema
- **password_reset**: Redefinição de senha
- **account_verification**: Verificação de conta
- **general**: Notificações gerais

### 2. Canais de Notificação
- **Web**: Notificações na interface web
- **Email**: Notificações por email
- **Push**: Notificações push (futuro)
- **SMS**: Notificações por SMS (futuro)

### 3. Níveis de Prioridade
- **Baixa (1)**: Informações não críticas
- **Normal (2)**: Notificações padrão
- **Alta (3)**: Notificações importantes
- **Urgente (4)**: Notificações críticas

## Estrutura do Sistema

### Models
- `NotificationChannel`: Canais de notificação disponíveis
- `NotificationTemplate`: Templates para diferentes tipos de notificação
- `Notification`: Notificações individuais
- `NotificationPreference`: Preferências de notificação do usuário

### Views
- `NotificationListView`: Lista de notificações do usuário
- `NotificationDetailView`: Detalhes de uma notificação
- `NotificationCreateView`: Criação de notificações (admin)
- `NotificationUpdateView`: Edição de notificações (admin)
- `NotificationDeleteView`: Exclusão de notificações
- `NotificationPreferenceView`: Configuração de preferências

### APIs AJAX
- `mark_as_read`: Marcar notificação como lida
- `mark_as_important`: Marcar/desmarcar como importante
- `mark_all_as_read`: Marcar todas como lidas
- `bulk_delete`: Exclusão em massa
- `bulk_mark_as_read`: Marcar múltiplas como lidas
- `notification_count`: Contador de não lidas
- `notification_popup`: Notificações para popup
- `notification_stats`: Estatísticas detalhadas
- `notification_analytics`: Analytics para dashboard

## Uso do Sistema

### Para Desenvolvedores

#### Criando uma Notificação
```python
from notifications.models import Notification, NotificationChannel

# Buscar canal
channel = NotificationChannel.objects.get(name='web')

# Criar notificação
notification = Notification.objects.create(
    recipient=user,
    title="Título da Notificação",
    message="Mensagem da notificação",
    type='general',
    channel=channel,
    priority=2
)
```

#### Enviando Notificação
```python
# Enviar notificação
notification.send()
```

#### Usando Templates
```python
from notifications.models import NotificationTemplate

# Buscar template
template = NotificationTemplate.objects.get(
    type='welcome',
    channel__name='web'
)

# Criar notificação com template
notification = Notification.objects.create(
    recipient=user,
    title=template.subject_template.format(user=user),
    message=template.content_template.format(user=user),
    type=template.type,
    channel=template.channel,
    priority=template.priority
)
```

### Para Templates

#### Carregando Template Tags
```html
{% load notification_tags %}
```

#### Exibindo Contador
```html
{% notification_counter user %}
```

#### Exibindo Card de Notificação
```html
{% notification_card notification %}
```

#### Usando Filtros
```html
<!-- Ícone do tipo -->
<i class="{{ notification.type|notification_icon }}"></i>

<!-- Cor do tipo -->
<span class="text-{{ notification.type|notification_color }}">

<!-- Verificar se é importante -->
{% if notification|is_important %}
    <i class="fas fa-star text-warning"></i>
{% endif %}
```

### Para JavaScript

#### Inicializando o Sistema
```javascript
// O sistema é inicializado automaticamente
// Mas pode ser instanciado manualmente
const manager = new NotificationManager();
```

#### Marcando como Lida
```javascript
markAsRead(notificationId);
```

#### Alternando Importância
```javascript
toggleImportant(notificationId);
```

#### Excluindo Notificação
```javascript
deleteNotification(notificationId);
```

## Configuração

### Settings
Adicione no `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'notifications',
    # ...
]

# Configurações de notificação
NOTIFICATION_SETTINGS = {
    'AUTO_DELETE_READ': False,  # Excluir automaticamente lidas
    'MAX_NOTIFICATIONS_PER_USER': 1000,  # Limite por usuário
    'ENABLE_REAL_TIME': True,  # Habilitar tempo real
    'DEFAULT_CHANNEL': 'web',  # Canal padrão
}
```

### URLs
Inclua as URLs no `urls.py` principal:
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('notifications/', include('notifications.urls')),
    # ...
]
```

## Segurança

### Permissões
- Usuários podem ver apenas suas próprias notificações
- Apenas staff pode criar notificações para outros usuários
- Proteção CSRF em todas as views AJAX
- Validação de permissões em todas as operações

### Validações
- Validação de tipos de notificação
- Verificação de propriedade antes de ações
- Sanitização de conteúdo HTML
- Proteção contra XSS

## Performance

### Otimizações
- Índices no banco de dados para consultas frequentes
- Paginação nas listagens
- Cache para contadores
- Atualização assíncrona via AJAX

### Monitoramento
- Logs de envio de notificações
- Estatísticas de entrega
- Métricas de engajamento
- Analytics de uso

## Extensibilidade

### Novos Canais
Para adicionar novos canais:
1. Criar entrada em `NotificationChannel`
2. Implementar método de envio em `Notification.send()`
3. Configurar templates necessários

### Novos Tipos
Para adicionar novos tipos:
1. Adicionar em `NOTIFICATION_TYPES`
2. Criar templates correspondentes
3. Implementar lógica específica se necessário

### Customização
O sistema suporta:
- Templates personalizados
- Canais customizados
- Tipos de notificação específicos
- Integração com sistemas externos

## Testes

### Criando Notificações de Teste
```python
# Via view (apenas staff)
POST /notifications/test/create/

# Via código
from notifications.models import create_test_notifications
create_test_notifications(user)
```

### Testes Unitários
```python
from django.test import TestCase
from notifications.models import Notification

class NotificationTests(TestCase):
    def test_create_notification(self):
        # Implementar testes...
        pass
```

## Troubleshooting

### Problemas Comuns
1. **Notificações não aparecem**: Verificar permissões e canal
2. **Contador não atualiza**: Verificar JavaScript e CSRF
3. **Emails não enviados**: Verificar configurações de email
4. **Performance lenta**: Verificar índices e paginação

### Logs
```python
import logging

logger = logging.getLogger('notifications')
logger.info(f"Notificação criada: {notification.id}")
```

## Versioning

**Versão Atual**: 1.0.0

### Changelog
- 1.0.0: Implementação inicial com funcionalidades básicas
- Funcionalidades de tempo real
- Sistema de templates
- APIs AJAX
- Interface unificada

## Suporte

Para suporte técnico ou dúvidas sobre o sistema de notificações, consulte:
- Documentação do projeto
- Logs do sistema
- Testes unitários
- Código-fonte comentado
