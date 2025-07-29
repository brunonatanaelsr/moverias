from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django_ratelimit.decorators import ratelimit  # ENHANCED: Rate limiting
from core.permissions import is_coordinator, is_technician
from core.cache_utils import cache_view
from core.logging_config import get_security_logger  # ENHANCED: Security logging
from core.unified_permissions import (
    get_user_permissions,
    is_technician,
    is_coordinator,
    is_admin,
    TechnicianRequiredMixin,
    CoordinatorRequiredMixin,
    AdminRequiredMixin,
    requires_technician,
    requires_coordinator,
    requires_admin
)
from .models import CustomUser, UserProfile, UserActivity, SystemRole
from .forms import UserCreateForm, UserUpdateForm, UserProfileForm, PermissionForm
import json

def is_admin_or_staff(user):
    """Verifica se o usuário é admin ou staff"""
    return user.is_staff or user.is_superuser or user.role in ['admin', 'coordenador']


@method_decorator(login_required, name='dispatch')
class ProfileView(UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)


class UserManagementMixin(CoordinatorRequiredMixin):
    """Mixin para verificar se o usuário pode gerenciar outros usuários"""
    pass

@method_decorator(ratelimit(key='user', rate='100/h', method='GET'), name='dispatch')
class UserListView(UserManagementMixin, LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = CustomUser.objects.select_related('profile').prefetch_related('groups', 'user_permissions')
        
        # Filtros
        search = self.request.GET.get('search')
        role = self.request.GET.get('role')
        group = self.request.GET.get('group')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search)
            )
        
        if role:
            queryset = queryset.filter(role=role)
            
        if group:
            queryset = queryset.filter(groups__name=group)
            
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()
        context['roles'] = CustomUser.ROLE_CHOICES
        
        # Estatísticas de usuários
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        inactive_users = CustomUser.objects.filter(is_active=False).count()
        
        context['total_users'] = total_users
        context['active_users'] = active_users
        context['inactive_users'] = inactive_users
        
        # Calcular porcentagens
        if total_users > 0:
            context['active_percentage'] = round((active_users / total_users) * 100, 1)
            context['inactive_percentage'] = round((inactive_users / total_users) * 100, 1)
        else:
            context['active_percentage'] = 0
            context['inactive_percentage'] = 0
        
        # Estatísticas por função
        context['stats_by_role'] = CustomUser.objects.values('role').annotate(count=Count('id'))
        context['user_permissions'] = get_user_permissions(self.request.user)
        
        return context

