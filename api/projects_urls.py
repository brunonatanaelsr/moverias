"""
URLs da API para projetos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import project_views

router = DefaultRouter()
router.register(r'projects', project_views.ProjectViewSet)
router.register(r'enrollments', project_views.ProjectEnrollmentViewSet)
router.register(r'sessions', project_views.ProjectSessionViewSet)
router.register(r'attendances', project_views.ProjectAttendanceViewSet)
router.register(r'evaluations', project_views.ProjectEvaluationViewSet)
router.register(r'resources', project_views.ProjectResourceViewSet)

app_name = 'api_projects'

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints adicionais
    path('stats/', project_views.ProjectStatsAPIView.as_view(), name='stats'),
    path('<int:project_id>/participants/', project_views.ProjectParticipantsAPIView.as_view(), name='participants'),
    path('<int:project_id>/attendance-report/', project_views.AttendanceReportAPIView.as_view(), name='attendance_report'),
    path('sessions/<int:session_id>/take-attendance/', project_views.TakeAttendanceAPIView.as_view(), name='take_attendance'),
]
