# ===================================
# MÓDULO DE CHAT - CONSUMIDORES WEBSOCKET
# ===================================

import json
import logging
from datetime import datetime
from typing import Dict, Set

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .models import ChatChannel, ChatMessage, ChatChannelMembership, ChatReaction

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumidor WebSocket para chat em tempo real
    Gerencia conexões, mensagens, reações e indicadores de digitação
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = None
        self.channel_group_name = None
        self.user = None
        self.typing_users: Set[int] = set()

    async def connect(self):
        """Conectar usuário ao canal de chat"""
        try:
            # Obter ID do canal da URL
            self.channel_id = self.scope['url_route']['kwargs']['channel_id']
            self.channel_group_name = f'chat_{self.channel_id}'
            self.user = self.scope['user']

            # Verificar se usuário está autenticado
            if not self.user.is_authenticated:
                logger.warning(f"Tentativa de conexão não autenticada no canal {self.channel_id}")
                await self.close()
                return

            # Verificar se usuário tem acesso ao canal
            has_access = await self.check_channel_access()
            if not has_access:
                logger.warning(f"Usuário {self.user.id} sem acesso ao canal {self.channel_id}")
                await self.close()
                return

            # Juntar ao grupo do canal
            await self.channel_layer.group_add(
                self.channel_group_name,
                self.channel_name
            )

            # Aceitar conexão
            await self.accept()

            # Notificar outros usuários sobre conexão
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name(),
                    'status': 'online'
                }
            )

            logger.info(f"Usuário {self.user.id} conectado ao canal {self.channel_id}")

        except Exception as e:
            logger.error(f"Erro na conexão WebSocket: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Desconectar usuário do canal"""
        try:
            if self.channel_group_name:
                # Notificar outros usuários sobre desconexão
                await self.channel_layer.group_send(
                    self.channel_group_name,
                    {
                        'type': 'user_status',
                        'user_id': self.user.id if self.user else None,
                        'user_name': self.user.get_full_name() if self.user else 'Usuário',
                        'status': 'offline'
                    }
                )

                # Sair do grupo
                await self.channel_layer.group_discard(
                    self.channel_group_name,
                    self.channel_name
                )

            logger.info(f"Usuário {self.user.id if self.user else 'desconhecido'} "
                       f"desconectado do canal {self.channel_id} (código: {close_code})")

        except Exception as e:
            logger.error(f"Erro na desconexão WebSocket: {e}")

    async def receive(self, text_data):
        """Receber mensagem do WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Roteamento de mensagens por tipo
            if message_type == 'message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing_indicator(data)
            elif message_type == 'reaction':
                await self.handle_message_reaction(data)
            elif message_type == 'ping':
                await self.handle_ping()
            else:
                logger.warning(f"Tipo de mensagem desconhecido: {message_type}")
                await self.send_error("Tipo de mensagem não suportado")

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            await self.send_error("Formato de mensagem inválido")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            await self.send_error("Erro interno do servidor")

    async def handle_chat_message(self, data):
        """Processar mensagem de chat"""
        try:
            content = data.get('content', '').strip()
            temp_id = data.get('temp_id')
            
            if not content:
                await self.send_error("Conteúdo da mensagem não pode estar vazio")
                return

            # Validar tamanho da mensagem
            if len(content) > 2000:
                await self.send_error("Mensagem muito longa (máximo 2000 caracteres)")
                return

            # Salvar mensagem no banco
            message = await self.save_message(content)
            if not message:
                await self.send_error("Erro ao salvar mensagem")
                return

            # Preparar dados da mensagem para broadcast
            message_data = {
                'id': str(message.id),
                'temp_id': temp_id,
                'content': message.content,
                'message_type': message.message_type,
                'channel_id': str(message.channel.id),
                'sender': {
                    'id': message.sender.id,
                    'full_name': message.sender.get_full_name(),
                    'avatar': message.sender.profile.avatar.url if hasattr(message.sender, 'profile') and message.sender.profile.avatar else None
                },
                'created_at': message.created_at.isoformat(),
                'edited': False,
                'attachments': [],
                'reactions': []
            }

            # Enviar mensagem para todos no grupo
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )

            # Atualizar analytics
            await self.update_analytics(message)

        except Exception as e:
            logger.error(f"Erro ao processar mensagem de chat: {e}")
            await self.send_error("Erro ao enviar mensagem")

    async def handle_typing_indicator(self, data):
        """Processar indicador de digitação"""
        try:
            is_typing = data.get('typing', False)
            
            # Enviar indicador para outros usuários no grupo
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'typing_indicator',
                    'user': {
                        'id': self.user.id,
                        'full_name': self.user.get_full_name()
                    },
                    'typing': is_typing,
                    'sender_channel_name': self.channel_name  # Para não enviar de volta
                }
            )

        except Exception as e:
            logger.error(f"Erro ao processar indicador de digitação: {e}")

    async def handle_message_reaction(self, data):
        """Processar reação à mensagem"""
        try:
            message_id = data.get('message_id')
            emoji = data.get('emoji')
            
            if not message_id or not emoji:
                await self.send_error("ID da mensagem e emoji são obrigatórios")
                return

            # Alternar reação
            reaction_data = await self.toggle_reaction(message_id, emoji)
            if not reaction_data:
                await self.send_error("Erro ao processar reação")
                return

            # Enviar atualização de reação para todos no grupo
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'emoji': emoji,
                    'user_id': self.user.id,
                    'action': reaction_data['action'],
                    'reactions': reaction_data['reactions']
                }
            )

        except Exception as e:
            logger.error(f"Erro ao processar reação: {e}")
            await self.send_error("Erro ao processar reação")

    async def handle_ping(self):
        """Responder a ping com pong"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))

    # ===================================
    # HANDLERS DE GRUPO
    # ===================================

    async def chat_message(self, event):
        """Enviar mensagem de chat para WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Enviar indicador de digitação para WebSocket"""
        # Não enviar de volta para o remetente
        if event.get('sender_channel_name') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': event['user'],
            'typing': event['typing']
        }))

    async def message_reaction(self, event):
        """Enviar reação de mensagem para WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'user_id': event['user_id'],
            'action': event['action'],
            'reactions': event['reactions']
        }))

    async def user_status(self, event):
        """Enviar status do usuário para WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'status': event['status']
        }))

    async def channel_update(self, event):
        """Enviar atualização do canal para WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'channel_update',
            'channel': event['channel']
        }))

    # ===================================
    # MÉTODOS DE BANCO DE DADOS
    # ===================================

    @database_sync_to_async
    def check_channel_access(self):
        """Verificar se usuário tem acesso ao canal"""
        try:
            channel = ChatChannel.objects.get(id=self.channel_id)
            return channel.members.filter(id=self.user.id).exists()
        except ChatChannel.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """Salvar mensagem no banco de dados"""
        try:
            channel = ChatChannel.objects.get(id=self.channel_id)
            
            # Verificar se usuário ainda tem acesso
            if not channel.members.filter(id=self.user.id).exists():
                return None

            message = ChatMessage.objects.create(
                channel=channel,
                sender=self.user,
                content=content,
                message_type='text'
            )

            # Atualizar timestamp de última leitura do remetente
            try:
                membership = ChatChannelMembership.objects.get(
                    user=self.user,
                    channel=channel
                )
                membership.last_read_at = timezone.now()
                membership.save(update_fields=['last_read_at'])
            except ChatChannelMembership.DoesNotExist:
                pass

            return message

        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            return None

    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        """Alternar reação na mensagem"""
        try:
            message = ChatMessage.objects.get(id=message_id)
            
            # Verificar acesso ao canal
            if not message.channel.members.filter(id=self.user.id).exists():
                return None

            # Verificar se reação já existe
            existing_reaction = ChatReaction.objects.filter(
                message=message,
                user=self.user,
                emoji=emoji
            ).first()

            if existing_reaction:
                existing_reaction.delete()
                action = 'removed'
            else:
                ChatReaction.objects.create(
                    message=message,
                    user=self.user,
                    emoji=emoji
                )
                action = 'added'

            # Obter todas as reações da mensagem
            reactions = ChatReaction.objects.filter(message=message)
            reactions_data = {}

            for reaction in reactions:
                if reaction.emoji not in reactions_data:
                    reactions_data[reaction.emoji] = {
                        'count': 0,
                        'users': []
                    }
                reactions_data[reaction.emoji]['count'] += 1
                reactions_data[reaction.emoji]['users'].append(reaction.user.id)

            return {
                'action': action,
                'reactions': reactions_data
            }

        except Exception as e:
            logger.error(f"Erro ao alternar reação: {e}")
            return None

    @database_sync_to_async
    def update_analytics(self, message):
        """Atualizar analytics do chat"""
        try:
            from .models import ChatAnalytics
            
            analytics, created = ChatAnalytics.objects.get_or_create(
                channel=message.channel,
                date=timezone.now().date(),
                defaults={
                    'messages_count': 0,
                    'active_users_count': 0
                }
            )
            
            analytics.messages_count += 1
            analytics.save(update_fields=['messages_count'])
            
        except Exception as e:
            logger.error(f"Erro ao atualizar analytics: {e}")

    # ===================================
    # MÉTODOS UTILITÁRIOS
    # ===================================

    async def send_error(self, message):
        """Enviar mensagem de erro para o cliente"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_success(self, message, data=None):
        """Enviar mensagem de sucesso para o cliente"""
        response = {
            'type': 'success',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        
        if data:
            response['data'] = data
            
        await self.send(text_data=json.dumps(response))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumidor WebSocket para notificações gerais do usuário
    """
    
    async def connect(self):
        """Conectar usuário às suas notificações"""
        try:
            self.user = self.scope['user']
            
            if not self.user.is_authenticated:
                await self.close()
                return

            self.notification_group_name = f'notifications_{self.user.id}'
            
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"Usuário {self.user.id} conectado às notificações")
            
        except Exception as e:
            logger.error(f"Erro na conexão de notificações: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Desconectar das notificações"""
        try:
            if hasattr(self, 'notification_group_name'):
                await self.channel_layer.group_discard(
                    self.notification_group_name,
                    self.channel_name
                )
            logger.info(f"Usuário {self.user.id if self.user else 'desconhecido'} "
                       f"desconectado das notificações")
        except Exception as e:
            logger.error(f"Erro na desconexão de notificações: {e}")

    async def notification(self, event):
        """Enviar notificação para usuário"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
