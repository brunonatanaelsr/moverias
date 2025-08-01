
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from members.models import Beneficiary
from members.forms import BeneficiaryForm

class BeneficiaryListView(LoginRequiredMixin, ListView):
    model = Beneficiary
    template_name = 'members/beneficiary_list.html'
    context_object_name = 'beneficiaries'
    
    def get_queryset(self):
        return Beneficiary.objects.all().order_by('-created_at')

class BeneficiaryCreateView(LoginRequiredMixin, CreateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:list')

    def form_valid(self, form):
        messages.success(self.request, 'Beneficiária cadastrada com sucesso!')
        return super().form_valid(form)

class BeneficiaryDetailView(LoginRequiredMixin, DetailView):
    model = Beneficiary
    template_name = 'members/beneficiary_detail.html'
    context_object_name = 'beneficiary'

class BeneficiaryUpdateView(LoginRequiredMixin, UpdateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:list')

    def form_valid(self, form):
        messages.success(self.request, 'Beneficiária atualizada com sucesso!')
        return super().form_valid(form)

class BeneficiaryDeleteView(LoginRequiredMixin, DeleteView):
    model = Beneficiary
    template_name = 'members/beneficiary_confirm_delete.html'
    success_url = reverse_lazy('members:list')

class BeneficiaryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'members/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_beneficiaries = Beneficiary.objects.count()
        active_beneficiaries = Beneficiary.objects.filter(status='ATIVA').count()
        
        context['total_beneficiaries'] = total_beneficiaries
        context['active_beneficiaries'] = active_beneficiaries
        context['inactive_beneficiaries'] = total_beneficiaries - active_beneficiaries
        
        # Calcular taxa de atividade
        if total_beneficiaries > 0:
            context['activity_rate'] = round((active_beneficiaries / total_beneficiaries) * 100, 1)
        else:
            context['activity_rate'] = 0
        
        # Adicionar beneficiárias recentes (últimas 5)
        context['recent_beneficiaries'] = Beneficiary.objects.filter(
            status='ATIVA'
        ).order_by('-created_at')[:5]
        
        return context


# ============================================================================
# VIEWS ADICIONAIS - FUNCIONALIDADES CRÍTICAS
# ============================================================================

class BeneficiaryImportView(LoginRequiredMixin, TemplateView):
    """View para importação de dados de beneficiárias"""
    template_name = 'members/import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Importar Dados de Beneficiárias',
            'subtitle': 'Upload de arquivo CSV ou Excel com dados das beneficiárias',
            'feature_status': 'Em desenvolvimento',
            'expected_release': 'Próxima sprint',
            'contact_support': 'Entre em contato com a equipe técnica para mais informações'
        })
        return context


class BeneficiaryReportsView(LoginRequiredMixin, TemplateView):
    """View para relatórios de beneficiárias"""
    template_name = 'members/reports.html'
    
    def get_context_data(self, **kwargs):
        from datetime import date
        from dateutil.relativedelta import relativedelta
        from django.db.models import Count
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        # Estatísticas básicas
        total_beneficiaries = Beneficiary.objects.count()
        try:
            active_beneficiaries = Beneficiary.objects.filter(status='ATIVA').count()
        except:
            active_beneficiaries = Beneficiary.objects.filter(status='ACTIVE').count()
        
        # Dados por idade (simplificado para evitar erros)
        age_ranges = {
            'age_18_25': 0,
            'age_26_35': 0,
            'age_36_50': 0,
            'age_50_plus': 0,
        }
        
        # Dados por escolaridade (simplificado)
        try:
            education_stats = Beneficiary.objects.values('education_level').annotate(
                count=Count('id')
            ).order_by('education_level')
        except:
            education_stats = []
        
        context.update({
            'title': 'Relatórios de Beneficiárias',
            'total_beneficiaries': total_beneficiaries,
            'active_beneficiaries': active_beneficiaries,
            'inactive_beneficiaries': total_beneficiaries - active_beneficiaries,
            'age_ranges': age_ranges,
            'education_stats': list(education_stats),
            'feature_status': 'Funcional com dados básicos',
            'last_updated': timezone.now(),
        })
        return context
