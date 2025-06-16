from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from .models import EvolutionRecord
from members.models import Beneficiary


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class EvolutionRecordListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de registros de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_list.html'
    context_object_name = 'records'
    paginate_by = 20
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_queryset(self):
        """Query otimizada com cache e múltiplos filtros"""
        search = self.request.GET.get('search', '')
        signature_filter = self.request.GET.get('signature_required', '')
        
        # Cache key baseada nos filtros
        cache_key = f"evolution_records_{search}_{signature_filter}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = EvolutionRecord.objects.select_related(
                'beneficiary', 'author'
            )
            
            if search:
                queryset = queryset.filter(
                    Q(beneficiary__full_name__icontains=search) |
                    Q(content__icontains=search)
                )
            
            if signature_filter:
                if signature_filter == 'required':
                    queryset = queryset.filter(signature_required=True)
                elif signature_filter == 'signed':
                    queryset = queryset.filter(signed_by_beneficiary__isnull=False)
                elif signature_filter == 'pending':
                    queryset = queryset.filter(
                        signature_required=True,
                        signed_by_beneficiary__isnull=True
                    )
            
            queryset = queryset.order_by('-date')
            
            # Cache por tempo curto (5 minutos)
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['SHORT'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['signature_filter'] = self.request.GET.get('signature_required', '')
        return context


class EvolutionRecordDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de um registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_detail.html'
    context_object_name = 'record'
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"evolution_record_{pk}"
        record = cache.get(cache_key)
        
        if record is None:
            record = EvolutionRecord.objects.select_related(
                'beneficiary', 'author'
            ).get(pk=pk)
            cache.set(cache_key, record, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return record


class EvolutionRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar novo registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['beneficiary', 'date', 'description', 'signature_required']
    success_url = reverse_lazy('evolution:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_form(self, form_class=None):
        """Otimizar queryset das beneficiárias no formulário"""
        form = super().get_form(form_class)
        if 'beneficiary' in form.fields:
            form.fields['beneficiary'].queryset = Beneficiary.objects.order_by('full_name')
        return form
    
    def get_initial(self):
        initial = super().get_initial()
        # Se beneficiário foi passado na URL (com cache)
        beneficiary_id = self.request.GET.get('beneficiary')
        if beneficiary_id:
            try:
                cache_key = f"beneficiary_{beneficiary_id}"
                beneficiary = cache.get(cache_key)
                if beneficiary is None:
                    beneficiary = Beneficiary.objects.get(pk=beneficiary_id)
                    cache.set(cache_key, beneficiary, settings.CACHE_TIMEOUT['SHORT'])
                
                initial['beneficiary'] = beneficiary
            except Beneficiary.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Invalidar caches relacionados
        cache_keys = [
            f"evolution_records__{signature_filter}"
            for signature_filter in ['', 'required', 'signed', 'pending']
        ]
        cache.delete_many(cache_keys)
        
        messages.success(self.request, f'Registro de evolução para {form.instance.beneficiary.full_name} criado com sucesso!')
        return response
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Registro de evolução para {form.instance.beneficiary.full_name} criado com sucesso!')
        return response


class EvolutionRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['date', 'description', 'signature_required', 'signed_by_beneficiary']
    success_url = reverse_lazy('evolution:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"evolution_record_{pk}"
        record = cache.get(cache_key)
        
        if record is None:
            record = EvolutionRecord.objects.select_related(
                'beneficiary', 'author'
            ).get(pk=pk)
            cache.set(cache_key, record, settings.CACHE_TIMEOUT['MEDIUM'])
        
        return record
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Invalidar caches
        cache.delete(f"evolution_record_{self.object.pk}")
        cache_keys = [
            f"evolution_records__{signature_filter}"
            for signature_filter in ['', 'required', 'signed', 'pending']
        ]
        cache.delete_many(cache_keys)
        
        messages.success(self.request, f'Registro de evolução para {form.instance.beneficiary.full_name} atualizado com sucesso!')
        return response


class EvolutionRecordDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Excluir registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_confirm_delete.html'
    success_url = reverse_lazy('evolution:list')
    
    def test_func(self):
        return is_technician(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Override delete para adicionar log e invalidar cache"""
        self.object = self.get_object()
        
        # Log da atividade
        from users.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            description=f'Excluiu registro de evolução de {self.object.beneficiary.full_name}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Invalidar caches
        cache.delete(f"evolution_record_{self.object.pk}")
        cache_keys = [
            f"evolution_records__{signature_filter}"
            for signature_filter in ['', 'required', 'signed', 'pending']
        ]
        cache.delete_many(cache_keys)
        
        success_url = self.get_success_url()
        self.object.delete()
        
        messages.success(request, f'Registro de evolução de {self.object.beneficiary.full_name} excluído com sucesso!')
        return redirect(success_url)
