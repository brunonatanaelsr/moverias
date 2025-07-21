"""
Views para o sistema de notificações
"""
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from core.unified_permissions import (
    
    get_user_permissions,
    requires_technician,
    requires_admin,
    TechnicianRequiredMixin,
    AdminRequiredMixin
)
from .models import Notification, NotificationPreference, NotificationTemplate, NotificationChannel
from .forms import NotificationForm, NotificationPreferenceForm, NotificationTemplateForm


class NotificationListView(LoginRequiredMixin, ListView):
    """Lista de notificações do usuário"""
    model = Notification
    template_name = 'notifications/notification_list_unified.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra notificações do usuário atual"""
        qs = Notification.objects.filter(recipient=self.request.user)
        
        # Filtro de busca
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | 
                Q(message__icontains=search)
            )
        
        # Filtros de status
        status_filter = self.request.GET.get('status')
        if status_filter:
            if status_filter == 'unread':
                qs = qs.filter(status='pending')
            elif status_filter == 'read':
                qs = qs.filter(status='read')
        
        # Filtros de categoria
        category = self.request.GET.get('type')
        if category:
            qs = qs.filter(type=category)
        
        # Filtros de prioridade
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas básicas
        user_notifications = Notification.objects.filter(recipient=self.request.user)
        context['unread_count'] = user_notifications.filter(status='pending').count()
        context['total_count'] = user_notifications.count()
        
        # Opções de filtro
        context['types'] = NotificationTemplate.NOTIFICATION_TYPES
        context['priorities'] = [
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ]
        context['statuses'] = [
            ('unread', 'Não lidas'),
            ('read', 'Lidas'),
        ]
        
        # Filtros ativos
        context['active_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'type': self.request.GET.get('type', ''),
            'priority': self.request.GET.get('priority', ''),
        }
        
        # Contexto para template unificado
        context['user_permissions'] = get_user_permissions(self.request.user)
        context['list_title'] = 'Notificações'
        context['module_name'] = 'Notificações'
        context['object_name'] = 'Notificação'
        context['create_url'] = 'notifications:create'
        context['detail_url'] = 'notifications:detail'
        context['edit_url'] = 'notifications:edit'
        context['delete_url'] = 'notifications:delete'
        context['can_create'] = get_user_permissions(self.request.user).get('can_create_notifications', False)
        context['can_edit'] = True
        context['can_delete'] = True
        
        # Estatísticas de hoje
        from datetime import datetime
        today = datetime.now().date()
        context['today_count'] = user_notifications.filter(created_at__date=today).count()
        
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """Detalhes de uma notificação"""
    model = Notification
    template_name = 'notifications/notification_detail_unified.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        """Apenas notificações do usuário atual"""
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Notificação'
        context['module_name'] = 'Notificações'
        context['list_url'] = reverse_lazy('notifications:list')
        context['edit_url'] = reverse_lazy('notifications:edit', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('notifications:delete', kwargs={'pk': self.object.pk})
        context['can_edit'] = self.request.user.is_staff or self.object.recipient == self.request.user
        context['can_delete'] = self.request.user.is_staff or self.object.recipient == self.request.user
        return context
    
    def get_object(self):
        """Marca como lida ao visualizar"""
        obj = super().get_object()
        if obj.status == 'pending':
            obj.status = 'read'
            obj.read_at = timezone.now()
            obj.save()
        return obj


class NotificationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Criar nova notificação (para admins)"""
    model = Notification
    form_class = NotificationForm
    template_name = 'notifications/notification_form_unified.html'
    success_url = reverse_lazy('notifications:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Notificação'
        context['module_name'] = 'Notificações'
        context['list_url'] = reverse_lazy('notifications:list')
        context['form_title'] = 'Criar Nova Notificação'
        context['submit_text'] = 'Criar Notificação'
        return context
    
    def form_valid(self, form):
        """Adiciona o usuário atual como criador"""
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Notificação criada com sucesso!')
        return super().form_valid(form)


class NotificationUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Editar notificação (para admins)"""
    model = Notification
    form_class = NotificationForm
    template_name = 'notifications/notification_form_unified.html'
    success_url = reverse_lazy('notifications:list')
    
    def get_queryset(self):
        """Apenas notificações do usuário atual ou staff"""
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Notificação'
        context['module_name'] = 'Notificações'
        context['list_url'] = reverse_lazy('notifications:list')
        context['form_title'] = 'Editar Notificação'
        context['submit_text'] = 'Atualizar Notificação'
        return context
    
    def form_valid(self, form):
        """Adiciona mensagem de sucesso"""
        messages.success(self.request, 'Notificação atualizada com sucesso!')
        return super().form_valid(form)


class NotificationPreferenceView(LoginRequiredMixin, UpdateView):
    """Configurar preferências de notificação"""
    model = NotificationPreference
    form_class = NotificationPreferenceForm
    template_name = 'notifications/notification_preferences.html'
    success_url = reverse_lazy('notifications:preferences')
    
    def get_object(self):
        """Obtém ou cria preferências do usuário"""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Preferências atualizadas com sucesso!')
        return super().form_valid(form)


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Marca uma notificação como lida via AJAX"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            recipient=request.user
        )
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificação marcada como lida'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """Marca todas as notificações como lidas via AJAX"""
    try:
        count = Notification.objects.filter(
            recipient=request.user, 
            status='pending'
        ).update(status='read', read_at=timezone.now())
        
        return JsonResponse({
            'success': True, 
            'count': count,
            'message': f'{count} notificações marcadas como lidas'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
def notification_count(request):
    """Retorna contador de notificações não lidas via AJAX"""
    count = Notification.objects.filter(
        recipient=request.user, 
        status='pending'
    ).count()
    return JsonResponse({'count': count})


@login_required
def notification_popup(request):
    """Retorna notificações recentes para popup"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        status='pending'
    ).order_by('-created_at')[:5]
    
    data = []
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'url': '#'
        })
    
    return JsonResponse({'notifications': data})


class NotificationChannelListView(LoginRequiredMixin, ListView):
    """Lista de canais de notificação disponíveis"""
    model = NotificationChannel
    template_name = 'notifications/channel_list.html'
    context_object_name = 'channels'
    
    def get_queryset(self):
        return NotificationChannel.objects.filter(is_active=True)


class NotificationTemplateListView(LoginRequiredMixin, ListView):
    """Lista de templates de notificação (para admins)"""
    model = NotificationTemplate
    template_name = 'notifications/template_list.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        return NotificationTemplate.objects.filter(is_active=True)


class NotificationTemplateCreateView(LoginRequiredMixin, CreateView):
    """Criar template de notificação"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications/template_form.html'
    success_url = reverse_lazy('notifications:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Template criado com sucesso!')
        return super().form_valid(form)


class NotificationTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Editar template de notificação"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications/template_form.html'
    success_url = reverse_lazy('notifications:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Template atualizado com sucesso!')
        return super().form_valid(form)


@login_required
def send_test_notification(request):
    """Envia notificação de teste"""
    if request.method == 'POST':
        try:
            # Criar notificação de teste
            notification = Notification.objects.create(
                recipient=request.user,
                title="Notificação de Teste",
                message="Esta é uma notificação de teste do sistema MoveMarias.",
                type='general',
                priority=2
            )
            
            # Enviar via canais configurados
            # notification.send_notification()
            
            messages.success(request, 'Notificação de teste enviada com sucesso!')
            return JsonResponse({'success': True})
            
        except Exception as e:
            messages.error(request, f'Erro ao enviar notificação: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


class NotificationSearchView(LoginRequiredMixin, View):
    """Busca de notificações"""
    
    def get(self, request):
        """Busca notificações por termo"""
        query = request.GET.get('q', '')
        
        if not query:
            return JsonResponse({'notifications': []})
        
        notifications = Notification.objects.filter(
            recipient=request.user
        ).filter(
            Q(title__icontains=query) | 
            Q(message__icontains=query)
        ).order_by('-created_at')[:10]
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                'category': notification.type,
                'is_read': notification.status == 'read',
                'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
                'url': '#'
            })
        
        return JsonResponse({'notifications': data})


@login_required
def notification_analytics(request):
    """Analytics de notificações para dashboard"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Estatísticas gerais
    total_notifications = Notification.objects.filter(recipient=request.user).count()
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        status='pending'
    ).count()
    
    # Notificações dos últimos 30 dias
    last_30_days = timezone.now() - timedelta(days=30)
    recent_notifications = Notification.objects.filter(
        recipient=request.user,
        created_at__gte=last_30_days
    ).count()
    
    # Notificações por categoria
    categories = Notification.objects.filter(
        recipient=request.user
    ).values('type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Notificações por prioridade
    priorities = Notification.objects.filter(
        recipient=request.user
    ).values('priority').annotate(
        count=Count('id')
    ).order_by('-count')
    
    data = {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
        'categories': list(categories),
        'priorities': list(priorities),
        'read_rate': round((total_notifications - unread_notifications) / total_notifications * 100, 2) if total_notifications > 0 else 0
    }
    
    return JsonResponse(data)


class NotificationExportView(LoginRequiredMixin, View):
    """Exportar notificações para CSV/JSON"""
    
    def get(self, request):
        """Exporta notificações do usuário"""
        import csv
        from django.http import HttpResponse
        
        format_type = request.GET.get('format', 'csv')
        
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="notifications.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Título', 'Mensagem', 'Categoria', 'Prioridade', 'Lida', 'Data de Criação', 'Data de Leitura'])
            
            for notification in notifications:
                writer.writerow([
                    notification.id,
                    notification.title,
                    notification.message,
                    notification.get_type_display(),
                    notification.get_priority_display(),
                    'Sim' if notification.status == 'read' else 'Não',
                    notification.created_at.strftime('%d/%m/%Y %H:%M'),
                    notification.read_at.strftime('%d/%m/%Y %H:%M') if notification.read_at else ''
                ])
            
            return response
        
        elif format_type == 'json':
            data = []
            for notification in notifications:
                data.append({
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'category': notification.type,
                    'priority': notification.priority,
                    'is_read': notification.status == 'read',
                    'created_at': notification.created_at.isoformat(),
                    'read_at': notification.read_at.isoformat() if notification.read_at else None
                })
            
            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = 'attachment; filename="notifications.json"'
            return response
        
        return JsonResponse({'error': 'Formato não suportado'}, status=400)


@login_required
@user_passes_test(lambda u: u.is_staff)
def create_test_notifications(request):
    """Cria notificações de teste para desenvolvimento"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Pegar o primeiro canal disponível
    channel = NotificationChannel.objects.first()
    if not channel:
        # Criar canal padrão se não existir
        channel = NotificationChannel.objects.create(
            name='web',
            display_name='Web',
            is_active=True
        )
    
    # Criar algumas notificações de teste
    test_notifications = [
        {
            'title': 'Bem-vindo ao Move Marias!',
            'message': 'Sua conta foi criada com sucesso. Explore todas as funcionalidades.',
            'type': 'welcome',
            'priority': 2
        },
        {
            'title': 'Novo Workshop Disponível',
            'message': 'O workshop "Empreendedorismo Feminino" está com inscrições abertas.',
            'type': 'workshop_enrollment',
            'priority': 3
        },
        {
            'title': 'Certificado Pronto',
            'message': 'Seu certificado do curso "Liderança Feminina" está pronto para download.',
            'type': 'certificate_ready',
            'priority': 2
        },
        {
            'title': 'Lembrete: Coaching Agendado',
            'message': 'Sua sessão de coaching está agendada para amanhã às 14:00.',
            'type': 'coaching_scheduled',
            'priority': 3
        }
    ]
    
    created_count = 0
    for notification_data in test_notifications:
        notification = Notification.objects.create(
            recipient=request.user,
            title=notification_data['title'],
            message=notification_data['message'],
            type=notification_data['type'],
            channel=channel,
            priority=notification_data['priority'],
            status='pending'
        )
        created_count += 1
    
    return JsonResponse({
        'success': True,
        'message': f'{created_count} notificações de teste criadas com sucesso!'
    })


class NotificationDeleteView(LoginRequiredMixin, DeleteView):
    """Excluir notificação"""
    model = Notification
    success_url = reverse_lazy('notifications:list')
    
    def get_queryset(self):
        """Apenas notificações do usuário atual ou staff"""
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Exclusão via AJAX ou redirect"""
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Verificar se o usuário tem permissão para excluir
        if not (self.request.user.is_staff or self.object.recipient == self.request.user):
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Você não tem permissão para excluir esta notificação'
                }, status=403)
            messages.error(request, 'Você não tem permissão para excluir esta notificação')
            return redirect(success_url)
        
        self.object.delete()
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Notificação excluída com sucesso'
            })
        
        messages.success(request, 'Notificação excluída com sucesso!')
        return redirect(success_url)


@login_required
@require_http_methods(["POST"])
def mark_as_important(request, notification_id):
    """Marca uma notificação como importante via AJAX"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            recipient=request.user
        )
        
        # Alterna o status de importância
        metadata = notification.metadata or {}
        is_important = not metadata.get('is_important', False)
        metadata['is_important'] = is_important
        notification.metadata = metadata
        notification.save()
        
        return JsonResponse({
            'success': True,
            'is_important': is_important,
            'message': 'Notificação marcada como importante' if is_important else 'Notificação desmarcada como importante'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_delete(request):
    """Exclusão em massa de notificações via AJAX"""
    try:
        notification_ids = request.POST.getlist('notification_ids')
        
        if not notification_ids:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma notificação selecionada'
            }, status=400)
        
        # Filtrar apenas notificações do usuário atual
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        )
        
        count = notifications.count()
        notifications.delete()
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'{count} notificações excluídas com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_mark_as_read(request):
    """Marca múltiplas notificações como lidas via AJAX"""
    try:
        notification_ids = request.POST.getlist('notification_ids')
        
        if not notification_ids:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma notificação selecionada'
            }, status=400)
        
        # Filtrar apenas notificações do usuário atual
        count = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
            status='pending'
        ).update(status='read', read_at=timezone.now())
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'{count} notificações marcadas como lidas'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)


