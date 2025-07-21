"""
Forms para o sistema de certificados
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import CertificateTemplate, CertificateRequest, Certificate
from members.models import Beneficiary
from workshops.models import Workshop


class CertificateTemplateForm(forms.ModelForm):
    """Form para criar/editar templates de certificado"""
    
    class Meta:
        model = CertificateTemplate
        fields = [
            'name', 'type', 'template_file', 'background_image', 
            'logo', 'signature_image', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do template'
            }),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'template_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.html,.htm'
            }),
            'background_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'signature_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_template_file(self):
        template_file = self.cleaned_data.get('template_file')
        if template_file:
            # Verificar extensão
            if not template_file.name.endswith(('.html', '.htm')):
                raise ValidationError("Apenas arquivos HTML são aceitos.")
            
            # Verificar tamanho (máximo 1MB)
            if template_file.size > 1024 * 1024:
                raise ValidationError("Arquivo muito grande. Máximo 1MB.")
        
        return template_file


class CertificateRequestForm(forms.ModelForm):
    """Form para solicitar certificado"""
    
    class Meta:
        model = CertificateRequest
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observações adicionais (opcional)',
                'rows': 3
            }),
        }


class CertificateSearchForm(forms.Form):
    """Form para buscar certificados"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, título ou código...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + Certificate.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + CertificateTemplate.CERTIFICATE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CertificateVerificationForm(forms.Form):
    """Form para verificar certificado"""
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Digite o código de verificação',
            'style': 'text-transform: uppercase;'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError("Código de verificação é obrigatório.")
        return code


class BulkCertificateForm(forms.Form):
    """Form para operações em lote com certificados"""
    certificates = forms.ModelMultipleChoiceField(
        queryset=Certificate.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    
    action = forms.ChoiceField(
        choices=[
            ('send_email', 'Enviar por email'),
            ('mark_delivered', 'Marcar como entregue'),
            ('regenerate', 'Regenerar PDF'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CertificateGenerationForm(forms.Form):
    """Form para gerar certificados manualmente"""
    workshop = forms.ModelChoiceField(
        queryset=None,  # Será definido na view
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    members = forms.ModelMultipleChoiceField(
        queryset=None,  # Será definido na view
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    template = forms.ModelChoiceField(
        queryset=CertificateTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    send_email = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        workshop = kwargs.pop('workshop', None)
        super().__init__(*args, **kwargs)
        
        if workshop:
            from workshops.models import Enrollment
            # Filtrar membros inscritos no workshop
            enrolled_members = Enrollment.objects.filter(
                workshop=workshop,
                status='completed'
            ).values_list('member', flat=True)
            
            from members.models import Member
            self.fields['members'].queryset = Member.objects.filter(
                id__in=enrolled_members
            )


class CertificateEmailForm(forms.Form):
    """Form para enviar certificado por email"""
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email do destinatário'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Assunto do email'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Mensagem personalizada (opcional)',
            'rows': 4
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        certificate = kwargs.pop('certificate', None)
        super().__init__(*args, **kwargs)
        
        if certificate:
            self.fields['recipient_email'].initial = certificate.member.email
            self.fields['subject'].initial = f"Seu certificado - {certificate.title}"


class CertificateForm(forms.ModelForm):
    """Form para criar/editar certificados"""
    
    class Meta:
        model = Certificate
        fields = [
            'member', 'workshop', 'template', 'title', 'description',
            'completion_date', 'hours_completed', 'grade', 'instructor',
            'status'
        ]
        widgets = {
            'member': forms.Select(attrs={
                'class': 'mm-form-input mm-form-select',
                'required': True
            }),
            'workshop': forms.Select(attrs={
                'class': 'mm-form-input mm-form-select'
            }),
            'template': forms.Select(attrs={
                'class': 'mm-form-input mm-form-select',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'mm-form-input',
                'placeholder': 'Título do certificado',
                'maxlength': 300,
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'mm-form-input mm-form-textarea',
                'placeholder': 'Descrição do certificado',
                'rows': 4,
                'required': True
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'mm-form-input',
                'type': 'date',
                'required': True
            }),
            'hours_completed': forms.NumberInput(attrs={
                'class': 'mm-form-input',
                'min': 0,
                'step': 1
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'mm-form-input',
                'min': 0,
                'max': 10,
                'step': 0.1
            }),
            'instructor': forms.TextInput(attrs={
                'class': 'mm-form-input',
                'placeholder': 'Nome do instrutor'
            }),
            'status': forms.Select(attrs={
                'class': 'mm-form-input mm-form-select'
            }),
        }
        labels = {
            'member': 'Beneficiária',
            'workshop': 'Workshop',
            'template': 'Template',
            'title': 'Título',
            'description': 'Descrição',
            'completion_date': 'Data de Conclusão',
            'hours_completed': 'Horas Completadas',
            'grade': 'Nota (0-10)',
            'instructor': 'Instrutor',
            'status': 'Status',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas beneficiárias ativas
        self.fields['member'].queryset = Beneficiary.objects.filter(status='ATIVA')
        
        # Filtrar apenas templates ativos
        self.fields['template'].queryset = CertificateTemplate.objects.filter(is_active=True)
        
        # Filtrar apenas workshops ativos ou concluídos
        self.fields['workshop'].queryset = Workshop.objects.filter(
            status__in=['ativo', 'concluido']
        )
    
    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        workshop = cleaned_data.get('workshop')
        
        # Verificar se já existe certificado para esta combinação
        if member and workshop:
            existing = Certificate.objects.filter(
                member=member,
                workshop=workshop
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing.exists():
                raise ValidationError("Já existe um certificado para esta beneficiária neste workshop.")
        
        return cleaned_data
