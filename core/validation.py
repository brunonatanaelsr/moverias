"""
Sistema de validação avançado para formulários
MoveMarias - Validação cliente e servidor integrada
"""

from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.utils.translation import gettext_lazy as _
import re

class MoveMariasValidationMixin:
    """Mixin para adicionar validação avançada aos formulários"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_validation_classes()
        self.add_validation_attributes()
    
    def add_validation_classes(self):
        """Adiciona classes CSS para validação"""
        for field_name, field in self.fields.items():
            widget = field.widget
            
            # Adiciona classes base
            css_class = widget.attrs.get('class', '')
            css_class += ' mm-form-input'
            
            # Adiciona classes específicas por tipo
            if isinstance(field, forms.CharField):
                css_class += ' mm-form-text'
            elif isinstance(field, forms.EmailField):
                css_class += ' mm-form-email'
            elif isinstance(field, forms.IntegerField):
                css_class += ' mm-form-number'
            elif isinstance(field, forms.DateField):
                css_class += ' mm-form-date'
            elif isinstance(field, forms.FileField):
                css_class += ' mm-form-file'
            elif isinstance(field, forms.ChoiceField):
                css_class += ' mm-form-select'
            elif isinstance(field, forms.BooleanField):
                css_class += ' mm-form-checkbox'
            
            # Adiciona classe de campo obrigatório
            if field.required:
                css_class += ' mm-form-required'
            
            widget.attrs['class'] = css_class.strip()
    
    def add_validation_attributes(self):
        """Adiciona atributos HTML5 para validação"""
        for field_name, field in self.fields.items():
            widget = field.widget
            
            # Adiciona atributos baseados no tipo de campo
            if isinstance(field, forms.EmailField):
                widget.attrs['type'] = 'email'
                widget.attrs['data-validation'] = 'email'
            
            if isinstance(field, forms.CharField):
                if field.min_length:
                    widget.attrs['minlength'] = field.min_length
                if field.max_length:
                    widget.attrs['maxlength'] = field.max_length
            
            if isinstance(field, forms.IntegerField):
                widget.attrs['type'] = 'number'
                if field.min_value is not None:
                    widget.attrs['min'] = field.min_value
                if field.max_value is not None:
                    widget.attrs['max'] = field.max_value
            
            # Adiciona placeholder se não existir
            if not widget.attrs.get('placeholder') and field.label:
                widget.attrs['placeholder'] = f"Digite {field.label.lower()}"
            
            # Adiciona atributos de validação customizada
            if hasattr(field, 'validation_pattern'):
                widget.attrs['pattern'] = field.validation_pattern
            
            if hasattr(field, 'validation_message'):
                widget.attrs['data-validation-message'] = field.validation_message
    
    def get_validation_rules(self):
        """Retorna regras de validação para JavaScript"""
        rules = {}
        
        for field_name, field in self.fields.items():
            field_rules = {}
            
            if field.required:
                field_rules['required'] = True
            
            if isinstance(field, forms.CharField):
                if field.min_length:
                    field_rules['minLength'] = field.min_length
                if field.max_length:
                    field_rules['maxLength'] = field.max_length
            
            if isinstance(field, forms.EmailField):
                field_rules['email'] = True
            
            if isinstance(field, forms.IntegerField):
                field_rules['number'] = True
                if field.min_value is not None:
                    field_rules['min'] = field.min_value
                if field.max_value is not None:
                    field_rules['max'] = field.max_value
            
            if hasattr(field, 'validation_pattern'):
                field_rules['pattern'] = field.validation_pattern
            
            if field_rules:
                rules[field_name] = field_rules
        
        return rules

class CPFValidator(RegexValidator):
    """Validador de CPF brasileiro"""
    regex = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$'  # Aceita formato formatado ou apenas números
    message = _('CPF deve estar no formato XXX.XXX.XXX-XX ou conter 11 dígitos')
    
    def __call__(self, value):
        # Remove pontos e traços
        cpf = re.sub(r'[^\d]', '', str(value))
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            raise forms.ValidationError(self.message)
        
        # Verifica se todos os dígitos são iguais
        if len(set(cpf)) == 1:
            raise forms.ValidationError(_('CPF inválido'))
        
        # Validação dos dígitos verificadores
        def calc_digit(cpf, weight):
            sum_val = sum(int(cpf[i]) * weight[i] for i in range(len(weight)))
            remainder = sum_val % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calc_digit(cpf, [10, 9, 8, 7, 6, 5, 4, 3, 2])
        second_digit = calc_digit(cpf, [11, 10, 9, 8, 7, 6, 5, 4, 3, 2])
        
        if int(cpf[9]) != first_digit or int(cpf[10]) != second_digit:
            raise forms.ValidationError(_('CPF inválido'))
    
    def validate(self, value):
        """Método para validação simples (retorna True/False)"""
        try:
            self(value)
            return True
        except forms.ValidationError:
            return False

class CNPJValidator(RegexValidator):
    """Validador de CNPJ brasileiro"""
    regex = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$'  # Aceita formato formatado ou apenas números
    message = _('CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX ou conter 14 dígitos')
    
    def __call__(self, value):
        # Remove pontos, barras e traços
        cnpj = re.sub(r'[^\d]', '', str(value))
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            raise forms.ValidationError(self.message)
        
        # Validação dos dígitos verificadores
        def calc_digit(cnpj, weights):
            sum_val = sum(int(cnpj[i]) * weights[i] for i in range(len(weights)))
            remainder = sum_val % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        first_digit = calc_digit(cnpj, first_weights)
        second_digit = calc_digit(cnpj, second_weights)
        
        if int(cnpj[12]) != first_digit or int(cnpj[13]) != second_digit:
            raise forms.ValidationError(_('CNPJ inválido'))
    
    def validate(self, value):
        """Método para validação simples (retorna True/False)"""
        try:
            self(value)
            return True
        except forms.ValidationError:
            return False

class PhoneValidator(RegexValidator):
    """Validador de telefone brasileiro"""
    regex = r'^\(\d{2}\) \d{4,5}-\d{4}$|^\d{10,11}$|^\+55 \d{2} \d{4,5}-\d{4}$'  # Aceita vários formatos
    message = _('Telefone deve estar no formato (XX) XXXXX-XXXX, (XX) XXXX-XXXX ou conter 10-11 dígitos')
    
    def validate(self, value):
        """Método para validação simples (retorna True/False)"""
        try:
            self(value)
            return True
        except forms.ValidationError:
            return False

class CEPValidator(RegexValidator):
    """Validador de CEP brasileiro"""
    regex = r'^\d{5}-\d{3}$|^\d{8}$'  # Aceita formato formatado ou apenas números
    message = _('CEP deve estar no formato XXXXX-XXX ou conter 8 dígitos')
    
    def validate(self, value):
        """Método para validação simples (retorna True/False)"""
        try:
            self(value)
            return True
        except forms.ValidationError:
            return False

# Campos customizados com validação
class CPFField(forms.CharField):
    """Campo para CPF com validação"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 14)
        kwargs.setdefault('validators', []).append(CPFValidator())
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'placeholder': 'XXX.XXX.XXX-XX',
            'data-mask': '000.000.000-00',
            'data-validation': 'cpf'
        })

