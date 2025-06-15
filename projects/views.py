from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
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
        queryset = super().get_queryset().select_related('beneficiary')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                beneficiary__full_name__icontains=search
            )
        return queryset.order_by('-created_at')


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de uma matrícula em projeto"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_detail.html'
    context_object_name = 'enrollment'
    
    def test_func(self):
        return is_technician(self.request.user)


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar nova matrícula em projeto"""
    
    model = ProjectEnrollment
    template_name = 'projects/project_form.html'
    fields = ['beneficiary', 'project_name', 'weekday', 'shift', 'start_time']
    success_url = reverse_lazy('projects:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} criada com sucesso!')
        return response


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar matrícula em projeto"""
    
    model = ProjectEnrollment
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
