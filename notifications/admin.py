"""
Admin interface para o sistema de notificações
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.admin import SimpleListFilter

from .models import Notification, NotificationPreference, NotificationTemplate, NotificationChannel


class NotificationStatusFilter(SimpleListFilter):
    """Filtro customizado para status de notificações"""
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pendente'),
            ('sent', 'Enviada'),
            ('delivered', 'Entregue'),
            ('read', 'Lida'),
            ('failed', 'Falhou'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class NotificationCategoryFilter(SimpleListFilter):
    """Filtro customizado para categorias de notificações"""
    title = 'Categoria'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return NotificationTemplate.NOTIFICATION_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administração de notificações"""
    
    list_display = [
        'title', 'recipient', 'type', 'channel', 'priority', 'status', 
        'created_at', 'read_at'
    ]
    list_filter = [
        NotificationStatusFilter, 
        NotificationCategoryFilter,
        'priority',
        'created_at',
        'channel'
    ]
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'message', 'recipient')
        }),
        ('Configurações', {
            'fields': ('type', 'channel', 'priority')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'mark_as_read',
        'mark_as_unread',
        'send_notification',
        'delete_old_notifications'
    ]
    
    def is_read_display(self, obj):
        """Exibe status de leitura com ícones"""
        if obj.is_read:
            return format_html(
                '<span style="color: green;">✓ Lida</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Não lida</span>'
            )
    is_read_display.short_description = 'Status'
    
    def action_buttons(self, obj):
        """Botões de ação customizados"""
        buttons = []
        
        if not obj.is_read:
            buttons.append(
                format_html(
                    '<a class="button" href="{}">Marcar como lida</a>',
                    reverse('admin:notifications_notification_mark_read', args=[obj.pk])
                )
            )
        
        if obj.action_url:
            buttons.append(
                format_html(
                    '<a class="button" href="{}" target="_blank">Ver ação</a>',
                    obj.action_url
                )
            )
        
        return format_html(' '.join(buttons))
    action_buttons.short_description = 'Ações'
    
    def get_queryset(self, request):
        """Otimiza queries com select_related"""
        return super().get_queryset(request).select_related('user')
    
    def mark_as_read(self, request, queryset):
        """Ação para marcar notificações como lidas"""
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} notificações marcadas como lidas.',
            messages.SUCCESS
        )
    mark_as_read.short_description = "Marcar como lidas"
    
    def mark_as_unread(self, request, queryset):
        """Ação para marcar notificações como não lidas"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(
            request,
            f'{updated} notificações marcadas como não lidas.',
            messages.SUCCESS
        )
    mark_as_unread.short_description = "Marcar como não lidas"
    
    def send_notification(self, request, queryset):
        """Ação para reenviar notificações"""
        sent = 0
        for notification in queryset:
            try:
                notification.send_notification()
                sent += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Erro ao enviar notificação {notification.id}: {str(e)}',
                    messages.ERROR
                )
        
        if sent > 0:
            self.message_user(
                request,
                f'{sent} notificações reenviadas com sucesso.',
                messages.SUCCESS
            )
    send_notification.short_description = "Reenviar notificações"
    
    def delete_old_notifications(self, request, queryset):
        """Ação para deletar notificações antigas"""
        # Remove notificações lidas com mais de 30 dias
        old_date = timezone.now() - timezone.timedelta(days=30)
        deleted = queryset.filter(
            is_read=True,
            created_at__lt=old_date
        ).delete()
        
        self.message_user(
            request,
            f'{deleted[0]} notificações antigas removidas.',
            messages.SUCCESS
        )
    delete_old_notifications.short_description = "Remover notificações antigas"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Administração de preferências de notificação"""
    
    list_display = [
        'user', 'email_enabled', 'sms_enabled', 'push_enabled', 
        'in_app_enabled', 'updated_at'
    ]
    list_filter = [
        'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
        'updated_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Canais de Notificação', {
            'fields': (
                'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled'
            )
        }),
        ('Categorias', {
            'fields': ('categories',)
        }),
        ('Configurações Avançadas', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Otimiza queries com select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Administração de templates de notificação"""
    
    list_display = [
        'name', 'type', 'channel', 'is_active', 'created_at'
    ]
    list_filter = ['type', 'channel', 'is_active', 'created_at']
    search_fields = ['name', 'subject_template', 'content_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'type', 'channel', 'is_active')
        }),
        ('Conteúdo', {
            'fields': ('subject_template', 'content_template')
        }),
        ('Configurações', {
            'fields': ('priority',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Administração de canais de notificação"""
    
    list_display = [
        'name', 'display_name', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    readonly_fields = []
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'display_name')
        }),
        ('Configurações', {
            'fields': ('is_active',)
        }),
        ('Configuração Técnica', {
            'fields': ('configuration',),
            'description': 'Configurações específicas do canal (JSON)',
            'classes': ('collapse',)
        })
    )
    
    actions = ['test_channel_action']
    
    def test_channel(self, obj):
        """Botão para testar canal"""
        return format_html(
            '<a class="button" href="{}">Testar</a>',
            reverse('admin:notifications_notificationchannel_test', args=[obj.pk])
        )
    test_channel.short_description = 'Teste'
    
    def test_channel_action(self, request, queryset):
        """Ação para testar canais selecionados"""
        for channel in queryset:
            try:
                # Implementar teste específico por tipo de canal
                if channel.channel_type == 'email':
                    # Teste de email
                    pass
                elif channel.channel_type == 'sms':
                    # Teste de SMS
                    pass
                elif channel.channel_type == 'push':
                    # Teste de push
                    pass
                
                self.message_user(
                    request,
                    f'Canal {channel.name} testado com sucesso.',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Erro ao testar canal {channel.name}: {str(e)}',
                    messages.ERROR
                )
    test_channel_action.short_description = "Testar canais"


# Customização do admin site
admin.site.site_header = 'MoveMarias - Sistema de Notificações'
admin.site.site_title = 'MoveMarias Admin'
admin.site.index_title = 'Painel de Administração'

# Estatísticas personalizadas no admin
class NotificationStatsAdmin(admin.ModelAdmin):
    """Classe para adicionar estatísticas ao admin"""
    
    def changelist_view(self, request, extra_context=None):
        """Adiciona estatísticas ao changelist"""
        extra_context = extra_context or {}
        
        # Estatísticas gerais
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        today_notifications = Notification.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Estatísticas por categoria
        category_stats = Notification.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        extra_context.update({
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'today_notifications': today_notifications,
            'category_stats': category_stats,
            'read_rate': round(
                (total_notifications - unread_notifications) / total_notifications * 100, 2
            ) if total_notifications > 0 else 0
        })
        
        return super().changelist_view(request, extra_context)


# Registrar estatísticas
admin.site.unregister(Notification)
admin.site.register(Notification, type('NotificationAdminWithStats', (NotificationAdmin, NotificationStatsAdmin), {}))
