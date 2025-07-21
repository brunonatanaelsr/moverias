from django.urls import path
from . import views_refactored

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views_refactored.communication_dashboard, name='dashboard'),
    
    # Mensagens
    path('messages/', views_refactored.messages_list, name='messages_list'),
    path('messages/<uuid:message_id>/', views_refactored.message_detail, name='message_detail'),
    path('messages/create/', views_refactored.create_message, name='create_message'),
    path('messages/<uuid:message_id>/edit/', views_refactored.edit_message, name='edit_message'),
    path('messages/<uuid:message_id>/delete/', views_refactored.delete_message, name='delete_message'),
    
    # Mensagens - Ações
    path('messages/<uuid:message_id>/mark-read/', views_refactored.mark_message_read, name='mark_message_read'),
    path('messages/<uuid:message_id>/mark-unread/', views_refactored.mark_message_unread, name='mark_message_unread'),
    path('messages/<uuid:message_id>/archive/', views_refactored.archive_message, name='archive_message'),
    path('messages/<uuid:message_id>/respond/', views_refactored.respond_to_message, name='respond_to_message'),
    
    # Ações em lote
    path('messages/bulk-action/', views_refactored.bulk_message_action, name='bulk_message_action'),
    
    # Respostas
    path('responses/', views_refactored.responses_list, name='responses_list'),
    path('responses/<int:response_id>/', views_refactored.response_detail, name='response_detail'),
    path('responses/<int:response_id>/edit/', views_refactored.edit_response, name='edit_response'),
    path('responses/<int:response_id>/delete/', views_refactored.delete_response, name='delete_response'),
    
    # Preferências
    path('preferences/', views_refactored.communication_preferences, name='preferences'),
    
    # Anexos
    path('messages/<uuid:message_id>/attachments/add/', views_refactored.add_attachment, name='add_attachment'),
    path('attachments/<int:attachment_id>/download/', views_refactored.download_attachment, name='download_attachment'),
    path('attachments/<int:attachment_id>/delete/', views_refactored.delete_attachment, name='delete_attachment'),
    
    # Analytics
    path('analytics/', views_refactored.communication_analytics, name='analytics'),
    path('analytics/engagement/', views_refactored.engagement_analytics, name='engagement_analytics'),
    path('analytics/response-rates/', views_refactored.response_rates_analytics, name='response_rates_analytics'),
    path('analytics/user-activity/', views_refactored.user_activity_analytics, name='user_activity_analytics'),
    
    # API endpoints
    path('api/messages/quick-send/', views_refactored.quick_send_message, name='quick_send_message'),
    path('api/messages/search/', views_refactored.search_messages, name='search_messages'),
    path('api/notifications/count/', views_refactored.notifications_count, name='notifications_count'),
    path('api/users/search/', views_refactored.search_users, name='search_users'),
    
    # Notificações
    path('notifications/', views_refactored.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views_refactored.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views_refactored.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Relatórios
    path('reports/', views_refactored.reports_dashboard, name='reports_dashboard'),
    path('reports/communication-summary/', views_refactored.communication_summary_report, name='communication_summary_report'),
    path('reports/user-engagement/', views_refactored.user_engagement_report, name='user_engagement_report'),
    path('reports/message-performance/', views_refactored.message_performance_report, name='message_performance_report'),
    
    # Configurações administrativas
    path('admin/settings/', views_refactored.admin_communication_settings, name='admin_settings'),
    path('admin/templates/', views_refactored.manage_message_templates, name='manage_templates'),
    path('admin/users/', views_refactored.manage_communication_users, name='manage_users'),
    
    # Exportação
    path('export/messages/', views_refactored.export_messages, name='export_messages'),
    path('export/analytics/', views_refactored.export_analytics, name='export_analytics'),
    
    # Migração de dados legados
    path('migrate/legacy-data/', views_refactored.migrate_legacy_data, name='migrate_legacy_data'),
]
