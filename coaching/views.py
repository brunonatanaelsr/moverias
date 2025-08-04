from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse
from core.permissions import is_technician
from core.export_utils import export_universal, DataFormatter, ExportManager
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


# =============================================================================
# EXPORT VIEWS
# =============================================================================

@login_required
def action_plans_export(request):
    """
    Exporta lista de planos de ação em CSV, Excel ou PDF
    """
    # Verificar permissão
    if not is_technician(request.user):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('coaching:dashboard')
    
    # Função personalizada para formatar dados de planos de ação
    def format_action_plan_data(action_plans):
        headers = [
            'Beneficiária', 'Objetivo Principal', 'Status', 'Data de Criação',
            'Data de Início', 'Data de Término', 'Progresso (%)', 'Observações'
        ]
        
        data = []
        for plan in action_plans:
            # Calcular progresso
            progress = getattr(plan, 'progress', 0) or 0
            
            data.append([
                str(plan.beneficiary),
                plan.main_goal if hasattr(plan, 'main_goal') else '',
                plan.get_status_display() if hasattr(plan, 'get_status_display') else plan.status,
                plan.created_at.strftime('%d/%m/%Y') if plan.created_at else '',
                plan.start_date.strftime('%d/%m/%Y') if hasattr(plan, 'start_date') and plan.start_date else '',
                plan.end_date.strftime('%d/%m/%Y') if hasattr(plan, 'end_date') and plan.end_date else '',
                f"{progress}%",
                plan.notes[:100] + '...' if hasattr(plan, 'notes') and plan.notes and len(plan.notes) > 100 else (getattr(plan, 'notes', '') or '')
            ])
        
        return data, headers
    
    return export_universal(
        request=request,
        model_class=ActionPlan,
        formatter_method=format_action_plan_data,
        filename_prefix="planos_acao",
        template_name="core/exports/pdf_report.html",
        extra_context={
            'report_type': 'Planos de Ação',
            'user': request.user
        }
    )


@login_required
def wheels_of_life_export(request):
    """
    Exporta lista de rodas da vida em CSV, Excel ou PDF
    """
    # Verificar permissão
    if not is_technician(request.user):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('coaching:dashboard')
    
    # Função personalizada para formatar dados de rodas da vida
    def format_wheel_data(wheels):
        headers = [
            'Beneficiária', 'Data de Criação', 'Carreira', 'Dinheiro', 'Saúde',
            'Família', 'Relacionamentos', 'Diversão', 'Crescimento Pessoal',
            'Contribuição Social', 'Média Geral', 'Observações'
        ]
        
        data = []
        for wheel in wheels:
            # Calcular média das áreas
            areas = [
                getattr(wheel, 'career', 0) or 0,
                getattr(wheel, 'money', 0) or 0,
                getattr(wheel, 'health', 0) or 0,
                getattr(wheel, 'family', 0) or 0,
                getattr(wheel, 'relationships', 0) or 0,
                getattr(wheel, 'fun', 0) or 0,
                getattr(wheel, 'personal_growth', 0) or 0,
                getattr(wheel, 'social_contribution', 0) or 0,
            ]
            average = sum(areas) / len(areas) if areas else 0
            
            data.append([
                str(wheel.beneficiary),
                wheel.created_at.strftime('%d/%m/%Y') if wheel.created_at else '',
                getattr(wheel, 'career', 0) or 0,
                getattr(wheel, 'money', 0) or 0,
                getattr(wheel, 'health', 0) or 0,
                getattr(wheel, 'family', 0) or 0,
                getattr(wheel, 'relationships', 0) or 0,
                getattr(wheel, 'fun', 0) or 0,
                getattr(wheel, 'personal_growth', 0) or 0,
                getattr(wheel, 'social_contribution', 0) or 0,
                f"{average:.1f}",
                getattr(wheel, 'notes', '')[:100] + '...' if getattr(wheel, 'notes', '') and len(getattr(wheel, 'notes', '')) > 100 else (getattr(wheel, 'notes', '') or '')
            ])
        
        return data, headers
    
    return export_universal(
        request=request,
        model_class=WheelOfLife,
        formatter_method=format_wheel_data,
        filename_prefix="rodas_vida",
        template_name="core/exports/pdf_report.html",
        extra_context={
            'report_type': 'Rodas da Vida',
            'user': request.user
        }
    )


