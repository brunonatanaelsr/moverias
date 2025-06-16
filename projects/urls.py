from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Lista de matrículas em projetos (página principal)
    path('', views.ProjectEnrollmentListView.as_view(), name='enrollment-list'),
    
    # CRUD para Projetos (entidade separada)
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    
    # CRUD para Matrículas em Projetos
    path('enrollment/create/', views.ProjectEnrollmentCreateView.as_view(), name='enrollment-create'),
    path('enrollment/<int:pk>/', views.ProjectEnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollment/<int:pk>/edit/', views.ProjectEnrollmentUpdateView.as_view(), name='enrollment-update'),
    path('enrollment/<int:pk>/delete/', views.ProjectEnrollmentDeleteView.as_view(), name='enrollment-delete'),
]
