from django.urls import path, include
from . import views

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Announcements
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    
    # Internal Memos
    path('memos/', views.memo_list, name='memo_list'),
    path('memos/create/', views.memo_create, name='memo_create'),
    path('memos/<int:pk>/', views.memo_detail, name='memo_detail'),
    path('memos/<int:pk>/edit/', views.memo_edit, name='memo_edit'),
    path('memos/<int:pk>/delete/', views.memo_delete, name='memo_delete'),
    
    # Newsletters
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='newsletter_create'),
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<int:pk>/edit/', views.newsletter_edit, name='newsletter_edit'),
    path('newsletters/<int:pk>/delete/', views.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<int:pk>/pdf/', views.newsletter_pdf, name='newsletter_pdf'),
    path('newsletters/<int:pk>/analytics/', views.newsletter_analytics_export, name='newsletter_analytics_export'),
    
    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    
    # Announcement Board
    path('board/', views.announcement_board, name='announcement_board'),
    
    # Settings and Configuration
    path('settings/', views.settings, name='settings'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('automation/rules/create/', views.automation_rule_create, name='automation_rule_create'),
    path('automation/rules/<int:pk>/edit/', views.automation_rule_edit, name='automation_rule_edit'),
    path('automation/rules/<int:pk>/delete/', views.automation_rule_delete, name='automation_rule_delete'),
    path('automation/rules/<int:pk>/toggle/', views.automation_rule_toggle, name='automation_rule_toggle'),
    
    # API endpoints
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/mark-as-read/', views.mark_as_read_api, name='mark_as_read_api'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/upload/', views.upload_api, name='upload_api'),
]
