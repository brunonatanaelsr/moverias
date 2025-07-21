"""
Sistema de certificados automático para MoveMarias
Gera certificados PDF p    member = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Benefici        member = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='certificate_requests',
        verbose_name='Beneficiária'
    ) = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='certificate_templates',
        verbose_name='Beneficiária'
    )    )rkshops e cursos completados
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os
import uuid
from datetime import datetime, timedelta
from members.models import Beneficiary
from workshops.models import Workshop, WorkshopEnrollment

User = get_user_model()


class CertificateTemplate(models.Model):
    """Template para diferentes tipos de certificados"""
    CERTIFICATE_TYPES = [
        ('workshop', 'Workshop'),
        ('course', 'Curso'),
        ('participation', 'Participação'),
        ('completion', 'Conclusão'),
        ('achievement', 'Conquista'),
        ('declaration', 'Declaração de Comparecimento'),
        ('benefit_receipt', 'Recibo de Benefício'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nome do Template")
    type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES, default='workshop')
    template_file = models.FileField(
        upload_to='certificates/templates/',
        verbose_name="Arquivo do Template",
        help_text="Template HTML para o certificado"
    )
    background_image = models.ImageField(
        upload_to='certificates/backgrounds/',
        blank=True,
        null=True,
        verbose_name="Imagem de Fundo"
    )
    logo = models.ImageField(
        upload_to='certificates/logos/',
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    signature_image = models.ImageField(
        upload_to='certificates/signatures/',
        blank=True,
        null=True,
        verbose_name="Assinatura"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de Certificado"
        verbose_name_plural = "Templates de Certificado"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Certificate(models.Model):
    """Certificado gerado para um participante"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('generated', 'Gerado'),
        ('delivered', 'Entregue'),
        ('expired', 'Expirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name="Beneficiária"
    )
    workshop = models.ForeignKey(
        Workshop,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name="Workshop",
        blank=True,
        null=True
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name="Template"
    )
    
    # Dados do certificado
    title = models.CharField(max_length=300, verbose_name="Título")
    description = models.TextField(verbose_name="Descrição")
    completion_date = models.DateField(verbose_name="Data de Conclusão")
    issue_date = models.DateField(auto_now_add=True, verbose_name="Data de Emissão")
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Expiração"
    )
    
    # Informações adicionais
    hours_completed = models.PositiveIntegerField(
        default=0,
        verbose_name="Horas Completadas"
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Nota"
    )
    instructor = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Instrutor"
    )
    
    # Status e arquivo
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    pdf_file = models.FileField(
        upload_to='certificates/generated/',
        blank=True,
        null=True,
        verbose_name="Arquivo PDF"
    )
    
    # Verificação
    verification_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="Código de Verificação"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-created_at']
        unique_together = ['member', 'workshop', 'template']
    
    def __str__(self):
        return f"Certificado: {self.member.full_name} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)
    
    def generate_verification_code(self):
        """Gera código de verificação único"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Certificate.objects.filter(verification_code=code).exists():
                return code
    
    def is_valid(self):
        """Verifica se o certificado ainda é válido"""
        if self.expiry_date:
            return timezone.now().date() <= self.expiry_date
        return True
    
    def get_verification_url(self):
        """Retorna URL para verificação do certificado"""
        from django.urls import reverse
        return reverse('certificates:verify', kwargs={'code': self.verification_code})
    
    def generate_pdf(self):
        """Gera o arquivo PDF do certificado"""
        from weasyprint import HTML, CSS
        from django.template.loader import render_to_string
        
        # Contexto para o template
        context = {
            'certificate': self,
            'member': self.member,
            'workshop': self.workshop,
            'template': self.template,
            'verification_url': self.get_verification_url(),
            'current_date': timezone.now().date(),
        }
        
        # Renderizar HTML
        html_string = render_to_string('certificates/certificate_template.html', context)
        
        # Gerar PDF
        html = HTML(string=html_string, base_url=settings.BASE_DIR)
        pdf = html.write_pdf()
        
        # Salvar arquivo
        filename = f"certificate_{self.id}.pdf"
        file_path = f"certificates/generated/{filename}"
        
        with default_storage.open(file_path, 'wb') as f:
            f.write(pdf)
        
        self.pdf_file = file_path
        self.status = 'generated'
        self.save()
        
        return pdf


class CertificateRequest(models.Model):
    """Solicitação de certificado"""
    member = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='certificate_requests',
        verbose_name="Beneficiária"
    )
    workshop = models.ForeignKey(
        Workshop,
        on_delete=models.CASCADE,
        related_name='certificate_requests',
        verbose_name="Workshop"
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name="Data do Processamento")
    approved = models.BooleanField(default=False, verbose_name="Aprovado")
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Certificado"
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Solicitação de Certificado"
        verbose_name_plural = "Solicitações de Certificado"
        ordering = ['-requested_at']
        unique_together = ['member', 'workshop']
    
    def __str__(self):
        return f"Solicitação: {self.member.full_name} - {self.workshop.name}"
    
    def approve(self, template=None):
        """Aprova a solicitação e gera o certificado"""
        if not template:
            template = CertificateTemplate.objects.filter(
                type='workshop',
                is_active=True
            ).first()
        
        if not template:
            raise ValueError("Nenhum template ativo encontrado")
        
        # Criar certificado
        certificate = Certificate.objects.create(
            member=self.member,
            workshop=self.workshop,
            template=template,
            title=f"Certificado de Participação - {self.workshop.title}",
            description=f"Certifica que {self.member.full_name} participou do workshop {self.workshop.name}",
            completion_date=timezone.now().date(),
            hours_completed=getattr(self.workshop, 'duration_hours', 0),
            instructor=self.workshop.instructor
        )
        
        # Gerar PDF
        certificate.generate_pdf()
        
        # Atualizar solicitação
        self.approved = True
        self.processed_at = timezone.now()
        self.certificate = certificate
        self.save()
        
        return certificate


class CertificateDelivery(models.Model):
    """Entrega de certificado"""
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('download', 'Download'),
        ('print', 'Impressão'),
        ('postal', 'Correio'),
    ]
    
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name="Certificado"
    )
    method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHODS,
        verbose_name="Método de Entrega"
    )
    delivered_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da Entrega")
    recipient_email = models.EmailField(blank=True, verbose_name="Email do Destinatário")
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Código de Rastreamento"
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Entrega de Certificado"
        verbose_name_plural = "Entregas de Certificado"
        ordering = ['-delivered_at']
    
    def __str__(self):
        return f"Entrega: {self.certificate} - {self.get_method_display()}"


# Funções auxiliares para automação
def auto_generate_certificates():
    """Gera certificados automaticamente para workshops completados"""
    
    # Buscar inscrições concluídas sem certificado
    completed_enrollments = WorkshopEnrollment.objects.filter(
        status='concluido',
        certificate_requests__isnull=True
    )
    
    certificates_created = 0
    
    for enrollment in completed_enrollments:
        # Verificar se atende aos critérios
        if enrollment.attendance_rate >= 75:  # 75% de presença mínima
            # Criar solicitação de certificado
            request = CertificateRequest.objects.create(
                member=enrollment.beneficiary,
                workshop=enrollment.workshop
            )
            
            # Aprovar automaticamente se atende aos critérios
            try:
                request.approve()
                certificates_created += 1
            except Exception as e:
                print(f"Erro ao gerar certificado para {enrollment}: {e}")
    
    return certificates_created


def send_certificate_email(certificate):
    """Envia certificado por email"""
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    
    subject = f"Seu certificado - {certificate.title}"
    
    # Renderizar email
    html_content = render_to_string('certificates/certificate_email.html', {
        'certificate': certificate,
        'member': certificate.member,
        'verification_url': certificate.get_verification_url(),
    })
    
    # Criar email
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[certificate.member.email],
    )
    
    email.content_subtype = 'html'
    
    # Anexar PDF se existir
    if certificate.pdf_file:
        email.attach_file(certificate.pdf_file.path)
    
    # Enviar
    email.send()
    
    # Registrar entrega
    CertificateDelivery.objects.create(
        certificate=certificate,
        method='email',
        recipient_email=certificate.member.email
    )


def verify_certificate(verification_code):
    """Verifica autenticidade de um certificado"""
    try:
        certificate = Certificate.objects.get(verification_code=verification_code)
        if certificate.is_valid():
            return {
                'valid': True,
                'certificate': certificate,
                'message': 'Certificado válido'
            }
        else:
            return {
                'valid': False,
                'certificate': certificate,
                'message': 'Certificado expirado'
            }
    except Certificate.DoesNotExist:
        return {
            'valid': False,
            'certificate': None,
            'message': 'Certificado não encontrado'
        }
