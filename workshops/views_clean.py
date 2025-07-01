# filepath: /Users/brunonatanael/Desktop/MoveMarias/02/workshops/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count, Avg, Prefetch
from django.utils import timezone
from django.http import JsonResponse
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
from .forms import (
    WorkshopForm, WorkshopSessionForm, WorkshopEnrollmentForm, 
    SessionAttendanceForm, WorkshopEvaluationForm, BulkAttendanceForm
)
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


# CRUD Views for Workshop Model

class WorkshopListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Workshop
    template_name = 'workshops/workshop_list.html'
    context_object_name = 'workshops'
    paginate_by = 15

    def test_func(self):
        return is_technician(self.request.user)

    def get_queryset(self):
        queryset = Workshop.objects.annotate(
            participant_count=Count('enrollments', filter=Q(enrollments__status='ativo'))
        )
        
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        workshop_type = self.request.GET.get('type', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(facilitator__icontains=search) |
                Q(description__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
            
        if workshop_type:
            queryset = queryset.filter(workshop_type=workshop_type)
        
        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workshop_types'] = Workshop.WORKSHOP_TYPES
        context['status_choices'] = Workshop.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('type', '')
        return context


class WorkshopDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Workshop
    template_name = 'workshops/workshop_detail.html'
    context_object_name = 'workshop'

    def test_func(self):
        return is_technician(self.request.user)

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"workshop_detail_{pk}"
        workshop = cache.get(cache_key)
        
        if workshop is None:
            workshop = Workshop.objects.prefetch_related(
                Prefetch('sessions', queryset=WorkshopSession.objects.order_by('session_date')),
                Prefetch('enrollments', queryset=WorkshopEnrollment.objects.select_related('beneficiary').filter(status='ativo'))
            ).get(pk=pk)
            
            cache.set(cache_key, workshop, settings.CACHE_TIMEOUT['LONG'])
        
        return workshop

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop = self.get_object()
        
        context['sessions'] = workshop.sessions.all()
        context['enrollments'] = workshop.enrollments.all()
        
        # Avaliações recentes
        recent_evaluations = WorkshopEvaluation.objects.select_related(
            'enrollment__beneficiary'
        ).filter(
            enrollment__workshop=workshop
        ).order_by('-evaluation_date')[:5]
        
        context['recent_evaluations'] = recent_evaluations
        context['average_rating'] = WorkshopEvaluation.objects.filter(
            enrollment__workshop=workshop
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        return context


class WorkshopCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Workshop
    form_class = WorkshopForm
    template_name = 'workshops/workshop_form.html'
    success_url = reverse_lazy('workshops:workshop-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Oficina "{form.instance.name}" criada com sucesso!')
        return super().form_valid(form)


class WorkshopUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Workshop
    form_class = WorkshopForm
    template_name = 'workshops/workshop_form.html'
    success_url = reverse_lazy('workshops:workshop-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Oficina "{form.instance.name}" atualizada com sucesso!')
        cache.delete(f"workshop_detail_{self.object.pk}")
        return super().form_valid(form)


class WorkshopDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Workshop
    template_name = 'workshops/workshop_confirm_delete.html'
    success_url = reverse_lazy('workshops:workshop-list')

    def test_func(self):
        return is_technician(self.request.user)

    def delete(self, request, *args, **kwargs):
        workshop = self.get_object()
        if workshop.enrollments.exists():
            messages.error(request, f'Não é possível excluir a oficina "{workshop.name}" pois existem matrículas associadas a ela.')
            return redirect('workshops:workshop-list')
        
        workshop_name = workshop.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f'Oficina "{workshop_name}" excluída com sucesso!')
        return response


# CRUD Views for WorkshopEnrollment Model

class WorkshopEnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = WorkshopEnrollment
    template_name = 'workshops/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        search = self.request.GET.get('search', '')
        workshop_filter = self.request.GET.get('workshop', '')
        status = self.request.GET.get('status', '')
        
        queryset = WorkshopEnrollment.objects.select_related('beneficiary', 'workshop')
        
        if search:
            queryset = queryset.filter(
                Q(beneficiary__full_name__icontains=search) |
                Q(workshop__name__icontains=search)
            )
        
        if workshop_filter:
            queryset = queryset.filter(workshop_id=workshop_filter)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-enrollment_date', 'workshop__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workshops'] = Workshop.objects.all().order_by('name')
        context['status_choices'] = WorkshopEnrollment.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_workshop'] = self.request.GET.get('workshop', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class WorkshopEnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = WorkshopEnrollment
    form_class = WorkshopEnrollmentForm
    template_name = 'workshops/enrollment_form.html'
    success_url = reverse_lazy('workshops:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not Workshop.objects.filter(status__in=['planejamento', 'ativo']).exists():
            messages.warning(self.request, "Não existem oficinas ativas. Crie uma oficina antes de realizar matrículas.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} na oficina "{form.instance.workshop.name}" criada com sucesso!')
        return response


class WorkshopEnrollmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WorkshopEnrollment
    form_class = WorkshopEnrollmentForm
    template_name = 'workshops/enrollment_form.html'
    success_url = reverse_lazy('workshops:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} na oficina "{form.instance.workshop.name}" atualizada com sucesso!')
        return response


class WorkshopEnrollmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = WorkshopEnrollment
    template_name = 'workshops/enrollment_confirm_delete.html'
    success_url = reverse_lazy('workshops:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def delete(self, request, *args, **kwargs):
        enrollment = self.get_object()
        beneficiary_name = enrollment.beneficiary.full_name
        workshop_name = enrollment.workshop.name

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Matrícula de {beneficiary_name} na oficina "{workshop_name}" excluída com sucesso!')
        return response


# CRUD Views for WorkshopSession Model

class WorkshopSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = WorkshopSession
    template_name = 'workshops/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        workshop_filter = self.request.GET.get('workshop', '')
        
        queryset = WorkshopSession.objects.select_related('workshop')
        
        if workshop_filter:
            queryset = queryset.filter(workshop_id=workshop_filter)
        
        return queryset.order_by('-session_date', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workshops'] = Workshop.objects.filter(status__in=['ativo', 'planejamento']).order_by('name')
        context['selected_workshop'] = self.request.GET.get('workshop', '')
        return context


class WorkshopSessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = WorkshopSession
    form_class = WorkshopSessionForm
    template_name = 'workshops/session_form.html'
    success_url = reverse_lazy('workshops:session-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sessão da oficina "{form.instance.workshop.name}" criada com sucesso!')
        return response


class WorkshopSessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WorkshopSession
    form_class = WorkshopSessionForm
    template_name = 'workshops/session_form.html'
    success_url = reverse_lazy('workshops:session-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Sessão da oficina "{form.instance.workshop.name}" atualizada com sucesso!')
        return response


class WorkshopSessionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = WorkshopSession
    template_name = 'workshops/session_confirm_delete.html'
    success_url = reverse_lazy('workshops:session-list')

    def test_func(self):
        return is_technician(self.request.user)

    def delete(self, request, *args, **kwargs):
        session = self.get_object()
        workshop_name = session.workshop.name

        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Sessão da oficina "{workshop_name}" excluída com sucesso!')
        return response


# Views for Attendance Management

@login_required
@user_passes_test(is_technician)
def bulk_attendance(request, session_id):
    """View para registro em massa de presenças"""
    session = get_object_or_404(WorkshopSession, id=session_id)
    
    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST, session=session)
        if form.is_valid():
            # Processar presenças
            enrollments = WorkshopEnrollment.objects.filter(
                workshop=session.workshop,
                status='ativo'
            )
            
            for enrollment in enrollments:
                field_name = f'attendance_{enrollment.id}'
                attended = form.cleaned_data.get(field_name, False)
                
                # Atualizar ou criar registro de presença
                attendance, created = SessionAttendance.objects.get_or_create(
                    session=session,
                    enrollment=enrollment,
                    defaults={'attended': attended}
                )
                
                if not created:
                    attendance.attended = attended
                    attendance.save()
            
            messages.success(request, f'Presenças da sessão "{session.topic}" registradas com sucesso!')
            return redirect('workshops:session-list')
    else:
        form = BulkAttendanceForm(session=session)
    
    return render(request, 'workshops/bulk_attendance.html', {
        'form': form,
        'session': session
    })


# CRUD Views for WorkshopEvaluation Model

class WorkshopEvaluationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = WorkshopEvaluation
    template_name = 'workshops/evaluation_list.html'
    context_object_name = 'evaluations'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        workshop_filter = self.request.GET.get('workshop', '')
        
        queryset = WorkshopEvaluation.objects.select_related('enrollment__beneficiary', 'enrollment__workshop')
        
        if workshop_filter:
            queryset = queryset.filter(enrollment__workshop_id=workshop_filter)
        
        return queryset.order_by('-evaluation_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workshops'] = Workshop.objects.all().order_by('name')
        context['selected_workshop'] = self.request.GET.get('workshop', '')
        return context


class WorkshopEvaluationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = WorkshopEvaluation
    form_class = WorkshopEvaluationForm
    template_name = 'workshops/evaluation_form.html'
    success_url = reverse_lazy('workshops:evaluation-list')

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Avaliação registrada com sucesso!')
        return response


# API Views for AJAX calls

@login_required
@user_passes_test(is_technician)
def get_workshop_stats(request, workshop_id):
    """API para obter estatísticas de uma oficina"""
    workshop = get_object_or_404(Workshop, id=workshop_id)
    
    stats = {
        'total_enrollments': workshop.enrollments.filter(status='ativo').count(),
        'total_sessions': workshop.sessions.count(),
        'average_rating': WorkshopEvaluation.objects.filter(
            enrollment__workshop=workshop
        ).aggregate(avg=Avg('rating'))['avg'] or 0,
        'completion_rate': 0  # Calcular baseado nas presenças
    }
    
    return JsonResponse(stats)


def clear_workshop_cache():
    """Clear workshop-related cache entries in a production-safe way"""
    try:
        # Clear specific cache patterns
        cache.delete_many([
            'workshop_list_',
            'workshop_detail_',
            'workshop_enrollments_',
            'workshop_sessions_'
        ])
    except Exception:
        # Fallback: clear all cache if pattern deletion fails
        cache.clear()
