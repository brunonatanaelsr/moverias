from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from members.models import Beneficiary
from members.forms import BeneficiaryForm
from workshops.models import Workshop


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


@login_required
@user_passes_test(is_technician)
def dashboard_home(request):
    """Dashboard principal"""
    context = {
        'total_beneficiaries': Beneficiary.objects.count(),
        'recent_beneficiaries': Beneficiary.objects.order_by('-created_at')[:5],
        'total_workshops': Workshop.objects.count(),
        'active_workshops': Workshop.objects.filter(status='ativo').count(),
        'recent_workshops': Workshop.objects.order_by('-created_at')[:3],
    }
    return render(request, 'dashboard/home.html', context)


@login_required
@user_passes_test(is_technician)
def beneficiaries_list(request):
    """Lista de beneficiárias com busca HTMX"""
    search_query = request.GET.get('q', '')
    beneficiaries = Beneficiary.objects.all()
    
    if search_query:
        beneficiaries = beneficiaries.filter(
            full_name__icontains=search_query
        )
    
    context = {
        'beneficiaries': beneficiaries.order_by('full_name'),
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