@login_required
def beneficiary_coaching_export(request, beneficiary_id):
    """
    Exporta histórico de coaching de uma beneficiária específica
    """
    # Verificar permissão
    if not is_technician(request.user):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('coaching:dashboard')
    
    beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)
    action_plans = ActionPlan.objects.filter(beneficiary=beneficiary).order_by('-created_at')
    wheels = WheelOfLife.objects.filter(beneficiary=beneficiary).order_by('-created_at')
    
    # Combinar dados de planos de ação e rodas da vida
    headers = [
        'Tipo', 'Data', 'Título/Objetivo', 'Status/Média', 'Progresso',
        'Observações', 'Detalhes'
    ]
    
    data = []
    
    # Adicionar planos de ação
    for plan in action_plans:
        data.append([
            'Plano de Ação',
            plan.created_at.strftime('%d/%m/%Y') if plan.created_at else '',
            getattr(plan, 'main_goal', '') or '',
            plan.get_status_display() if hasattr(plan, 'get_status_display') else plan.status,
            f"{getattr(plan, 'progress', 0) or 0}%",
            getattr(plan, 'notes', '')[:100] + '...' if getattr(plan, 'notes', '') and len(getattr(plan, 'notes', '')) > 100 else (getattr(plan, 'notes', '') or ''),
            f"Início: {plan.start_date.strftime('%d/%m/%Y') if hasattr(plan, 'start_date') and plan.start_date else 'N/A'}"
        ])
    
    # Adicionar rodas da vida
    for wheel in wheels:
        areas = [
            getattr(wheel, 'career', 0) or 0,
            getattr(wheel, 'money', 0) or 0,
            getattr(wheel, 'health', 0) or 0,
            getattr(wheel, 'family', 0) or 0,
            getattr(wheel, 'relationships', 0) or 0,
            getattr(wheel, 'fun', 0) or 0,
            getattr(wheel, 'personal_growth', 0) or 0,
            getattr(wheel, 'social_contribution', 0) or 0,
        ]
        average = sum(areas) / len(areas) if areas else 0
        
        data.append([
            'Roda da Vida',
            wheel.created_at.strftime('%d/%m/%Y') if wheel.created_at else '',
            'Avaliação das Áreas da Vida',
            f"Média: {average:.1f}",
            'N/A',
            getattr(wheel, 'notes', '')[:100] + '...' if getattr(wheel, 'notes', '') and len(getattr(wheel, 'notes', '')) > 100 else (getattr(wheel, 'notes', '') or ''),
            f"Maior área: {max(areas) if areas else 0} | Menor área: {min(areas) if areas else 0}"
        ])
    
    # Ordenar por data (mais recente primeiro)
    data.sort(key=lambda x: x[1], reverse=True)
    
    export_format = request.GET.get('format', 'csv')
    filename = f"coaching_{beneficiary.full_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
    
    try:
        if export_format == 'csv':
            return ExportManager.export_to_csv(data, filename, headers)
        elif export_format == 'excel':
            return ExportManager.export_to_excel(data, filename, headers, f"Coaching - {beneficiary.full_name}")
        elif export_format == 'pdf':
            context = {
                'data': data,
                'headers': headers,
                'title': f'Histórico de Coaching - {beneficiary.full_name}',
                'generated_at': timezone.now(),
                'beneficiary': beneficiary,
                'total_records': len(data),
                'action_plans_count': action_plans.count(),
                'wheels_count': wheels.count(),
                'report_type': 'Coaching por Beneficiária',
                'user': request.user
            }
            return ExportManager.export_to_pdf('core/exports/pdf_report.html', context, filename)
    except Exception as e:
        messages.error(request, f'Erro ao exportar dados: {str(e)}')
        return redirect('members:beneficiary_detail', pk=beneficiary.pk)