class CNPJField(forms.CharField):
    """Campo para CNPJ com validação"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 18)
        kwargs.setdefault('validators', []).append(CNPJValidator())
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'placeholder': 'XX.XXX.XXX/XXXX-XX',
            'data-mask': '00.000.000/0000-00',
            'data-validation': 'cnpj'
        })

class PhoneField(forms.CharField):
    """Campo para telefone com validação"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 15)
        kwargs.setdefault('validators', []).append(PhoneValidator())
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'placeholder': '(XX) XXXXX-XXXX',
            'data-mask': '(00) 00000-0000',
            'data-validation': 'phone'
        })

class CEPField(forms.CharField):
    """Campo para CEP com validação"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 9)
        kwargs.setdefault('validators', []).append(CEPValidator())
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'placeholder': 'XXXXX-XXX',
            'data-mask': '00000-000',
            'data-validation': 'cep'
        })

class PasswordField(forms.CharField):
    """Campo para senha com validação avançada"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.PasswordInput())
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'data-validation': 'password',
            'data-validation-message': 'Senha deve ter pelo menos 8 caracteres, incluindo letras e números'
        })
    
    def validate(self, value):
        super().validate(value)
        
        if value and len(value) < 8:
            raise forms.ValidationError(_('Senha deve ter pelo menos 8 caracteres'))
        
        if value and not re.search(r'[a-zA-Z]', value):
            raise forms.ValidationError(_('Senha deve conter pelo menos uma letra'))
        
        if value and not re.search(r'\d', value):
            raise forms.ValidationError(_('Senha deve conter pelo menos um número'))

class ImageField(forms.ImageField):
    """Campo para imagem com validação de tamanho"""
    def __init__(self, *args, **kwargs):
        self.max_size = kwargs.pop('max_size', 5 * 1024 * 1024)  # 5MB default
        super().__init__(*args, **kwargs)
        
        self.widget.attrs.update({
            'accept': 'image/*',
            'data-validation': 'image',
            'data-max-size': self.max_size
        })
    
    def validate(self, value):
        super().validate(value)
        
        if value and hasattr(value, 'size') and value.size > self.max_size:
            raise forms.ValidationError(
                _('Arquivo muito grande. Tamanho máximo permitido: %(max_size)s MB') % {
                    'max_size': self.max_size / (1024 * 1024)
                }
            )

# Formulário base para MoveMarias
class MoveMariasForm(MoveMariasValidationMixin, forms.Form):
    """Formulário base com validação avançada"""
    pass

class MoveMariasModelForm(MoveMariasValidationMixin, forms.ModelForm):
    """Model form base com validação avançada"""
    pass
