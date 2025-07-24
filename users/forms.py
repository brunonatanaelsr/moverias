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
            
        # Campos específicos com validação
        self.fields['email'].widget.attrs.update({
            'placeholder': 'email@exemplo.com',
            'type': 'email',
            'data-validate': 'email',
            'data-required': 'true',
            'data-check-uniqueness': 'true'
        })
        
        self.fields['phone'].widget.attrs.update({
            'placeholder': '(11) 99999-9999',
            'data-validate': 'phone'
        })
        
        self.fields['full_name'].widget.attrs.update({
            'placeholder': 'Nome completo do usuário',
            'data-validate': 'name',
            'data-required': 'true'
        })


class UserProfileForm(forms.ModelForm):
    """Formulário para o perfil do usuário"""
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'bio', 'birth_date', 'address', 'emergency_contact', 'emergency_phone', 
                 'skills', 'availability', 'notes']
        widgets = {
            'profile_image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'bio': forms.Textarea(attrs={'rows': 3}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Python, Django, Design Gráfico'}),
            'availability': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Segundas e quartas, manhã'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'profile_image': 'Foto de Perfil',
            'emergency_contact': 'Nome do Contato de Emergência',
            'emergency_phone': 'Telefone do Contato de Emergência',
        }
        help_texts = {
            'profile_image': 'Imagens aceitas: JPG, JPEG, PNG, GIF (máx. 2MB)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS
        for field_name, field in self.fields.items():
            if field_name == 'profile_image':
                # O widget já tem sua classe definida
                continue
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            })
            
        # Adicionar validação para telefone de emergência
        if 'emergency_phone' in self.fields:
            self.fields['emergency_phone'].widget.attrs.update({
                'data-validate': 'phone'
            })
    
    def clean_profile_image(self):
        """Validação customizada para imagem de perfil"""
        image = self.cleaned_data.get('profile_image')
        
        if image:
            # Verificar tamanho (2MB máximo)
            max_size = 2 * 1024 * 1024  # 2MB em bytes
            if image.size > max_size:
                raise forms.ValidationError(
                    f'A imagem é muito grande ({image.size / (1024*1024):.1f}MB). '
                    f'O tamanho máximo permitido é {max_size / (1024*1024):.0f}MB.'
                )
            
            # Verificar se é uma imagem válida
            try:
                from PIL import Image
                img = Image.open(image)
                img.verify()
            except Exception:
                raise forms.ValidationError('Arquivo inválido. Por favor, envie uma imagem válida.')
        
        return image


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


class UserCreateForm(UserCreationForm):
    """Formulário robusto para criação de usuários"""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'usuario@email.com'
        })
    )
    
    full_name = forms.CharField(
        label='Nome Completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Nome completo do usuário'
        })
    )
    
    role = forms.ChoiceField(
        label='Função',
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    phone = forms.CharField(
        label='Telefone',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '(85) 99999-9999'
        })
    )
    
    department = forms.CharField(
        label='Departamento',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Departamento ou setor'
        })
    )
    
    groups = forms.ModelMultipleChoiceField(
        label='Grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        })
    )
    
    is_staff = forms.BooleanField(
        label='Acesso ao Admin',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        }),
        help_text='Permite acesso ao painel administrativo do Django'
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'role', 'phone', 'department', 'groups', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'nome.usuario'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está em uso.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Adicionar aos grupos selecionados
            if self.cleaned_data.get('groups'):
                user.groups.set(self.cleaned_data['groups'])
        return user

class UserUpdateForm(forms.ModelForm):
    """Formulário robusto para atualização de usuários"""
    
    groups = forms.ModelMultipleChoiceField(
        label='Grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'full_name', 'role', 'phone', 'department', 'is_active', 'is_staff', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'role': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'department': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.all()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Atualizar grupos
            if 'groups' in self.cleaned_data:
                user.groups.set(self.cleaned_data['groups'])
        return user

class PermissionForm(forms.Form):
    """Formulário para gerenciar permissões de usuário"""
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Campo para grupos
        self.fields['groups'] = forms.ModelMultipleChoiceField(
            queryset=Group.objects.all(),
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
            required=False,
            label='Grupos'
        )
        
        # Campo para permissões individuais
        self.fields['permissions'] = forms.ModelMultipleChoiceField(
            queryset=Permission.objects.all().select_related('content_type'),
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
            required=False,
            label='Permissões Individuais'
        )
        
        if user:
            self.fields['groups'].initial = user.groups.all()
            self.fields['permissions'].initial = user.user_permissions.all()

class GroupForm(forms.ModelForm):
    """Formulário para criação/edição de grupos"""
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        }),
        required=False,
        label='Permissões do Grupo'
    )
    
    class Meta:
        model = Group
        fields = ('name', 'permissions')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nome do grupo'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.all()
    
    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            # Atualizar permissões
            if 'permissions' in self.cleaned_data:
                group.permissions.set(self.cleaned_data['permissions'])
        return group
