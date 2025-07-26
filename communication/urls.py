# ===================================
# MÓDULO DE COMUNICAÇÃO - URLs INTEGRADAS
# ===================================

from django.urls import path, include
from . import views_simple

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views_simple.communication_dashboard, name='dashboard'),
    
    # Comunicados
    path('announcements/', views_simple.announcements_list, name='announcements_list'),
    path('announcements/<int:announcement_id>/', views_simple.announcement_detail, name='announcement_detail'),
    path('announcements/create/', views_simple.create_announcement, name='create_announcement'),
    path('announcements/<int:announcement_id>/edit/', views_simple.edit_announcement, name='edit_announcement'),
    path('announcements/<int:announcement_id>/delete/', views_simple.delete_announcement, name='delete_announcement'),
    
    # Mensagens
    path('messages/', views_simple.messages_list, name='messages_list'),
    path('messages/<int:message_id>/', views_simple.message_detail, name='message_detail'),
    path('messages/create/', views_simple.create_message, name='create_message'),
    path('messages/<int:message_id>/read/', views_simple.mark_message_read, name='mark_message_read'),
    
    # Newsletters
    path('newsletters/', views_simple.newsletters_list, name='newsletters_list'),
    path('newsletters/<int:newsletter_id>/', views_simple.newsletter_detail, name='newsletter_detail'),
    
    # Políticas
    path('policies/', views_simple.policies_list, name='policies_list'),
    path('policies/<int:policy_id>/', views_simple.policy_detail, name='policy_detail'),
    path('policies/<int:policy_id>/acknowledge/', views_simple.acknowledge_policy, name='acknowledge_policy'),
    
    # Feedback
    path('feedback/', views_simple.feedback_list, name='feedback_list'),
    path('feedback/create/', views_simple.create_feedback, name='create_feedback'),
    
    # Enquetes
    path('surveys/', views_simple.surveys_list, name='surveys_list'),
    path('surveys/<int:survey_id>/', views_simple.survey_detail, name='survey_detail'),
    
    # Recursos de Aprendizado
    path('resources/', views_simple.resources_list, name='resources_list'),
    path('resources/<int:resource_id>/', views_simple.resource_detail, name='resource_detail'),
    
    # Analytics
    path('analytics/', views_simple.communication_analytics, name='analytics'),
    
    # APIs
    path('api/metrics/', views_simple.metrics_api, name='metrics_api'),
    path('api/search/', views_simple.search_api, name='search_api'),
]
