"""
Script para migração de dados dos modelos antigos (Project/Task) para o novo modelo unificado (BeneficiaryActivity).
Este script pode ser executado como comando de gerenciamento Django.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time

from members.models import Beneficiary
from projects.models import Project, ProjectEnrollment, ProjectSession, ProjectAttendance
from tasks.models import Task, TaskBoard
from activities.models import BeneficiaryActivity, ActivitySession, ActivityAttendance

User = get_user_model()


class Command(BaseCommand):
    help = 'Migra dados dos modelos antigos para o novo sistema unificado de atividades'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa simulação sem salvar dados'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força migração mesmo com dados existentes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Verificar se já existem dados no novo sistema
        if BeneficiaryActivity.objects.exists() and not force:
            self.stdout.write(
                self.style.ERROR(
                    'Já existem atividades no novo sistema. Use --force para sobrescrever.'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Iniciando migração de dados...'))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULAÇÃO - Nenhum dado será salvo'))

        try:
            with transaction.atomic():
                # Migrar projetos
                projects_migrated = self.migrate_projects(dry_run)
                
                # Migrar tarefas
                tasks_migrated = self.migrate_tasks(dry_run)
                
                if dry_run:
                    # Forçar rollback no modo simulação
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.WARNING(
                            f'SIMULAÇÃO CONCLUÍDA - {projects_migrated} projetos e {tasks_migrated} tarefas processados'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Migração concluída! {projects_migrated} projetos e {tasks_migrated} tarefas migrados.'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante a migração: {str(e)}')
            )
            raise

    def migrate_projects(self, dry_run=False):
        """Migra projetos do modelo antigo para atividades"""
        migrated_count = 0
        
        projects = Project.objects.all()
        self.stdout.write(f'Migrando {projects.count()} projetos...')
        
        for project in projects:
            # Obter todas as matrículas do projeto
            enrollments = ProjectEnrollment.objects.filter(project=project)
            
            if not enrollments.exists():
                self.stdout.write(
                    self.style.WARNING(f'Projeto {project.name} não tem matrículas. Pulando.')
                )
                continue
            
            # Criar uma atividade para cada beneficiária matriculada
            for enrollment in enrollments:
                if not dry_run:
                    activity = self.create_activity_from_project(project, enrollment)
                    self.migrate_project_sessions(project, activity)
                
                migrated_count += 1
                
                if dry_run:
                    self.stdout.write(
                        f'[SIMULAÇÃO] Criaria atividade para {enrollment.beneficiary.full_name} - {project.name}'
                    )
        
        return migrated_count

    def create_activity_from_project(self, project, enrollment):
        """Cria atividade baseada no projeto e matrícula"""
        
        # Mapear status do projeto para atividade
        status_mapping = {
            'ATIVO': 'ACTIVE',
            'PAUSADO': 'PAUSED',
            'CONCLUIDO': 'COMPLETED',
            'CANCELADO': 'CANCELLED',
        }
        
        # Determinar tipo de atividade baseado no nome do projeto
        activity_type = self.determine_activity_type(project.name)
        
        # Obter usuário para criação (primeiro usuário ativo)
        created_by = User.objects.filter(is_active=True).first()
        
        activity = BeneficiaryActivity.objects.create(
            beneficiary=enrollment.beneficiary,
            title=project.name,
            description=project.description or '',
            activity_type=activity_type,
            status=status_mapping.get(project.status, 'ACTIVE'),
            priority='MEDIUM',  # Padrão
            start_date=project.start_date,
            end_date=project.end_date,
            frequency='WEEKLY',  # Padrão baseado na estrutura de projetos
            facilitator=project.coordinator,
            location=project.location,
            materials_needed='',  # Não disponível no modelo antigo
            objectives=project.objectives,
            expected_outcomes=project.target_audience,  # Adaptação
            completion_percentage=self.calculate_completion_percentage(project),
            created_by=created_by,
        )
        
        return activity

    def migrate_project_sessions(self, project, activity):
        """Migra sessões do projeto para a atividade"""
        
        sessions = ProjectSession.objects.filter(project=project)
        
        for session in sessions:
            # Criar sessão da atividade
            activity_session = ActivitySession.objects.create(
                activity=activity,
                session_number=sessions.filter(
                    session_date__lte=session.session_date
                ).count(),
                title=session.topic,
                description=session.description,
                session_date=session.session_date,
                start_time=session.start_time,
                end_time=session.end_time,
                status=self.determine_session_status(session),
                facilitator=session.facilitator,
                location=session.location,
                materials_used=session.materials_needed,
                content_covered=session.notes,
                objectives_achieved='',  # Não disponível no modelo antigo
                observations=session.notes,
            )
            
            # Migrar presença
            self.migrate_session_attendance(session, activity_session, activity.beneficiary)

    def migrate_session_attendance(self, old_session, new_session, beneficiary):
        """Migra presença da sessão"""
        
        # Buscar presença da beneficiária específica
        try:
            enrollment = ProjectEnrollment.objects.get(
                project=old_session.project,
                beneficiary=beneficiary
            )
            
            attendance = ProjectAttendance.objects.get(
                session=old_session,
                enrollment=enrollment
            )
            
            # Obter usuário para registro
            recorded_by = User.objects.filter(is_active=True).first()
            
            ActivityAttendance.objects.create(
                session=new_session,
                attended=attendance.attended,
                arrival_time=attendance.arrival_time,
                departure_time=attendance.departure_time,
                notes=attendance.notes,
                excuse_reason='',  # Não disponível no modelo antigo
                recorded_by=recorded_by,
            )
            
        except (ProjectEnrollment.DoesNotExist, ProjectAttendance.DoesNotExist):
            # Criar registro de presença padrão
            recorded_by = User.objects.filter(is_active=True).first()
            
            ActivityAttendance.objects.create(
                session=new_session,
                attended=False,
                recorded_by=recorded_by,
            )

    def migrate_tasks(self, dry_run=False):
        """Migra tarefas do modelo antigo para atividades"""
        migrated_count = 0
        
        tasks = Task.objects.all()
        self.stdout.write(f'Migrando {tasks.count()} tarefas...')
        
        for task in tasks:
            # Tentar associar tarefa a uma beneficiária
            # Se a tarefa não tiver beneficiária associada, pular
            if not hasattr(task, 'beneficiary') or not task.beneficiary:
                continue
            
            if not dry_run:
                self.create_activity_from_task(task)
            
            migrated_count += 1
            
            if dry_run:
                self.stdout.write(
                    f'[SIMULAÇÃO] Criaria atividade para tarefa: {task.title}'
                )
        
        return migrated_count

    def create_activity_from_task(self, task):
        """Cria atividade baseada na tarefa"""
        
        # Mapear status da tarefa
        status_mapping = {
            'todo': 'PLANNED',
            'doing': 'ACTIVE',
            'done': 'COMPLETED',
            'cancelled': 'CANCELLED',
        }
        
        # Mapear prioridade
        priority_mapping = {
            'low': 'LOW',
            'medium': 'MEDIUM',
            'high': 'HIGH',
            'urgent': 'URGENT',
        }
        
        # Obter usuário para criação
        created_by = task.created_by if hasattr(task, 'created_by') else User.objects.filter(is_active=True).first()
        
        activity = BeneficiaryActivity.objects.create(
            beneficiary=task.beneficiary,
            title=task.title,
            description=task.description,
            activity_type='OTHER',  # Padrão para tarefas
            status=status_mapping.get(task.status, 'PLANNED'),
            priority=priority_mapping.get(task.priority, 'MEDIUM'),
            start_date=task.start_date or date.today(),
            end_date=task.due_date,
            frequency='UNIQUE',  # Tarefas são geralmente únicas
            facilitator=task.assigned_to.username if hasattr(task, 'assigned_to') else 'Sistema',
            location='',  # Não disponível no modelo de tarefas
            materials_needed='',
            objectives=task.description,
            expected_outcomes='',
            completion_percentage=task.progress if hasattr(task, 'progress') else 0,
            created_by=created_by,
        )
        
        return activity

    def determine_activity_type(self, project_name):
        """Determina tipo de atividade baseado no nome do projeto"""
        name_lower = project_name.lower()
        
        if 'workshop' in name_lower:
            return 'WORKSHOP'
        elif 'curso' in name_lower:
            return 'COURSE'
        elif 'terapia' in name_lower or 'psicolog' in name_lower:
            return 'THERAPY'
        elif 'juridic' in name_lower or 'legal' in name_lower:
            return 'LEGAL'
        elif 'saude' in name_lower or 'medic' in name_lower:
            return 'HEALTH'
        elif 'educac' in name_lower or 'ensino' in name_lower:
            return 'EDUCATIONAL'
        elif 'profission' in name_lower or 'trabalho' in name_lower:
            return 'VOCATIONAL'
        else:
            return 'OTHER'

    def determine_session_status(self, session):
        """Determina status da sessão baseado na data"""
        today = date.today()
        
        if session.session_date < today:
            return 'COMPLETED'
        elif session.session_date == today:
            return 'IN_PROGRESS'
        else:
            return 'SCHEDULED'

    def calculate_completion_percentage(self, project):
        """Calcula percentual de conclusão baseado no projeto"""
        if project.status == 'CONCLUIDO':
            return 100
        elif project.status == 'CANCELADO':
            return 0
        else:
            # Calcular baseado na proporção de sessões concluídas
            total_sessions = project.sessions.count()
            completed_sessions = project.sessions.filter(
                session_date__lt=date.today()
            ).count()
            
            if total_sessions > 0:
                return int((completed_sessions / total_sessions) * 100)
            else:
                return 0
