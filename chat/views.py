from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatChannel, ChatMessage, ChatChannelMembership, ChatAnalytics
from .forms import ChatRoomForm, ChatMessageForm
import json

User = get_user_model()

# Aliases for backward compatibility
ChatRoom = ChatChannel
ChatRoomMembership = ChatChannelMembership


@login_required
def chat_home(request):
    """Página principal do chat completa com interface moderna"""
    
    # Canais públicos
    public_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='public'
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Canais privados
    private_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='private'
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Canais de departamento
    department_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='department'
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Canais de projeto
    project_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='project'
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Canais favoritos
    favorite_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        memberships__is_favorite=True,
        memberships__user=request.user
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Conversas diretas (DMs)
    direct_messages = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='direct'
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__created_at__gt=request.user.profile.last_seen_at if hasattr(request.user, 'profile') else timezone.now()
        ))
    ).order_by('-last_message_time')
    
    # Adicionar informação do outro usuário para DMs
    for dm in direct_messages:
        other_user = dm.members.exclude(id=request.user.id).first()
        dm.other_user = other_user
        
        # Verificar se usuário está online (implementar lógica de presença)
        if hasattr(other_user, 'profile'):
            dm.other_user.is_online = other_user.profile.is_online if hasattr(other_user.profile, 'is_online') else False
            dm.other_user.status = other_user.profile.status if hasattr(other_user.profile, 'status') else 'offline'
        else:
            dm.other_user.is_online = False
            dm.other_user.status = 'offline'
    
    # Canal selecionado (primeiro da lista ou especificado)
    selected_channel = None
    channel_id = request.GET.get('channel')
    
    if channel_id:
        # Buscar canal específico em todas as listas
        all_channels = list(public_channels) + list(private_channels) + list(department_channels) + list(project_channels) + list(direct_messages)
        selected_channel = next((ch for ch in all_channels if str(ch.id) == channel_id), None)
    
    if not selected_channel:
        # Selecionar primeiro canal disponível
        if public_channels.exists():
            selected_channel = public_channels.first()
        elif favorite_channels.exists():
            selected_channel = favorite_channels.first()
        elif direct_messages.exists():
            selected_channel = direct_messages.first()
        elif private_channels.exists():
            selected_channel = private_channels.first()
        elif department_channels.exists():
            selected_channel = department_channels.first()
        elif project_channels.exists():
            selected_channel = project_channels.first()

    # Adicionar informações do outro usuário se for DM
    if selected_channel and selected_channel.channel_type == 'direct':
        other_user = selected_channel.members.exclude(id=request.user.id).first()
        selected_channel.other_user = other_user

    # Mensagens do canal selecionado
    messages_list = []
    if selected_channel:
        messages_list = selected_channel.messages.filter(
            is_deleted=False
        ).select_related('author').order_by('-created_at')[:50]
        
        # Marcar como lida
        try:
            membership = ChatChannelMembership.objects.get(
                user=request.user,
                channel=selected_channel
            )
            membership.last_read_at = timezone.now()
            membership.save()
        except ChatChannelMembership.DoesNotExist:
            pass

    # Usuários online (implementar lógica de presença)
    online_users = User.objects.filter(
        is_active=True
    ).exclude(id=request.user.id)[:20]
    
    # Adicionar informações de status para usuários online
    for user in online_users:
        if hasattr(user, 'profile'):
            user.is_online = user.profile.is_online if hasattr(user.profile, 'is_online') else True
            user.status = user.profile.status if hasattr(user.profile, 'status') else 'online'
        else:
            user.is_online = True
            user.status = 'online'

    # Estatísticas
    total_messages = ChatMessage.objects.filter(
        channel__in=public_channels.union(private_channels).union(department_channels).union(project_channels).union(direct_messages),
        created_at__date=timezone.now().date()
    ).count()
    
    total_active_users = User.objects.filter(
        is_active=True,
        last_login__date=timezone.now().date()
    ).count()
    context = {
        'public_channels': public_channels,
        'private_channels': private_channels,
        'department_channels': department_channels,
        'project_channels': project_channels,
        'favorite_channels': favorite_channels,
        'direct_messages': direct_messages,
        'selected_channel': selected_channel,
        'messages': list(reversed(messages_list)),
        'online_users': online_users,
        'total_messages': total_messages,
        'total_active_users': total_active_users,
        'current_channel_id': selected_channel.id if selected_channel else None,
    }
    
    # Usar o template principal novo
    return render(request, 'chat/chat_main.html', context)


