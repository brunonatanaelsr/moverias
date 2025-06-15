from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import EvolutionRecord
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class EvolutionRecordListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de registros de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_list.html'
    context_object_name = 'records'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('beneficiary')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                beneficiary__full_name__icontains=search
            )
        return queryset.order_by('-date')


class EvolutionRecordDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de um registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_detail.html'
    context_object_name = 'record'
    
    def test_func(self):
        return is_technician(self.request.user)


class EvolutionRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar novo registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['beneficiary', 'date', 'description', 'signature_required']
    success_url = reverse_lazy('evolution:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_initial(self):
        initial = super().get_initial()
        # Se beneficiário foi passado na URL
        beneficiary_id = self.request.GET.get('beneficiary')
        if beneficiary_id:
            try:
                beneficiary = Beneficiary.objects.get(pk=beneficiary_id)
                initial['beneficiary'] = beneficiary
            except Beneficiary.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Registro de evolução para {form.instance.beneficiary.full_name} criado com sucesso!')
        return response


class EvolutionRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['date', 'description', 'signature_required', 'signed_by_beneficiary']
    success_url = reverse_lazy('evolution:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Registro de evolução para {form.instance.beneficiary.full_name} atualizado com sucesso!')
        return response
