# 🔧 Move Marias - Documentação Técnica

## 📋 Arquitetura Detalhada

### **Estrutura de Diretórios**
```
moverias/
├── 📁 movemarias/                 # Configurações do projeto Django
│   ├── settings/                  # Configurações por ambiente
│   ├── urls.py                   # URLs principais
│   └── wsgi.py                   # WSGI para produção
├── 📁 core/                      # Módulo central
│   ├── decorators.py             # Decoradores customizados
│   ├── export_utils.py           # Sistema de exportação
│   ├── permissions.py            # Sistema de permissões
│   └── unified_permissions.py    # Permissões unificadas
├── 📁 members/                   # Gestão de beneficiárias
│   ├── models.py                 # Modelo Beneficiary
│   ├── views.py                  # Views CRUD
│   ├── forms.py                  # Formulários
│   └── templates/                # Templates específicos
├── 📁 workshops/                 # Sistema de workshops
│   ├── models.py                 # Workshop, Session, Enrollment
│   ├── views.py                  # Views + Exportação
│   └── templates/                # Templates Kanban-style
├── 📁 activities/                # Atividades individuais
│   ├── models.py                 # BeneficiaryActivity
│   ├── views.py                  # Dashboard + CRUD
│   └── templates/                # Interface responsiva
├── 📁 tasks/                     # Sistema Kanban
│   ├── models.py                 # TaskBoard, Task, Column
│   ├── views.py                  # Kanban + Ajax
│   └── templates/                # Interface drag-and-drop
├── 📁 coaching/                  # Ferramentas de coaching
│   ├── models.py                 # ActionPlan, WheelOfLife
│   ├── views.py                  # Coaching tools
│   └── templates/                # Visualizações interativas
├── 📁 communication/             # Sistema de comunicação
│   ├── models.py                 # Messages, Announcements
│   ├── views.py                  # Comunicação interna
│   └── templates/                # Interface de mensagens
├── 📁 chat/                      # Chat em tempo real
│   ├── models.py                 # ChatRoom, Message
│   ├── consumers.py              # WebSocket consumers
│   ├── routing.py                # WebSocket routing
│   └── templates/                # Interface de chat
├── 📁 certificates/              # Geração de certificados
│   ├── models.py                 # Certificate templates
│   ├── views.py                  # Geração PDF
│   └── templates/                # Templates de certificados
├── 📁 social/                    # Anamnese social
│   ├── models.py                 # SocialAnamnesis
│   ├── views.py                  # Formulários extensos
│   └── templates/                # Formulários multipasso
├── 📁 evolution/                 # Registros de evolução
│   ├── models.py                 # EvolutionRecord
│   ├── views.py                  # Acompanhamento temporal
│   └── templates/                # Timeline interface
├── 📁 projects/                  # Gestão de projetos
│   ├── models.py                 # Project, Enrollment
│   ├── views.py                  # CRUD de projetos
│   └── templates/                # Dashboard de projetos
├── 📁 notifications/             # Sistema de notificações
│   ├── models.py                 # Notification, UserNotification
│   ├── views.py                  # Gerenciamento de notificações
│   ├── tasks.py                  # Tarefas Celery
│   └── templates/                # Interface de notificações
├── 📁 dashboard/                 # Painel administrativo
│   ├── views.py                  # Métricas e analytics
│   ├── utils.py                  # Utilitários de dashboard
│   └── templates/                # Interface de dashboard
├── 📁 users/                     # Gestão de usuários
│   ├── models.py                 # User extensions
│   ├── views.py                  # Perfis e permissões
│   └── templates/                # Interface de usuários
├── 📁 hr/                        # Recursos humanos
│   ├── models.py                 # Employee, Document
│   ├── views.py                  # Gestão de RH
│   └── templates/                # Interface de RH
├── 📁 api/                       # APIs REST
│   ├── views.py                  # ViewSets da API
│   ├── serializers.py           # Serializadores DRF
│   └── urls.py                   # URLs da API
├── 📁 templates/                 # Templates globais
│   ├── layouts/                  # Layouts base
│   ├── components/               # Componentes reutilizáveis
│   └── core/exports/             # Templates de exportação
├── 📁 static/                    # Arquivos estáticos
│   ├── css/                      # Estilos CSS
│   ├── js/                       # JavaScript
│   └── img/                      # Imagens
├── 📁 tests/                     # Testes automatizados
│   ├── test_models.py            # Testes de modelos
│   ├── test_views.py             # Testes de views
│   └── test_utils.py             # Testes de utilitários
├── 📄 manage.py                  # Script Django
├── 📄 requirements.txt           # Dependências Python
├── 📄 conftest.py               # Configuração de testes
└── 📄 pytest.ini               # Configuração pytest
```

