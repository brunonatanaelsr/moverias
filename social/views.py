# Copilot: CreateView + UpdateView SocialAnamnesis.
# Permissão: user em grupo "Tecnica".
# Ao finalizar wizard, marcar locked=True.

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Prefetch, Count
from django.http import JsonResponse
from formtools.wizard.views import SessionWizardView
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
from .models import SocialAnamnesis, FamilyMember, IdentifiedVulnerability, VulnerabilityCategory, SocialAnamnesisEvolution
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


class SocialAnamnesisWizard(LoginRequiredMixin, TechnicianRequiredMixin, SessionWizardView):
    """Wizard de 3 etapas para criar anamnese social"""
    
    form_list = [
        ('step1', SocialAnamnesisStep1Form),
        ('step2', SocialAnamnesisStep2Form),
        ('step3', SocialAnamnesisStep3Form),
    ]
    
    template_name = 'social/anamnesis_wizard.html'
    
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
            created_by=self.request.user,
            housing_situation=form_data.get('housing_situation', ''),
            family_income=form_data.get('family_income', 0),
            support_network=form_data.get('support_network', ''),
            observations=form_data.get('observations', ''),
            status='completed'
        )
        
        messages.success(self.request, f'Anamnese social de {anamnesis.beneficiary.full_name} criada com sucesso!')
        return redirect('social:detail', pk=anamnesis.pk)


