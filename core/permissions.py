"""
Centralized permission functions for Move Marias system.
This module contains all permission checking functions to avoid code duplication.
"""

from django.contrib.auth.models import Group


def is_technician(user):
    """
    Verifica se o usuário pertence ao grupo Técnica ou é superuser.
    
    Args:
        user: Django User instance
    
    Returns:
        bool: True se o usuário tem permissões de técnico
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


def is_coordinator(user):
    """
    Verifica se o usuário é coordenador.
    
    Args:
        user: Django User instance
    
    Returns:
        bool: True se o usuário é coordenador
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.groups.filter(name='Coordenação').exists() or user.is_superuser


def is_admin(user):
    """
    Verifica se o usuário é administrador.
    
    Args:
        user: Django User instance
    
    Returns:
        bool: True se o usuário é admin
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.is_staff or user.is_superuser


def can_edit_beneficiary(user, beneficiary=None):
    """
    Verifica se o usuário pode editar dados de beneficiárias.
    
    Args:
        user: Django User instance
        beneficiary: Beneficiary instance (opcional)
    
    Returns:
        bool: True se pode editar
    """
    return is_technician(user) or is_coordinator(user)


def can_view_reports(user):
    """
    Verifica se o usuário pode visualizar relatórios.
    
    Args:
        user: Django User instance
    
    Returns:
        bool: True se pode ver relatórios
    """
    return is_technician(user) or is_coordinator(user)


def ensure_groups_exist():
    """
    Garante que os grupos necessários existam no sistema.
    """
    required_groups = ['Tecnica', 'Coordenação', 'Voluntários']
    
    for group_name in required_groups:
        Group.objects.get_or_create(name=group_name)