@login_required
def room_detail(request, room_id):
    """Detalhes da sala de chat"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verificar se o usuário é membro da sala
    if not room.members.filter(id=request.user.id).exists():
        messages.error(request, 'Você não tem acesso a esta sala.')
        return redirect('chat:home')
    
    # Mensagens da sala
    messages_list = room.messages.filter(
        is_deleted=False
    ).order_by('created_at')
    
    # Paginação
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Marcar como lida
    membership = ChatRoomMembership.objects.get(
        user=request.user,
        room=room
    )
    membership.mark_as_read()
    
    # Membros da sala
    room_members = room.members.all()
    
    context = {
        'room': room,
        'messages': page_obj,
        'room_members': room_members,
        'message_form': ChatMessageForm(),
    }
    
    return render(request, 'chat/room_detail.html', context)


@login_required
def room_create(request):
    """Criar nova sala de chat"""
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.save()
            
            # Adicionar criador como membro e admin
            ChatRoomMembership.objects.create(
                user=request.user,
                room=room,
                role='admin'
            )
            
            messages.success(request, 'Sala criada com sucesso!')
            return redirect('chat:room_detail', room_id=room.id)
    else:
        form = ChatRoomForm()
    
    return render(request, 'chat/room_form.html', {'form': form, 'title': 'Criar Sala'})


@login_required
def room_edit(request, room_id):
    """Editar sala de chat"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verificar se o usuário pode editar (admin ou criador)
    membership = ChatRoomMembership.objects.filter(
        user=request.user,
        room=room
    ).first()
    
    if not membership or (membership.role not in ['admin', 'moderator'] and room.created_by != request.user):
        messages.error(request, 'Você não tem permissão para editar esta sala.')
        return redirect('chat:room_detail', room_id=room.id)
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sala atualizada com sucesso!')
            return redirect('chat:room_detail', room_id=room.id)
    else:
        form = ChatRoomForm(instance=room)
    
    return render(request, 'chat/room_form.html', {'form': form, 'title': 'Editar Sala', 'room': room})


@login_required
@require_http_methods(["POST"])
def send_message(request, room_id):
    """Enviar mensagem"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verificar se o usuário é membro da sala
    if not room.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    form = ChatMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.room = room
        message.sender = request.user
        message.save()
        
        # Processar menções (@username)
        content = message.content
        mentioned_users = []
        words = content.split()
        for word in words:
            if word.startswith('@'):
                username = word[1:]
                try:
                    user = User.objects.get(username=username)
                    if room.members.filter(id=user.id).exists():
                        mentioned_users.append(user)
                except User.DoesNotExist:
                    pass
        
        message.mentions.set(mentioned_users)
        
        # Atualizar timestamp da sala
        room.updated_at = timezone.now()
        room.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender': message.sender.get_full_name(),
                    'created_at': message.created_at.isoformat(),
                }
            })
        else:
            messages.success(request, 'Mensagem enviada!')
            return redirect('chat:room_detail', room_id=room.id)
    
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def room_members(request, room_id):
    """Gerenciar membros da sala"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verificar permissões
    membership = ChatRoomMembership.objects.filter(
        user=request.user,
        room=room
    ).first()
    
    if not membership or (membership.role not in ['admin', 'moderator'] and room.created_by != request.user):
        messages.error(request, 'Você não tem permissão para gerenciar membros.')
        return redirect('chat:room_detail', room_id=room.id)
    
    members = room.members.all()
    
    # Adicionar membro
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            if not room.members.filter(id=user.id).exists():
                ChatRoomMembership.objects.create(
                    user=user,
                    room=room,
                    role='member'
                )
                messages.success(request, f'{user.get_full_name()} foi adicionado à sala.')
            else:
                messages.warning(request, 'Usuário já é membro desta sala.')
        except User.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
        
        return redirect('chat:room_members', room_id=room.id)
    
    # Usuários disponíveis para adicionar
    available_users = User.objects.exclude(
        id__in=room.members.values_list('id', flat=True)
    ).filter(is_active=True)
    
    context = {
        'room': room,
        'members': members,
        'available_users': available_users,
    }
    
    return render(request, 'chat/room_members.html', context)


@login_required
def notifications(request):
    """Página de notificações do chat - using analytics instead"""
    # Get recent chat activity as notifications
    recent_activity = ChatAnalytics.objects.filter(
        user=request.user,
        metric_type='message_sent'
    ).order_by('-period_start')[:20]
    
    context = {
        'recent_activity': recent_activity,
    }
    
    return render(request, 'chat/notifications.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read - simplified version"""
    # For now, just return success
    # In the future, implement actual notification system
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:notifications')


@login_required
def search_messages(request):
    """Buscar mensagens"""
    query = request.GET.get('q', '')
    room_id = request.GET.get('room')
    
    if not query:
        messages = ChatMessage.objects.none()
    else:
        # Buscar apenas em salas do usuário
        user_rooms = ChatRoom.objects.filter(members=request.user)
        
        messages = ChatMessage.objects.filter(
            room__in=user_rooms,
            content__icontains=query,
            is_deleted=False
        ).order_by('-created_at')
        
        if room_id:
            messages = messages.filter(room_id=room_id)
    
    # Paginação
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'messages': page_obj,
        'query': query,
        'room_id': room_id,
        'user_rooms': ChatRoom.objects.filter(members=request.user),
    }
    
    return render(request, 'chat/search.html', context)


