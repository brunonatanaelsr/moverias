from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from communication.models import (
    Announcement, InternalMemo, Newsletter, SuggestionBox,
    CommunicationMessage, MessageRecipient, MessageResponse, 
    CommunicationPreferences
)
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Migra dados legados de comunicação para o novo modelo unificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa uma simulação sem salvar dados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas durante a migração',
        )

    def handle(self, *args, **options):
        # Verificar se os modelos refatorados estão disponíveis
        if CommunicationMessage is None:
            self.stdout.write(
                self.style.ERROR('Modelos refatorados não encontrados. Verifique se as migrações foram aplicadas.')
            )
            return
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DE SIMULAÇÃO - Nenhum dado será salvo')
            )
        
        # Contadores para relatório
        counters = {
            'announcements': 0,
            'memos': 0,
            'newsletters': 0,
            'suggestions': 0,
            'total': 0,
            'errors': 0
        }
        
        try:
            # Migrar Comunicados
            self.stdout.write('Migrando Comunicados...')
            counters['announcements'] = self.migrate_announcements(dry_run, verbose)
            
            # Migrar Memorandos
            self.stdout.write('Migrando Memorandos...')
            counters['memos'] = self.migrate_memos(dry_run, verbose)
            
            # Migrar Newsletters
            self.stdout.write('Migrando Newsletters...')
            counters['newsletters'] = self.migrate_newsletters(dry_run, verbose)
            
            # Migrar Sugestões
            self.stdout.write('Migrando Sugestões...')
            counters['suggestions'] = self.migrate_suggestions(dry_run, verbose)
            
            # Criar preferências padrão para usuários
            self.stdout.write('Criando preferências padrão...')
            self.create_default_preferences(dry_run, verbose)
            
            # Calcular total
            counters['total'] = sum([
                counters['announcements'],
                counters['memos'],
                counters['newsletters'],
                counters['suggestions']
            ])
            
            # Relatório final
            self.print_migration_report(counters)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante a migração: {str(e)}')
            )
            raise

    def migrate_announcements(self, dry_run, verbose):
        """Migra comunicados para o novo modelo"""
        count = 0
        
        try:
            announcements = Announcement.objects.all()
            
            for announcement in announcements:
                if verbose:
                    self.stdout.write(f'Migrando comunicado: {announcement.title}')
                
                if not dry_run:
                    # Criar mensagem unificada
                    message = CommunicationMessage.objects.create(
                        title=announcement.title,
                        content=announcement.content,
                        message_type='announcement',
                        priority=self.map_priority(getattr(announcement, 'priority', 'medium')),
                        status='published',
                        category=self.map_category(getattr(announcement, 'category', 'general')),
                        author=announcement.author,
                        publish_date=announcement.created_at,
                        created_at=announcement.created_at,
                        updated_at=announcement.updated_at or announcement.created_at
                    )
                    
                    # Criar destinatários (todos os usuários se não especificado)
                    recipients = getattr(announcement, 'recipients', None)
                    if recipients and recipients.exists():
                        for user in recipients.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                    else:
                        # Enviar para todos os usuários
                        for user in User.objects.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                
                count += 1
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao migrar comunicados: {str(e)}')
            )
            
        return count

    def migrate_memos(self, dry_run, verbose):
        """Migra memorandos para o novo modelo"""
        count = 0
        
        try:
            memos = InternalMemo.objects.all()
            
            for memo in memos:
                if verbose:
                    self.stdout.write(f'Migrando memorando: {memo.title}')
                
                if not dry_run:
                    # Criar mensagem unificada
                    message = CommunicationMessage.objects.create(
                        title=memo.title,
                        content=memo.content,
                        message_type='memo',
                        priority=self.map_priority(getattr(memo, 'priority', 'medium')),
                        status='published',
                        category=self.map_category(getattr(memo, 'category', 'general')),
                        author=memo.from_user,
                        publish_date=memo.created_at,
                        created_at=memo.created_at,
                        updated_at=memo.updated_at or memo.created_at
                    )
                    
                    # Criar destinatários
                    if memo.to_users.exists():
                        for user in memo.to_users.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                    else:
                        # Enviar para todos os usuários
                        for user in User.objects.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                
                count += 1
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao migrar memorandos: {str(e)}')
            )
            
        return count

    def migrate_newsletters(self, dry_run, verbose):
        """Migra newsletters para o novo modelo"""
        count = 0
        
        try:
            newsletters = Newsletter.objects.all()
            
            for newsletter in newsletters:
                if verbose:
                    self.stdout.write(f'Migrando newsletter: {newsletter.title}')
                
                if not dry_run:
                    # Criar mensagem unificada
                    message = CommunicationMessage.objects.create(
                        title=newsletter.title,
                        content=newsletter.content,
                        message_type='newsletter',
                        priority='medium',
                        status='published',
                        category='general',
                        author=newsletter.author,
                        publish_date=newsletter.created_at,
                        created_at=newsletter.created_at,
                        updated_at=newsletter.updated_at or newsletter.created_at
                    )
                    
                    # Criar destinatários
                    recipients = getattr(newsletter, 'recipients', None)
                    if recipients and recipients.exists():
                        for user in recipients.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                    else:
                        # Enviar para todos os usuários
                        for user in User.objects.all():
                            MessageRecipient.objects.create(
                                message=message,
                                user=user,
                                is_read=False
                            )
                
                count += 1
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao migrar newsletters: {str(e)}')
            )
            
        return count

    def migrate_suggestions(self, dry_run, verbose):
        """Migra sugestões para o novo modelo"""
        count = 0
        
        try:
            suggestions = SuggestionBox.objects.all()
            
            for suggestion in suggestions:
                if verbose:
                    self.stdout.write(f'Migrando sugestão: {suggestion.title}')
                
                if not dry_run:
                    # Criar mensagem unificada
                    message = CommunicationMessage.objects.create(
                        title=suggestion.title,
                        content=suggestion.content,
                        message_type='notification',
                        priority='low',
                        status='published',
                        category='general',
                        author=suggestion.author,
                        publish_date=suggestion.created_at,
                        created_at=suggestion.created_at,
                        updated_at=suggestion.updated_at or suggestion.created_at,
                        allow_responses=True
                    )
                    
                    # Criar destinatários (administradores e NGOs)
                    admin_users = User.objects.filter(
                        user_type__in=['admin', 'ngo']
                    )
                    for user in admin_users:
                        MessageRecipient.objects.create(
                            message=message,
                            user=user,
                            is_read=False
                        )
                
                count += 1
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao migrar sugestões: {str(e)}')
            )
            
        return count

    def create_default_preferences(self, dry_run, verbose):
        """Cria preferências padrão para usuários que não possuem"""
        count = 0
        
        try:
            users_without_preferences = User.objects.filter(
                communication_preferences__isnull=True
            )
            
            for user in users_without_preferences:
                if verbose:
                    self.stdout.write(f'Criando preferências para: {user.get_full_name()}')
                
                if not dry_run:
                    CommunicationPreferences.objects.create(
                        user=user,
                        email_notifications=True,
                        push_notifications=True,
                        sms_notifications=False,
                        notification_frequency='immediate',
                        message_types=['announcement', 'memo', 'newsletter', 'notification'],
                        categories=['general', 'policy', 'event', 'training'],
                        language='pt',
                        timezone='America/Sao_Paulo'
                    )
                
                count += 1
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar preferências: {str(e)}')
            )
            
        return count

    def map_priority(self, old_priority):
        """Mapeia prioridades do sistema antigo para o novo"""
        priority_map = {
            'baixa': 'low',
            'low': 'low',
            'media': 'medium',
            'medium': 'medium',
            'alta': 'high',
            'high': 'high',
            'urgente': 'urgent',
            'urgent': 'urgent'
        }
        return priority_map.get(old_priority, 'medium')

    def map_category(self, old_category):
        """Mapeia categorias do sistema antigo para o novo"""
        category_map = {
            'geral': 'general',
            'general': 'general',
            'politica': 'policy',
            'policy': 'policy',
            'evento': 'event',
            'event': 'event',
            'treinamento': 'training',
            'training': 'training',
            'seguranca': 'safety',
            'safety': 'safety',
            'rh': 'hr',
            'hr': 'hr',
            'tecnico': 'technical',
            'technical': 'technical',
            'financeiro': 'financial',
            'financial': 'financial',
            'social': 'social'
        }
        return category_map.get(old_category, 'general')

    def print_migration_report(self, counters):
        """Imprime relatório da migração"""
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*50)
        )
        self.stdout.write(
            self.style.SUCCESS('RELATÓRIO DE MIGRAÇÃO')
        )
        self.stdout.write(
            self.style.SUCCESS('='*50)
        )
        
        self.stdout.write(f'Comunicados migrados: {counters["announcements"]}')
        self.stdout.write(f'Memorandos migrados: {counters["memos"]}')
        self.stdout.write(f'Newsletters migradas: {counters["newsletters"]}')
        self.stdout.write(f'Sugestões migradas: {counters["suggestions"]}')
        self.stdout.write(f'Total de mensagens: {counters["total"]}')
        
        if counters['errors'] > 0:
            self.stdout.write(
                self.style.ERROR(f'Erros encontrados: {counters["errors"]}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nMigração concluída com sucesso!')
        )
