# ===================================
# MÓDULO DE CHAT - ROTEAMENTO WEBSOCKET
# ===================================

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat em tempo real
    re_path(r'ws/chat/(?P<channel_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Notificações do usuário
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
