from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Employee, Department, JobPosition, 
    EmployeeDocument, PerformanceReview, TrainingRecord
)


@login_required
def hr_dashboard(request):
    """Dashboard principal do módulo RH."""
    context = {
        'total_employees': Employee.objects.filter(employment_status='active').count(),
        'total_departments': Department.objects.count(),
        'total_positions': JobPosition.objects.count(),
        'recent_hires': Employee.objects.filter(
            hire_date__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'pending_reviews': PerformanceReview.objects.filter(
            is_final=False
        ).count(),
        'upcoming_trainings': TrainingRecord.objects.filter(
            status='planned'
        ).count(),
    }
    return render(request, 'hr/dashboard.html', context)


@login_required
def employee_list(request):
    """Lista todos os funcionários com filtros."""
    employees = Employee.objects.select_related(
        'user', 'department', 'job_position', 'direct_supervisor'
    ).filter(employment_status='active')
    
    # Filtros
    search = request.GET.get('search')
    department_id = request.GET.get('department')
    position_id = request.GET.get('position')
    
    if search:
        employees = employees.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(full_name__icontains=search) |
            Q(cpf__icontains=search)
        )
    
    if department_id:
        employees = employees.filter(department_id=department_id)
    
    if position_id:
        employees = employees.filter(job_position_id=position_id)
    
    # Paginação
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'departments': Department.objects.all(),
        'positions': JobPosition.objects.all(),
        'search': search,
        'selected_department': department_id,
        'selected_position': position_id,
    }
    return render(request, 'hr/employee_list.html', context)


@login_required
def employee_detail(request, pk):
    """Detalhes de um funcionário específico."""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Documentos do funcionário
    documents = EmployeeDocument.objects.filter(employee=employee)
    
    # Avaliações de desempenho
    reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')
    
    # Treinamentos
    trainings = TrainingRecord.objects.filter(employee=employee).order_by('-completion_date')
    
    context = {
        'employee': employee,
        'documents': documents,
        'reviews': reviews,
        'trainings': trainings,
    }
    return render(request, 'hr/employee_detail.html', context)


@login_required
def employee_create(request):
    """Criar novo funcionário."""
    if request.method == 'POST':
        # TODO: Implementar formulário e criação
        messages.success(request, 'Funcionário criado com sucesso!')
        return redirect('hr:employee_list')
    
    return render(request, 'hr/employee_form.html', {
        'title': 'Novo Funcionário'
    })


@login_required
def employee_edit(request, pk):
    """Editar funcionário existente."""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        # TODO: Implementar formulário e edição
        messages.success(request, f'Funcionário {employee.user.get_full_name()} atualizado com sucesso!')
        return redirect('hr:employee_detail', pk=employee.pk)
    
    return render(request, 'hr/employee_form.html', {
        'employee': employee,
        'title': f'Editar {employee.user.get_full_name()}'
    })


@login_required
def department_list(request):
    """Lista todos os departamentos."""
    departments = Department.objects.annotate(
        employee_count=Count('employees', filter=Q(employees__employment_status='active'))
    ).select_related('manager')
    
    return render(request, 'hr/department_list.html', {
        'departments': departments
    })


@login_required
def department_detail(request, pk):
    """Detalhes de um departamento."""
    department = get_object_or_404(Department, pk=pk)
    employees = Employee.objects.filter(
        department=department, employment_status='active'
    ).select_related('user', 'job_position')
    
    return render(request, 'hr/department_detail.html', {
        'department': department,
        'employees': employees
    })


@login_required
def performance_reviews(request):
    """Lista todas as avaliações de desempenho."""
    reviews = PerformanceReview.objects.select_related(
        'employee__user', 'reviewed_by'
    ).order_by('-review_date')
    
    # Filtros
    is_final = request.GET.get('is_final')
    if is_final is not None:
        reviews = reviews.filter(is_final=is_final == 'true')
    
    # Paginação
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hr/performance_reviews.html', {
        'page_obj': page_obj,
        'selected_is_final': is_final,
    })


@login_required
def training_records(request):
    """Lista todos os registros de treinamento."""
    trainings = TrainingRecord.objects.select_related(
        'employee__user'
    ).order_by('-completion_date')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        trainings = trainings.filter(status=status)
    
    # Paginação
    paginator = Paginator(trainings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hr/training_records.html', {
        'page_obj': page_obj,
        'selected_status': status,
        'status_choices': TrainingRecord.STATUS_CHOICES,
    })


@login_required
def reports_dashboard(request):
    """Dashboard de relatórios de RH."""
    # Estatísticas gerais
    total_employees = Employee.objects.filter(employment_status='active').count()
    
    # Funcionários por departamento
    dept_stats = Department.objects.annotate(
        employee_count=Count('employees', filter=Q(employees__employment_status='active'))
    ).values('name', 'employee_count')
    
    # Avaliações médias por departamento
    avg_reviews = Department.objects.annotate(
        avg_rating=Avg('employees__performance_reviews__overall_rating')
    ).values('name', 'avg_rating')
    
    # Treinamentos por status
    training_stats = TrainingRecord.objects.values('status').annotate(
        count=Count('id')
    )
    
    context = {
        'total_employees': total_employees,
        'dept_stats': list(dept_stats),
        'avg_reviews': list(avg_reviews),
        'training_stats': list(training_stats),
    }
    
    return render(request, 'hr/reports_dashboard.html', context)


@login_required
def employee_search_api(request):
    """API para busca de funcionários (usado em selects)."""
    query = request.GET.get('q', '')
    employees = Employee.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query) |
        Q(full_name__icontains=query),
        employment_status='active'
    ).select_related('user', 'job_position')[:10]
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'text': f"{emp.full_name} - {emp.job_position.title if emp.job_position else 'Sem cargo'}",
            'email': emp.user.email,
            'position': emp.job_position.title if emp.job_position else '',
        })
    
    return JsonResponse({'results': results})
