from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import ChatChannel, ChatMessage, ChatChannelMembership

User = get_user_model()

@login_required
def chat_api_conversations(request):
    """API para listar conversas do usuário atual"""
    user = request.user
    
    # Buscar canais diretos do usuário
    direct_channels = ChatChannel.objects.filter(
        channel_type='direct',
        members=user,
        is_active=True
    ).prefetch_related('members', 'messages')
    
    conversations = []
    for channel in direct_channels:
        # Encontrar o outro usuário na conversa
        other_user = channel.members.exclude(id=user.id).first()
        if not other_user:
            continue
            
        # Última mensagem
        last_message = channel.messages.order_by('-created_at').first()
        
        # Mensagens não lidas
        unread_count = channel.messages.filter(
            sender__ne=user,
            created_at__gt=user.last_seen or timezone.now() - timedelta(days=30)
        ).count()
        
        conversations.append({
            'channel_id': str(channel.id),
            'user': {
                'id': other_user.id,
                'name': other_user.get_full_name() or other_user.username,
                'username': other_user.username,
                'is_online': hasattr(other_user, 'is_online') and other_user.is_online,
                'avatar': getattr(other_user, 'avatar', None)
            },
            'last_message': last_message.content if last_message else None,
            'last_message_time': last_message.created_at.isoformat() if last_message else None,
            'unread_count': unread_count
        })
    
    # Ordenar por última mensagem
    conversations.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    
    return JsonResponse(conversations, safe=False)

@login_required
def chat_api_users(request):
    """API para listar usuários ativos do sistema"""
    current_user = request.user
    
    # Buscar usuários ativos (excluindo o usuário atual)
    users = User.objects.exclude(id=current_user.id).filter(
        is_active=True
    ).select_related('profile')
    
    # Filtrar por termo de busca se fornecido
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    users_data = []
    for user in users_page:
        # Verificar se existe conversa direta
        existing_channel = ChatChannel.objects.filter(
            channel_type='direct',
            members=current_user
        ).filter(members=user).first()
        
        users_data.append({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'username': user.username,
            'email': user.email,
            'department': getattr(user, 'department', None),
            'is_online': hasattr(user, 'is_online') and user.is_online,
            'avatar': getattr(user, 'avatar', None),
            'last_seen': getattr(user, 'last_seen', None),
            'has_conversation': existing_channel is not None
        })
    
    return JsonResponse(users_data, safe=False)

@login_required
def chat_api_messages(request, user_id):
    """API para listar mensagens de uma conversa específica"""
    current_user = request.user
    other_user = get_object_or_404(User, id=user_id)
    
    # Buscar ou criar canal direto
    channel = ChatChannel.objects.filter(
        channel_type='direct',
        members=current_user
    ).filter(members=other_user).first()
    
    if not channel:
        # Criar novo canal se não existir
        channel = ChatChannel.objects.create(
            name=f"Direct: {current_user.username} - {other_user.username}",
            channel_type='direct',
            created_by=current_user,
            max_members=2
        )
        channel.members.add(current_user, other_user)
    
    # Buscar mensagens do canal
    messages = ChatMessage.objects.filter(
        channel=channel
    ).select_related('sender').order_by('created_at')
    
    # Paginação
    paginator = Paginator(messages, 50)
    page = request.GET.get('page', 1)
    messages_page = paginator.get_page(page)
    
    messages_data = []
    for message in messages_page:
        messages_data.append({
            'id': str(message.id),
            'content': message.content,
            'sender': {
                'id': message.sender.id,
                'name': message.sender.get_full_name() or message.sender.username,
                'username': message.sender.username
            },
            'created_at': message.created_at.isoformat(),
            'is_edited': message.is_edited,
            'message_type': message.message_type
        })
    
    return JsonResponse(messages_data, safe=False)

@login_required
@require_http_methods(["POST"])
def chat_api_send_message(request):
    """API para enviar mensagem"""
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        
        if not recipient_id or not content:
            return JsonResponse({'success': False, 'error': 'Dados inválidos'}, status=400)
        
        current_user = request.user
        recipient = get_object_or_404(User, id=recipient_id)
        
        # Buscar ou criar canal direto
        channel = ChatChannel.objects.filter(
            channel_type='direct',
            members=current_user
        ).filter(members=recipient).first()
        
        if not channel:
            # Criar novo canal
            channel = ChatChannel.objects.create(
                name=f"Direct: {current_user.username} - {recipient.username}",
                channel_type='direct',
                created_by=current_user,
                max_members=2
            )
            channel.members.add(current_user, recipient)
        
        # Criar mensagem
        message = ChatMessage.objects.create(
            channel=channel,
            sender=current_user,
            content=content,
            message_type='text'
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(message.id),
                'content': message.content,
                'sender': {
                    'id': message.sender.id,
                    'name': message.sender.get_full_name() or message.sender.username,
                    'username': message.sender.username
                },
                'created_at': message.created_at.isoformat(),
                'message_type': message.message_type
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def chat_api_current_user(request):
    """API para obter informações do usuário atual"""
    user = request.user
    return JsonResponse({
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'username': user.username,
        'email': user.email,
        'is_online': True,  # Assumir que o usuário está online se está fazendo a requisição
        'avatar': getattr(user, 'avatar', None)
    })

@login_required
def chat_api_mark_as_read(request, channel_id):
    """API para marcar mensagens como lidas"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        channel = get_object_or_404(ChatChannel, id=channel_id)
        user = request.user
        
        # Verificar se o usuário é membro do canal
        if not channel.members.filter(id=user.id).exists():
            return JsonResponse({'error': 'Acesso negado'}, status=403)
        
        # Marcar mensagens como lidas (implementar lógica específica se necessário)
        # Por enquanto, apenas retornar sucesso
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_api_user_status(request, user_id):
    """API para obter status de um usuário"""
    user = get_object_or_404(User, id=user_id)
    
    return JsonResponse({
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'username': user.username,
        'is_online': hasattr(user, 'is_online') and user.is_online,
        'last_seen': getattr(user, 'last_seen', None)
    })

@login_required
def chat_api_channels(request):
    """API para listar canais do usuário"""
    user = request.user
    
    channels = ChatChannel.objects.filter(
        members=user,
        is_active=True
    ).exclude(channel_type='direct')
    
    channels_data = []
    for channel in channels:
        last_message = channel.messages.order_by('-created_at').first()
        
        channels_data.append({
            'id': str(channel.id),
            'name': channel.name,
            'description': channel.description,
            'channel_type': channel.channel_type,
            'member_count': channel.members.count(),
            'last_message': last_message.content if last_message else None,
            'last_message_time': last_message.created_at.isoformat() if last_message else None,
            'unread_count': 0  # Implementar lógica de contagem se necessário
        })
    
    return JsonResponse(channels_data, safe=False)
