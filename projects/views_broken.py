"""
Views para o módulo de projetos
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Project, ProjectEnrollment, ProjectSession, ProjectAttendance, ProjectEvaluation, ProjectResource
from .forms import ProjectForm, ProjectEnrollmentForm, ProjectSessionForm, ProjectEvaluationForm
from members.models import Beneficiary
from core.mixins import AuditMixin, StaffRequiredMixin, MessageMixin


@login_required
def project_list(request):
from django.core.exceptions import ValidationError

from .models import Project, ProjectEnrollment, ProjectSession, ProjectAttendance, ProjectEvaluation, ProjectResource
from .forms import ProjectForm, ProjectEnrollmentForm, ProjectSessionForm, ProjectEvaluationForm
from members.models import Beneficiary
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    FormView, TemplateView
)
from datetime import datetime, timedelta
import json
import csv

from .models import (
    Project, ProjectEnrollment, ProjectSession, ProjectAttendance,
    ProjectEvaluation, ProjectResource
)
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class ProjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de projetos"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Filtra projetos com busca"""
        qs = Project.objects.all()
        
        # Busca por nome
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(coordinator__icontains=search)
            )
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Project.STATUS_CHOICES
        return context


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de um projeto"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Estatísticas do projeto
        context['total_participants'] = project.total_participants
        context['total_sessions'] = project.total_sessions
        context['attendance_rate'] = project.attendance_rate
        context['completion_rate'] = project.get_completion_rate()
        
        # Próximas sessões
        context['upcoming_sessions'] = project.sessions.filter(
            session_date__gte=timezone.now().date()
        ).order_by('session_date', 'start_time')[:5]
        
        # Participantes ativos
        context['active_participants'] = project.get_active_participants()[:10]
        
        # Recursos do projeto
        context['resources'] = project.resources.all()[:5]
        
        return context


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar novo projeto"""
    model = Project
    fields = ['name', 'description', 'coordinator', 'location', 'start_date', 'end_date', 'status', 'max_participants', 'objectives', 'target_audience']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Projeto criado com sucesso!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar projeto"""
    model = Project
    fields = ['name', 'description', 'coordinator', 'location', 'start_date', 'end_date', 'status', 'max_participants', 'objectives', 'target_audience']
    template_name = 'projects/project_form.html'

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Projeto atualizado com sucesso!')
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Deletar projeto"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        return is_technician(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Projeto deletado com sucesso!')
        return super().delete(request, *args, **kwargs)


class ProjectEnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de inscrições em projetos"""
    model = ProjectEnrollment
    template_name = 'projects/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Filtra inscrições"""
        qs = ProjectEnrollment.objects.select_related('project', 'beneficiary')
        
        # Filtro por projeto
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(status='ATIVO')
        context['status_choices'] = ProjectEnrollment.STATUS_CHOICES
        return context


class ProjectSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de sessões de projeto"""
    model = ProjectSession
    template_name = 'projects/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Filtra sessões"""
        qs = ProjectSession.objects.select_related('project')
        
        # Filtro por projeto
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        
        # Filtro por data
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(session_date__gte=date_from)
        if date_to:
            qs = qs.filter(session_date__lte=date_to)
        
        return qs.order_by('-session_date', '-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(status='ATIVO')
        return context


class ProjectDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard de projetos"""
    template_name = 'projects/dashboard.html'

    def test_func(self):
        return is_technician(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        context['total_projects'] = Project.objects.count()
        context['active_projects'] = Project.objects.filter(status='ATIVO').count()
        context['total_participants'] = ProjectEnrollment.objects.filter(
            status='ATIVO'
        ).count()
        context['total_sessions'] = ProjectSession.objects.count()
        
        # Projetos por status
        context['projects_by_status'] = Project.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Sessões desta semana
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        context['sessions_this_week'] = ProjectSession.objects.filter(
            session_date__range=[week_start, week_end]
        ).select_related('project').order_by('session_date', 'start_time')
        
        return context


@login_required
def project_analytics(request, project_id):
    """Analytics de um projeto específico"""
    if not is_technician(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('core:home')
    
    project = get_object_or_404(Project, id=project_id)
    
    # Estatísticas básicas
    data = {
        'project_name': project.name,
        'total_participants': project.total_participants,
        'total_sessions': project.total_sessions,
        'attendance_rate': project.attendance_rate,
        'completion_rate': project.get_completion_rate(),
    }
    
    # Presença por sessão
    sessions_data = []
    for session in project.sessions.all():
        sessions_data.append({
            'date': session.session_date.strftime('%Y-%m-%d'),
            'topic': session.topic,
            'attendance_count': session.attendance_count,
            'attendance_percentage': session.attendance_percentage,
        })
    
    data['sessions'] = sessions_data
    
    # Avaliações
    evaluations = ProjectEvaluation.objects.filter(
        enrollment__project=project
    ).aggregate(
        avg_rating=Avg('rating'),
        avg_content=Avg('content_quality'),
        avg_facilitator=Avg('facilitator_rating'),
        total_evaluations=Count('id')
    )
    
    data['evaluations'] = evaluations
    
    return JsonResponse(data)


@login_required
def export_project_data(request, project_id):
    """Exportar dados do projeto"""
    if not is_technician(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('core:home')
    
    project = get_object_or_404(Project, id=project_id)
    format_type = request.GET.get('format', 'csv')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{project.name}_participantes.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Nome', 'Projeto', 'Status', 'Data de Inscrição', 
            'Taxa de Presença'
        ])
        
        for enrollment in project.enrollments.all():
            writer.writerow([
                enrollment.beneficiary.full_name,
                enrollment.project.name,
                enrollment.get_status_display(),
                enrollment.created_at.strftime('%d/%m/%Y'),
                f"{enrollment.attendance_rate:.1f}%" if hasattr(enrollment, 'attendance_rate') else "N/A"
            ])
        
        return response
    
    return JsonResponse({'error': 'Formato não suportado'}, status=400)


@login_required
def project_calendar(request):
    """Calendário de sessões dos projetos"""
    if not is_technician(request.user):
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    # Buscar sessões do mês atual
    today = timezone.now().date()
    month_start = today.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)
    
    sessions = ProjectSession.objects.filter(
        session_date__range=[month_start, month_end]
    ).select_related('project')
    
    # Preparar dados para o calendário
    calendar_data = []
    for session in sessions:
        calendar_data.append({
            'id': session.id,
            'title': f"{session.project.name} - {session.topic}",
            'start': f"{session.session_date}T{session.start_time}",
            'end': f"{session.session_date}T{session.end_time}",
            'url': f"/projects/sessions/{session.id}/",
        })
    
    return JsonResponse(calendar_data, safe=False)

    def get_queryset(self):
        """Filtra projetos com busca e filtros"""
        qs = Project.objects.all()
        
        # Busca
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(coordinator__icontains=search)
            )
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Project.STATUS_CHOICES
        
        # Estatísticas
        context['total_projects'] = Project.objects.count()
        context['active_projects'] = Project.objects.filter(status='ATIVO').count()
        context['completed_projects'] = Project.objects.filter(status='CONCLUIDO').count()
        
        return context


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Projeto "{form.instance.name}" criado com sucesso!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Projeto "{form.instance.name}" atualizado com sucesso!')
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project-list')

    def test_func(self):
        return is_technician(self.request.user)

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        if project.enrollments.exists():
            messages.error(request, f'Não é possível excluir o projeto "{project.name}" pois existem matrículas associadas a ele.')
            return redirect('projects:project-list')
        
        project_name = project.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f'Projeto "{project_name}" excluído com sucesso!')
        return response


# CRUD Views for ProjectEnrollment Model

class ProjectEnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProjectEnrollment
    template_name = 'projects/project_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        search = self.request.GET.get('search', '')
        project_filter = self.request.GET.get('project', '')
        status = self.request.GET.get('status', '')
        
        cache_key = f"project_enrollments_list_{search}_{project_filter}_{status}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = ProjectEnrollment.objects.select_related('beneficiary', 'project')
            
            if search:
                queryset = queryset.filter(
                    Q(beneficiary__full_name__icontains=search) |
                    Q(project__name__icontains=search)
                )
            
            if project_filter:
                queryset = queryset.filter(project_id=project_filter)
            
            if status:
                queryset = queryset.filter(status=status)
            
            queryset = queryset.order_by('-created_at', 'project__name')
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['MEDIUM'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.all().order_by('name')
        context['status_choices'] = ProjectEnrollment.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_project'] = self.request.GET.get('project', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ProjectEnrollmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ProjectEnrollment
    template_name = 'projects/project_detail.html'
    context_object_name = 'enrollment'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"project_enrollment_detail_{pk}"
        enrollment = cache.get(cache_key)
        
        if enrollment is None:
            enrollment = ProjectEnrollment.objects.select_related('beneficiary', 'project').get(pk=pk)
            cache.set(cache_key, enrollment, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return enrollment


class ProjectEnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProjectEnrollment
    form_class = ProjectEnrollmentForm
    template_name = 'projects/project_enrollment_form.html'
    success_url = reverse_lazy('projects:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not Project.objects.exists():
            messages.warning(self.request, "Não existem projetos cadastrados. Crie um projeto antes de realizar matrículas.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} no projeto "{form.instance.project.name}" criada com sucesso!')
        # Clear cache using pattern matching - production safe
        self.clear_project_cache()
        return response
    
    def clear_project_cache(self):
        """Clear project-related cache entries in a production-safe way"""
        try:
            # Clear specific cache patterns
            cache.delete_many([
                'project_enrollments_list_',
                'project_enrollments_list_active',
                'project_enrollments_list_inactive',
                'project_enrollments_list_pending'
            ])
        except Exception:
            # Fallback: clear all cache if pattern deletion fails
            cache.clear()


class ProjectEnrollmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ProjectEnrollment
    form_class = ProjectEnrollmentForm
    template_name = 'projects/project_enrollment_form.html'
    success_url = reverse_lazy('projects:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"project_enrollment_detail_{pk}"
        enrollment = cache.get(cache_key)
        if enrollment is None:
            enrollment = ProjectEnrollment.objects.select_related('beneficiary', 'project').get(pk=pk)
            cache.set(cache_key, enrollment, settings.CACHE_TIMEOUT['MEDIUM'])
        return enrollment

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} no projeto "{form.instance.project.name}" atualizada com sucesso!')
        cache.delete(f"project_enrollment_detail_{self.object.pk}")
        self.clear_project_cache()
        return response
    
    def clear_project_cache(self):
        """Clear project-related cache entries in a production-safe way"""
        try:
            # Clear specific cache patterns
            cache.delete_many([
                'project_enrollments_list_',
                'project_enrollments_list_active',
                'project_enrollments_list_inactive',
                'project_enrollments_list_pending'
            ])
        except Exception:
            # Fallback: clear all cache if pattern deletion fails
            cache.clear()


class ProjectEnrollmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProjectEnrollment
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def delete(self, request, *args, **kwargs):
        enrollment = self.get_object()
        beneficiary_name = enrollment.beneficiary.full_name
        project_name = enrollment.project.name

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Matrícula de {beneficiary_name} no projeto "{project_name}" excluída com sucesso!')
        self.clear_project_cache()
        return response
    
    def clear_project_cache(self):
        """Clear project-related cache entries in a production-safe way"""
        try:
            # Clear specific cache patterns
            cache.delete_many([
                'project_enrollments_list_',
                'project_enrollments_list_active',
                'project_enrollments_list_inactive',
                'project_enrollments_list_pending'
            ])
        except Exception:
            # Fallback: clear all cache if pattern deletion fails
            cache.clear()
