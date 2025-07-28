from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class CommunicationMessage(models.Model):
    """Modelo unificado para todas as comunicações"""
    
    MESSAGE_TYPES = [
        ('announcement', 'Comunicado'),
        ('memo', 'Memorando'),
        ('newsletter', 'Newsletter'),
        ('notification', 'Notificação'),
        ('alert', 'Alerta'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('scheduled', 'Agendado'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'Geral'),
        ('policy', 'Política'),
        ('event', 'Evento'),
        ('training', 'Treinamento'),
        ('safety', 'Segurança'),
        ('hr', 'Recursos Humanos'),
        ('technical', 'Técnico'),
        ('financial', 'Financeiro'),
        ('social', 'Social'),
    ]
    
    # Campos principais
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    summary = models.TextField('Resumo', max_length=500, blank=True)
    
    # Categorização
    message_type = models.CharField('Tipo', max_length=20, choices=MESSAGE_TYPES)
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField('Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_messages',
        verbose_name='Autor'
    )
    
    # Configurações
    is_pinned = models.BooleanField('Fixado', default=False)
    is_confidential = models.BooleanField('Confidencial', default=False)
    requires_acknowledgment = models.BooleanField('Requer Confirmação', default=False)
    requires_response = models.BooleanField('Requer Resposta', default=False)
    
    # Datas
    publish_date = models.DateTimeField('Data de Publicação', default=timezone.now)
    expire_date = models.DateTimeField('Data de Expiração', null=True, blank=True)
    response_deadline = models.DateTimeField('Prazo de Resposta', null=True, blank=True)
    
    # Métricas
    view_count = models.IntegerField('Visualizações', default=0)
    read_count = models.IntegerField('Leituras', default=0)
    response_count = models.IntegerField('Respostas', default=0)
    engagement_score = models.FloatField('Score de Engajamento', default=0.0)
    
    # Relacionamento com entidades específicas (genérico)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Mensagem de Comunicação'
        verbose_name_plural = 'Mensagens de Comunicação'
        ordering = ['-is_pinned', '-publish_date']
        indexes = [
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['publish_date']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.title}"
    
    def is_published(self):
        return self.status == 'published' and self.publish_date <= timezone.now()
    
    def is_expired(self):
        return self.expire_date and timezone.now() > self.expire_date
    
    def get_recipients_count(self):
        return self.recipients.count()
    
    def get_read_percentage(self):
        total = self.get_recipients_count()
        return (self.read_count / total * 100) if total > 0 else 0
    
    def update_engagement_score(self):
        """Calcula score de engajamento baseado em métricas"""
        if self.view_count == 0:
            self.engagement_score = 0.0
            return
        
        read_rate = self.read_count / self.view_count
        response_rate = self.response_count / self.read_count if self.read_count > 0 else 0
        
        # Peso baseado na prioridade
        priority_weight = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'urgent': 2.0
        }
        
        base_score = (read_rate * 0.6 + response_rate * 0.4) * 100
        self.engagement_score = base_score * priority_weight.get(self.priority, 1.0)
        self.save(update_fields=['engagement_score'])


