from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.utils import timezone
from core.permissions import is_technician
from .models import ActionPlan, WheelOfLife
from members.models import Beneficiary


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


class ActionPlanCreateView(CreateConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo coaching?"
    confirmation_entity = "coaching"  # "Criar novo plano de ação"""
    
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


class ActionPlanUpdateView(EditConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste coaching?"
    confirmation_entity = "coaching"  # "Editar plano de ação"""
    
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


class ActionPlanDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir este coaching?"
    confirmation_entity = "coaching"
    dangerous_operation = True  # Excluir plano de ação
    
    model = ActionPlan
    template_name = 'coaching/action_plan_confirm_delete.html'
    success_url = reverse_lazy('coaching:action_plan_list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Override delete para adicionar log"""
        self.object = self.get_object()
        
        # Log da atividade
        from users.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            description=f'Excluiu plano de ação de {self.object.beneficiary.full_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        success_url = self.get_success_url()
        self.object.delete()
        
        messages.success(request, f'Plano de ação de {self.object.beneficiary.full_name} excluído com sucesso!')
        return redirect(success_url)


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


class WheelOfLifeCreateView(CreateConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):
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


class WheelOfLifeUpdateView(EditConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
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


class WheelOfLifeDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Excluir roda da vida"""
    
    model = WheelOfLife
    template_name = 'coaching/wheel_confirm_delete.html'
    success_url = reverse_lazy('coaching:wheel_list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Override delete para adicionar log"""
        self.object = self.get_object()
        
        # Log da atividade
        from users.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            description=f'Excluiu roda da vida de {self.object.beneficiary.full_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        success_url = self.get_success_url()
        self.object.delete()
        
        messages.success(request, f'Roda da vida de {self.object.beneficiary.full_name} excluída com sucesso!')
        return redirect(success_url)


# ============================================================================
# VIEWS ADICIONAIS - FUNCIONALIDADES CRÍTICAS
# ============================================================================

class CoachingSessionListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View para listagem de sessões de coaching"""
    template_name = 'coaching/sessions.html'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Sessões de Coaching',
            'subtitle': 'Gestão de sessões individuais e em grupo',
            'feature_status': 'Em desenvolvimento',
            'expected_release': 'Próxima sprint',
            'contact_support': 'Entre em contato com a equipe técnica para mais informações'
        })
        return context


class CoachingSessionCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View para criação de sessões de coaching"""
    template_name = 'coaching/session_create.html'
    
    def test_func(self):
        return is_technician(self.request.user)


class CoachingSessionDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View para detalhes de sessão de coaching"""
    template_name = 'coaching/session_detail.html'
    
    def test_func(self):
        return is_technician(self.request.user)


class CoachingReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View para relatórios de coaching"""
    template_name = 'coaching/reports.html'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas básicas
        total_action_plans = ActionPlan.objects.count()
        active_action_plans = ActionPlan.objects.filter(status='ACTIVE').count()
        total_wheels = WheelOfLife.objects.count()
        
        # Action plans por status
        action_plan_stats = ActionPlan.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Beneficiárias com mais action plans
        top_beneficiaries = Beneficiary.objects.annotate(
            action_plan_count=Count('action_plans')
        ).filter(action_plan_count__gt=0).order_by('-action_plan_count')[:5]
        
        context.update({
            'title': 'Relatórios de Coaching',
            'total_action_plans': total_action_plans,
            'active_action_plans': active_action_plans,
            'completed_action_plans': ActionPlan.objects.filter(status='COMPLETED').count(),
            'total_wheels': total_wheels,
            'action_plan_stats': list(action_plan_stats),
            'top_beneficiaries': top_beneficiaries,
            'feature_status': 'Funcional com dados básicos',
            'last_updated': timezone.now(),
        })
        return context
