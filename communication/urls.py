from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views.communication_dashboard, name='dashboard'),
    
    # Comunicados/Anúncios
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<uuid:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    
    # Memorandos
    path('memos/', views.memo_list, name='memo_list'),
    path('memos/<uuid:pk>/', views.memo_detail, name='memo_detail'),
    path('memos/create/', views.create_memo, name='create_memo'),
    
    # Sugestões
    path('suggestions/', views.suggestion_list, name='suggestion_list'),
    path('suggestions/create/', views.suggestion_create, name='suggestion_create'),
    
    # Newsletters
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='newsletter_create'),
    
    # Configurações
    path('settings/', views.settings_view, name='settings'),
]
