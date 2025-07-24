from django.contrib import admin
from .models import FileUpload, SystemConfig, SystemLog


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    """Admin para gerenciar uploads de arquivos"""
    list_display = ['title', 'original_name', 'category', 'uploaded_by', 'file_size_formatted', 'is_public', 'download_count', 'uploaded_at']
    list_filter = ['category', 'is_public', 'uploaded_at', 'uploaded_by']
    search_fields = ['title', 'description', 'original_name', 'uploaded_by__username', 'uploaded_by__email']
    readonly_fields = ['file_size', 'file_type', 'download_count', 'uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Informações do Arquivo', {
            'fields': ('file', 'title', 'original_name', 'description')
        }),
        ('Classificação', {
            'fields': ('category', 'is_public')
        }),
        ('Metadados', {
            'fields': ('file_size', 'file_type', 'download_count'),
            'classes': ('collapse',)
        }),
        ('Informações de Upload', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by')


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """Admin para configurações do sistema"""
    list_display = ['key', 'value', 'description', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    """Admin para logs do sistema"""
    list_display = ['level', 'message_preview', 'user', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['message', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def message_preview(self, obj):
        """Preview da mensagem truncada"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensagem'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
