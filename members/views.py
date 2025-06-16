from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Beneficiary, Consent
from .forms import BeneficiaryForm


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class BeneficiaryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de beneficiárias"""
    
    model = Beneficiary
    template_name = 'members/beneficiary_list.html'
    context_object_name = 'beneficiaries'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Query otimizada com filtros múltiplos"""
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        # Buscar sempre dados frescos do banco (sem cache)
        queryset = Beneficiary.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(neighbourhood__icontains=search) |
                Q(phone_1__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('full_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dados para filtros
        context['status_choices'] = Beneficiary.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        # Estatísticas
        context['total_active'] = Beneficiary.objects.filter(status='ATIVA').count()
        context['total_inactive'] = Beneficiary.objects.filter(status='INATIVA').count()
        
        return context


class BeneficiaryDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de uma beneficiária"""
    
    model = Beneficiary
    template_name = 'members/beneficiary_detail.html'
    context_object_name = 'beneficiary'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"beneficiary_detail_{pk}"
        beneficiary = cache.get(cache_key)
        
        if beneficiary is None:
            beneficiary = get_object_or_404(Beneficiary, pk=pk)
            cache.set(cache_key, beneficiary, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return beneficiary
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Buscar matrículas em projetos
        context['project_enrollments'] = self.object.project_enrollments.select_related('project').all()
        
        # Buscar anamneses sociais (usando related_name correto)
        context['social_anamneses'] = self.object.social_anamnesis.all()[:5]  # Últimas 5
        
        return context


class BeneficiaryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar nova beneficiária"""
    
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:beneficiary-list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Invalidar caches relacionados
        cache.delete_many([key for key in cache._cache.keys() if key.startswith('beneficiaries_list_')])
        
        messages.success(self.request, f'Beneficiária {form.instance.full_name} cadastrada com sucesso!')
        return response


class BeneficiaryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar beneficiária"""
    
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:beneficiary-list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"beneficiary_detail_{pk}"
        beneficiary = cache.get(cache_key)
        if beneficiary is None:
            beneficiary = get_object_or_404(Beneficiary, pk=pk)
            cache.set(cache_key, beneficiary, settings.CACHE_TIMEOUT['MEDIUM'])
        return beneficiary
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Invalidar caches
        cache.delete(f"beneficiary_detail_{self.object.pk}")
        cache.delete_many([key for key in cache._cache.keys() if key.startswith('beneficiaries_list_')])
        
        messages.success(self.request, f'Beneficiária {form.instance.full_name} atualizada com sucesso!')
        return response


class BeneficiaryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Excluir beneficiária"""
    
    model = Beneficiary
    template_name = 'members/beneficiary_confirm_delete.html'
    success_url = reverse_lazy('members:beneficiary-list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        beneficiary = self.get_object()
        
        # Verificar se há matrículas ativas
        active_enrollments = beneficiary.project_enrollments.filter(status='ATIVO').count()
        if active_enrollments > 0:
            messages.error(request, f'Não é possível excluir a beneficiária "{beneficiary.full_name}" pois ela possui {active_enrollments} matrícula(s) ativa(s) em projetos.')
            return redirect('members:beneficiary-detail', pk=beneficiary.pk)
        
        beneficiary_name = beneficiary.full_name
        beneficiary_id = beneficiary.pk
        
        response = super().delete(request, *args, **kwargs)
        
        # Invalidar caches
        cache.delete(f"beneficiary_detail_{beneficiary_id}")
        cache.delete_many([key for key in cache._cache.keys() if key.startswith('beneficiaries_list_')])
        
        messages.success(request, f'Beneficiária "{beneficiary_name}" excluída com sucesso!')
        return response


@login_required
@user_passes_test(is_technician)
@require_POST
def toggle_beneficiary_status(request, pk):
    """Ativar/Inativar beneficiária"""
    try:
        beneficiary = get_object_or_404(Beneficiary, pk=pk)
        
        if beneficiary.is_active:
            beneficiary.deactivate()
            message = f'Beneficiária {beneficiary.full_name} inativada com sucesso!'
        else:
            beneficiary.activate()
            message = f'Beneficiária {beneficiary.full_name} ativada com sucesso!'
        
        # Não precisamos mais limpar cache pois removemos cache da lista
        
        messages.success(request, message)
        
    except Exception as e:
        messages.error(request, f'Erro ao alterar status da beneficiária: {str(e)}')
    
    # Sempre redirecionar para a lista de beneficiárias
    return redirect('members:beneficiary-list')
