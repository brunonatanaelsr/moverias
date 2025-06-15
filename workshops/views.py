from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
from members.models import Beneficiary


class WorkshopListView(LoginRequiredMixin, ListView):
    model = Workshop
    template_name = 'workshops/workshop_list.html'
    context_object_name = 'workshops'
    paginate_by = 10

    def get_queryset(self):
        queryset = Workshop.objects.annotate(
            participant_count=Count('enrollments', filter=Q(enrollments__status='ativo'))
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(facilitator__icontains=search) |
                Q(description__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        workshop_type = self.request.GET.get('type')
        if workshop_type:
            queryset = queryset.filter(workshop_type=workshop_type)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workshop_types'] = Workshop.WORKSHOP_TYPES
        context['status_choices'] = Workshop.STATUS_CHOICES
        return context


class WorkshopDetailView(LoginRequiredMixin, DetailView):
    model = Workshop
    template_name = 'workshops/workshop_detail.html'
    context_object_name = 'workshop'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop = self.get_object()
        context['sessions'] = workshop.sessions.all()
        context['enrollments'] = workshop.enrollments.filter(status='ativo')
        context['recent_evaluations'] = WorkshopEvaluation.objects.filter(
            enrollment__workshop=workshop
        ).order_by('-date')[:5]
        return context


class WorkshopCreateView(LoginRequiredMixin, CreateView):
    model = Workshop
    template_name = 'workshops/workshop_form.html'
    fields = ['name', 'description', 'workshop_type', 'facilitator', 'location', 
              'start_date', 'end_date', 'max_participants', 'objectives', 'materials_needed']
    success_url = reverse_lazy('workshops:workshop_list')

    def form_valid(self, form):
        messages.success(self.request, 'Oficina criada com sucesso!')
        return super().form_valid(form)


class WorkshopUpdateView(LoginRequiredMixin, UpdateView):
    model = Workshop
    template_name = 'workshops/workshop_form.html'
    fields = ['name', 'description', 'workshop_type', 'facilitator', 'location', 
              'start_date', 'end_date', 'status', 'max_participants', 'objectives', 'materials_needed']
    success_url = reverse_lazy('workshops:workshop_list')

    def form_valid(self, form):
        messages.success(self.request, 'Oficina atualizada com sucesso!')
        return super().form_valid(form)


class SessionListView(LoginRequiredMixin, ListView):
    model = WorkshopSession
    template_name = 'workshops/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        workshop_id = self.kwargs.get('workshop_id')
        if workshop_id:
            return WorkshopSession.objects.filter(workshop_id=workshop_id)
        return WorkshopSession.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop_id = self.kwargs.get('workshop_id')
        if workshop_id:
            context['workshop'] = get_object_or_404(Workshop, id=workshop_id)
        return context


class SessionCreateView(LoginRequiredMixin, CreateView):
    model = WorkshopSession
    template_name = 'workshops/session_form.html'
    fields = ['session_number', 'date', 'start_time', 'end_time', 'topic', 
              'content_covered', 'materials_used', 'observations']

    def get_initial(self):
        initial = super().get_initial()
        workshop_id = self.kwargs.get('workshop_id')
        if workshop_id:
            workshop = get_object_or_404(Workshop, id=workshop_id)
            initial['workshop'] = workshop
            # Auto-incrementar número da sessão
            last_session = workshop.sessions.order_by('-session_number').first()
            initial['session_number'] = (last_session.session_number + 1) if last_session else 1
        return initial

    def form_valid(self, form):
        workshop_id = self.kwargs.get('workshop_id')
        if workshop_id:
            form.instance.workshop = get_object_or_404(Workshop, id=workshop_id)
        messages.success(self.request, 'Sessão criada com sucesso!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workshops:session_list', kwargs={'workshop_id': self.object.workshop.id})


@login_required
def enrollment_list(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    enrollments = workshop.enrollments.all()
    
    search = request.GET.get('search')
    if search:
        enrollments = enrollments.filter(
            beneficiary__full_name__icontains=search
        )
    
    status = request.GET.get('status')
    if status:
        enrollments = enrollments.filter(status=status)
    
    context = {
        'workshop': workshop,
        'enrollments': enrollments,
        'status_choices': WorkshopEnrollment.STATUS_CHOICES,
    }
    return render(request, 'workshops/enrollment_list.html', context)


@login_required
def enrollment_create(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    
    if request.method == 'POST':
        beneficiary_id = request.POST.get('beneficiary')
        if beneficiary_id:
            beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
            
            # Verificar se já existe inscrição
            if WorkshopEnrollment.objects.filter(workshop=workshop, beneficiary=beneficiary).exists():
                messages.error(request, 'Esta beneficiária já está inscrita nesta oficina.')
            else:
                enrollment = WorkshopEnrollment.objects.create(
                    workshop=workshop,
                    beneficiary=beneficiary,
                    enrollment_date=timezone.now().date()
                )
                
                # Criar registros de presença para todas as sessões existentes
                for session in workshop.sessions.all():
                    SessionAttendance.objects.get_or_create(
                        session=session,
                        enrollment=enrollment
                    )
                
                messages.success(request, f'{beneficiary.full_name} foi inscrita com sucesso!')
                return redirect('workshops:enrollment_list', workshop_id=workshop.id)
    
    # Beneficiárias que ainda não estão inscritas
    enrolled_beneficiaries = workshop.enrollments.values_list('beneficiary_id', flat=True)
    available_beneficiaries = Beneficiary.objects.exclude(id__in=enrolled_beneficiaries)
    
    context = {
        'workshop': workshop,
        'beneficiaries': available_beneficiaries,
    }
    return render(request, 'workshops/enrollment_form.html', context)


@login_required
def attendance_register(request, session_id):
    session = get_object_or_404(WorkshopSession, id=session_id)
    attendances = SessionAttendance.objects.filter(session=session)
    
    if request.method == 'POST':
        for attendance in attendances:
            present = request.POST.get(f'present_{attendance.id}') == 'on'
            late = request.POST.get(f'late_{attendance.id}') == 'on'
            left_early = request.POST.get(f'left_early_{attendance.id}') == 'on'
            participation_quality = request.POST.get(f'participation_{attendance.id}')
            notes = request.POST.get(f'notes_{attendance.id}', '')
            
            attendance.present = present
            attendance.late = late
            attendance.left_early = left_early
            attendance.participation_quality = participation_quality
            attendance.notes = notes
            attendance.save()
        
        messages.success(request, 'Presença registrada com sucesso!')
        return redirect('workshops:workshop_detail', pk=session.workshop.id)
    
    context = {
        'session': session,
        'attendances': attendances,
        'participation_choices': SessionAttendance._meta.get_field('participation_quality').choices,
    }
    return render(request, 'workshops/attendance_register.html', context)


@login_required
def workshop_report(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    
    # Estatísticas gerais
    total_enrollments = workshop.enrollments.count()
    active_enrollments = workshop.enrollments.filter(status='ativo').count()
    completed_enrollments = workshop.enrollments.filter(status='concluido').count()
    
    # Taxa de frequência geral
    total_sessions = workshop.sessions.count()
    if total_sessions > 0:
        attendances = SessionAttendance.objects.filter(session__workshop=workshop)
        total_possible = attendances.count()
        total_present = attendances.filter(present=True).count()
        attendance_rate = (total_present / total_possible * 100) if total_possible > 0 else 0
    else:
        attendance_rate = 0
    
    # Avaliações recentes
    recent_evaluations = WorkshopEvaluation.objects.filter(
        enrollment__workshop=workshop
    ).order_by('-date')[:10]
    
    # Participantes com baixa frequência
    low_attendance = []
    for enrollment in workshop.enrollments.filter(status='ativo'):
        if enrollment.attendance_rate < 70:  # Menos de 70% de presença
            low_attendance.append(enrollment)
    
    context = {
        'workshop': workshop,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'attendance_rate': attendance_rate,
        'recent_evaluations': recent_evaluations,
        'low_attendance': low_attendance,
        'sessions': workshop.sessions.all(),
    }
    return render(request, 'workshops/workshop_report.html', context)
