from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
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

def csrf_failure(request, reason=""):
    """View para tratar falhas de CSRF"""
    context = {
        'reason': reason,
        'title': 'Erro de Segurança CSRF',
    }
    return render(request, 'core/csrf_failure.html', context, status=403)


@login_required
@user_passes_test(is_admin_or_staff)
def settings_view(request):
    """Página de configurações do sistema"""
    from django.contrib.auth import get_user_model
    from users.models import UserActivity
    
    User = get_user_model()  # Usa o modelo de usuário customizado
    
    # Estatísticas do sistema
    system_stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'admin_users': User.objects.filter(is_superuser=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'last_activity': UserActivity.objects.order_by('-timestamp').first(),
        'database_size': '0 MB',  # Placeholder
        'cache_status': 'Ativo' if hasattr(settings, 'CACHES') else 'Inativo',
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'timezone': settings.TIME_ZONE,
        'language': settings.LANGUAGE_CODE,
    }
    
    # Configurações de segurança
    security_settings = {
        'csrf_cookie_secure': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        'session_cookie_secure': getattr(settings, 'SESSION_COOKIE_SECURE', False),
        'secure_ssl_redirect': getattr(settings, 'SECURE_SSL_REDIRECT', False),
        'secure_hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 0),
        'secure_content_type_nosniff': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
        'secure_browser_xss_filter': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
    }
    
    context = {
        'system_stats': system_stats,
        'security_settings': security_settings,
        'title': 'Configurações do Sistema'
    }
    
    return render(request, 'core/settings.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def audit_logs(request):
    """Página de logs de auditoria"""
    from users.models import UserActivity
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Filtros
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_filter = request.GET.get('date', '')
    
    # Query base
    logs = UserActivity.objects.select_related('user').all()
    
    # Aplicar filtros
    if user_filter:
        logs = logs.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )
    
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)
    
    if date_filter:
        logs = logs.filter(timestamp__date=date_filter)
    
    # Ordenar por data mais recente
    logs = logs.order_by('-timestamp')
    
    # Paginação
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas dos logs
    log_stats = {
        'total_logs': UserActivity.objects.count(),
        'today_logs': UserActivity.objects.filter(timestamp__date=timezone.now().date()).count(),
        'unique_users': UserActivity.objects.values('user').distinct().count(),
        'most_active_user': UserActivity.objects.values('user__username').annotate(
            count=Count('id')
        ).order_by('-count').first(),
    }
    
    context = {
        'page_obj': page_obj,
        'log_stats': log_stats,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'date_filter': date_filter,
        'title': 'Logs de Auditoria'
    }
    
    return render(request, 'core/audit_logs.html', context)

@login_required
def global_search(request):
    """
    Busca global no sistema - pesquisa em múltiplos modelos
    """
    query = request.GET.get('search', '').strip()
    results = {
        'query': query,
        'users': [],
        'members': [],
        'projects': [],
        'workshops': [],
        'certificates': [],
        'notifications': [],
        'total_count': 0
    }
    
    if query and len(query) >= 2:  # Mínimo 2 caracteres
        from django.contrib.auth import get_user_model
        from django.db.models import Q
        
        User = get_user_model()
        
        # Buscar usuários
        try:
            from users.models import CustomUser
            users = CustomUser.objects.filter(
                Q(full_name__icontains=query) | 
                Q(email__icontains=query) |
                Q(username__icontains=query)
            ).select_related('profile')[:5]
            results['users'] = users
        except ImportError:
            pass
        
        # Buscar membros/beneficiários
        try:
            from members.models import Member
            members = Member.objects.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(cpf__icontains=query)
            )[:5]
            results['members'] = members
        except ImportError:
            pass
        
        # Buscar projetos
        try:
            from projects.models import Project
            projects = Project.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:5]
            results['projects'] = projects
        except ImportError:
            pass
        
        # Buscar workshops
        try:
            from workshops.models import Workshop
            workshops = Workshop.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )[:5]
            results['workshops'] = workshops
        except ImportError:
            pass
        
        # Buscar certificados
        try:
            from certificates.models import Certificate
            certificates = Certificate.objects.filter(
                Q(title__icontains=query) |
                Q(verification_code__icontains=query)
            )[:5]
            results['certificates'] = certificates
        except ImportError:
            pass
        
        # Buscar notificações
        try:
            from notifications.models import Notification
            notifications = Notification.objects.filter(
                Q(title__icontains=query) |
                Q(message__icontains=query),
                recipient=request.user
            )[:5]
            results['notifications'] = notifications
        except ImportError:
            pass
        
        # Calcular total
        results['total_count'] = (
            len(results['users']) +
            len(results['members']) + 
            len(results['projects']) +
            len(results['workshops']) +
            len(results['certificates']) +
            len(results['notifications'])
        )
    
    # Retornar JSON para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        
        # Converter querysets para dicts
        def serialize_results(queryset, fields):
            return [
                {field: str(getattr(obj, field, '')) for field in fields}
                for obj in queryset
            ]
        
        json_results = {
            'query': results['query'],
            'total_count': results['total_count'],
            'users': serialize_results(results['users'], ['id', 'full_name', 'email']),
            'members': serialize_results(results['members'], ['id', 'name', 'email']),
            'projects': serialize_results(results['projects'], ['id', 'name', 'description']),
            'workshops': serialize_results(results['workshops'], ['id', 'title', 'description']),
            'certificates': serialize_results(results['certificates'], ['id', 'title', 'verification_code']),
            'notifications': serialize_results(results['notifications'], ['id', 'title', 'message']),
        }
        
        return JsonResponse(json_results)
    
    # Retornar template para navegação normal
    return render(request, 'core/global_search.html', results)
