from django.contrib import admin
from .models import (
    ChatChannel, ChatChannelMembership, ChatMessage, ChatThread, 
    ChatReaction, ChatMention, ChatIntegration, ChatBot, ChatAnalytics
)

# Aliases for backward compatibility
ChatRoom = ChatChannel
ChatRoomMembership = ChatChannelMembership
ChatMessageReaction = ChatReaction


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'created_by', 'is_active', 'is_archived', 'created_at']
    list_filter = ['channel_type', 'is_active', 'is_archived', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'channel_type', 'created_by')
        }),
        ('Configurações', {
            'fields': ('is_active', 'is_archived', 'max_members')
        }),
        ('Relacionamentos', {
            'fields': ('department', 'project', 'task'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['channel', 'sender', 'message_type', 'created_at', 'is_edited']
    list_filter = ['channel', 'message_type', 'is_edited', 'created_at']
    search_fields = ['content', 'sender__username', 'channel__name']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Mensagem', {
            'fields': ('channel', 'sender', 'content', 'message_type')
        }),
        ('Arquivo', {
            'fields': ('file_attachment', 'file_name', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('is_edited', 'reply_to')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ChatRoomMembership)
class ChatRoomMembershipAdmin(admin.ModelAdmin):
    list_display = ['channel', 'user', 'role', 'joined_at', 'is_muted']
    list_filter = ['role', 'is_muted', 'joined_at']
    search_fields = ['user__username', 'channel__name']
    readonly_fields = ['joined_at']


@admin.register(ChatIntegration)
class ChatIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'is_active', 'created_at']
    list_filter = ['integration_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(ChatBot)
class ChatBotAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(ChatReaction)
class ChatReactionAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'reaction', 'created_at']
    list_filter = ['reaction', 'created_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['created_at']
