from django.urls import path, include
from . import views
from .widget_urls import chat_widget_urlpatterns

app_name = 'chat'

urlpatterns = [
    # Chat principal
    path('', views.chat_home, name='home'),
    
    # Canais (channels)
    path('channels/', views.chat_home, name='channel_list'),
    path('channels/create/', views.channel_create, name='channel_create'),
    path('channels/<uuid:channel_id>/', views.channel_detail, name='channel_detail'),
    path('channels/<uuid:channel_id>/edit/', views.channel_edit, name='channel_edit'),
    path('channels/<uuid:channel_id>/members/', views.channel_members, name='channel_members'),
    
    # Mensagens diretas (DMs)
    path('dm/', views.dm_list, name='dm_list'),
    path('dm/<int:user_id>/', views.dm_conversation, name='dm_conversation'),
    
    # Mensagens
    path('send/', views.send_message, name='send_message'),
    path('channels/<uuid:channel_id>/send/', views.send_message, name='send_channel_message'),
    
    # API/AJAX
    path('api/channels/<uuid:channel_id>/messages/', views.get_messages, name='get_messages'),
    path('api/messages/', views.get_messages, name='get_all_messages'),
    
    # Reações
    path('api/messages/<uuid:message_id>/react/', views.toggle_reaction, name='toggle_reaction'),
    
    # Busca
    path('search/', views.search_messages, name='search'),
    
    # Notificações
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Busca
    path('search/', views.search_messages, name='search'),
    
    # Chat Widget APIs
    path('', include(chat_widget_urlpatterns)),
]
