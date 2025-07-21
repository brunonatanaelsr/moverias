"""
Sistema de notificações em tempo real usando Server-Sent Events (SSE).
"""
import json
import time
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from notifications.models import Notification, NotificationChannel

logger = logging.getLogger(__name__)


class NotificationStreamView(View):
    """
    View para streaming de notificações em tempo real via Server-Sent Events.
    """
    
    @method_decorator(login_required)
    def get(self, request):
        """
        Estabelece conexão SSE para notificações em tempo real.
        """
        def event_stream():
            # Cache key para o usuário
            cache_key = f"notifications_stream_{request.user.id}"
            last_check = cache.get(cache_key, timezone.now())
            
            # Enviar evento inicial de conexão
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'timestamp': timezone.now().isoformat()})}\n\n"
            
            while True:
                try:
                    # Verificar novas notificações
                    new_notifications = Notification.objects.filter(
                        recipient=request.user,
                        created_at__gt=last_check,
                        status__in=['pending', 'sent', 'delivered']
                    ).order_by('-created_at')
                    
                    if new_notifications.exists():
                        for notification in new_notifications:
                            data = {
                                'id': notification.id,
                                'title': notification.title,
                                'message': notification.message,
                                'type': notification.type,
                                'timestamp': notification.created_at.isoformat(),
                                'url': notification.action_url if hasattr(notification, 'action_url') else None
                            }
                            
                            yield f"event: notification\ndata: {json.dumps(data)}\n\n"
                        
                        # Atualizar timestamp da última verificação
                        last_check = timezone.now()
                        cache.set(cache_key, last_check, timeout=3600)  # 1 hora
                    
                    # Enviar heartbeat a cada 30 segundos
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': timezone.now().isoformat()})}\n\n"
                    
                    # Aguardar antes da próxima verificação
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Erro no stream de notificações para usuário {request.user.id}: {e}")
                    yield f"event: error\ndata: {json.dumps({'error': 'Stream error', 'message': str(e)})}\n\n"
                    break
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response


@login_required
def notification_count_api(request):
    """
    API para obter contagem de notificações não lidas.
    """
    unread_count = Notification.objects.filter(
        recipient=request.user,
        status__in=['pending', 'sent', 'delivered']
    ).count()
    
    return HttpResponse(
        json.dumps({'unread_count': unread_count}),
        content_type='application/json'
    )


@login_required  
@csrf_exempt
def mark_notification_read_api(request, notification_id):
    """
    API para marcar notificação como lida.
    """
    if request.method == 'POST':
        try:
            notification = get_object_or_404(
                Notification,
                id=notification_id,
                recipient=request.user
            )
            notification.mark_as_read()
            
            return HttpResponse(
                json.dumps({'success': True, 'message': 'Notificação marcada como lida'}),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )
    
    return HttpResponse(
        json.dumps({'error': 'Método não permitido'}),
        content_type='application/json',
        status=405
    )


@login_required
@csrf_exempt
def mark_all_read_api(request):
    """
    API para marcar todas as notificações como lidas.
    """
    if request.method == 'POST':
        try:
            notifications = Notification.objects.filter(
                recipient=request.user,
                status__in=['pending', 'sent', 'delivered']
            )
            
            count = notifications.count()
            notifications.update(
                status='read',
                read_at=timezone.now()
            )
            
            return HttpResponse(
                json.dumps({
                    'success': True, 
                    'message': f'{count} notificações marcadas como lidas'
                }),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )
    
    return HttpResponse(
        json.dumps({'error': 'Método não permitido'}),
        content_type='application/json',
        status=405
    )


class NotificationWebSocketConsumer:
    """
    Consumer WebSocket para notificações (para uso futuro com Django Channels).
    Este é um placeholder para implementação futura.
    """
    
    def __init__(self):
        self.user = None
        self.notifications_group = None
    
    async def connect(self):
        """Conectar ao WebSocket"""
        if self.scope['user'].is_authenticated:
            self.user = self.scope['user']
            self.notifications_group = f"notifications_{self.user.id}"
            
            # Adicionar ao grupo de notificações do usuário
            await self.channel_layer.group_add(
                self.notifications_group,
                self.channel_name
            )
            
            await self.accept()
            
            # Enviar notificações não lidas
            await self.send_unread_notifications()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        """Desconectar do WebSocket"""
        if self.notifications_group:
            await self.channel_layer.group_discard(
                self.notifications_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receber mensagem do WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            elif action == 'mark_all_read':
                await self.mark_all_notifications_read()
            elif action == 'get_count':
                await self.send_unread_count()
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
    
    async def send_notification(self, event):
        """Enviar notificação para o cliente"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def send_unread_notifications(self):
        """Enviar notificações não lidas"""
        # Implementar busca de notificações não lidas
        pass
    
    async def send_unread_count(self):
        """Enviar contagem de notificações não lidas"""
        # Implementar contagem
        pass
    
    async def mark_notification_read(self, notification_id):
        """Marcar notificação como lida"""
        # Implementar marcação como lida
        pass
    
    async def mark_all_notifications_read(self):
        """Marcar todas as notificações como lidas"""
        # Implementar marcação de todas como lidas
        pass
    
    async def send_error(self, message):
        """Enviar erro para o cliente"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))


def send_real_time_notification(user, notification_data):
    """
    Função helper para enviar notificação em tempo real.
    """
    try:
        # Cache para notificação
        cache_key = f"realtime_notification_{user.id}_{int(time.time())}"
        cache.set(cache_key, notification_data, timeout=300)  # 5 minutos
        
        # Se usando Django Channels, enviar via WebSocket
        # from channels.layers import get_channel_layer
        # channel_layer = get_channel_layer()
        # if channel_layer:
        #     async_to_sync(channel_layer.group_send)(
        #         f"notifications_{user.id}",
        #         {
        #             'type': 'send_notification',
        #             'notification': notification_data
        #         }
        #     )
        
        logger.info(f"Notificação em tempo real enviada para usuário {user.id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação em tempo real: {e}")
        return False


def create_and_send_notification(user, title, message, notification_type='general', action_url=None):
    """
    Função helper para criar e enviar notificação.
    """
    try:
        # Criar notificação no banco
        # Obter canal in_app (padrão)
        try:
            channel = NotificationChannel.objects.get(name='in_app')
        except NotificationChannel.DoesNotExist:
            # Criar canal padrão se não existir
            channel = NotificationChannel.objects.create(
                name='in_app',
                display_name='In-App',
                is_active=True
            )
        
        notification = Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            type=notification_type,
            channel=channel
        )
        
        # Preparar dados para tempo real
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'timestamp': notification.created_at.isoformat(),
            'url': action_url
        }
        
        # Enviar em tempo real
        send_real_time_notification(user, notification_data)
        
        return notification
        
    except Exception as e:
        logger.error(f"Erro ao criar notificação: {e}")
        return None


