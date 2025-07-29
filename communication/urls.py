# ===================================
# MÓDULO DE COMUNICAÇÃO - URLs INTEGRADAS
# ===================================

from django.urls import path, include
from . import views

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views.communication_dashboard, name='dashboard'),
    
    # Comunicados
    path('announcements/', views.announcements_list, name='announcements_list'),
    path('announcements/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcements/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    
    # Mensagens
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/create/', views.create_message, name='create_message'),
    path('messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    
    # Newsletters
    path('newsletters/', views.newsletters_list, name='newsletters_list'),
    path('newsletters/<int:newsletter_id>/', views.newsletter_detail, name='newsletter_detail'),
    
    # Políticas
    path('policies/', views.policies_list, name='policies_list'),
    path('policies/<int:policy_id>/', views.policy_detail, name='policy_detail'),
    path('policies/<int:policy_id>/acknowledge/', views.acknowledge_policy, name='acknowledge_policy'),
    
    # Feedback
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/create/', views.create_feedback, name='create_feedback'),
    
    # Enquetes
    path('surveys/', views.surveys_list, name='surveys_list'),
    path('surveys/<int:survey_id>/', views.survey_detail, name='survey_detail'),
    
    # Recursos de Aprendizado
    path('resources/', views.resources_list, name='resources_list'),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    
    # Analytics
    path('analytics/', views.communication_analytics, name='analytics'),
    
    # Configurações
    path('settings/', views.communication_settings, name='settings'),
    
    # APIs
    path('api/metrics/', views.metrics_api, name='metrics_api'),
    path('api/search/', views.search_api, name='search_api'),
]
