"""
URLs para o sistema de notificações
"""
from django.urls import path, include
from django.contrib.auth.decorators import login_required

from . import views
from .realtime import (
    NotificationStreamView, notification_count_api, 
    mark_notification_read_api, mark_all_read_api
)

app_name = 'notifications'

urlpatterns = [
    # Lista e visualização de notificações
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.NotificationDeleteView.as_view(), name='delete'),
    
    # Criação e edição de notificações (admin)
    path('create/', views.NotificationCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.NotificationUpdateView.as_view(), name='edit'),
    
    # Preferências do usuário
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
    
    # Ações AJAX
    path('mark-read/<int:notification_id>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('mark-important/<int:notification_id>/', views.mark_as_important, name='mark_important'),
    path('bulk-delete/', views.bulk_delete, name='bulk_delete'),
    path('bulk-mark-read/', views.bulk_mark_as_read, name='bulk_mark_read'),
    path('count/', views.notification_count, name='count'),
    path('popup/', views.notification_popup, name='popup'),
    path('stats/', views.notification_stats, name='stats'),
    path('test/create/', views.create_test_notifications, name='create_test'),
    
    # Busca
    path('search/', views.NotificationSearchView.as_view(), name='search'),
    
    # Analytics
    path('analytics/', views.notification_analytics, name='analytics'),
    
    # Exportar
    path('export/', views.NotificationExportView.as_view(), name='export'),
    
    # Canais de notificação
    path('channels/', views.NotificationChannelListView.as_view(), name='channels'),
    
    # Templates (admin)
    path('templates/', views.NotificationTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.NotificationTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.NotificationTemplateUpdateView.as_view(), name='template_edit'),
    
    # Teste
    path('test/', views.send_test_notification, name='test'),
    
    # API endpoints
    path('api/', include([
        path('list/', views.NotificationListView.as_view(), name='api_list'),
        path('count/', views.notification_count, name='api_count'),
        path('popup/', views.notification_popup, name='api_popup'),
        path('search/', views.NotificationSearchView.as_view(), name='api_search'),
        path('analytics/', views.notification_analytics, name='api_analytics'),
        path('stats/', views.notification_stats, name='api_stats'),
        path('mark-read/<int:notification_id>/', views.mark_as_read, name='api_mark_read'),
        path('mark-all-read/', views.mark_all_as_read, name='api_mark_all_read'),
        path('mark-important/<int:notification_id>/', views.mark_as_important, name='api_mark_important'),
        path('bulk-delete/', views.bulk_delete, name='api_bulk_delete'),
        path('bulk-mark-read/', views.bulk_mark_as_read, name='api_bulk_mark_read'),
    ])),
    
    # Real-time notifications
    path('stream/', NotificationStreamView.as_view(), name='notification-stream'),
    path('api/count/', notification_count_api, name='notification-count-api'),
    path('api/mark-read/<int:notification_id>/', mark_notification_read_api, name='mark-read-api'),
    path('api/mark-all-read/', mark_all_read_api, name='mark-all-read-api'),
]
