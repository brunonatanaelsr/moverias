from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    Announcement, AnnouncementReadReceipt, InternalMemo, MemoResponse,
    Newsletter, SuggestionBox, CommunicationSettings
)
from .forms import (
    AnnouncementForm, InternalMemoForm, MemoResponseForm,
    NewsletterForm, SuggestionBoxForm, CommunicationSettingsForm
)


@login_required
def communication_dashboard(request):
    """Dashboard principal da comunicação"""
    # Comunicados recentes
    recent_announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:5]
    
    # Memorandos recentes
    recent_memos = InternalMemo.objects.filter(
        Q(to_users=request.user) | Q(to_departments__employees__user=request.user)
    ).distinct().order_by('-created_at')[:5]
    
    # Sugestões recentes
    recent_suggestions = SuggestionBox.objects.filter(
        status='open'
    ).order_by('-created_at')[:6]
    
    # Sugestões pendentes (se for admin)
    pending_suggestions = None
    if request.user.is_staff:
        pending_suggestions = SuggestionBox.objects.filter(
            status='open'
        ).order_by('-created_at')[:5]
    
    # Estatísticas
    stats = {
        'total_announcements': Announcement.objects.filter(is_active=True).count(),
        'unread_announcements': get_unread_announcements_count(request.user),
        'total_memos': InternalMemo.objects.filter(
            Q(to_users=request.user) | Q(to_departments__employees__user=request.user)
        ).distinct().count(),
        'total_suggestions': SuggestionBox.objects.count(),
        'pending_responses': InternalMemo.objects.filter(
            Q(to_users=request.user) | Q(to_departments__employees__user=request.user),
            requires_response=True
        ).exclude(
            responses__user=request.user
        ).distinct().count(),
    }
    
    # Combina anúncios e memorandos em uma única lista ordenada por data
    recent_messages = []
    for announcement in recent_announcements:
        recent_messages.append({
            'id': announcement.id,
            'type': 'announcement',
            'subject': announcement.title,
            'recipient': 'Todos',
            'status': 'sent',
            'created_at': announcement.created_at
        })
    for memo in recent_memos:
        recent_messages.append({
            'id': memo.id,
            'type': 'memo',
            'subject': memo.subject,
            'recipient': memo.to_departments.first().name if memo.to_departments.exists() else 'Privado',
            'status': 'pending' if memo.requires_response else 'sent',
            'created_at': memo.created_at
        })
    
    # Ordena por data de criação, mais recentes primeiro
    recent_messages.sort(key=lambda x: x['created_at'], reverse=True)
    
    context = {
        'recent_messages': recent_messages,
        'total_messages': stats['total_announcements'] + stats['total_memos'],
        'messages_sent': stats['total_announcements'] + (stats['total_memos'] - stats['pending_responses']),
        'pending_messages': stats['pending_responses'],
    }
    
    return render(request, 'communication/dashboard.html', context)


@login_required
def announcement_list(request):
    """Lista de comunicados"""
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    )
    
    # Filtrar por categoria
    category = request.GET.get('category')
    if category:
        announcements = announcements.filter(category=category)
    
    # Filtrar por prioridade
    priority = request.GET.get('priority')
    if priority:
        announcements = announcements.filter(priority=priority)
    
    # Busca
    search = request.GET.get('search')
    if search:
        announcements = announcements.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )
    
    # Ordenar por data de publicação
    announcements = announcements.order_by('-publish_date')
    
    # Paginação
    paginator = Paginator(announcements, 10)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)
    
    # Marcar como lidos
    for announcement in announcements:
        AnnouncementReadReceipt.objects.get_or_create(
            announcement=announcement,
            user=request.user
        )
    
    context = {
        'announcements': announcements,
        'categories': Announcement.CATEGORY_CHOICES,
        'priorities': Announcement.PRIORITY_CHOICES,
        'current_category': category,
        'current_priority': priority,
        'search': search,
    }
    
    return render(request, 'communication/announcement_list.html', context)


@login_required
def announcement_detail(request, pk):
    """Detalhes do comunicado"""
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    
    # Marcar como lido
    read_receipt, created = AnnouncementReadReceipt.objects.get_or_create(
        announcement=announcement,
        user=request.user
    )
    
    # Confirmar leitura se necessário
    if request.method == 'POST' and announcement.requires_acknowledgment:
        read_receipt.acknowledge()
        messages.success(request, 'Leitura confirmada com sucesso!')
        return redirect('communication:announcement_detail', pk=pk)
    
    context = {
        'announcement': announcement,
        'read_receipt': read_receipt,
    }
    
    return render(request, 'communication/announcement_detail.html', context)


@login_required
def memo_list(request):
    """Lista de memorandos"""
    memos = InternalMemo.objects.filter(
        Q(to_users=request.user) | Q(to_departments__employees__user=request.user)
    ).distinct()
    
    # Filtrar por tipo
    memo_type = request.GET.get('type')
    if memo_type:
        memos = memos.filter(memo_type=memo_type)
    
    # Filtrar por status de resposta
    requires_response = request.GET.get('requires_response')
    if requires_response == 'true':
        memos = memos.filter(requires_response=True)
    elif requires_response == 'false':
        memos = memos.filter(requires_response=False)
    
    # Busca
    search = request.GET.get('search')
    if search:
        memos = memos.filter(
            Q(subject__icontains=search) | Q(content__icontains=search)
        )
    
    # Ordenar por data
    memos = memos.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(memos, 10)
    page = request.GET.get('page')
    memos = paginator.get_page(page)
    
    context = {
        'memos': memos,
        'memo_types': InternalMemo.MEMO_TYPES,
        'current_type': memo_type,
        'requires_response': requires_response,
        'search': search,
        'today': timezone.now().date(),
    }
    
    return render(request, 'communication/memo_list.html', context)


