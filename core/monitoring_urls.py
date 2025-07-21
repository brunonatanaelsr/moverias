"""
Monitoring URLs
"""
from django.urls import path
from . import monitoring_views

urlpatterns = [
    # Basic health checks
    path('health/', monitoring_views.health_check, name='health_check'),
    path('health/detailed/', monitoring_views.health_detailed, name='health_detailed'),
    
    # Dashboard views
    path('dashboard/', monitoring_views.MonitoringDashboardView.as_view(), name='monitoring_dashboard'),
    path('config/', monitoring_views.MonitoringConfigView.as_view(), name='monitoring_config'),
    path('widget/', monitoring_views.monitoring_widget, name='monitoring_widget'),
    
    # API endpoints
    path('api/health/', monitoring_views.SystemHealthAPIView.as_view(), name='api_system_health'),
    path('api/history/', monitoring_views.MonitoringHistoryAPIView.as_view(), name='api_monitoring_history'),
    path('api/stats/', monitoring_views.SystemStatsAPIView.as_view(), name='api_system_stats'),
    path('api/jobs/', monitoring_views.BackgroundJobsAPIView.as_view(), name='api_background_jobs'),
    
    # Test endpoints
    path('test/', monitoring_views.test_monitoring, name='test_monitoring'),
]
