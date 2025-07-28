from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models_refactored import (
    CommunicationMessage, MessageRecipient, MessageResponse, 
    MessageAttachment, CommunicationPreferences
)
from .forms_refactored import (
    CommunicationMessageForm, MessageResponseForm, 
    CommunicationPreferencesForm
)
import json
from datetime import datetime, timedelta

User = get_user_model()

@login_required
@cache_page(60 * 5)  # Cache por 5 minutos
def communication_dashboard(request):
    """Dashboard unificado de comunicação"""
    
    # Buscar mensagens para o usuário atual
    user_messages = CommunicationMessage.objects.filter(
        recipients__user=request.user,
        status='published',
        publish_date__lte=timezone.now()
    ).select_related('author').prefetch_related('recipients', 'attachments')
    
    # Estatísticas gerais
    stats = {
        'total_messages': user_messages.count(),
        'unread_messages': user_messages.filter(recipients__is_read=False).count(),
        'urgent_messages': user_messages.filter(priority='urgent').count(),
        'pending_responses': user_messages.filter(
            requires_response=True,
            responses__user__ne=request.user
        ).count(),
    }
    
    # Mensagens recentes por tipo
    recent_messages = {}
    for msg_type, display_name in CommunicationMessage.MESSAGE_TYPES:
        recent_messages[msg_type] = user_messages.filter(
            message_type=msg_type
        ).order_by('-publish_date')[:5]
    
    # Mensagens não lidas
    unread_messages = user_messages.filter(
        recipients__is_read=False
    ).order_by('-publish_date')[:10]
    
    # Mensagens urgentes
    urgent_messages = user_messages.filter(
        priority='urgent',
        recipients__is_read=False
    ).order_by('-publish_date')[:5]
    
    # Métricas de engajamento (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    engagement_metrics = user_messages.filter(
        publish_date__gte=thirty_days_ago
    ).aggregate(
        avg_engagement=Avg('engagement_score'),
        total_responses=Count('responses'),
        avg_read_time=Avg('view_count')
    )
    
    # Atividade recente
    recent_activity = []
    
    # Mensagens lidas recentemente
    recent_reads = MessageRecipient.objects.filter(
        user=request.user,
        read_at__isnull=False
    ).select_related('message').order_by('-read_at')[:5]
    
    for read in recent_reads:
        recent_activity.append({
            'type': 'read',
            'message': read.message,
            'timestamp': read.read_at,
            'description': f'Leu: {read.message.title}'
        })
    
    # Respostas recentes
    recent_responses = MessageResponse.objects.filter(
        user=request.user
    ).select_related('message').order_by('-created_at')[:5]
    
    for response in recent_responses:
        recent_activity.append({
            'type': 'response',
            'message': response.message,
            'timestamp': response.created_at,
            'description': f'Respondeu: {response.message.title}'
        })
    
    # Ordenar atividade por timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]
    
    context = {
        'stats': stats,
        'recent_messages': recent_messages,
        'unread_messages': unread_messages,
        'urgent_messages': urgent_messages,
        'engagement_metrics': engagement_metrics,
        'recent_activity': recent_activity,
        'message_types': CommunicationMessage.MESSAGE_TYPES,
    }
    
    return render(request, 'communication/dashboard_unified.html', context)


