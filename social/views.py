# Copilot: CreateView + UpdateView SocialAnamnesis.
# Permissão: user em grupo "Tecnica".
# Ao finalizar wizard, marcar locked=True.

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Prefetch
from formtools.wizard.views import SessionWizardView
from .models import SocialAnamnesis
from .forms import (
    SocialAnamnesisStep1Form, 
    SocialAnamnesisStep2Form, 
    SocialAnamnesisStep3Form,
    SocialAnamnesisUpdateForm
)
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class SocialAnamnesisWizard(LoginRequiredMixin, UserPassesTestMixin, SessionWizardView):
    """Wizard de 3 etapas para criar anamnese social"""
    
    form_list = [
        ('step1', SocialAnamnesisStep1Form),
        ('step2', SocialAnamnesisStep2Form),
        ('step3', SocialAnamnesisStep3Form),
    ]
    
    template_name = 'social/anamnesis_wizard.html'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'step1':
            # Passar dados do beneficiário se especificado na URL (com otimização)
            beneficiary_id = self.request.GET.get('beneficiary')
            if beneficiary_id:
                try:
                    # Cache da beneficiária
                    cache_key = f"beneficiary_{beneficiary_id}"
                    beneficiary = cache.get(cache_key)
                    if beneficiary is None:
                        beneficiary = Beneficiary.objects.get(pk=beneficiary_id)
                        cache.set(cache_key, beneficiary, settings.CACHE_TIMEOUT['SHORT'])
                    
                    kwargs['initial'] = {'beneficiary': beneficiary}
                except Beneficiary.DoesNotExist:
                    pass
        return kwargs
    
    def done(self, form_list, **kwargs):
        """Processar dados de todos os formulários"""
        # Combinar dados de todos os steps
        form_data = {}
        for form in form_list:
            form_data.update(form.cleaned_data)
        
        # Criar a anamnese
        anamnesis = SocialAnamnesis.objects.create(
            beneficiary=form_data['beneficiary'],
            family_composition=form_data['family_composition'],
            income=form_data['income'],
            vulnerabilities=form_data['vulnerabilities'],
            substance_use=form_data.get('substance_use', ''),
            observations=form_data.get('observations', ''),
            signed_by_technician=self.request.user,
            signed_by_beneficiary=form_data.get('signed_by_beneficiary', False),
            locked=True  # Bloquear após finalização
        )
        
        messages.success(self.request, f'Anamnese social de {anamnesis.beneficiary.full_name} criada com sucesso!')
        return redirect('social:detail', pk=anamnesis.pk)


class SocialAnamnesisUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar anamnese social existente"""
    
    model = SocialAnamnesis
    form_class = SocialAnamnesisUpdateForm
    template_name = 'social/anamnesis_form.html'
    success_url = reverse_lazy('social:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"social_anamnesis_{pk}"
        anamnesis = cache.get(cache_key)
        
        if anamnesis is None:
            anamnesis = SocialAnamnesis.objects.select_related(
                'beneficiary', 'signed_by_technician'
            ).get(pk=pk)
            cache.set(cache_key, anamnesis, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return anamnesis
    
    def form_valid(self, form):
        # Definir usuário atual para validação no modelo
        form.instance._current_user = self.request.user
        
        try:
            response = super().form_valid(form)
            
            # Invalidar cache
            cache.delete(f"social_anamnesis_{self.object.pk}")
            
            messages.success(self.request, 'Anamnese social atualizada com sucesso!')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao salvar: {str(e)}')
            return self.form_invalid(form)


class SocialAnamnesisDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Visualizar anamnese social"""
    
    model = SocialAnamnesis
    template_name = 'social/anamnesis_detail.html'
    context_object_name = 'anamnesis'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"social_anamnesis_{pk}"
        anamnesis = cache.get(cache_key)
        
        if anamnesis is None:
            anamnesis = SocialAnamnesis.objects.select_related(
                'beneficiary', 'signed_by_technician'
            ).get(pk=pk)
            cache.set(cache_key, anamnesis, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return anamnesis


class SocialAnamnesisListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Listar anamneses sociais"""
    
    model = SocialAnamnesis
    template_name = 'social/anamnesis_list.html'
    context_object_name = 'anamnesis_list'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Query otimizada com cache e select_related"""
        search = self.request.GET.get('search', '')
        locked_filter = self.request.GET.get('locked', '')
        
        # Cache key baseada nos filtros
        cache_key = f"social_anamnesis_list_{search}_{locked_filter}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = SocialAnamnesis.objects.select_related(
                'beneficiary', 'signed_by_technician'
            )
            
            if search:
                queryset = queryset.filter(
                    Q(beneficiary__full_name__icontains=search) |
                    Q(beneficiary__cpf__icontains=search)
                )
            
            if locked_filter:
                queryset = queryset.filter(locked=locked_filter == 'true')
            
            queryset = queryset.order_by('-date')
            
            # Cache por tempo curto (5 minutos)
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['SHORT'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['locked_filter'] = self.request.GET.get('locked', '')
        return context


@login_required
@user_passes_test(is_technician)
def lock_anamnesis(request, pk):
    """Bloquear/desbloquear anamnese para edição"""
    anamnesis = get_object_or_404(
        SocialAnamnesis.objects.select_related('beneficiary'), 
        pk=pk
    )
    
    if request.method == 'POST':
        if request.user.is_superuser:
            anamnesis.locked = not anamnesis.locked
            anamnesis.save()
            status = "bloqueada" if anamnesis.locked else "desbloqueada"
            messages.success(request, f'Anamnese {status} com sucesso!')
        else:
            messages.error(request, 'Apenas administradores podem alterar o status de bloqueio.')
    
    return redirect('social:detail', pk=pk)


class SocialAnamnesisDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Excluir anamnese social"""
    
    model = SocialAnamnesis
    template_name = 'social/anamnesis_confirm_delete.html'
    success_url = reverse_lazy('social:list')
    
    def test_func(self):
        return self.request.user.is_superuser  # Apenas superusuários podem excluir
    
    def get_object(self, queryset=None):
        """Verificar se a anamnese pode ser excluída"""
        obj = super().get_object(queryset)
        if obj.locked:
            messages.error(self.request, 'Não é possível excluir uma anamnese bloqueada.')
            return redirect('social:detail', pk=obj.pk)
        return obj
    
    def delete(self, request, *args, **kwargs):
        """Override delete para adicionar log e invalidar cache"""
        self.object = self.get_object()
        
        # Log da atividade
        from users.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            description=f'Excluiu anamnese social de {self.object.beneficiary.full_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Invalidar cache
        cache.delete(f"social_anamnesis_{self.object.pk}")
        cache_keys = [f"social_anamnesis_list_{search}_{locked_filter}" 
                     for search in ['', 'test'] for locked_filter in ['', 'true', 'false']]
        cache.delete_many(cache_keys)
        
        success_url = self.get_success_url()
        self.object.delete()
        
        messages.success(request, f'Anamnese social de {self.object.beneficiary.full_name} excluída com sucesso!')
        return redirect(success_url)
