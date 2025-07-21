"""
Administração do sistema de certificados
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CertificateTemplate, Certificate, CertificateRequest, CertificateDelivery
)


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'type', 'is_active', 'created_at', 'preview_template'
    ]
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'type']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'type', 'is_active')
        }),
        ('Arquivos', {
            'fields': ('template_file', 'background_image', 'logo', 'signature_image')
        }),
    )
    
    def preview_template(self, obj):
        if obj.template_file:
            return format_html(
                '<a href="{}" target="_blank" class="button">Visualizar</a>',
                obj.template_file.url
            )
        return '-'
    preview_template.short_description = 'Preview'


class CertificateDeliveryInline(admin.TabularInline):
    model = CertificateDelivery
    extra = 0
    readonly_fields = ['delivered_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'member', 'workshop', 'status', 'issue_date', 
        'verification_code', 'view_certificate', 'download_certificate'
    ]
    list_filter = ['status', 'template__type', 'issue_date', 'completion_date']
    search_fields = [
        'title', 'member__name', 'workshop__title', 'verification_code'
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'verification_code', 'created_at', 'updated_at']
    inlines = [CertificateDeliveryInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('member', 'workshop', 'template', 'title', 'description')
        }),
        ('Datas', {
            'fields': ('completion_date', 'issue_date', 'expiry_date')
        }),
        ('Detalhes', {
            'fields': ('hours_completed', 'grade', 'instructor')
        }),
        ('Status', {
            'fields': ('status', 'pdf_file', 'verification_code')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def view_certificate(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" class="button">Visualizar</a>',
                reverse('certificates:detail', kwargs={'certificate_id': obj.id})
            )
        return '-'
    view_certificate.short_description = 'Visualizar'
    
    def download_certificate(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" class="button">Download</a>',
                reverse('certificates:download', kwargs={'certificate_id': obj.id})
            )
        return '-'
    download_certificate.short_description = 'Download'
    
    actions = ['generate_pdf', 'send_email', 'mark_as_delivered']
    
    def generate_pdf(self, request, queryset):
        """Gerar PDF para certificados selecionados"""
        count = 0
        for certificate in queryset:
            try:
                certificate.generate_pdf()
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Erro ao gerar PDF para {certificate}: {e}",
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} certificados gerados com sucesso.",
                level='SUCCESS'
            )
    
    generate_pdf.short_description = "Gerar PDF dos certificados selecionados"
    
    def send_email(self, request, queryset):
        """Enviar certificados por email"""
        from .models import send_certificate_email
        
        count = 0
        for certificate in queryset:
            try:
                send_certificate_email(certificate)
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Erro ao enviar email para {certificate}: {e}",
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} certificados enviados por email.",
                level='SUCCESS'
            )
    
    send_email.short_description = "Enviar certificados por email"
    
    def mark_as_delivered(self, request, queryset):
        """Marcar como entregue"""
        count = queryset.update(status='delivered')
        self.message_user(
            request,
            f"{count} certificados marcados como entregues.",
            level='SUCCESS'
        )
    
    mark_as_delivered.short_description = "Marcar como entregue"


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = [
        'member', 'workshop', 'requested_at', 'approved', 
        'processed_at', 'approve_request'
    ]
    list_filter = ['approved', 'requested_at', 'processed_at']
    search_fields = ['member__name', 'workshop__title']
    ordering = ['-requested_at']
    readonly_fields = ['requested_at', 'processed_at']
    
    fieldsets = (
        ('Solicitação', {
            'fields': ('member', 'workshop', 'requested_at', 'notes')
        }),
        ('Processamento', {
            'fields': ('approved', 'processed_at', 'certificate')
        }),
    )
    
    def approve_request(self, obj):
        if not obj.approved:
            return format_html(
                '<a href="{}" class="button">Aprovar</a>',
                reverse('certificates:approve_request', kwargs={'request_id': obj.id})
            )
        return 'Aprovado'
    approve_request.short_description = 'Ação'
    
    actions = ['approve_selected_requests']
    
    def approve_selected_requests(self, request, queryset):
        """Aprovar solicitações selecionadas"""
        count = 0
        for cert_request in queryset.filter(approved=False):
            try:
                cert_request.approve()
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Erro ao aprovar solicitação de {cert_request.member}: {e}",
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} solicitações aprovadas e certificados gerados.",
                level='SUCCESS'
            )
    
    approve_selected_requests.short_description = "Aprovar solicitações selecionadas"


@admin.register(CertificateDelivery)
class CertificateDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'certificate', 'method', 'delivered_at', 'recipient_email', 'tracking_code'
    ]
    list_filter = ['method', 'delivered_at']
    search_fields = [
        'certificate__title', 'certificate__member__name', 
        'recipient_email', 'tracking_code'
    ]
    ordering = ['-delivered_at']
    readonly_fields = ['delivered_at']
    
    fieldsets = (
        ('Entrega', {
            'fields': ('certificate', 'method', 'delivered_at')
        }),
        ('Detalhes', {
            'fields': ('recipient_email', 'tracking_code', 'notes')
        }),
    )


# Customização do admin
admin.site.site_header = "MoveMarias - Administração"
admin.site.site_title = "MoveMarias Admin"
admin.site.index_title = "Painel de Administração"
