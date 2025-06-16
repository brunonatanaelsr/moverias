from django.contrib import admin
from .models import Project, ProjectEnrollment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'project', 'weekday_display', 'shift_display', 'status', 'created_at')
    list_filter = ('project', 'weekday', 'shift', 'status', 'created_at')
    search_fields = ('beneficiary__full_name', 'project__name', 'enrollment_code')
    readonly_fields = ('enrollment_code', 'created_at')
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary',)
        }),
        ('Projeto', {
            'fields': ('project', 'status')
        }),
        ('Cronograma', {
            'fields': ('weekday', 'shift', 'start_time')
        }),
        ('Sistema', {
            'fields': ('enrollment_code', 'created_at'),
            'classes': ('collapse',)
        })
    )
