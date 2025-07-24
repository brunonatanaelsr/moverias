
# Imports únicos e organizados
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from core.unified_permissions import (
    get_user_permissions,
    requires_technician,
    requires_admin,
    requires_coordinator,
    TechnicianRequiredMixin,
    AdminRequiredMixin,
    CoordinatorRequiredMixin
)
from .models import (
    Department, JobPosition, Employee, EmployeeDocument, 
    PerformanceReview, TrainingRecord, OnboardingProgram, 
    OnboardingInstance, Goal, Feedback, AdvancedTraining, 
    TrainingRegistration, HRAnalytics
)
from .forms import (
    DepartmentForm, JobPositionForm, EmployeeForm, 
    EmployeeDocumentForm, PerformanceReviewForm, TrainingRecordForm
)

# ...existing code...


@login_required
@requires_coordinator
def document_detail(request, pk):
    """Detalhes do documento de funcionário"""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    return render(request, 'hr/document_detail.html', {'document': document})


@login_required
@requires_coordinator
def document_create(request):
    """Criação de documento de funcionário"""
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento cadastrado com sucesso!')
            return redirect('hr:document_list')
    else:
        form = EmployeeDocumentForm()
    return render(request, 'hr/document_form.html', {'form': form})


@login_required
@requires_coordinator
def document_edit(request, pk):
    """Edição de documento de funcionário"""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento atualizado com sucesso!')
            return redirect('hr:document_list')
    else:
        form = EmployeeDocumentForm(instance=document)
    return render(request, 'hr/document_form.html', {'form': form, 'document': document})


@login_required
@requires_coordinator
def document_delete(request, pk):
    """Exclusão de documento de funcionário"""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Documento excluído com sucesso!')
        return redirect('hr:document_list')
    return render(request, 'hr/document_confirm_delete.html', {'document': document})