class NotificationMiddleware:
    """
    Middleware para adicionar informações de notificação ao contexto.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Adicionar dados de notificação ao contexto"""
        if request.user.is_authenticated:
            # Cache para evitar consultas repetidas
            cache_key = f"notifications_context_{request.user.id}"
            cached_data = cache.get(cache_key)
            
            if cached_data is None:
                unread_notifications = Notification.objects.filter(
                    recipient=request.user,
                    status__in=['pending', 'sent', 'delivered']
                ).order_by('-created_at')[:5]  # Últimas 5 não lidas
                
                unread_count = Notification.objects.filter(
                    recipient=request.user,
                    status__in=['pending', 'sent', 'delivered']
                ).count()
                
                cached_data = {
                    'unread_notifications': list(unread_notifications.values(
                        'id', 'title', 'message', 'type', 'created_at'
                    )),
                    'unread_notifications_count': unread_count
                }
                
                # Cache por 2 minutos
                cache.set(cache_key, cached_data, timeout=120)
            
            # Adicionar ao contexto da request
            request.notifications_data = cached_data


def notification_context_processor(request):
    """
    Context processor para notificações.
    """
    if request.user.is_authenticated and hasattr(request, 'notifications_data'):
        return request.notifications_data
    
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0
    }


# Signals para notificações automáticas
from django.db.models.signals import post_save
from django.dispatch import receiver
from members.models import Beneficiary
from projects.models import Project, ProjectEnrollment


@receiver(post_save, sender=Beneficiary)
def notify_new_beneficiary(sender, instance, created, **kwargs):
    """
    Notificar quando nova beneficiária é cadastrada.
    """
    if created:
        # Notificar administradores
        from django.contrib.auth.models import Group
        try:
            admin_group = Group.objects.get(name='Admin')
            for user in admin_group.user_set.all():
                create_and_send_notification(
                    user=user,
                    title='Nova Beneficiária Cadastrada',
                    message=f'A beneficiária {instance.nome_completo} foi cadastrada no sistema.',
                    notification_type='system_update'
                )
        except Group.DoesNotExist:
            pass


@receiver(post_save, sender=Project)
def notify_new_project(sender, instance, created, **kwargs):
    """
    Notificar quando novo projeto é criado.
    """
    if created:
        # Notificar equipe técnica
        from django.contrib.auth.models import Group
        try:
            tecnica_group = Group.objects.get(name='Técnica')
            for user in tecnica_group.user_set.all():
                if user != instance.coordinator:  # Não notificar o próprio coordenador
                    create_and_send_notification(
                        user=user,
                        title='Novo Projeto Criado',
                        message=f'O projeto "{instance.name}" foi criado por {instance.coordinator.get_full_name() or instance.coordinator.username}.',
                        notification_type='project_invitation'
                    )
        except Group.DoesNotExist:
            pass


@receiver(post_save, sender=ProjectEnrollment)
def notify_new_participant(sender, instance, created, **kwargs):
    """
    Notificar quando nova participante é adicionada ao projeto.
    """
    if created:
        # Notificar coordenador do projeto
        create_and_send_notification(
            user=instance.project.coordinator,
            title='Nova Participante no Projeto',
            message=f'{instance.user.get_full_name()} foi adicionada ao projeto "{instance.project.name}".',
            notification_type='project_invitation'
        )


# Função para envio de notificações por email (opcional)
def send_email_notification(user, notification):
    """
    Enviar notificação por email (se habilitado nas preferências).
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Verificar se usuário tem notificação por email habilitada
        from notifications.models import NotificationPreference
        try:
            preference = NotificationPreference.objects.get(user=user)
            if not preference.email_notifications:
                return False
        except NotificationPreference.DoesNotExist:
            # Se não tem preferência, assumir que quer receber
            pass
        
        # Renderizar template de email
        subject = f"[Move Marias] {notification.title}"
        message = render_to_string('notifications/email_notification.html', {
            'user': user,
            'notification': notification,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
        })
        
        send_mail(
            subject=subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=message,
            fail_silently=False
        )
        
        logger.info(f"Notificação por email enviada para {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação por email: {e}")
        return False
