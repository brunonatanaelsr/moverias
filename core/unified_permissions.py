"""
Sistema de permissões unificado para Move Marias
"""
from django.contrib.auth.models import Group
from django.core.cache import cache
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    if not user.is_authenticated:
        return False
    
    # Cache da verificação por 5 minutos
    cache_key = f"user_is_technician_{user.id}"
    result = cache.get(cache_key)
    
    if result is None:
        result = user.groups.filter(name='Tecnica').exists() or user.is_superuser
        cache.set(cache_key, result, 300)
    
    return result


def is_coordinator(user):
    """Verifica se o usuário pertence ao grupo Coordenador"""
    if not user.is_authenticated:
        return False
    
    # Cache da verificação por 5 minutos
    cache_key = f"user_is_coordinator_{user.id}"
    result = cache.get(cache_key)
    
    if result is None:
        result = (
            user.groups.filter(name__in=['Coordenador', 'Tecnica']).exists() or
            user.is_superuser or
            getattr(user, 'role', None) in ['admin', 'coordenador']
        )
        cache.set(cache_key, result, 300)
    
    return result


def is_admin(user):
    """Verifica se o usuário é administrador"""
    if not user.is_authenticated:
        return False
    
    cache_key = f"user_is_admin_{user.id}"
    result = cache.get(cache_key)
    
    if result is None:
        result = (
            user.is_superuser or
            user.is_staff or
            getattr(user, 'role', None) == 'admin'
        )
        cache.set(cache_key, result, 300)
    
    return result


def has_module_permission(user, module_name):
    """Verifica se o usuário tem permissão para acessar um módulo específico"""
    if not user.is_authenticated:
        return False
    
    # Admins e coordenadores têm acesso a tudo
    if is_admin(user) or is_coordinator(user):
        return True
    
    # Técnicas têm acesso a módulos específicos
    if is_technician(user):
        allowed_modules = [
            'members', 'workshops', 'certificates', 'social', 
            'evolution', 'coaching', 'projects'
        ]
        return module_name in allowed_modules
    
    return False


def requires_technician(view_func):
    """Decorator para views que requerem permissão de técnica"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_technician(request.user):
            messages.error(request, 'Acesso negado. Você precisa ser técnica para acessar esta página.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def requires_coordinator(view_func):
    """Decorator para views que requerem permissão de coordenador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_coordinator(request.user):
            messages.error(request, 'Acesso negado. Você precisa ser coordenador para acessar esta página.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def requires_admin(view_func):
    """Decorator para views que requerem permissão de administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'Acesso negado. Você precisa ser administrador para acessar esta página.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


class TechnicianRequiredMixin:
    """Mixin para CBVs que requerem permissão de técnica"""
    def test_func(self):
        return is_technician(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Acesso negado. Você precisa ser técnica para acessar esta página.')
        return redirect('dashboard:home')


class CoordinatorRequiredMixin:
    """Mixin para CBVs que requerem permissão de coordenador"""
    def test_func(self):
        return is_coordinator(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Acesso negado. Você precisa ser coordenador para acessar esta página.')
        return redirect('dashboard:home')


class AdminRequiredMixin:
    """Mixin para CBVs que requerem permissão de administrador"""
    def test_func(self):
        return is_admin(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Acesso negado. Você precisa ser administrador para acessar esta página.')
        return redirect('dashboard:home')


def clear_user_permissions_cache(user_id):
    """Limpa o cache de permissões de um usuário"""
    cache_keys = [
        f"user_is_technician_{user_id}",
        f"user_is_coordinator_{user_id}",
        f"user_is_admin_{user_id}",
    ]
    cache.delete_many(cache_keys)


def get_user_permissions(user):
    """Retorna um dicionário com todas as permissões do usuário"""
    return {
        'is_technician': is_technician(user),
        'is_coordinator': is_coordinator(user),
        'is_admin': is_admin(user),
        'modules': {
            'members': has_module_permission(user, 'members'),
            'workshops': has_module_permission(user, 'workshops'),
            'certificates': has_module_permission(user, 'certificates'),
            'social': has_module_permission(user, 'social'),
            'evolution': has_module_permission(user, 'evolution'),
            'coaching': has_module_permission(user, 'coaching'),
            'projects': has_module_permission(user, 'projects'),
            'users': has_module_permission(user, 'users'),
            'notifications': has_module_permission(user, 'notifications'),
            'hr': has_module_permission(user, 'hr'),
        }
    }
