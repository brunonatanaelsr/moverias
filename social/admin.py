from django.contrib import admin
from .models import SocialAnamnesis


@admin.register(SocialAnamnesis)
class SocialAnamnesisAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'date', 'income', 'signed_by_technician', 'locked')
    list_filter = ('date', 'locked', 'signed_by_beneficiary', 'signed_by_technician')
    search_fields = ('beneficiary__full_name', 'vulnerabilities')
    readonly_fields = ('date',)
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary', 'date')
        }),
        ('Dados Familiares', {
            'fields': ('family_composition', 'income')
        }),
        ('Vulnerabilidades', {
            'fields': ('vulnerabilities', 'substance_use')
        }),
        ('Observações', {
            'fields': ('observations',)
        }),
        ('Assinaturas', {
            'fields': ('signed_by_technician', 'signed_by_beneficiary', 'locked')
        })
    )
