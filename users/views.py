from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from .models import CustomUser, UserProfile, UserActivity, SystemRole
from .forms import CustomUserForm, UserProfileForm, SystemRoleForm

User = get_user_model()


def is_admin_or_staff(user):
    """Verifica se o usuário é admin ou staff"""
    return user.is_staff or user.is_superuser or user.role in ['admin', 'coordenador']


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def get_queryset(self):
        queryset = CustomUser.objects.select_related('profile').annotate(
            activity_count=Count('activities')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search)
            )
        
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset.order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = CustomUser.ROLE_CHOICES
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(is_active=True).count()
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'

    def test_func(self):
        return is_admin_or_staff(self.request.user) or self.get_object() == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        context['recent_activities'] = user_obj.activities.order_by('-timestamp')[:10]
        context['user_groups'] = user_obj.groups.all()
        context['user_permissions'] = user_obj.user_permissions.all()
        # Anamneses sociais onde o usuário é beneficiária OU técnica responsável
        from social.models import SocialAnamnesis
        context['social_anamneses'] = SocialAnamnesis.objects.filter(
            Q(beneficiary=user_obj) | Q(signed_by_technician=user_obj)
        ).order_by('-date')
        return context


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def form_valid(self, form):
        user = form.save()
        # Criar perfil automaticamente
        UserProfile.objects.create(user=user)
        
        # Log da atividade
        UserActivity.objects.create(
            user=self.request.user,
            action='create',
            description=f'Criou o usuário {user.full_name} ({user.email})',
            ip_address=self.get_client_ip()
        )
        
        messages.success(self.request, f'Usuário {user.full_name} criado com sucesso!')
        return super().form_valid(form)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        return is_admin_or_staff(self.request.user) or self.get_object() == self.request.user

    def form_valid(self, form):
        user = form.save()
        
        # Log da atividade
        UserActivity.objects.create(
            user=self.request.user,
            action='update',
            description=f'Atualizou o usuário {user.full_name} ({user.email})',
            ip_address=self.get_client_ip()
        )
        
        messages.success(self.request, f'Usuário {user.full_name} atualizado com sucesso!')
        return super().form_valid(form)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


@login_required
@user_passes_test(is_admin_or_staff)
def user_toggle_status(request, pk):
    """Ativar/desativar usuário"""
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = 'ativado' if user.is_active else 'desativado'
        
        # Log da atividade
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f'Usuario {user.full_name} foi {status}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f'Usuário {user.full_name} foi {status} com sucesso!')
        
        if request.headers.get('HX-Request'):
            return JsonResponse({'success': True, 'status': status})
    
    return redirect('users:user_list')


class SystemRoleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SystemRole
    template_name = 'users/role_list.html'
    context_object_name = 'roles'

    def test_func(self):
        return is_admin_or_staff(self.request.user)


class SystemRoleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SystemRole
    form_class = SystemRoleForm
    template_name = 'users/role_form.html'
    success_url = reverse_lazy('users:role_list')

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Função criada com sucesso!')
        return super().form_valid(form)


class SystemRoleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SystemRole
    form_class = SystemRoleForm
    template_name = 'users/role_form.html'
    success_url = reverse_lazy('users:role_list')

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Função atualizada com sucesso!')
        return super().form_valid(form)


class SystemRoleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SystemRole
    success_url = reverse_lazy('users:role_list')

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Função excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class UserActivityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserActivity
    template_name = 'users/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 50

    def test_func(self):
        return is_admin_or_staff(self.request.user)

    def get_queryset(self):
        queryset = UserActivity.objects.select_related('user')
        
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = CustomUser.objects.filter(is_active=True).order_by('full_name')
        
        # Calcular número de usuários únicos nas atividades
        activities = context['activities']
        if activities:
            unique_users = activities.values_list('user', flat=True).distinct()
            context['unique_users_count'] = len(set(unique_users))
        else:
            context['unique_users_count'] = 0
            
        return context


@login_required
def profile_view(request):
    """Visualizar/editar perfil próprio"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST, instance=user, is_self_edit=True)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Log da atividade
            UserActivity.objects.create(
                user=user,
                action='update',
                description='Atualizou o próprio perfil',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('users:profile')
    else:
        user_form = CustomUserForm(instance=user, is_self_edit=True)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'recent_activities': user.activities.order_by('-timestamp')[:5],
    }
    return render(request, 'users/profile.html', context)


def get_client_ip(request):
    """Obter IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
