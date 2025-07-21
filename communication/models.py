from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class Announcement(models.Model):
    """Comunicados e Anúncios"""
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
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
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    summary = models.TextField('Resumo', max_length=500, blank=True)
    
    # Categorização
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField('Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements',
        verbose_name='Autor'
    )
    
    # Destinatários
    departments = models.ManyToManyField(
        'hr.Department',
        related_name='announcements',
        verbose_name='Departamentos',
        blank=True
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='targeted_announcements',
        verbose_name='Usuários Específicos',
        blank=True
    )
    is_global = models.BooleanField('Global (Todos)', default=False)
    
    # Configurações
    is_active = models.BooleanField('Ativo', default=True)
    is_pinned = models.BooleanField('Fixado', default=False)
    requires_acknowledgment = models.BooleanField('Requer Confirmação de Leitura', default=False)
    
    # Datas
    publish_date = models.DateTimeField('Data de Publicação', default=timezone.now)
    expire_date = models.DateTimeField('Data de Expiração', null=True, blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Comunicado'
        verbose_name_plural = 'Comunicados'
        ordering = ['-is_pinned', '-publish_date']

    def __str__(self):
        return self.title

    def get_read_count(self):
        return self.read_receipts.count()

    def get_total_recipients(self):
        if self.is_global:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.filter(is_active=True).count()
        
        count = self.target_users.count()
        for dept in self.departments.all():
            count += dept.employees.filter(user__is_active=True).count()
        return count

    def get_read_percentage(self):
        total = self.get_total_recipients()
        if total == 0:
            return 0
        return (self.get_read_count() / total) * 100

    def is_expired(self):
        if self.expire_date:
            return timezone.now() > self.expire_date
        return False

    def user_can_read(self, user):
        if self.is_global:
            return True
        
        if self.target_users.filter(pk=user.pk).exists():
            return True
        
        if hasattr(user, 'employee_profile'):
            if self.departments.filter(pk=user.employee_profile.department.pk).exists():
                return True
        
        return False


class AnnouncementAttachment(models.Model):
    """Anexos dos comunicados"""
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Comunicado'
    )
    file = models.FileField(
        'Arquivo',
        upload_to='communication/attachments/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'])]
    )
    name = models.CharField('Nome', max_length=255)
    description = models.TextField('Descrição', blank=True)
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} - {self.announcement.title}"

    def get_file_size(self):
        if self.file:
            return self.file.size
        return 0


class AnnouncementReadReceipt(models.Model):
    """Confirmação de leitura dos comunicados"""
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        verbose_name='Comunicado'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcement_reads',
        verbose_name='Usuário'
    )
    read_at = models.DateTimeField('Lido em', auto_now_add=True)
    acknowledged = models.BooleanField('Confirmado', default=False)
    acknowledged_at = models.DateTimeField('Confirmado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Confirmação de Leitura'
        verbose_name_plural = 'Confirmações de Leitura'
        unique_together = ['announcement', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.announcement.title}"

    def acknowledge(self):
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['acknowledged', 'acknowledged_at'])


class InternalMemo(models.Model):
    """Memorandos Internos"""
    MEMO_TYPES = [
        ('informative', 'Informativo'),
        ('directive', 'Diretivo'),
        ('request', 'Solicitação'),
        ('policy', 'Política'),
        ('procedure', 'Procedimento'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    memo_number = models.CharField('Número do Memorando', max_length=50, unique=True)
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    memo_type = models.CharField('Tipo', max_length=20, choices=MEMO_TYPES, default='informative')
    
    # Origem e Destino
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_memos',
        verbose_name='De'
    )
    from_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.CASCADE,
        related_name='sent_memos',
        verbose_name='Departamento Origem'
    )
    
    to_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_memos',
        verbose_name='Para Usuários',
        blank=True
    )
    to_departments = models.ManyToManyField(
        'hr.Department',
        related_name='received_memos',
        verbose_name='Para Departamentos',
        blank=True
    )
    
    # Configurações
    requires_response = models.BooleanField('Requer Resposta', default=False)
    response_deadline = models.DateTimeField('Prazo de Resposta', null=True, blank=True)
    is_confidential = models.BooleanField('Confidencial', default=False)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Memorando'
        verbose_name_plural = 'Memorandos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.memo_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.memo_number:
            # Gerar número do memorando
            year = timezone.now().year
            count = InternalMemo.objects.filter(created_at__year=year).count() + 1
            self.memo_number = f"MEMO-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def get_recipients_count(self):
        count = self.to_users.count()
        for dept in self.to_departments.all():
            count += dept.employees.filter(user__is_active=True).count()
        return count

    def user_can_read(self, user):
        if self.to_users.filter(pk=user.pk).exists():
            return True
        
        if hasattr(user, 'employee_profile'):
            if self.to_departments.filter(pk=user.employee_profile.department.pk).exists():
                return True
        
        return False


