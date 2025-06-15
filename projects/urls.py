from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Lista de projetos
    path('', views.ProjectListView.as_view(), name='list'),
    
    # CRUD projetos
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='edit'),
    
    # Matrículas
    path('enrollment/create/', views.ProjectEnrollmentCreateView.as_view(), name='enrollment_create'),
    path('enrollment/<int:pk>/', views.ProjectEnrollmentDetailView.as_view(), name='enrollment_detail'),
    path('enrollment/<int:pk>/edit/', views.ProjectEnrollmentUpdateView.as_view(), name='enrollment_edit'),
]
