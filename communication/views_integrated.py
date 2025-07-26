# ===================================
# MÓDULO DE COMUNICAÇÃO - VIEWS INTEGRADAS
# ===================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import (
    Announcement, InternalMemo, Newsletter, 
    CommunicationMessage, MessageResponse,
    CommunicationChannel, CommunicationTemplate, 
    CommunicationAnalytics, SuggestionBox
)
from .forms import (
    AnnouncementForm, InternalMemoForm, NewsletterForm,
    CommunicationMessageForm, PolicyForm, FeedbackForm,
    SurveyForm, LearningResourceForm
)

import json
from datetime import datetime, timedelta

User = get_user_model()

# ===================================
# DASHBOARD PRINCIPAL
# ===================================

@login_required
def communication_dashboard(request):
    """Dashboard principal de comunicação"""
    
    # Estatísticas gerais
    total_announcements = Announcement.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).count()
    
    total_messages = CommunicationMessage.objects.filter(
        is_active=True
    ).count()
    
    unread_messages = CommunicationMessage.objects.filter(
        recipients=request.user,
        read_by__ne=request.user
    ).count()
    
    # Comunicados recentes
    recent_announcements = Announcement.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:5]
    
    # Mensagens recentes
    recent_messages = CommunicationMessage.objects.filter(
        Q(recipients=request.user) | Q(author=request.user),
        is_active=True
    ).order_by('-created_at')[:10]
    
    # Newsletters ativas
    active_newsletters = Newsletter.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:3]
    
    # Políticas pendentes de leitura
    pending_policies = Policy.objects.filter(
        is_active=True,
        requires_acknowledgment=True
    ).exclude(
        acknowledgments__user=request.user
    )[:5]
    
    # Enquetes ativas
    active_surveys = Survey.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).exclude(
        responses__user=request.user
    )[:3]
    
    # Recursos de aprendizado recentes
    recent_resources = LearningResource.objects.filter(
        is_published=True
    ).order_by('-published_date')[:5]
    
    # Feedback pendente de resposta (para admins)
    pending_feedback = None
    if request.user.is_staff:
        pending_feedback = Feedback.objects.filter(
            status='pending'
        ).count()
    
    context = {
        'stats': {
            'total_announcements': total_announcements,
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'pending_feedback': pending_feedback,
        },
        'recent_announcements': recent_announcements,
        'recent_messages': recent_messages,
        'active_newsletters': active_newsletters,
        'pending_policies': pending_policies,
        'active_surveys': active_surveys,
        'recent_resources': recent_resources,
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
        is_published=True,
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
    """Criar novo comunicado"""
    
    if not (request.user.is_staff or request.user.has_perm('communication.add_announcement')):
        messages.error(request, 'Você não tem permissão para criar comunicados.')
        return redirect('communication:announcements_list')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            form.save_m2m()
            
            messages.success(request, 'Comunicado criado com sucesso!')
            return redirect('communication:announcement_detail', announcement_id=announcement.id)
    else:
        form = AnnouncementForm()
    
    context = {
        'form': form,
        'title': 'Criar Comunicado',
    }
    
    return render(request, 'communication/announcement_form.html', context)

@login_required
def edit_announcement(request, announcement_id):
    """Editar comunicado"""
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if not (request.user == announcement.author or request.user.is_staff):
        messages.error(request, 'Você não tem permissão para editar este comunicado.')
        return redirect('communication:announcement_detail', announcement_id=announcement.id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comunicado atualizado com sucesso!')
            return redirect('communication:announcement_detail', announcement_id=announcement.id)
    else:
        form = AnnouncementForm(instance=announcement)
    
    context = {
        'form': form,
        'announcement': announcement,
        'title': 'Editar Comunicado',
    }
    
    return render(request, 'communication/announcement_form.html', context)

@login_required
def delete_announcement(request, announcement_id):
    """Excluir comunicado"""
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if not (request.user == announcement.author or request.user.is_staff):
        messages.error(request, 'Você não tem permissão para excluir este comunicado.')
        return redirect('communication:announcement_detail', announcement_id=announcement.id)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Comunicado excluído com sucesso!')
        return redirect('communication:announcements_list')
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'communication/announcement_confirm_delete.html', context)

# ===================================
# MENSAGENS INTERNAS
# ===================================

@login_required
def messages_list(request):
    """Lista de mensagens do usuário"""
    
    # Filtros
    message_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    
    if message_type == 'sent':
        messages_qs = CommunicationMessage.objects.filter(
            author=request.user
        )
    elif message_type == 'received':
        messages_qs = CommunicationMessage.objects.filter(
            recipients=request.user
        )
    else:
        messages_qs = CommunicationMessage.objects.filter(
            Q(author=request.user) | Q(recipients=request.user)
        )
    
    if status == 'unread':
        messages_qs = messages_qs.exclude(read_by=request.user)
    elif status == 'read':
        messages_qs = messages_qs.filter(read_by=request.user)
    
    messages_qs = messages_qs.filter(is_active=True).order_by('-created_at')
    
    # Paginação
    paginator = Paginator(messages_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_type': message_type,
        'current_status': status,
    }
    
    return render(request, 'communication/messages_list.html', context)

@login_required
def message_detail(request, message_id):
    """Detalhes da mensagem"""
    
    message = get_object_or_404(
        CommunicationMessage,
        id=message_id,
        is_active=True
    )
    
    # Verificar permissão
    if not (request.user == message.author or 
            message.recipients.filter(id=request.user.id).exists()):
        messages.error(request, 'Você não tem acesso a esta mensagem.')
        return redirect('communication:messages_list')
    
    # Marcar como lida
    message.read_by.add(request.user)
    
    # Respostas
    responses = message.responses.filter(is_active=True).order_by('created_at')
    
    context = {
        'message': message,
        'responses': responses,
        'can_reply': message.allow_replies,
        'can_edit': request.user == message.author,
    }
    
    return render(request, 'communication/message_detail.html', context)

@login_required
def create_message(request):
    """Criar nova mensagem"""
    
    if request.method == 'POST':
        form = CommunicationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.save()
            form.save_m2m()
            
            messages.success(request, 'Mensagem enviada com sucesso!')
            return redirect('communication:message_detail', message_id=message.id)
    else:
        form = CommunicationMessageForm()
    
    context = {
        'form': form,
        'title': 'Nova Mensagem',
    }
    
    return render(request, 'communication/message_form.html', context)

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
    
    # Marcar como lida
    newsletter.read_by.add(request.user)
    
    context = {
        'newsletter': newsletter,
        'can_edit': request.user == newsletter.author or request.user.is_staff,
    }
    
    return render(request, 'communication/newsletter_detail.html', context)

# ===================================
# POLÍTICAS
# ===================================

@login_required
def policies_list(request):
    """Lista de políticas"""
    
    policies = Policy.objects.filter(is_active=True)
    
    # Separar por status de leitura
    read_policies = policies.filter(acknowledgments__user=request.user)
    unread_policies = policies.exclude(acknowledgments__user=request.user)
    
    context = {
        'read_policies': read_policies,
        'unread_policies': unread_policies,
    }
    
    return render(request, 'communication/policies_list.html', context)

@login_required
def policy_detail(request, policy_id):
    """Detalhes da política"""
    
    policy = get_object_or_404(Policy, id=policy_id, is_active=True)
    
    # Verificar se já foi lida
    has_acknowledged = policy.acknowledgments.filter(user=request.user).exists()
    
    context = {
        'policy': policy,
        'has_acknowledged': has_acknowledged,
    }
    
    return render(request, 'communication/policy_detail.html', context)

# ===================================
# FEEDBACK
# ===================================

@login_required
def feedback_list(request):
    """Lista de feedback"""
    
    if request.user.is_staff:
        # Admins veem todo feedback
        feedback_qs = Feedback.objects.all()
    else:
        # Usuários veem apenas seu próprio feedback
        feedback_qs = Feedback.objects.filter(user=request.user)
    
    feedback_qs = feedback_qs.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(feedback_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'is_admin': request.user.is_staff,
    }
    
    return render(request, 'communication/feedback_list.html', context)

@login_required
def create_feedback(request):
    """Criar novo feedback"""
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            
            messages.success(request, 'Feedback enviado com sucesso!')
            return redirect('communication:feedback_list')
    else:
        form = FeedbackForm()
    
    context = {
        'form': form,
        'title': 'Enviar Feedback',
    }
    
    return render(request, 'communication/feedback_form.html', context)

# ===================================
# ENQUETES
# ===================================

@login_required
def surveys_list(request):
    """Lista de enquetes"""
    
    # Enquetes ativas
    active_surveys = Survey.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    
    # Enquetes respondidas pelo usuário
    answered_surveys = Survey.objects.filter(
        responses__user=request.user
    ).distinct()
    
    # Enquetes finalizadas
    finished_surveys = Survey.objects.filter(
        is_active=True,
        end_date__lt=timezone.now()
    )
    
    context = {
        'active_surveys': active_surveys,
        'answered_surveys': answered_surveys,
        'finished_surveys': finished_surveys,
    }
    
    return render(request, 'communication/surveys_list.html', context)

@login_required
def survey_detail(request, survey_id):
    """Detalhes da enquete"""
    
    survey = get_object_or_404(Survey, id=survey_id, is_active=True)
    
    # Verificar se já respondeu
    has_responded = survey.responses.filter(user=request.user).exists()
    
    # Verificar se está no período ativo
    is_active = (survey.start_date <= timezone.now() <= survey.end_date)
    
    context = {
        'survey': survey,
        'has_responded': has_responded,
        'is_active': is_active,
        'questions': survey.questions.filter(is_active=True).order_by('order'),
    }
    
    return render(request, 'communication/survey_detail.html', context)

# ===================================
# RECURSOS DE APRENDIZADO
# ===================================

@login_required
def resources_list(request):
    """Lista de recursos de aprendizado"""
    
    # Filtros
    category = request.GET.get('category')
    resource_type = request.GET.get('type')
    search = request.GET.get('search')
    
    resources = LearningResource.objects.filter(is_published=True)
    
    if category:
        resources = resources.filter(category=category)
    
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    
    if search:
        resources = resources.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    resources = resources.order_by('-published_date')
    
    # Paginação
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': LearningResource.CATEGORY_CHOICES,
        'resource_types': LearningResource.RESOURCE_TYPES,
        'current_category': category,
        'current_type': resource_type,
        'current_search': search,
    }
    
    return render(request, 'communication/resources_list.html', context)

