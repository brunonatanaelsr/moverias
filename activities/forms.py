"""
Formulários para o módulo de atividades dos beneficiários.
"""

from django import forms
from django.forms import ModelForm, DateInput, TimeInput, Select, Textarea, TextInput
from django.core.exceptions import ValidationError
from datetime import date, datetime, time

from members.models import Beneficiary
from social.models import SocialAnamnesis
from .models import (
    BeneficiaryActivity,
    ActivitySession,
    ActivityAttendance,
    ActivityFeedback,
    ActivityNote
)


class BeneficiaryActivityForm(ModelForm):
    """
    Formulário para criação e edição de atividades.
    """
    
    class Meta:
        model = BeneficiaryActivity
        fields = [
            'beneficiary',
            'title',
            'description',
            'activity_type',
            'status',
            'priority',
            'start_date',
            'end_date',
            'frequency',
            'facilitator',
            'location',
            'materials_needed',
            'objectives',
            'expected_outcomes',
            'social_anamnesis',
            'completion_percentage',
        ]
        
        widgets = {
            'beneficiary': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'title': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da atividade',
                'required': True
            }),
            'description': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição detalhada da atividade'
            }),
            'activity_type': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'priority': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'end_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'frequency': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'facilitator': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do facilitador/responsável',
                'required': True
            }),
            'location': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local onde será realizada a atividade',
                'required': True
            }),
            'materials_needed': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Materiais necessários para a atividade'
            }),
            'objectives': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivos da atividade',
                'required': True
            }),
            'expected_outcomes': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Resultados esperados'
            }),
            'social_anamnesis': Select(attrs={
                'class': 'form-select'
            }),
            'completion_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'value': 0
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar beneficiárias ativas
        self.fields['beneficiary'].queryset = Beneficiary.objects.filter(
            status='ATIVA'
        ).order_by('full_name')
        
        # Filtrar anamneses sociais se beneficiária já foi selecionada
        if self.instance and self.instance.beneficiary:
            self.fields['social_anamnesis'].queryset = SocialAnamnesis.objects.filter(
                beneficiary=self.instance.beneficiary
            ).order_by('-created_at')
        else:
            self.fields['social_anamnesis'].queryset = SocialAnamnesis.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(
                    "A data de início deve ser anterior à data de término."
                )
        
        return cleaned_data


class ActivitySessionForm(ModelForm):
    """
    Formulário para criação e edição de sessões.
    """
    
    class Meta:
        model = ActivitySession
        fields = [
            'session_number',
            'title',
            'description',
            'session_date',
            'start_time',
            'end_time',
            'status',
            'facilitator',
            'location',
            'materials_used',
            'content_covered',
            'objectives_achieved',
            'observations',
        ]
        
        widgets = {
            'session_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'required': True
            }),
            'title': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da sessão',
                'required': True
            }),
            'description': Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descrição da sessão'
            }),
            'session_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'start_time': TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'end_time': TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'status': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'facilitator': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do facilitador',
                'required': True
            }),
            'location': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local da sessão',
                'required': True
            }),
            'materials_used': Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Materiais utilizados'
            }),
            'content_covered': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Conteúdo abordado na sessão'
            }),
            'objectives_achieved': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivos alcançados'
            }),
            'observations': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        session_date = cleaned_data.get('session_date')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError(
                    "O horário de início deve ser anterior ao horário de término."
                )
        
        # Validar se a sessão não está muito no passado
        if session_date and session_date < date.today() - timedelta(days=30):
            raise ValidationError(
                "Não é possível criar sessões com mais de 30 dias no passado."
            )
        
        return cleaned_data


class ActivityAttendanceForm(ModelForm):
    """
    Formulário para registro de presença.
    """
    
    class Meta:
        model = ActivityAttendance
        fields = [
            'attended',
            'arrival_time',
            'departure_time',
            'notes',
            'excuse_reason',
        ]
        
        widgets = {
            'attended': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'attended-checkbox'
            }),
            'arrival_time': TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'departure_time': TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'notes': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a presença'
            }),
            'excuse_reason': Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Motivo da ausência (se aplicável)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        attended = cleaned_data.get('attended')
        arrival_time = cleaned_data.get('arrival_time')
        departure_time = cleaned_data.get('departure_time')
        excuse_reason = cleaned_data.get('excuse_reason')
        
        if attended:
            if not arrival_time:
                raise ValidationError(
                    "Horário de chegada é obrigatório quando presente."
                )
            if not departure_time:
                raise ValidationError(
                    "Horário de saída é obrigatório quando presente."
                )
            if arrival_time and departure_time and arrival_time >= departure_time:
                raise ValidationError(
                    "Horário de chegada deve ser anterior ao horário de saída."
                )
        else:
            if not excuse_reason:
                raise ValidationError(
                    "Motivo da ausência é obrigatório quando ausente."
                )
        
        return cleaned_data


class ActivityFeedbackForm(ModelForm):
    """
    Formulário para feedback das atividades.
    """
    
    class Meta:
        model = ActivityFeedback
        fields = [
            'rating',
            'content_quality',
            'facilitator_rating',
            'positive_aspects',
            'improvements_suggested',
            'additional_comments',
            'would_recommend',
        ]
        
        widgets = {
            'rating': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'content_quality': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'facilitator_rating': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'positive_aspects': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Aspectos positivos da atividade'
            }),
            'improvements_suggested': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Sugestões de melhoria'
            }),
            'additional_comments': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comentários adicionais'
            }),
            'would_recommend': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ActivityNoteForm(ModelForm):
    """
    Formulário para notas das atividades.
    """
    
    class Meta:
        model = ActivityNote
        fields = [
            'note_type',
            'title',
            'content',
            'is_confidential',
        ]
        
        widgets = {
            'note_type': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'title': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da nota',
                'required': True
            }),
            'content': Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Conteúdo da nota',
                'required': True
            }),
            'is_confidential': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ActivityFilterForm(forms.Form):
    """
    Formulário para filtros de atividades.
    """
    
    beneficiary = forms.ModelChoiceField(
        queryset=Beneficiary.objects.filter(status='ATIVA').order_by('full_name'),
        empty_label="Todas as beneficiárias",
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    activity_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + BeneficiaryActivity.ACTIVITY_TYPES,
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + BeneficiaryActivity.STATUS_CHOICES,
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'Todas as prioridades')] + BeneficiaryActivity.PRIORITY_CHOICES,
        required=False,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError(
                    "A data inicial deve ser anterior à data final."
                )
        
        return cleaned_data


class QuickSessionForm(forms.Form):
    """
    Formulário simplificado para criação rápida de sessões.
    """
    
    session_date = forms.DateField(
        widget=DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    
    start_time = forms.TimeField(
        widget=TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'required': True
        })
    )
    
    end_time = forms.TimeField(
        widget=TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'required': True
        })
    )
    
    topic = forms.CharField(
        max_length=200,
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tópico da sessão',
            'required': True
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError(
                    "O horário de início deve ser anterior ao horário de término."
                )
        
        return cleaned_data
