from django.urls import path
from . import views

app_name = 'workshops'

urlpatterns = [
    # Oficinas
    path('', views.WorkshopListView.as_view(), name='workshop_list'),
    path('create/', views.WorkshopCreateView.as_view(), name='workshop_create'),
    path('<int:pk>/', views.WorkshopDetailView.as_view(), name='workshop_detail'),
    path('<int:pk>/edit/', views.WorkshopUpdateView.as_view(), name='workshop_edit'),
    path('<int:workshop_id>/report/', views.workshop_report, name='workshop_report'),
    
    # Sessões
    path('<int:workshop_id>/sessions/', views.SessionListView.as_view(), name='session_list'),
    path('<int:workshop_id>/sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:session_id>/attendance/', views.attendance_register, name='attendance_register'),
    
    # Inscrições
    path('<int:workshop_id>/enrollments/', views.enrollment_list, name='enrollment_list'),
    path('<int:workshop_id>/enrollments/create/', views.enrollment_create, name='enrollment_create'),
]
