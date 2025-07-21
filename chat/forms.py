from django import forms
from django.contrib.auth import get_user_model
from .models import ChatChannel, ChatMessage, ChatChannelMembership

User = get_user_model()
# Aliases for backward compatibility
ChatRoom = ChatChannel
ChatRoomMembership = ChatChannelMembership


class ChatRoomForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Selecione os membros iniciais da sala (opcional)"
    )

    class Meta:
        model = ChatChannel
        fields = ['name', 'description', 'channel_type', 'max_members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Nome da sala'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Descrição da sala',
                'rows': 3
            }),
            'channel_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': '50'
            })
        }

    def save(self, commit=True):
        room = super().save(commit=commit)
        
        if commit:
            # Adicionar membros selecionados
            members = self.cleaned_data.get('members', [])
            for member in members:
                ChatRoomMembership.objects.get_or_create(
                    user=member,
                    room=room,
                    defaults={'role': 'member'}
                )
        
        return room


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent resize-none',
                'placeholder': 'Digite sua mensagem...',
                'rows': 2,
                'maxlength': 1000
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False  # Permitir apenas anexo
        self.fields['attachment'].help_text = "Arquivos até 10MB (imagens, documentos, etc.)"

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        attachment = cleaned_data.get('attachment')
        
        if not content and not attachment:
            raise forms.ValidationError("Digite uma mensagem ou anexe um arquivo.")
        
        return cleaned_data


class ChatRoomMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )
    
    role = forms.ChoiceField(
        choices=ChatRoomMembership.MEMBER_ROLES,
        initial='member',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )

    def __init__(self, *args, **kwargs):
        room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)
        
        if room:
            # Excluir usuários que já são membros
            self.fields['user'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id__in=room.members.values_list('id', flat=True))


class ChatSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
            'placeholder': 'Buscar mensagens...'
        })
    )
    
    room = forms.ModelChoiceField(
        queryset=ChatRoom.objects.all(),
        required=False,
        empty_label="Todas as salas",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar apenas salas do usuário
            self.fields['room'].queryset = ChatRoom.objects.filter(
                members=user,
                is_active=True
            )


class QuickMessageForm(forms.Form):
    """Formulário rápido para envio de mensagens via AJAX"""
    content = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent resize-none',
            'placeholder': 'Digite sua mensagem...',
            'rows': 1
        })
    )
    
    reply_to = forms.UUIDField(required=False, widget=forms.HiddenInput())


class ChatNotificationSettingsForm(forms.Form):
    """Formulário para configurações de notificações"""
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-move-purple-600 focus:ring-move-purple-500'
        })
    )
    
    desktop_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-move-purple-600 focus:ring-move-purple-500'
        })
    )
    
    sound_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-move-purple-600 focus:ring-move-purple-500'
        })
    )
    
    show_online_status = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-move-purple-600 focus:ring-move-purple-500'
        })
    )
    
    allow_direct_messages = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-move-purple-600 focus:ring-move-purple-500'
        })
    )
