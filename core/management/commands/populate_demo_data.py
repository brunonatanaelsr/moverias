#!/usr/bin/env python3
# populate_demo_data.py - Command Django para popular dados de demonstração

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o sistema com dados de demonstração'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                          help='Limpa dados existentes antes de popular')
        parser.add_argument('--module', type=str, choices=['all', 'social', 'communication', 'certificates', 'hr'],
                          default='all', help='Módulo específico para popular')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_demo_data()
        
        module = options['module']
        
        if module in ['all', 'social']:
            self.populate_social_data()
        
        if module in ['all', 'communication']:
            self.populate_communication_data()
        
        if module in ['all', 'certificates']:
            self.populate_certificates_data()
        
        if module in ['all', 'hr']:
            self.populate_hr_data()
        
        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados com sucesso!'))

    def clear_demo_data(self):
        """Remove dados de demonstração existentes"""
        try:
            from members.models import Beneficiary
            from communication.models import Announcement
            
            self.stdout.write('Limpando dados existentes...')
            
            # Limpar apenas dados de demo (com flag específica ou criados pelo script)
            Beneficiary.objects.filter(full_name__startswith='[DEMO]').delete()
            Announcement.objects.filter(title__startswith='[DEMO]').delete()
            
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'Módulo não encontrado: {e}'))

    def populate_social_data(self):
        """Popula dados do módulo social"""
        try:
            from members.models import Beneficiary
            
            self.stdout.write('Criando dados do módulo social...')
            
            # Criar beneficiárias de exemplo
            beneficiaries_data = [
                {
                    'full_name': '[DEMO] Maria Silva Santos',
                    'email': 'maria.santos.demo@email.com',
                    'phone_1': '(11) 98765-4321',
                    'dob': timezone.now().date() - timedelta(days=365*35),
                    'address': 'Rua das Flores, 123',
                    'neighbourhood': 'Centro',
                    'status': 'ATIVA'
                },
                {
                    'full_name': '[DEMO] Ana Carolina Oliveira',
                    'email': 'ana.oliveira.demo@email.com',
                    'phone_1': '(11) 99876-5432',
                    'dob': timezone.now().date() - timedelta(days=365*28),
                    'address': 'Av. Principal, 456',
                    'neighbourhood': 'Jardim das Rosas',
                    'status': 'ATIVA'
                },
                {
                    'full_name': '[DEMO] Francisca dos Santos',
                    'email': 'francisca.santos.demo@email.com',
                    'phone_1': '(11) 97654-3210',
                    'dob': timezone.now().date() - timedelta(days=365*42),
                    'address': 'Rua da Esperança, 789',
                    'neighbourhood': 'Vila Nova',
                    'status': 'ATIVA'
                },
                {
                    'full_name': '[DEMO] Rosa Lima Costa',
                    'email': 'rosa.costa.demo@email.com',
                    'phone_1': '(11) 96543-2109',
                    'dob': timezone.now().date() - timedelta(days=365*31),
                    'address': 'Rua do Progresso, 321',
                    'neighbourhood': 'Bela Vista',
                    'status': 'ATIVA'
                },
                {
                    'full_name': '[DEMO] Joana Ferreira',
                    'email': 'joana.ferreira.demo@email.com',
                    'phone_1': '(11) 95432-1098',
                    'dob': timezone.now().date() - timedelta(days=365*26),
                    'address': 'Av. da Liberdade, 654',
                    'neighbourhood': 'Centro Histórico',
                    'status': 'ATIVA'
                }
            ]
            
            created_members = []
            for data in beneficiaries_data:
                beneficiary, created = Beneficiary.objects.get_or_create(
                    email=data['email'],
                    defaults=data
                )
                if created:
                    created_members.append(beneficiary)
                    self.stdout.write(f'Criada beneficiária: {beneficiary.full_name}')
            
            self.stdout.write(f'Criadas {len(created_members)} beneficiárias')
            
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'Módulo social não encontrado: {e}'))

    def populate_communication_data(self):
        """Popula dados do módulo de comunicação"""
        try:
            from communication.models import Announcement
            
            self.stdout.write('Criando dados do módulo de comunicação...')
            
            # Obter usuário admin para ser o autor
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.first()
            
            if not admin_user:
                self.stdout.write(self.style.WARNING('Nenhum usuário encontrado. Criando usuário demo...'))
                admin_user = User.objects.create_user(
                    username='admin_demo',
                    email='admin@demo.com',
                    password='demo123',
                    is_staff=True
                )
            
            announcements_data = [
                {
                    'title': '[DEMO] Workshop de Empreendedorismo Feminino',
                    'content': 'Participe do nosso workshop sobre empreendedorismo feminino! Aprenda técnicas de gestão, marketing digital e como formalizar seu negócio. Inscrições limitadas.',
                    'category': 'workshop',
                    'priority': 'high',
                    'is_active': True
                },
                {
                    'title': '[DEMO] Alteração no Horário de Atendimento',
                    'content': 'Informamos que a partir do próximo mês, nosso horário de atendimento será das 8h às 17h, de segunda a sexta-feira.',
                    'category': 'general',
                    'priority': 'medium',
                    'is_active': True
                },
                {
                    'title': '[DEMO] Nova Parceria com Banco do Empreendedor',
                    'content': 'Temos o prazer de anunciar nossa nova parceria! Agora oferecemos consultoria gratuita para microcrédito e abertura de contas empresariais.',
                    'category': 'partnership',
                    'priority': 'high',
                    'is_active': True
                },
                {
                    'title': '[DEMO] Curso de Informática Básica',
                    'content': 'Vagas abertas para o curso de informática básica! Aprenda a usar computador, internet e redes sociais para alavancar seu negócio.',
                    'category': 'course',
                    'priority': 'medium',
                    'is_active': True
                },
                {
                    'title': '[DEMO] Feira de Artesanato e Empreendedorismo',
                    'content': 'Participe da nossa feira mensal! Expositores podem se inscrever até o dia 15. Venha mostrar seus produtos e fazer networking.',
                    'category': 'event',
                    'priority': 'high',
                    'is_active': True
                }
            ]
            
            created_announcements = 0
            for data in announcements_data:
                announcement, created = Announcement.objects.get_or_create(
                    title=data['title'],
                    defaults={
                        **data,
                        'author': admin_user,
                        'publish_date': timezone.now() - timedelta(days=random.randint(1, 30))
                    }
                )
                if created:
                    created_announcements += 1
                    self.stdout.write(f'Criado comunicado: {announcement.title}')
            
            self.stdout.write(f'Criados {created_announcements} comunicados')
            
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'Módulo de comunicação não encontrado: {e}'))

    def populate_certificates_data(self):
        """Popula dados do módulo de certificados"""
        try:
            from certificates.models import Certificate, CertificateTemplate
            from members.models import Beneficiary
            
            self.stdout.write('Criando dados do módulo de certificados...')
            
            # Verificar se já existe um template
            template = CertificateTemplate.objects.first()
            if not template:
                self.stdout.write(self.style.WARNING('Nenhum template de certificado encontrado. Pulando certificados.'))
                return
            
            # Obter algumas beneficiárias para associar certificados
            beneficiaries = Beneficiary.objects.filter(full_name__startswith='[DEMO]')[:3]
            
            if beneficiaries:
                created_certificates = 0
                for beneficiary in beneficiaries:
                    certificate, created = Certificate.objects.get_or_create(
                        member=beneficiary,
                        template=template,
                        defaults={
                            'title': f'[DEMO] Certificado - {beneficiary.full_name}',
                            'issue_date': timezone.now().date() - timedelta(days=random.randint(1, 90)),
                            'status': 'generated'
                        }
                    )
                    if created:
                        created_certificates += 1
                        self.stdout.write(f'Criado certificado para: {beneficiary.full_name}')
                
                self.stdout.write(f'Criados {created_certificates} certificados')
            else:
                self.stdout.write(self.style.WARNING('Nenhuma beneficiária demo encontrada para certificados'))
                
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'Módulo de certificados não encontrado: {e}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Erro ao criar certificados: {e}'))

    def populate_hr_data(self):
        """Popula dados do módulo de RH"""
        try:
            from hr.models import JobPosition
            
            self.stdout.write('Criando dados do módulo de RH...')
            
            positions_data = [
                {
                    'title': '[DEMO] Assistente Administrativa',
                    'description': 'Vaga para assistente administrativa com experiência em atendimento ao público',
                    'requirements': 'Ensino médio completo, conhecimentos básicos de informática',
                },
                {
                    'title': '[DEMO] Coordenadora de Projetos',
                    'description': 'Coordenação de projetos sociais e ações de empreendedorismo feminino',
                    'requirements': 'Ensino superior, experiência em gestão de projetos',
                }
            ]
            
            created_positions = 0
            for data in positions_data:
                position, created = JobPosition.objects.get_or_create(
                    title=data['title'],
                    defaults=data
                )
                if created:
                    created_positions += 1
                    self.stdout.write(f'Criada posição: {position.title}')
            
            self.stdout.write(f'Criadas {created_positions} posições')
            
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f'Módulo de RH não encontrado: {e}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Erro ao criar posições: {e}'))
