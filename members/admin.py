# Copilot: registrar Beneficiary e Consent no admin.
# Beneficiary list_display full_name, dob, nis, created_at;
# search_fields full_name, nis, cpf, rg; list_filter neighbourhood, created_at.
# Consent inline (StackedInline) em Beneficiary, readonly_fields pdf, signed_at.

from django.contrib import admin
from .models import Beneficiary, Consent


class ConsentInline(admin.StackedInline):
    model = Consent
    extra = 0
    readonly_fields = ('pdf', 'signed_at', 'signed_ip')
    fields = ('lgpd_agreement', 'image_use_agreement', 'signed_at', 'signed_ip', 'pdf')


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'dob', 'nis', 'neighbourhood', 'created_at')
    search_fields = ('full_name', 'nis', 'cpf', 'rg')
    list_filter = ('neighbourhood', 'created_at')
    inlines = [ConsentInline]
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('full_name', 'dob', 'nis')
        }),
        ('Contato', {
            'fields': ('phone_1', 'phone_2')
        }),
        ('Documentos', {
            'fields': ('rg', 'cpf'),
            'classes': ('collapse',)
        }),
        ('Endereço', {
            'fields': ('address', 'neighbourhood', 'reference')
        }),
        ('Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'lgpd_agreement', 'image_use_agreement', 'signed_at')
    list_filter = ('lgpd_agreement', 'image_use_agreement', 'signed_at')
    readonly_fields = ('signed_at', 'signed_ip', 'pdf')
    search_fields = ('beneficiary__full_name',)
