from django.urls import path, include
from . import views
from . import monitoring_views
from . import test_views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.global_search, name='global-search'),
    path('config/email/', views.email_config, name='email-config'),
    path('settings/', views.settings_view, name='settings'),
    path('audit-logs/', views.audit_logs, name='audit-logs'),
    
    # Test URLs (temporary)
    path('test-csrf/', test_views.test_csrf, name='test-csrf'),
    
    # Enhanced monitoring system
    path('monitoring/', include('core.monitoring_urls')),
    
    # Legacy health checks (for compatibility)
    path('health/', monitoring_views.health_check, name='health-check'),
    path('health/detailed/', monitoring_views.health_detailed, name='health-detailed'),
    
]
