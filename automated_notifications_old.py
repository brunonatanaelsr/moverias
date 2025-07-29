#!/usr/bin/env python3
"""
Sistema de Notificações Automáticas Inteligentes
Parte da Fase 3 do Plano de Melhorias Incrementais - Automação
"""

import os
import sys
import django
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.db.models import Q, F, Count, Case, When
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()


class NotificationRule:
    """Classe base para regras de notificação"""
    
    def __init__(self, name, description, frequency='daily'):
        self.name = name
        self.description = description
        self.frequency = frequency  # daily, weekly, monthly
        self.enabled = True
    
    def should_trigger(self):
        """Verifica se a notificação deve ser disparada"""
        raise NotImplementedError
    
    def get_recipients(self):
        """Retorna lista de usuários que devem receber a notificação"""
        raise NotImplementedError
    
    def get_context_data(self):
        """Retorna dados para o template da notificação"""
        raise NotImplementedError
    
    def get_template_name(self):
        """Retorna nome do template de email"""
        raise NotImplementedError
    
    def get_subject(self):
        """Retorna assunto do email"""
        raise NotImplementedError


class BeneficiaryInactivityRule(NotificationRule):
    """Notifica sobre beneficiárias inativas por muito tempo"""
    
    def __init__(self):
        super().__init__(
            name="Beneficiárias Inativas",
            description="Beneficiárias sem evolução há mais de 30 dias",
            frequency='weekly'
        )
    
    def should_trigger(self):
        from members.models import Beneficiary
        
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        inactive_count = Beneficiary.objects.filter(
            status='ATIVA',
            evolution_records__date__lt=thirty_days_ago
        ).exclude(
            evolution_records__date__gte=thirty_days_ago
        ).count()
        
        return inactive_count > 0
    
    def get_recipients(self):
        return User.objects.filter(
            Q(is_staff=True) | Q(groups__name='Coordenadores')
        ).distinct()
    
    def get_context_data(self):
        from members.models import Beneficiary
        
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        inactive_beneficiaries = Beneficiary.objects.filter(
            status='ATIVA'
        ).annotate(
            last_evolution=models.Max('evolution_records__date')
        ).filter(
            Q(last_evolution__lt=thirty_days_ago) | Q(last_evolution__isnull=True)
        ).select_related().order_by('last_evolution')[:20]
        
        return {
            'inactive_beneficiaries': inactive_beneficiaries,
            'count': inactive_beneficiaries.count(),
            'threshold_days': 30
        }
    
    def get_template_name(self):
        return 'notifications/beneficiary_inactivity.html'
    
    def get_subject(self):
        return "Relatório Semanal: Beneficiárias com Baixa Atividade"


class ProjectDeadlineRule(NotificationRule):
    """Notifica sobre projetos próximos do prazo"""
    
    def __init__(self):
        super().__init__(
            name="Prazos de Projetos",
            description="Projetos com prazo vencendo em 7 dias",
            frequency='daily'
        )
    
    def should_trigger(self):
        from projects.models import Project
        
        seven_days_ahead = timezone.now().date() + timedelta(days=7)
        
        expiring_count = Project.objects.filter(
            status='ATIVO',
            end_date__lte=seven_days_ahead,
            end_date__gte=timezone.now().date()
        ).count()
        
        return expiring_count > 0
    
    def get_recipients(self):
        return User.objects.filter(
            Q(is_staff=True) | 
            Q(groups__name__in=['Coordenadores', 'Gestores de Projeto'])
        ).distinct()
    
    def get_context_data(self):
        from projects.models import Project
        
        seven_days_ahead = timezone.now().date() + timedelta(days=7)
        
        expiring_projects = Project.objects.filter(
            status='ATIVO',
            end_date__lte=seven_days_ahead,
            end_date__gte=timezone.now().date()
        ).annotate(
            days_remaining=F('end_date') - timezone.now().date(),
            enrollment_count=Count('enrollments')
        ).order_by('end_date')
        
        return {
            'expiring_projects': expiring_projects,
            'count': expiring_projects.count()
        }
    
    def get_template_name(self):
        return 'notifications/project_deadlines.html'
    
    def get_subject(self):
        return "Alerta: Projetos com Prazos Próximos"


