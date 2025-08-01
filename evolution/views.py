from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from core.unified_permissions import (
    
    get_user_permissions,
    requires_technician,
    requires_admin,
    TechnicianRequiredMixin,
    AdminRequiredMixin
)
from .models import EvolutionRecord
from members.models import Beneficiary
from django.http import HttpResponse
import io
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.views import View

class EvolutionExportExcelView(LoginRequiredMixin, TechnicianRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        queryset = EvolutionRecord.objects.select_related('beneficiary', 'author').order_by('-date')
        wb = Workbook()
        ws = wb.active
        ws.title = "Registros de Evolução"
        ws.append(["Beneficiária", "Data", "Descrição", "Autor", "Assinatura Requerida", "Assinado"])
        for record in queryset:
            ws.append([
                str(record.beneficiary),
                record.date.strftime('%d/%m/%Y'),
                record.description,
                str(record.author),
                "Sim" if record.signature_required else "Não",
                "Sim" if record.signed_by_beneficiary else "Não"
            ])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="evolucao.xlsx"'
        wb.save(response)
        return response

class EvolutionExportPDFView(LoginRequiredMixin, TechnicianRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        queryset = EvolutionRecord.objects.select_related('beneficiary', 'author').order_by('-date')
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Registros de Evolução")
        y -= 40
        p.setFont("Helvetica", 10)
        for record in queryset:
            if y < 80:
                p.showPage()
                y = height - 50
            p.drawString(50, y, f"Beneficiária: {record.beneficiary} | Data: {record.date.strftime('%d/%m/%Y')} | Autor: {record.author}")
            y -= 15
            p.drawString(60, y, f"Descrição: {record.description[:120]}{'...' if len(record.description) > 120 else ''}")
            y -= 15
            p.drawString(60, y, f"Assinatura Requerida: {'Sim' if record.signature_required else 'Não'} | Assinado: {'Sim' if record.signed_by_beneficiary else 'Não'}")
            y -= 25
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="evolucao.pdf"'
        return response


def is_technician(user):
    """Verifica se o usuário pertence ao grupo Técnica"""
    return user.groups.filter(name='Tecnica').exists() or user.is_superuser


class EvolutionRecordListView(LoginRequiredMixin, TechnicianRequiredMixin, ListView):
    """Lista de registros de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_list.html'
    context_object_name = 'records'
    paginate_by = 20
    
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
        context['user_permissions'] = get_user_permissions(self.request.user)
        # Dados para gráficos: evolução por mês e beneficiária
        from django.db.models.functions import TruncMonth
        from django.db.models import Count
        records_by_month = (
            EvolutionRecord.objects
            .values('beneficiary__full_name')
            .annotate(month=TruncMonth('date'))
            .annotate(total=Count('id'))
            .order_by('month')
        )
        context['records_by_month'] = list(records_by_month)
        return context


class EvolutionRecordDetailView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
    """Detalhes de um registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_detail.html'
    context_object_name = 'record'
    
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


class EvolutionRecordCreateView(CreateConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, CreateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo evolução?"
    confirmation_entity = "evolução"  # "Criar novo registro de evolução"""
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Auditoria: log de criação
        from core.audit import log_user_action
        log_user_action(
            user=self.request.user,
            action='CREATE',
            request=self.request,
            description=f'Criou registro de evolução para {form.instance.beneficiary}',
            content_object=form.instance,
            old_values=None,
            new_values={field: getattr(form.instance, field) for field in form.instance._meta.fields}
        )
        messages.success(self.request, f'Registro de evolução criado com sucesso para {form.instance.beneficiary}')
        return response
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['beneficiary', 'date', 'description', 'signature_required', 'workshops', 'projects', 'anamneses', 'evidence']
    success_url = reverse_lazy('evolution:list')
    
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


class EvolutionRecordUpdateView(EditConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste evolução?"
    confirmation_entity = "evolução"
    
    def form_valid(self, form):
        old_values = {field.name: getattr(self.get_object(), field.name) for field in self.model._meta.fields}
        response = super().form_valid(form)
        # Auditoria: log de edição
        from core.audit import log_user_action
        log_user_action(
            user=self.request.user,
            action='UPDATE',
            request=self.request,
            description=f'Editou registro de evolução de {self.object.beneficiary}',
            content_object=self.object,
            old_values=old_values,
            new_values={field.name: getattr(self.object, field.name) for field in self.model._meta.fields}
        )
        # ...existing code...
    """Editar registro de evolução"""
    
    model = EvolutionRecord
    template_name = 'evolution/evolution_form.html'
    fields = ['date', 'description', 'signature_required', 'signed_by_beneficiary', 'workshops', 'projects', 'anamneses', 'evidence']
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


class EvolutionRecordDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir este evolução?"
    confirmation_entity = "evolução"
    dangerous_operation = True
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Auditoria: log de exclusão
        from core.audit import log_user_action
        old_values = {field.name: getattr(self.object, field.name) for field in self.model._meta.fields}
        log_user_action(
            user=request.user,
            action='DELETE',
            request=request,
            description=f'Excluiu registro de evolução de {self.object.beneficiary}',
            content_object=self.object,
            old_values=old_values,
            new_values=None
        )
        # ...existing code...
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
