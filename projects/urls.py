from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Lista de projetos
    path('', views.project_list, name='project-list'),
    path('<int:pk>/', views.project_detail, name='project-detail'),
    path('create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project-update'),
    
    # Matrículas em projetos
    path('enrollments/', views.project_enrollment_list, name='enrollment-list'),
    path('enrollment/create/', views.ProjectEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('enrollment/<int:pk>/', views.ProjectEnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollment/<int:pk>/edit/', views.ProjectEnrollmentUpdateView.as_view(), name='enrollment-update'),
    path('enrollment/<int:pk>/delete/', views.ProjectEnrollmentDeleteView.as_view(), name='enrollment-delete'),
    
    # Exportação
    path('<int:pk>/export/', views.export_project_data, name='project-export'),
]
