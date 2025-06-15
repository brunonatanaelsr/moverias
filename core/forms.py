from django import forms
from django.conf import settings


class EmailConfigForm(forms.Form):
    """Formulário para configuração de email SMTP"""
    
    email_backend = forms.ChoiceField(
        label='Backend de Email',
        choices=[
            ('django.core.mail.backends.smtp.EmailBackend', 'SMTP'),
            ('django.core.mail.backends.console.EmailBackend', 'Console (Debug)'),
            ('django.core.mail.backends.filebased.EmailBackend', 'Arquivo'),
            ('django.core.mail.backends.dummy.EmailBackend', 'Dummy (Não envia)'),
        ],
        initial='django.core.mail.backends.smtp.EmailBackend',
        help_text='Escolha o método de envio de emails'
    )
    
    email_host = forms.CharField(
        label='Servidor SMTP',
        max_length=255,
        initial='smtp.gmail.com',
        help_text='Ex: smtp.gmail.com, smtp.outlook.com, smtp.sendgrid.net'
    )
    
    email_port = forms.IntegerField(
        label='Porta SMTP',
        initial=587,
        help_text='587 para TLS, 465 para SSL, 25 para não criptografado'
    )
    
    email_use_tls = forms.BooleanField(
        label='Usar TLS',
        required=False,
        initial=True,
        help_text='Recomendado para a maioria dos provedores SMTP'
    )
    
    email_use_ssl = forms.BooleanField(
        label='Usar SSL',
        required=False,
        initial=False,
        help_text='Use apenas se o provedor exigir SSL em vez de TLS'
    )
    
    email_host_user = forms.CharField(
        label='Usuário SMTP',
        max_length=255,
        required=False,
        help_text='Seu email ou nome de usuário SMTP'
    )
    
    email_host_password = forms.CharField(
        label='Senha SMTP',
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text='Sua senha ou token de aplicativo'
    )
    
    default_from_email = forms.EmailField(
        label='Email Remetente Padrão',
        initial='noreply@movemarias.org',
        help_text='Email que aparecerá como remetente'
    )
    
    server_email = forms.EmailField(
        label='Email do Servidor',
        initial='server@movemarias.org',
        help_text='Email usado para notificações de erro do servidor'
    )
    
    test_email = forms.EmailField(
        label='Email para Teste',
        required=False,
        help_text='Digite um email para enviar um teste'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar classes CSS do Tailwind
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded'
                })
            else:
                field.widget.attrs.update({
                    'class': 'mt-1 focus:ring-purple-500 focus:border-purple-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md'
                })
                
        # Campos específicos
        self.fields['email_host_password'].widget.attrs.update({
            'placeholder': 'Digite a senha ou token do aplicativo'
        })
        
        self.fields['test_email'].widget.attrs.update({
            'placeholder': 'exemplo@email.com'
        })
