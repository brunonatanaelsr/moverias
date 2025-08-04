from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count, Avg, Prefetch
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from core.unified_permissions import (
    is_technician, TechnicianRequiredMixin, requires_technician
)
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from core.export_utils import export_universal, DataFormatter, ExportManager
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
from .forms import (
    WorkshopForm, WorkshopSessionForm, WorkshopEnrollmentForm, 
    SessionAttendanceForm, WorkshopEvaluationForm, BulkAttendanceForm
)
from members.models import Beneficiary


# CRUD Views for Workshop Model

class WorkshopListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
    model = Workshop
    template_name = 'workshops/workshop_list.html'
    context_object_name = 'workshops'
    paginate_by = 15

    def test_func(self):
        return is_technician(self.request.user)

    def get_queryset(self):
        # OTIMIZAÇÃO: prefetch_related para evitar N+1 queries
        queryset = Workshop.objects.prefetch_related(
            'enrollments__beneficiary',
            'sessions',
            'enrollments'
        ).annotate(
            participant_count=Count('enrollments', filter=Q(enrollments__status='ativo')),
            session_count=Count('sessions', distinct=True)
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


class WorkshopDetailView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
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


class WorkshopCreateView(CreateConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo oficina?"
    confirmation_entity = "oficina"
    model = Workshop
    form_class = WorkshopForm
    template_name = 'workshops/workshop_form.html'
    success_url = reverse_lazy('workshops:workshop-list')
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro desta nova oficina?"
    confirmation_entity = "oficina"

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Oficina "{form.instance.name}" criada com sucesso!')
        return super().form_valid(form)


class WorkshopUpdateView(EditConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste oficina?"
    confirmation_entity = "oficina"
    model = Workshop
    form_class = WorkshopForm
    template_name = 'workshops/workshop_form.html'
    success_url = reverse_lazy('workshops:workshop-list')
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações nesta oficina?"
    confirmation_entity = "oficina"

    def test_func(self):
        return is_technician(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Oficina "{form.instance.name}" atualizada com sucesso!')
        cache.delete(f"workshop_detail_{self.object.pk}")
        return super().form_valid(form)


class WorkshopDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, DeleteView):
    
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir este oficina?"
    confirmation_entity = "oficina"
    dangerous_operation = Truemodel = Workshop
    template_name = 'workshops/workshop_confirm_delete.html'
    success_url = reverse_lazy('workshops:workshop-list')
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir esta oficina?"
    confirmation_entity = "oficina"
    dangerous_operation = True

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

class WorkshopEnrollmentListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
    model = WorkshopEnrollment
    template_name = 'workshops/enrollment_list_general.html'
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


class WorkshopEnrollmentCreateView(CreateConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
    model = WorkshopEnrollment
    form_class = WorkshopEnrollmentForm
    template_name = 'workshops/enrollment_form.html'
    success_url = reverse_lazy('workshops:enrollment-list')

    def test_func(self):
        return is_technician(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pré-selecionar oficina se passado via GET
        workshop_id = self.request.GET.get('workshop')
        if workshop_id:
            try:
                workshop = Workshop.objects.get(pk=workshop_id)
                kwargs['initial'] = kwargs.get('initial', {})
                kwargs['initial']['workshop'] = workshop
            except Workshop.DoesNotExist:
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop_id = self.request.GET.get('workshop')
        workshop = None
        if workshop_id:
            try:
                workshop = Workshop.objects.get(pk=workshop_id)
            except Workshop.DoesNotExist:
                workshop = None
        context['workshop'] = workshop

        # Filtrar beneficiárias ativas e não matriculadas nesta oficina
        if workshop:
            enrolled_ids = WorkshopEnrollment.objects.filter(workshop=workshop, status='ativo').values_list('beneficiary_id', flat=True)
            beneficiaries = Beneficiary.objects.filter(status='ATIVA').exclude(id__in=enrolled_ids).order_by('full_name')
        else:
            # Se não há oficina selecionada, mostrar todas ativas
            beneficiaries = Beneficiary.objects.filter(status='ATIVA').order_by('full_name')
        context['beneficiaries'] = beneficiaries

        if not Workshop.objects.filter(status__in=['planejamento', 'ativo']).exists():
            messages.warning(self.request, "Não existem oficinas ativas. Crie uma oficina antes de realizar matrículas.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Matrícula de {form.instance.beneficiary.full_name} na oficina "{form.instance.workshop.name}" criada com sucesso!')
        return response


class WorkshopEnrollmentUpdateView(EditConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, UpdateView):
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


class WorkshopEnrollmentDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, DeleteView):
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

class WorkshopSessionListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
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


class WorkshopSessionCreateView(CreateConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
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


class WorkshopSessionUpdateView(EditConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, UpdateView):
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


class WorkshopSessionDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, DeleteView):
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
@requires_technician
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

class WorkshopEvaluationListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
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


class WorkshopEvaluationCreateView(CreateConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
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
@requires_technician
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


# Workshop Report View

@login_required
@requires_technician
def workshop_report(request, pk):
    """Gera relatório detalhado da oficina"""
    workshop = get_object_or_404(Workshop, pk=pk)
    
    # Estatísticas da oficina
    total_sessions = workshop.sessions.count()
    total_enrollments = workshop.enrollments.filter(status='ativo').count()
    
    # Dados de presença
    attendance_data = []
    for session in workshop.sessions.all():
        session_attendance = SessionAttendance.objects.filter(session=session)
        present_count = session_attendance.filter(attended=True).count()
        total_enrolled = session_attendance.count()
        
        attendance_data.append({
            'session': session,
            'present': present_count,
            'total': total_enrolled,
            'percentage': (present_count / total_enrolled * 100) if total_enrolled > 0 else 0
        })
    
    # Avaliações
    evaluations = WorkshopEvaluation.objects.filter(workshop=workshop)
    avg_rating = evaluations.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    context = {
        'workshop': workshop,
        'total_sessions': total_sessions,
        'total_enrollments': total_enrollments,
        'attendance_data': attendance_data,
        'evaluations': evaluations,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'workshops/workshop_report.html', context)


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


# =============================================================================
# EXPORT VIEWS
# =============================================================================

@login_required
@requires_technician
def workshops_export(request):
    """
    Exporta lista de workshops em CSV, Excel ou PDF
    """
    return export_universal(
        request=request,
        model_class=Workshop,
        formatter_method=DataFormatter.format_workshop_data,
        filename_prefix="workshops",
        template_name="core/exports/pdf_report.html",
        extra_context={
            'report_type': 'Workshops',
            'user': request.user
        }
    )


@login_required
@requires_technician
def workshop_enrollments_export(request, pk):
    """
    Exporta matrículas de um workshop específico
    """
    workshop = get_object_or_404(Workshop, pk=pk)
    enrollments = WorkshopEnrollment.objects.filter(workshop=workshop).select_related('beneficiary')
    
    # Formatar dados para exportação
    headers = [
        'Beneficiária', 'Telefone', 'Bairro', 'Status da Matrícula', 
        'Data de Matrícula', 'Data de Última Presença'
    ]
    
    data = []
    for enrollment in enrollments:
        # Buscar última presença
        last_attendance = SessionAttendance.objects.filter(
            enrollment=enrollment, present=True
        ).order_by('-session__date').first()
        
        data.append([
            enrollment.beneficiary.full_name,
            enrollment.beneficiary.phone_1 or '',
            enrollment.beneficiary.neighbourhood or '',
            enrollment.get_status_display(),
            enrollment.created_at.strftime('%d/%m/%Y') if enrollment.created_at else '',
            last_attendance.session.date.strftime('%d/%m/%Y') if last_attendance else 'Nunca'
        ])
    
    export_format = request.GET.get('format', 'csv')
    filename = f"matriculas_workshop_{workshop.name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
    
    try:
        if export_format == 'csv':
            return ExportManager.export_to_csv(data, filename, headers)
        elif export_format == 'excel':
            return ExportManager.export_to_excel(data, filename, headers, f"Matrículas - {workshop.name}")
        elif export_format == 'pdf':
            context = {
                'data': data,
                'headers': headers,
                'title': f'Matrículas - {workshop.name}',
                'generated_at': timezone.now(),
                'workshop': workshop,
                'total_enrollments': len(data),
                'report_type': 'Matrículas de Workshop',
                'user': request.user
            }
            return ExportManager.export_to_pdf('core/exports/pdf_report.html', context, filename)
    except Exception as e:
        messages.error(request, f'Erro ao exportar dados: {str(e)}')
        return redirect('workshops:workshop_detail', pk=workshop.pk)


@login_required
@requires_technician
def workshop_attendance_export(request, pk):
    """
    Exporta relatório de frequência de um workshop
    """
    workshop = get_object_or_404(Workshop, pk=pk)
    sessions = WorkshopSession.objects.filter(workshop=workshop).order_by('date')
    enrollments = WorkshopEnrollment.objects.filter(workshop=workshop).select_related('beneficiary')
    
    # Cabeçalhos dinâmicos com as datas das sessões
    headers = ['Beneficiária', 'Telefone', 'Total de Presenças', 'Percentual de Frequência']
    session_headers = [f"Sessão {session.date.strftime('%d/%m')}" for session in sessions]
    headers.extend(session_headers)
    
    data = []
    for enrollment in enrollments:
        attendances = SessionAttendance.objects.filter(enrollment=enrollment).select_related('session')
        attendance_dict = {att.session.id: att.present for att in attendances}
        
        total_sessions = sessions.count()
        total_present = sum(1 for session in sessions if attendance_dict.get(session.id, False))
        percentage = (total_present / total_sessions * 100) if total_sessions > 0 else 0
        
        row = [
            enrollment.beneficiary.full_name,
            enrollment.beneficiary.phone_1 or '',
            total_present,
            f"{percentage:.1f}%"
        ]
        
        # Adicionar presença de cada sessão
        for session in sessions:
            present = attendance_dict.get(session.id, False)
            row.append("✓" if present else "✗")
        
        data.append(row)
    
    export_format = request.GET.get('format', 'csv')
    filename = f"frequencia_workshop_{workshop.name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
    
    try:
        if export_format == 'csv':
            return ExportManager.export_to_csv(data, filename, headers)
        elif export_format == 'excel':
            return ExportManager.export_to_excel(data, filename, headers, f"Frequência - {workshop.name}")
        elif export_format == 'pdf':
            context = {
                'data': data,
                'headers': headers,
                'title': f'Relatório de Frequência - {workshop.name}',
                'generated_at': timezone.now(),
                'workshop': workshop,
                'total_sessions': sessions.count(),
                'report_type': 'Relatório de Frequência',
                'user': request.user
            }
            return ExportManager.export_to_pdf('core/exports/pdf_report.html', context, filename)
    except Exception as e:
        messages.error(request, f'Erro ao exportar relatório: {str(e)}')
        return redirect('workshops:workshop_detail', pk=workshop.pk)