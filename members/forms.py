from django import forms
from django.core.exceptions import ValidationError
from .models import Beneficiary
import re


class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = [
            'full_name', 'dob', 'nis', 'phone_1', 'phone_2', 
            'rg', 'cpf', 'address', 'neighbourhood', 'reference'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo da beneficiária'
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
                'placeholder': '(11) 99999-9999'
            }),
            'phone_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'rg': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XX.XXX.XXX-X'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00'
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
        }

    def clean_cpf(self):
        """Validação básica de CPF"""
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remover formatação
            cpf_digits = re.sub(r'\D', '', cpf)
            
            # Verificar se tem 11 dígitos
            if len(cpf_digits) != 11:
                raise ValidationError('CPF deve ter 11 dígitos.')
            
            # Verificar se não são todos iguais
            if cpf_digits == cpf_digits[0] * 11:
                raise ValidationError('CPF inválido.')
            
            return cpf_digits
        return cpf

    def clean_phone_1(self):
        """Validação de telefone"""
        phone = self.cleaned_data.get('phone_1')
        if phone:
            # Remover formatação
            phone_digits = re.sub(r'\D', '', phone)
            
            # Verificar se tem pelo menos 10 dígitos
            if len(phone_digits) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
            
            return phone
        return phone

    def clean_phone_2(self):
        """Validação de telefone secundário"""
        phone = self.cleaned_data.get('phone_2')
        if phone:
            # Remover formatação
            phone_digits = re.sub(r'\D', '', phone)
            
            # Verificar se tem pelo menos 10 dígitos
            if len(phone_digits) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
            
            return phone
        return phone

    def clean_full_name(self):
        """Validação do nome completo"""
        name = self.cleaned_data.get('full_name')
        if name:
            # Verificar se tem pelo menos nome e sobrenome
            name_parts = name.strip().split()
            if len(name_parts) < 2:
                raise ValidationError('Por favor, informe nome e sobrenome.')
            
            return name.title()  # Capitalizar nome
        return name
