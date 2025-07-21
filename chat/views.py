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
    """Página principal do chat"""
    # Salas do usuário
    user_rooms = ChatRoom.objects.filter(
        members=request.user, 
        is_active=True
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # Unread messages count instead of notifications
    unread_count = 0
    for room in user_rooms:
        unread_count += room.messages.filter(
            created_at__gt=timezone.now() - timezone.timedelta(hours=24),
            is_deleted=False
        ).exclude(sender=request.user).count()
    
    # Sala selecionada (primeira da lista ou especificada)
    selected_room = None
    if user_rooms.exists():
        room_id = request.GET.get('room')
        if room_id:
            selected_room = user_rooms.filter(id=room_id).first()
        if not selected_room:
            selected_room = user_rooms.first()
    
    # Mensagens da sala selecionada
    messages_list = []
    if selected_room:
        messages_list = selected_room.messages.filter(
            is_deleted=False
        ).order_by('created_at')
        
        # Marcar como lida
        membership = ChatRoomMembership.objects.get(
            user=request.user,
            room=selected_room
        )
        membership.mark_as_read()
    
    # Usuários online (simplificado)
    online_users = User.objects.filter(
        is_active=True,
        last_login__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).exclude(id=request.user.id)[:10]
    
    context = {
        'user_rooms': user_rooms,
        'selected_room': selected_room,
        'messages': messages_list,
        'unread_count': unread_count,
        'online_users': online_users,
        'message_form': ChatMessageForm(),
    }
    
    return render(request, 'chat/home.html', context)


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
