"""
Sistema de notificações para MoveMarias
Suporta notificações em tempo real, email e push notifications
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import json
from datetime import datetime, timedelta

User = get_user_model()


class NotificationChannel(models.Model):
    """Canais de notificação disponíveis"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome")
    display_name = models.CharField(max_length=100, verbose_name="Nome de Exibição")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    configuration = models.JSONField(default=dict, verbose_name="Configuração")
    
    class Meta:
        verbose_name = "Canal de Notificação"
        verbose_name_plural = "Canais de Notificação"
    
    def __str__(self):
        return self.display_name


class NotificationTemplate(models.Model):
    """Templates para diferentes tipos de notificação"""
    NOTIFICATION_TYPES = [
        ('welcome', 'Boas-vindas'),
        ('workshop_enrollment', 'Inscrição em Workshop'),
        ('workshop_reminder', 'Lembrete de Workshop'),
        ('certificate_ready', 'Certificado Pronto'),
        ('project_invitation', 'Convite para Projeto'),
        ('coaching_scheduled', 'Coaching Agendado'),
        ('system_update', 'Atualização do Sistema'),
        ('password_reset', 'Redefinição de Senha'),
        ('account_verification', 'Verificação de Conta'),
        ('general', 'Geral'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nome")
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, verbose_name="Tipo")
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name="Canal"
    )
    
    # Templates
    subject_template = models.CharField(
        max_length=200,
        verbose_name="Template do Assunto",
        help_text="Use variáveis como {{user.name}}, {{workshop.title}}"
    )
    content_template = models.TextField(
        verbose_name="Template do Conteúdo",
        help_text="Suporta HTML e variáveis"
    )
    
    # Configurações
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    priority = models.IntegerField(
        default=1,
        choices=[
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        verbose_name="Prioridade"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de Notificação"
        verbose_name_plural = "Templates de Notificação"
        unique_together = ['type', 'channel']
    
    def __str__(self):
        return f"{self.name} - {self.channel.display_name}"


class Notification(models.Model):
    """Notificação individual"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregue'),
        ('read', 'Lida'),
        ('failed', 'Falhou'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinatário"
    )
    
    # Conteúdo
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensagem")
    html_message = models.TextField(blank=True, verbose_name="Mensagem HTML")
    
    # Classificação
    type = models.CharField(max_length=30, choices=NotificationTemplate.NOTIFICATION_TYPES, verbose_name="Tipo")
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Canal"
    )
    priority = models.IntegerField(
        default=1,
        choices=[
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        verbose_name="Prioridade"
    )
    
    # Objeto relacionado (genérico)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Metadados
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Marcar notificação como lida"""
        if self.status != 'read':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_delivered(self):
        """Marcar notificação como entregue"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save()
    
    def send(self):
        """Enviar notificação"""
        if self.status != 'pending':
            return False
        
        try:
            if self.channel.name == 'email':
                self._send_email()
            elif self.channel.name == 'push':
                self._send_push()
            elif self.channel.name == 'sms':
                self._send_sms()
            elif self.channel.name == 'in_app':
                self._send_in_app()
            
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save()
            return True
            
        except Exception as e:
            self.status = 'failed'
            self.metadata['error'] = str(e)
            self.save()
            return False
    
    def _send_email(self):
        """Enviar notificação por email"""
        send_mail(
            subject=self.title,
            message=self.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.recipient.email],
            html_message=self.html_message if self.html_message else None,
            fail_silently=False,
        )
    
    def _send_push(self):
        """Enviar push notification"""
        # Implementar integração com serviço de push (Firebase, etc.)
        pass
    
    def _send_sms(self):
        """Enviar SMS"""
        # Implementar integração com serviço de SMS
        pass
    
    def _send_in_app(self):
        """Notificação in-app (já salva no banco)"""
        pass


class NotificationPreference(models.Model):
    """Preferências de notificação do usuário"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name="Usuário"
    )
    
    # Canais habilitados
    email_enabled = models.BooleanField(default=True, verbose_name="Email")
    push_enabled = models.BooleanField(default=True, verbose_name="Push")
    sms_enabled = models.BooleanField(default=False, verbose_name="SMS")
    in_app_enabled = models.BooleanField(default=True, verbose_name="In-App")
    
    # Tipos de notificação
    workshop_notifications = models.BooleanField(default=True, verbose_name="Workshops")
    certificate_notifications = models.BooleanField(default=True, verbose_name="Certificados")
    project_notifications = models.BooleanField(default=True, verbose_name="Projetos")
    coaching_notifications = models.BooleanField(default=True, verbose_name="Coaching")
    system_notifications = models.BooleanField(default=True, verbose_name="Sistema")
    
    # Configurações avançadas
    quiet_hours_start = models.TimeField(
        default='22:00',
        verbose_name="Início do Silêncio"
    )
    quiet_hours_end = models.TimeField(
        default='08:00',
        verbose_name="Fim do Silêncio"
    )
    frequency_limit = models.IntegerField(
        default=10,
        verbose_name="Limite de Notificações por Dia"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferência de Notificação"
        verbose_name_plural = "Preferências de Notificação"
    
    def __str__(self):
        return f"Preferências de {self.user.username}"
    
    def can_receive_notification(self, notification_type, channel):
        """Verifica se o usuário pode receber a notificação"""
        # Verificar se o canal está habilitado
        if channel == 'email' and not self.email_enabled:
            return False
        elif channel == 'push' and not self.push_enabled:
            return False
        elif channel == 'sms' and not self.sms_enabled:
            return False
        elif channel == 'in_app' and not self.in_app_enabled:
            return False
        
        # Verificar tipo de notificação
        type_mapping = {
            'workshop_enrollment': self.workshop_notifications,
            'workshop_reminder': self.workshop_notifications,
            'certificate_ready': self.certificate_notifications,
            'project_invitation': self.project_notifications,
            'coaching_scheduled': self.coaching_notifications,
            'system_update': self.system_notifications,
        }
        
        if notification_type in type_mapping:
            return type_mapping[notification_type]
        
        return True
    
    def is_in_quiet_hours(self):
        """Verifica se está no horário de silêncio"""
        now = timezone.now().time()
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
    
    def daily_notification_count(self):
        """Conta notificações recebidas hoje"""
        today = timezone.now().date()
        return Notification.objects.filter(
            recipient=self.user,
            created_at__date=today
        ).count()
    
    def can_receive_more_notifications(self):
        """Verifica se pode receber mais notificações hoje"""
        return self.daily_notification_count() < self.frequency_limit


class NotificationBatch(models.Model):
    """Lote de notificações para envio em massa"""
    name = models.CharField(max_length=100, verbose_name="Nome do Lote")
    description = models.TextField(blank=True, verbose_name="Descrição")
    
    # Filtros
    target_users = models.ManyToManyField(
        User,
        related_name='notification_batches',
        verbose_name="Usuários Alvo"
    )
    
    # Template
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name="Template"
    )
    
    # Conteúdo
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensagem")
    
    # Agendamento
    scheduled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Agendado para"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Rascunho'),
            ('scheduled', 'Agendado'),
            ('sending', 'Enviando'),
            ('sent', 'Enviado'),
            ('failed', 'Falhou'),
        ],
        default='draft',
        verbose_name="Status"
    )
    
    # Resultados
    total_recipients = models.IntegerField(default=0, verbose_name="Total de Destinatários")
    sent_count = models.IntegerField(default=0, verbose_name="Enviados")
    failed_count = models.IntegerField(default=0, verbose_name="Falharam")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lote de Notificação"
        verbose_name_plural = "Lotes de Notificação"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def send_batch(self):
        """Enviar lote de notificações"""
        if self.status != 'scheduled':
            return False
        
        self.status = 'sending'
        self.save()
        
        sent_count = 0
        failed_count = 0
        
        for user in self.target_users.all():
            try:
                # Criar notificação individual
                notification = Notification.objects.create(
                    recipient=user,
                    title=self.title,
                    message=self.message,
                    type=self.template.type,
                    channel=self.template.channel,
                    priority=self.template.priority
                )
                
                # Enviar
                if notification.send():
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
        
        self.sent_count = sent_count
        self.failed_count = failed_count
        self.status = 'sent' if failed_count == 0 else 'failed'
        self.save()
        
        return True