class MessageRecipient(models.Model):
    """Relacionamento entre mensagens e destinatários"""
    
    RECIPIENT_TYPES = [
        ('user', 'Usuário'),
        ('department', 'Departamento'),
        ('global', 'Global'),
    ]
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    recipient_type = models.CharField('Tipo de Destinatário', max_length=20, choices=RECIPIENT_TYPES)
    
    # Para usuários específicos
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='received_messages'
    )
    
    # Para departamentos
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='received_messages'
    )
    
    # Status de leitura
    is_read = models.BooleanField('Lido', default=False)
    read_at = models.DateTimeField('Lido em', null=True, blank=True)
    is_acknowledged = models.BooleanField('Confirmado', default=False)
    acknowledged_at = models.DateTimeField('Confirmado em', null=True, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Destinatário'
        verbose_name_plural = 'Destinatários'
        unique_together = ['message', 'user', 'department']
        indexes = [
            models.Index(fields=['message', 'is_read']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} - {self.message.title}"
        elif self.department:
            return f"{self.department.name} - {self.message.title}"
        return f"Global - {self.message.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            
            # Atualizar contador da mensagem
            self.message.read_count += 1
            self.message.save(update_fields=['read_count'])
    
    def acknowledge(self):
        if not self.is_acknowledged:
            self.is_acknowledged = True
            self.acknowledged_at = timezone.now()
            self.save(update_fields=['is_acknowledged', 'acknowledged_at'])


class MessageResponse(models.Model):
    """Respostas às mensagens"""
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_responses'
    )
    content = models.TextField('Resposta')
    
    # Thread de respostas
    parent_response = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Resposta'
        verbose_name_plural = 'Respostas'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['message', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.message.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Atualizar contador da mensagem
            self.message.response_count += 1
            self.message.save(update_fields=['response_count'])


class MessageAttachment(models.Model):
    """Anexos das mensagens"""
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        'Arquivo',
        upload_to='communication/attachments/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
                              'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'zip', 'rar']
        )]
    )
    name = models.CharField('Nome', max_length=255)
    description = models.TextField('Descrição', blank=True)
    file_size = models.IntegerField('Tamanho do Arquivo', default=0)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.message.title}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Retorna tamanho do arquivo em formato legível"""
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class CommunicationPreferences(models.Model):
    """Preferências de comunicação do usuário"""
    
    NOTIFICATION_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    ]
    
    FREQUENCY_CHOICES = [
        ('immediate', 'Imediato'),
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('never', 'Nunca'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_preferences'
    )
    
    # Preferências por tipo de mensagem
    announcements_enabled = models.BooleanField('Comunicados', default=True)
    memos_enabled = models.BooleanField('Memorandos', default=True)
    newsletters_enabled = models.BooleanField('Newsletters', default=True)
    notifications_enabled = models.BooleanField('Notificações', default=True)
    alerts_enabled = models.BooleanField('Alertas', default=True)
    
    # Métodos de notificação preferidos
    preferred_methods = models.JSONField('Métodos Preferidos', default=list)
    
    # Frequência de digest
    digest_frequency = models.CharField('Frequência do Resumo', max_length=20, 
                                       choices=FREQUENCY_CHOICES, default='daily')
    
    # Horários preferidos
    quiet_hours_start = models.TimeField('Início do Período Silencioso', null=True, blank=True)
    quiet_hours_end = models.TimeField('Fim do Período Silencioso', null=True, blank=True)
    
    # Filtros automáticos
    priority_filter = models.CharField('Filtro de Prioridade', max_length=10, 
                                      choices=CommunicationMessage.PRIORITY_CHOICES, 
                                      default='low')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Preferências de Comunicação'
        verbose_name_plural = 'Preferências de Comunicação'
    
    def __str__(self):
        return f"Preferências de {self.user.get_full_name()}"
    
    def should_receive_message(self, message):
        """Verifica se o usuário deve receber uma mensagem baseado nas preferências"""
        
        # Verificar se o tipo está habilitado
        type_enabled = {
            'announcement': self.announcements_enabled,
            'memo': self.memos_enabled,
            'newsletter': self.newsletters_enabled,
            'notification': self.notifications_enabled,
            'alert': self.alerts_enabled,
        }
        
        if not type_enabled.get(message.message_type, True):
            return False
        
        # Verificar filtro de prioridade
        priority_levels = ['low', 'medium', 'high', 'urgent']
        min_priority_index = priority_levels.index(self.priority_filter)
        message_priority_index = priority_levels.index(message.priority)
        
        return message_priority_index >= min_priority_index
    
    def is_quiet_time(self):
        """Verifica se está no período silencioso"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        current_time = timezone.now().time()
        return self.quiet_hours_start <= current_time <= self.quiet_hours_end