@login_required
def messages_list(request):
    """Lista unificada de mensagens com filtros avançados"""
    
    # Buscar mensagens para o usuário
    messages = CommunicationMessage.objects.filter(
        recipients__user=request.user,
        status='published'
    ).select_related('author').prefetch_related('recipients', 'attachments')
    
    # Filtros
    message_type = request.GET.get('type')
    if message_type:
        messages = messages.filter(message_type=message_type)
    
    priority = request.GET.get('priority')
    if priority:
        messages = messages.filter(priority=priority)
    
    category = request.GET.get('category')
    if category:
        messages = messages.filter(category=category)
    
    read_status = request.GET.get('read_status')
    if read_status == 'unread':
        messages = messages.filter(recipients__is_read=False)
    elif read_status == 'read':
        messages = messages.filter(recipients__is_read=True)
    
    requires_response = request.GET.get('requires_response')
    if requires_response == 'true':
        messages = messages.filter(requires_response=True)
    
    # Busca por texto
    search = request.GET.get('search')
    if search:
        messages = messages.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search) |
            Q(author__first_name__icontains=search) |
            Q(author__last_name__icontains=search)
        )
    
    # Ordenação
    order_by = request.GET.get('order_by', '-publish_date')
    if order_by in ['publish_date', '-publish_date', 'title', '-title', 'priority', '-priority']:
        messages = messages.order_by(order_by)
    
    # Paginação
    paginator = Paginator(messages, 20)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    
    # Marcar como visualizadas
    for message in messages_page:
        message.view_count += 1
        message.save(update_fields=['view_count'])
    
    context = {
        'messages': messages_page,
        'message_types': CommunicationMessage.MESSAGE_TYPES,
        'priority_choices': CommunicationMessage.PRIORITY_CHOICES,
        'category_choices': CommunicationMessage.CATEGORY_CHOICES,
        'filters': {
            'type': message_type,
            'priority': priority,
            'category': category,
            'read_status': read_status,
            'requires_response': requires_response,
            'search': search,
            'order_by': order_by,
        }
    }
    
    return render(request, 'communication/messages_list.html', context)


@login_required
def message_detail(request, message_id):
    """Detalhes de uma mensagem específica"""
    
    message = get_object_or_404(
        CommunicationMessage,
        id=message_id,
        recipients__user=request.user,
        status='published'
    )
    
    # Buscar recipient específico para o usuário
    recipient = get_object_or_404(
        MessageRecipient,
        message=message,
        user=request.user
    )
    
    # Marcar como lida
    if not recipient.is_read:
        recipient.mark_as_read()
    
    # Processar resposta
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'respond':
            form = MessageResponseForm(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.message = message
                response.user = request.user
                response.save()
                messages.success(request, 'Resposta enviada com sucesso!')
                return redirect('communication:message_detail', message_id=message_id)
        
        elif action == 'acknowledge' and message.requires_acknowledgment:
            recipient.acknowledge()
            messages.success(request, 'Confirmação de leitura registrada!')
            return redirect('communication:message_detail', message_id=message_id)
    
    else:
        form = MessageResponseForm() if message.requires_response else None
    
    # Buscar respostas
    responses = message.responses.select_related('user').order_by('created_at')
    
    # Verificar se usuário já respondeu
    user_response = responses.filter(user=request.user).first()
    
    context = {
        'message': message,
        'recipient': recipient,
        'responses': responses,
        'user_response': user_response,
        'form': form,
    }
    
    return render(request, 'communication/message_detail.html', context)


@login_required
def create_message(request):
    """Criar nova mensagem (apenas para staff)"""
    
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para criar mensagens.')
        return redirect('communication:dashboard')
    
    if request.method == 'POST':
        form = CommunicationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.save()
            
            # Processar destinatários
            recipients_data = json.loads(request.POST.get('recipients_data', '[]'))
            for recipient_data in recipients_data:
                MessageRecipient.objects.create(
                    message=message,
                    recipient_type=recipient_data['type'],
                    user_id=recipient_data.get('user_id'),
                    department_id=recipient_data.get('department_id')
                )
            
            # Processar anexos
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    file=attachment,
                    name=attachment.name
                )
            
            messages.success(request, 'Mensagem criada com sucesso!')
            return redirect('communication:message_detail', message_id=message.id)
    
    else:
        form = CommunicationMessageForm()
    
    # Buscar usuários e departamentos para seleção
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    departments = []  # Implementar busca de departamentos conforme modelo HR
    
    context = {
        'form': form,
        'users': users,
        'departments': departments,
    }
    
    return render(request, 'communication/message_create.html', context)


@login_required
def preferences_view(request):
    """Configurações de preferências de comunicação"""
    
    preferences, created = CommunicationPreferences.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = CommunicationPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferências atualizadas com sucesso!')
            return redirect('communication:preferences')
    else:
        form = CommunicationPreferencesForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    
    return render(request, 'communication/preferences.html', context)


