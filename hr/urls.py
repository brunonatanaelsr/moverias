from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Dashboard Principal
    path('', views.hr_dashboard, name='dashboard'),
    
    # Funcionários
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    
    # Departamentos
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    
    # Cargos
    path('positions/', views.job_position_list, name='job_position_list'),
    path('positions/create/', views.job_position_create, name='job_position_create'),
    path('positions/<int:pk>/edit/', views.job_position_edit, name='job_position_edit'),
    path('positions/<int:pk>/delete/', views.job_position_delete, name='job_position_delete'),
    path('positions/<int:pk>/', views.job_position_detail, name='job_position_detail'),
    
    # Avaliações de Desempenho
    path('reviews/', views.performance_reviews, name='performance_review_list'),
    
    # Treinamentos Básicos
    path('trainings/', views.training_records, name='training_record_list'),
    
    # Módulos Modernos
    
    # Onboarding
    path('onboarding/', views.onboarding_dashboard, name='onboarding_dashboard'),
    path('onboarding/programs/', views.onboarding_programs, name='onboarding_programs'),
    path('onboarding/programs/create/', views.onboarding_program_create, name='onboarding_program_create'),
    path('onboarding/programs/<int:pk>/', views.onboarding_program_detail, name='onboarding_program_detail'),
    path('onboarding/instances/', views.onboarding_instances, name='onboarding_instances'),
    path('onboarding/instances/create/', views.onboarding_instance_create, name='onboarding_instance_create'),
    path('onboarding/instances/<int:pk>/', views.onboarding_instance_detail, name='onboarding_instance_detail'),
    
    # Metas e Objetivos
    path('goals/', views.goals_dashboard, name='goals_dashboard'),
    path('goals/create/', views.goal_create, name='goal_create'),
    path('goals/<int:pk>/', views.goal_detail, name='goal_detail'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/update-progress/', views.goal_update_progress, name='goal_update_progress'),
    
    # Feedback
    path('feedback/', views.feedback_dashboard, name='feedback_dashboard'),
    path('feedback/give/', views.give_feedback, name='give_feedback'),
    path('feedback/<int:pk>/', views.feedback_detail, name='feedback_detail'),
    path('feedback/<int:pk>/mark-read/', views.mark_feedback_read, name='mark_feedback_read'),
    
    # Treinamentos Avançados
    path('advanced-training/', views.training_dashboard, name='training_dashboard'),
    path('advanced-training/create/', views.advanced_training_create, name='advanced_training_create'),
    path('advanced-training/<int:pk>/', views.advanced_training_detail, name='advanced_training_detail'),
    path('advanced-training/<int:pk>/register/', views.training_register, name='training_register'),
    path('advanced-training/<int:pk>/registrations/', views.training_registrations, name='training_registrations'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export/', views.analytics_export, name='analytics_export'),
    
    # Relatórios
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/turnover/', views.turnover_report, name='turnover_report'),
    path('reports/performance/', views.performance_report, name='performance_report'),
    path('reports/training/', views.training_report, name='training_report'),
    
    # API
    path('api/employees/search/', views.employee_search_api, name='employee_search_api'),
    path('api/goals/progress/', views.goals_progress_api, name='goals_progress_api'),
    path('api/feedback/stats/', views.feedback_stats_api, name='feedback_stats_api'),
    path('api/analytics/charts/', views.analytics_charts_api, name='analytics_charts_api'),
    
    # Documentos
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
]
