from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from members.models import Beneficiary
from members.forms import BeneficiaryForm
from workshops.models import Workshop


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


@login_required
@user_passes_test(is_technician)
def dashboard_home(request):
    """Dashboard principal com indicadores expandidos"""
    from django.contrib.auth import get_user_model
    from users.models import UserActivity
    from social.models import SocialAnamnesis
    from evolution.models import EvolutionRecord
    from projects.models import ProjectEnrollment
    
    User = get_user_model()
    now = timezone.now()
    today = now.date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Estatísticas de Beneficiárias
    total_beneficiaries = Beneficiary.objects.count()
    new_beneficiaries_week = Beneficiary.objects.filter(created_at__date__gte=last_week).count()
    new_beneficiaries_month = Beneficiary.objects.filter(created_at__date__gte=last_month).count()
    
    # Estatísticas de Usuários
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    recent_logins = User.objects.filter(last_login__date__gte=last_week).count()
    
    # Estatísticas de Atividades do Sistema
    total_activities = UserActivity.objects.count()
    activities_today = UserActivity.objects.filter(timestamp__date=today).count()
    activities_week = UserActivity.objects.filter(timestamp__date__gte=last_week).count()
    
    # Estatísticas de Anamneses Sociais
    total_interviews = SocialAnamnesis.objects.count()
    pending_interviews = SocialAnamnesis.objects.filter(locked=False).count()
    completed_interviews = SocialAnamnesis.objects.filter(locked=True).count()
    
    # Estatísticas de Evoluções
    total_evolutions = EvolutionRecord.objects.count()
    evolutions_month = EvolutionRecord.objects.filter(created_at__date__gte=last_month).count()
    
    # Estatísticas de Projetos
    total_projects = ProjectEnrollment.objects.count()
    active_projects = ProjectEnrollment.objects.filter(status='ATIVO').count()
    
    # Workshops com otimizações
    workshop_stats = Workshop.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='ativo')),
        completed=Count('id', filter=Q(status='finalizada')),
        cancelled=Count('id', filter=Q(status='cancelada'))
    )
    
    # Dados recentes para listagens
    recent_beneficiaries = Beneficiary.objects.order_by('-created_at')[:5]
    recent_workshops = Workshop.objects.order_by('-created_at')[:3]
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:5]
    
    # Estatísticas por faixa etária das beneficiárias
    age_stats = {
        'children': Beneficiary.objects.filter(dob__gte=today - timedelta(days=18*365)).count(),
        'adults': Beneficiary.objects.filter(
            dob__lt=today - timedelta(days=18*365),
            dob__gte=today - timedelta(days=60*365)
        ).count(),
        'elderly': Beneficiary.objects.filter(dob__lt=today - timedelta(days=60*365)).count(),
    }
    
    context = {
        # Beneficiárias
        'total_beneficiaries': total_beneficiaries,
        'new_beneficiaries_week': new_beneficiaries_week,
        'new_beneficiaries_month': new_beneficiaries_month,
        'recent_beneficiaries': recent_beneficiaries,
        
        # Usuários
        'total_users': total_users,
        'active_users': active_users,
        'recent_logins': recent_logins,
        
        # Atividades
        'total_activities': total_activities,
        'activities_today': activities_today,
        'activities_week': activities_week,
        'recent_activities': recent_activities,
        
        # Entrevistas
        'total_interviews': total_interviews,
        'pending_interviews': pending_interviews,
        'completed_interviews': completed_interviews,
        
        # Evoluções
        'total_evolutions': total_evolutions,
        'evolutions_month': evolutions_month,
        
        # Projetos
        'total_projects': total_projects,
        'active_projects': active_projects,
        
        # Workshops
        'total_workshops': workshop_stats['total'],
        'active_workshops': workshop_stats['active'],
        'completed_workshops': workshop_stats['completed'],
        'cancelled_workshops': workshop_stats['cancelled'],
        'recent_workshops': recent_workshops,
        
        # Estatísticas demográficas
        'age_stats': age_stats,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiaries_list(request):
    """Lista de beneficiárias com busca HTMX e otimizações"""
    search_query = request.GET.get('q', '')
    
    # Query sem select_related pois não há campo created_by
    beneficiaries = Beneficiary.objects.all()
    
    if search_query:
        beneficiaries = beneficiaries.filter(
            Q(full_name__icontains=search_query) |
            Q(cpf__icontains=search_query) |
            Q(phone_1__icontains=search_query) |
            Q(phone_2__icontains=search_query)
        )
    
    # Paginação para melhor performance
    from django.core.paginator import Paginator
    paginator = Paginator(beneficiaries.order_by('full_name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/partials/beneficiaries_table.html', context)
    
    return render(request, 'dashboard/beneficiaries_list.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiary_detail(request, pk):
    """Detalhes de uma beneficiária"""
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    
    context = {
        'beneficiary': beneficiary,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/partials/beneficiary_detail.html', context)
    
    return render(request, 'dashboard/beneficiary_detail.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiary_create(request):
    """Formulário para criar nova beneficiária"""
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            beneficiary = form.save()
            messages.success(
                request, 
                f'Beneficiária {beneficiary.full_name} cadastrada com sucesso!'
            )
            return redirect('dashboard:beneficiary_detail', pk=beneficiary.pk)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = BeneficiaryForm()
    
    context = {
        'form': form,
        'title': 'Nova Beneficiária'
    }
    return render(request, 'dashboard/beneficiary_form.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiary_edit(request, pk):
    """Formulário para editar beneficiária"""
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST, instance=beneficiary)
        if form.is_valid():
            beneficiary = form.save()
            messages.success(
                request, 
                f'Dados de {beneficiary.full_name} atualizados com sucesso!'
            )
            return redirect('dashboard:beneficiary_detail', pk=beneficiary.pk)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = BeneficiaryForm(instance=beneficiary)
    
    context = {
        'form': form,
        'beneficiary': beneficiary,
        'title': f'Editar {beneficiary.full_name}'
    }
    return render(request, 'dashboard/beneficiary_form.html', context)