# APIs para AJAX
@login_required
@require_http_methods(["GET"])
def api_messages_stats(request):
    """API para estatísticas de mensagens"""
    
    # Calcular estatísticas
    user_messages = CommunicationMessage.objects.filter(
        recipients__user=request.user,
        status='published'
    )
    
    stats = {
        'total': user_messages.count(),
        'unread': user_messages.filter(recipients__is_read=False).count(),
        'urgent': user_messages.filter(priority='urgent').count(),
        'pending_responses': user_messages.filter(
            requires_response=True
        ).exclude(responses__user=request.user).count(),
    }
    
    # Estatísticas por tipo
    by_type = {}
    for msg_type, display_name in CommunicationMessage.MESSAGE_TYPES:
        by_type[msg_type] = {
            'name': display_name,
            'count': user_messages.filter(message_type=msg_type).count(),
            'unread': user_messages.filter(
                message_type=msg_type,
                recipients__is_read=False
            ).count()
        }
    
    return JsonResponse({
        'stats': stats,
        'by_type': by_type,
    })


@login_required
@require_http_methods(["POST"])
def api_mark_as_read(request):
    """API para marcar mensagens como lidas"""
    
    data = json.loads(request.body)
    message_ids = data.get('message_ids', [])
    
    recipients = MessageRecipient.objects.filter(
        message_id__in=message_ids,
        user=request.user,
        is_read=False
    )
    
    count = 0
    for recipient in recipients:
        recipient.mark_as_read()
        count += 1
    
    return JsonResponse({
        'success': True,
        'marked_count': count,
        'message': f'{count} mensagens marcadas como lidas'
    })


@login_required
@require_http_methods(["POST"])
def api_bulk_actions(request):
    """API para ações em lote"""
    
    data = json.loads(request.body)
    action = data.get('action')
    message_ids = data.get('message_ids', [])
    
    if action == 'mark_read':
        recipients = MessageRecipient.objects.filter(
            message_id__in=message_ids,
            user=request.user,
            is_read=False
        )
        count = 0
        for recipient in recipients:
            recipient.mark_as_read()
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'{count} mensagens marcadas como lidas'
        })
    
    elif action == 'archive':
        # Implementar lógica de arquivamento
        return JsonResponse({
            'success': True,
            'message': 'Mensagens arquivadas com sucesso'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Ação inválida'
    })


@login_required
def analytics_dashboard(request):
    """Dashboard de analytics para gestores"""
    
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar este dashboard.')
        return redirect('communication:dashboard')
    
    # Métricas gerais
    total_messages = CommunicationMessage.objects.filter(status='published').count()
    total_recipients = MessageRecipient.objects.count()
    total_reads = MessageRecipient.objects.filter(is_read=True).count()
    avg_engagement = CommunicationMessage.objects.aggregate(
        avg_engagement=Avg('engagement_score')
    )['avg_engagement'] or 0
    
    # Métricas por período (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_messages = CommunicationMessage.objects.filter(
        publish_date__gte=thirty_days_ago,
        status='published'
    )
    
    # Engajamento por tipo de mensagem
    engagement_by_type = {}
    for msg_type, display_name in CommunicationMessage.MESSAGE_TYPES:
        messages_of_type = recent_messages.filter(message_type=msg_type)
        engagement_by_type[msg_type] = {
            'name': display_name,
            'count': messages_of_type.count(),
            'avg_engagement': messages_of_type.aggregate(
                avg=Avg('engagement_score')
            )['avg'] or 0,
            'read_rate': messages_of_type.aggregate(
                rate=Avg('read_count')
            )['rate'] or 0
        }
    
    # Top mensagens por engajamento
    top_messages = recent_messages.order_by('-engagement_score')[:10]
    
    # Usuários mais ativos
    most_active_users = User.objects.annotate(
        response_count=Count('message_responses')
    ).filter(
        message_responses__created_at__gte=thirty_days_ago
    ).order_by('-response_count')[:10]
    
    context = {
        'total_messages': total_messages,
        'total_recipients': total_recipients,
        'total_reads': total_reads,
        'read_rate': (total_reads / total_recipients * 100) if total_recipients > 0 else 0,
        'avg_engagement': avg_engagement,
        'engagement_by_type': engagement_by_type,
        'top_messages': top_messages,
        'most_active_users': most_active_users,
    }
    
    return render(request, 'communication/analytics_dashboard.html', context)
