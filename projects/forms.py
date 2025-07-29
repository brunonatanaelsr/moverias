"""
Forms para o módulo de projetos
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Project, ProjectEnrollment, ProjectSession, ProjectAttendance,
    ProjectEvaluation, ProjectResource
)
from members.models import Beneficiary


class ProjectForm(forms.ModelForm):
    """Form para criar/editar projetos"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'coordinator', 'location', 'start_date',
            'end_date', 'status', 'max_participants', 'objectives', 'target_audience'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do projeto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição do projeto'
            }),
            'coordinator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do coordenador'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local do projeto'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivos do projeto'
            }),
            'target_audience': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Público alvo'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obrigatórios
        self.fields['name'].required = True
        self.fields['coordinator'].required = True
        self.fields['start_date'].required = True
        self.fields['objectives'].required = True
        
        # Help texts
        self.fields['max_participants'].help_text = "Número máximo de participantes"
        self.fields['end_date'].help_text = "Data de término (opcional)"
        
        # Valores padrão
        self.fields['status'].initial = 'ATIVO'
        self.fields['max_participants'].initial = 30
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("A data de término deve ser posterior à data de início.")
        
        return cleaned_data


class ProjectEnrollmentForm(forms.ModelForm):
    """Form para inscrições em projetos"""
    
    class Meta:
        model = ProjectEnrollment
        fields = [
            'beneficiary', 'project', 'weekday', 'shift', 'start_time', 'status'
        ]
        widgets = {
            'beneficiary': forms.Select(attrs={
                'class': 'form-control'
            }),
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'weekday': forms.Select(attrs={
                'class': 'form-control'
            }),
            'shift': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar beneficiárias ativas
        self.fields['beneficiary'].queryset = Beneficiary.optimized_objects.filter(status='ATIVA')
        self.fields['beneficiary'].empty_label = "Selecione uma beneficiária"
        
        # Filtrar projetos ativos
        self.fields['project'].queryset = Project.optimized_objects.filter(status='ATIVO')
        self.fields['project'].empty_label = "Selecione um projeto"
        
        # Configurar campos obrigatórios
        self.fields['beneficiary'].required = True
        self.fields['project'].required = True
        self.fields['weekday'].required = True
        self.fields['shift'].required = True
        self.fields['start_time'].required = True
        
        # Valores padrão
        self.fields['status'].initial = 'ATIVO'
    
    def clean(self):
        cleaned_data = super().clean()
        beneficiary = cleaned_data.get('beneficiary')
        project = cleaned_data.get('project')
        
        # Verificar se já existe inscrição
        if beneficiary and project:
            existing = ProjectEnrollment.objects.filter(
                beneficiary=beneficiary,
                project=project
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError("Esta beneficiária já está inscrita neste projeto.")
        
        return cleaned_data


class ProjectSessionForm(forms.ModelForm):
    """Form para sessões de projeto"""
    
    class Meta:
        model = ProjectSession
        fields = [
            'project', 'session_date', 'start_time', 'end_time', 'topic',
            'description', 'facilitator', 'location', 'materials_needed',
            'is_mandatory'
        ]
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-control'
            }),
            'session_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tópico da sessão'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da sessão'
            }),
            'facilitator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do facilitador'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local da sessão'
            }),
            'materials_needed': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Materiais necessários'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar projetos ativos
        self.fields['project'].queryset = Project.optimized_objects.filter(status='ATIVO')
        self.fields['project'].empty_label = "Selecione um projeto"
        
        # Configurar campos obrigatórios
        self.fields['project'].required = True
        self.fields['session_date'].required = True
        self.fields['start_time'].required = True
        self.fields['end_time'].required = True
        self.fields['topic'].required = True
        self.fields['facilitator'].required = True
        
        # Valores padrão
        self.fields['is_mandatory'].initial = True
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        session_date = cleaned_data.get('session_date')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Horário de início deve ser anterior ao horário de término.")
        
        # Verificar conflitos de horário
        if session_date and start_time and end_time:
            project = cleaned_data.get('project')
            if project:
                conflicts = ProjectSession.objects.filter(
                    project=project,
                    session_date=session_date,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if conflicts.exists():
                    raise ValidationError("Existe conflito de horário com outra sessão.")
        
        return cleaned_data


class ProjectEvaluationForm(forms.ModelForm):
    """Form para avaliação de projeto"""
    
    class Meta:
        model = ProjectEvaluation
        fields = [
            'enrollment', 'session', 'rating', 'content_quality',
            'facilitator_rating', 'feedback', 'suggestions', 'would_recommend'
        ]
        widgets = {
            'enrollment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'session': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'content_quality': forms.Select(attrs={
                'class': 'form-control'
            }),
            'facilitator_rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Seu feedback sobre o projeto'
            }),
            'suggestions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Sugestões para melhorias'
            }),
            'would_recommend': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obrigatórios
        self.fields['enrollment'].required = True
        self.fields['rating'].required = True
        self.fields['content_quality'].required = True
        self.fields['facilitator_rating'].required = True
        self.fields['feedback'].required = True
        
        # Help texts
        self.fields['rating'].help_text = "Avaliação geral (1 = Péssimo, 5 = Excelente)"
        self.fields['content_quality'].help_text = "Qualidade do conteúdo (1 = Péssimo, 5 = Excelente)"
        self.fields['facilitator_rating'].help_text = "Avaliação do facilitador (1 = Péssimo, 5 = Excelente)"
        
        # Valores padrão
        self.fields['would_recommend'].initial = True


class ProjectResourceForm(forms.ModelForm):
    """Form para recursos do projeto"""
    
    class Meta:
        model = ProjectResource
        fields = [
            'name', 'resource_type', 'description', 'quantity', 'cost',
            'supplier', 'acquisition_date', 'is_available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do recurso'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do recurso'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fornecedor'
            }),
            'acquisition_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obrigatórios
        self.fields['name'].required = True
        self.fields['resource_type'].required = True
        self.fields['description'].required = True
        self.fields['quantity'].required = True
        
        # Valores padrão
        self.fields['quantity'].initial = 1
        self.fields['is_available'].initial = True
    project = forms.ModelChoiceField(
        queryset=Project.optimized_objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Projeto',
        empty_label=None  # Ensure no "-- -----" empty label by default
    )

    class Meta:
        model = ProjectEnrollment
        fields = ['beneficiary', 'project', 'weekday', 'shift', 'start_time', 'status']
        widgets = {
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Pop the 'user' kwarg if it's passed, as it's not used directly by ModelForm
        # but might be passed by the view.
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Handle the case where no projects exist
        if not Project.optimized_objects.exists():
            self.fields['project'].queryset = Project.optimized_objects.none()
            self.fields['project'].widget.attrs['disabled'] = True
            self.fields['project'].help_text = 'Não há projetos cadastrados. Crie um projeto antes de matricular beneficiárias.'
            # Optionally, make it not required if disabled, though Django might handle this.
            # self.fields['project'].required = False 
        else:
             # Ensure the queryset is fresh if projects were added after form class definition
            self.fields['project'].queryset = Project.optimized_objects.all().order_by('name')


        # If editing an existing instance, ensure the project field is correctly set
        if self.instance and self.instance.pk and self.instance.project:
            self.fields['project'].initial = self.instance.project
        elif not Project.optimized_objects.exists():
             self.fields['project'].initial = None


