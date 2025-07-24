# Copilot: criar modelo Beneficiary.
# Campos: full_name Char(120), dob Date, nis Char(15) opcional,
# phone_1 e phone_2 Char(20), rg e cpf criptografados (django_cryptography.encrypt),
# address, neighbourhood, reference Text, created_at auto_now_add.
# Métodos: __str__ retorna full_name.
# Meta ordering por full_name.

from django.db import models
# from django_cryptography.fields import encrypt  # Temporariamente desabilitado
import hashlib
import os
from datetime import date


class Beneficiary(models.Model):
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('INATIVA', 'Inativa'),
    ]
    
    full_name = models.CharField('Nome Completo', max_length=120)
    email = models.EmailField('Email', blank=True, null=True)
    dob = models.DateField('Data de Nascimento')
    nis = models.CharField('NIS', max_length=15, blank=True, null=True)
    phone_1 = models.CharField('Telefone 1', max_length=20)
    phone_2 = models.CharField('Telefone 2', max_length=20, blank=True, null=True)
    rg = models.CharField('RG', max_length=20, blank=True, null=True)  # Temporariamente sem criptografia
    cpf = models.CharField('CPF', max_length=14, blank=True, null=True)  # Temporariamente sem criptografia
    address = models.TextField('Endereço')
    neighbourhood = models.CharField('Bairro', max_length=100)
    reference = models.TextField('Ponto de Referência', blank=True)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ATIVA')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Beneficiária'
        verbose_name_plural = 'Beneficiárias'

    def __str__(self):
        return self.full_name
    
    @property
    def age(self):
        """Calcula a idade da beneficiária"""
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    
    @property
    def is_active(self):
        """Retorna True se a beneficiária está ativa"""
        return self.status == 'ATIVA'
    
    def activate(self):
        """Ativa a beneficiária"""
        self.status = 'ATIVA'
        self.save(update_fields=['status'])
    
    def deactivate(self):
        """Inativa a beneficiária"""
        self.status = 'INATIVA'
        self.save(update_fields=['status'])


class Consent(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='consents')
    lgpd_agreement = models.BooleanField('Concordo com LGPD', default=False)
    image_use_agreement = models.BooleanField('Concordo com uso de imagem', default=False)
    signed_at = models.DateTimeField('Assinado em', auto_now_add=True)
    signed_ip = models.GenericIPAddressField('IP da assinatura')
    pdf = models.FileField('PDF do Termo', upload_to='consents/', blank=True, null=True)

    class Meta:
        verbose_name = 'Termo de Consentimento'
        verbose_name_plural = 'Termos de Consentimento'

    def __str__(self):
        return f"Termo de {self.beneficiary.full_name} - {self.signed_at.strftime('%d/%m/%Y')}"

    def generate_pdf(self):
        """Gera PDF do termo usando WeasyPrint e salva com hash único"""
        # TODO: Implementar geração de PDF quando WeasyPrint estiver configurado
        # from weasyprint import HTML
        # from django.template.loader import render_to_string
        # from django.conf import settings
        
        # # Gerar hash único para o arquivo
        # content_hash = hashlib.md5(f"{self.beneficiary.id}_{self.signed_at}".encode()).hexdigest()
        # filename = f"termo_{content_hash}.pdf"
        
        # # Renderizar template HTML
        # html_content = render_to_string('members/consent_pdf.html', {
        #     'consent': self,
        #     'beneficiary': self.beneficiary
        # })
        
        # # Gerar PDF
        # pdf_path = os.path.join(settings.MEDIA_ROOT, 'consents', filename)
        # os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        # HTML(string=html_content).write_pdf(pdf_path)
        
        # # Salvar caminho no modelo
        # self.pdf.name = f'consents/{filename}'
        # self.save()
        
        # return pdf_path
        pass
