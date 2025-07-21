from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    BeneficiaryActivity,
    ActivitySession,
    ActivityAttendance,
    ActivityFeedback,
    ActivityNote
)


@admin.register(BeneficiaryActivity)
class BeneficiaryActivityAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'beneficiary',
        'activity_type',
        'status',
        'priority',
        'start_date',
        'end_date',
        'facilitator',
        'attendance_rate_display',
        'impact_score',
        'created_at'
    ]
    
    list_filter = [
        'activity_type',
        'status',
        'priority',
        'start_date',
        'created_at'
    ]
    
    search_fields = [
        'title',
        'beneficiary__full_name',
        'facilitator',
        'description'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'attendance_rate_display',
        'total_sessions',
        'completed_sessions'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'beneficiary',
                'title',
                'description',
                'activity_type',
                'status',
                'priority'
            )
        }),
        ('Programação', {
            'fields': (
                'start_date',
                'end_date',
                'frequency'
            )
        }),
        ('Recursos', {
            'fields': (
                'facilitator',
                'location',
                'materials_needed'
            )
        }),
        ('Objetivos e Resultados', {
            'fields': (
                'objectives',
                'expected_outcomes',
                'completion_percentage',
                'impact_score'
            )
        }),
        ('Integração', {
            'fields': (
                'social_anamnesis',
            )
        }),
        ('Metadados', {
            'fields': (
                'id',
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
        ('Estatísticas', {
            'fields': (
                'total_sessions',
                'completed_sessions',
                'attendance_rate_display'
            ),
            'classes': ('collapse',)
        })
    )
    
    def attendance_rate_display(self, obj):
        rate = obj.attendance_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}">{:.1f}%</span>',
            color,
            rate
        )
    attendance_rate_display.short_description = 'Taxa de Presença'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'beneficiary',
            'social_anamnesis',
            'created_by'
        )


class ActivityAttendanceInline(admin.TabularInline):
    model = ActivityAttendance
    extra = 0
    readonly_fields = ['recorded_by', 'recorded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recorded_by')


@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'activity',
        'session_number',
        'session_date',
        'start_time',
        'end_time',
        'status',
        'facilitator',
        'attendance_status'
    ]
    
    list_filter = [
        'status',
        'session_date',
        'activity__activity_type'
    ]
    
    search_fields = [
        'title',
        'activity__title',
        'activity__beneficiary__full_name',
        'facilitator'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_minutes'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'activity',
                'session_number',
                'title',
                'description'
            )
        }),
        ('Programação', {
            'fields': (
                'session_date',
                'start_time',
                'end_time',
                'duration_minutes',
                'status'
            )
        }),
        ('Recursos', {
            'fields': (
                'facilitator',
                'location',
                'materials_used'
            )
        }),
        ('Conteúdo', {
            'fields': (
                'content_covered',
                'objectives_achieved',
                'observations'
            )
        }),
        ('Metadados', {
            'fields': (
                'id',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ActivityAttendanceInline]
    
    def attendance_status(self, obj):
        try:
            attendance = obj.attendance.get()
            if attendance.attended:
                return format_html('<span style="color: green;">Presente</span>')
            else:
                return format_html('<span style="color: red;">Ausente</span>')
        except ActivityAttendance.DoesNotExist:
            return format_html('<span style="color: gray;">Não registrada</span>')
    attendance_status.short_description = 'Presença'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'activity',
            'activity__beneficiary'
        ).prefetch_related('attendance')


@admin.register(ActivityAttendance)
class ActivityAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'session',
        'beneficiary_name',
        'session_date',
        'attended',
        'arrival_time',
        'departure_time',
        'duration_present',
        'recorded_by',
        'recorded_at'
    ]
    
    list_filter = [
        'attended',
        'session__session_date',
        'recorded_at'
    ]
    
    search_fields = [
        'session__activity__beneficiary__full_name',
        'session__title',
        'notes'
    ]
    
    readonly_fields = [
        'recorded_by',
        'recorded_at',
        'duration_present'
    ]
    
    def beneficiary_name(self, obj):
        return obj.session.activity.beneficiary.full_name
    beneficiary_name.short_description = 'Beneficiária'
    
    def session_date(self, obj):
        return obj.session.session_date
    session_date.short_description = 'Data da Sessão'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'session',
            'session__activity',
            'session__activity__beneficiary',
            'recorded_by'
        )


@admin.register(ActivityFeedback)
class ActivityFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'activity',
        'beneficiary_name',
        'rating',
        'content_quality',
        'facilitator_rating',
        'average_rating',
        'would_recommend',
        'created_at'
    ]
    
    list_filter = [
        'rating',
        'content_quality',
        'facilitator_rating',
        'would_recommend',
        'created_at'
    ]
    
    search_fields = [
        'activity__title',
        'activity__beneficiary__full_name',
        'positive_aspects',
        'improvements_suggested'
    ]
    
    readonly_fields = [
        'created_at',
        'average_rating'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'activity',
            )
        }),
        ('Avaliações', {
            'fields': (
                'rating',
                'content_quality',
                'facilitator_rating',
                'average_rating'
            )
        }),
        ('Comentários', {
            'fields': (
                'positive_aspects',
                'improvements_suggested',
                'additional_comments'
            )
        }),
        ('Recomendação', {
            'fields': (
                'would_recommend',
            )
        }),
        ('Metadados', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    def beneficiary_name(self, obj):
        return obj.activity.beneficiary.full_name
    beneficiary_name.short_description = 'Beneficiária'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'activity',
            'activity__beneficiary'
        )


@admin.register(ActivityNote)
class ActivityNoteAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'activity',
        'beneficiary_name',
        'note_type',
        'is_confidential',
        'created_by',
        'created_at'
    ]
    
    list_filter = [
        'note_type',
        'is_confidential',
        'created_at'
    ]
    
    search_fields = [
        'title',
        'content',
        'activity__title',
        'activity__beneficiary__full_name'
    ]
    
    readonly_fields = [
        'created_by',
        'created_at'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'activity',
                'note_type',
                'title'
            )
        }),
        ('Conteúdo', {
            'fields': (
                'content',
                'is_confidential'
            )
        }),
        ('Metadados', {
            'fields': (
                'created_by',
                'created_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def beneficiary_name(self, obj):
        return obj.activity.beneficiary.full_name
    beneficiary_name.short_description = 'Beneficiária'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'activity',
            'activity__beneficiary',
            'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Configurações adicionais do admin
admin.site.site_header = 'MoveMarias - Administração'
admin.site.site_title = 'MoveMarias Admin'
admin.site.index_title = 'Painel de Administração'
