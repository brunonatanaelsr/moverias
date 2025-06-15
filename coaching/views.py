from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import ActionPlan, WheelOfLife
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class ActionPlanListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de planos de ação"""
    
    model = ActionPlan
    template_name = 'coaching/action_plan_list.html'
    context_object_name = 'action_plans'
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
        return queryset


class ActionPlanDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de um plano de ação"""
    
    model = ActionPlan
    template_name = 'coaching/action_plan_detail.html'
    context_object_name = 'action_plan'
    
    def test_func(self):
        return is_technician(self.request.user)


class ActionPlanCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar novo plano de ação"""
    
    model = ActionPlan
    template_name = 'coaching/action_plan_form.html'
    fields = ['beneficiary', 'main_goal', 'priority_areas', 'actions', 'institute_support']
    success_url = reverse_lazy('coaching:action_plan_list')
    
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
        response = super().form_valid(form)
        messages.success(self.request, f'Plano de ação para {form.instance.beneficiary.full_name} criado com sucesso!')
        return response


class ActionPlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar plano de ação"""
    
    model = ActionPlan
    template_name = 'coaching/action_plan_form.html'
    fields = ['main_goal', 'priority_areas', 'actions', 'institute_support', 'semester_review']
    success_url = reverse_lazy('coaching:action_plan_list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Plano de ação para {form.instance.beneficiary.full_name} atualizado com sucesso!')
        return response


class WheelOfLifeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de rodas da vida"""
    
    model = WheelOfLife
    template_name = 'coaching/wheel_list.html'
    context_object_name = 'wheels'
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
        return queryset


class WheelOfLifeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de uma roda da vida"""
    
    model = WheelOfLife
    template_name = 'coaching/wheel_detail.html'
    context_object_name = 'wheel'
    
    def test_func(self):
        return is_technician(self.request.user)


class WheelOfLifeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar nova roda da vida"""
    
    model = WheelOfLife
    template_name = 'coaching/wheel_form.html'
    fields = [
        'beneficiary', 'date', 'family', 'finance', 'health', 'career',
        'relationships', 'personal_growth', 'leisure', 'spirituality',
        'education', 'environment', 'contribution', 'emotions'
    ]
    success_url = reverse_lazy('coaching:wheel_list')
    
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
        response = super().form_valid(form)
        messages.success(self.request, f'Roda da vida para {form.instance.beneficiary.full_name} criada com sucesso!')
        return response


class WheelOfLifeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar roda da vida"""
    
    model = WheelOfLife
    template_name = 'coaching/wheel_form.html'
    fields = [
        'date', 'family', 'finance', 'health', 'career',
        'relationships', 'personal_growth', 'leisure', 'spirituality',
        'education', 'environment', 'contribution', 'emotions'
    ]
    success_url = reverse_lazy('coaching:wheel_list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Roda da vida para {form.instance.beneficiary.full_name} atualizada com sucesso!')
        return response
