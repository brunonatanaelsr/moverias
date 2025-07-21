"""
URLs da API para notificações
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import notification_views

router = DefaultRouter()
router.register(r'notifications', notification_views.NotificationViewSet)
router.register(r'preferences', notification_views.NotificationPreferenceViewSet)
router.register(r'templates', notification_views.NotificationTemplateViewSet)

app_name = 'api_notifications'

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints adicionais
    path('send-bulk/', notification_views.SendBulkNotificationAPIView.as_view(), name='send_bulk'),
    path('mark-all-read/', notification_views.MarkAllReadAPIView.as_view(), name='mark_all_read'),
    path('stats/', notification_views.NotificationStatsAPIView.as_view(), name='stats'),
    path('channels/', notification_views.NotificationChannelListAPIView.as_view(), name='channels'),
]
