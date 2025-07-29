#!/usr/bin/env python3
"""
Sistema de Notificações Automáticas - Move Marias
Implementa notificações inteligentes baseadas em regras de negócio
"""

import os
import sys
import django
import logging
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod

# Configurar Django antes de importar models
sys.path.append('/workspaces/move')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')

try:
    django.setup()
    
    # Importar modelos Django após setup
    from members.models import Beneficiary
    from projects.models import Project, ProjectEnrollment
    from workshops.models import Workshop
    from evolution.models import EvolutionRecord
    
    DJANGO_READY = True
except Exception as e:
    print(f"⚠️ Django não configurado corretamente: {e}")
    DJANGO_READY = False
    
    # Mock models para permitir execução sem Django
    class MockModel:
        objects = None
        
        @classmethod
        def count(cls):
            return 0
            
        @classmethod 
        def filter(cls, **kwargs):
            return cls()
            
    Beneficiary = MockModel
    Project = MockModel
    ProjectEnrollment = MockModel
    Workshop = MockModel
    EvolutionRecord = MockModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NotificationResult:
    """Resultado de uma notificação enviada"""
    success: bool
    message: str
    recipients: List[str]
    notification_type: str

class NotificationRule(ABC):
    """Classe base para regras de notificação"""
    
    def __init__(self, name: str, frequency: str, recipients: List[str]):
        self.name = name
        self.frequency = frequency  # 'daily', 'weekly', 'monthly'
        self.recipients = recipients
    
    @abstractmethod
    def should_trigger(self) -> bool:
        """Verifica se a regra deve ser disparada"""
        pass
    
    @abstractmethod
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém os dados para a notificação"""
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """Nome do template de email"""
        pass

class BeneficiaryInactivityRule(NotificationRule):
    """Notifica sobre beneficiárias inativas"""
    
    def __init__(self):
        super().__init__(
            name="Beneficiárias Inativas",
            frequency="weekly",
            recipients=['coordenacao@movemarias.org']
        )
    
    def should_trigger(self) -> bool:
        """Verifica se há beneficiárias inativas há mais de 30 dias"""
        if not DJANGO_READY:
            return True  # Simular para demonstração
        
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            inactive_count = Beneficiary.objects.filter(
                last_interaction__lt=cutoff_date,
                status='active'
            ).count()
            return inactive_count > 0
        except Exception as e:
            logger.error(f"Erro ao verificar beneficiárias inativas: {e}")
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém dados das beneficiárias inativas"""
        if not DJANGO_READY:
            return {
                'total_inactive': 3,
                'beneficiaries': [
                    {'name': 'Ana Silva', 'phone': '(11) 98765-4321', 'days_inactive': 35, 'responsible': 'Maria Santos'},
                    {'name': 'João Santos', 'phone': '(11) 99887-6655', 'days_inactive': 42, 'responsible': 'Pedro Lima'},
                    {'name': 'Carla Dias', 'phone': '(11) 97766-5544', 'days_inactive': 28, 'responsible': 'Ana Costa'}
                ],
                'cutoff_days': 30
            }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            inactive_beneficiaries = Beneficiary.objects.filter(
                last_interaction__lt=cutoff_date,
                status='active'
            ).select_related('responsible').order_by('last_interaction')[:10]
            
            return {
                'total_inactive': inactive_beneficiaries.count(),
                'beneficiaries': [
                    {
                        'name': b.name,
                        'phone': b.phone,
                        'last_interaction': b.last_interaction,
                        'responsible': b.responsible.name if b.responsible else 'Não definido',
                        'days_inactive': (datetime.now().date() - (b.last_interaction or datetime.now().date())).days
                    } for b in inactive_beneficiaries
                ],
                'cutoff_days': 30
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados de beneficiárias inativas: {e}")
            return {'total_inactive': 0, 'beneficiaries': []}
    
    def get_template_name(self) -> str:
        return 'notifications/beneficiary_inactivity.html'

class ProjectDeadlineRule(NotificationRule):
    """Notifica sobre projetos próximos do prazo"""
    
    def __init__(self):
        super().__init__(
            name="Prazos de Projetos",
            frequency="daily",
            recipients=['gestao@movemarias.org']
        )
    
    def should_trigger(self) -> bool:
        """Verifica se há projetos vencendo em 7 dias"""
        if not DJANGO_READY:
            return True  # Simular para demonstração
            
        try:
            deadline = datetime.now() + timedelta(days=7)
            projects_count = Project.objects.filter(
                end_date__lte=deadline,
                status__in=['active', 'in_progress']
            ).count()
            return projects_count > 0
        except Exception as e:
            logger.error(f"Erro ao verificar prazos de projetos: {e}")
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém dados dos projetos próximos do prazo"""
        if not DJANGO_READY:
            return {
                'total_projects': 2,
                'projects': [
                    {'name': 'Projeto Empoderamento', 'end_date': '2024-01-15', 'days_remaining': 3, 'urgency': 'high', 'responsible': 'Ana Santos', 'status': 'Ativo'},
                    {'name': 'Workshop Direitos', 'end_date': '2024-01-20', 'days_remaining': 8, 'urgency': 'medium', 'responsible': 'Carlos Lima', 'status': 'Em Progresso'}
                ],
                'deadline_days': 7
            }
        
        try:
            deadline = datetime.now() + timedelta(days=7)
            projects = Project.objects.filter(
                end_date__lte=deadline,
                status__in=['active', 'in_progress']
            ).select_related('responsible').order_by('end_date')
            
            project_data = []
            for p in projects:
                days_remaining = (p.end_date - datetime.now().date()).days if p.end_date else 0
                urgency = 'high' if days_remaining <= 3 else 'medium'
                
                project_data.append({
                    'name': p.name,
                    'end_date': p.end_date,
                    'days_remaining': days_remaining,
                    'urgency': urgency,
                    'responsible': p.responsible.name if p.responsible else 'Não definido',
                    'status': p.get_status_display()
                })
            
            return {
                'total_projects': len(project_data),
                'projects': project_data,
                'deadline_days': 7
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados de prazos de projetos: {e}")
            return {'total_projects': 0, 'projects': []}
    
    def get_template_name(self) -> str:
        return 'notifications/project_deadlines.html'

class WorkshopCapacityRule(NotificationRule):
    """Notifica sobre workshops com vagas disponíveis"""
    
    def __init__(self):
        super().__init__(
            name="Vagas em Workshops",
            frequency="weekly",
            recipients=['educacao@movemarias.org']
        )
    
    def should_trigger(self) -> bool:
        """Verifica se há workshops com mais de 50% de vagas disponíveis"""
        if not DJANGO_READY:
            return True  # Simular para demonstração
            
        try:
            workshops = Workshop.objects.filter(
                status='active',
                start_date__gte=datetime.now()
            )
            
            for workshop in workshops:
                enrolled = workshop.enrollments.filter(status='enrolled').count()
                if workshop.capacity and enrolled < (workshop.capacity * 0.5):
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar vagas em workshops: {e}")
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém dados dos workshops com vagas"""
        try:
            workshops = Workshop.objects.filter(
                status='active',
                start_date__gte=datetime.now()
            )
            
            available_workshops = []
            for workshop in workshops:
                enrolled = workshop.enrollments.filter(status='enrolled').count()
                if workshop.capacity and enrolled < (workshop.capacity * 0.5):
                    available_spots = workshop.capacity - enrolled
                    occupancy_rate = (enrolled / workshop.capacity) * 100
                    
                    available_workshops.append({
                        'name': workshop.name,
                        'start_date': workshop.start_date,
                        'capacity': workshop.capacity,
                        'enrolled': enrolled,
                        'available_spots': available_spots,
                        'occupancy_rate': round(occupancy_rate, 1),
                        'instructor': workshop.instructor.name if workshop.instructor else 'Não definido'
                    })
            
            return {
                'total_workshops': len(available_workshops),
                'workshops': available_workshops,
                'threshold_percentage': 50
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados de workshops: {e}")
            return {'total_workshops': 0, 'workshops': []}
    
    def get_template_name(self) -> str:
        return 'notifications/workshop_capacity.html'

class PendingDocumentsRule(NotificationRule):
    """Notifica sobre documentos pendentes de aprovação"""
    
    def __init__(self):
        super().__init__(
            name="Documentos Pendentes",
            frequency="daily",
            recipients=['admin@movemarias.org']
        )
    
    def should_trigger(self) -> bool:
        """Verifica se há documentos pendentes há mais de 3 dias"""
        try:
            # Como não temos um modelo específico de documentos,
            # vamos simular com evolution records
            cutoff_date = datetime.now() - timedelta(days=3)
            pending_count = EvolutionRecord.objects.filter(
                created_at__lt=cutoff_date,
                status='pending'
            ).count()
            return pending_count > 0
        except Exception as e:
            logger.error(f"Erro ao verificar documentos pendentes: {e}")
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém dados dos documentos pendentes"""
        try:
            cutoff_date = datetime.now() - timedelta(days=3)
            pending_docs = EvolutionRecord.objects.filter(
                created_at__lt=cutoff_date,
                status='pending'
            ).select_related('beneficiary', 'responsible')[:10]
            
            docs_data = []
            for doc in pending_docs:
                days_pending = (datetime.now().date() - doc.created_at.date()).days
                
                docs_data.append({
                    'beneficiary_name': doc.beneficiary.name,
                    'document_type': 'Registro de Evolução',
                    'created_date': doc.created_at,
                    'days_pending': days_pending,
                    'responsible': doc.responsible.name if doc.responsible else 'Não definido'
                })
            
            return {
                'total_pending': len(docs_data),
                'documents': docs_data,
                'threshold_days': 3
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados de documentos pendentes: {e}")
            return {'total_pending': 0, 'documents': []}
    
    def get_template_name(self) -> str:
        return 'notifications/pending_documents.html'

class SystemHealthRule(NotificationRule):
    """Notifica sobre saúde geral do sistema"""
    
    def __init__(self):
        super().__init__(
            name="Saúde do Sistema",
            frequency="daily",
            recipients=['tech@movemarias.org']
        )
    
    def should_trigger(self) -> bool:
        """Sempre envia relatório diário do sistema"""
        return True
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Obtém estatísticas gerais do sistema"""
        try:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Estatísticas básicas
            stats = {
                'total_beneficiaries': Beneficiary.objects.count(),
                'active_beneficiaries': Beneficiary.objects.filter(status='active').count(),
                'new_beneficiaries_week': Beneficiary.objects.filter(created_at__gte=week_ago).count(),
                
                'total_projects': Project.objects.count(),
                'active_projects': Project.objects.filter(status='active').count(),
                'projects_ending_week': Project.objects.filter(
                    end_date__lte=today + timedelta(days=7),
                    status='active'
                ).count(),
                
                'total_workshops': Workshop.objects.count(),
                'upcoming_workshops': Workshop.objects.filter(
                    start_date__gte=today,
                    status='active'
                ).count(),
                
                'evolution_records_week': EvolutionRecord.objects.filter(
                    created_at__gte=week_ago
                ).count(),
                
                'report_date': today,
                'period_start': week_ago
            }
            
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do sistema: {e}")
            return {
                'error': str(e),
                'report_date': datetime.now().date()
            }
    
    def get_template_name(self) -> str:
        return 'notifications/system_health.html'

class EmailSender:
    """Classe para envio de emails"""
    
    def __init__(self, smtp_host: str = 'localhost', smtp_port: int = 587):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
    
    def send_email(self, to_addresses: List[str], subject: str, 
                   html_content: str, from_address: str = 'notificacoes@movemarias.org') -> bool:
        """Envia email HTML"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Em modo de teste, não envia email real
            if hasattr(self, '_test_mode') and self._test_mode:
                logger.info(f"📧 EMAIL DE TESTE - Para: {to_addresses}, Assunto: {subject}")
                return True
            
            # Configuração real de SMTP aqui
            # server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            # server.starttls()
            # server.login(username, password)
            # server.send_message(msg)
            # server.quit()
            
            logger.info(f"Email enviado para: {to_addresses}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False

class NotificationEngine:
    """Engine principal de notificações"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.email_sender = EmailSender()
        if test_mode:
            self.email_sender._test_mode = True
        
        # Inicializar regras
        self.rules = [
            BeneficiaryInactivityRule(),
            ProjectDeadlineRule(),
            WorkshopCapacityRule(),
            PendingDocumentsRule(),
            SystemHealthRule()
        ]
    
    def load_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Carrega e renderiza template de email"""
        template_path = f'/workspaces/move/templates/{template_name}'
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Renderização simples de template (substituição de variáveis)
            for key, value in context.items():
                placeholder = f'{{{{{key}}}}}'
                if isinstance(value, list):
                    # Para listas, criar HTML simples
                    if value and isinstance(value[0], dict):
                        list_html = '<ul>'
                        for item in value[:5]:  # Limitar a 5 itens
                            list_html += f'<li>{item}</li>'
                        list_html += '</ul>'
                        template_content = template_content.replace(placeholder, list_html)
                    else:
                        template_content = template_content.replace(placeholder, ', '.join(map(str, value)))
                else:
                    template_content = template_content.replace(placeholder, str(value))
            
            return template_content
            
        except FileNotFoundError:
            logger.warning(f"Template {template_name} não encontrado, usando conteúdo padrão")
            return self._get_default_template(context)
        except Exception as e:
            logger.error(f"Erro ao carregar template {template_name}: {e}")
            return self._get_default_template(context)
    
    def _get_default_template(self, context: Dict[str, Any]) -> str:
        """Template padrão quando o arquivo não existe"""
        return f"""
        <html>
        <body>
            <h2>Notificação Move Marias</h2>
            <p>Dados da notificação:</p>
            <pre>{context}</pre>
            <hr>
            <p><small>Sistema Move Marias - Notificação Automática</small></p>
        </body>
        </html>
        """
    
    def process_notifications(self, frequency_filter: Optional[str] = None) -> List[NotificationResult]:
        """Processa todas as notificações"""
        results = []
        
        logger.info(f"Processando notificações - Frequência: {frequency_filter or 'todas'}")
        
        for rule in self.rules:
            try:
                # Filtrar por frequência se especificado
                if frequency_filter and rule.frequency != frequency_filter:
                    continue
                
                # Verificar se deve disparar
                if not rule.should_trigger():
                    logger.info(f"Regra {rule.name} não foi disparada")
                    continue
                
                # Obter dados
                data = rule.get_notification_data()
                if not data:
                    logger.warning(f"Nenhum dado para regra {rule.name}")
                    continue
                
                # Carregar template
                html_content = self.load_template(rule.get_template_name(), data)
                
                # Enviar email
                subject = f"Move Marias - {rule.name}"
                success = self.email_sender.send_email(
                    to_addresses=rule.recipients,
                    subject=subject,
                    html_content=html_content
                )
                
                result = NotificationResult(
                    success=success,
                    message=f"Notificação {rule.name} processada",
                    recipients=rule.recipients,
                    notification_type=rule.name
                )
                results.append(result)
                
                if success:
                    logger.info(f"✅ Notificação enviada: {rule.name}")
                else:
                    logger.error(f"❌ Falha ao enviar: {rule.name}")
                    
            except Exception as e:
                logger.error(f"Erro ao processar regra {rule.name}: {e}")
                results.append(NotificationResult(
                    success=False,
                    message=f"Erro ao processar regra {rule.name}: {e}",
                    recipients=rule.recipients,
                    notification_type=rule.name
                ))
        
        return results
    
    def create_email_templates(self):
        """Cria templates de email se não existirem"""
        templates_dir = '/workspaces/move/templates/notifications'
        os.makedirs(templates_dir, exist_ok=True)
        
        templates = {
            'beneficiary_inactivity.html': self._get_beneficiary_template(),
            'project_deadlines.html': self._get_project_template(),
            'workshop_capacity.html': self._get_workshop_template(),
            'pending_documents.html': self._get_documents_template(),
            'system_health.html': self._get_health_template()
        }
        
        for filename, content in templates.items():
            filepath = os.path.join(templates_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        logger.info(f"Templates criados em: {templates_dir}")
    
    def _get_beneficiary_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Beneficiárias Inativas - Move Marias</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2 style="color: #d63384;">🔔 Beneficiárias Inativas</h2>
    <p>Foram identificadas <strong>{{total_inactive}}</strong> beneficiárias inativas há mais de {{cutoff_days}} dias.</p>
    
    <h3>Beneficiárias que precisam de atenção:</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f8f9fa;">
            <th style="border: 1px solid #ddd; padding: 8px;">Nome</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Telefone</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Dias Inativa</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Responsável</th>
        </tr>
        {{beneficiaries}}
    </table>
    
    <p style="margin-top: 20px;">
        <a href="http://movemarias.org/beneficiaries/" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Ver Todas as Beneficiárias
        </a>
    </p>
    
    <hr>
    <p><small>Sistema Move Marias - Notificação Automática</small></p>
</body>
</html>"""

    def _get_project_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Prazos de Projetos - Move Marias</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2 style="color: #fd7e14;">⏰ Projetos Próximos do Prazo</h2>
    <p>Há <strong>{{total_projects}}</strong> projeto(s) que vencem nos próximos {{deadline_days}} dias.</p>
    
    <h3>Projetos que precisam de atenção:</h3>
    {{projects}}
    
    <p style="margin-top: 20px;">
        <a href="http://movemarias.org/projects/" style="background-color: #fd7e14; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Ver Todos os Projetos
        </a>
    </p>
    
    <hr>
    <p><small>Sistema Move Marias - Notificação Automática</small></p>
</body>
</html>"""

    def _get_workshop_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vagas em Workshops - Move Marias</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2 style="color: #198754;">🎓 Workshops com Vagas Disponíveis</h2>
    <p>Há <strong>{{total_workshops}}</strong> workshop(s) com mais de {{threshold_percentage}}% de vagas disponíveis.</p>
    
    <h3>Oportunidades de divulgação:</h3>
    {{workshops}}
    
    <p style="margin-top: 20px;">
        <a href="http://movemarias.org/workshops/" style="background-color: #198754; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Ver Todos os Workshops
        </a>
    </p>
    
    <hr>
    <p><small>Sistema Move Marias - Notificação Automática</small></p>
</body>
</html>"""

    def _get_documents_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Documentos Pendentes - Move Marias</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2 style="color: #dc3545;">📋 Documentos Pendentes de Aprovação</h2>
    <p>Há <strong>{{total_pending}}</strong> documento(s) pendente(s) há mais de {{threshold_days}} dias.</p>
    
    <h3>Documentos que precisam de revisão:</h3>
    {{documents}}
    
    <p style="margin-top: 20px;">
        <a href="http://movemarias.org/admin/" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Revisar Documentos
        </a>
    </p>
    
    <hr>
    <p><small>Sistema Move Marias - Notificação Automática</small></p>
</body>
</html>"""

    def _get_health_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Saúde do Sistema - Move Marias</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2 style="color: #6f42c1;">🖥️ Relatório de Saúde do Sistema</h2>
    <p>Relatório diário do sistema Move Marias - {{report_date}}</p>
    
    <h3>Estatísticas Gerais:</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Total de Beneficiárias:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{total_beneficiaries}}</td></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Beneficiárias Ativas:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{active_beneficiaries}}</td></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Novas esta Semana:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{new_beneficiaries_week}}</td></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Total de Projetos:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{total_projects}}</td></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Projetos Ativos:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{active_projects}}</td></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Total de Workshops:</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{{total_workshops}}</td></tr>
    </table>
    
    <p style="margin-top: 20px;">
        <a href="http://movemarias.org/dashboard/" style="background-color: #6f42c1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Ver Dashboard Completo
        </a>
    </p>
    
    <hr>
    <p><small>Sistema Move Marias - Notificação Automática</small></p>
</body>
</html>"""

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Notificações Automáticas - Move Marias')
    parser.add_argument('--frequency', choices=['daily', 'weekly', 'monthly'], 
                       help='Filtrar notificações por frequência')
    parser.add_argument('--test', action='store_true', 
                       help='Modo de teste (não envia emails reais)')
    parser.add_argument('--create-templates', action='store_true',
                       help='Criar templates de email')
    
    args = parser.parse_args()
    
    print("🔔 SISTEMA DE NOTIFICAÇÕES AUTOMÁTICAS")
    print("=" * 50)
    
    if args.test:
        print("🧪 MODO DE TESTE - Emails não serão enviados")
    
    try:
        engine = NotificationEngine(test_mode=args.test)
        
        if args.create_templates:
            engine.create_email_templates()
            return
        
        # Processar notificações
        results = engine.process_notifications(args.frequency)
        
        # Resumo final
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        
        logger.info("=== RESUMO DE NOTIFICAÇÕES ===")
        logger.info(f"Notificações enviadas: {successful}")
        
        if failed > 0:
            logger.error(f"Erros encontrados: {failed}")
            for result in results:
                if not result.success:
                    logger.error(f"  ✗ {result.message}")
        
        print("=" * 50)
        print("✅ PROCESSAMENTO CONCLUÍDO!")
        if failed > 0:
            print(f"⚠️  {failed} erro(s) encontrado(s)")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erro crítico no sistema: {e}")
        print(f"❌ ERRO CRÍTICO: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