class MemoResponse(models.Model):
    """Respostas aos memorandos"""
    memo = models.ForeignKey(
        InternalMemo,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Memorando'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memo_responses',
        verbose_name='Usuário'
    )
    content = models.TextField('Resposta')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Resposta ao Memorando'
        verbose_name_plural = 'Respostas aos Memorandos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.memo.title}"


class Newsletter(models.Model):
    """Newsletter Interna"""
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    summary = models.TextField('Resumo', max_length=500, blank=True)
    
    # Configurações
    is_published = models.BooleanField('Publicado', default=False)
    publish_date = models.DateTimeField('Data de Publicação', null=True, blank=True)
    
    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='newsletters',
        verbose_name='Autor'
    )
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'
        ordering = ['-publish_date']

    def __str__(self):
        return self.title

    def publish(self):
        self.is_published = True
        self.publish_date = timezone.now()
        self.save(update_fields=['is_published', 'publish_date'])


class SuggestionBox(models.Model):
    """Caixa de Sugestões"""
    SUGGESTION_TYPES = [
        ('improvement', 'Melhoria'),
        ('complaint', 'Reclamação'),
        ('idea', 'Ideia'),
        ('feedback', 'Feedback'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('under_review', 'Em Análise'),
        ('in_progress', 'Em Andamento'),
        ('implemented', 'Implementado'),
        ('rejected', 'Rejeitado'),
        ('closed', 'Fechado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    suggestion_type = models.CharField('Tipo', max_length=20, choices=SUGGESTION_TYPES, default='improvement')
    
    # Autor (opcional para sugestões anônimas)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='suggestions',
        verbose_name='Autor'
    )
    is_anonymous = models.BooleanField('Anônimo', default=False)
    
    # Departamento relacionado
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='suggestions',
        verbose_name='Departamento'
    )
    
    # Status
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_suggestions',
        verbose_name='Atribuído a'
    )
    
    # Resposta
    response = models.TextField('Resposta', blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='responded_suggestions',
        verbose_name='Respondido por'
    )
    responded_at = models.DateTimeField('Respondido em', null=True, blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Sugestão'
        verbose_name_plural = 'Sugestões'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def respond(self, response, user):
        self.response = response
        self.responded_by = user
        self.responded_at = timezone.now()
        self.save(update_fields=['response', 'responded_by', 'responded_at'])


class CommunicationSettings(models.Model):
    """Configurações de Comunicação do usuário"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_settings',
        verbose_name='Usuário'
    )
    
    # Notificações
    email_announcements = models.BooleanField('Comunicados por Email', default=True)
    email_memos = models.BooleanField('Memorandos por Email', default=True)
    email_newsletters = models.BooleanField('Newsletters por Email', default=False)
    
    # Preferências
    digest_frequency = models.CharField('Frequência do Resumo', max_length=10, choices=[
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('never', 'Nunca'),
    ], default='weekly')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configurações de Comunicação'
        verbose_name_plural = 'Configurações de Comunicação'

    def __str__(self):
        return f"Configurações de {self.user.get_full_name()}"


class CommunicationCampaign(models.Model):
    """Campanhas de Comunicação"""
    CAMPAIGN_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
        ('mixed', 'Misto'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('scheduled', 'Agendado'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField('Nome da Campanha', max_length=200)
    description = models.TextField('Descrição', blank=True)
    campaign_type = models.CharField('Tipo', max_length=20, choices=CAMPAIGN_TYPES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Conteúdo
    subject = models.CharField('Assunto', max_length=200)
    content = models.TextField('Conteúdo')
    html_content = models.TextField('Conteúdo HTML', blank=True)
    
    # Segmentação
    target_departments = models.ManyToManyField(
        'hr.Department',
        related_name='communication_campaigns',
        verbose_name='Departamentos',
        blank=True
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='communication_campaigns',
        verbose_name='Usuários Específicos',
        blank=True
    )
    segmentation_rules = models.JSONField('Regras de Segmentação', default=dict, blank=True)
    
    # Agendamento
    send_at = models.DateTimeField('Enviar em', null=True, blank=True)
    sent_at = models.DateTimeField('Enviado em', null=True, blank=True)
    
    # Métricas
    recipients_count = models.IntegerField('Total de Destinatários', default=0)
    sent_count = models.IntegerField('Enviados', default=0)
    delivered_count = models.IntegerField('Entregues', default=0)
    opened_count = models.IntegerField('Abertos', default=0)
    clicked_count = models.IntegerField('Clicados', default=0)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_campaigns',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Campanha de Comunicação'
        verbose_name_plural = 'Campanhas de Comunicação'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.delivered_count == 0:
            return 0
        return (self.opened_count / self.delivered_count) * 100

    @property
    def click_rate(self):
        if self.opened_count == 0:
            return 0
        return (self.clicked_count / self.opened_count) * 100


class CommunicationTemplate(models.Model):
    """Templates de Comunicação"""
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('announcement', 'Comunicado'),
    ]

    name = models.CharField('Nome do Template', max_length=200)
    description = models.TextField('Descrição', blank=True)
    template_type = models.CharField('Tipo', max_length=20, choices=TEMPLATE_TYPES)
    
    # Conteúdo
    subject_template = models.CharField('Template do Assunto', max_length=200, blank=True)
    content_template = models.TextField('Template do Conteúdo')
    html_template = models.TextField('Template HTML', blank=True)
    
    # Configurações
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    
    # Variáveis disponíveis
    available_variables = models.JSONField('Variáveis Disponíveis', default=dict, blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_communication_templates',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Template de Comunicação'
        verbose_name_plural = 'Templates de Comunicação'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CommunicationChannel(models.Model):
    """Canais de Comunicação"""
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('slack', 'Slack'),
        ('telegram', 'Telegram'),
        ('webhook', 'Webhook'),
    ]

    name = models.CharField('Nome do Canal', max_length=200)
    channel_type = models.CharField('Tipo', max_length=20, choices=CHANNEL_TYPES)
    configuration = models.JSONField('Configuração', default=dict)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Limites
    daily_limit = models.IntegerField('Limite Diário', default=1000)
    hourly_limit = models.IntegerField('Limite por Hora', default=100)
    
    # Estatísticas
    total_sent = models.IntegerField('Total Enviado', default=0)
    total_delivered = models.IntegerField('Total Entregue', default=0)
    total_failed = models.IntegerField('Total Falhou', default=0)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_communication_channels',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Canal de Comunicação'
        verbose_name_plural = 'Canais de Comunicação'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"

    @property
    def delivery_rate(self):
        if self.total_sent == 0:
            return 0
        return (self.total_delivered / self.total_sent) * 100


class CommunicationSegment(models.Model):
    """Segmentos de Audiência"""
    name = models.CharField('Nome do Segmento', max_length=200)
    description = models.TextField('Descrição', blank=True)
    
    # Regras de segmentação
    filter_rules = models.JSONField('Regras de Filtro', default=dict)
    
    # Usuários
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='communication_segments',
        verbose_name='Usuários',
        blank=True
    )
    
    # Configurações
    is_active = models.BooleanField('Ativo', default=True)
    auto_update = models.BooleanField('Atualização Automática', default=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_segments',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Segmento de Audiência'
        verbose_name_plural = 'Segmentos de Audiência'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_users_count(self):
        return self.users.count()


class CommunicationAnalytics(models.Model):
    """Analytics de Comunicação"""
    campaign = models.ForeignKey(
        CommunicationCampaign,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='Campanha',
        null=True,
        blank=True
    )
    date = models.DateField('Data', null=True, blank=True)
    
    # Métricas
    sent_count = models.IntegerField('Enviados', default=0)
    delivered_count = models.IntegerField('Entregues', default=0)
    opened_count = models.IntegerField('Abertos', default=0)
    clicked_count = models.IntegerField('Clicados', default=0)
    bounced_count = models.IntegerField('Rejeitados', default=0)
    unsubscribed_count = models.IntegerField('Descadastrados', default=0)
    
    # Engagement
    unique_opens = models.IntegerField('Aberturas Únicas', default=0)
    unique_clicks = models.IntegerField('Cliques Únicos', default=0)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Analytics de Comunicação'
        verbose_name_plural = 'Analytics de Comunicação'

    def __str__(self):
        return f"Analytics - {self.date or self.created_at.date()}"


class CommunicationEvent(models.Model):
    """Eventos de Comunicação"""
    EVENT_TYPES = [
        ('sent', 'Enviado'),
        ('delivered', 'Entregue'),
        ('opened', 'Aberto'),
        ('clicked', 'Clicado'),
        ('bounced', 'Rejeitado'),
        ('unsubscribed', 'Descadastrado'),
        ('failed', 'Falhou'),
    ]

    campaign = models.ForeignKey(
        CommunicationCampaign,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Campanha',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_events',
        verbose_name='Usuário'
    )
    event_type = models.CharField('Tipo do Evento', max_length=20, choices=EVENT_TYPES)
    
    # Dados do evento
    event_data = models.JSONField('Dados do Evento', default=dict, blank=True)
    
    # Metadados
    timestamp = models.DateTimeField('Timestamp', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)

    class Meta:
        verbose_name = 'Evento de Comunicação'
        verbose_name_plural = 'Eventos de Comunicação'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_event_type_display()}"


class CommunicationPreference(models.Model):
    """Preferências de Comunicação dos Usuários"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_preferences_legacy',
        verbose_name='Usuário'
    )
    
    # Canais preferidos
    email_enabled = models.BooleanField('Email', default=True)
    sms_enabled = models.BooleanField('SMS', default=True)
    push_enabled = models.BooleanField('Push Notifications', default=True)
    in_app_enabled = models.BooleanField('In-App', default=True)
    
    # Tipos de comunicação
    announcements_enabled = models.BooleanField('Comunicados', default=True)
    newsletters_enabled = models.BooleanField('Newsletters', default=True)
    events_enabled = models.BooleanField('Eventos', default=True)
    reminders_enabled = models.BooleanField('Lembretes', default=True)
    
    # Frequência
    frequency = models.CharField(
        'Frequência',
        max_length=20,
        choices=[
            ('immediate', 'Imediato'),
            ('daily', 'Diário'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensal'),
        ],
        default='immediate'
    )
    
    # Horários
    preferred_time_start = models.TimeField('Horário Preferido - Início', null=True, blank=True)
    preferred_time_end = models.TimeField('Horário Preferido - Fim', null=True, blank=True)
    
    # Timezone
    timezone = models.CharField('Timezone', max_length=50, default='America/Sao_Paulo')
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Preferência de Comunicação'
        verbose_name_plural = 'Preferências de Comunicação'

    def __str__(self):
        return f"Preferências de {self.user.get_full_name()}"

# Manter compatibilidade com modelos antigos


# ===== MODELOS REFATORADOS =====

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
    summary = models.CharField('Resumo', max_length=500, blank=True)
    
    # Classificação
    message_type = models.CharField(
        'Tipo de Mensagem',
        max_length=50,
        choices=MESSAGE_TYPES,
        default='announcement'
    )
    priority = models.CharField(
        'Prioridade',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    category = models.CharField(
        'Categoria',
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    
    # Metadata
    tags = models.CharField('Tags', max_length=200, blank=True)
    
    # Controle de resposta
    requires_response = models.BooleanField('Requer Resposta', default=False)
    allow_responses = models.BooleanField('Permite Respostas', default=True)
    response_deadline = models.DateTimeField('Prazo para Resposta', blank=True, null=True)
    
    # Controle de exibição
    is_pinned = models.BooleanField('Fixado', default=False)
    publish_date = models.DateTimeField('Data de Publicação', blank=True, null=True)
    expire_date = models.DateTimeField('Data de Expiração', blank=True, null=True)
    
    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_messages',
        verbose_name='Autor'
    )
    
    # Métricas
    view_count = models.IntegerField('Visualizações', default=0)
    response_count = models.IntegerField('Respostas', default=0)
    engagement_score = models.FloatField('Score de Engajamento', default=0.0)
    
    # Campos genéricos para relacionamentos
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadados JSON
    metadata = models.JSONField('Metadados', default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Mensagem de Comunicação'
        verbose_name_plural = 'Mensagens de Comunicação'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['message_type', 'category']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return f'/communication/messages/{self.id}/'
    
    def is_published(self):
        return (
            self.status == 'published' and
            self.publish_date and
            self.publish_date <= timezone.now()
        )
    
    def is_expired(self):
        return (
            self.expire_date and
            self.expire_date <= timezone.now()
        )
    
    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


class MessageRecipient(models.Model):
    """Destinatários das mensagens com controle individual"""
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('delivered', 'Entregue'),
        ('failed', 'Falhou'),
        ('bounced', 'Rejeitada'),
    ]
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='Mensagem'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Usuário'
    )
    
    # Status de leitura
    is_read = models.BooleanField('Lida', default=False)
    read_at = models.DateTimeField('Lida em', blank=True, null=True)
    
    # Controle de arquivamento
    is_archived = models.BooleanField('Arquivada', default=False)
    archived_at = models.DateTimeField('Arquivada em', blank=True, null=True)
    
    # Status de entrega
    delivery_status = models.CharField(
        'Status de Entrega',
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending'
    )
    delivery_attempted_at = models.DateTimeField('Tentativa de Entrega', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Destinatário da Mensagem'
        verbose_name_plural = 'Destinatários da Mensagem'
        ordering = ['-created_at']
        unique_together = [['message', 'user']]
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['message', 'delivery_status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.message.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_unread(self):
        self.is_read = False
        self.read_at = None
        self.save()
    
    def archive(self):
        if not self.is_archived:
            self.is_archived = True
            self.archived_at = timezone.now()
            self.save()


class MessageResponse(models.Model):
    """Respostas às mensagens"""
    
    RESPONSE_TYPE_CHOICES = [
        ('reply', 'Resposta'),
        ('acknowledgment', 'Confirmação'),
        ('question', 'Pergunta'),
        ('feedback', 'Feedback'),
    ]
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Mensagem'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_responses',
        verbose_name='Usuário'
    )
    
    content = models.TextField('Conteúdo da Resposta')
    response_type = models.CharField(
        'Tipo de Resposta',
        max_length=20,
        choices=RESPONSE_TYPE_CHOICES,
        default='reply'
    )
    
    # Controle de privacidade
    is_private = models.BooleanField('Resposta Privada', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Resposta à Mensagem'
        verbose_name_plural = 'Respostas às Mensagens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message', 'created_at']),
            models.Index(fields=['user', 'response_type']),
        ]
    
    def __str__(self):
        return f"Resposta de {self.user.get_full_name()} para {self.message.title}"


