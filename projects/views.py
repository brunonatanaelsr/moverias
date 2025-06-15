from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count
from .models import ProjectEnrollment
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class ProjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de projetos e matrículas"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Query otimizada com cache e filtros múltiplos"""
        search = self.request.GET.get('search', '')
        project_name = self.request.GET.get('project_name', '')
        status = self.request.GET.get('status', '')
        
        # Cache key baseada nos filtros
        cache_key = f"projects_list_{search}_{project_name}_{status}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = ProjectEnrollment.objects.select_related(
                'beneficiary'
            )
            
            if search:
                queryset = queryset.filter(
                    Q(beneficiary__full_name__icontains=search) |
                    Q(project_name__icontains=search)
                )
            
            if project_name:
                queryset = queryset.filter(project_name__icontains=project_name)
            
            if status:
                queryset = queryset.filter(status=status)
            
            queryset = queryset.order_by('-created_at')
            
            # Cache por tempo médio (30 minutos)
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['MEDIUM'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dados para filtros
        context['project_names'] = ProjectEnrollment.objects.values_list(
            'project_name', flat=True
        ).distinct().order_by('project_name')
        
        context['status_choices'] = ProjectEnrollment.STATUS_CHOICES if hasattr(ProjectEnrollment, 'STATUS_CHOICES') else []
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de uma matrícula em projeto"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_detail.html'
    context_object_name = 'enrollment'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"project_enrollment_{pk}"
        enrollment = cache.get(cache_key)
        
        if enrollment is None:
            enrollment = ProjectEnrollment.objects.select_related(
                'beneficiary'
            ).get(pk=pk)
            cache.set(cache_key, enrollment, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return enrollment


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar nova matrícula em projeto"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_form.html'
    fields = ['beneficiary', 'project_name', 'weekday', 'shift', 'start_time']
    success_url = reverse_lazy('projects:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_form(self, form_class=None):
        """Otimizar queryset das beneficiárias no formulário"""
        form = super().get_form(form_class)
        if 'beneficiary' in form.fields:
            form.fields['beneficiary'].queryset = Beneficiary.objects.order_by('full_name')
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Invalidar caches relacionados de forma mais simples
        cache_keys = [
            f"projects_list__{form.instance.project_name}_",
            f"projects_list___{getattr(form.instance, 'status', '')}",
            "projects_list___"
        ]
        cache.delete_many(cache_keys)
        
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} criada com sucesso!')
        return response


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar matrícula em projeto"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_form.html'
    fields = ['beneficiary', 'project_name', 'weekday', 'shift', 'start_time', 'status']
    success_url = reverse_lazy('projects:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"project_enrollment_{pk}"
        enrollment = cache.get(cache_key)
        
        if enrollment is None:
            enrollment = ProjectEnrollment.objects.select_related(
                'beneficiary'
            ).get(pk=pk)
            cache.set(cache_key, enrollment, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return enrollment
    
    def get_form(self, form_class=None):
        """Otimizar queryset das beneficiárias no formulário"""
        form = super().get_form(form_class)
        if 'beneficiary' in form.fields:
            form.fields['beneficiary'].queryset = Beneficiary.objects.order_by('full_name')
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Invalidar caches
        cache.delete(f"project_enrollment_{self.object.pk}")
        cache_keys = [
            f"projects_list__{form.instance.project_name}_",
            "projects_list___"
        ]
        cache.delete_many(cache_keys)
        
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} atualizada com sucesso!')
        return response
    template_name = 'projects/project_form.html'
    fields = ['project_name', 'weekday', 'shift', 'start_time', 'status']
    success_url = reverse_lazy('projects:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} atualizada com sucesso!')
        return response


class ProjectEnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar nova matrícula (alias para ProjectCreateView)"""
    
    model = ProjectEnrollment
    template_name = 'projects/enrollment_form.html'
    fields = ['beneficiary', 'project_name', 'weekday', 'shift', 'start_time']
    success_url = reverse_lazy('projects:list')
    
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
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} criada com sucesso!')
        return response


class ProjectEnrollmentDetailView(ProjectDetailView):
    """Alias para ProjectDetailView"""
    template_name = 'projects/enrollment_detail.html'


class ProjectEnrollmentUpdateView(ProjectUpdateView):
    """Alias para ProjectUpdateView"""
    template_name = 'projects/enrollment_form.html'