@login_required
def memo_detail(request, pk):
    """Detalhes do memorando"""
    memo = get_object_or_404(InternalMemo, pk=pk)
    
    # Verificar se o usuário pode ler
    if not memo.user_can_read(request.user):
        messages.error(request, 'Você não tem permissão para acessar este memorando.')
        return redirect('communication:memo_list')
    
    # Processar resposta
    if request.method == 'POST':
        form = MemoResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.memo = memo
            response.user = request.user
            response.save()
            messages.success(request, 'Resposta enviada com sucesso!')
            return redirect('communication:memo_detail', pk=pk)
    else:
        form = MemoResponseForm()
    
    # Verificar se já respondeu
    user_response = memo.responses.filter(user=request.user).first()
    
    context = {
        'memo': memo,
        'form': form,
        'user_response': user_response,
        'responses': memo.responses.all(),
    }
    
    return render(request, 'communication/memo_detail.html', context)


@login_required
def suggestion_list(request):
    """Lista de sugestões"""
    suggestions = SuggestionBox.objects.all()
    
    # Filtrar por tipo
    suggestion_type = request.GET.get('type')
    if suggestion_type:
        suggestions = suggestions.filter(suggestion_type=suggestion_type)
    
    # Filtrar por status
    status = request.GET.get('status')
    if status:
        suggestions = suggestions.filter(status=status)
    
    # Busca
    search = request.GET.get('search')
    if search:
        suggestions = suggestions.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(suggestions, 10)
    page = request.GET.get('page')
    suggestions = paginator.get_page(page)
    
    context = {
        'suggestions': suggestions,
        'suggestion_types': SuggestionBox.SUGGESTION_TYPES,
        'status_choices': SuggestionBox.STATUS_CHOICES,
        'current_type': suggestion_type,
        'current_status': status,
        'search': search,
    }
    
    return render(request, 'communication/suggestion_list.html', context)


@login_required
def suggestion_create(request):
    """Criar nova sugestão"""
    if request.method == 'POST':
        form = SuggestionBoxForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            if not form.cleaned_data.get('is_anonymous'):
                suggestion.author = request.user
            suggestion.save()
            messages.success(request, 'Sugestão enviada com sucesso!')
            return redirect('communication:suggestion_list')
    else:
        form = SuggestionBoxForm()
    
    return render(request, 'communication/suggestion_create.html', {'form': form})


@login_required
def newsletter_list(request):
    """Lista de newsletters"""
    newsletters = Newsletter.objects.filter(
        is_published=True
    ).order_by('-publish_date')
    
    # Busca
    search = request.GET.get('search')
    if search:
        newsletters = newsletters.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(newsletters, 10)
    page = request.GET.get('page')
    newsletters = paginator.get_page(page)
    
    return render(request, 'communication/newsletter_list.html', {
        'newsletters': newsletters,
        'search': search,
    })


@login_required
def settings_view(request):
    """Configurações de comunicação"""
    settings_obj, created = CommunicationSettings.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = CommunicationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('communication:settings')
    else:
        form = CommunicationSettingsForm(instance=settings_obj)
    
    return render(request, 'communication/settings.html', {'form': form})


def get_unread_announcements_count(user):
    """Conta comunicados não lidos"""
    total_announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    ).count()
    
    read_announcements = AnnouncementReadReceipt.objects.filter(
        user=user
    ).count()
    
    return total_announcements - read_announcements


# Views para Staff/Admin
@login_required
def create_announcement(request):
    """Criar comunicado (apenas staff)"""
    if not request.user.is_staff:
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
            return redirect('communication:announcements_list')
    else:
        form = AnnouncementForm()
    
    return render(request, 'communication/announcement_create.html', {'form': form})


@login_required
def create_memo(request):
    """Criar memorando (apenas staff)"""
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para criar memorandos.')
        return redirect('communication:memo_list')
    
    if request.method == 'POST':
        form = InternalMemoForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.from_user = request.user
            # Assumir departamento do usuário se tiver
            if hasattr(request.user, 'employee_profile'):
                memo.from_department = request.user.employee_profile.department
            memo.save()
            form.save_m2m()
            messages.success(request, 'Memorando criado com sucesso!')
            return redirect('communication:memo_list')
    else:
        form = InternalMemoForm()
    
    return render(request, 'communication/memo_create.html', {'form': form})


@login_required
def newsletter_create(request):
    """Criar newsletter (apenas staff)"""
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para criar newsletters.')
        return redirect('communication:newsletter_list')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST, request.FILES)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            messages.success(request, 'Newsletter criada com sucesso!')
            return redirect('communication:newsletter_list')
    else:
        form = NewsletterForm()
    
    return render(request, 'communication/newsletter_create.html', {'form': form})
