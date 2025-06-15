from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Dashboard
    path('', views.hr_dashboard, name='dashboard'),
    
    # Funcionários
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    
    # Departamentos
    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    
    # Avaliações de Desempenho
    path('reviews/', views.performance_reviews, name='performance_reviews'),
    
    # Treinamentos
    path('trainings/', views.training_records, name='training_records'),
    
    # Relatórios
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    
    # API
    path('api/employees/search/', views.employee_search_api, name='employee_search_api'),
]
