from django.urls import path, include
from . import views
from . import monitoring_views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('config/email/', views.email_config, name='email_config'),
    
    # Health checks
    path('health/', monitoring_views.health_check, name='health_check'),
    path('health/detailed/', monitoring_views.health_detailed, name='health_detailed'),
    
    # System monitoring
    path('monitoring/', monitoring_views.system_monitoring_dashboard, name='system_monitoring'),
    path('monitoring/refresh/', monitoring_views.refresh_monitoring, name='refresh_monitoring'),
    path('monitoring/clear-cache/', monitoring_views.clear_cache, name='clear_cache'),
    path('monitoring/alerts/', monitoring_views.system_alerts, name='system_alerts'),
    
    # Reports
    path('reports/generate/', monitoring_views.generate_report, name='generate_report'),
    path('reports/export-alerts/', monitoring_views.export_alerts, name='export_alerts'),
    path('reports/clear-alerts/', monitoring_views.clear_alerts, name='clear_alerts'),
]
