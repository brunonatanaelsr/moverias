"""
Comando para popular o banco com dados de exemplo das atividades.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, time
import random

from members.models import Beneficiary
from social.models import SocialAnamnesis
from activities.models import (
    BeneficiaryActivity,
    ActivitySession,
    ActivityAttendance,
    ActivityFeedback,
    ActivityNote
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados de exemplo para o módulo de atividades'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa todos os dados existentes antes de criar novos'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Limpando dados existentes...'))
            BeneficiaryActivity.objects.all().delete()
            ActivitySession.objects.all().delete()
            ActivityAttendance.objects.all().delete()
            ActivityFeedback.objects.all().delete()
            ActivityNote.objects.all().delete()

        # Verificar se há beneficiárias
        beneficiaries = Beneficiary.objects.filter(status='ATIVA')
        if not beneficiaries.exists():
            self.stdout.write(
                self.style.ERROR(
                    'Não há beneficiárias ativas. Crie pelo menos uma beneficiária primeiro.'
                )
            )
            return

        # Verificar se há usuários
        users = User.objects.filter(is_active=True)
        if not users.exists():
            self.stdout.write(
                self.style.ERROR(
                    'Não há usuários ativos. Crie pelo menos um usuário primeiro.'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Criando dados de exemplo...'))

        # Criar atividades de exemplo
        self.create_sample_activities(beneficiaries, users)

        self.stdout.write(
            self.style.SUCCESS(
                f'Dados de exemplo criados com sucesso!'
            )
        )

    def create_sample_activities(self, beneficiaries, users):
        """Cria atividades de exemplo"""
        
        activity_templates = [
            {
                'title': 'Curso de Costura Básica',
                'activity_type': 'COURSE',
                'description': 'Curso básico de costura para iniciantes com foco em geração de renda',
                'objectives': 'Ensinar técnicas básicas de costura e desenvolver habilidades para empreendedorismo',
                'expected_outcomes': 'Capacitar para trabalho autônomo ou inserção no mercado de trabalho',
                'facilitator': 'Maria Santos',
                'location': 'Sala de Costura - Sede',
                'materials_needed': 'Máquina de costura, tecidos, linhas, agulhas, tesouras',
                'frequency': 'WEEKLY',
                'duration_days': 60,
            },
            {
                'title': 'Terapia Individual',
                'activity_type': 'THERAPY',
                'description': 'Acompanhamento psicológico individual para desenvolvimento pessoal',
                'objectives': 'Promover autoestima e desenvolvimento de habilidades emocionais',
                'expected_outcomes': 'Melhoria na qualidade de vida e relacionamentos',
                'facilitator': 'Dra. Ana Paula',
                'location': 'Consultório Psicológico',
                'materials_needed': 'Material de apoio terapêutico',
                'frequency': 'WEEKLY',
                'duration_days': 90,
            },
            {
                'title': 'Workshop de Empreendedorismo',
                'activity_type': 'WORKSHOP',
                'description': 'Workshop sobre como iniciar um pequeno negócio',
                'objectives': 'Desenvolver competências empreendedoras e de gestão',
                'expected_outcomes': 'Capacitar para criação de negócios próprios',
                'facilitator': 'João Silva',
                'location': 'Auditório Principal',
                'materials_needed': 'Projetor, computador, materiais impressos',
                'frequency': 'WEEKLY',
                'duration_days': 30,
            },
            {
                'title': 'Aconselhamento Jurídico',
                'activity_type': 'LEGAL',
                'description': 'Orientação jurídica sobre direitos e questões legais',
                'objectives': 'Informar sobre direitos e prover orientação legal',
                'expected_outcomes': 'Empoderamento através do conhecimento de direitos',
                'facilitator': 'Dr. Carlos Lima',
                'location': 'Escritório Jurídico',
                'materials_needed': 'Documentos, material informativo',
                'frequency': 'MONTHLY',
                'duration_days': 180,
            },
            {
                'title': 'Curso de Informática Básica',
                'activity_type': 'COURSE',
                'description': 'Curso básico de informática e inclusão digital',
                'objectives': 'Promover inclusão digital e capacitar para uso de tecnologia',
                'expected_outcomes': 'Melhorar empregabilidade e acesso a serviços digitais',
                'facilitator': 'Prof. Roberto',
                'location': 'Laboratório de Informática',
                'materials_needed': 'Computadores, material didático',
                'frequency': 'BIWEEKLY',
                'duration_days': 45,
            },
        ]

        created_activities = []
        
        for beneficiary in beneficiaries:
            # Criar 2-4 atividades por beneficiária
            num_activities = random.randint(2, 4)
            templates_used = random.sample(activity_templates, num_activities)
            
            for template in templates_used:
                start_date = date.today() - timedelta(days=random.randint(0, 30))
                end_date = start_date + timedelta(days=template['duration_days'])
                
                # Definir status baseado nas datas
                if start_date > date.today():
                    status = 'PLANNED'
                elif end_date < date.today():
                    status = 'COMPLETED'
                else:
                    status = 'ACTIVE'
                
                # Criar atividade
                activity = BeneficiaryActivity.objects.create(
                    beneficiary=beneficiary,
                    title=template['title'],
                    description=template['description'],
                    activity_type=template['activity_type'],
                    status=status,
                    priority=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    start_date=start_date,
                    end_date=end_date,
                    frequency=template['frequency'],
                    facilitator=template['facilitator'],
                    location=template['location'],
                    materials_needed=template['materials_needed'],
                    objectives=template['objectives'],
                    expected_outcomes=template['expected_outcomes'],
                    completion_percentage=random.randint(0, 100) if status == 'ACTIVE' else (100 if status == 'COMPLETED' else 0),
                    created_by=random.choice(users),
                )
                
                created_activities.append(activity)
                
                # Criar sessões para a atividade
                self.create_sessions_for_activity(activity, users)
                
                # Criar feedback para atividades concluídas
                if status == 'COMPLETED':
                    self.create_feedback_for_activity(activity)
                
                # Criar notas para algumas atividades
                if random.choice([True, False]):
                    self.create_notes_for_activity(activity, users)
        
        # Calcular impact score para todas as atividades
        for activity in created_activities:
            activity.calculate_impact_score()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Criadas {len(created_activities)} atividades de exemplo'
            )
        )

    def create_sessions_for_activity(self, activity, users):
        """Cria sessões para uma atividade"""
        
        # Determinar número de sessões baseado na frequência
        frequency_sessions = {
            'UNIQUE': 1,
            'WEEKLY': 8,
            'BIWEEKLY': 4,
            'MONTHLY': 3,
        }
        
        num_sessions = frequency_sessions.get(activity.frequency, 4)
        
        # Criar sessões
        for i in range(1, num_sessions + 1):
            session_date = activity.start_date + timedelta(days=i * 7)  # Semanal por padrão
            
            if session_date > activity.end_date:
                break
            
            # Definir status da sessão
            if session_date < date.today():
                session_status = 'COMPLETED'
            elif session_date == date.today():
                session_status = 'IN_PROGRESS'
            else:
                session_status = 'SCHEDULED'
            
            session = ActivitySession.objects.create(
                activity=activity,
                session_number=i,
                title=f'Sessão {i} - {activity.title}',
                description=f'Sessão {i} do curso {activity.title}',
                session_date=session_date,
                start_time=time(14, 0),  # 14:00
                end_time=time(16, 0),    # 16:00
                status=session_status,
                facilitator=activity.facilitator,
                location=activity.location,
                content_covered=f'Conteúdo da sessão {i}' if session_status == 'COMPLETED' else '',
                objectives_achieved=f'Objetivos da sessão {i}' if session_status == 'COMPLETED' else '',
            )
            
            # Criar registro de presença para sessões passadas
            if session_status == 'COMPLETED':
                attended = random.choice([True, True, True, False])  # 75% de chance de estar presente
                
                ActivityAttendance.objects.create(
                    session=session,
                    attended=attended,
                    arrival_time=time(13, 50) if attended else None,
                    departure_time=time(16, 5) if attended else None,
                    notes='Participação ativa' if attended else '',
                    excuse_reason='' if attended else 'Problemas pessoais',
                    recorded_by=random.choice(users),
                )

    def create_feedback_for_activity(self, activity):
        """Cria feedback para uma atividade concluída"""
        
        ActivityFeedback.objects.create(
            activity=activity,
            rating=random.randint(4, 5),
            content_quality=random.randint(4, 5),
            facilitator_rating=random.randint(4, 5),
            positive_aspects='Conteúdo muito útil e facilitador experiente',
            improvements_suggested='Poderia ter mais exercícios práticos',
            additional_comments='Curso muito bom, recomendo!',
            would_recommend=True,
        )

    def create_notes_for_activity(self, activity, users):
        """Cria notas para uma atividade"""
        
        note_templates = [
            {
                'type': 'PROGRESS',
                'title': 'Progresso Positivo',
                'content': 'Beneficiária demonstra ótimo progresso nas atividades propostas.',
            },
            {
                'type': 'CONCERN',
                'title': 'Necessita Atenção',
                'content': 'Beneficiária precisa de apoio adicional em alguns aspectos.',
            },
            {
                'type': 'ACHIEVEMENT',
                'title': 'Conquista Importante',
                'content': 'Beneficiária alcançou um marco importante em seu desenvolvimento.',
            },
        ]
        
        # Criar 1-2 notas por atividade
        for i in range(random.randint(1, 2)):
            template = random.choice(note_templates)
            
            ActivityNote.objects.create(
                activity=activity,
                note_type=template['type'],
                title=template['title'],
                content=template['content'],
                is_confidential=random.choice([True, False]),
                created_by=random.choice(users),
            )