# Funções auxiliares
def create_notification(recipient, title, message, notification_type='general', 
                       channel='in_app', priority=1, related_object=None):
    """Criar notificação"""
    try:
        # Verificar preferências do usuário
        preferences, created = NotificationPreference.objects.get_or_create(
            user=recipient
        )
        
        # Verificar se pode receber notificação
        if not preferences.can_receive_notification(notification_type, channel):
            return None
        
        # Verificar horário de silêncio
        if preferences.is_in_quiet_hours() and priority < 3:
            return None
        
        # Verificar limite diário
        if not preferences.can_receive_more_notifications():
            return None
        
        # Obter canal
        channel_obj = NotificationChannel.objects.get(name=channel)
        
        # Criar notificação
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            type=notification_type,
            channel=channel_obj,
            priority=priority,
            related_object=related_object
        )
        
        return notification
        
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
        return None


def send_notification(recipient, title, message, notification_type='general',
                     channel='in_app', priority=1, related_object=None):
    """Criar e enviar notificação"""
    notification = create_notification(
        recipient, title, message, notification_type, 
        channel, priority, related_object
    )
    
    if notification:
        return notification.send()
    
    return False


def send_bulk_notification(recipients, title, message, notification_type='general',
                          channel='in_app', priority=1):
    """Enviar notificação em massa"""
    results = []
    
    for recipient in recipients:
        result = send_notification(
            recipient, title, message, notification_type, channel, priority
        )
        results.append(result)
    
    return results


def get_user_notifications(user, unread_only=False, limit=None):
    """Obter notificações do usuário"""
    notifications = Notification.objects.filter(recipient=user)
    
    if unread_only:
        notifications = notifications.exclude(status='read')
    
    notifications = notifications.order_by('-created_at')
    
    if limit:
        notifications = notifications[:limit]
    
    return notifications


def mark_all_as_read(user):
    """Marcar todas as notificações como lidas"""
    return Notification.objects.filter(
        recipient=user,
        status__in=['pending', 'sent', 'delivered']
    ).update(
        status='read',
        read_at=timezone.now()
    )
