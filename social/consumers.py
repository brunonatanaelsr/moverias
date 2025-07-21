"""
WebSocket consumers para chat em tempo real
MoveMarias - Sistema de comunicação instantânea
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer para chat em tempo real"""
    
    async def connect(self):
        """Conecta ao WebSocket"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        
        # Verifica se o usuário está autenticado
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Junta ao grupo do chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notifica que o usuário entrou no chat
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket"""
        # Notifica que o usuário saiu do chat
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Remove do grupo do chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recebe mensagem do WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read':
                await self.handle_read(data)
            elif message_type == 'reaction':
                await self.handle_reaction(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensagem inválido'
            }))
    
    async def handle_message(self, data):
        """Processa mensagem de chat"""
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        # Salva a mensagem no banco de dados
        chat_message = await self.save_message(message)
        
        # Envia a mensagem para o grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': chat_message
            }
        )
    
    async def handle_typing(self, data):
        """Processa indicador de digitação"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': self.user.username,
                'is_typing': data.get('is_typing', False)
            }
        )
    
    async def handle_read(self, data):
        """Processa confirmação de leitura"""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_message_read(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'user': self.user.username
                }
            )
    
    async def handle_reaction(self, data):
        """Processa reação a mensagem"""
        message_id = data.get('message_id')
        reaction = data.get('reaction')
        
        if message_id and reaction:
            await self.save_reaction(message_id, reaction)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'reaction': reaction,
                    'user': self.user.username
                }
            )
    
    async def chat_message(self, event):
        """Envia mensagem para o WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Envia indicador de digitação"""
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))
    
    async def message_read(self, event):
        """Envia confirmação de leitura"""
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id'],
            'user': event['user']
        }))
    
    async def message_reaction(self, event):
        """Envia reação a mensagem"""
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'reaction': event['reaction'],
            'user': event['user']
        }))
    
    async def user_joined(self, event):
        """Notifica que um usuário entrou no chat"""
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': event['user'],
                'timestamp': event['timestamp']
            }))
    
    async def user_left(self, event):
        """Notifica que um usuário saiu do chat"""
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user': event['user'],
                'timestamp': event['timestamp']
            }))
    
    @database_sync_to_async
    def save_message(self, message):
        """Salva mensagem no banco de dados"""
        # Aqui você salvaria a mensagem em um modelo ChatMessage
        # Por enquanto, retornamos um objeto simulado
        return {
            'id': 1,
            'user': self.user.username,
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'room': self.room_name
        }
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Marca mensagem como lida"""
        # Aqui você marcaria a mensagem como lida no banco
        pass
    
    @database_sync_to_async
    def save_reaction(self, message_id, reaction):
        """Salva reação a mensagem"""
        # Aqui você salvaria a reação no banco
        pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer para notificações em tempo real"""
    
    async def connect(self):
        """Conecta ao WebSocket de notificações"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.notification_group_name = f'notifications_{self.user.id}'
        
        # Junta ao grupo de notificações do usuário
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket de notificações"""
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recebe dados do WebSocket"""
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
        except json.JSONDecodeError:
            pass
    
    async def send_notification(self, event):
        """Envia notificação para o usuário"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marca notificação como lida"""
        # Aqui você marcaria a notificação como lida no banco
        pass


class DashboardConsumer(AsyncWebsocketConsumer):
    """Consumer para atualizações do dashboard em tempo real"""
    
    async def connect(self):
        """Conecta ao WebSocket do dashboard"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.dashboard_group_name = 'dashboard_updates'
        
        # Junta ao grupo de atualizações do dashboard
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket do dashboard"""
        await self.channel_layer.group_discard(
            self.dashboard_group_name,
            self.channel_name
        )
    
    async def dashboard_update(self, event):
        """Envia atualização do dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))
