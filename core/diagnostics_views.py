from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.urls import get_resolver
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from pathlib import Path
import os
import re

def is_technician_or_admin(user):
    """Verificar se o usuário é técnico ou admin"""
    return user.is_superuser or user.groups.filter(name__in=['Técnico', 'Administrador']).exists()

@login_required
@user_passes_test(is_technician_or_admin)
def template_diagnostics(request):
    """View de diagnóstico de templates"""
    
    # 1. Informações do sistema
    system_info = {
        'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
        'debug_mode': settings.DEBUG,
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'template_dirs': settings.TEMPLATES[0]['DIRS'],
        'app_dirs_enabled': settings.TEMPLATES[0]['APP_DIRS'],
    }
    
    # 2. Context processors
    context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']
    cp_status = []
    
    for cp_path in context_processors:
        status = {'path': cp_path, 'working': False, 'error': None}
        try:
            module_path, function_name = cp_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[function_name])
            processor_func = getattr(module, function_name)
            
            # Testar o context processor
            context = processor_func(request)
            status['working'] = True
            status['context_keys'] = list(context.keys()) if context else []
        except Exception as e:
            status['error'] = str(e)
        
        cp_status.append(status)
    
    # 3. Templates escaneados
    templates_scan = scan_all_templates()
    
    # 4. URLs e views
    urls_scan = scan_urls_and_views()
    
    # 5. Permissões do usuário atual
    user_permissions = get_user_diagnostic_permissions(request.user)
    
    # 6. Apps instaladas
    installed_apps = []
    for app_config in apps.get_app_configs():
        app_info = {
            'name': app_config.name,
            'label': app_config.label,
            'path': app_config.path,
            'has_templates': os.path.exists(os.path.join(app_config.path, 'templates')),
            'has_urls': os.path.exists(os.path.join(app_config.path, 'urls.py')),
        }
        installed_apps.append(app_info)
    
    # 7. Estrutura de navegação
    navigation_analysis = analyze_navigation_structure()
    
    context = {
        'system_info': system_info,
        'context_processors': cp_status,
        'templates_scan': templates_scan,
        'urls_scan': urls_scan,
        'user_permissions': user_permissions,
        'installed_apps': installed_apps,
        'navigation_analysis': navigation_analysis,
    }
    
    return render(request, 'core/diagnostics/template_diagnostics.html', context)

def scan_all_templates():
    """Escanear todos os templates do projeto"""
    templates_found = {
        'main_templates': [],
        'app_templates': {},
        'total_count': 0,
        'issues': []
    }
    
    # Templates principais
    main_template_dir = Path(settings.BASE_DIR) / 'templates'
    if main_template_dir.exists():
        templates_found['main_templates'] = scan_directory_templates(main_template_dir)
        templates_found['total_count'] += len(templates_found['main_templates'])
    
    # Templates de apps
    for app_config in apps.get_app_configs():
        app_templates_dir = Path(app_config.path) / 'templates'
        if app_templates_dir.exists():
            app_templates = scan_directory_templates(app_templates_dir)
            templates_found['app_templates'][app_config.name] = app_templates
            templates_found['total_count'] += len(app_templates)
    
    return templates_found

def scan_directory_templates(directory):
    """Escanear templates em um diretório"""
    templates = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                
                template_info = {
                    'path': rel_path,
                    'full_path': full_path,
                    'size': os.path.getsize(full_path),
                    'issues': check_template_issues(full_path)
                }
                templates.append(template_info)
    return templates

def check_template_issues(template_path):
    """Verificar problemas em um template"""
    issues = []
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Verificar extends
            extends_match = re.search(r'{%\s*extends\s+["\']([^"\']+)["\']', content)
            if extends_match:
                parent_template = extends_match.group(1)
                try:
                    get_template(parent_template)
                except TemplateDoesNotExist:
                    issues.append(f'Template pai não encontrado: {parent_template}')
            
            # Verificar blocks
            blocks_defined = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
            blocks_ended = re.findall(r'{%\s*endblock\s*(?:\w+)?\s*%}', content)
            
            if len(blocks_defined) != len(blocks_ended):
                issues.append('Número de blocks não confere com endblocks')
            
            # Verificar includes
            includes = re.findall(r'{%\s*include\s+["\']([^"\']+)["\']', content)
            for include_template in includes:
                try:
                    get_template(include_template)
                except TemplateDoesNotExist:
                    issues.append(f'Template incluído não encontrado: {include_template}')
    
    except Exception as e:
        issues.append(f'Erro ao ler template: {str(e)}')
    
    return issues

