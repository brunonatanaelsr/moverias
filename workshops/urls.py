from django.urls import path
from . import views

app_name = 'workshops'

urlpatterns = [
    # Workshop CRUD
    path('', views.WorkshopListView.as_view(), name='workshop-list'),
    path('create/', views.WorkshopCreateView.as_view(), name='workshop-create'),
    path('<int:pk>/', views.WorkshopDetailView.as_view(), name='workshop-detail'),
    path('<int:pk>/edit/', views.WorkshopUpdateView.as_view(), name='workshop-update'),
    path('<int:pk>/delete/', views.WorkshopDeleteView.as_view(), name='workshop-delete'),
    path('<int:pk>/report/', views.workshop_report, name='workshop-report'),
    
    # Workshop Enrollment CRUD
    path('enrollments/', views.WorkshopEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/create/', views.WorkshopEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('enrollments/<int:pk>/edit/', views.WorkshopEnrollmentUpdateView.as_view(), name='enrollment-update'),
    path('enrollments/<int:pk>/delete/', views.WorkshopEnrollmentDeleteView.as_view(), name='enrollment-delete'),
    
    # Workshop Session CRUD
    path('sessions/', views.WorkshopSessionListView.as_view(), name='session-list'),
    path('sessions/create/', views.WorkshopSessionCreateView.as_view(), name='session-create'),
    path('sessions/<int:pk>/edit/', views.WorkshopSessionUpdateView.as_view(), name='session-update'),
    path('sessions/<int:pk>/delete/', views.WorkshopSessionDeleteView.as_view(), name='session-delete'),
    
    # Attendance Management
    path('sessions/<int:session_id>/attendance/', views.bulk_attendance, name='bulk-attendance'),
    
    # Workshop Evaluation CRUD
    path('evaluations/', views.WorkshopEvaluationListView.as_view(), name='evaluation-list'),
    path('evaluations/create/', views.WorkshopEvaluationCreateView.as_view(), name='evaluation-create'),
    
    # API endpoints
    path('api/stats/<int:workshop_id>/', views.get_workshop_stats, name='workshop-stats'),
]
