from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Workshop, WorkshopSession, WorkshopEnrollment, SessionAttendance, WorkshopEvaluation
from members.models import Beneficiary


class WorkshopForm(forms.ModelForm):
    """Form para criação e edição de oficinas"""
    
    class Meta:
        model = Workshop
        fields = [
            'name', 'description', 'workshop_type', 'facilitator', 
            'location', 'start_date', 'end_date', 'status', 
            'max_participants', 'objectives', 'materials_needed'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da oficina'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição detalhada da oficina'
            }),
            'workshop_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'facilitator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do facilitador'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local onde será realizada'
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
                'max': 100
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivos da oficina'
            }),
            'materials_needed': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Materiais necessários (opcional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError({
                    'end_date': 'A data de término deve ser posterior à data de início.'
                })

        if start_date and start_date < timezone.now().date():
            raise ValidationError({
                'start_date': 'A data de início não pode ser no passado.'
            })

        return cleaned_data


class WorkshopSessionForm(forms.ModelForm):
    """Form para criação e edição de sessões de oficina"""
    
    class Meta:
        model = WorkshopSession
        fields = ['workshop', 'session_date', 'start_time', 'end_time', 'topic', 'notes']
        widgets = {
            'workshop': forms.Select(attrs={
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
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a sessão (opcional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        session_date = cleaned_data.get('session_date')

        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError({
                    'end_time': 'O horário de término deve ser posterior ao horário de início.'
                })

        if session_date and session_date < timezone.now().date():
            raise ValidationError({
                'session_date': 'A data da sessão não pode ser no passado.'
            })

        return cleaned_data


class WorkshopEnrollmentForm(forms.ModelForm):
    """Form para matrícula em oficinas"""
    
    class Meta:
        model = WorkshopEnrollment
        fields = ['workshop', 'beneficiary', 'enrollment_date', 'status', 'notes']
        widgets = {
            'workshop': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary': forms.Select(attrs={
                'class': 'form-control'
            }),
            'enrollment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a matrícula (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas oficinas ativas para novas matrículas
        self.fields['workshop'].queryset = Workshop.objects.filter(
            status__in=['planejamento', 'ativo']
        ).order_by('name')
        
        # Filtrar beneficiários ativos
        self.fields['beneficiary'].queryset = Beneficiary.objects.filter(
            status='ativo'
        ).order_by('full_name')

    def clean(self):
        cleaned_data = super().clean()
        workshop = cleaned_data.get('workshop')
        beneficiary = cleaned_data.get('beneficiary')

        if workshop and beneficiary:
            # Verificar se já existe uma matrícula ativa para este beneficiário nesta oficina
            existing_enrollment = WorkshopEnrollment.objects.filter(
                workshop=workshop,
                beneficiary=beneficiary,
                status='ativo'
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_enrollment.exists():
                raise ValidationError({
                    'beneficiary': 'Este beneficiário já possui uma matrícula ativa nesta oficina.'
                })

            # Verificar se a oficina não excedeu o limite de participantes
            if workshop.max_participants:
                current_enrollments = WorkshopEnrollment.objects.filter(
                    workshop=workshop,
                    status='ativo'
                ).exclude(pk=self.instance.pk if self.instance else None).count()

                if current_enrollments >= workshop.max_participants:
                    raise ValidationError({
                        'workshop': f'Esta oficina já atingiu o limite máximo de {workshop.max_participants} participantes.'
                    })

        return cleaned_data


class SessionAttendanceForm(forms.ModelForm):
    """Form para registro de presença em sessões"""
    
    class Meta:
        model = SessionAttendance
        fields = ['session', 'enrollment', 'attended', 'notes']
        widgets = {
            'session': forms.Select(attrs={
                'class': 'form-control'
            }),
            'enrollment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'attended': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações sobre a presença (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if session:
            # Filtrar apenas matrículas da oficina relacionada à sessão
            self.fields['enrollment'].queryset = WorkshopEnrollment.objects.filter(
                workshop=session.workshop,
                status='ativo'
            ).select_related('beneficiary').order_by('beneficiary__full_name')


class WorkshopEvaluationForm(forms.ModelForm):
    """Form para avaliação de oficinas"""
    
    class Meta:
        model = WorkshopEvaluation
        fields = ['enrollment', 'rating', 'feedback', 'suggestions']
        widgets = {
            'enrollment': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'step': 1
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Feedback sobre a oficina'
            }),
            'suggestions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Sugestões para melhorias (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas matrículas ativas
        self.fields['enrollment'].queryset = WorkshopEnrollment.objects.filter(
            status='ativo'
        ).select_related('beneficiary', 'workshop').order_by('beneficiary__full_name')


class BulkAttendanceForm(forms.Form):
    """Form para registro em massa de presenças"""
    
    session = forms.ModelChoiceField(
        queryset=WorkshopSession.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Sessão'
    )
    
    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if session:
            self.session = session
            # Buscar todas as matrículas ativas da oficina
            enrollments = WorkshopEnrollment.objects.filter(
                workshop=session.workshop,
                status='ativo'
            ).select_related('beneficiary').order_by('beneficiary__full_name')
            
            # Criar um campo de checkbox para cada matrícula
            for enrollment in enrollments:
                field_name = f'attendance_{enrollment.id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=enrollment.beneficiary.full_name,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
                
                # Marcar como presente se já existe registro
                existing_attendance = SessionAttendance.objects.filter(
                    session=session,
                    enrollment=enrollment
                ).first()
                
                if existing_attendance:
                    self.fields[field_name].initial = existing_attendance.attended