@login_required
def notification_stats(request):
    """Estatísticas detalhadas de notificações"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    user_notifications = Notification.objects.filter(recipient=request.user)
    
    # Estatísticas por período
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        'total': user_notifications.count(),
        'unread': user_notifications.filter(status='pending').count(),
        'today': user_notifications.filter(created_at__date=today).count(),
        'week': user_notifications.filter(created_at__gte=week_ago).count(),
        'month': user_notifications.filter(created_at__gte=month_ago).count(),
    }
    
    # Estatísticas por categoria
    categories = user_notifications.values('type').annotate(
        count=Count('id'),
        unread=Count('id', filter=Q(status='pending'))
    ).order_by('-count')
    
    # Estatísticas por prioridade
    priorities = user_notifications.values('priority').annotate(
        count=Count('id'),
        unread=Count('id', filter=Q(status='pending'))
    ).order_by('-priority')
    
    # Notificações mais recentes
    recent_notifications = user_notifications.order_by('-created_at')[:10]
    
    data = {
        'stats': stats,
        'categories': list(categories),
        'priorities': list(priorities),
        'recent_notifications': [
            {
                'id': notif.id,
                'title': notif.title,
                'type': notif.type,
                'priority': notif.priority,
                'created_at': notif.created_at.strftime('%d/%m/%Y %H:%M'),
                'is_read': notif.status == 'read'
            }
            for notif in recent_notifications
        ]
    }
    
    return JsonResponse(data)
