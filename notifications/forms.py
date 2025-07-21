"""
Forms para o sistema de notificações
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Notification, NotificationPreference, NotificationTemplate, NotificationChannel

User = get_user_model()


class NotificationForm(forms.ModelForm):
    """Form para criar/editar notificações"""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'message', 'recipient', 'type', 'channel', 'priority'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'Título da notificação'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500',
                'rows': 4,
                'placeholder': 'Mensagem da notificação'
            }),
            'recipient': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'channel': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas usuários ativos
        self.fields['recipient'].queryset = User.objects.filter(is_active=True).order_by('full_name')
        
        # Filtrar apenas canais ativos
        self.fields['channel'].queryset = NotificationChannel.objects.filter(is_active=True)
        
        # Definir canal padrão se não existir
        if not self.fields['channel'].queryset.exists():
            # Criar canal web padrão se não existir
            channel, created = NotificationChannel.objects.get_or_create(
                name='web',
                defaults={
                    'display_name': 'Web',
                    'is_active': True
                }
            )
            self.fields['channel'].queryset = NotificationChannel.objects.filter(is_active=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS e configurações
        self.fields['recipient'].queryset = User.objects.filter(is_active=True)
        self.fields['recipient'].empty_label = "Selecione um usuário"
        
        # Tornar alguns campos obrigatórios
        self.fields['title'].required = True
        self.fields['message'].required = True
        self.fields['recipient'].required = True
        self.fields['type'].required = True


class NotificationPreferenceForm(forms.ModelForm):
    """Form para configurar preferências de notificação"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'workshop_notifications', 'certificate_notifications', 
            'project_notifications', 'coaching_notifications', 'system_notifications',
            'quiet_hours_start', 'quiet_hours_end', 'frequency_limit'
        ]
        widgets = {
            'email_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'push_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'in_app_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'workshop_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'certificate_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'project_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'coaching_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'system_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'quiet_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'frequency_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar help texts
        self.fields['email_enabled'].help_text = "Receber notificações por email"
        self.fields['sms_enabled'].help_text = "Receber notificações por SMS"
        self.fields['push_enabled'].help_text = "Receber notificações push"
        self.fields['in_app_enabled'].help_text = "Receber notificações na aplicação"
        self.fields['quiet_hours_start'].help_text = "Início do horário silencioso"
        self.fields['quiet_hours_end'].help_text = "Fim do horário silencioso"
        
        # Valores padrão
        self.fields['in_app_enabled'].initial = True
        self.fields['email_enabled'].initial = True


class NotificationTemplateForm(forms.ModelForm):
    """Form para criar/editar templates de notificação"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'type', 'channel', 'subject_template', 
            'content_template', 'priority', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do template'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'channel': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template do assunto'
            }),
            'content_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Template do conteúdo'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obrigatórios
        self.fields['name'].required = True
        self.fields['type'].required = True
        self.fields['channel'].required = True
        self.fields['subject_template'].required = True
        self.fields['content_template'].required = True
        
        # Configurar help texts
        self.fields['available_variables'].help_text = "JSON com variáveis disponíveis para uso no template"
        self.fields['html_content'].help_text = "Versão HTML do template (opcional)"
        
        # Valores padrão
        self.fields['is_active'].initial = True
    
    def clean_available_variables(self):
        """Valida JSON das variáveis disponíveis"""
        variables = self.cleaned_data.get('available_variables')
        if variables:
            try:
                import json
                json.loads(variables)
            except json.JSONDecodeError:
                raise ValidationError("Variáveis disponíveis devem ser um JSON válido.")
        return variables


class NotificationChannelForm(forms.ModelForm):
    """Form para configurar canais de notificação"""
    
    class Meta:
        model = NotificationChannel
        fields = ['name', 'display_name', 'is_active', 'configuration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do canal'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome de exibição'
            }),
            'configuration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Configuração específica do canal (JSON)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obrigatórios
        self.fields['name'].required = True
        self.fields['display_name'].required = True
        
        # Configurar help texts
        self.fields['configuration'].help_text = "JSON com configurações específicas do canal"
        
        # Valores padrão
        self.fields['is_active'].initial = True
    
    def clean_configuration(self):
        """Valida JSON da configuração"""
        configuration = self.cleaned_data.get('configuration')
        if configuration:
            try:
                import json
                json.loads(configuration)
            except json.JSONDecodeError:
                raise forms.ValidationError("Configuração deve ser um JSON válido")
        return configuration
        if configuration:
            try:
                import json
                json.loads(configuration)
            except json.JSONDecodeError:
                raise ValidationError("Configuração deve ser um JSON válido.")
        return configuration


class BulkNotificationForm(forms.Form):
    """Form para envio de notificações em lote"""
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título da notificação'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Mensagem da notificação'
        })
    )
    
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Selecione os usuários que devem receber a notificação"
    )
    
    category = forms.ChoiceField(
        choices=NotificationTemplate.NOTIFICATION_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    priority = forms.ChoiceField(
        choices=[
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        initial=2
    )
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Enviar por email"
    )
    
    send_push = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Enviar push notification"
    )
    
    send_in_app = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Enviar notificação na aplicação"
    )
    
    def clean(self):
        """Validações gerais do form"""
        cleaned_data = super().clean()
        
        # Ao menos um canal deve estar selecionado
        channels = [
            cleaned_data.get('send_email'),
            cleaned_data.get('send_push'),
            cleaned_data.get('send_in_app')
        ]
        
        if not any(channels):
            raise ValidationError("Pelo menos um canal de envio deve ser selecionado.")
        
        return cleaned_data


class NotificationSearchForm(forms.Form):
    """Form para busca de notificações"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar notificações...'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'Todas as categorias')] + list(NotificationTemplate.NOTIFICATION_TYPES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'Todas as prioridades')] + [
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos os status'),
            ('read', 'Lidas'),
            ('unread', 'Não lidas')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        """Validar datas"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("A data inicial deve ser anterior à data final.")
        
        return cleaned_data
