from django.contrib import admin
from .models import ActionPlan, WheelOfLife


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('beneficiary__full_name', 'main_goal')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary',)
        }),
        ('Planejamento', {
            'fields': ('main_goal', 'priority_areas', 'actions')
        }),
        ('Apoio', {
            'fields': ('institute_support',)
        }),
        ('Revisão', {
            'fields': ('semester_review',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WheelOfLife)
class WheelOfLifeAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'date', 'average_score')
    list_filter = ('date',)
    search_fields = ('beneficiary__full_name',)
    readonly_fields = ('created_at', 'average_score')
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary', 'date')
        }),
        ('Áreas de Vida (0-10)', {
            'fields': (
                ('family', 'finance', 'health', 'career'),
                ('relationships', 'personal_growth', 'leisure', 'spirituality'),
                ('education', 'environment', 'contribution', 'emotions')
            )
        }),
        ('Resultado', {
            'fields': ('average_score',),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
