from django.contrib import admin
from .models import (
    Announcement, AnnouncementAttachment, AnnouncementReadReceipt,
    InternalMemo, MemoResponse, Newsletter, SuggestionBox, CommunicationSettings
)


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 1


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'author', 'publish_date', 'is_active', 'is_pinned']
    list_filter = ['category', 'priority', 'is_active', 'is_pinned', 'publish_date']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AnnouncementAttachmentInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'content', 'summary', 'category', 'priority')
        }),
        ('Publicação', {
            'fields': ('author', 'publish_date', 'expire_date', 'is_active', 'is_pinned')
        }),
        ('Destinatários', {
            'fields': ('is_global', 'departments', 'target_users')
        }),
        ('Configurações', {
            'fields': ('requires_acknowledgment',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InternalMemo)
class InternalMemoAdmin(admin.ModelAdmin):
    list_display = ['memo_number', 'title', 'memo_type', 'from_user', 'created_at', 'requires_response']
    list_filter = ['memo_type', 'requires_response', 'is_confidential', 'created_at']
    search_fields = ['memo_number', 'title', 'content']
    readonly_fields = ['memo_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('memo_number', 'title', 'content', 'memo_type')
        }),
        ('Origem', {
            'fields': ('from_user', 'from_department')
        }),
        ('Destinatários', {
            'fields': ('to_users', 'to_departments')
        }),
        ('Configurações', {
            'fields': ('requires_response', 'response_deadline', 'is_confidential')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MemoResponse)
class MemoResponseAdmin(admin.ModelAdmin):
    list_display = ['memo', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['memo__title', 'user__username', 'content']
    readonly_fields = ['created_at']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_published', 'publish_date']
    list_filter = ['is_published', 'publish_date', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SuggestionBox)
class SuggestionBoxAdmin(admin.ModelAdmin):
    list_display = ['title', 'suggestion_type', 'status', 'author', 'created_at', 'is_anonymous']
    list_filter = ['suggestion_type', 'status', 'is_anonymous', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'suggestion_type', 'department')
        }),
        ('Autor', {
            'fields': ('author', 'is_anonymous')
        }),
        ('Status', {
            'fields': ('status', 'assigned_to')
        }),
        ('Resposta', {
            'fields': ('response', 'responded_by', 'responded_at')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CommunicationSettings)
class CommunicationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_announcements', 'email_memos', 'digest_frequency']
    list_filter = ['email_announcements', 'email_memos', 'digest_frequency']
    search_fields = ['user__username', 'user__email']