---

## 🔐 Sistema de Permissões

### **Grupos de Usuários**
```python
# Grupos principais
GRUPOS = {
    'Administrador': ['*'],  # Acesso total
    'Coordenacao': [
        'view_dashboard',
        'view_reports',
        'export_data',
        'manage_workshops',
        'view_all_beneficiaries'
    ],
    'Tecnica': [
        'add_beneficiary',
        'change_beneficiary', 
        'view_beneficiary',
        'add_workshop',
        'change_workshop',
        'add_activity',
        'change_activity'
    ],
    'Suporte': [
        'view_beneficiary',
        'view_workshop',
        'view_activity'
    ]
}
```

### **Decoradores de Permissão**
```python
# Uso nos views
@login_required
@requires_technician
def view_beneficiaria(request, pk):
    # Apenas usuários do grupo Técnica
    pass

@login_required  
@user_passes_test(is_coordenacao)
def dashboard_executivo(request):
    # Apenas coordenação
    pass
```

---

## 📊 Sistema de Exportação

### **Arquitetura Centralizada**
```python
# core/export_utils.py
class ExportManager:
    @staticmethod
    def export_to_csv(data, filename, headers=None):
        """Exportação CSV universal"""
        
    @staticmethod  
    def export_to_excel(data, filename, headers=None):
        """Excel com formatação profissional"""
        
    @staticmethod
    def export_to_pdf(template_name, context, filename):
        """PDF com template personalizado"""

def export_universal(request, model_class, formatter_method, 
                    filename_prefix, template_name=None):
    """Função universal para qualquer modelo"""
```

### **Formatadores Específicos**
```python
class DataFormatter:
    @staticmethod
    def format_beneficiary_data(beneficiaries):
        """Formatação específica para beneficiárias"""
        
    @staticmethod
    def format_workshop_data(workshops):
        """Formatação específica para workshops"""
        
    @staticmethod  
    def format_task_data(tasks):
        """Formatação específica para tarefas"""
```

### **Templates PDF**
```html
<!-- templates/core/exports/pdf_report.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial; font-size: 11px; }
        .header { border-bottom: 2px solid #366092; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #366092; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Gerado em: {{ generated_at|date:"d/m/Y H:i" }}</p>
    </div>
    <!-- Dados dinâmicos -->
</body>
</html>
```

---

## 💬 Sistema de Chat (WebSockets)