class SocialAnamnesisUpdateView(EditConfirmationMixin, LoginRequiredMixin, TechnicianRequiredMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste anamnese social?"
    confirmation_entity = "anamnese social""""Editar anamnese social existente"""
    
    model = SocialAnamnesis
    form_class = SocialAnamnesisUpdateForm
    template_name = 'social/anamnesis_form.html'
    success_url = reverse_lazy('social:list')
    
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


class SocialAnamnesisDetailView(LoginRequiredMixin, TechnicianRequiredMixin, DetailView):
    """Visualizar anamnese social"""
    
    model = SocialAnamnesis
    template_name = 'social/anamnesis_detail.html'
    context_object_name = 'anamnesis'
    
    def get_object(self, queryset=None):
        """Otimizar query do objeto"""
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f"social_anamnesis_{pk}"
        anamnesis = cache.get(cache_key)
        
        if anamnesis is None:
            anamnesis = SocialAnamnesis.objects.select_related(
                'beneficiary', 'created_by'
            ).prefetch_related(
                'family_members',
                'vulnerabilities__category',
                'evolutions'
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
        status_filter = self.request.GET.get('status', '')
        
        # Cache key baseada nos filtros
        cache_key = f"social_anamnesis_list_{search}_{status_filter}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = SocialAnamnesis.objects.select_related(
                'beneficiary', 'created_by'
            ).prefetch_related(
                'vulnerabilities__category'
            )
            
            if search:
                queryset = queryset.filter(
                    Q(beneficiary__full_name__icontains=search) |
                    Q(observations__icontains=search)
                )
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            queryset = queryset.order_by('-created_at')
            
            # Cache por tempo curto (5 minutos)
            cache.set(cache_key, queryset, settings.CACHE_TIMEOUT['SHORT'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        # Adicionar opções para filtros
        context['status_choices'] = SocialAnamnesis.STATUS_CHOICES
        
        return context


@login_required
@user_passes_test(is_technician)
def add_evolution(request, pk):
    """Adicionar evolução à anamnese social"""
    anamnesis = get_object_or_404(
        SocialAnamnesis.objects.select_related('beneficiary'), 
        pk=pk
    )
    
    if request.method == 'POST':
        try:
            evolution = SocialAnamnesisEvolution.objects.create(
                anamnesis=anamnesis,
                professional=request.user.get_full_name() or request.user.username,
                evolution_type=request.POST.get('evolution_type', 'followup'),
                description=request.POST.get('description', ''),
                actions_taken=request.POST.get('actions_taken', ''),
                next_steps=request.POST.get('next_steps', ''),
                created_by=request.user
            )
            
            messages.success(request, 'Evolução adicionada com sucesso!')
            
            # Invalidar cache
            cache.delete(f"social_anamnesis_{pk}")
            
            return JsonResponse({
                'success': True,
                'message': 'Evolução adicionada com sucesso!',
                'evolution': {
                    'id': evolution.id,
                    'date': evolution.date.strftime('%d/%m/%Y'),
                    'professional': evolution.professional,
                    'evolution_type': evolution.get_evolution_type_display(),
                    'description': evolution.description,
                    'actions_taken': evolution.actions_taken,
                    'next_steps': evolution.next_steps
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao adicionar evolução: {str(e)}'
            })
    
    return redirect('social:detail', pk=pk)


@login_required
@user_passes_test(is_technician)
def vulnerability_categories_api(request):
    """API para listar categorias de vulnerabilidade"""
    categories = VulnerabilityCategory.objects.filter(is_active=True).order_by('name')
    
    data = [{
        'id': cat.id,
        'name': cat.name,
        'description': cat.description,
        'color': cat.color,
        'priority_level': cat.priority_level
    } for cat in categories]
    
    return JsonResponse({'categories': data})


@login_required
@user_passes_test(is_technician)
def lock_anamnesis(request, pk):
    """Alterar status da anamnese"""
    anamnesis = get_object_or_404(
        SocialAnamnesis.objects.select_related('beneficiary'), 
        pk=pk
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in ['draft', 'completed', 'review', 'approved']:
            anamnesis.status = new_status
            anamnesis.save()
            
            status_display = dict(SocialAnamnesis.STATUS_CHOICES)[new_status]
            messages.success(request, f'Status da anamnese alterado para: {status_display}')
            
            # Invalidar cache
            cache.delete(f"social_anamnesis_{pk}")
        else:
            messages.error(request, 'Status inválido.')
    
    return redirect('social:detail', pk=pk)


class SocialAnamnesisDeleteView(DeleteConfirmationMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    
    
    # Configurações da confirmação
    confirmation_message = "Tem certeza que deseja excluir este anamnese social?"
    confirmation_entity = "anamnese social"
    dangerous_operation = True"""Excluir anamnese social"""
    
    model = SocialAnamnesis
    template_name = 'social/anamnesis_confirm_delete.html'
    success_url = reverse_lazy('social:list')
    
    def test_func(self):
        return self.request.user.is_superuser  # Apenas superusuários podem excluir
    
    def get_object(self, queryset=None):
        """Verificar se a anamnese pode ser excluída"""
        obj = super().get_object(queryset)
        if obj.status == 'approved':
            messages.error(self.request, 'Não é possível excluir uma anamnese aprovada.')
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
        cache_keys = [f"social_anamnesis_list_{search}_{status}_{risk}" 
                     for search in ['', 'test'] 
                     for status in ['', 'draft', 'completed', 'review', 'approved'] 
                     for risk in ['', 'baixo', 'medio', 'alto', 'critico']]
        cache.delete_many(cache_keys)
        
        success_url = self.get_success_url()
        self.object.delete()
        
        messages.success(request, f'Anamnese social de {self.object.beneficiary.full_name} excluída com sucesso!')
        return redirect(success_url)


# Novas views para assinatura digital e relatórios

@login_required
@user_passes_test(is_technician)
def wizard_signature_view(request, pk):
    """View para assinatura digital da anamnese"""
    anamnesis = get_object_or_404(
        SocialAnamnesis.objects.select_related('beneficiary', 'signed_by_technician'), 
        pk=pk
    )
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Processar assinatura da beneficiária
                beneficiary_signature = request.POST.get('beneficiary_signature')
                if beneficiary_signature:
                    anamnesis.signature_beneficiary = beneficiary_signature
                    anamnesis.signed_by_beneficiary = True
                
                # Processar confirmação da técnica
                technician_confirmation = request.POST.get('technician_confirmation')
                technician_password = request.POST.get('technician_password')
                
                if technician_confirmation and technician_password:
                    # Verificar senha da técnica
                    from django.contrib.auth import authenticate
                    user = authenticate(username=request.user.username, password=technician_password)
                    
                    if user:
                        anamnesis.signed_by_technician = request.user
                        anamnesis.signature_technician = f"Assinatura eletrônica de {user.get_full_name()}"
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Senha incorreta para confirmação da assinatura.'
                        })
                
                # Verificar se ambas as assinaturas estão presentes
                if anamnesis.signed_by_beneficiary and anamnesis.signed_by_technician:
                    from django.utils import timezone
                    anamnesis.signature_timestamp = timezone.now()
                    anamnesis.is_signed = True
                    anamnesis.locked = True
                    anamnesis.status = 'completed'
                
                anamnesis.save()
                
                # Invalidar cache
                cache.delete(f"social_anamnesis_{pk}")
                
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse_lazy('social:anamnesis_detail', kwargs={'pk': pk})
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        else:
            messages.error(request, 'Método de requisição inválido.')
            return redirect('social:anamnesis_detail', pk=pk)
    
    context = {
        'anamnesis': anamnesis,
    }
    
    return render(request, 'social/wizard_signature.html', context)


class SocialReportsView(LoginRequiredMixin, CoordinatorRequiredMixin, TemplateView):
    """View para relatórios sociais"""
    template_name = 'social/social_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas resumo
        total_anamneses = SocialAnamnesis.objects.count()
        completed_anamneses = SocialAnamnesis.objects.filter(status='completed').count()
        draft_anamneses = SocialAnamnesis.objects.filter(status='draft').count()
        signed_anamneses = SocialAnamnesis.objects.filter(is_signed=True).count()
        
        context.update({
            'total_anamneses': total_anamneses,
            'completed_anamneses': completed_anamneses,
            'draft_anamneses': draft_anamneses,
            'signed_anamneses': signed_anamneses,
        })
        
        # Lista de técnicas para filtro
        from django.contrib.auth.models import User, Group
        technician_group = Group.objects.get(name='Tecnica')
        context['technicians'] = User.objects.filter(groups=technician_group)
        
        # Relatórios recentes (simulado)
        context['recent_reports'] = []  # Em uma implementação real, viria do banco
        
        return context


class VulnerabilityAnalyticsView(LoginRequiredMixin, CoordinatorRequiredMixin, TemplateView):
    """View para analytics de vulnerabilidades"""
    template_name = 'social/vulnerability_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categorias de vulnerabilidades
        context['vulnerability_categories'] = VulnerabilityCategory.objects.filter(is_active=True)
        
        # Contagens por gravidade
        from django.db.models import Count
        severity_counts = IdentifiedVulnerability.objects.values('severity').annotate(
            count=Count('id')
        )
        
        severity_data = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for item in severity_counts:
            severity_data[item['severity']] = item['count']
        
        context['severity_counts'] = severity_data
        
        # Top vulnerabilidades
        top_vulnerabilities = IdentifiedVulnerability.objects.values(
            'category__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        total_vulnerabilities = IdentifiedVulnerability.objects.count()
        
        for vuln in top_vulnerabilities:
            vuln['percentage'] = (vuln['count'] / total_vulnerabilities * 100) if total_vulnerabilities > 0 else 0
            vuln['trend'] = 0  # Em uma implementação real, calcularia a tendência
            vuln['avg_severity'] = 'medium'  # Simplificado
        
        context['top_vulnerabilities'] = top_vulnerabilities
        
        return context


@login_required
@user_passes_test(is_technician)
def generate_anamnesis_pdf(request, pk):
    """Gerar PDF da anamnese social"""
    anamnesis = get_object_or_404(
        SocialAnamnesis.objects.select_related('beneficiary', 'signed_by_technician')
        .prefetch_related('family_members', 'vulnerabilities__category', 'evolutions'), 
        pk=pk
    )
    
    try:
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from io import BytesIO
        
        # Criar buffer
        buffer = BytesIO()
        
        # Criar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Conteúdo do PDF
        story = []
        
        # Título
        title = Paragraph(f"Anamnese Social - {anamnesis.beneficiary.full_name}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Informações básicas
        info_text = f"""
        <b>Beneficiária:</b> {anamnesis.beneficiary.full_name}<br/>
        <b>Data de Criação:</b> {anamnesis.created_at.strftime('%d/%m/%Y %H:%M')}<br/>
        <b>Criada por:</b> {anamnesis.created_by.get_full_name()}<br/>
        <b>Status:</b> {anamnesis.get_status_display()}<br/>
        """
        
        if anamnesis.family_income:
            info_text += f"<b>Renda Familiar:</b> R$ {anamnesis.family_income:.2f}<br/>"
        
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Situação habitacional
        if anamnesis.housing_situation:
            story.append(Paragraph("<b>Situação Habitacional:</b>", styles['Heading2']))
            story.append(Paragraph(anamnesis.housing_situation, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Rede de apoio
        if anamnesis.support_network:
            story.append(Paragraph("<b>Rede de Apoio:</b>", styles['Heading2']))
            story.append(Paragraph(anamnesis.support_network, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Observações
        if anamnesis.observations:
            story.append(Paragraph("<b>Observações:</b>", styles['Heading2']))
            story.append(Paragraph(anamnesis.observations, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Assinaturas
        if anamnesis.is_signed:
            signature_text = f"""
            <b>DOCUMENTO ASSINADO DIGITALMENTE</b><br/>
            Data/Hora: {anamnesis.signature_timestamp.strftime('%d/%m/%Y às %H:%M')}<br/>
            Técnica Responsável: {anamnesis.signed_by_technician.get_full_name()}<br/>
            Beneficiária: {'Assinado' if anamnesis.signed_by_beneficiary else 'Não assinado'}
            """
            story.append(Paragraph(signature_text, styles['Normal']))
        
        # Gerar PDF
        doc.build(story)
        
        # Preparar resposta
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="anamnese_social_{anamnesis.beneficiary.full_name}_{anamnesis.created_at.strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except ImportError:
        messages.error(request, 'Biblioteca ReportLab não instalada. PDF não disponível.')
        return redirect('social:anamnesis_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('social:anamnesis_detail', pk=pk)


class SocialDashboardView(LoginRequiredMixin, TechnicianRequiredMixin, TemplateView):
    """Dashboard analítico do módulo social"""
    
    template_name = 'social/anamnesis_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cache dos dados do dashboard
        cache_key = "social_dashboard_data"
        dashboard_data = cache.get(cache_key)
        
        if dashboard_data is None:
            # Estatísticas básicas
            anamneses = SocialAnamnesis.objects.all()
            
            dashboard_data = {
                'total_anamneses': anamneses.count(),
                'completed_count': anamneses.filter(status='completed').count(),
                'draft_count': anamneses.filter(status='draft').count(),
                'update_required_count': anamneses.filter(status='requires_update').count(),
                'total_vulnerabilities': IdentifiedVulnerability.objects.count(),
                'total_beneficiaries_attended': anamneses.values('beneficiary').distinct().count(),
                
                # Vulnerabilidades por categoria
                'vulnerability_stats': VulnerabilityCategory.objects.annotate(
                    count=Count('identified_vulnerabilities')
                ).order_by('-count')[:5],
                
                # Atividades recentes (últimas 10)
                'recent_activities': SocialAnamnesisEvolution.objects.select_related(
                    'anamnesis__beneficiary', 'created_by'
                ).order_by('-created_at')[:10],
                
                # Anamneses recentes
                'recent_anamneses': anamneses.select_related(
                    'beneficiary', 'created_by'
                ).order_by('-created_at')[:5]
            }
            
            # Cache por 15 minutos
            cache.set(cache_key, dashboard_data, 900)
        
        context.update(dashboard_data)
        return context
