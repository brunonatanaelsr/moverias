from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count, Avg, Min, Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Beneficiary, Consent
from .forms import BeneficiaryForm
from workshops.models import WorkshopEnrollment
from projects.models import ProjectEnrollment
from social.models import SocialAnamnesis


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


class BeneficiaryReportView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Beneficiary
    template_name = 'members/beneficiary_report.html'
    context_object_name = 'beneficiary'

    def test_func(self):
        return is_technician(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiary = self.object

        # Oficinas
        context['workshop_enrollments'] = WorkshopEnrollment.objects.filter(beneficiary=beneficiary).select_related('workshop')
        # Projetos
        context['project_enrollments'] = ProjectEnrollment.objects.filter(beneficiary=beneficiary).select_related('project')
        # Anamneses
        context['social_anamneses'] = SocialAnamnesis.objects.filter(beneficiary=beneficiary)
        # Cadastro completo
        required_fields = ['full_name', 'dob', 'cpf', 'rg', 'address', 'neighbourhood', 'phone_1']
        missing_fields = [f for f in required_fields if not getattr(beneficiary, f, None)]
        context['missing_fields'] = missing_fields
        context['is_complete'] = not missing_fields
        # Vulnerabilidade (exemplo: renda, filhos, anamnese)
        # Busca a última anamnese social
        last_anamnesis = beneficiary.social_anamnesis.order_by('-date').first() if hasattr(beneficiary, 'social_anamnesis') else None
        vulnerable_keywords = ['vulnerabilidade', 'baixa renda', 'violência', 'risco', 'social', 'extrema', 'moradia', 'alimentação', 'desemprego']
        is_vulnerable = False
        if last_anamnesis and last_anamnesis.vulnerabilities:
            is_vulnerable = any(kw in last_anamnesis.vulnerabilities.lower() for kw in vulnerable_keywords)
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


class BeneficiaryReportDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
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
            anamneses = beneficiary.social_anamnesis.order_by('-date')
            if anamneses.exists():
                # Tenta extrair número de filhos do campo family_composition (ex: "Filhos: 2")
                import re
                texto = anamneses.first().family_composition or ''
                match = re.search(r'filh[oa]s?:?\s*(\d+)', texto, re.IGNORECASE)
                if match:
                    return int(match.group(1))
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
            beneficiaries = [b for b in beneficiaries if hasattr(b, 'social_anamnesis') and b.social_anamnesis.filter(vulnerability=True).exists()]
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

# Nenhuma alteração de backend é necessária para adicionar um botão de navegação para a página de relatórios.
# A alteração deve ser feita no template 'members/beneficiary_list.html', adicionando um botão/link para a view 'BeneficiaryReportDashboardView'.
# Exemplo de código a ser adicionado ao template:
# <a href="{% url 'members:beneficiary-report-dashboard' %}" class="btn btn-primary mb-3">Relatórios das Beneficiárias</a>
