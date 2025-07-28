# URLs para API do Chat Interno
from django.urls import path
from . import chat_api_views

app_name = 'chat_api'

urlpatterns = [
    path('users/', chat_api_views.chat_users, name='users'),
    path('unread-count/', chat_api_views.chat_unread_count, name='unread_count'),
    path('messages/<int:user_id>/', chat_api_views.chat_messages, name='messages'),
    path('send/', chat_api_views.chat_send_message, name='send_message'),
    path('online-users/', chat_api_views.chat_online_users, name='online_users'),
]