class UserDetailView(UserManagementMixin, LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Atividades recentes
        context['recent_activities'] = UserActivity.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # Permissões
        context['user_permissions'] = user.get_all_permissions()
        context['group_permissions'] = []
        
        for group in user.groups.all():
            group_perms = group.permissions.all()
            context['group_permissions'].append({
                'group': group,
                'permissions': group_perms
            })
        
        return context

class UserCreateView(CreateConfirmationMixin, UserManagementMixin, LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = UserCreateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user-list')
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo usuário?"
    confirmation_entity = "usuário"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuário {self.object.full_name} criado com sucesso!')
        return response

class UserUpdateView(EditConfirmationMixin, UserManagementMixin, LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'users/user_form.html'
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste usuário?"
    confirmation_entity = "usuário"

    def get_success_url(self):
        return reverse('users:user-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuário {self.object.full_name} atualizado com sucesso!')
        return response

class UserDeleteView(DeleteConfirmationMixin, UserManagementMixin, LoginRequiredMixin, DeleteView):
    
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir este usuário?"
    confirmation_entity = "usuário"
    dangerous_operation = Truemodel = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user-list')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, 'Você não pode excluir sua própria conta!')
            return redirect('users:user-list')
        
        messages.success(request, f'Usuário {user.full_name} excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class PermissionManagementView(UserManagementMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_permissions.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Todas as permissões disponíveis organizadas por app
        all_permissions = Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'codename'
        )
        
        permissions_by_app = {}
        available_apps = set()
        for perm in all_permissions:
            app_label = perm.content_type.app_label
            available_apps.add(app_label)
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        # Permissões do usuário
        user_permissions = user.user_permissions.all()
        user_permissions_ids = list(user_permissions.values_list('id', flat=True))
        
        # Permissões por grupos
        group_permissions_count = 0
        for group in user.groups.all():
            group_permissions_count += group.permissions.count()
        
        # Total de permissões
        total_permissions = len(user_permissions_ids) + group_permissions_count
        
        context.update({
            'permissions_by_app': permissions_by_app,
            'available_apps': sorted(available_apps),
            'user_permissions': user_permissions,
            'user_permissions_ids': user_permissions_ids,
            'all_groups': Group.objects.all(),
            'user_groups': user.groups.all(),
            'group_permissions_count': group_permissions_count,
            'total_permissions': total_permissions,
        })
        
        return context

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        
        try:
            # Atualizar permissões individuais
            permission_ids = request.POST.getlist('user_permissions')
            user.user_permissions.set(permission_ids)
            
            # Atualizar grupos
            group_ids = request.POST.getlist('groups')
            user.groups.set(group_ids)
            
            # Log da atividade
            UserActivity.objects.create(
                user=user,
                performer=request.user,
                action="Permissões atualizadas",
                details=f"Permissões diretas: {len(permission_ids)}, Grupos: {len(group_ids)}"
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Permissões de {user.full_name} atualizadas com sucesso!'
                })
            
            messages.success(request, f'Permissões de {user.full_name} atualizadas com sucesso!')
            return redirect('users:user_permissions', pk=user.pk)
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao atualizar permissões: {str(e)}'
                })
            
            messages.error(request, f'Erro ao atualizar permissões: {str(e)}')
            return redirect('users:user_permissions', pk=user.pk)