class WorkshopCapacityRule(NotificationRule):
    """Notifica sobre workshops com vagas disponíveis"""
    
    def __init__(self):
        super().__init__(
            name="Vagas em Workshops",
            description="Workshops com muitas vagas disponíveis",
            frequency='weekly'
        )
    
    def should_trigger(self):
        from workshops.models import Workshop
        
        workshops_with_vacancies = Workshop.objects.filter(
            status='ativo',
            date__gte=timezone.now().date()
        ).annotate(
            enrollment_count=Count('enrollments'),
            vacancy_rate=Case(
                When(max_participants=0, then=0),
                default=(F('max_participants') - Count('enrollments')) * 100 / F('max_participants')
            )
        ).filter(vacancy_rate__gte=50).count()
        
        return workshops_with_vacancies > 0
    
    def get_recipients(self):
        return User.objects.filter(
            Q(groups__name__in=['Coordenadores', 'Educadores'])
        ).distinct()
    
    def get_context_data(self):
        from workshops.models import Workshop
        
        workshops = Workshop.objects.filter(
            status='ativo',
            date__gte=timezone.now().date()
        ).annotate(
            enrollment_count=Count('enrollments'),
            available_spots=F('max_participants') - Count('enrollments'),
            vacancy_rate=Case(
                When(max_participants=0, then=0),
                default=(F('max_participants') - Count('enrollments')) * 100 / F('max_participants')
            )
        ).filter(vacancy_rate__gte=50).order_by('-vacancy_rate')[:10]
        
        return {
            'workshops': workshops,
            'count': workshops.count()
        }
    
    def get_template_name(self):
        return 'notifications/workshop_capacity.html'
    
    def get_subject(self):
        return "Relatório: Workshops com Vagas Disponíveis"


class PendingDocumentsRule(NotificationRule):
    """Notifica sobre documentos pendentes de revisão"""
    
    def __init__(self):
        super().__init__(
            name="Documentos Pendentes",
            description="Documentos aguardando aprovação há mais de 3 dias",
            frequency='daily'
        )
    
    def should_trigger(self):
        # Assumindo que existe um modelo de documentos
        three_days_ago = timezone.now().date() - timedelta(days=3)
        
        # Adaptar conforme modelo real
        try:
            from core.models import FileUpload
            
            pending_count = FileUpload.objects.filter(
                status='PENDING',
                uploaded_at__date__lte=three_days_ago
            ).count()
            
            return pending_count > 0
        except:
            return False
    
    def get_recipients(self):
        return User.objects.filter(
            Q(is_staff=True) | Q(groups__name='Revisores')
        ).distinct()
    
    def get_context_data(self):
        try:
            from core.models import FileUpload
            
            three_days_ago = timezone.now().date() - timedelta(days=3)
            
            pending_docs = FileUpload.objects.filter(
                status='PENDING',
                uploaded_at__date__lte=three_days_ago
            ).select_related('uploaded_by').order_by('uploaded_at')[:20]
            
            return {
                'pending_documents': pending_docs,
                'count': pending_docs.count(),
                'threshold_days': 3
            }
        except:
            return {'pending_documents': [], 'count': 0}
    
    def get_template_name(self):
        return 'notifications/pending_documents.html'
    
    def get_subject(self):
        return "Alerta: Documentos Pendentes de Aprovação"


