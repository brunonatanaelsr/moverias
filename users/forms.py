from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from .models import CustomUser, UserProfile, SystemRole


class CustomUserForm(UserCreationForm):
    """Formulário para criação/edição de usuários"""
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'full_name', 'role', 'phone', 'department', 'is_active']
        
    def __init__(self, *args, **kwargs):
        is_self_edit = kwargs.pop('is_self_edit', False)
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['email'].required = True
        self.fields['full_name'].required = True
        
        # Se for edição própria, remover campos sensíveis
        if is_self_edit:
            if 'role' in self.fields:
                del self.fields['role']
            if 'is_active' in self.fields:
                del self.fields['is_active']
                
        # Aplicar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            })
            
        # Campos específicos
        self.fields['email'].widget.attrs.update({
            'placeholder': 'email@exemplo.com',
            'type': 'email'
        })
        
        self.fields['phone'].widget.attrs.update({
            'placeholder': '(11) 99999-9999'
        })
        
        self.fields['full_name'].widget.attrs.update({
            'placeholder': 'Nome completo do usuário'
        })


class UserProfileForm(forms.ModelForm):
    """Formulário para o perfil do usuário"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'birth_date', 'address', 'emergency_contact', 'emergency_phone', 
                 'skills', 'availability', 'notes']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Python, Django, Design Gráfico'}),
            'availability': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Segundas e quartas, manhã'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'emergency_contact': 'Nome do Contato de Emergência',
            'emergency_phone': 'Telefone do Contato de Emergência',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            })


class SystemRoleForm(forms.ModelForm):
    """Formulário para funções do sistema"""
    
    class Meta:
        model = SystemRole
        fields = ['name', 'description', 'permissions', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Organizar permissões por app
        permissions = Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'codename'
        )
        
        # Aplicar classes CSS
        for field_name, field in self.fields.items():
            if field_name != 'permissions':
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                })


class UserSearchForm(forms.Form):
    """Formulário de busca de usuários"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nome, email ou username...',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('', 'Todas as funções')] + CustomUser.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos os status'),
            ('active', 'Ativos'),
            ('inactive', 'Inativos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        })
    )


class UserPermissionForm(forms.ModelForm):
    """Formulário para gerenciar permissões de usuário"""
    
    class Meta:
        model = CustomUser
        fields = ['groups', 'user_permissions']
        widgets = {
            'groups': forms.CheckboxSelectMultiple(),
            'user_permissions': forms.CheckboxSelectMultiple(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar grupos relevantes
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        
        # Organizar permissões
        self.fields['user_permissions'].queryset = Permission.objects.select_related(
            'content_type'
        ).order_by('content_type__app_label', 'codename')
