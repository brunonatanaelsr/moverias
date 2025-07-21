from django.urls import path
from . import chat_widget_views

# URLs para o Chat Widget
chat_widget_urlpatterns = [
    path('api/chat/conversations/', chat_widget_views.chat_api_conversations, name='chat_api_conversations'),
    path('api/chat/users/', chat_widget_views.chat_api_users, name='chat_api_users'),
    path('api/chat/messages/<int:user_id>/', chat_widget_views.chat_api_messages, name='chat_api_messages'),
    path('api/chat/send-message/', chat_widget_views.chat_api_send_message, name='chat_api_send_message'),
    path('api/chat/current-user/', chat_widget_views.chat_api_current_user, name='chat_api_current_user'),
    path('api/chat/mark-as-read/<uuid:channel_id>/', chat_widget_views.chat_api_mark_as_read, name='chat_api_mark_as_read'),
    path('api/chat/user-status/<int:user_id>/', chat_widget_views.chat_api_user_status, name='chat_api_user_status'),
    path('api/chat/channels/', chat_widget_views.chat_api_channels, name='chat_api_channels'),
]
