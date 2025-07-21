from django.urls import path, include
from . import views
from .widget_urls import chat_widget_urlpatterns

app_name = 'chat'

urlpatterns = [
    # Chat principal
    path('', views.chat_home, name='home'),
    
    # Salas
    path('rooms/', views.chat_home, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<uuid:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<uuid:room_id>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<uuid:room_id>/members/', views.room_members, name='room_members'),
    
    # Mensagens
    path('rooms/<uuid:room_id>/send/', views.send_message, name='send_message'),
    
    # API/AJAX
    path('api/rooms/<uuid:room_id>/messages/', views.get_messages, name='get_messages'),
    
    # Notificações
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Busca
    path('search/', views.search_messages, name='search'),
    
    # Chat Widget APIs
    path('', include(chat_widget_urlpatterns)),
]
