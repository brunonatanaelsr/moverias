from django import forms
from django.core.exceptions import ValidationError
from core.validators import validate_cpf, validate_phone, validate_rg, validate_full_name, sanitize_input
from .models import Beneficiary
import re


class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = [
            'full_name', 'dob', 'nis', 'phone_1', 'phone_2', 
            'rg', 'cpf', 'address', 'neighbourhood', 'reference', 'status'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo da beneficiária',
                'data-validate': 'name',
                'data-required': 'true'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'nis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de Identificação Social'
            }),
            'phone_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'data-validate': 'phone',
                'data-required': 'true'
            }),
            'phone_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'data-validate': 'phone'
            }),
            'rg': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XX.XXX.XXX-X'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'data-validate': 'cpf',
                'data-check-uniqueness': 'true'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo com CEP'
            }),
            'neighbourhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do bairro'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ponto de referência próximo'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_cpf(self):
        """Validação robusta de CPF"""
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Sanitizar entrada
            cpf = sanitize_input(cpf)
            
            # Remover formatação
            cpf_digits = re.sub(r'\D', '', cpf)
            
            # Usar validador robusto
            if not validate_cpf(cpf_digits):
                raise ValidationError('CPF inválido. Verifique os dígitos informados.')
            
            # Verificar se CPF já existe no sistema (campos criptografados requerem verificação manual)
            all_beneficiaries = Beneficiary.objects.exclude(pk=self.instance.pk if self.instance else None)
            for beneficiary in all_beneficiaries:
                try:
                    if beneficiary.cpf == cpf_digits:
                        raise ValidationError('Este CPF já está cadastrado no sistema.')
                except:
                    # Se houver erro na descriptografia, continua
                    continue
            
            return cpf_digits
        return cpf

    def clean_phone_1(self):
        """Validação robusta de telefone"""
        phone = self.cleaned_data.get('phone_1')
        if phone:
            # Sanitizar entrada
            phone = sanitize_input(phone)
            
            # Usar validador robusto
            if not validate_phone(phone):
                raise ValidationError('Telefone inválido. Use o formato (11) 99999-9999.')
            
            return phone
        return phone

    def clean_phone_2(self):
        """Validação robusta de telefone secundário"""
        phone = self.cleaned_data.get('phone_2')
        if phone:
            # Sanitizar entrada
            phone = sanitize_input(phone)
            
            # Usar validador robusto
            if not validate_phone(phone):
                raise ValidationError('Telefone inválido. Use o formato (11) 99999-9999.')
            
            return phone
        return phone

    def clean_full_name(self):
        """Validação robusta do nome completo"""
        name = self.cleaned_data.get('full_name')
        if name:
            # Sanitizar entrada
            name = sanitize_input(name)
            
            # Usar validador robusto
            is_valid, message = validate_full_name(name)
            if not is_valid:
                raise ValidationError(message)
            
            return name.title()  # Capitalizar nome
        return name
    
    def clean_rg(self):
        """Validação de RG"""
        rg = self.cleaned_data.get('rg')
        if rg:
            # Sanitizar entrada
            rg = sanitize_input(rg)
            
            # Usar validador robusto
            if not validate_rg(rg):
                raise ValidationError('RG inválido. Verifique o número informado.')
            
            return rg
        return rg
    
    def clean_address(self):
        """Sanitizar endereço"""
        address = self.cleaned_data.get('address')
        if address:
            return sanitize_input(address)
        return address
    
    def clean_neighbourhood(self):
        """Sanitizar bairro"""
        neighbourhood = self.cleaned_data.get('neighbourhood')
        if neighbourhood:
            return sanitize_input(neighbourhood)
        return neighbourhood
    
    def clean_reference(self):
        """Sanitizar ponto de referência"""
        reference = self.cleaned_data.get('reference')
        if reference:
            return sanitize_input(reference)
        return reference
