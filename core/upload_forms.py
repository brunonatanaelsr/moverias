"""
Forms para sistema de upload de arquivos
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from .models import FileUpload


class FileUploadForm(forms.ModelForm):
    """Form para upload de arquivos"""
    
    class Meta:
        model = FileUpload
        fields = ['file', 'title', 'description', 'category', 'is_public']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.xlsx,.xls,.txt',
                'id': 'file_input'
            }),
            'title': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Digite o título do arquivo...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Descrição opcional do arquivo...'
            }),
            'category': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
        help_texts = {
            'is_public': 'Marque para tornar o arquivo visível para todos os usuários',
            'file': 'Arquivos permitidos: PDF, DOC, DOCX, JPG, JPEG, PNG, GIF, XLSX, XLS, TXT (máx. 10MB)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['file'].required = True
        
        # Se não há arquivo, preencher título automaticamente
        if not self.initial.get('title') and 'file' in self.files:
            file_obj = self.files['file']
            if file_obj:
                # Remover extensão e usar como título inicial
                filename = file_obj.name
                if '.' in filename:
                    title = '.'.join(filename.split('.')[:-1])
                else:
                    title = filename
                self.initial['title'] = title
    
    def clean_file(self):
        """Validação customizada do arquivo"""
        file = self.cleaned_data.get('file')
        
        if not file:
            return file
        
        # Verificar tamanho (10MB máximo)
        max_size = 10 * 1024 * 1024  # 10MB em bytes
        if file.size > max_size:
            raise ValidationError(
                f'O arquivo é muito grande ({file.size / (1024*1024):.1f}MB). '
                f'O tamanho máximo permitido é {max_size / (1024*1024):.0f}MB.'
            )
        
        # Verificar extensão
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'xlsx', 'xls', 'txt']
        file_extension = file.name.split('.')[-1].lower() if '.' in file.name else ''
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Tipo de arquivo não permitido: .{file_extension}. '
                f'Extensões permitidas: {", ".join(allowed_extensions)}'
            )
        
        return file
    
    def clean_title(self):
        """Validação do título"""
        title = self.cleaned_data.get('title')
        
        if title:
            title = title.strip()
            if len(title) < 3:
                raise ValidationError('O título deve ter pelo menos 3 caracteres.')
            
            if len(title) > 200:
                raise ValidationError('O título não pode ter mais de 200 caracteres.')
        
        return title
    
    def save(self, commit=True):
        """Salvar com dados adicionais"""
        instance = super().save(commit=False)
        
        if self.cleaned_data.get('file'):
            # Preencher nome original se não estiver definido
            if not instance.original_name:
                instance.original_name = self.cleaned_data['file'].name
        
        if commit:
            instance.save()
        
        return instance


class FileSearchForm(forms.Form):
    """Form para busca de arquivos"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Buscar por título, descrição ou nome do arquivo...'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'Todas as categorias')] + FileUpload.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    only_public = forms.BooleanField(
        label='Apenas arquivos públicos',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )


class QuickUploadForm(forms.ModelForm):
    """Form simplificado para upload rápido"""
    
    class Meta:
        model = FileUpload
        fields = ['file', 'title']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.xlsx,.xls,.txt'
            }),
            'title': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm',
                'placeholder': 'Título do arquivo...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['file'].required = True