@login_required
@requires_coordinator
def employee_create(request):
    """Criação de funcionário"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário criado com sucesso!')
            return redirect('hr:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'hr/employee_form.html', {'form': form})

@login_required
@requires_coordinator
def employee_edit(request, pk):
    """Edição de funcionário"""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário atualizado com sucesso!')
            return redirect('hr:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'hr/employee_form.html', {'form': form, 'employee': employee})

@login_required
@requires_coordinator
def employee_delete(request, pk):
    """Exclusão de funcionário"""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Funcionário excluído com sucesso!')
        return redirect('hr:employee_list')
    return render(request, 'hr/employee_confirm_delete.html', {'employee': employee})
@login_required
@requires_coordinator
def job_position_create(request):
    """Criação de cargo"""
    if request.method == 'POST':
        form = JobPositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo criado com sucesso!')
            return redirect('hr:job_position_list')
    else:
        form = JobPositionForm()
    return render(request, 'hr/position_form.html', {'form': form})

@login_required
@requires_coordinator
def job_position_edit(request, pk):
    """Edição de cargo"""
    position = get_object_or_404(JobPosition, pk=pk)
    if request.method == 'POST':
        form = JobPositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo atualizado com sucesso!')
            return redirect('hr:job_position_list')
    else:
        form = JobPositionForm(instance=position)
    return render(request, 'hr/position_form.html', {'form': form, 'position': position})

@login_required
@requires_coordinator
def job_position_delete(request, pk):
    """Exclusão de cargo"""
    position = get_object_or_404(JobPosition, pk=pk)
    if request.method == 'POST':
        position.delete()
        messages.success(request, 'Cargo excluído com sucesso!')
        return redirect('hr:job_position_list')
    return render(request, 'hr/position_confirm_delete.html', {'position': position})


@login_required
@requires_coordinator
def hr_dashboard(request):
    """Dashboard principal do RH com métricas avançadas"""
    # Estatísticas gerais
    stats = {
        'total_employees': Employee.objects.filter(employment_status='active').count(),
        'total_departments': Department.objects.filter(is_active=True).count(),
        'total_positions': JobPosition.objects.filter(is_active=True).count(),
        'pending_reviews': PerformanceReview.objects.filter(is_final=False).count(),
        'training_in_progress': TrainingRecord.objects.filter(status='in_progress').count(),
        'active_onboarding': OnboardingInstance.objects.filter(status='in_progress').count(),
        'active_goals': Goal.objects.filter(status='active').count(),
        'pending_feedback': Feedback.objects.filter(read_at__isnull=True).count(),
    }
    
    # Funcionários recém-contratados
    recent_hires = Employee.objects.filter(
        employment_status='active',
        hire_date__gte=timezone.now().date() - timezone.timedelta(days=30)
    ).order_by('-hire_date')[:5]
    
    # Aniversários do mês
    current_month = timezone.now().month
    birthdays = Employee.objects.filter(
        employment_status='active',
        birth_date__month=current_month
    ).order_by('birth_date__day')[:5]
    
    # Treinamentos próximos
    upcoming_trainings = AdvancedTraining.objects.filter(
        status='open',
        start_date__gte=timezone.now(),
        start_date__lte=timezone.now() + timezone.timedelta(days=30)
    ).order_by('start_date')[:5]
    
    # Onboarding em andamento
    active_onboarding = OnboardingInstance.objects.filter(
        status='in_progress'
    ).select_related('employee', 'program')[:5]
    
    # Metas próximas do prazo
    overdue_goals = Goal.objects.filter(
        status='active',
        target_date__lte=timezone.now().date() + timezone.timedelta(days=7)
    ).select_related('owner')[:5]
    
    # Métricas de departamento
    department_stats = Department.objects.filter(is_active=True).annotate(
        employee_count=Count('employees', filter=Q(employees__employment_status='active')),
        active_goals=Count('employees__owned_goals', filter=Q(employees__owned_goals__status='active'))
    ).order_by('-employee_count')[:5]
    
    # Calcular métricas de performance
    performance_metrics = calculate_performance_metrics()
    
    context = {
        'stats': stats,
        'recent_hires': recent_hires,
        'birthdays': birthdays,
        'upcoming_trainings': upcoming_trainings,
        'active_onboarding': active_onboarding,
        'overdue_goals': overdue_goals,
        'department_stats': department_stats,
        'performance_metrics': performance_metrics,
        'user_permissions': get_user_permissions(request.user),
    }
    
    return render(request, 'hr/dashboard.html', context)


def calculate_performance_metrics():
    """Calcula métricas de performance do RH"""
    today = timezone.now().date()
    last_month = today - timedelta(days=30)
    
    # Taxa de turnover (últimos 30 dias)
    total_active = Employee.objects.filter(employment_status='active').count()
    terminated = Employee.objects.filter(
        termination_date__gte=last_month,
        termination_date__lte=today
    ).count()
    
    turnover_rate = (terminated / total_active * 100) if total_active > 0 else 0
    
    # Satisfação média (baseada em feedback)
    satisfaction_feedback = Feedback.objects.filter(
        feedback_type='positive',
        created_at__gte=last_month
    ).count()
    
    total_feedback = Feedback.objects.filter(
        created_at__gte=last_month
    ).count()
    
    satisfaction_rate = (satisfaction_feedback / total_feedback * 100) if total_feedback > 0 else 0
    
    # Conclusão de metas
    completed_goals = Goal.objects.filter(
        status='completed',
        completion_date__gte=last_month
    ).count()
    
    total_goals = Goal.objects.filter(
        target_date__gte=last_month
    ).count()
    
    goal_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
    
    # Horas de treinamento
    training_hours = TrainingRecord.objects.filter(
        status='completed',
        end_date__gte=last_month
    ).aggregate(
        total_hours=Sum('hours')
    )['total_hours'] or 0
    
    return {
        'turnover_rate': round(turnover_rate, 1),
        'satisfaction_rate': round(satisfaction_rate, 1),
        'goal_completion_rate': round(goal_completion_rate, 1),
        'training_hours': training_hours,
    }


@login_required
@requires_coordinator
def onboarding_dashboard(request):
    """Dashboard de onboarding"""
    programs = OnboardingProgram.objects.filter(status='active')
    
    # Instâncias ativas
    active_instances = OnboardingInstance.objects.filter(
        status='in_progress'
    ).select_related('employee', 'program', 'mentor')
    
    # Estatísticas
    stats = {
        'total_programs': programs.count(),
        'active_instances': active_instances.count(),
        'completed_this_month': OnboardingInstance.objects.filter(
            status='completed',
            actual_completion_date__month=timezone.now().month
        ).count(),
        'overdue_instances': OnboardingInstance.objects.filter(
            status='in_progress',
            expected_completion_date__lt=timezone.now().date()
        ).count(),
    }
    
    context = {
        'programs': programs,
        'active_instances': active_instances,
        'stats': stats,
    }
    
    return render(request, 'hr/onboarding_dashboard.html', context)


@login_required
def goals_dashboard(request):
    """Dashboard de metas"""
    user_employee = getattr(request.user, 'employee_profile', None)
    
    # Metas do usuário
    my_goals = Goal.objects.filter(
        owner=user_employee
    ).order_by('-created_at') if user_employee else []
    
    # Metas colaborativas
    collaborative_goals = Goal.objects.filter(
        collaborators=user_employee
    ).order_by('-created_at') if user_employee else []
    
    # Estatísticas gerais
    stats = {
        'total_goals': Goal.objects.count(),
        'active_goals': Goal.objects.filter(status='active').count(),
        'completed_goals': Goal.objects.filter(status='completed').count(),
        'overdue_goals': Goal.objects.filter(
            status='active',
            target_date__lt=timezone.now().date()
        ).count(),
    }
    
    # Metas por departamento
    department_goals = Department.objects.filter(is_active=True).annotate(
        total_goals=Count('employees__owned_goals'),
        completed_goals=Count('employees__owned_goals', filter=Q(employees__owned_goals__status='completed'))
    ).order_by('-total_goals')
    
    context = {
        'my_goals': my_goals,
        'collaborative_goals': collaborative_goals,
        'stats': stats,
        'department_goals': department_goals,
    }
    
    return render(request, 'hr/goals_dashboard.html', context)


@login_required
def feedback_dashboard(request):
    """Dashboard de feedback"""
    user_employee = getattr(request.user, 'employee_profile', None)
    
    # Feedback recebido
    received_feedback = Feedback.objects.filter(
        to_user=user_employee
    ).order_by('-created_at') if user_employee else []
    
    # Feedback enviado
    given_feedback = Feedback.objects.filter(
        from_user=user_employee
    ).order_by('-created_at') if user_employee else []
    
    # Estatísticas
    stats = {
        'total_feedback': Feedback.objects.count(),
        'positive_feedback': Feedback.objects.filter(feedback_type='positive').count(),
        'constructive_feedback': Feedback.objects.filter(feedback_type='constructive').count(),
        'recognition_feedback': Feedback.objects.filter(feedback_type='recognition').count(),
        'unread_feedback': Feedback.objects.filter(
            to_user=user_employee,
            read_at__isnull=True
        ).count() if user_employee else 0,
    }
    
    context = {
        'received_feedback': received_feedback,
        'given_feedback': given_feedback,
        'stats': stats,
    }
    
    return render(request, 'hr/feedback_dashboard.html', context)


@login_required
def training_dashboard(request):
    """Dashboard de treinamentos"""
    # Treinamentos disponíveis
    available_trainings = AdvancedTraining.objects.filter(
        status='open',
        start_date__gte=timezone.now()
    ).order_by('start_date')
    
    user_employee = getattr(request.user, 'employee_profile', None)
    
    # Minhas inscrições
    if user_employee:
        my_registrations = TrainingRegistration.objects.filter(
            employee=user_employee
        ).select_related('training')
    else:
        my_registrations = TrainingRegistration.objects.none()
    
    # Estatísticas
    stats = {
        'available_trainings': available_trainings.count(),
        'my_registrations': my_registrations.count(),
        'completed_trainings': my_registrations.filter(status='completed').count(),
        'total_training_hours': TrainingRecord.objects.filter(
            employee=user_employee,
            status='completed'
        ).aggregate(
            total_hours=Sum('hours')
        )['total_hours'] or 0 if user_employee else 0,
    }
    
    context = {
        'available_trainings': available_trainings,
        'my_registrations': my_registrations,
        'stats': stats,
    }
    
    return render(request, 'hr/training_dashboard.html', context)


@login_required
def analytics_dashboard(request):
    """Dashboard de analytics de RH"""
    # Métricas dos últimos 6 meses
    six_months_ago = timezone.now().date() - timedelta(days=180)
    
    # Dados de turnover
    turnover_data = []
    for i in range(6):
        month_start = six_months_ago + timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        total_employees = Employee.objects.filter(
            hire_date__lte=month_end,
            employment_status='active'
        ).count()
        
        terminated = Employee.objects.filter(
            termination_date__gte=month_start,
            termination_date__lt=month_end
        ).count()
        
        turnover_rate = (terminated / total_employees * 100) if total_employees > 0 else 0
        
        turnover_data.append({
            'month': month_start.strftime('%B'),
            'rate': round(turnover_rate, 1)
        })
    
    # Métricas de treinamento
    training_metrics = HRAnalytics.objects.filter(
        metric_type='training_hours',
        period_start__gte=six_months_ago
    ).order_by('period_start')
    
    # Satisfação por departamento
    department_satisfaction = []
    for dept in Department.objects.filter(is_active=True):
        positive_feedback = Feedback.objects.filter(
            to_user__department=dept,
            feedback_type='positive',
            created_at__gte=six_months_ago
        ).count()
        
        total_feedback = Feedback.objects.filter(
            to_user__department=dept,
            created_at__gte=six_months_ago
        ).count()
        
        satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        department_satisfaction.append({
            'department': dept.name,
            'satisfaction_rate': round(satisfaction_rate, 1),
            'feedback_count': total_feedback
        })
    
    context = {
        'turnover_data': turnover_data,
        'training_metrics': training_metrics,
        'department_satisfaction': department_satisfaction,
    }
    
    return render(request, 'hr/analytics_dashboard.html', context)


@login_required
@requires_coordinator
def document_list(request):
    """Lista de documentos de funcionários"""
    documents = EmployeeDocument.objects.all()
    return render(request, 'hr/document_list.html', {'documents': documents})



# Views básicas para funcionamento do sistema
@login_required
def employee_list(request):
    """Lista de funcionários"""
    employees = Employee.objects.filter(employment_status='active')
    return render(request, 'hr/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    """Detalhes do funcionário"""
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'hr/employee_detail.html', {'employee': employee})

@login_required
@requires_coordinator
def department_list(request):
    """Lista de departamentos"""
    departments = Department.objects.filter(is_active=True)
    return render(request, 'hr/department_list.html', {'departments': departments})


@login_required
@requires_coordinator
def department_create(request):
    """Criação de departamento"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento criado com sucesso!')
            return redirect('hr:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'hr/department_form.html', {'form': form})


@login_required
@requires_coordinator
def department_edit(request, pk):
    """Edição de departamento"""
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento atualizado com sucesso!')
            return redirect('hr:department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'hr/department_form.html', {'form': form, 'department': department})


@login_required
@requires_coordinator
def department_delete(request, pk):
    """Exclusão de departamento"""
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Departamento excluído com sucesso!')
        return redirect('hr:department_list')
    return render(request, 'hr/department_confirm_delete.html', {'department': department})

@login_required
def department_detail(request, pk):
    """Detalhes do departamento"""
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'hr/department_detail.html', {'department': department})


@login_required
def job_position_list(request):
    """Lista de cargos"""
    positions = JobPosition.objects.filter(is_active=True)
    return render(request, 'hr/job_position_list.html', {'positions': positions})

@login_required
def job_position_detail(request, pk):
    """Detalhes do cargo"""
    position = get_object_or_404(JobPosition, pk=pk)
    return render(request, 'hr/job_position_detail.html', {'position': position})

@login_required
def performance_reviews(request):
    """Lista de avaliações"""
    reviews = PerformanceReview.objects.all()
    return render(request, 'hr/performance_review_list.html', {'reviews': reviews})

@login_required
def training_records(request):
    """Lista de treinamentos"""
    trainings = TrainingRecord.objects.all()
    return render(request, 'hr/training_record_list.html', {'trainings': trainings})

@login_required
def reports_dashboard(request):
    """Dashboard de relatórios"""
    return render(request, 'hr/reports_dashboard.html')

@login_required
def employee_search_api(request):
    """API de busca de funcionários"""
    return JsonResponse({'employees': []})

# Views dos novos módulos (placeholder)
@login_required
def onboarding_programs(request):
    """Lista de programas de onboarding"""
    return render(request, 'hr/onboarding_programs.html')

@login_required
def onboarding_program_create(request):
    """Criar programa de onboarding"""
    return render(request, 'hr/onboarding_program_form.html')

@login_required
def onboarding_program_detail(request, pk):
    """Detalhes do programa de onboarding"""
    return render(request, 'hr/onboarding_program_detail.html')

@login_required
def onboarding_instances(request):
    """Lista de instâncias de onboarding"""
    return render(request, 'hr/onboarding_instances.html')

@login_required
def onboarding_instance_create(request):
    """Criar instância de onboarding"""
    return render(request, 'hr/onboarding_instance_form.html')

@login_required
def onboarding_instance_detail(request, pk):
    """Detalhes da instância de onboarding"""
    return render(request, 'hr/onboarding_instance_detail.html')

@login_required
def goal_create(request):
    """Criar meta"""
    return render(request, 'hr/goal_form.html')

@login_required
def goal_detail(request, pk):
    """Detalhes da meta"""
    return render(request, 'hr/goal_detail.html')

@login_required
def goal_edit(request, pk):
    """Editar meta"""
    return render(request, 'hr/goal_form.html')

@login_required
def goal_update_progress(request, pk):
    """Atualizar progresso da meta"""
    return JsonResponse({'success': True})

@login_required
def give_feedback(request):
    """Dar feedback"""
    return render(request, 'hr/feedback_form.html')

@login_required
def feedback_detail(request, pk):
    """Detalhes do feedback"""
    return render(request, 'hr/feedback_detail.html')

@login_required
def mark_feedback_read(request, pk):
    """Marcar feedback como lido"""
    return JsonResponse({'success': True})

@login_required
def advanced_training_create(request):
    """Criar treinamento avançado"""
    return render(request, 'hr/advanced_training_form.html')

@login_required
def advanced_training_detail(request, pk):
    """Detalhes do treinamento avançado"""
    return render(request, 'hr/advanced_training_detail.html')

@login_required
def training_register(request, pk):
    """Registrar-se no treinamento"""
    return JsonResponse({'success': True})

@login_required
def training_registrations(request, pk):
    """Lista de inscrições no treinamento"""
    return render(request, 'hr/training_registrations.html')

@login_required
def analytics_export(request):
    """Exportar analytics"""
    return JsonResponse({'success': True})

@login_required
def turnover_report(request):
    """Relatório de turnover"""
    return render(request, 'hr/turnover_report.html')

@login_required
def performance_report(request):
    """Relatório de performance"""
    return render(request, 'hr/performance_report.html')

@login_required
def training_report(request):
    """Relatório de treinamentos"""
    return render(request, 'hr/training_report.html')

@login_required
def goals_progress_api(request):
    """API de progresso de metas"""
    return JsonResponse({'goals': []})

@login_required
def feedback_stats_api(request):
    """API de estatísticas de feedback"""
    return JsonResponse({'stats': {}})

@login_required
def analytics_charts_api(request):
    """API de gráficos de analytics"""
    return JsonResponse({'charts': {}})
