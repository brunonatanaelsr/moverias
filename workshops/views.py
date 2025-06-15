from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Prefetch
from django.utils import timezone
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
from members.models import Beneficiary


class WorkshopListView(LoginRequiredMixin, ListView):
    model = Workshop
    template_name = 'workshops/workshop_list.html'
    context_object_name = 'workshops'
    paginate_by = 10

    def get_queryset(self):
        # Cache key baseada nos parâmetros de filtro
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        workshop_type = self.request.GET.get('type', '')
        
        cache_key = f"workshops_list_{search}_{status}_{workshop_type}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Workshop.objects.annotate(
                participant_count=Count('enrollments', filter=Q(enrollments__status='ativo'))
            )
            
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
            
            # Cache por tempo médio (30 minutos)
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['MEDIUM'])
            
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

    def get_object(self, queryset=None):
        """Otimizar query do objeto principal"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"workshop_detail_{pk}"
        workshop = cache.get(cache_key)
        
        if workshop is None:
            workshop = Workshop.objects.prefetch_related(
                Prefetch('sessions', queryset=WorkshopSession.objects.order_by('session_number')),
                Prefetch('enrollments', queryset=WorkshopEnrollment.objects.select_related('beneficiary').filter(status='ativo'))
            ).get(pk=pk)
            
            # Cache por tempo longo (1 hora)
            cache.set(cache_key, workshop, settings.CACHE_TIMEOUT['LONG'])
        
        return workshop

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop = self.get_object()
        
        # Usar dados já carregados via prefetch_related
        context['sessions'] = workshop.sessions.all()
        context['enrollments'] = workshop.enrollments.all()
        
        # Cache para avaliações recentes
        cache_key = f"workshop_evaluations_{workshop.pk}"
        recent_evaluations = cache.get(cache_key)
        
        if recent_evaluations is None:
            recent_evaluations = WorkshopEvaluation.objects.select_related(
                'enrollment__beneficiary', 'evaluator'
            ).filter(
                enrollment__workshop=workshop
            ).order_by('-date')[:5]
            
            cache.set(cache_key, list(recent_evaluations), settings.CACHE_TIMEOUT['SHORT'])
            
        context['recent_evaluations'] = recent_evaluations
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
    """Lista otimizada de inscrições com cache e select_related"""
    # Cache do workshop
    cache_key = f"workshop_{workshop_id}"
    workshop = cache.get(cache_key)
    if workshop is None:
        workshop = get_object_or_404(Workshop, id=workshop_id)
        cache.set(cache_key, workshop, settings.CACHE_TIMEOUT['MEDIUM'])
    
    # Query otimizada das inscrições
    enrollments = WorkshopEnrollment.objects.select_related(
        'beneficiary', 'workshop'
    ).filter(workshop_id=workshop_id)
    
    search = request.GET.get('search')
    if search:
        enrollments = enrollments.filter(
            beneficiary__full_name__icontains=search
        )
    
    status = request.GET.get('status')
    if status:
        enrollments = enrollments.filter(status=status)
    
    # Ordenação para performance
    enrollments = enrollments.order_by('beneficiary__full_name')
    
    context = {
        'workshop': workshop,
        'enrollments': enrollments,
        'status_choices': WorkshopEnrollment.STATUS_CHOICES,
    }
    return render(request, 'workshops/enrollment_list.html', context)


@login_required
def enrollment_create(request, workshop_id):
    """Criar inscrição otimizada com bulk operations"""
    # Cache do workshop
    cache_key = f"workshop_{workshop_id}"
    workshop = cache.get(cache_key)
    if workshop is None:
        workshop = get_object_or_404(Workshop.objects.select_related('created_by'), id=workshop_id)
        cache.set(cache_key, workshop, settings.CACHE_TIMEOUT['MEDIUM'])
    
    if request.method == 'POST':
        beneficiary_id = request.POST.get('beneficiary')
        if beneficiary_id:
            beneficiary = get_object_or_404(
                Beneficiary.objects.select_related('created_by'), 
                id=beneficiary_id
            )
            
            # Verificar se já existe inscrição (query otimizada)
            if WorkshopEnrollment.objects.filter(
                workshop_id=workshop_id, 
                beneficiary_id=beneficiary_id
            ).exists():
                messages.error(request, 'Esta beneficiária já está inscrita nesta oficina.')
            else:
                enrollment = WorkshopEnrollment.objects.create(
                    workshop=workshop,
                    beneficiary=beneficiary,
                    enrollment_date=timezone.now().date()
                )
                
                # Bulk create dos registros de presença para melhor performance
                sessions = workshop.sessions.all()
                attendance_records = [
                    SessionAttendance(session=session, enrollment=enrollment)
                    for session in sessions
                ]
                
                if attendance_records:
                    SessionAttendance.objects.bulk_create(attendance_records)
                
                # Invalidar caches relacionados
                cache.delete(f"workshop_detail_{workshop_id}")
                cache.delete(f"workshop_evaluations_{workshop_id}")
                
                messages.success(request, f'{beneficiary.full_name} foi inscrita com sucesso!')
                return redirect('workshops:enrollment_list', workshop_id=workshop.id)
    
    # Beneficiárias que ainda não estão inscritas (query otimizada)
    enrolled_beneficiaries = WorkshopEnrollment.objects.filter(
        workshop_id=workshop_id
    ).values_list('beneficiary_id', flat=True)
    
    available_beneficiaries = Beneficiary.objects.exclude(
        id__in=enrolled_beneficiaries
    ).select_related('created_by').order_by('full_name')
    
    context = {
        'workshop': workshop,
        'beneficiaries': available_beneficiaries,
    }
    return render(request, 'workshops/enrollment_form.html', context)


@login_required
def attendance_register(request, session_id):
    """Registrar presença com bulk update otimizado"""
    session = get_object_or_404(
        WorkshopSession.objects.select_related('workshop'), 
        id=session_id
    )
    
    attendances = SessionAttendance.objects.select_related(
        'enrollment__beneficiary'
    ).filter(session=session).order_by('enrollment__beneficiary__full_name')
    
    if request.method == 'POST':
        # Bulk update para melhor performance
        attendance_updates = []
        
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
            attendance_updates.append(attendance)
        
        # Bulk update
        if attendance_updates:
            SessionAttendance.objects.bulk_update(
                attendance_updates,
                ['present', 'late', 'left_early', 'participation_quality', 'notes']
            )
        
        # Invalidar caches relacionados
        cache.delete(f"workshop_detail_{session.workshop.id}")
        cache.delete(f"workshop_evaluations_{session.workshop.id}")
        
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
    """Relatório otimizado com cache e aggregate queries"""
    # Cache do relatório
    cache_key = f"workshop_report_{workshop_id}"
    report_data = cache.get(cache_key)
    
    if report_data is None:
        workshop = get_object_or_404(
            Workshop.objects.select_related('created_by'),
            id=workshop_id
        )
        
        # Estatísticas com queries agregadas otimizadas
        enrollment_stats = workshop.enrollments.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ativo')),
            completed=Count('id', filter=Q(status='concluido'))
        )
        
        total_enrollments = enrollment_stats['total']
        active_enrollments = enrollment_stats['active']
        completed_enrollments = enrollment_stats['completed']
        
        # Taxa de frequência geral com query otimizada
        total_sessions = workshop.sessions.count()
        if total_sessions > 0:
            attendance_stats = SessionAttendance.objects.filter(
                session__workshop=workshop
            ).aggregate(
                total_possible=Count('id'),
                total_present=Count('id', filter=Q(present=True))
            )
            
            total_possible = attendance_stats['total_possible']
            total_present = attendance_stats['total_present']
            attendance_rate = (total_present / total_possible * 100) if total_possible > 0 else 0
        else:
            attendance_rate = 0
        
        # Avaliações recentes otimizadas
        recent_evaluations = WorkshopEvaluation.objects.select_related(
            'enrollment__beneficiary', 'evaluator'
        ).filter(
            enrollment__workshop=workshop
        ).order_by('-date')[:10]
        
        # Participantes com baixa frequência (calculado de forma otimizada)
        low_attendance_enrollments = []
        active_enrollments_qs = workshop.enrollments.select_related(
            'beneficiary'
        ).filter(status='ativo')
        
        for enrollment in active_enrollments_qs:
            # Usar property que já existe no modelo
            if hasattr(enrollment, 'attendance_rate') and enrollment.attendance_rate < 70:
                low_attendance_enrollments.append(enrollment)
        
        report_data = {
            'workshop': workshop,
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'completed_enrollments': completed_enrollments,
            'attendance_rate': attendance_rate,
            'recent_evaluations': list(recent_evaluations),
            'low_attendance': low_attendance_enrollments,
        }
        
        # Cache por tempo médio (30 minutos)
        cache.set(cache_key, report_data, settings.CACHE_TIMEOUT['MEDIUM'])
    
    return render(request, 'workshops/workshop_report.html', report_data)
    
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
