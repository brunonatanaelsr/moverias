from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count
from .models import Project, ProjectEnrollment
from .forms import ProjectForm, ProjectEnrollmentForm
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


# CRUD Views for Project Model

class ProjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Project
    template_name = 'projects/project_master_list.html'
    context_object_name = 'projects'
    paginate_by = 15

    def test_func(self):
        return is_technician(self.request.user)

    def get_queryset(self):
        queryset = Project.objects.all()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
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
