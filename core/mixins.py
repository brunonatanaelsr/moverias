"""
Mixins comuns para o sistema MoveMarias
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone


class AuditMixin:
    """Mixin para auditoria de ações"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_timestamp'] = timezone.now()
        return context
    
    def form_valid(self, form):
        """Adiciona informações de auditoria ao salvar"""
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin que requer que o usuário seja staff"""
    
    def test_func(self):
        return self.request.user.is_staff


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requer que o usuário seja admin"""
    
    def test_func(self):
        return self.request.user.is_superuser


class MessageMixin:
    """Mixin para adicionar mensagens de sucesso/erro"""
    
    success_message = ""
    error_message = ""
    
    def form_valid(self, form):
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.error_message:
            messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class PaginationMixin:
    """Mixin para paginação padrão"""
    
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'paginator' in context:
            context['pagination_range'] = self.get_pagination_range(context['page_obj'])
        return context
    
    def get_pagination_range(self, page_obj):
        """Calcula o range de páginas para exibir"""
        current_page = page_obj.number
        total_pages = page_obj.paginator.num_pages
        
        if total_pages <= 7:
            return range(1, total_pages + 1)
        
        if current_page <= 4:
            return range(1, 8)
        
        if current_page > total_pages - 4:
            return range(total_pages - 6, total_pages + 1)
        
        return range(current_page - 3, current_page + 4)
