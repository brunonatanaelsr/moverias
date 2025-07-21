from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import (
    CommunicationMessage, MessageResponse, MessageAttachment, 
    CommunicationPreferences, MessageRecipient
)

User = get_user_model()

class CommunicationMessageForm(forms.ModelForm):
    """Formulário para criação/edição de mensagens"""
    
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        }),
        required=False,
        label='Destinatários'
    )
    
    send_to_all = forms.BooleanField(
        required=False,
        label='Enviar para todos os usuários',
        help_text='Marque esta opção para enviar para todos os usuários do sistema',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )
    
    schedule_for_later = forms.BooleanField(
        required=False,
        label='Agendar para envio posterior',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )
    
    publish_date = forms.DateTimeField(
        required=False,
        label='Data de publicação',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
        })
    )
    
    class Meta:
        model = CommunicationMessage
        fields = [
            'title', 'content', 'message_type', 'priority', 'category',
            'requires_response', 'allow_responses', 'tags', 'publish_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Título da mensagem'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Digite o conteúdo da mensagem...'
            }),
            'message_type': forms.Select(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'priority': forms.Select(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Tags separadas por vírgula'
            }),
            'requires_response': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'allow_responses': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'tags': forms.TextInput(attrs={
                'placeholder': 'Separar tags com vírgula'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da mensagem'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar destinatários baseado no tipo de usuário
        if self.user:
            if self.user.user_type == 'admin':
                self.fields['recipients'].queryset = User.objects.all()
            elif self.user.user_type == 'ngo':
                # NGO pode enviar para beneficiários e outros NGOs
                self.fields['recipients'].queryset = User.objects.filter(
                    user_type__in=['beneficiary', 'ngo']
                )
            else:
                # Beneficiários podem enviar apenas para NGOs e admins
                self.fields['recipients'].queryset = User.objects.filter(
                    user_type__in=['ngo', 'admin']
                )
    
    def clean(self):
        cleaned_data = super().clean()
        recipients = cleaned_data.get('recipients')
        send_to_all = cleaned_data.get('send_to_all')
        schedule_for_later = cleaned_data.get('schedule_for_later')
        publish_date = cleaned_data.get('publish_date')
        
        # Validar destinatários
        if not send_to_all and not recipients:
            raise ValidationError('Você deve selecionar destinatários ou marcar "Enviar para todos"')
        
        # Validar agendamento
        if schedule_for_later and not publish_date:
            raise ValidationError('Data de publicação é obrigatória para agendamento')
        
        if publish_date and publish_date <= timezone.now():
            raise ValidationError('Data de publicação deve ser futura')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.author = self.user
        
        # Definir status baseado no agendamento
        if self.cleaned_data.get('schedule_for_later'):
            instance.status = 'scheduled'
        else:
            instance.status = 'published'
            if not instance.publish_date:
                instance.publish_date = timezone.now()
        
        if commit:
            instance.save()
            
            # Criar recipients
            recipients = self.cleaned_data.get('recipients')
            send_to_all = self.cleaned_data.get('send_to_all')
            
            if send_to_all:
                # Enviar para todos os usuários
                for user in User.objects.all():
                    MessageRecipient.objects.create(
                        message=instance,
                        user=user
                    )
            elif recipients:
                # Enviar para usuários selecionados
                for user in recipients:
                    MessageRecipient.objects.create(
                        message=instance,
                        user=user
                    )
        
        return instance


class MessageResponseForm(forms.ModelForm):
    """Formulário para respostas a mensagens"""
    
    class Meta:
        model = MessageResponse
        fields = ['content', 'response_type']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Digite sua resposta...'
            }),
            'response_type': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.message = kwargs.pop('message', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        if self.message:
            instance.message = self.message
        
        if commit:
            instance.save()
        
        return instance


class MessageAttachmentForm(forms.ModelForm):
    """Formulário para anexos de mensagens"""
    
    class Meta:
        model = MessageAttachment
        fields = ['file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do arquivo (opcional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'
            })
        }


class CommunicationPreferencesForm(forms.ModelForm):
    """Formulário para preferências de comunicação"""
    
    class Meta:
        model = CommunicationPreferences
        exclude = ['user']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'push_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notification_frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quiet_hours_start': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance


class MessageFilterForm(forms.Form):
    """Formulário para filtros de mensagens"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar mensagens...'
        })
    )
    
    message_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + CommunicationMessage.MESSAGE_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas as categorias')] + CommunicationMessage.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas as prioridades')] + CommunicationMessage.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_read = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas'), ('true', 'Lidas'), ('false', 'Não lidas')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    author = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BulkMessageActionForm(forms.Form):
    """Formulário para ações em lote"""
    
    ACTION_CHOICES = [
        ('mark_read', 'Marcar como lida'),
        ('mark_unread', 'Marcar como não lida'),
        ('archive', 'Arquivar'),
        ('delete', 'Excluir'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    message_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_message_ids(self):
        ids = self.cleaned_data.get('message_ids')
        if ids:
            try:
                return [int(id) for id in ids.split(',')]
            except ValueError:
                raise ValidationError('IDs de mensagens inválidos')
        return []


class QuickMessageForm(forms.ModelForm):
    """Formulário simplificado para mensagens rápidas"""
    
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CommunicationMessage
        fields = ['title', 'content', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assunto da mensagem'
            }),
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Mensagem...'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar destinatários baseado no tipo de usuário
        if self.user:
            if self.user.user_type == 'admin':
                self.fields['recipient'].queryset = User.objects.all()
            elif self.user.user_type == 'ngo':
                self.fields['recipient'].queryset = User.objects.filter(
                    user_type__in=['beneficiary', 'ngo']
                )
            else:
                self.fields['recipient'].queryset = User.objects.filter(
                    user_type__in=['ngo', 'admin']
                )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Definir valores padrão para mensagem rápida
        instance.author = self.user
        instance.message_type = 'notification'
        instance.status = 'published'
        instance.publish_date = timezone.now()
        
        if commit:
            instance.save()
            
            # Criar recipient
            recipient = self.cleaned_data.get('recipient')
            if recipient:
                MessageRecipient.objects.create(
                    message=instance,
                    user=recipient
                )
        
        return instance
