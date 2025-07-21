from django import forms
from .models import (
    Announcement, InternalMemo, MemoResponse, Newsletter, 
    SuggestionBox, CommunicationSettings
)


class AnnouncementForm(forms.ModelForm):
    """Formulário para criar/editar comunicados"""
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'summary', 'category', 'priority',
            'departments', 'target_users', 'is_global', 'is_pinned',
            'requires_acknowledgment', 'publish_date', 'expire_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do comunicado'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Conteúdo do comunicado'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Resumo opcional'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'departments': forms.CheckboxSelectMultiple(),
            'target_users': forms.CheckboxSelectMultiple(),
            'publish_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'expire_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class InternalMemoForm(forms.ModelForm):
    """Formulário para criar/editar memorandos"""
    
    class Meta:
        model = InternalMemo
        fields = [
            'title', 'content', 'memo_type', 'to_users', 'to_departments',
            'requires_response', 'response_deadline', 'is_confidential'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do memorando'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Conteúdo do memorando'
            }),
            'memo_type': forms.Select(attrs={'class': 'form-control'}),
            'to_users': forms.CheckboxSelectMultiple(),
            'to_departments': forms.CheckboxSelectMultiple(),
            'response_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class MemoResponseForm(forms.ModelForm):
    """Formulário para responder memorandos"""
    
    class Meta:
        model = MemoResponse
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Sua resposta...'
            })
        }


class NewsletterForm(forms.ModelForm):
    """Formulário para criar/editar newsletters"""
    
    class Meta:
        model = Newsletter
        fields = ['title', 'content', 'summary']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da newsletter'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Conteúdo da newsletter'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Resumo opcional'
            }),
        }


class SuggestionBoxForm(forms.ModelForm):
    """Formulário para criar sugestões"""
    
    class Meta:
        model = SuggestionBox
        fields = ['title', 'description', 'suggestion_type', 'department', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da sugestão'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Descreva sua sugestão...'
            }),
            'suggestion_type': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }


class CommunicationSettingsForm(forms.ModelForm):
    """Formulário para configurações de comunicação"""
    
    class Meta:
        model = CommunicationSettings
        fields = [
            'email_announcements', 'email_memos', 'email_newsletters',
            'digest_frequency'
        ]
        widgets = {
            'digest_frequency': forms.Select(attrs={'class': 'form-control'}),
        }


class AnnouncementSearchForm(forms.Form):
    """Formulário de busca para comunicados"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar comunicados...'
        })
    )
    category = forms.ChoiceField(
        choices=[('', 'Todas as categorias')] + Announcement.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MemoSearchForm(forms.Form):
    """Formulário de busca para memorandos"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar memorandos...'
        })
    )
    memo_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + InternalMemo.MEMO_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    requires_response = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class SuggestionSearchForm(forms.Form):
    """Formulário de busca para sugestões"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar sugestões...'
        })
    )
    suggestion_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + SuggestionBox.SUGGESTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + SuggestionBox.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
