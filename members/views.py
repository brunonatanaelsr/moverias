from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count, Avg, Min, Max
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import csv
from core.unified_permissions import (
    is_technician, is_coordinator, TechnicianRequiredMixin, 
    CoordinatorRequiredMixin, requires_technician, requires_coordinator
)
from core.smart_cache import SmartCacheManager, list_cache, detail_cache
from .models import Beneficiary, Consent
from .forms import BeneficiaryForm
from workshops.models import WorkshopEnrollment
from projects.models import ProjectEnrollment
from social.models import SocialAnamnesis
from evolution.models import EvolutionRecord

# Dashboard view será definida no final do arquivo


class BeneficiaryListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
    """Lista de beneficiárias"""
    
    model = Beneficiary
    template_name = 'members/beneficiary_list.html'
    context_object_name = 'beneficiaries'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Query otimizada com prefetch para evitar N+1"""
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        # OTIMIZAÇÃO: prefetch_related para relacionamentos
        queryset = Beneficiary.objects.prefetch_related(
            'workshop_enrollments__workshop',
            'project_enrollments__project', 
            'evolution_records',
            'consents'
        ).annotate(
            workshop_count=Count('workshop_enrollments', distinct=True),
            project_count=Count('project_enrollments', distinct=True),
            evolution_count=Count('evolution_records', distinct=True)
        )
        
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
        
        # OTIMIZAÇÃO: Estatísticas com cache inteligente
        cache_key = SmartCacheManager.get_cache_key('stats', 'beneficiaries')
        stats = SmartCacheManager.get_cache(cache_key)
        if stats is None:
            stats = {
                'total_active': Beneficiary.objects.filter(status='ATIVA').count(),
                'total_inactive': Beneficiary.objects.filter(status='INATIVA').count()
            }
            SmartCacheManager.set_cache(cache_key, stats, 'short')
        
        context.update(stats)
        return context


class BeneficiaryDetailView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
    """Detalhes de uma beneficiária"""
    
    model = Beneficiary
    template_name = 'members/beneficiary_detail.html'
    context_object_name = 'beneficiary'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """OTIMIZAÇÃO: Query com prefetch_related para todos os relacionamentos"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"beneficiary_detail_{pk}"
        beneficiary = cache.get(cache_key)
        
        if beneficiary is None:
            beneficiary = get_object_or_404(
                Beneficiary.objects.prefetch_related(
                    'workshop_enrollments__workshop',
                    'project_enrollments__project',
                    'evolution_records',
                    'social_anamneses',
                    'consents'
                ),
                pk=pk
            )
            cache.set(cache_key, beneficiary, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return beneficiary
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Buscar matrículas em projetos com select_related
        context['project_enrollments'] = self.object.project_enrollments.select_related('project').all()
        
        # Buscar anamneses sociais com otimização (usando related_name correto)
        context['social_anamneses'] = self.object.social_anamneses.select_related('beneficiary').all()[:5]  # Últimas 5
        
        return context


class BeneficiaryCreateView(LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
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


class BeneficiaryUpdateView(LoginRequiredMixin, TechnicianRequiredMixin, UpdateView):
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


class BeneficiaryDeleteView(LoginRequiredMixin, TechnicianRequiredMixin, DeleteView):
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
@requires_technician
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


class BeneficiaryReportView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
    model = Beneficiary
    template_name = 'members/beneficiary_report.html'
    context_object_name = 'beneficiary'

    def test_func(self):
        return is_technician(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiary = self.object

        # Oficinas com select_related
        context['workshop_enrollments'] = WorkshopEnrollment.objects.filter(
            beneficiary=beneficiary
        ).select_related('workshop')
        
        # Projetos com select_related
        context['project_enrollments'] = ProjectEnrollment.objects.filter(
            beneficiary=beneficiary
        ).select_related('project')
        
        # Anamneses com select_related
        context['social_anamneses'] = SocialAnamnesis.objects.filter(
            beneficiary=beneficiary
        ).select_related('beneficiary')
        
        # Cadastro completo
        required_fields = ['full_name', 'dob', 'cpf', 'rg', 'address', 'neighbourhood', 'phone_1']
        missing_fields = [f for f in required_fields if not getattr(beneficiary, f, None)]
        context['missing_fields'] = missing_fields
        context['is_complete'] = not missing_fields
        
        # Vulnerabilidade (exemplo: renda, filhos, anamnese)
        # Busca a última anamnese social com otimização
        last_anamnesis = beneficiary.social_anamneses.order_by('-created_at').first() if hasattr(beneficiary, 'social_anamneses') else None
        vulnerable_keywords = ['vulnerabilidade', 'baixa renda', 'violência', 'risco', 'social', 'extrema', 'moradia', 'alimentação', 'desemprego']
        is_vulnerable = False
        if last_anamnesis and last_anamnesis.observations:
            is_vulnerable = any(kw in last_anamnesis.observations.lower() for kw in vulnerable_keywords)
        context['is_vulnerable'] = any([
            is_vulnerable,
            hasattr(beneficiary, 'number_of_children') and getattr(beneficiary, 'number_of_children', 0) >= 3,
            # Adapte conforme regras do sistema
        ])
        # Idade
        context['age'] = beneficiary.age if hasattr(beneficiary, 'age') else None
        # Localização
        context['address'] = beneficiary.address
        context['neighbourhood'] = beneficiary.neighbourhood
        # Número de filhos
        context['number_of_children'] = getattr(beneficiary, 'number_of_children', None)
        # Insights extras (exemplo: total de oficinas, projetos, frequência, etc)
        context['insights'] = {
            'total_workshops': context['workshop_enrollments'].count(),
            'total_projects': context['project_enrollments'].count(),
            'total_anamneses': context['social_anamneses'].count(),
            'is_active': beneficiary.status == 'ATIVA',
        }
        return context


class BeneficiaryReportDashboardView(LoginRequiredMixin, TechnicianRequiredMixin, TemplateView):
    template_name = 'members/beneficiary_report_dashboard.html'

    def test_func(self):
        return is_technician(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiaries = Beneficiary.objects.all()
        # Filtros
        status = self.request.GET.get('status', '')
        neighbourhood = self.request.GET.get('neighbourhood', '')
        min_age = self.request.GET.get('min_age', '')
        max_age = self.request.GET.get('max_age', '')
        vulnerability = self.request.GET.get('vulnerability', '')
        num_children = self.request.GET.get('num_children', '')

        # Função auxiliar para extrair número de filhos da última anamnese
        def get_children_count(beneficiary):
            anamneses = beneficiary.social_anamneses.order_by('-created_at')
            if anamneses.exists():
                # Tenta extrair número de filhos do campo family_members relacionado
                anamnese = anamneses.first()
                if hasattr(anamnese, 'family_members'):
                    return anamnese.family_members.filter(relationship='child').count()
            return 0

        # Adiciona atributo dinâmico para cada beneficiária
        for b in beneficiaries:
            b.number_of_children = get_children_count(b)

        # Aplicar filtros
        if status:
            beneficiaries = beneficiaries.filter(status=status)
        if neighbourhood:
            beneficiaries = beneficiaries.filter(neighbourhood__icontains=neighbourhood)
        if min_age:
            beneficiaries = [b for b in beneficiaries if hasattr(b, 'age') and b.age and b.age >= int(min_age)]
        if max_age:
            beneficiaries = [b for b in beneficiaries if hasattr(b, 'age') and b.age and b.age <= int(max_age)]
        if vulnerability == 'sim':
            beneficiaries = [b for b in beneficiaries if hasattr(b, 'social_anamneses') and b.social_anamneses.filter(vulnerability=True).exists()]
        if num_children:
            beneficiaries = [b for b in beneficiaries if getattr(b, 'number_of_children', 0) == int(num_children)]

        # Insights
        total = len(beneficiaries)
        total_active = Beneficiary.objects.filter(status='ATIVA').count()
        total_inactive = Beneficiary.objects.filter(status='INATIVA').count()
        avg_age = int(sum([b.age for b in beneficiaries if hasattr(b, 'age') and b.age]) / total) if total else 0
        min_age_val = min([b.age for b in beneficiaries if hasattr(b, 'age') and b.age], default=None)
        max_age_val = max([b.age for b in beneficiaries if hasattr(b, 'age') and b.age], default=None)
        neighbourhoods = Beneficiary.objects.values('neighbourhood').annotate(count=Count('id')).order_by('-count')
        # Distribuição de filhos (dinâmico)
        from collections import Counter
        children_counter = Counter([getattr(b, 'number_of_children', 0) for b in beneficiaries])
        children_dist = [
            {'number_of_children': k, 'count': v} for k, v in sorted(children_counter.items())
        ]
        # Para gráficos: distribuição por bairro, idade, filhos, status
        context.update({
            'beneficiaries': beneficiaries,
            'total': total,
            'total_active': total_active,
            'total_inactive': total_inactive,
            'avg_age': avg_age,
            'min_age': min_age_val,
            'max_age': max_age_val,
            'neighbourhoods': neighbourhoods,
            'children_dist': children_dist,
            'status_choices': Beneficiary.STATUS_CHOICES,
        })
        return context


@login_required
def beneficiary_complete_report(request, pk):
    """Relatório individual completo da beneficiária"""
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    
    # Anamnese Social mais recente
    latest_social_anamnesis = SocialAnamnesis.objects.filter(
        beneficiary=beneficiary
    ).order_by('-date').first()
    
    # Todas as anamneses sociais
    social_anamneses = SocialAnamnesis.objects.filter(
        beneficiary=beneficiary
    ).order_by('-date')
    
    # Evoluções/Atendimentos
    evolutions = EvolutionRecord.objects.filter(
        beneficiary=beneficiary
    ).order_by('-date')
    
    # Estatísticas de evoluções
    evolution_stats = {
        'total': evolutions.count(),
        'last_30_days': evolutions.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).count(),
        'last_3_months': evolutions.filter(
            date__gte=timezone.now().date() - timedelta(days=90)
        ).count(),
    }
    
    # Projetos da beneficiária
    project_participations = ProjectEnrollment.objects.filter(
        beneficiary=beneficiary
    ).select_related('project').order_by('-enrollment_date')
    
    # Estatísticas de projetos
    project_stats = {
        'total': project_participations.count(),
        'active': project_participations.filter(
            project__status='ACTIVE',
            status='ACTIVE'
        ).count(),
        'completed': project_participations.filter(
            status='COMPLETED'
        ).count(),
    }
    
    # Atividades de coaching - TEMPORARIAMENTE DESABILITADO
    # coaching_sessions = CoachingSession.objects.filter(
    #     beneficiary=beneficiary
    # ).order_by('-date')
    
    # Estatísticas de coaching
    coaching_stats = {
        'total': 0,  # coaching_sessions.count(),
        'last_30_days': 0,  # coaching_sessions.filter(
        #     date__gte=timezone.now().date() - timedelta(days=30)
        # ).count(),
        'avg_rating': 0,  # coaching_sessions.aggregate(
        #     avg_rating=Avg('satisfaction_rating')
        # )['avg_rating'] or 0,
    }
    
    # Termos de consentimento
    consents = Consent.objects.filter(beneficiary=beneficiary).order_by('-signed_at')
    
    # Timeline de atividades (últimas 20)
    timeline_activities = []
    
    # Adicionar evoluções ao timeline
    for evolution in evolutions[:10]:
        timeline_activities.append({
            'date': evolution.date,
            'type': 'evolution',
            'title': 'Atendimento/Evolução',
            'description': evolution.description[:100] + '...' if len(evolution.description) > 100 else evolution.description,
            'professional': evolution.professional.full_name if hasattr(evolution, 'professional') else 'N/A',
            'icon': 'medical-bag',
            'color': 'blue'
        })
    
    # Adicionar coaching ao timeline - TEMPORARIAMENTE DESABILITADO
    # for session in coaching_sessions[:10]:
    #     timeline_activities.append({
    #         'date': session.date,
    #         'type': 'coaching',
    #         'title': 'Sessão de Coaching',
    #         'description': session.notes[:100] + '...' if session.notes and len(session.notes) > 100 else session.notes or 'Sem observações',
    #         'professional': session.coach.full_name if hasattr(session, 'coach') else 'N/A',
    #         'icon': 'user-tie',
    #         'color': 'green'
    #     })
    
    # Adicionar participações em projetos ao timeline
    for participation in project_participations[:5]:
        timeline_activities.append({
            'date': participation.joined_at.date(),
            'type': 'project',
            'title': f'Projeto: {participation.project.name}',
            'description': f'Ingressou no projeto {participation.project.name}',
            'professional': 'Sistema',
            'icon': 'project-diagram',
            'color': 'purple'
        })
    
    # Ordenar timeline por data (mais recente primeiro)
    timeline_activities.sort(key=lambda x: x['date'], reverse=True)
    timeline_activities = timeline_activities[:20]  # Limitar a 20 itens
    
    # Indicadores de risco e alertas
    alerts = []
    
    # Verificar se tem atendimento recente
    if not evolutions.filter(date__gte=timezone.now().date() - timedelta(days=60)).exists():
        alerts.append({
            'type': 'warning',
            'title': 'Sem atendimento recente',
            'message': 'Beneficiária não tem evolução registrada nos últimos 60 dias',
            'icon': 'exclamation-triangle'
        })
    
    # Verificar idade
    if beneficiary.age < 18:
        alerts.append({
            'type': 'info',
            'title': 'Menor de idade',
            'message': 'Beneficiária é menor de idade, atenção especial aos protocolos',
            'icon': 'child'
        })
    elif beneficiary.age >= 60:
        alerts.append({
            'type': 'info',
            'title': 'Idosa',
            'message': 'Beneficiária é idosa, atenção especial aos cuidados',
            'icon': 'user-clock'
        })
    
    # Verificar consentimentos
    if not consents.filter(lgpd_agreement=True).exists():
        alerts.append({
            'type': 'danger',
            'title': 'LGPD não aceita',
            'message': 'Beneficiária não possui termo de consentimento LGPD assinado',
            'icon': 'shield-exclamation'
        })
    
    # Dados para gráficos
    chart_data = {
        'evolutions_by_month': {},
        'projects_progress': [],
        'coaching_satisfaction': []
    }
    
    # Evoluções por mês (últimos 12 meses)
    for i in range(12):
        month_start = (timezone.now().date() - relativedelta(months=i)).replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        
        count = evolutions.filter(
            date__gte=month_start,
            date__lte=month_end
        ).count()
        
        chart_data['evolutions_by_month'][month_start.strftime('%Y-%m')] = count
    
    # Progresso dos projetos
    for participation in project_participations:
        if hasattr(participation, 'progress_percentage'):
            chart_data['projects_progress'].append({
                'name': participation.project.name,
                'progress': participation.progress_percentage
            })
    
    # Satisfação do coaching - TEMPORARIAMENTE DESABILITADO
    # for session in coaching_sessions.filter(satisfaction_rating__isnull=False):
    #     chart_data['coaching_satisfaction'].append({
    #         'date': session.date.strftime('%Y-%m-%d'),
    #         'rating': session.satisfaction_rating
    #     })
    
    context = {
        'beneficiary': beneficiary,
        'latest_social_anamnesis': latest_social_anamnesis,
        'social_anamneses': social_anamneses[:5],  # Últimas 5
        'evolutions': evolutions[:10],  # Últimas 10
        'evolution_stats': evolution_stats,
        'project_participations': project_participations[:5],  # Últimos 5
        'project_stats': project_stats,
        'coaching_sessions': [],  # coaching_sessions[:10],  # Últimas 10 - TEMPORARIAMENTE DESABILITADO
        'coaching_stats': coaching_stats,
        'consents': consents,
        'timeline_activities': timeline_activities,
        'alerts': alerts,
        'chart_data': chart_data,
        'report_generated_at': timezone.now(),
    }
    
    return render(request, 'members/beneficiary_complete_report.html', context)

@login_required
def beneficiary_export_report(request, pk):
    """Exportar relatório completo da beneficiária para PDF"""
    # TODO: Implementar geração de PDF quando WeasyPrint estiver configurado
    pass


class BeneficiaryDashboardView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
    """Dashboard completo da beneficiária com integração de todos os módulos"""
    model = Beneficiary
    template_name = 'members/beneficiary_dashboard.html'
    context_object_name = 'beneficiary'
    
    def get_object(self, queryset=None):
        """Otimizar query com todos os relacionamentos"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(
            Beneficiary.objects.select_related().prefetch_related(
                'social_anamneses__vulnerabilities',
                'project_enrollments__project',
                'evolution_records',
                'action_plans',
                'wheel_of_life',
                'workshop_enrollments__workshop',
                'consents'
            ),
            pk=pk
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiary = self.object
        
        # Anamnese Social
        social_anamnesis = beneficiary.social_anamneses.filter(locked=True).first()
        context['social_anamnesis'] = social_anamnesis
        
        # Projetos
        active_projects = beneficiary.project_enrollments.filter(
            status='ACTIVE'
        ).select_related('project')
        context['active_projects'] = active_projects
        
        # Evoluções
        recent_evolutions = beneficiary.evolution_records.order_by('-date')[:10]
        context['recent_evolutions'] = recent_evolutions
        
        # Coaching
        coaching_plans = beneficiary.action_plans.filter(
            status='ACTIVE'
        ).order_by('-created_at')
        context['coaching_plans'] = coaching_plans
        
        # Workshops
        workshop_enrollments = beneficiary.workshop_enrollments.filter(
            status='ativo'
        ).select_related('workshop')
        context['workshop_enrollments'] = workshop_enrollments
        
        # Timeline unificado
        context['timeline'] = self.get_unified_timeline(beneficiary)
        
        # Alertas
        context['alerts'] = self.get_beneficiary_alerts(beneficiary)
        
        # Métricas
        context['metrics'] = self.get_beneficiary_metrics(beneficiary)
        
        # Próximas ações
        context['next_actions'] = self.get_next_actions(beneficiary)
        
        return context
    
    def get_unified_timeline(self, beneficiary):
        """Criar timeline unificado com todas as atividades"""
        timeline = []
        
        # Evoluções
        for evolution in beneficiary.evolution_records.all():
            timeline.append({
                'date': evolution.date,
                'datetime': datetime.combine(evolution.date, datetime.min.time()),
                'type': 'evolution',
                'title': 'Atendimento/Evolução',
                'description': evolution.description[:100] + '...' if len(evolution.description) > 100 else evolution.description,
                'module': 'evolution',
                'icon': 'fas fa-user-md',
                'color': '#3B82F6',  # Blue
                'url': f'/evolution/{evolution.id}/'
            })
        
        # Projetos
        for enrollment in beneficiary.project_enrollments.all():
            timeline.append({
                'date': enrollment.enrollment_date,
                'datetime': datetime.combine(enrollment.enrollment_date, datetime.min.time()),
                'type': 'project',
                'title': f'Projeto: {enrollment.project.name}',
                'description': f'Ingressou no projeto {enrollment.project.name}',
                'module': 'projects',
                'icon': 'fas fa-project-diagram',
                'color': '#10B981',  # Green
                'url': f'/projects/{enrollment.project.id}/'
            })
        
        # Coaching
        for plan in beneficiary.action_plans.all():
            timeline.append({
                'date': plan.created_at.date(),
                'datetime': plan.created_at,
                'type': 'coaching',
                'title': 'Plano de Ação',
                'description': plan.main_goal[:100] + '...' if len(plan.main_goal) > 100 else plan.main_goal,
                'module': 'coaching',
                'icon': 'fas fa-target',
                'color': '#8B5CF6',  # Purple
                'url': f'/coaching/action-plans/{plan.id}/'
            })
        
        # Roda da Vida
        for wheel in beneficiary.wheel_of_life.all():
            timeline.append({
                'date': wheel.date,
                'datetime': datetime.combine(wheel.date, datetime.min.time()),
                'type': 'wheel',
                'title': 'Roda da Vida',
                'description': 'Avaliação da roda da vida',
                'module': 'coaching',
                'icon': 'fas fa-circle-notch',
                'color': '#8B5CF6',  # Purple
                'url': f'/coaching/wheel-of-life/{wheel.id}/'
            })
        
        # Workshops
        for enrollment in beneficiary.workshop_enrollments.all():
            timeline.append({
                'date': enrollment.enrollment_date,
                'datetime': datetime.combine(enrollment.enrollment_date, datetime.min.time()),
                'type': 'workshop',
                'title': f'Workshop: {enrollment.workshop.name}',
                'description': f'Inscrita no workshop {enrollment.workshop.name}',
                'module': 'workshops',
                'icon': 'fas fa-chalkboard-teacher',
                'color': '#F59E0B',  # Orange
                'url': f'/workshops/{enrollment.workshop.id}/'
            })
        
        # Anamneses
        for anamnesis in beneficiary.social_anamneses.all():
            timeline.append({
                'date': anamnesis.created_at.date(),
                'datetime': anamnesis.created_at,
                'type': 'anamnesis',
                'title': 'Anamnese Social',
                'description': 'Anamnese social atualizada',
                'module': 'social',
                'icon': 'fas fa-clipboard-list',
                'color': '#EF4444',  # Red
                'url': f'/social/anamnesis/{anamnesis.id}/'
            })
        
        # Ordenar por data (mais recente primeiro)
        timeline.sort(key=lambda x: x['datetime'], reverse=True)
        
        return timeline[:20]  # Limitar a 20 itens
    
    def get_beneficiary_alerts(self, beneficiary):
        """Gerar alertas para a beneficiária"""
        alerts = []
        now = timezone.now()
        
        # Alerta de acompanhamento
        last_evolution = beneficiary.evolution_records.order_by('-date').first()
        if not last_evolution or (now.date() - last_evolution.date).days > 30:
            alerts.append({
                'type': 'warning',
                'title': 'Sem acompanhamento recente',
                'message': 'Beneficiária sem evolução registrada há mais de 30 dias',
                'action_url': f'/evolution/create/?beneficiary={beneficiary.pk}',
                'action_text': 'Registrar Evolução',
                'priority': 'high',
                'icon': 'fas fa-exclamation-triangle'
            })
        
        # Alerta de anamnese
        if not beneficiary.social_anamneses.filter(locked=True).exists():
            alerts.append({
                'type': 'info',
                'title': 'Anamnese Social pendente',
                'message': 'Anamnese social não foi finalizada',
                'action_url': f'/social/anamnesis/new/{beneficiary.pk}/',
                'action_text': 'Finalizar Anamnese',
                'priority': 'medium',
                'icon': 'fas fa-clipboard-list'
            })
        
        # Alerta de idade
        if beneficiary.age < 18:
            alerts.append({
                'type': 'info',
                'title': 'Menor de idade',
                'message': 'Beneficiária é menor de idade - atenção especial aos protocolos',
                'priority': 'medium',
                'icon': 'fas fa-child'
            })
        elif beneficiary.age >= 60:
            alerts.append({
                'type': 'info',
                'title': 'Idosa',
                'message': 'Beneficiária é idosa - atenção especial aos cuidados',
                'priority': 'medium',
                'icon': 'fas fa-user-clock'
            })
        
        # Alerta de LGPD
        if not beneficiary.consents.filter(lgpd_agreement=True).exists():
            alerts.append({
                'type': 'danger',
                'title': 'LGPD não aceita',
                'message': 'Beneficiária não possui termo de consentimento LGPD assinado',
                'priority': 'high',
                'icon': 'fas fa-shield-exclamation'
            })
        
        # Alerta de projetos inativos
        if not beneficiary.project_enrollments.filter(status='ACTIVE').exists():
            alerts.append({
                'type': 'warning',
                'title': 'Sem projetos ativos',
                'message': 'Beneficiária não está participando de nenhum projeto',
                'action_url': f'/projects/enrollment/create/?beneficiary={beneficiary.pk}',
                'action_text': 'Inscrever em Projeto',
                'priority': 'medium',
                'icon': 'fas fa-project-diagram'
            })
        
        return alerts
    
    def get_beneficiary_metrics(self, beneficiary):
        """Calcular métricas da beneficiária"""
        now = timezone.now()
        
        # Métricas de engajamento
        total_activities = (
            beneficiary.evolution_records.count() +
            beneficiary.project_enrollments.count() +
            beneficiary.action_plans.count() +
            beneficiary.workshop_enrollments.count()
        )
        
        # Última atividade
        last_activities = []
        if beneficiary.evolution_records.exists():
            last_activities.append(beneficiary.evolution_records.order_by('-date').first().date)
        if beneficiary.project_enrollments.exists():
            last_activities.append(beneficiary.project_enrollments.order_by('-enrollment_date').first().enrollment_date)
        if beneficiary.action_plans.exists():
            last_activities.append(beneficiary.action_plans.order_by('-created_at').first().created_at.date())
        
        last_activity = max(last_activities) if last_activities else None
        
        # Métricas de progresso
        completed_projects = beneficiary.project_enrollments.filter(status='COMPLETED').count()
        total_projects = beneficiary.project_enrollments.count()
        
        # Frequência de evolução
        evolution_last_30_days = beneficiary.evolution_records.filter(
            date__gte=now.date() - timedelta(days=30)
        ).count()
        
        # Dias desde última atividade
        inactive_days = 0
        if last_activity:
            inactive_days = (now.date() - last_activity).days
        
        return {
            'engagement': {
                'total_activities': total_activities,
                'last_activity': last_activity,
                'inactive_days': inactive_days,
                'evolution_last_30_days': evolution_last_30_days,
            },
            'progress': {
                'completed_projects': completed_projects,
                'total_projects': total_projects,
                'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0,
                'active_projects': beneficiary.project_enrollments.filter(status='ACTIVE').count(),
            },
            'coaching': {
                'active_plans': beneficiary.action_plans.filter(status='ACTIVE').count(),
                'total_plans': beneficiary.action_plans.count(),
                'wheel_assessments': beneficiary.wheel_of_life.count(),
            },
            'workshops': {
                'active_enrollments': beneficiary.workshop_enrollments.filter(status='ativo').count(),
                'total_enrollments': beneficiary.workshop_enrollments.count(),
            }
        }
    
    def get_next_actions(self, beneficiary):
        """Sugerir próximas ações para a beneficiária"""
        actions = []
        
        # Se não tem anamnese finalizada
        if not beneficiary.social_anamneses.filter(locked=True).exists():
            actions.append({
                'title': 'Finalizar Anamnese Social',
                'description': 'Complete a anamnese social para melhor acompanhamento',
                'url': f'/social/anamnesis/new/{beneficiary.pk}/',
                'icon': 'fas fa-clipboard-list',
                'color': 'red',
                'priority': 1
            })
        
        # Se não tem evolução recente
        last_evolution = beneficiary.evolution_records.order_by('-date').first()
        if not last_evolution or (timezone.now().date() - last_evolution.date).days > 30:
            actions.append({
                'title': 'Registrar Evolução',
                'description': 'Registre o progresso e observações da beneficiária',
                'url': f'/evolution/create/?beneficiary={beneficiary.pk}',
                'icon': 'fas fa-chart-line',
                'color': 'blue',
                'priority': 2
            })
        
        # Se não tem projetos ativos
        if not beneficiary.project_enrollments.filter(status='ACTIVE').exists():
            actions.append({
                'title': 'Inscrever em Projeto',
                'description': 'Inscreva a beneficiária em um projeto adequado',
                'url': f'/projects/enrollment/create/?beneficiary={beneficiary.pk}',
                'icon': 'fas fa-project-diagram',
                'color': 'green',
                'priority': 3
            })
        
        # Se não tem plano de ação
        if not beneficiary.action_plans.filter(status='ACTIVE').exists():
            actions.append({
                'title': 'Criar Plano de Ação',
                'description': 'Desenvolva um plano de ação personalizado',
                'url': f'/coaching/action-plans/create/?beneficiary={beneficiary.pk}',
                'icon': 'fas fa-target',
                'color': 'purple',
                'priority': 4
            })
        
        # Se não tem avaliação roda da vida recente
        recent_wheel = beneficiary.wheel_of_life.filter(
            date__gte=timezone.now().date() - timedelta(days=180)
        ).exists()
        if not recent_wheel:
            actions.append({
                'title': 'Avaliar Roda da Vida',
                'description': 'Realize uma avaliação da roda da vida',
                'url': f'/coaching/wheel-of-life/create/?beneficiary={beneficiary.pk}',
                'icon': 'fas fa-circle-notch',
                'color': 'purple',
                'priority': 5
            })
        
        return sorted(actions, key=lambda x: x['priority'])[:5]
