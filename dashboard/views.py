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
    """Dashboard principal com otimizações de performance"""
    # Estatísticas com consultas otimizadas
    total_beneficiaries = Beneficiary.objects.count()
    
    # Beneficiárias recentes (sem select_related pois não há created_by)
    recent_beneficiaries = Beneficiary.objects.order_by('-created_at')[:5]
    
    # Workshops com otimizações
    workshop_stats = Workshop.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='ativo'))
    )
    
    # Workshops recentes (removendo select_related desnecessário)
    recent_workshops = Workshop.objects.order_by('-created_at')[:3]
    
    context = {
        'total_beneficiaries': total_beneficiaries,
        'recent_beneficiaries': recent_beneficiaries,
        'total_workshops': workshop_stats['total'],
        'active_workshops': workshop_stats['active'],
        'recent_workshops': recent_workshops,
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
