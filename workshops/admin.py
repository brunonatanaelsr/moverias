from django.contrib import admin
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ['name', 'workshop_type', 'facilitator', 'start_date', 'status', 'total_participants', 'max_participants']
    list_filter = ['workshop_type', 'status', 'start_date']
    search_fields = ['name', 'facilitator', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'workshop_type', 'facilitator')
        }),
        ('Cronograma', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Configurações', {
            'fields': ('location', 'max_participants', 'objectives', 'materials_needed')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkshopSession)
class WorkshopSessionAdmin(admin.ModelAdmin):
    list_display = ['workshop', 'session_date', 'topic', 'start_time', 'end_time']
    list_filter = ['workshop', 'session_date']
    search_fields = ['workshop__name', 'topic', 'content_covered']
    readonly_fields = ['created_at']


@admin.register(WorkshopEnrollment)
class WorkshopEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'workshop', 'enrollment_date', 'status', 'attendance_rate']
    list_filter = ['workshop', 'status', 'enrollment_date']
    search_fields = ['beneficiary__full_name', 'workshop__name']
    readonly_fields = ['created_at']


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'session', 'attended']
    list_filter = ['session__workshop', 'attended', 'session__session_date']
    search_fields = ['enrollment__beneficiary__full_name', 'session__workshop__name']


@admin.register(WorkshopEvaluation)
class WorkshopEvaluationAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'evaluation_date', 'rating']
    list_filter = ['evaluation_date', 'enrollment__workshop', 'rating']
    search_fields = ['enrollment__beneficiary__full_name', 'enrollment__workshop__name']
    readonly_fields = ['created_at']