@login_required
def resource_detail(request, resource_id):
    """Detalhes do recurso"""
    
    resource = get_object_or_404(
        LearningResource,
        id=resource_id,
        is_published=True
    )
    
    # Incrementar visualizações
    resource.views_count += 1
    resource.save(update_fields=['views_count'])
    
    context = {
        'resource': resource,
        'can_edit': request.user == resource.author or request.user.is_staff,
    }
    
    return render(request, 'communication/resource_detail.html', context)

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
    active_surveys = Survey.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()
    
    # Comunicados por categoria
    announcements_by_category = Announcement.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Engajamento por mês
    current_month = timezone.now().replace(day=1)
    
    context = {
        'stats': {
            'total_announcements': total_announcements,
            'total_messages': total_messages,
            'total_newsletters': total_newsletters,
            'active_surveys': active_surveys,
        },
        'announcements_by_category': announcements_by_category,
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
            'published': Announcement.objects.filter(is_published=True).count(),
            'this_month': Announcement.objects.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
        },
        'messages': {
            'total': CommunicationMessage.objects.count(),
            'active': CommunicationMessage.objects.filter(is_active=True).count(),
            'this_week': CommunicationMessage.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        },
        'engagement': {
            'read_rate': 85.5,  # Calcular taxa de leitura real
            'response_rate': 42.3,  # Calcular taxa de resposta real
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
        is_published=True
    )[:5]
    
    for announcement in announcements:
        results.append({
            'type': 'announcement',
            'title': announcement.title,
            'url': f'/communication/announcements/{announcement.id}/',
            'excerpt': announcement.summary or announcement.content[:150]
        })
    
    # Buscar em mensagens
    messages_qs = CommunicationMessage.objects.filter(
        Q(subject__icontains=query) | Q(content__icontains=query),
        is_active=True,
        recipients=request.user
    )[:5]
    
    for message in messages_qs:
        results.append({
            'type': 'message',
            'title': message.subject,
            'url': f'/communication/messages/{message.id}/',
            'excerpt': message.content[:150]
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
    message.read_by.add(request.user)
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def acknowledge_policy(request, policy_id):
    """Confirmar leitura de política"""
    
    policy = get_object_or_404(Policy, id=policy_id, is_active=True)
    
    # Criar ou atualizar confirmação
    from .models import PolicyAcknowledgment
    acknowledgment, created = PolicyAcknowledgment.objects.get_or_create(
        user=request.user,
        policy=policy,
        defaults={'acknowledged_at': timezone.now()}
    )
    
    return JsonResponse({'success': True, 'created': created})
