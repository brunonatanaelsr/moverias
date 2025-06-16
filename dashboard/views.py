from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache
import csv
from datetime import timedelta
from core.optimizers import CacheManager, QueryOptimizer
from members.models import Beneficiary
from members.forms import BeneficiaryForm
from workshops.models import Workshop


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


@login_required
@user_passes_test(is_technician)
def dashboard_home(request):
    """Dashboard principal com indicadores em tempo real (SEM CACHE)"""
    
    # Dados adicionais que precisam ser calculados
    from django.contrib.auth import get_user_model
    from users.models import UserActivity
    from social.models import SocialAnamnesis
    from evolution.models import EvolutionRecord
    from projects.models import ProjectEnrollment, Project
    from coaching.models import ActionPlan, WheelOfLife
    
    User = get_user_model()
    now = timezone.now()
    today = now.date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Estatísticas em tempo real (SEM CACHE)
    extended_stats = {
        # Beneficiárias com aggregation
        'beneficiary_stats': Beneficiary.objects.aggregate(
            total=Count('id'),
            new_week=Count('id', filter=Q(created_at__date__gte=last_week)),
            new_month=Count('id', filter=Q(created_at__date__gte=last_month))
        ),
        
        # Usuários
        'user_stats': User.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            recent_logins=Count('id', filter=Q(last_login__date__gte=last_week))
        ),
        
        # Atividades
        'activity_stats': UserActivity.objects.aggregate(
            total=Count('id'),
            today=Count('id', filter=Q(timestamp__date=today)),
            week=Count('id', filter=Q(timestamp__date__gte=last_week))
        ),
        
        # Anamneses
        'anamnesis_stats': SocialAnamnesis.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(locked=False)),
            completed=Count('id', filter=Q(locked=True))
        ),
        
        # Evoluções
        'evolution_stats': EvolutionRecord.objects.aggregate(
            total=Count('id'),
            month=Count('id', filter=Q(created_at__date__gte=last_month))
        ),
        
        # Projetos (usando o modelo Project)
        'project_stats': Project.objects.aggregate(
            total=Count('id'),
            active=Count('id')  # Todos os projetos são considerados ativos
        ),
        
        # Matrículas em projetos
        'enrollment_stats': ProjectEnrollment.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ATIVO'))
        ),
        
        # Planos de Ação
        'action_plan_stats': ActionPlan.objects.aggregate(
            total=Count('id'),
            recent=Count('id', filter=Q(created_at__date__gte=last_month))
        ),
        
        # Rodas da Vida
        'wheel_stats': WheelOfLife.objects.aggregate(
            total=Count('id'),
            recent=Count('id', filter=Q(created_at__date__gte=last_month))
        ),
            
        # Workshops com aggregation
        'workshop_stats': Workshop.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ativo')),
            completed=Count('id', filter=Q(status='concluido')),
            cancelled=Count('id', filter=Q(status='cancelado'))
        )
    }
    
    # Dados recentes em tempo real (SEM CACHE)
    recent_data = {
        'recent_beneficiaries': Beneficiary.objects.order_by('-created_at')[:5],
        'recent_workshops': Workshop.objects.order_by('-created_at')[:3],
        'recent_activities': UserActivity.objects.select_related('user').order_by('-timestamp')[:5],
        'upcoming_events': Workshop.objects.filter(
            status='ativo',
            start_date__gte=today
        ).order_by('start_date')[:5]
    }
    
    # Estatísticas por faixa etária em tempo real
    age_stats = {
        'children': Beneficiary.objects.filter(dob__gte=today - timedelta(days=18*365)).count(),
        'adults': Beneficiary.objects.filter(
            dob__lt=today - timedelta(days=18*365),
            dob__gte=today - timedelta(days=60*365)
        ).count(),
        'elderly': Beneficiary.objects.filter(dob__lt=today - timedelta(days=60*365)).count(),
    }
    
    # Criar contexto unificado com todas as estatísticas
    context = {
        # Estatísticas principais para compatibilidade com template
        'stats': {
            'total_beneficiaries': extended_stats['beneficiary_stats']['total'],
            'active_projects': extended_stats['project_stats']['total'],  # Usar total de projetos
            'active_workshops': extended_stats['workshop_stats']['active'],
            'monthly_sessions': extended_stats['evolution_stats']['month'],
            'total_anamnesis': extended_stats['anamnesis_stats']['total'],
            'completed_anamnesis': extended_stats['anamnesis_stats']['completed'],
            'pending_anamnesis': extended_stats['anamnesis_stats']['pending'],
        },
        # Dados detalhados
        **extended_stats,
        **recent_data,
        'age_stats': age_stats,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiaries_list(request):
    """Lista de beneficiárias com busca HTMX e otimizações"""
    search_query = request.GET.get('q', '')
    
    # Query simples sem cache por enquanto
    beneficiaries = Beneficiary.objects.all()
    
    if search_query:
        beneficiaries = beneficiaries.filter(
            Q(full_name__icontains=search_query) |
            Q(phone_1__icontains=search_query) |
            Q(phone_2__icontains=search_query) |
            Q(neighbourhood__icontains=search_query)
        )
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(beneficiaries.order_by('full_name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': paginator.count
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


@login_required
@user_passes_test(is_technician)
def beneficiaries_export(request):
    """Export beneficiaries list to CSV"""
    
    # Get all beneficiaries with optimized query
    beneficiaries = Beneficiary.objects.select_related().order_by('full_name')
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="beneficiarias_movemarias_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'Nome Completo',
        'Data de Nascimento', 
        'NIS',
        'Telefone 1',
        'Telefone 2',
        'Bairro',
        'Endereço',
        'Referência',
        'Data de Cadastro'
    ])
    
    # Write beneficiary data
    for beneficiary in beneficiaries:
        writer.writerow([
            beneficiary.full_name,
            beneficiary.dob.strftime('%d/%m/%Y') if beneficiary.dob else '',
            beneficiary.nis or '',
            beneficiary.phone_1 or '',
            beneficiary.phone_2 or '',
            beneficiary.neighbourhood or '',
            beneficiary.address or '',
            beneficiary.reference or '',
            beneficiary.created_at.strftime('%d/%m/%Y %H:%M') if beneficiary.created_at else ''
        ])
    
    return response
