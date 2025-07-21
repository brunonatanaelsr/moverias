from django import forms
from django.contrib.auth import get_user_model
from core.validation import (
    MoveMariasModelForm, CPFField, PhoneField, CEPField, 
    PasswordField, ImageField
)
from .models import (
    Employee, Department, JobPosition, 
    EmployeeDocument, PerformanceReview, TrainingRecord
)

User = get_user_model()


class DepartmentForm(MoveMariasModelForm):
    """Formulário para criar/editar departamentos"""
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Nome do departamento',
                'maxlength': 100
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descrição do departamento'
            }),
            'manager': forms.Select(attrs={
                'class': 'mm-form-select-enhanced'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(is_active=True)
        self.fields['manager'].empty_label = "Selecione um gerente"


class JobPositionForm(MoveMariasModelForm):
    """Formulário para criar/editar cargos"""
    
    class Meta:
        model = JobPosition
        fields = [
            'title', 'description', 'requirements', 'responsibilities',
            'department', 'salary_range_min', 'salary_range_max', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Título do cargo',
                'maxlength': 100
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descrição do cargo'
            }),
            'requirements': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Requisitos para o cargo'
            }),
            'responsibilities': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Responsabilidades do cargo'
            }),
            'department': forms.Select(attrs={
                'class': 'mm-form-select-enhanced'
            }),
            'salary_range_min': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Salário mínimo',
                'min': '0'
            }),
            'salary_range_max': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Salário máximo',
                'min': '0'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_range_min')
        salary_max = cleaned_data.get('salary_range_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError('Salário mínimo não pode ser maior que o salário máximo')
        
        return cleaned_data


class EmployeeForm(MoveMariasModelForm):
    """Formulário para criar/editar funcionários"""
    
    # Campos customizados com validação
    cpf = CPFField(label='CPF')
    phone = PhoneField(label='Telefone')
    zip_code = CEPField(label='CEP')
    emergency_contact_phone = PhoneField(label='Telefone do contato de emergência')
    
    class Meta:
        model = Employee
        fields = [
            'user', 'employee_number', 'full_name', 'cpf', 'rg', 'birth_date',
            'gender', 'marital_status', 'phone', 'personal_email', 'address',
            'city', 'state', 'zip_code', 'emergency_contact_name',
            'emergency_contact_relationship', 'emergency_contact_phone',
            'job_position', 'department', 'direct_supervisor', 'employment_type',
            'employment_status', 'hire_date', 'salary', 'education_level',
            'skills', 'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'mm-form-select-enhanced'
            }),
            'employee_number': forms.TextInput(attrs={
                'placeholder': 'Número de matrícula',
                'maxlength': 20
            }),
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Nome completo',
                'maxlength': 200
            }),
            'rg': forms.TextInput(attrs={
                'placeholder': 'RG',
                'maxlength': 20
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'data-validation': 'birth-date'
            }),
            'gender': forms.Select(attrs={
                'class': 'mm-form-select-enhanced'
            }),
            'marital_status': forms.Select(attrs={
                'class': 'mm-form-select-enhanced'
            }),
            'personal_email': forms.EmailInput(attrs={
                'placeholder': 'email@exemplo.com'
            }),
            'address': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Endereço completo'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'Cidade',
                'maxlength': 100
            }),
            'state': forms.TextInput(attrs={
                'placeholder': 'UF',
                'maxlength': 2,
                'data-validation': 'state'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'placeholder': 'Nome do contato de emergência',
                'maxlength': 200
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parentesco'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'job_position': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'direct_supervisor': forms.Select(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Salário'
            }),
            'education_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nível de escolaridade'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Habilidades e competências'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações'
            }),
        }


class EmployeeDocumentForm(forms.ModelForm):
    """Formulário para upload de documentos de funcionários"""
    
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'title', 'description', 'file', 'is_confidential']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do documento'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do documento'
            }),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PerformanceReviewForm(forms.ModelForm):
    """Formulário para avaliações de desempenho"""
    
    class Meta:
        model = PerformanceReview
        fields = [
            'employee', 'review_type', 'review_period_start', 'review_period_end',
            'technical_skills', 'communication', 'teamwork', 'leadership',
            'punctuality', 'productivity', 'strengths', 'areas_for_improvement',
            'goals_for_next_period', 'employee_comments', 'review_date', 'is_final'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'review_type': forms.Select(attrs={'class': 'form-control'}),
            'review_period_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'review_period_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'technical_skills': forms.Select(attrs={'class': 'form-control'}),
            'communication': forms.Select(attrs={'class': 'form-control'}),
            'teamwork': forms.Select(attrs={'class': 'form-control'}),
            'leadership': forms.Select(attrs={'class': 'form-control'}),
            'punctuality': forms.Select(attrs={'class': 'form-control'}),
            'productivity': forms.Select(attrs={'class': 'form-control'}),
            'strengths': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Pontos fortes do funcionário'
            }),
            'areas_for_improvement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Áreas que precisam de melhoria'
            }),
            'goals_for_next_period': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Metas para o próximo período'
            }),
            'employee_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentários do funcionário'
            }),
            'review_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class TrainingRecordForm(forms.ModelForm):
    """Formulário para registros de treinamento"""
    
    class Meta:
        model = TrainingRecord
        fields = [
            'employee', 'training_name', 'training_type', 'provider',
            'start_date', 'end_date', 'hours', 'cost', 'status',
            'certificate_obtained', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'training_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do treinamento'
            }),
            'training_type': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Provedor/Instituição'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Carga horária'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Custo do treinamento'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações'
            }),
        }


class EmployeeSearchForm(forms.Form):
    """Formulário de busca para funcionários"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, email ou CPF...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label='Todos os departamentos',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Employee.EMPLOYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TrainingSearchForm(forms.Form):
    """Formulário de busca para treinamentos"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar treinamentos...'
        })
    )
    training_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + TrainingRecord.TRAINING_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + TrainingRecord.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(employment_status='active'),
        required=False,
        empty_label='Todos os funcionários',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