class SystemHealthRule(NotificationRule):
    """Notifica sobre a saúde do sistema"""
    
    def __init__(self):
        super().__init__(
            name="Saúde do Sistema",
            description="Relatório diário sobre performance e erros",
            frequency='daily'
        )
    
    def should_trigger(self):
        # Sempre envia relatório diário para administradores
        return True
    
    def get_recipients(self):
        return User.objects.filter(is_superuser=True)
    
    def get_context_data(self):
        from django.db import connection
        from members.models import Beneficiary
        from projects.models import Project
        from workshops.models import Workshop
        
        # Estatísticas básicas
        stats = {
            'beneficiaries_count': Beneficiary.objects.count(),
            'active_beneficiaries': Beneficiary.objects.filter(status='ATIVA').count(),
            'active_projects': Project.objects.filter(status='ATIVO').count(),
            'upcoming_workshops': Workshop.objects.filter(
                status='ativo',
                date__gte=timezone.now().date(),
                date__lte=timezone.now().date() + timedelta(days=7)
            ).count(),
        }
        
        # Performance do banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
        
        stats['database_tables'] = table_count
        
        # Logs de erro (se configurado)
        try:
            import os
            log_file = os.path.join(settings.BASE_DIR, 'logs', 'django.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    recent_errors = [
                        line for line in f.readlines()[-100:] 
                        if 'ERROR' in line
                    ]
                stats['recent_errors'] = len(recent_errors)
            else:
                stats['recent_errors'] = 0
        except:
            stats['recent_errors'] = 0
        
        return {
            'stats': stats,
            'date': timezone.now().date()
        }
    
    def get_template_name(self):
        return 'notifications/system_health.html'
    
    def get_subject(self):
        return f"Relatório Diário do Sistema - {timezone.now().strftime('%d/%m/%Y')}"


class NotificationEngine:
    """Engine principal para processar notificações"""
    
    def __init__(self):
        self.rules = [
            BeneficiaryInactivityRule(),
            ProjectDeadlineRule(),
            WorkshopCapacityRule(),
            PendingDocumentsRule(),
            SystemHealthRule(),
        ]
        
        self.sent_notifications = []
        self.errors = []
    
    def process_notifications(self, frequency=None):
        """Processa todas as notificações para uma frequência específica"""
        logger.info(f"Processando notificações - Frequência: {frequency or 'todas'}")
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if frequency and rule.frequency != frequency:
                continue
            
            try:
                if rule.should_trigger():
                    self.send_notification(rule)
                else:
                    logger.info(f"Regra {rule.name} não foi disparada")
                    
            except Exception as e:
                error_msg = f"Erro ao processar regra {rule.name}: {str(e)}"
                self.errors.append(error_msg)
                logger.error(error_msg)
        
        self.log_summary()
    
    def send_notification(self, rule):
        """Envia notificação para uma regra específica"""
        try:
            recipients = rule.get_recipients()
            if not recipients.exists():
                logger.warning(f"Nenhum destinatário encontrado para {rule.name}")
                return
            
            context = rule.get_context_data()
            subject = rule.get_subject()
            template_name = rule.get_template_name()
            
            # Renderizar template
            html_content = render_to_string(template_name, context)
            
            # Preparar emails
            emails = []
            for recipient in recipients:
                emails.append((
                    subject,
                    html_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email]
                ))
            
            # Enviar emails em massa
            send_mass_mail(emails, fail_silently=False)
            
            notification_info = f"Notificação {rule.name} enviada para {recipients.count()} usuários"
            self.sent_notifications.append(notification_info)
            logger.info(notification_info)
            
        except Exception as e:
            error_msg = f"Erro ao enviar notificação {rule.name}: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
    
    def log_summary(self):
        """Log resumo da execução"""
        logger.info("=== RESUMO DE NOTIFICAÇÕES ===")
        logger.info(f"Notificações enviadas: {len(self.sent_notifications)}")
        
        for notification in self.sent_notifications:
            logger.info(f"  ✓ {notification}")
        
        if self.errors:
            logger.error(f"Erros encontrados: {len(self.errors)}")
            for error in self.errors:
                logger.error(f"  ✗ {error}")