@login_required
@user_passes_test(is_coordinator)
def toggle_user_status(request, pk):
    """Toggle user active/inactive status via AJAX"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, pk=pk)
        
        if user == request.user:
            return JsonResponse({'success': False, 'message': 'Você não pode desativar sua própria conta!'})
        
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save()
        
        # Log da atividade
        UserActivity.objects.create(
            user=user,
            performer=request.user,
            action="Status alterado",
            details=f"Status alterado de {'ativo' if old_status else 'inativo'} para {'ativo' if user.is_active else 'inativo'}"
        )
        
        status = 'ativado' if user.is_active else 'desativado'
        return JsonResponse({
            'success': True, 
            'message': f'Usuário {user.full_name} {status} com sucesso!',
            'is_active': user.is_active
        })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
@user_passes_test(is_coordinator)
def user_activity_log(request, pk):
    """View para visualizar log de atividades de um usuário"""
    user = get_object_or_404(CustomUser, pk=pk)
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')
    
    # Filtros
    action_filter = request.GET.get('action')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if action_filter:
        activities = activities.filter(action__icontains=action_filter)
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(timestamp__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        from datetime import datetime
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(timestamp__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/user_activity_log.html', {
        'user_obj': user,
        'page_obj': page_obj,
        'activities': page_obj.object_list,
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
    })

@login_required
@user_passes_test(is_coordinator)
def bulk_user_actions(request):
    """View para ações em lote nos usuários"""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            messages.error(request, 'Nenhum usuário selecionado.')
            return redirect('users:user_list')
        
        users = CustomUser.objects.filter(id__in=user_ids)
        
        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'{users.count()} usuários ativados com sucesso!')
            
        elif action == 'deactivate':
            # Não permitir desativar o próprio usuário
            users = users.exclude(id=request.user.id)
            users.update(is_active=False)
            messages.success(request, f'{users.count()} usuários desativados com sucesso!')
            
        elif action == 'delete':
            # Não permitir excluir o próprio usuário
            users = users.exclude(id=request.user.id)
            count = users.count()
            users.delete()
            messages.success(request, f'{count} usuários excluídos com sucesso!')
            
        elif action == 'add_to_group':
            group_id = request.POST.get('group_id')
            if group_id:
                group = get_object_or_404(Group, id=group_id)
                for user in users:
                    user.groups.add(group)
                messages.success(request, f'{users.count()} usuários adicionados ao grupo {group.name}!')
            else:
                messages.error(request, 'Por favor, selecione um grupo.')
                
        elif action == 'remove_from_group':
            group_id = request.POST.get('group_id')
            if group_id:
                group = get_object_or_404(Group, id=group_id)
                for user in users:
                    user.groups.remove(group)
                messages.success(request, f'{users.count()} usuários removidos do grupo {group.name}!')
            else:
                messages.error(request, 'Por favor, selecione um grupo.')
        
        return redirect('users:user_list')
    
    return redirect('users:user_list')

@login_required
@user_passes_test(is_coordinator)
def user_export(request):
    """Exportar dados de usuários para CSV"""
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="usuarios_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nome Completo', 'Email', 'Usuário', 'Função', 'Status', 
        'Data de Cadastro', 'Último Login', 'Grupos', 'Permissões Diretas'
    ])
    
    for user in CustomUser.objects.all():
        writer.writerow([
            user.id,
            user.full_name,
            user.email,
            user.username,
            user.get_role_display(),
            'Ativo' if user.is_active else 'Inativo',
            user.date_joined.strftime('%d/%m/%Y %H:%M'),
            user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca',
            ', '.join([g.name for g in user.groups.all()]),
            user.user_permissions.count()
        ])
    
    return response

@login_required
@user_passes_test(is_coordinator)
def group_management(request):
    """View para gerenciar grupos de usuários"""
    groups = Group.objects.annotate(user_count=Count('user')).order_by('name')
    
    return render(request, 'users/group_management.html', {
        'groups': groups,
        'permissions': Permission.objects.all().order_by('content_type__app_label', 'codename')
    })

@login_required
@user_passes_test(is_coordinator) 
def create_group(request):
    """Criar novo grupo"""
    if request.method == 'POST':
        name = request.POST.get('name')
        permissions = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'Nome do grupo é obrigatório.')
            return redirect('users:group_management')
        
        group, created = Group.objects.get_or_create(name=name)
        if created:
            group.permissions.set(permissions)
            messages.success(request, f'Grupo {name} criado com sucesso!')
        else:
            messages.error(request, f'Grupo {name} já existe.')
    
    return redirect('users:group_management')

@login_required
@user_passes_test(is_coordinator)
def edit_group(request, pk):
    """Editar grupo"""
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        permissions = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'Nome do grupo é obrigatório.')
            return redirect('users:group_management')
        
        group.name = name
        group.save()
        group.permissions.set(permissions)
        
        messages.success(request, f'Grupo {name} atualizado com sucesso!')
        return redirect('users:group_management')
    
    return render(request, 'users/group_form.html', {
        'group': group,
        'permissions': Permission.objects.all().order_by('content_type__app_label', 'codename')
    })

@login_required
@user_passes_test(is_coordinator)
def delete_group(request, pk):
    """Excluir grupo"""
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'Grupo {group_name} excluído com sucesso!')
        return redirect('users:group_management')
    
    return render(request, 'users/group_confirm_delete.html', {'group': group})

@login_required
@user_passes_test(is_coordinator)
def user_reset_password(request, pk):
    """Reset da senha do usuário"""
    user = get_object_or_404(get_user_model(), pk=pk)
    
    if request.method == 'POST':
        # Gerar nova senha temporária
        import secrets
        import string
        
        # Gerar senha temporária de 12 caracteres
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # Definir a nova senha
        user.set_password(new_password)
        user.save()
        
        # Registrar a ação
        messages.success(request, 
            f'Senha do usuário {user.get_full_name() or user.username} foi resetada com sucesso! '
            f'Nova senha temporária: {new_password}. '
            f'Informe ao usuário para alterar esta senha no primeiro login.'
        )
        
        return redirect('users:user-detail', pk=user.pk)
    
    return render(request, 'users/user_reset_password.html', {'user': user})
