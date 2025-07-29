# ===================================
# MÓDULO DE COMUNICAÇÃO - VIEWS SIMPLES
# ===================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from .models import (
    Announcement, InternalMemo, Newsletter, 
    CommunicationMessage, CommunicationAnalytics, SuggestionBox
)

User = get_user_model()

# ===================================
# DASHBOARD PRINCIPAL
# ===================================

@login_required
def communication_dashboard(request):
    """Dashboard principal de comunicação"""
    
    # Estatísticas gerais  
    total_announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    ).count()
    
    total_messages = CommunicationMessage.objects.filter(
        status='published'
    ).count()
    
    # Comunicados recentes
    recent_announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:5]
    
    # Mensagens recentes
    recent_messages = CommunicationMessage.objects.filter(
        status='published'
    ).order_by('-created_at')[:10]
    
    # Newsletters ativas
    active_newsletters = Newsletter.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:3]
    
    context = {
        'stats': {
            'total_announcements': total_announcements,
            'total_messages': total_messages,
            'unread_messages': 0,  # Placeholder
            'pending_feedback': None,
        },
        'recent_announcements': recent_announcements,
        'recent_messages': recent_messages,
        'active_newsletters': active_newsletters,
        'pending_policies': [],  # Placeholder
        'active_surveys': [],  # Placeholder
        'recent_resources': [],  # Placeholder
    }
    
    return render(request, 'communication/dashboard.html', context)

# ===================================
# COMUNICADOS (ANNOUNCEMENTS)
# ===================================

@login_required
def announcements_list(request):
    """Lista de comunicados"""
    
    # Filtros
    category = request.GET.get('category')
    priority = request.GET.get('priority') 
    search = request.GET.get('search')
    
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    )
    
    if category:
        announcements = announcements.filter(category=category)
    
    if priority:
        announcements = announcements.filter(priority=priority)
        
    if search:
        announcements = announcements.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(summary__icontains=search)
        )
    
    announcements = announcements.order_by('-publish_date')
    
    # Paginação
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Announcement.CATEGORY_CHOICES,
        'priorities': Announcement.PRIORITY_CHOICES,
        'current_category': category,
        'current_priority': priority,
        'current_search': search,
    }
    
    return render(request, 'communication/announcements_list.html', context)

@login_required
def announcement_detail(request, announcement_id):
    """Detalhes do comunicado"""
    
    announcement = get_object_or_404(
        Announcement, 
        id=announcement_id,
        is_published=True,
        publish_date__lte=timezone.now()
    )
    
    # Marcar como lido
    announcement.read_by.add(request.user)
    
    context = {
        'announcement': announcement,
        'can_edit': request.user == announcement.author or request.user.is_staff,
    }
    
    return render(request, 'communication/announcement_detail.html', context)

@login_required
def create_announcement(request):
    """Criar novo comunicado - placeholder"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('communication:announcements_list')

@login_required
def edit_announcement(request, announcement_id):
    """Editar comunicado - placeholder"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('communication:announcement_detail', announcement_id=announcement_id)

@login_required 
def delete_announcement(request, announcement_id):
    """Excluir comunicado - placeholder"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('communication:announcement_detail', announcement_id=announcement_id)

# ===================================
# MENSAGENS INTERNAS
# ===================================

@login_required
def messages_list(request):
    """Lista de mensagens do usuário"""
    
    messages_qs = CommunicationMessage.objects.filter(
        status='published'
    ).order_by('-created_at')
    
    # Paginação
    paginator = Paginator(messages_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_type': 'all',
        'current_status': 'all',
    }
    
    return render(request, 'communication/messages_list.html', context)

@login_required
def message_detail(request, message_id):
    """Detalhes da mensagem"""
    
    message = get_object_or_404(
        CommunicationMessage,
        id=message_id,
        status='published'
    )
    
    context = {
        'message': message,
        'responses': [],
        'can_reply': False,
        'can_edit': request.user == message.author,
    }
    
    return render(request, 'communication/message_detail.html', context)

@login_required
def create_message(request):
    """Criar nova mensagem - placeholder"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('communication:messages_list')

# ===================================
# NEWSLETTERS
# ===================================

@login_required
def newsletters_list(request):
    """Lista de newsletters"""
    
    newsletters = Newsletter.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')
    
    # Paginação
    paginator = Paginator(newsletters, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'communication/newsletters_list.html', context)

@login_required
def newsletter_detail(request, newsletter_id):
    """Detalhes da newsletter"""
    
    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        is_published=True,
        publish_date__lte=timezone.now()
    )
    
    context = {
        'newsletter': newsletter,
        'can_edit': request.user == newsletter.author or request.user.is_staff,
    }
    
    return render(request, 'communication/newsletter_detail.html', context)