class MessageAttachment(models.Model):
    """Anexos das mensagens"""
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Mensagem'
    )
    
    file = models.FileField(
        'Arquivo',
        upload_to='communication/attachments/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif']
            )
        ]
    )
    
    # Metadata do arquivo
    original_filename = models.CharField('Nome Original', max_length=255, blank=True)
    file_size = models.IntegerField('Tamanho do Arquivo', blank=True, null=True)
    content_type = models.CharField('Tipo de Conteúdo', max_length=100, blank=True)
    
    # Descrição
    description = models.CharField('Descrição', max_length=255, blank=True)
    
    # Controle de acesso
    is_public = models.BooleanField('Público', default=True)
    
    # Métricas
    download_count = models.IntegerField('Downloads', default=0)
    
    # Uploader
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Enviado por'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Anexo da Mensagem'
        verbose_name_plural = 'Anexos das Mensagens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Anexo: {self.original_filename or self.file.name}"
    
    def get_file_size_display(self):
        if self.file_size:
            if self.file_size < 1024:
                return f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                return f"{self.file_size / 1024:.1f} KB"
            else:
                return f"{self.file_size / (1024 * 1024):.1f} MB"
        return "Tamanho desconhecido"


class CommunicationPreferences(models.Model):
    """Preferências de comunicação do usuário"""
    
    NOTIFICATION_FREQUENCY_CHOICES = [
        ('immediate', 'Imediata'),
        ('daily', 'Diária'),
        ('weekly', 'Semanal'),
        ('none', 'Nenhuma'),
    ]
    
    LANGUAGE_CHOICES = [
        ('pt', 'Português'),
        ('en', 'English'),
        ('es', 'Español'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_preferences',
        verbose_name='Usuário'
    )
    
    # Canais de notificação
    email_notifications = models.BooleanField('Notificações por Email', default=True)
    push_notifications = models.BooleanField('Notificações Push', default=True)
    sms_notifications = models.BooleanField('Notificações SMS', default=False)
    
    # Frequência
    notification_frequency = models.CharField(
        'Frequência de Notificação',
        max_length=20,
        choices=NOTIFICATION_FREQUENCY_CHOICES,
        default='immediate'
    )
    
    # Filtros
    message_types = models.JSONField('Tipos de Mensagem', default=list)
    categories = models.JSONField('Categorias', default=list)
    
    # Horário silencioso
    quiet_hours_start = models.TimeField('Início do Horário Silencioso', blank=True, null=True)
    quiet_hours_end = models.TimeField('Fim do Horário Silencioso', blank=True, null=True)
    
    # Localização
    language = models.CharField(
        'Idioma',
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='pt'
    )
    timezone = models.CharField('Fuso Horário', max_length=50, default='America/Sao_Paulo')
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Preferências de Comunicação'
        verbose_name_plural = 'Preferências de Comunicação'
        unique_together = [['user']]
    
    def __str__(self):
        return f"Preferências de {self.user.get_full_name()}"
    
    def get_allowed_message_types(self):
        if self.message_types:
            return self.message_types
        return [choice[0] for choice in CommunicationMessage.MESSAGE_TYPES]
    
    def get_allowed_categories(self):
        if self.categories:
            return self.categories
        return [choice[0] for choice in CommunicationMessage.CATEGORY_CHOICES]


class CommunicationAnalyticsRefactored(models.Model):
    """Analytics de comunicação refatorado"""
    
    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='analytics_refactored',
        verbose_name='Mensagem',
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_analytics_refactored',
        verbose_name='Usuário',
        blank=True,
        null=True
    )
    
    # Métricas
    metric_name = models.CharField('Nome da Métrica', max_length=100)
    metric_value = models.JSONField('Valor da Métrica')
    
    # Período
    period_start = models.DateTimeField('Início do Período')
    period_end = models.DateTimeField('Fim do Período')
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Analítica de Comunicação Refatorada'
        verbose_name_plural = 'Analíticas de Comunicação Refatoradas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.metric_name} - {self.period_start.date()}"


# Manter compatibilidade com modelos antigos