### **Configuração Django Channels**
```python
# movemarias/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### **Consumer WebSocket**
```python
# chat/consumers.py
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Conectar ao chat room"""
        
    async def disconnect(self, close_code):
        """Desconectar do chat room"""
        
    async def receive(self, text_data):
        """Receber mensagem do WebSocket"""
        
    async def chat_message(self, event):
        """Enviar mensagem para WebSocket"""
```

### **Frontend JavaScript**
```javascript
// static/js/chat.js
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    appendMessage(data.message, data.user, data.timestamp);
};

function sendMessage() {
    chatSocket.send(JSON.stringify({
        'message': messageInput.value,
        'type': 'chat_message'
    }));
}
```

---

## 🔔 Sistema de Notificações

### **Tipos de Notificação**
```python
# notifications/models.py
class Notification(models.Model):
    TYPES = [
        ('workshop_reminder', 'Lembrete de Workshop'),
        ('task_deadline', 'Prazo de Tarefa'),
        ('new_message', 'Nova Mensagem'),
        ('system_alert', 'Alerta do Sistema'),
        ('achievement', 'Conquista'),
    ]
    
    type = models.CharField(max_length=50, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### **Tarefas Celery**
```python
# notifications/tasks.py
@shared_task
def send_workshop_reminders():
    """Enviar lembretes de workshop"""
    tomorrow = timezone.now() + timedelta(days=1)
    workshops = Workshop.objects.filter(
        start_date__date=tomorrow.date(),
        status='ativo'
    )
    
    for workshop in workshops:
        for enrollment in workshop.enrollments.filter(status='ativo'):
            Notification.objects.create(
                type='workshop_reminder',
                title=f'Workshop amanhã: {workshop.name}',
                message=f'Lembre-se do workshop {workshop.name} amanhã às {workshop.start_time}',
                recipient=enrollment.beneficiary.user
            )
```

---

## 🎯 Sistema Kanban (Tasks)

### **Modelos Principais**
```python
# tasks/models.py
class TaskBoard(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='board_members')
    
class TaskColumn(models.Model):
    board = models.ForeignKey(TaskBoard, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField()
    
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    board = models.ForeignKey(TaskBoard, on_delete=models.CASCADE)
    column = models.ForeignKey(TaskColumn, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField()
```

### **API AJAX para Drag & Drop**
```python
# tasks/views.py
@require_http_methods(["POST"])
@login_required
def task_update_column(request):
    """Atualizar coluna da tarefa via AJAX"""
    task_id = request.POST.get('task_id')
    column_id = request.POST.get('column_id')
    order = request.POST.get('order', 0)
    
    task = get_object_or_404(Task, id=task_id)
    column = get_object_or_404(TaskColumn, id=column_id)
    
    task.column = column
    task.order = order
    task.save()
    
    return JsonResponse({'status': 'success'})
```

### **Frontend Drag & Drop**
```javascript
// static/js/kanban.js
function initDragAndDrop() {
    $('.kanban-column').sortable({
        connectWith: '.kanban-column',
        placeholder: 'task-placeholder',
        update: function(event, ui) {
            updateTaskPosition(ui.item);
        }
    });
}

function updateTaskPosition(taskElement) {
    const taskId = taskElement.data('task-id');
    const columnId = taskElement.parent().data('column-id');
    const order = taskElement.index();
    
    $.post('/tasks/api/task/update-column/', {
        task_id: taskId,
        column_id: columnId,
        order: order,
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
    });
}
```

---

## 📊 Dashboard e Analytics

### **Métricas em Tempo Real**
```python
# dashboard/views.py
@login_required
@requires_technician  
def dashboard_stats_api(request):
    """API para métricas do dashboard"""
    stats = {
        'beneficiaries': {
            'total': Beneficiary.objects.count(),
            'active': Beneficiary.objects.filter(status='ATIVA').count(),
            'new_this_month': Beneficiary.objects.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count()
        },
        'workshops': {
            'active': Workshop.objects.filter(status='ativo').count(),
            'participants_today': WorkshopSession.objects.filter(
                date=timezone.now().date()
            ).aggregate(
                total=Count('attendances__enrollment__beneficiary')
            )['total'] or 0
        },
        'tasks': {
            'pending': Task.objects.filter(status='PENDENTE').count(),
            'overdue': Task.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=['PENDENTE', 'EM_ANDAMENTO']
            ).count()
        }
    }
    return JsonResponse(stats)
```

### **Gráficos e Visualizações**
```javascript
// static/js/dashboard.js
function loadDashboardCharts() {
    // Gráfico de beneficiárias por mês
    fetch('/dashboard/api/stats/')
        .then(response => response.json())
        .then(data => {
            createBeneficiariesChart(data.beneficiaries);
            createWorkshopsChart(data.workshops);
            updateMetricCards(data);
        });
}

function createBeneficiariesChart(data) {
    const ctx = document.getElementById('beneficiariesChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.months,
            datasets: [{
                label: 'Novas Beneficiárias',
                data: data.values,
                borderColor: 'rgb(54, 96, 146)',
                backgroundColor: 'rgba(54, 96, 146, 0.1)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Crescimento de Beneficiárias' }
            }
        }
    });
}
```

---

## 🔧 Configurações de Ambiente

### **Settings por Ambiente**
```python
# movemarias/settings/base.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'channels',
    'celery',
    'django_celery_beat',
    'corsheaders',
    'crispy_forms',
    'crispy_tailwind',
    
    # Local apps
    'core',
    'members',
    'workshops',
    'activities',
    'tasks',
    'coaching',
    'communication',
    'certificates',
    'social',
    'evolution',
    'projects',
    'chat',
    'dashboard',
    'notifications',
    'users',
    'hr',
    'api',
]
```

### **Configuração de Desenvolvimento**
```python
# movemarias/settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### **Configuração de Produção**
```python
# movemarias/settings/production.py
from .base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['movemarias.herokuapp.com', 'movemarias.org']

# PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
    }
}

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

## 🧪 Testes Automatizados

### **Configuração pytest**
```python
# conftest.py
import pytest
from django.test import Client
from django.contrib.auth.models import User, Group
from members.models import Beneficiary

@pytest.fixture
def user_tecnica():
    """Usuário do grupo Técnica"""
    user = User.objects.create_user(
        username='tecnica',
        email='tecnica@test.com',
        password='testpass123'
    )
    group, _ = Group.objects.get_or_create(name='Tecnica')
    user.groups.add(group)
    return user

@pytest.fixture  
def sample_beneficiary():
    """Beneficiária de exemplo"""
    return Beneficiary.objects.create(
        full_name='Maria Silva',
        email='maria@test.com',
        phone_1='11999999999',
        status='ATIVA'
    )
```

### **Testes de Modelos**
```python
# tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from members.models import Beneficiary

@pytest.mark.django_db
class TestBeneficiaryModel:
    def test_create_beneficiary(self):
        """Teste criação de beneficiária"""
        beneficiary = Beneficiary.objects.create(
            full_name='Ana Costa',
            email='ana@test.com',
            status='ATIVA'
        )
        assert beneficiary.full_name == 'Ana Costa'
        assert beneficiary.status == 'ATIVA'
        
    def test_email_validation(self):
        """Teste validação de email"""
        with pytest.raises(ValidationError):
            beneficiary = Beneficiary(
                full_name='Teste',
                email='email-invalido',
                status='ATIVA'
            )
            beneficiary.full_clean()
```

### **Testes de Views**
```python
# tests/test_views.py
import pytest
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
class TestBeneficiaryViews:
    def test_beneficiary_list_requires_login(self, client):
        """Teste que lista requer login"""
        url = reverse('members:beneficiary_list')
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login
        
    def test_beneficiary_list_with_permission(self, client, user_tecnica):
        """Teste lista com permissão"""
        client.force_login(user_tecnica)
        url = reverse('members:beneficiary_list')
        response = client.get(url)
        assert response.status_code == 200
```

### **Testes de API**
```python
# tests/test_api.py
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

@pytest.mark.django_db
class TestBeneficiaryAPI:
    def test_api_requires_authentication(self):
        """Teste que API requer autenticação"""
        client = APIClient()
        url = '/api/v1/beneficiaries/'
        response = client.get(url)
        assert response.status_code == 401
        
    def test_api_with_token(self, user_tecnica):
        """Teste API com token"""
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user_tecnica)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = '/api/v1/beneficiaries/'
        response = client.get(url)
        assert response.status_code == 200
```

---

## 🚀 Deploy e Produção

### **Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "movemarias.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### **docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/movemarias
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: movemarias
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    
  celery:
    build: .
    command: celery -A movemarias worker -l info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/movemarias
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### **Heroku Deployment**
```bash
# Procfile
web: gunicorn movemarias.wsgi:application
worker: celery -A movemarias worker -l info
beat: celery -A movemarias beat -l info

# app.json para review apps
{
  "name": "Move Marias",
  "description": "Sistema de Gestão de Beneficiárias",
  "scripts": {
    "postdeploy": "python manage.py migrate && python manage.py collectstatic --noinput"
  },
  "env": {
    "DJANGO_SETTINGS_MODULE": "movemarias.settings.production",
    "SECRET_KEY": {
      "generator": "secret"
    }
  },
  "addons": [
    "heroku-postgresql",
    "heroku-redis"
  ]
}
```

---

## 🔍 Monitoramento e Logs

### **Configuração Sentry**
```python
# movemarias/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(auto_enabling=True),
        CeleryIntegration(auto_enabling=True),
    ],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### **Logs Estruturados**
```python
# movemarias/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'movemarias.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

---

## 📈 Performance e Otimização

### **Cache Strategy**
```python
# core/cache.py
from django.core.cache import cache
from django.conf import settings

def get_cached_stats(cache_key, queryset_func, timeout=300):
    """Cache genérico para estatísticas"""
    data = cache.get(cache_key)
    if data is None:
        data = queryset_func()
        cache.set(cache_key, data, timeout)
    return data

# Uso nas views
stats = get_cached_stats(
    'dashboard_stats',
    lambda: calculate_dashboard_stats(),
    timeout=600  # 10 minutos
)
```

### **Database Optimization**
```python
# Queries otimizadas
beneficiaries = Beneficiary.objects.select_related(
    'created_by'
).prefetch_related(
    'workshop_enrollments__workshop',
    'project_enrollments__project'
).filter(status='ATIVA')

# Indices no banco
class Meta:
    indexes = [
        models.Index(fields=['status', 'created_at']),
        models.Index(fields=['full_name']),
        models.Index(fields=['email']),
    ]
```

### **Frontend Optimization**
```html
<!-- Templates com lazy loading -->
{% load static %}

<!-- CSS crítico inline -->
<style>
  .critical-css { /* CSS essencial */ }
</style>

<!-- CSS não crítico lazy -->
<link rel="preload" href="{% static 'css/main.css' %}" as="style" onload="this.onload=null;this.rel='stylesheet'">

<!-- JavaScript com defer -->
<script defer src="{% static 'js/main.js' %}"></script>

<!-- Imagens com lazy loading -->
<img src="{% static 'img/placeholder.jpg' %}" data-src="{% static 'img/real-image.jpg' %}" class="lazy">
```

---

*Esta documentação técnica complementa o README principal e fornece detalhes de implementação para desenvolvedores e administradores do sistema.* 🔧
