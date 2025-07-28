# API Views para Chat Interno
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

@login_required
def chat_users(request):
    """Lista de usuários disponíveis para chat"""
    try:
        # Buscar usuários ativos exceto o próprio usuário
        users = User.objects.filter(
            is_active=True
        ).exclude(
            id=request.user.id
        ).values(
            'id', 'first_name', 'last_name', 'username', 'email', 'last_login'
        )
        
        # Processar dados dos usuários
        users_data = []
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            if not full_name:
                full_name = user['username']
            
            # Determinar se está online (logou nas últimas 15 minutos)
            is_online = False
            if user['last_login']:
                is_online = user['last_login'] > timezone.now() - timedelta(minutes=15)
            
            # Buscar última mensagem (simulado por enquanto)
            last_message = None
            unread_count = 0
            
            # TODO: Implementar busca real de mensagens quando o modelo for criado
            # try:
            #     last_msg = ChatMessage.objects.filter(
            #         Q(sender=request.user, recipient_id=user['id']) |
            #         Q(sender_id=user['id'], recipient=request.user)
            #     ).order_by('-created_at').first()
            #     
            #     if last_msg:
            #         last_message = last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content
            #     
            #     unread_count = ChatMessage.objects.filter(
            #         sender_id=user['id'],
            #         recipient=request.user,
            #         is_read=False
            #     ).count()
            # except:
            #     pass
            
            users_data.append({
                'id': user['id'],
                'name': full_name,
                'email': user['email'],
                'username': user['username'],
                'is_online': is_online,
                'last_message': last_message,
                'unread_count': unread_count,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            })
        
        # Ordenar: online primeiro, depois por nome
        users_data.sort(key=lambda x: (not x['is_online'], x['name']))
        
        return JsonResponse({
            'success': True,
            'users': users_data,
            'total_count': len(users_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat_unread_count(request):
    """Contador de mensagens não lidas"""
    try:
        # TODO: Implementar contagem real quando o modelo for criado
        # unread_count = ChatMessage.objects.filter(
        #     recipient=request.user,
        #     is_read=False
        # ).count()
        
        # Por enquanto, retornar 0
        unread_count = 0
        
        return JsonResponse({
            'success': True,
            'count': unread_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat_messages(request, user_id):
    """Mensagens de uma conversa específica"""
    try:
        # Verificar se o usuário existe
        try:
            other_user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuário não encontrado'
            }, status=404)
        
        # TODO: Implementar busca real de mensagens quando o modelo for criado
        # messages = ChatMessage.objects.filter(
        #     Q(sender=request.user, recipient=other_user) |
        #     Q(sender=other_user, recipient=request.user)
        # ).order_by('created_at')
        
        # messages_data = [
        #     {
        #         'id': msg.id,
        #         'content': msg.content,
        #         'is_own': msg.sender == request.user,
        #         'timestamp': msg.created_at.isoformat(),
        #         'is_read': msg.is_read
        #     }
        #     for msg in messages
        # ]
        
        # # Marcar mensagens como lidas
        # ChatMessage.objects.filter(
        #     sender=other_user,
        #     recipient=request.user,
        #     is_read=False
        # ).update(is_read=True)
        
        # Por enquanto, retornar mensagens mockadas
        messages_data = [
            {
                'id': 1,
                'content': f'Olá! Esta é uma conversa com {other_user.get_full_name() or other_user.username}.',
                'is_own': False,
                'timestamp': (timezone.now() - timedelta(minutes=5)).isoformat(),
                'is_read': True
            },
            {
                'id': 2,
                'content': 'Oi! Como posso ajudar?',
                'is_own': True,
                'timestamp': (timezone.now() - timedelta(minutes=2)).isoformat(),
                'is_read': True
            }
        ]
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'other_user': {
                'id': other_user.id,
                'name': other_user.get_full_name() or other_user.username,
                'username': other_user.username
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_send_message(request):
    """Enviar nova mensagem"""
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        
        if not recipient_id or not content:
            return JsonResponse({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)
        
        # Verificar se o destinatário existe
        try:
            recipient = User.objects.get(id=recipient_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Destinatário não encontrado'
            }, status=404)
        
        # TODO: Implementar criação real da mensagem quando o modelo for criado
        # message = ChatMessage.objects.create(
        #     sender=request.user,
        #     recipient=recipient,
        #     content=content
        # )
        
        # Por enquanto, simular sucesso
        message_id = timezone.now().timestamp()
        
        return JsonResponse({
            'success': True,
            'message_id': int(message_id),
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat_online_users(request):
    """Lista de usuários online"""
    try:
        # Usuários que fizeram login nas últimas 15 minutos
        online_threshold = timezone.now() - timedelta(minutes=15)
        
        online_users = User.objects.filter(
            is_active=True,
            last_login__gt=online_threshold
        ).exclude(
            id=request.user.id
        ).values('id', 'first_name', 'last_name', 'username')
        
        users_data = []
        for user in online_users:
            full_name = f"{user['first_name']} {user['last_name']}".strip()
            if not full_name:
                full_name = user['username']
                
            users_data.append({
                'id': user['id'],
                'name': full_name,
                'username': user['username']
            })
        
        return JsonResponse({
            'success': True,
            'online_users': users_data,
            'count': len(users_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
