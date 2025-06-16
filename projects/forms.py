\
from django import forms
from .models import Project, ProjectEnrollment
from members.models import Beneficiary

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProjectEnrollmentForm(forms.ModelForm):
    beneficiary = forms.ModelChoiceField(
        queryset=Beneficiary.objects.order_by('full_name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Beneficiária'
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all().order_by('name'),
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
        if not Project.objects.exists():
            self.fields['project'].queryset = Project.objects.none()
            self.fields['project'].widget.attrs['disabled'] = True
            self.fields['project'].help_text = 'Não há projetos cadastrados. Crie um projeto antes de matricular beneficiárias.'
            # Optionally, make it not required if disabled, though Django might handle this.
            # self.fields['project'].required = False 
        else:
             # Ensure the queryset is fresh if projects were added after form class definition
            self.fields['project'].queryset = Project.objects.all().order_by('name')


        # If editing an existing instance, ensure the project field is correctly set
        if self.instance and self.instance.pk and self.instance.project:
            self.fields['project'].initial = self.instance.project
        elif not Project.objects.exists():
             self.fields['project'].initial = None


