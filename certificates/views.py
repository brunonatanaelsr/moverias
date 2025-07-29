"""
Views para o sistema de certificados
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from core.unified_permissions import (
    is_technician, is_coordinator, is_admin, 
    TechnicianRequiredMixin, CoordinatorRequiredMixin, AdminRequiredMixin,
    requires_technician, requires_coordinator, requires_admin
)
from .models import (
    Certificate, CertificateTemplate, CertificateRequest, CertificateDelivery,
    auto_generate_certificates, send_certificate_email, verify_certificate
)
from .forms import CertificateTemplateForm, CertificateRequestForm, CertificateForm
from members.models import Beneficiary
from workshops.models import Workshop, WorkshopEnrollment
from activities.models import BeneficiaryActivity
from django.template.loader import render_to_string
import weasyprint
import os
from datetime import datetime, timedelta


@login_required
def certificates_dashboard(request):
    """Dashboard de certificados"""
    # Verificar se o usuário tem uma beneficiária associada pelo email
    beneficiary = None
    try:
        beneficiary = Beneficiary.objects.get(email=request.user.email)
    except Beneficiary.DoesNotExist:
        # Se não encontrar pela email, não há beneficiária associada
        pass
    
    # Certificados da beneficiária
    certificates = Certificate.objects.filter(member=beneficiary).order_by('-created_at') if beneficiary else Certificate.objects.none()
    
    # Solicitações pendentes
    pending_requests = CertificateRequest.objects.filter(
        member=beneficiary,
        approved=False
    ).order_by('-requested_at') if beneficiary else CertificateRequest.objects.none()
    
    # Workshops elegíveis para certificado
    eligible_workshops = []
    if beneficiary:
        enrollments = WorkshopEnrollment.objects.filter(
            member=beneficiary,
            status='completed'
        ).exclude(
            workshop__in=certificates.values_list('workshop', flat=True)
        )
        
        for enrollment in enrollments:
            if enrollment.attendance_percentage >= 75:  # 75% de presença mínima
                eligible_workshops.append(enrollment.workshop)
    
    # Se o usuário for admin/técnica, mostrar todos os certificados
    if hasattr(request.user, 'role') and request.user.role in ['admin', 'tecnica']:
        certificates = Certificate.objects.all().order_by('-created_at')
        pending_requests = CertificateRequest.objects.filter(approved=False).order_by('-requested_at')
    
    # Aplicar filtros se fornecidos
    status_filter = request.GET.get('status')
    certificate_type_filter = request.GET.get('certificate_type')
    beneficiary_filter = request.GET.get('beneficiary')
    
    if status_filter:
        certificates = certificates.filter(status=status_filter)
    
    if certificate_type_filter:
        certificates = certificates.filter(certificate_type=certificate_type_filter)
    
    if beneficiary_filter:
        certificates = certificates.filter(
            Q(member__full_name__icontains=beneficiary_filter) |
            Q(member__email__icontains=beneficiary_filter)
        )
    
    # Paginação
    paginator = Paginator(certificates, 12)  # 12 certificados por página
    page = request.GET.get('page')
    certificates = paginator.get_page(page)
    
    context = {
        'beneficiary': beneficiary,
        'certificates': certificates,
        'pending_requests': pending_requests,
        'eligible_workshops': eligible_workshops,
        'total_certificates': Certificate.objects.count(),
        'pending_count': pending_requests.count(),
        'eligible_count': len(eligible_workshops),
    }
    
    return render(request, 'certificates/list.html', context)


@login_required
def certificate_detail(request, certificate_id):
    """Detalhes de um certificado"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Verificar se o usuário pode ver este certificado
    if certificate.member.user != request.user and not request.user.is_staff:
        raise Http404("Certificado não encontrado")
    
    # Histórico de entregas
    deliveries = CertificateDelivery.objects.filter(certificate=certificate)
    
    context = {
        'certificate': certificate,
        'deliveries': deliveries,
        'can_download': certificate.pdf_file and certificate.status == 'generated',
    }
    
    return render(request, 'certificates/certificate_detail.html', context)