# ===================================
# PLACEHOLDERS PARA OUTRAS FUNCIONALIDADES
# ===================================

@login_required
def policies_list(request):
    """Lista de políticas - placeholder"""
    context = {
        'read_policies': [],
        'unread_policies': [],
    }
    return render(request, 'communication/policies_list.html', context)

@login_required
def policy_detail(request, policy_id):
    """Detalhes da política - placeholder"""
    return HttpResponse("Política não encontrada", status=404)

@login_required
def feedback_list(request):
    """Lista de feedback - placeholder"""
    context = {
        'page_obj': None,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'communication/feedback_list.html', context)

@login_required
def create_feedback(request):
    """Criar novo feedback - placeholder"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('communication:dashboard')

@login_required
def surveys_list(request):
    """Lista de enquetes - placeholder"""
    context = {
        'active_surveys': [],
        'answered_surveys': [],
        'finished_surveys': [],
    }
    return render(request, 'communication/surveys_list.html', context)

@login_required
def survey_detail(request, survey_id):
    """Detalhes da enquete - placeholder"""
    return HttpResponse("Enquete não encontrada", status=404)

@login_required
def resources_list(request):
    """Lista de recursos - placeholder"""
    context = {
        'page_obj': None,
        'categories': [],
        'resource_types': [],
        'current_category': None,
        'current_type': None,
        'current_search': None,
    }
    return render(request, 'communication/resources_list.html', context)

@login_required
def resource_detail(request, resource_id):
    """Detalhes do recurso - placeholder"""
    return HttpResponse("Recurso não encontrado", status=404)

# ===================================
# ANALYTICS E RELATÓRIOS
# ===================================

@login_required
def communication_analytics(request):
    """Analytics de comunicação"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('communication:dashboard')
    
    # Estatísticas gerais
    total_announcements = Announcement.objects.count()
    total_messages = CommunicationMessage.objects.count()
    total_newsletters = Newsletter.objects.count()
    
    context = {
        'stats': {
            'total_announcements': total_announcements,
            'total_messages': total_messages,
            'total_newsletters': total_newsletters,
            'active_surveys': 0,
        },
        'announcements_by_category': [],
    }
    
    return render(request, 'communication/analytics.html', context)

# ===================================
# APIs
# ===================================

@login_required
@require_http_methods(["GET"])
def metrics_api(request):
    """API de métricas"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    metrics = {
        'announcements': {
            'total': Announcement.objects.count(),
            'published': Announcement.objects.filter(is_active=True).count(),
            'this_month': Announcement.objects.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
        },
        'messages': {
            'total': CommunicationMessage.objects.count(),
            'active': CommunicationMessage.objects.filter(status='published').count(),
            'this_week': CommunicationMessage.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        },
        'engagement': {
            'read_rate': 85.5,
            'response_rate': 42.3,
        }
    }
    
    return JsonResponse(metrics)

@login_required
@require_http_methods(["GET"])
def search_api(request):
    """API de busca"""
    
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    results = []
    
    # Buscar em comunicados
    announcements = Announcement.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query),
        is_active=True
    )[:5]
    
    for announcement in announcements:
        results.append({
            'type': 'announcement',
            'title': announcement.title,
            'url': f'/communication/announcements/{announcement.id}/',
            'excerpt': announcement.summary or announcement.content[:150]
        })
    
    return JsonResponse({'results': results})

# ===================================
# VIEWS AUXILIARES
# ===================================

@login_required
@require_http_methods(["POST"])
def mark_message_read(request, message_id):
    """Marcar mensagem como lida"""
    
    message = get_object_or_404(CommunicationMessage, id=message_id)
    # Lógica para marcar como lida seria implementada aqui
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def acknowledge_policy(request, policy_id):
    """Confirmar leitura de política - placeholder"""
    return JsonResponse({'success': True, 'created': False})

@login_required
def communication_settings(request):
    """Configurações do módulo de comunicação"""
    context = {
        'title': 'Configurações - Comunicação',
        'user': request.user,
    }
    return render(request, 'communication/settings.html', context)

@login_required
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API simplificada de estatísticas para o dashboard"""
    
    # Estatísticas básicas acessíveis a todos os usuários logados
    stats = {
        'announcements': {
            'published': Announcement.objects.filter(
                is_active=True,
                publish_date__lte=timezone.now()
            ).count(),
        },
        'messages': {
            'active': CommunicationMessage.objects.filter(status='published').count(),
        },
        'engagement': {
            'read_rate': 85.5,  # Placeholder
        }
    }
    
    return JsonResponse(stats)
