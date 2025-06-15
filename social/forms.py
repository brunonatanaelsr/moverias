# Copilot: ModelForm SocialAnamnesis.
# Dividir em 3 etapas com django-formtools Wizard ou crispy-forms;
# validar income >= 0; wizard salva parcial.

from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column
from .models import SocialAnamnesis


class SocialAnamnesisStep1Form(forms.ModelForm):
    """Primeiro passo: Dados básicos"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['beneficiary', 'family_composition', 'income']
        widgets = {
            'family_composition': forms.Textarea(attrs={'rows': 4}),
            'income': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Familiares',
                'beneficiary',
                'family_composition',
                'income'
            ),
            Submit('submit', 'Próximo', css_class='btn btn-primary')
        )

    def clean_income(self):
        income = self.cleaned_data.get('income')
        if income is not None and income < 0:
            raise ValidationError('A renda não pode ser negativa.')
        return income


class SocialAnamnesisStep2Form(forms.ModelForm):
    """Segundo passo: Vulnerabilidades"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['vulnerabilities', 'substance_use']
        widgets = {
            'vulnerabilities': forms.Textarea(attrs={'rows': 6}),
            'substance_use': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Vulnerabilidades e Riscos',
                'vulnerabilities',
                'substance_use'
            ),
            Row(
                Column(Submit('prev_step', 'Anterior', css_class='btn btn-secondary'), css_class='col-6'),
                Column(Submit('submit', 'Próximo', css_class='btn btn-primary'), css_class='col-6')
            )
        )


class SocialAnamnesisStep3Form(forms.ModelForm):
    """Terceiro passo: Finalização"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['observations', 'signed_by_beneficiary']
        widgets = {
            'observations': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Observações e Assinatura',
                'observations',
                'signed_by_beneficiary'
            ),
            Row(
                Column(Submit('prev_step', 'Anterior', css_class='btn btn-secondary'), css_class='col-6'),
                Column(Submit('submit', 'Finalizar', css_class='btn btn-success'), css_class='col-6')
            )
        )


class SocialAnamnesisUpdateForm(forms.ModelForm):
    """Formulário completo para edição"""
    
    class Meta:
        model = SocialAnamnesis
        fields = [
            'family_composition', 'income', 'vulnerabilities', 
            'substance_use', 'observations', 'signed_by_beneficiary'
        ]
        widgets = {
            'family_composition': forms.Textarea(attrs={'rows': 4}),
            'vulnerabilities': forms.Textarea(attrs={'rows': 6}),
            'substance_use': forms.Textarea(attrs={'rows': 4}),
            'observations': forms.Textarea(attrs={'rows': 4}),
            'income': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Familiares',
                Row(
                    Column('family_composition', css_class='col-12'),
                    Column('income', css_class='col-6')
                )
            ),
            Fieldset(
                'Vulnerabilidades',
                'vulnerabilities',
                'substance_use'
            ),
            Fieldset(
                'Finalização',
                'observations',
                'signed_by_beneficiary'
            ),
            Submit('submit', 'Salvar Alterações', css_class='btn btn-primary')
        )

    def clean_income(self):
        income = self.cleaned_data.get('income')
        if income is not None and income < 0:
            raise ValidationError('A renda não pode ser negativa.')
        return income