@login_required
def download_certificate(request, certificate_id):
    """Download do certificado em PDF"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Verificar permissão
    if certificate.member.email != request.user.email and not request.user.is_staff:
        raise Http404("Certificado não encontrado")
    
    # Verificar se PDF existe
    if not certificate.pdf_file:
        messages.error(request, "Certificado ainda não foi gerado.")
        return redirect('certificates:detail', certificate_id=certificate.id)
    
    # Registrar download
    CertificateDelivery.objects.create(
        certificate=certificate,
        method='download',
        recipient_email=request.user.email
    )
    
    # Retornar arquivo
    try:
        response = HttpResponse(
            certificate.pdf_file.read(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="certificado_{certificate.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao baixar certificado: {e}")
        return redirect('certificates:detail', certificate_id=certificate.id)


@login_required
def request_certificate(request, workshop_id):
    """Solicitar certificado para um workshop"""
    workshop = get_object_or_404(Workshop, id=workshop_id)
    try:
        beneficiary = Beneficiary.objects.get(email=request.user.email)
    except Beneficiary.DoesNotExist:
        messages.error(request, "Perfil de beneficiária não encontrado.")
        return redirect('workshops:detail', workshop_id=workshop.id)
    
    # Verificar se pode solicitar certificado
    try:
        enrollment = WorkshopEnrollment.objects.get(member=beneficiary, workshop=workshop)
        if enrollment.status != 'completed':
            messages.error(request, "Você precisa concluir o workshop para solicitar certificado.")
            return redirect('workshops:detail', workshop_id=workshop.id)
        
        if enrollment.attendance_percentage < 75:
            messages.error(request, "Você precisa ter pelo menos 75% de presença para solicitar certificado.")
            return redirect('workshops:detail', workshop_id=workshop.id)
    except WorkshopEnrollment.DoesNotExist:
        messages.error(request, "Você não está inscrito neste workshop.")
        return redirect('workshops:detail', workshop_id=workshop.id)
    
    # Verificar se já existe solicitação
    if CertificateRequest.objects.filter(member=beneficiary, workshop=workshop).exists():
        messages.info(request, "Você já solicitou certificado para este workshop.")
        return redirect('certificates:dashboard')
    
    # Verificar se já possui certificado
    if Certificate.objects.filter(member=beneficiary, workshop=workshop).exists():
        messages.info(request, "Você já possui certificado para este workshop.")
        return redirect('certificates:dashboard')
    
    if request.method == 'POST':
        # Criar solicitação
        certificate_request = CertificateRequest.objects.create(
            member=beneficiary,
            workshop=workshop,
            notes=request.POST.get('notes', '')
        )
        
        messages.success(request, "Solicitação de certificado enviada com sucesso!")
        return redirect('certificates:dashboard')
    
    context = {
        'workshop': workshop,
        'beneficiary': beneficiary,
        'enrollment': enrollment,
    }
    
    return render(request, 'certificates/request_certificate.html', context)


def verify_certificate_view(request, code):
    """Verificar autenticidade de certificado"""
    result = verify_certificate(code)
    
    context = {
        'verification_result': result,
        'code': code,
    }
    
    return render(request, 'certificates/verify_certificate.html', context)


@require_http_methods(["POST"])
def verify_certificate_api(request):
    """API para verificar certificado"""
    code = request.POST.get('code', '').strip().upper()
    
    if not code:
        return JsonResponse({
            'valid': False,
            'message': 'Código de verificação é obrigatório'
        })
    
    result = verify_certificate(code)
    
    if result['valid']:
        certificate = result['certificate']
        return JsonResponse({
            'valid': True,
            'certificate': {
                'id': str(certificate.id),
                'title': certificate.title,
                'member_name': certificate.member.full_name,
                'issue_date': certificate.issue_date.isoformat(),
                'completion_date': certificate.completion_date.isoformat(),
                'workshop': certificate.workshop.title if certificate.workshop else None,
                'instructor': certificate.instructor,
                'hours_completed': certificate.hours_completed,
                'verification_code': certificate.verification_code,
            },
            'message': result['message']
        })
    else:
        return JsonResponse({
            'valid': False,
            'message': result['message']
        })


# Views administrativas
@requires_admin
def admin_certificates_list(request):
    """Lista de certificados para administradores"""
    certificates = Certificate.objects.all().order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        certificates = certificates.filter(
            Q(beneficiary__name__icontains=search) |
            Q(title__icontains=search) |
            Q(verification_code__icontains=search)
        )
    
    if status:
        certificates = certificates.filter(status=status)
    
    # Paginação
    paginator = Paginator(certificates, 20)
    page = request.GET.get('page')
    certificates = paginator.get_page(page)
    
    context = {
        'certificates': certificates,
        'search': search,
        'status': status,
        'status_choices': Certificate.STATUS_CHOICES,
    }
    
    return render(request, 'certificates/admin_certificates_list.html', context)


@requires_admin
def admin_certificate_requests(request):
    """Lista de solicitações de certificado para administradores"""
    requests = CertificateRequest.objects.all().order_by('-requested_at')
    
    # Filtros
    approved = request.GET.get('approved', '')
    if approved == 'true':
        requests = requests.filter(approved=True)
    elif approved == 'false':
        requests = requests.filter(approved=False)
    
    # Paginação
    paginator = Paginator(requests, 20)
    page = request.GET.get('page')
    requests = paginator.get_page(page)
    
    context = {
        'requests': requests,
        'approved': approved,
    }
    
    return render(request, 'certificates/admin_certificate_requests.html', context)


@requires_admin
def approve_certificate_request(request, request_id):
    """Aprovar solicitação de certificado"""
    certificate_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        try:
            # Aprovar e gerar certificado
            certificate = certificate_request.approve()
            
            # Enviar por email se solicitado
            if request.POST.get('send_email'):
                send_certificate_email(certificate)
            
            messages.success(request, f"Certificado aprovado e gerado para {certificate_request.beneficiary.name}")
        except Exception as e:
            messages.error(request, f"Erro ao aprovar certificado: {e}")
    
    return redirect('certificates:admin_requests')


@requires_admin
def auto_generate_certificates_view(request):
    """Gerar certificados automaticamente"""
    if request.method == 'POST':
        try:
            count = auto_generate_certificates()
            messages.success(request, f"{count} certificados gerados automaticamente.")
        except Exception as e:
            messages.error(request, f"Erro ao gerar certificados: {e}")
    
    return redirect('certificates:admin_certificates')


@requires_admin
def send_certificate_email_view(request, certificate_id):
    """Enviar certificado por email"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        try:
            send_certificate_email(certificate)
            messages.success(request, f"Certificado enviado por email para {certificate.member.email}")
        except Exception as e:
            messages.error(request, f"Erro ao enviar email: {e}")
    
    return redirect('certificates:admin_certificates')


