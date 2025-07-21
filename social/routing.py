"""
Roteamento ASGI para WebSockets
MoveMarias - Configuração de rotas assíncronas
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    path('ws/dashboard/', consumers.DashboardConsumer.as_asgi()),
]
