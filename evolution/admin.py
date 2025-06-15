from django.contrib import admin
from .models import EvolutionRecord


@admin.register(EvolutionRecord)
class EvolutionRecordAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'date', 'author', 'signature_required', 'signed_by_beneficiary')
    list_filter = ('date', 'signature_required', 'signed_by_beneficiary', 'author')
    search_fields = ('beneficiary__full_name', 'description', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary', 'date')
        }),
        ('Conteúdo', {
            'fields': ('description',)
        }),
        ('Assinatura', {
            'fields': ('signature_required', 'signed_by_beneficiary')
        }),
        ('Sistema', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo registro
            obj.author = request.user
        super().save_model(request, obj, form, change)