@login_required
@csrf_exempt
def get_messages(request, room_id):
    """API para obter mensagens (AJAX)"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verificar acesso
    if not room.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    last_message_id = request.GET.get('last_id')
    
    messages = room.messages.filter(is_deleted=False).order_by('created_at')
    
    if last_message_id:
        messages = messages.filter(created_at__gt=ChatMessage.objects.get(id=last_message_id).created_at)
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': str(message.id),
            'content': message.content,
            'sender': message.sender.get_full_name(),
            'sender_id': message.sender.id,
            'created_at': message.created_at.isoformat(),
            'message_type': message.message_type,
            'is_current_user': message.sender == request.user,
        })
    
    return JsonResponse({'success': True, 'messages': messages_data})


@login_required
def channel_create(request):
    """Criar novo canal de chat"""
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.created_by = request.user
            channel.channel_type = 'channel'
            channel.save()
            
            # Adicionar criador como membro e admin
            ChatChannelMembership.objects.create(
                user=request.user,
                channel=channel,
                role='admin'
            )
            
            messages.success(request, 'Canal criado com sucesso!')
            return redirect('chat:home') + f'?channel={channel.id}'
    else:
        form = ChatRoomForm()
    
    return render(request, 'chat/channel_form.html', {'form': form, 'title': 'Criar Canal'})


@login_required
def channel_detail(request, channel_id):
    """Detalhes do canal de chat"""
    channel = get_object_or_404(ChatChannel, id=channel_id)
    
    # Verificar se o usuário é membro do canal
    if not channel.members.filter(id=request.user.id).exists():
        messages.error(request, 'Você não tem acesso a este canal.')
        return redirect('chat:home')
    
    return redirect('chat:home') + f'?channel={channel_id}'


@login_required
def channel_edit(request, channel_id):
    """Editar canal de chat"""
    channel = get_object_or_404(ChatChannel, id=channel_id)
    
    # Verificar se o usuário pode editar (admin ou criador)
    membership = ChatChannelMembership.objects.filter(
        user=request.user,
        channel=channel
    ).first()
    
    if not membership or (membership.role not in ['admin', 'moderator'] and channel.created_by != request.user):
        messages.error(request, 'Você não tem permissão para editar este canal.')
        return redirect('chat:home') + f'?channel={channel_id}'
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, instance=channel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Canal atualizado com sucesso!')
            return redirect('chat:home') + f'?channel={channel_id}'
    else:
        form = ChatRoomForm(instance=channel)
    
    return render(request, 'chat/channel_form.html', {
        'form': form, 
        'title': 'Editar Canal',
        'channel': channel
    })


@login_required
def channel_members(request, channel_id):
    """Gerenciar membros do canal"""
    channel = get_object_or_404(ChatChannel, id=channel_id)
    
    # Verificar permissão
    membership = ChatChannelMembership.objects.filter(
        user=request.user,
        channel=channel
    ).first()
    
    if not membership:
        messages.error(request, 'Você não tem acesso a este canal.')
        return redirect('chat:home')
    
    members = channel.members.all()
    
    context = {
        'channel': channel,
        'members': members,
        'user_membership': membership,
        'can_manage': membership.role in ['admin', 'moderator'] or channel.created_by == request.user
    }
    
    return render(request, 'chat/channel_members.html', context)


@login_required
def dm_list(request):
    """Lista de conversas diretas"""
    dm_channels = ChatChannel.objects.filter(
        members=request.user,
        is_active=True,
        channel_type='direct'
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    return redirect('chat:home')


@login_required
def dm_conversation(request, user_id):
    """Conversa direta com usuário específico"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Buscar ou criar canal DM
    dm_channel = ChatChannel.objects.filter(
        channel_type='direct',
        members__in=[request.user, other_user]
    ).annotate(
        member_count=Count('members')
    ).filter(member_count=2).first()
    
    if not dm_channel:
        # Criar novo canal DM
        dm_channel = ChatChannel.objects.create(
            name=f"{request.user.get_full_name()} & {other_user.get_full_name()}",
            channel_type='direct',
            created_by=request.user
        )
        dm_channel.members.add(request.user, other_user)
        
        # Criar memberships
        ChatChannelMembership.objects.create(
            user=request.user,
            channel=dm_channel,
            role='member'
        )
        ChatChannelMembership.objects.create(
            user=other_user,
            channel=dm_channel,
            role='member'
        )
    
    return redirect('chat:home') + f'?channel={dm_channel.id}'


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def toggle_reaction(request, message_id):
    """Alternar reação na mensagem"""
    try:
        data = json.loads(request.body)
        emoji = data.get('emoji')
        
        if not emoji:
            return JsonResponse({'success': False, 'message': 'Emoji não fornecido'})
        
        message = get_object_or_404(ChatMessage, id=message_id)
        
        # Verificar acesso ao canal
        if not message.channel.members.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Acesso negado'})
        
        # Importar modelo de reação
        from .models import ChatReaction
        
        # Verificar se já existe reação
        existing_reaction = ChatReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).first()
        
        if existing_reaction:
            # Remover reação
            existing_reaction.delete()
            action = 'removed'
        else:
            # Adicionar reação
            ChatReaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            action = 'added'
        
        # Contar reações atualizadas
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
        
        return JsonResponse({
            'success': True,
            'action': action,
            'reactions': reactions_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
