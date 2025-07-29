"""
Decoradores para adicionar confirmações em operações CRUD
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
import json


def requires_confirmation(
    message=None, 
    warning=None, 
    entity_name=None,
    success_message=None,
    redirect_url=None,
    template_name=None
):
    """
    Decorator que adiciona confirmação para operações CRUD
    
    Args:
        message: Mensagem de confirmação personalizada
        warning: Aviso adicional sobre a operação
        entity_name: Nome da entidade (beneficiária, projeto, etc.)
        success_message: Mensagem de sucesso após confirmação
        redirect_url: URL para redirecionamento após sucesso
        template_name: Template para renderizar confirmação (se não for AJAX)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Se não for POST/DELETE, executar normalmente
            if request.method not in ['POST', 'DELETE']:
                return view_func(request, *args, **kwargs)
            
            # Verificar se já foi confirmado
            if request.POST.get('confirmed') == 'true' or request.GET.get('confirmed') == 'true':
                try:
                    result = view_func(request, *args, **kwargs)
                    if success_message:
                        messages.success(request, success_message)
                    return result
                except Exception as e:
                    messages.error(request, f"Erro ao executar operação: {str(e)}")
                    if redirect_url:
                        return redirect(redirect_url)
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Se for AJAX, retornar dados de confirmação
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                confirmation_data = {
                    'requires_confirmation': True,
                    'message': message or f"Tem certeza que deseja realizar esta operação?",
                    'warning': warning,
                    'entity_name': entity_name,
                    'confirm_url': request.build_absolute_uri(),
                }
                return JsonResponse(confirmation_data)
            
            # Para requisições normais, renderizar página de confirmação
            context = {
                'message': message or f"Tem certeza que deseja realizar esta operação?",
                'warning': warning,
                'entity_name': entity_name,
                'confirm_url': request.build_absolute_uri(),
                'cancel_url': request.META.get('HTTP_REFERER', '/'),
                'form_data': request.POST if request.method == 'POST' else None,
            }
            
            template = template_name or 'core/confirmation.html'
            return render_to_string(template, context, request=request)
        
        return wrapper
    return decorator


def delete_confirmation(entity_name=None, success_url=None):
    """
    Decorator específico para operações de exclusão
    """
    return requires_confirmation(
        message=f"Tem certeza que deseja excluir {entity_name or 'este item'}?",
        warning="Esta ação não pode ser desfeita. Todos os dados relacionados também serão removidos.",
        entity_name=entity_name,
        success_message=f"{entity_name or 'Item'} excluído com sucesso!",
        redirect_url=success_url
    )


def edit_confirmation(entity_name=None):
    """
    Decorator específico para operações de edição
    """
    return requires_confirmation(
        message=f"Confirma as alterações {entity_name or 'neste item'}?",
        entity_name=entity_name,
        success_message=f"{entity_name or 'Item'} atualizado com sucesso!"
    )


def create_confirmation(entity_name=None):
    """
    Decorator específico para operações de criação
    """
    return requires_confirmation(
        message=f"Confirma o cadastro {entity_name or 'deste item'}?",
        entity_name=entity_name,
        success_message=f"{entity_name or 'Item'} cadastrado com sucesso!"
    )


def status_change_confirmation(action="alterar status", entity_name=None):
    """
    Decorator para mudanças de status (ativar/desativar)
    """
    return requires_confirmation(
        message=f"Confirma {action} {entity_name or 'deste item'}?",
        entity_name=entity_name,
        success_message=f"Status {entity_name or 'do item'} alterado com sucesso!"
    )


class ConfirmationMixin:
    """
    Mixin para Class-Based Views que adiciona confirmação automática
    """
    confirmation_message = None
    confirmation_warning = None
    entity_name = None
    success_message = None
    requires_confirmation_for = ['post', 'delete', 'put', 'patch']
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar se método requer confirmação
        if request.method.lower() in [method.lower() for method in self.requires_confirmation_for]:
            # Se já foi confirmado, proceder normalmente
            if request.POST.get('confirmed') == 'true' or request.GET.get('confirmed') == 'true':
                try:
                    result = super().dispatch(request, *args, **kwargs)
                    if self.success_message:
                        messages.success(request, self.success_message)
                    return result
                except Exception as e:
                    messages.error(request, f"Erro ao executar operação: {str(e)}")
                    return self.handle_error(e)
            
            # Mostrar confirmação
            return self.show_confirmation(request, *args, **kwargs)
        
        return super().dispatch(request, *args, **kwargs)
    
    def show_confirmation(self, request, *args, **kwargs):
        """Mostra tela/modal de confirmação"""
        context = self.get_confirmation_context(request, *args, **kwargs)
        
        # Se for AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'requires_confirmation': True,
                **context
            })
        
        # Renderizar template de confirmação
        return self.render_confirmation(request, context)
    
    def get_confirmation_context(self, request, *args, **kwargs):
        """Contexto para confirmação"""
        return {
            'message': self.get_confirmation_message(request, *args, **kwargs),
            'warning': self.get_confirmation_warning(request, *args, **kwargs),
            'entity_name': self.get_entity_name(request, *args, **kwargs),
            'confirm_url': request.build_absolute_uri(),
            'cancel_url': self.get_cancel_url(request, *args, **kwargs),
        }
    
    def get_confirmation_message(self, request, *args, **kwargs):
        if self.confirmation_message:
            return self.confirmation_message
        entity = self.get_entity_name(request, *args, **kwargs)
        action = self.get_action_name(request)
        return f"Confirma {action} {entity}?"
    
    def get_confirmation_warning(self, request, *args, **kwargs):
        return self.confirmation_warning
    
    def get_entity_name(self, request, *args, **kwargs):
        return self.entity_name or "este item"
    
    def get_action_name(self, request):
        method = request.method.lower()
        actions = {
            'post': 'o cadastro de',
            'put': 'a edição de', 
            'patch': 'a alteração de',
            'delete': 'a exclusão de'
        }
        return actions.get(method, 'a operação com')
    
    def get_cancel_url(self, request, *args, **kwargs):
        return request.META.get('HTTP_REFERER', '/')
    
    def render_confirmation(self, request, context):
        """Renderiza template de confirmação"""
        template_name = getattr(self, 'confirmation_template', 'core/confirmation.html')
        return render_to_string(template_name, context, request=request)
    
    def handle_error(self, exception):
        """Lida com erros durante execução"""
        return redirect(self.get_success_url() if hasattr(self, 'get_success_url') else '/')


# Mixins específicos para diferentes tipos de operação
class DeleteConfirmationMixin(ConfirmationMixin):
    """Mixin específico para exclusões"""
    requires_confirmation_for = ['post', 'delete']
    confirmation_warning = "Esta ação não pode ser desfeita. Todos os dados relacionados também serão removidos."
    
    def get_confirmation_message(self, request, *args, **kwargs):
        entity = self.get_entity_name(request, *args, **kwargs)
        return f"Tem certeza que deseja excluir {entity}?"


class EditConfirmationMixin(ConfirmationMixin):
    """Mixin específico para edições"""
    requires_confirmation_for = ['post', 'put', 'patch']
    
    def get_confirmation_message(self, request, *args, **kwargs):
        entity = self.get_entity_name(request, *args, **kwargs)
        return f"Confirma as alterações em {entity}?"


class CreateConfirmationMixin(ConfirmationMixin):
    """Mixin específico para criações"""
    requires_confirmation_for = ['post']
    
    def get_confirmation_message(self, request, *args, **kwargs):
        entity = self.get_entity_name(request, *args, **kwargs)
        return f"Confirma o cadastro de {entity}?"
