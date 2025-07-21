"""
URLs para o módulo de atividades dos beneficiários.
"""

from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # Dashboard principal
    path(
        'beneficiary/<int:beneficiary_id>/dashboard/',
        views.beneficiary_activities_dashboard,
        name='beneficiary_dashboard'
    ),
    
    # Lista e CRUD de atividades
    path('', views.activities_list, name='activities_list'),
    path('create/', views.BeneficiaryActivityCreateView.as_view(), name='activity_create'),
    path('<uuid:pk>/', views.BeneficiaryActivityDetailView.as_view(), name='activity_detail'),
    path('<uuid:pk>/edit/', views.BeneficiaryActivityUpdateView.as_view(), name='activity_edit'),
    
    # Sessões
    path('<uuid:activity_id>/session/create/', views.activity_session_create, name='session_create'),
    path('session/<uuid:session_id>/attendance/', views.attendance_record, name='attendance_record'),
    
    # Feedback e notas
    path('<uuid:activity_id>/feedback/', views.activity_feedback, name='activity_feedback'),
    path('<uuid:activity_id>/note/create/', views.activity_note_create, name='note_create'),
    
    # APIs
    path(
        'api/beneficiary/<int:beneficiary_id>/activities/',
        views.beneficiary_activities_api,
        name='beneficiary_activities_api'
    ),
    path('api/metrics/', views.activities_metrics_api, name='activities_metrics_api'),
    
    # Relatórios
    path('reports/', views.activities_report, name='activities_report'),
]
