from django.contrib import admin
from .models import (
    TaskBoard, TaskColumn, Task, TaskLabel, TaskComment, 
    TaskAttachment, TaskActivity
)


@admin.register(TaskBoard)
class TaskBoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'department', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['members']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TaskColumn)
class TaskColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'order', 'color']
    list_filter = ['board']
    search_fields = ['name']
    ordering = ['board', 'order']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'board', 'column', 'assignee', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['board', 'column', 'priority', 'status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'board', 'column')
        }),
        ('Atribuição', {
            'fields': ('assignee', 'reporter')
        }),
        ('Detalhes', {
            'fields': ('priority', 'status', 'due_date', 'estimated_hours', 'estimated_cost')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'color']
    list_filter = ['board']
    search_fields = ['name']


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'created_at']
    list_filter = ['task__board', 'created_at']
    search_fields = ['content', 'task__title']
    readonly_fields = ['created_at']


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'file', 'uploaded_by', 'uploaded_at']
    list_filter = ['task__board', 'uploaded_at']
    search_fields = ['task__title']
    readonly_fields = ['uploaded_at']


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'activity_type', 'created_at']
    list_filter = ['activity_type', 'task__board', 'created_at']
    search_fields = ['description', 'task__title']
    readonly_fields = ['created_at']
