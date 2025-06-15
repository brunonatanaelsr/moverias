from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from crispy_forms.bootstrap import FormActions

from .models import (
    Employee, Department, JobPosition, 
    EmployeeDocument, PerformanceReview, TrainingRecord
)

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """Formulário para criação/edição de funcionários."""
    
    class Meta:
        model = Employee
        fields = [
            'user', 'cpf', 'phone', 'mobile_phone', 'address', 'city', 'state', 'zip_code',
            'department', 'job_position', 'supervisor', 'hire_date', 'salary', 'benefits',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'education_level', 'skills', 'certifications', 'photo', 'notes', 'is_active'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'benefits': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'certifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': '(11) 0000-0000', 'class': 'form-control'}),
            'mobile_phone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000', 'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Filtrar supervisores para não incluir o próprio funcionário
        if self.instance.pk:
            self.fields['supervisor'].queryset = Employee.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)
        
        self.helper.layout = Layout(
            HTML('<div class="card"><div class="card-header"><h4>Informações Pessoais</h4></div><div class="card-body">'),
            Row(
                Column('user', css_class='form-group col-md-6'),
                Column('cpf', css_class='form-group col-md-6'),
            ),
            Row(
                Column('phone', css_class='form-group col-md-6'),
                Column('mobile_phone', css_class='form-group col-md-6'),
            ),
            'address',
            Row(
                Column('city', css_class='form-group col-md-4'),
                Column('state', css_class='form-group col-md-4'),
                Column('zip_code', css_class='form-group col-md-4'),
            ),
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Informações Profissionais</h4></div><div class="card-body">'),
            Row(
                Column('department', css_class='form-group col-md-6'),
                Column('job_position', css_class='form-group col-md-6'),
            ),
            Row(
                Column('supervisor', css_class='form-group col-md-4'),
                Column('hire_date', css_class='form-group col-md-4'),
                Column('salary', css_class='form-group col-md-4'),
            ),
            'benefits',
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Contato de Emergência</h4></div><div class="card-body">'),
            Row(
                Column('emergency_contact_name', css_class='form-group col-md-4'),
                Column('emergency_contact_phone', css_class='form-group col-md-4'),
                Column('emergency_contact_relationship', css_class='form-group col-md-4'),
            ),
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Formação e Competências</h4></div><div class="card-body">'),
            'education_level',
            'skills',
            'certifications',
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Outros</h4></div><div class="card-body">'),
            'photo',
            'notes',
            'is_active',
            HTML('</div></div>'),
            
            FormActions(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url "hr:employee_list" %}" class="btn btn-secondary">Cancelar</a>'),
            )
        )


class DepartmentForm(forms.ModelForm):
    """Formulário para criação/edição de departamentos."""
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Salvar', css_class='btn btn-primary'))


class JobPositionForm(forms.ModelForm):
    """Formulário para criação/edição de cargos."""
    
    class Meta:
        model = JobPosition
        fields = ['title', 'description', 'requirements', 'min_salary', 'max_salary', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'min_salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'max_salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'requirements',
            Row(
                Column('min_salary', css_class='form-group col-md-6'),
                Column('max_salary', css_class='form-group col-md-6'),
            ),
            'is_active',
            FormActions(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
            )
        )


class EmployeeDocumentForm(forms.ModelForm):
    """Formulário para upload de documentos de funcionários."""
    
    class Meta:
        model = EmployeeDocument
        fields = ['title', 'document_type', 'file', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Salvar', css_class='btn btn-primary'))


class PerformanceReviewForm(forms.ModelForm):
    """Formulário para avaliações de desempenho."""
    
    class Meta:
        model = PerformanceReview
        fields = [
            'employee', 'reviewer', 'review_period_start', 'review_period_end',
            'goals_achievement', 'quality_of_work', 'teamwork', 'communication',
            'punctuality', 'initiative', 'leadership', 'overall_rating',
            'strengths', 'areas_for_improvement', 'development_plan', 'status'
        ]
        widgets = {
            'review_period_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'review_period_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'goals_achievement': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'quality_of_work': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'teamwork': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'communication': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'punctuality': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'initiative': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'leadership': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'overall_rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'strengths': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'areas_for_improvement': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'development_plan': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<div class="card"><div class="card-header"><h4>Informações da Avaliação</h4></div><div class="card-body">'),
            Row(
                Column('employee', css_class='form-group col-md-6'),
                Column('reviewer', css_class='form-group col-md-6'),
            ),
            Row(
                Column('review_period_start', css_class='form-group col-md-6'),
                Column('review_period_end', css_class='form-group col-md-6'),
            ),
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Critérios de Avaliação (1-5)</h4></div><div class="card-body">'),
            Row(
                Column('goals_achievement', css_class='form-group col-md-6'),
                Column('quality_of_work', css_class='form-group col-md-6'),
            ),
            Row(
                Column('teamwork', css_class='form-group col-md-6'),
                Column('communication', css_class='form-group col-md-6'),
            ),
            Row(
                Column('punctuality', css_class='form-group col-md-4'),
                Column('initiative', css_class='form-group col-md-4'),
                Column('leadership', css_class='form-group col-md-4'),
            ),
            'overall_rating',
            HTML('</div></div>'),
            
            HTML('<div class="card mt-3"><div class="card-header"><h4>Comentários e Plano de Desenvolvimento</h4></div><div class="card-body">'),
            'strengths',
            'areas_for_improvement',
            'development_plan',
            'status',
            HTML('</div></div>'),
            
            FormActions(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
            )
        )


class TrainingRecordForm(forms.ModelForm):
    """Formulário para registros de treinamento."""
    
    class Meta:
        model = TrainingRecord
        fields = [
            'employee', 'training_name', 'training_type', 'description',
            'start_date', 'completion_date', 'duration_hours', 'status',
            'certificate_number', 'cost', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={'min': 0, 'step': '0.5', 'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('employee', css_class='form-group col-md-6'),
                Column('training_type', css_class='form-group col-md-6'),
            ),
            'training_name',
            'description',
            Row(
                Column('start_date', css_class='form-group col-md-6'),
                Column('completion_date', css_class='form-group col-md-6'),
            ),
            Row(
                Column('duration_hours', css_class='form-group col-md-4'),
                Column('status', css_class='form-group col-md-4'),
                Column('cost', css_class='form-group col-md-4'),
            ),
            'certificate_number',
            'notes',
            FormActions(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
            )
        )


class EmployeeSearchForm(forms.Form):
    """Formulário de busca de funcionários."""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nome, email ou CPF...',
            'class': 'form-control'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Todos os departamentos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    position = forms.ModelChoiceField(
        queryset=JobPosition.objects.filter(is_active=True),
        required=False,
        empty_label="Todos os cargos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-4'),
                Column('department', css_class='form-group col-md-3'),
                Column('position', css_class='form-group col-md-3'),
                Column(Submit('submit', 'Buscar', css_class='btn btn-primary'), css_class='form-group col-md-2'),
            )
        )
