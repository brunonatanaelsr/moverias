"""
Formulários e campos seguros para Move Marias
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class SecureCPFField(forms.CharField):
    """Campo seguro para validação de CPF"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 14)
        kwargs.setdefault('widget', forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'Digite um CPF válido no formato 000.000.000-00'
        }))
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        super().validate(value)
        if value:
            self.validate_cpf(value)
    
    def validate_cpf(self, cpf):
        """Validação completa de CPF"""
        # Remover formatação
        cpf_digits = re.sub(r'\D', '', cpf)
        
        # Verificar comprimento
        if len(cpf_digits) != 11:
            raise ValidationError('CPF deve ter 11 dígitos.')
        
        # Verificar se não são todos iguais
        if cpf_digits == cpf_digits[0] * 11:
            raise ValidationError('CPF inválido.')
        
        # Calcular dígito verificador
        def calculate_digit(digits):
            sum_total = 0
            for i, digit in enumerate(digits):
                sum_total += int(digit) * (len(digits) + 1 - i)
            remainder = sum_total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Validar primeiro dígito
        first_digit = calculate_digit(cpf_digits[:9])
        if first_digit != int(cpf_digits[9]):
            raise ValidationError('CPF inválido.')
        
        # Validar segundo dígito
        second_digit = calculate_digit(cpf_digits[:10])
        if second_digit != int(cpf_digits[10]):
            raise ValidationError('CPF inválido.')
        
        return cpf_digits
    
    def clean(self, value):
        value = super().clean(value)
        if value:
            # Retornar apenas os dígitos para armazenamento
            return re.sub(r'\D', '', value)
        return value


class SecureEmailField(forms.EmailField):
    """Campo de email com validações adicionais"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email'
        }))
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        super().validate(value)
        if value:
            self.validate_email_security(value)
    
    def validate_email_security(self, email):
        """Validações de segurança para email"""
        # Lista de domínios temporários conhecidos
        temp_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org'
        ]
        
        domain = email.split('@')[1].lower()
        if domain in temp_domains:
            raise ValidationError('Emails temporários não são permitidos.')
        
        return email


class SecurePhoneField(forms.CharField):
    """Campo seguro para telefone brasileiro"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 15)
        kwargs.setdefault('widget', forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999',
            'pattern': r'\(\d{2}\) \d{4,5}-\d{4}',
            'title': 'Digite um telefone válido no formato (11) 99999-9999'
        }))
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        super().validate(value)
        if value:
            self.validate_phone(value)
    
    def validate_phone(self, phone):
        """Validação de telefone brasileiro"""
        # Remover formatação
        phone_digits = re.sub(r'\D', '', phone)
        
        # Verificar comprimento (10 ou 11 dígitos)
        if len(phone_digits) not in [10, 11]:
            raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')
        
        # Verificar DDD válido (11-99)
        ddd = phone_digits[:2]
        if not (11 <= int(ddd) <= 99):
            raise ValidationError('DDD inválido.')
        
        # Para celular (11 dígitos), deve começar com 9
        if len(phone_digits) == 11 and phone_digits[2] != '9':
            raise ValidationError('Celular deve começar com 9 após o DDD.')
        
        return phone_digits
    
    def clean(self, value):
        value = super().clean(value)
        if value:
            # Retornar formatado
            digits = re.sub(r'\D', '', value)
            if len(digits) == 11:
                return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
            elif len(digits) == 10:
                return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return value


class EmailConfigForm(forms.Form):
    """Formulário para configuração de email SMTP"""
    
    email_backend = forms.ChoiceField(
        label='Backend de Email',
        choices=[
            ('django.core.mail.backends.smtp.EmailBackend', 'SMTP'),
            ('django.core.mail.backends.console.EmailBackend', 'Console (Debug)'),
            ('django.core.mail.backends.filebased.EmailBackend', 'Arquivo'),
            ('django.core.mail.backends.dummy.EmailBackend', 'Dummy (Não envia)'),
        ],
        initial='django.core.mail.backends.smtp.EmailBackend',
        help_text='Escolha o método de envio de emails'
    )
    
    email_host = forms.CharField(
        label='Servidor SMTP',
        max_length=255,
        initial='smtp.gmail.com',
        help_text='Ex: smtp.gmail.com, smtp.outlook.com, smtp.sendgrid.net'
    )
    
    email_port = forms.IntegerField(
        label='Porta SMTP',
        initial=587,
        help_text='587 para TLS, 465 para SSL, 25 para não criptografado'
    )
    
    email_use_tls = forms.BooleanField(
        label='Usar TLS',
        required=False,
        initial=True,
        help_text='Recomendado para a maioria dos provedores SMTP'
    )
    
    email_use_ssl = forms.BooleanField(
        label='Usar SSL',
        required=False,
        initial=False,
        help_text='Use apenas se o provedor exigir SSL em vez de TLS'
    )
    
    email_host_user = forms.CharField(
        label='Usuário SMTP',
        max_length=255,
        required=False,
        help_text='Seu email ou nome de usuário SMTP'
    )
    
    email_host_password = forms.CharField(
        label='Senha SMTP',
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text='Sua senha ou token de aplicativo'
    )
    
    default_from_email = forms.EmailField(
        label='Email Remetente Padrão',
        initial='noreply@movemarias.org',
        help_text='Email que aparecerá como remetente'
    )
    
    server_email = forms.EmailField(
        label='Email do Servidor',
        initial='server@movemarias.org',
        help_text='Email usado para notificações de erro do servidor'
    )
    
    test_email = forms.EmailField(
        label='Email para Teste',
        required=False,
        help_text='Digite um email para enviar um teste'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS do Tailwind
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded'
                })
            else:
                field.widget.attrs.update({
                    'class': 'mt-1 focus:ring-purple-500 focus:border-purple-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md'
                })
                
        # Campos específicos
        self.fields['email_host_password'].widget.attrs.update({
            'placeholder': 'Digite a senha ou token do aplicativo'
        })
        
        self.fields['test_email'].widget.attrs.update({
            'placeholder': 'exemplo@email.com'
        })
