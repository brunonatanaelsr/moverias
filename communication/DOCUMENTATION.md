# Módulo de Comunicação - Documentação Técnica

## Visão Geral

O módulo de comunicação é um sistema completo e integrado para gerenciar todas as comunicações internas da organização Move Marias. Oferece funcionalidades robustas para criação, distribuição e acompanhamento de anúncios, memorandos, newsletters e mensagens diretas.

## Estrutura Técnica

### Modelos de Dados

#### 1. Announcement (Anúncios)
```python
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    target_audience = models.ManyToManyField(User, blank=True)
    target_departments = models.ManyToManyField(Department, blank=True)
    is_pinned = models.BooleanField(default=False)
    requires_acknowledgment = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. InternalMemo (Memorandos)
```python
class InternalMemo(models.Model):
    number = models.CharField(max_length=50, unique=True)  # Numeração automática
    subject = models.CharField(max_length=200)
    content = models.TextField()
    memo_type = models.CharField(max_length=20, choices=MEMO_TYPE_CHOICES)
    from_department = models.ForeignKey(Department, related_name='sent_memos')
    to_department = models.ForeignKey(Department, related_name='received_memos')
    requires_response = models.BooleanField(default=False)
    response_deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
```

#### 3. Newsletter (Newsletters)
```python
class Newsletter(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField()
    template = models.ForeignKey('NewsletterTemplate', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
```

#### 4. Message (Mensagens Diretas)
```python
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages')
    recipient = models.ForeignKey(User, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    parent_message = models.ForeignKey('self', null=True, blank=True)  # Para threads
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
```

### Views Principais

#### Dashboard
- **Função**: Visão geral de todas as comunicações
- **Template**: `communication/dashboard.html`
- **Contexto**: Estatísticas, comunicações recentes, notificações pendentes

#### Announcement Views
- `announcement_list`: Lista todas as comunicações
- `announcement_create`: Formulário de criação
- `announcement_detail`: Visualização detalhada
- `announcement_board`: Quadro visual de anúncios

#### Newsletter Views
- `newsletter_create`: Criação com templates e seções dinâmicas
- `newsletter_detail`: Visualização com analytics
- `newsletter_pdf`: Geração de PDF
- `newsletter_analytics_export`: Exportação de dados

### Templates

#### Estrutura de Templates
```
communication/templates/communication/
├── dashboard.html              # Dashboard principal
├── announcement_create.html    # Criação de anúncios
├── announcement_detail.html    # Detalhes do anúncio
├── announcement_board.html     # Quadro de anúncios
├── memo_create.html           # Criação de memorandos
├── memo_detail.html           # Detalhes do memorando
├── newsletter_create.html     # Criação de newsletters
├── newsletter_detail.html     # Detalhes da newsletter
└── settings.html              # Configurações do módulo
```

#### Características dos Templates
- **Responsivo**: Adaptável a diferentes tamanhos de tela
- **Interativo**: JavaScript avançado para UX moderna
- **Acessível**: Conformidade com padrões de acessibilidade
- **Performático**: Carregamento otimizado e lazy loading

### CSS e JavaScript

#### CSS (`static/css/communication.css`)
- **Variáveis CSS**: Sistema de cores e espaçamentos consistente
- **Componentes**: Cards, botões, formulários, modais padronizados
- **Animações**: Transições suaves e feedback visual
- **Responsividade**: Breakpoints mobile-first

#### JavaScript (`static/js/communication.js`)
- **Modular**: Estrutura orientada a objetos
- **Utils**: Funções utilitárias para AJAX, validação, formatação
- **Managers**: Gerenciadores especializados (Modal, Form, Upload, etc.)
- **APIs**: Integração com endpoints REST

### Funcionalidades Principais

#### 1. Sistema de Prioridades
```javascript
PRIORITY_LEVELS = {
    'low': { color: '#10b981', label: 'Baixa' },
    'medium': { color: '#f59e0b', label: 'Média' },
    'high': { color: '#ef4444', label: 'Alta' },
    'urgent': { color: '#dc2626', label: 'Urgente', pulse: true }
}
```

#### 2. Sistema de Notificações
- Notificações em tempo real
- Email notifications (quando configurado)
- Browser notifications
- Notificações push (planejado)

#### 3. Sistema de Upload
- Drag & drop interface
- Validação de tipos de arquivo
- Preview de imagens
- Progress indicators
- Múltiplos arquivos

#### 4. Sistema de Templates
- Templates reutilizáveis para newsletters
- Editor WYSIWYG integrado (TinyMCE)
- Seções dinâmicas
- Preview em tempo real

#### 5. Analytics e Relatórios
- Estatísticas de leitura
- Taxa de engajamento
- Gráficos interativos (Chart.js)
- Exportação de dados

### APIs e Endpoints

#### Endpoints REST
```python
# Dashboard Stats
GET /api/dashboard-stats/
Response: {
    'total_announcements': int,
    'unread_count': int,
    'urgent_count': int,
    'recent_activity': []
}

# Mark as Read
POST /api/mark-as-read/
Body: { 'id': int, 'type': str }
Response: { 'success': bool }

# Search
GET /api/search/?q=query&type=all
Response: {
    'results': [
        {
            'id': int,
            'title': str,
            'content': str,
            'type': str,
            'url': str,
            'created_at': datetime
        }
    ]
}
```

### Configurações do Sistema

#### Settings (`communication/settings.py`)
```python
COMMUNICATION_SETTINGS = {
    'AUTO_ARCHIVE_DAYS': 30,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_FILE_TYPES': ['.pdf', '.doc', '.docx', '.jpg', '.png'],
    'DEFAULT_PRIORITY': 'medium',
    'REQUIRE_READ_CONFIRMATION': True,
    'EMAIL_NOTIFICATIONS': True,
    'BROWSER_NOTIFICATIONS': True
}
```

### Segurança e Permissões

#### Sistema de Permissões
```python
COMMUNICATION_PERMISSIONS = [
    'communication.add_announcement',
    'communication.change_announcement',
    'communication.delete_announcement',
    'communication.view_announcement',
    'communication.add_newsletter',
    'communication.change_newsletter',
    'communication.delete_newsletter',
    'communication.view_newsletter_analytics'
]
```

#### Validações de Segurança
- CSRF protection em todos os formulários
- Sanitização de conteúdo HTML
- Validação de upload de arquivos
- Rate limiting em APIs
- Logs de auditoria

### Performance

#### Otimizações Implementadas
- **Database**: Indexes otimizados, select_related, prefetch_related
- **Frontend**: Lazy loading, code splitting, minificação
- **Cache**: Cache de consultas frequentes, cache de templates
- **CDN**: Assets estáticos via CDN

#### Métricas de Performance
- Tempo de carregamento: < 2s
- First Contentful Paint: < 1s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1

### Testes

#### Cobertura de Testes
```bash
# Executar testes
python manage.py test communication

# Testes com cobertura
coverage run --source='.' manage.py test communication
coverage report -m
```

#### Tipos de Testes
- **Unit Tests**: Modelos, views, formulários
- **Integration Tests**: APIs, workflows completos
- **Selenium Tests**: Interface do usuário
- **Performance Tests**: Load testing das APIs

### Deployment

#### Requisitos de Produção
```requirements.txt
Django>=4.2.0
Pillow>=10.0.0
python-decouple>=3.8
celery>=5.3.0  # Para tarefas assíncronas
redis>=5.0.0   # Cache e message broker
```

#### Configuração de Produção
```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery para tarefas assíncronas
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### Monitoramento

#### Logs Estruturados
```python
import structlog

logger = structlog.get_logger(__name__)

# Exemplo de uso
logger.info(
    "announcement_created",
    user_id=request.user.id,
    announcement_id=announcement.id,
    priority=announcement.priority
)
```

#### Métricas Coletadas
- Número de comunicações por tipo
- Taxa de leitura por usuário
- Tempo médio de leitura
- Erros de upload
- Performance das APIs

### Roadmap de Desenvolvimento

#### Próximas Funcionalidades
1. **Integração com Microsoft Teams/Slack**
   - Notificações automáticas
   - Comandos de bot

2. **Sistema de Aprovação Workflow**
   - Aprovação hierárquica
   - Histórico de aprovações

3. **Templates Avançados**
   - Editor de templates drag-and-drop
   - Biblioteca de componentes

4. **Analytics Avançado**
   - Heatmaps de leitura
   - A/B testing de comunicações

5. **Mobile App**
   - Aplicativo nativo
   - Push notifications

### Troubleshooting

#### Problemas Comuns

**1. Upload de arquivos não funcionando**
```bash
# Verificar permissões
chmod 755 media/uploads/
chown www-data:www-data media/uploads/

# Verificar configurações
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**2. Notificações não sendo enviadas**
```python
# Verificar configurações de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**3. Performance lenta**
```python
# Adicionar indexes
class Announcement(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    priority = models.CharField(max_length=10, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'priority']),
        ]
```

### Documentação da API

Para documentação completa da API, acesse:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

### Suporte e Manutenção

Para suporte técnico ou reportar bugs:
- Email: dev@movemarias.org
- Issue Tracker: GitHub Issues
- Documentação: Wiki interno

---

**Versão**: 1.0.0  
**Última atualização**: {{ current_date }}  
**Autor**: Equipe de Desenvolvimento Move Marias
