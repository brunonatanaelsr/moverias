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
    """Lista de projetos com filtros e busca"""
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    projects = Project.objects.all().order_by('-created_at')
    
    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(coordinator__username__icontains=query)
        )
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Project.STATUS_CHOICES,
    }
    
    return render(request, 'projects/project_list.html', context)


@login_required
def project_detail(request, pk):
    """Detalhes de um projeto"""
    project = get_object_or_404(Project, pk=pk)
    
    # Estatísticas do projeto
    stats = {
        'total_enrollments': project.enrollments.count(),
        'active_enrollments': project.enrollments.filter(status='active').count(),
        'total_sessions': project.sessions.count(),
        'avg_attendance': project.sessions.aggregate(
            avg_attendance=Avg('attendances__count')
        )['avg_attendance'] or 0,
    }
    
    context = {
        'project': project,
        'stats': stats,
    }
    
    return render(request, 'projects/project_detail.html', context)


class ProjectCreateView(LoginRequiredMixin, StaffRequiredMixin, AuditMixin, CreateView):
    """View para criar projeto"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')
    
    def form_valid(self, form):
        form.instance.coordinator = self.request.user
        messages.success(self.request, 'Projeto criado com sucesso!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, StaffRequiredMixin, AuditMixin, UpdateView):
    """View para editar projeto"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('projects:project-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Projeto atualizado com sucesso!')
        return super().form_valid(form)


@login_required
def project_enrollment_list(request, project_pk):
    """Lista de inscrições de um projeto"""
    project = get_object_or_404(Project, pk=project_pk)
    enrollments = project.enrollments.all().order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(enrollments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'project': project,
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'projects/enrollment_list.html', context)


@login_required
def export_project_data(request, pk):
    """Exporta dados do projeto em CSV"""
    project = get_object_or_404(Project, pk=pk)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="projeto_{project.id}_dados.csv"'
    
    import csv
    writer = csv.writer(response)
    
    # Cabeçalho
    writer.writerow([
        'Beneficiária', 'Email', 'Telefone', 'Status', 
        'Data Inscrição', 'Total Sessões', 'Total Presenças'
    ])
    
    # Dados das inscrições
    for enrollment in project.enrollments.all():
        beneficiary = enrollment.beneficiary
        total_sessions = project.sessions.count()
        total_attendances = ProjectAttendance.objects.filter(
            enrollment=enrollment,
            present=True
        ).count()
        
        writer.writerow([
            beneficiary.full_name,
            beneficiary.email,
            beneficiary.phone_1,
            enrollment.get_status_display(),
            enrollment.created_at.strftime('%d/%m/%Y'),
            total_sessions,
            total_attendances,
        ])
    
    return response
