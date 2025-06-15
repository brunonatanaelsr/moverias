from django.contrib import admin
from .models import ProjectEnrollment


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'project_name', 'weekday_display', 'shift_display', 'status', 'created_at')
    list_filter = ('project_name', 'weekday', 'shift', 'status', 'created_at')
    search_fields = ('beneficiary__full_name', 'project_name', 'enrollment_code')
    readonly_fields = ('enrollment_code', 'created_at')
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary',)
        }),
        ('Projeto', {
            'fields': ('project_name', 'status')
        }),
        ('Cronograma', {
            'fields': ('weekday', 'shift', 'start_time')
        }),
        ('Sistema', {
            'fields': ('enrollment_code', 'created_at'),
            'classes': ('collapse',)
        })
    )