def scan_urls_and_views():
    """Escanear URLs e views"""
    resolver = get_resolver()
    url_patterns = extract_url_patterns(resolver)
    
    views_analysis = {
        'total_patterns': len(url_patterns),
        'with_templates': 0,
        'without_templates': 0,
        'issues': []
    }
    
    for pattern in url_patterns[:50]:  # Limitar para evitar timeout
        if hasattr(pattern, 'callback'):
            view_name = getattr(pattern.callback, '__name__', str(pattern.callback))
            
            # Tentar adivinhar template
            template_name = guess_template_name(pattern, view_name)
            
            if template_name:
                try:
                    get_template(template_name)
                    views_analysis['with_templates'] += 1
                except TemplateDoesNotExist:
                    views_analysis['without_templates'] += 1
                    views_analysis['issues'].append({
                        'url': str(pattern.pattern),
                        'view': view_name,
                        'template': template_name,
                        'issue': 'Template não encontrado'
                    })
    
    return views_analysis

def extract_url_patterns(resolver, namespace=''):
    """Extrair padrões de URL"""
    patterns = []
    
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            sub_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
            patterns.extend(extract_url_patterns(pattern, sub_namespace))
        else:
            patterns.append(pattern)
    
    return patterns

def guess_template_name(pattern, view_name):
    """Adivinhar nome do template"""
    url_parts = str(pattern.pattern).strip('^$').split('/')
    app_name = url_parts[0] if url_parts and url_parts[0] else 'core'
    
    clean_parts = [part for part in url_parts if part and not any(c in part for c in ['(', ')', '?', '*', '+', '\\'])]
    
    if len(clean_parts) >= 2:
        return f"{app_name}/{clean_parts[1]}.html"
    elif len(clean_parts) == 1:
        return f"{app_name}/index.html"
    
    return None

def get_user_diagnostic_permissions(user):
    """Obter informações de permissões do usuário para diagnóstico"""
    permissions_info = {
        'is_authenticated': user.is_authenticated,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'groups': list(user.groups.values_list('name', flat=True)),
        'permissions': [],
        'modules_access': {}
    }
    
    if user.is_authenticated:
        # Permissões específicas
        user_permissions = user.get_all_permissions()
        permissions_info['permissions'] = list(user_permissions)
        
        # Tentar obter permissões unificadas
        try:
            from core.unified_permissions import get_user_permissions
            unified_perms = get_user_permissions(user)
            permissions_info['unified_permissions'] = unified_perms
        except ImportError:
            permissions_info['unified_permissions'] = None
    
    return permissions_info

def analyze_navigation_structure():
    """Analisar estrutura de navegação"""
    navigation_info = {
        'template_exists': False,
        'valid_urls': [],
        'invalid_urls': [],
        'issues': []
    }
    
    navigation_template = Path(settings.BASE_DIR) / 'templates/layouts/includes/navigation.html'
    
    if navigation_template.exists():
        navigation_info['template_exists'] = True
        
        try:
            with open(navigation_template, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extrair URLs
                url_patterns = re.findall(r'{%\s*url\s+["\']([^"\']+)["\']', content)
                
                for url_name in url_patterns:
                    try:
                        from django.urls import reverse
                        reverse(url_name)
                        navigation_info['valid_urls'].append(url_name)
                    except Exception as e:
                        navigation_info['invalid_urls'].append({
                            'url_name': url_name,
                            'error': str(e)
                        })
        
        except Exception as e:
            navigation_info['issues'].append(f'Erro ao ler template de navegação: {e}')
    else:
        navigation_info['issues'].append('Template de navegação não encontrado')
    
    return navigation_info