# Views baseadas em classe para templates
class CertificateTemplateListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = CertificateTemplate
    template_name = 'certificates/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return CertificateTemplate.objects.filter(is_active=True)


class CertificateTemplateCreateView(CreateConfirmationMixin, LoginRequiredMixin, AdminRequiredMixin, CreateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo certificado?"
    confirmation_entity = "certificado"model = CertificateTemplate
    form_class = CertificateTemplateForm
    template_name = 'certificates/template_form.html'
    success_url = reverse_lazy('certificates:template_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, "Template de certificado criado com sucesso!")
        return super().form_valid(form)


class CertificateTemplateUpdateView(EditConfirmationMixin, LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste certificado?"
    confirmation_entity = "certificado"model = CertificateTemplate
    form_class = CertificateTemplateForm
    template_name = 'certificates/template_form.html'
    success_url = reverse_lazy('certificates:template_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, "Template de certificado atualizado com sucesso!")
        return super().form_valid(form)


@login_required
@requires_admin
def certificate_create(request):
    """Criar novo certificado"""
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.created_by = request.user
            certificate.save()
            messages.success(request, 'Certificado criado com sucesso!')
            return redirect('certificates:detail', certificate_id=certificate.id)
    else:
        form = CertificateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'certificates/create.html', context)


@login_required
@requires_admin
def certificate_edit(request, certificate_id):
    """Editar certificado existente"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        form = CertificateForm(request.POST, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificado atualizado com sucesso!')
            return redirect('certificates:detail', certificate_id=certificate.id)
    else:
        form = CertificateForm(instance=certificate)
    
    context = {
        'form': form,
        'certificate': certificate,
    }
    
    return render(request, 'certificates/edit.html', context)


@login_required
@requires_admin
def certificate_delete(request, certificate_id):
    """Deletar certificado"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    if request.method == 'POST':
        certificate.delete()
        messages.success(request, 'Certificado deletado com sucesso!')
        return redirect('certificates:list')
    
    context = {
        'certificate': certificate,
    }
    
    return render(request, 'certificates/delete.html', context)


@login_required
def gerar_recibo_beneficio(request, beneficiary_id):
    """
    Gera recibo de benefício para uma beneficiária específica
    """
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    if request.method == 'POST':
        benefit_description = request.POST.get('benefit_description', '')
        
        context = {
            'beneficiary': beneficiary,
            'benefit_description': benefit_description,
            'current_date': timezone.now(),
        }
        
        # Gerar PDF se requisitado
        if request.POST.get('generate_pdf'):
            return gerar_pdf_recibo_beneficio(beneficiary, benefit_description)
        
        # Renderizar template para visualização
        return render(request, 'certificates/recibo_beneficio.html', context)
    
    # Formulário para preenchimento
    return render(request, 'certificates/form_recibo_beneficio.html', {
        'beneficiary': beneficiary
    })

@login_required
def gerar_declaracao_comparecimento(request, beneficiary_id):
    """
    Gera declaração de comparecimento para uma beneficiária específica
    """
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    if request.method == 'POST':
        activity_name = request.POST.get('activity_name', '')
        activity_date = request.POST.get('activity_date', '')
        activity_duration = request.POST.get('activity_duration', '')
        additional_info = request.POST.get('additional_info', '')
        
        # Converter data se fornecida
        parsed_date = None
        if activity_date:
            try:
                parsed_date = datetime.strptime(activity_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        context = {
            'beneficiary': beneficiary,
            'activity_name': activity_name,
            'activity_date': parsed_date,
            'activity_duration': activity_duration,
            'additional_info': additional_info,
            'current_date': timezone.now(),
        }
        
        # Gerar PDF se requisitado
        if request.POST.get('generate_pdf'):
            return gerar_pdf_declaracao_comparecimento(beneficiary, context)
        
        # Renderizar template para visualização
        return render(request, 'certificates/declaracao_comparecimento.html', context)
    
    # Buscar atividades recentes da beneficiária para sugestões
    recent_activities = BeneficiaryActivity.objects.filter(
        beneficiary=beneficiary,
        status='active'
    ).order_by('-created_at')[:5]
    
    # Formulário para preenchimento
    return render(request, 'certificates/form_declaracao_comparecimento.html', {
        'beneficiary': beneficiary,
        'recent_activities': recent_activities
    })

def gerar_pdf_recibo_beneficio(beneficiary, benefit_description):
    """
    Gera PDF do recibo de benefício
    """
    context = {
        'beneficiary': beneficiary,
        'benefit_description': benefit_description,
        'current_date': timezone.now(),
    }
    
    html_string = render_to_string('certificates/recibo_beneficio.html', context)
    
    # Gerar PDF usando weasyprint
    try:
        pdf = weasyprint.HTML(string=html_string).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"recibo_beneficio_{beneficiary.full_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('certificates:gerar_recibo_beneficio', beneficiary_id=beneficiary.id)

def gerar_pdf_declaracao_comparecimento(beneficiary, context):
    """
    Gera PDF da declaração de comparecimento
    """
    html_string = render_to_string('certificates/declaracao_comparecimento.html', context)
    
    # Gerar PDF usando weasyprint
    try:
        pdf = weasyprint.HTML(string=html_string).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"declaracao_comparecimento_{beneficiary.full_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('certificates:gerar_declaracao_comparecimento', beneficiary_id=beneficiary.id)

@login_required
def lista_beneficiarias_certificados(request):
    """
    Lista todas as beneficiárias para gerar certificados
    """
    beneficiaries = Beneficiary.objects.filter(status='ATIVA').order_by('full_name')
    
    # Filtro por nome se fornecido
    search = request.GET.get('search')
    if search:
        beneficiaries = beneficiaries.filter(full_name__icontains=search)
    
    # Paginação
    paginator = Paginator(beneficiaries, 20)
    page = request.GET.get('page')
    beneficiaries = paginator.get_page(page)
    
    return render(request, 'certificates/lista_beneficiarias.html', {
        'beneficiaries': beneficiaries,
        'search': search
    })

@login_required
def dashboard_certificados(request):
    """
    Dashboard principal do sistema de certificados
    """
    # Estatísticas
    total_beneficiaries = Beneficiary.objects.filter(status='ATIVA').count()
    certificates_generated = Certificate.objects.filter(status='generated').count()
    recent_certificates = Certificate.objects.order_by('-created_at')[:10]
    
    # Certificados pendentes
    pending_requests = CertificateRequest.objects.filter(status='pending').count()
    
    context = {
        'total_beneficiaries': total_beneficiaries,
        'certificates_generated': certificates_generated,
        'pending_requests': pending_requests,
        'recent_certificates': recent_certificates,
    }
    
    return render(request, 'certificates/dashboard.html', context)
