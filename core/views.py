from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import EmailConfigForm
import os


def home(request):
    """Página inicial - redireciona para dashboard se logado"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'core/home.html')


def is_admin_or_staff(user):
    """Verifica se o usuário é admin ou staff"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin_or_staff)
def email_config(request):
    """Configuração de email SMTP"""
    
    if request.method == 'POST':
        form = EmailConfigForm(request.POST)
        
        if form.is_valid():
            # Salvar configurações no arquivo .env
            env_file_path = settings.BASE_DIR / '.env'
            
            # Ler arquivo .env atual
            env_vars = {}
            if env_file_path.exists():
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key] = value
            
            # Atualizar variáveis de email
            env_vars.update({
                'EMAIL_BACKEND': form.cleaned_data['email_backend'],
                'EMAIL_HOST': form.cleaned_data['email_host'],
                'EMAIL_PORT': str(form.cleaned_data['email_port']),
                'EMAIL_USE_TLS': str(form.cleaned_data['email_use_tls']),
                'EMAIL_USE_SSL': str(form.cleaned_data['email_use_ssl']),
                'EMAIL_HOST_USER': form.cleaned_data['email_host_user'],
                'EMAIL_HOST_PASSWORD': form.cleaned_data['email_host_password'],
                'DEFAULT_FROM_EMAIL': form.cleaned_data['default_from_email'],
                'SERVER_EMAIL': form.cleaned_data['server_email'],
            })
            
            # Escrever arquivo .env
            with open(env_file_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f'{key}={value}\n')
            
            messages.success(request, 'Configurações de email salvas com sucesso! Reinicie o servidor para aplicar as mudanças.')
            
            # Se email de teste foi fornecido, enviar teste
            test_email = form.cleaned_data.get('test_email')
            if test_email:
                try:
                    # Atualizar configurações temporariamente
                    settings.EMAIL_BACKEND = form.cleaned_data['email_backend']
                    settings.EMAIL_HOST = form.cleaned_data['email_host']
                    settings.EMAIL_PORT = form.cleaned_data['email_port']
                    settings.EMAIL_USE_TLS = form.cleaned_data['email_use_tls']
                    settings.EMAIL_USE_SSL = form.cleaned_data['email_use_ssl']
                    settings.EMAIL_HOST_USER = form.cleaned_data['email_host_user']
                    settings.EMAIL_HOST_PASSWORD = form.cleaned_data['email_host_password']
                    settings.DEFAULT_FROM_EMAIL = form.cleaned_data['default_from_email']
                    
                    send_mail(
                        subject='Teste de Email - Move Marias',
                        message=f'''
Este é um email de teste do sistema Move Marias.

Se você recebeu este email, significa que a configuração SMTP está funcionando corretamente.

Configurações testadas:
- Servidor: {form.cleaned_data['email_host']}:{form.cleaned_data['email_port']}
- TLS: {form.cleaned_data['email_use_tls']}
- Usuário: {form.cleaned_data['email_host_user']}

Data/Hora: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}

---
Sistema Move Marias
                        ''',
                        from_email=form.cleaned_data['default_from_email'],
                        recipient_list=[test_email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, f'Email de teste enviado com sucesso para {test_email}!')
                    
                except Exception as e:
                    messages.error(request, f'Erro ao enviar email de teste: {str(e)}')
            
            return redirect('core:email_config')
    else:
        # Carregar configurações atuais
        initial_data = {
            'email_backend': getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'),
            'email_host': getattr(settings, 'EMAIL_HOST', 'localhost'),
            'email_port': getattr(settings, 'EMAIL_PORT', 587),
            'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
            'email_use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
            'email_host_user': getattr(settings, 'EMAIL_HOST_USER', ''),
            'email_host_password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@movemarias.org'),
            'server_email': getattr(settings, 'SERVER_EMAIL', 'server@movemarias.org'),
        }
        form = EmailConfigForm(initial=initial_data)
    
    context = {
        'form': form,
        'current_backend': getattr(settings, 'EMAIL_BACKEND', 'Não configurado'),
        'current_host': getattr(settings, 'EMAIL_HOST', 'Não configurado'),
    }
    
    return render(request, 'core/email_config.html', context)