def create_notification_templates():
    """Cria templates de email para as notificações"""
    templates_dir = BASE_DIR / 'templates' / 'notifications'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Template para beneficiárias inativas
    beneficiary_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Beneficiárias Inativas</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .beneficiary-item { border-bottom: 1px solid #eee; padding: 10px 0; }
        .alert { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Relatório: Beneficiárias com Baixa Atividade</h2>
        </div>
        
        <div class="content">
            <div class="alert">
                <strong>⚠️ Atenção:</strong> {{ count }} beneficiárias não tiveram registros de evolução nos últimos {{ threshold_days }} dias.
            </div>
            
            <h3>Beneficiárias que necessitam atenção:</h3>
            
            {% for beneficiary in inactive_beneficiaries %}
            <div class="beneficiary-item">
                <strong>{{ beneficiary.name }}</strong><br>
                <small>
                    Status: {{ beneficiary.status }} | 
                    Última evolução: {{ beneficiary.last_evolution|date:"d/m/Y"|default:"Nunca" }}
                </small>
            </div>
            {% endfor %}
            
            <p style="margin-top: 20px;">
                <strong>Recomendação:</strong> Entre em contato com essas beneficiárias para verificar seu status atual e agendar novos atendimentos se necessário.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    (templates_dir / 'beneficiary_inactivity.html').write_text(beneficiary_template.strip())
    
    # Template para projetos com prazo vencendo
    project_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Projetos com Prazos Próximos</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .project-item { border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; background: #f8f9fa; }
        .urgent { border-left-color: #dc3545; background: #f8d7da; }
        .warning { border-left-color: #ffc107; background: #fff3cd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🚨 Alerta: Prazos de Projetos</h2>
        </div>
        
        <div class="content">
            <p><strong>{{ count }} projeto(s)</strong> têm prazos vencendo nos próximos 7 dias:</p>
            
            {% for project in expiring_projects %}
            <div class="project-item {% if project.days_remaining <= 2 %}urgent{% else %}warning{% endif %}">
                <h4>{{ project.name }}</h4>
                <p>
                    <strong>Prazo:</strong> {{ project.end_date|date:"d/m/Y" }}<br>
                    <strong>Dias restantes:</strong> {{ project.days_remaining }}<br>
                    <strong>Participantes:</strong> {{ project.enrollment_count }}<br>
                    <strong>Status:</strong> {{ project.status }}
                </p>
            </div>
            {% endfor %}
            
            <p style="margin-top: 20px;">
                <strong>Ação requerida:</strong> Verifique o progresso desses projetos e tome as medidas necessárias antes do vencimento.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    (templates_dir / 'project_deadlines.html').write_text(project_template.strip())
    
    # Template para saúde do sistema
    system_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Saúde do Sistema</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
        .stat-item { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📊 Relatório Diário do Sistema</h2>
            <p>{{ date|date:"d/m/Y" }}</p>
        </div>
        
        <div class="content">
            <h3>Estatísticas Gerais</h3>
            
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-number">{{ stats.beneficiaries_count }}</div>
                    <div>Total de Beneficiárias</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-number">{{ stats.active_beneficiaries }}</div>
                    <div>Beneficiárias Ativas</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-number">{{ stats.active_projects }}</div>
                    <div>Projetos Ativos</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-number">{{ stats.upcoming_workshops }}</div>
                    <div>Workshops esta Semana</div>
                </div>
            </div>
            
            <h3>Saúde Técnica</h3>
            <ul>
                <li><strong>Tabelas no banco:</strong> {{ stats.database_tables }}</li>
                <li><strong>Erros recentes:</strong> {{ stats.recent_errors }}</li>
            </ul>
            
            {% if stats.recent_errors > 10 %}
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <strong>⚠️ Atenção:</strong> Alto número de erros detectados. Verificar logs do sistema.
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
    """
    
    (templates_dir / 'system_health.html').write_text(system_template.strip())
    
    logger.info(f"Templates criados em: {templates_dir}")


def main():
    """Função principal para executar notificações"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Notificações Automáticas')
    parser.add_argument('--frequency', choices=['daily', 'weekly', 'monthly'], 
                       help='Frequência das notificações a processar')
    parser.add_argument('--create-templates', action='store_true',
                       help='Criar templates de email')
    parser.add_argument('--test', action='store_true',
                       help='Modo de teste (não envia emails)')
    
    args = parser.parse_args()
    
    if args.create_templates:
        create_notification_templates()
        return
    
    print("🔔 SISTEMA DE NOTIFICAÇÕES AUTOMÁTICAS")
    print("=" * 50)
    
    if args.test:
        print("🧪 MODO DE TESTE - Emails não serão enviados")
        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    engine = NotificationEngine()
    engine.process_notifications(frequency=args.frequency)
    
    print("\n" + "=" * 50)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    
    if engine.errors:
        print(f"⚠️  {len(engine.errors)} erro(s) encontrado(s)")
        return 1
    
    print(f"📧 {len(engine.sent_notifications)} notificação(ões) processada(s)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
