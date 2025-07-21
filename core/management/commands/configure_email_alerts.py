"""
Comando para configurar alertas por email e gerenciar administradores
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import json
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Configurar alertas por email e gerenciar administradores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-admins',
            action='store_true',
            help='Listar administradores atuais',
        )
        parser.add_argument(
            '--add-admin',
            type=str,
            help='Adicionar email de administrador',
        )
        parser.add_argument(
            '--remove-admin',
            type=str,
            help='Remover email de administrador',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Testar envio de email para um endereço',
        )
        parser.add_argument(
            '--configure-alerts',
            action='store_true',
            help='Configurar alertas por email',
        )
        parser.add_argument(
            '--set-threshold',
            nargs=3,
            metavar=('METRIC', 'WARNING', 'CRITICAL'),
            help='Definir thresholds para uma métrica (ex: cpu_usage 70 85)',
        )
        parser.add_argument(
            '--enable-notifications',
            action='store_true',
            help='Habilitar notificações por email',
        )
        parser.add_argument(
            '--disable-notifications',
            action='store_true',
            help='Desabilitar notificações por email',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostrar status das configurações',
        )

    def handle(self, *args, **options):
        if options['list_admins']:
            self.list_admins()
        elif options['add_admin']:
            self.add_admin(options['add_admin'])
        elif options['remove_admin']:
            self.remove_admin(options['remove_admin'])
        elif options['test_email']:
            self.test_email(options['test_email'])
        elif options['configure_alerts']:
            self.configure_alerts()
        elif options['set_threshold']:
            self.set_threshold(*options['set_threshold'])
        elif options['enable_notifications']:
            self.enable_notifications()
        elif options['disable_notifications']:
            self.disable_notifications()
        elif options['status']:
            self.show_status()
        else:
            self.show_help()

    def list_admins(self):
        """Listar administradores atuais"""
        self.stdout.write(self.style.SUCCESS('=== ADMINISTRADORES ATUAIS ==='))
        
        # Administradores do sistema
        admin_users = User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', 'first_name', 'last_name', 'role')
        
        if admin_users:
            self.stdout.write('\n📧 Administradores do Sistema:')
            for email, first_name, last_name, role in admin_users:
                name = f"{first_name} {last_name}".strip() or "Sem nome"
                self.stdout.write(f"  • {email} ({name}) - {role}")
        else:
            self.stdout.write(self.style.WARNING('  Nenhum administrador encontrado'))
        
        # Emails de alerta configurados
        alert_emails = self.get_alert_emails()
        if alert_emails:
            self.stdout.write('\n🚨 Emails de Alerta:')
            for email in alert_emails:
                self.stdout.write(f"  • {email}")
        else:
            self.stdout.write(self.style.WARNING('\n  Nenhum email de alerta configurado'))

    def add_admin(self, email):
        """Adicionar email de administrador"""
        if not self.validate_email(email):
            self.stdout.write(self.style.ERROR(f'Email inválido: {email}'))
            return
        
        alert_emails = self.get_alert_emails()
        
        if email in alert_emails:
            self.stdout.write(self.style.WARNING(f'Email já está na lista: {email}'))
            return
        
        alert_emails.append(email)
        self.save_alert_emails(alert_emails)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Email adicionado: {email}'))

    def remove_admin(self, email):
        """Remover email de administrador"""
        alert_emails = self.get_alert_emails()
        
        if email not in alert_emails:
            self.stdout.write(self.style.WARNING(f'Email não encontrado: {email}'))
            return
        
        alert_emails.remove(email)
        self.save_alert_emails(alert_emails)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Email removido: {email}'))

    def test_email(self, email):
        """Testar envio de email"""
        if not self.validate_email(email):
            self.stdout.write(self.style.ERROR(f'Email inválido: {email}'))
            return
        
        self.stdout.write(f'🧪 Testando envio para: {email}')
        
        try:
            subject = 'Teste de Email - Move Marias'
            message = f'''
            Olá!
            
            Este é um email de teste do sistema Move Marias.
            
            Se você recebeu este email, a configuração está funcionando corretamente.
            
            Detalhes do teste:
            - Data/Hora: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
            - Sistema: Move Marias
            - Tipo: Teste de configuração
            
            Atenciosamente,
            Sistema Move Marias
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Email enviado com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao enviar email: {str(e)}'))

    def configure_alerts(self):
        """Configurar alertas por email"""
        self.stdout.write(self.style.SUCCESS('=== CONFIGURAÇÃO DE ALERTAS ==='))
        
        # Verificar configuração de email
        if not self.check_email_config():
            self.stdout.write(self.style.ERROR('❌ Configuração de email inválida'))
            return
        
        # Configurar alertas padrão
        alert_config = {
            'enabled': True,
            'cooldown_minutes': 30,
            'thresholds': {
                'cpu_usage': {'warning': 70, 'critical': 85},
                'memory_usage': {'warning': 70, 'critical': 85},
                'disk_usage': {'warning': 80, 'critical': 90},
                'response_time': {'warning': 500, 'critical': 1000},
                'error_rate': {'warning': 1, 'critical': 5},
                'cache_hit_rate': {'warning': 80, 'critical': 60},
            },
            'notification_types': [
                'critical_alerts',
                'system_down',
                'performance_degradation',
                'security_alerts',
            ],
            'last_updated': timezone.now().isoformat(),
        }
        
        # Salvar configuração
        cache.set('alert_config', alert_config, 60 * 60 * 24 * 365)  # 1 ano
        
        self.stdout.write(self.style.SUCCESS('✅ Configuração de alertas salva'))
        
        # Mostrar configuração
        self.stdout.write('\n📋 Configuração Atual:')
        self.stdout.write(f'  • Status: {"Habilitado" if alert_config["enabled"] else "Desabilitado"}')
        self.stdout.write(f'  • Cooldown: {alert_config["cooldown_minutes"]} minutos')
        self.stdout.write(f'  • Thresholds configurados: {len(alert_config["thresholds"])}')
        self.stdout.write(f'  • Tipos de notificação: {len(alert_config["notification_types"])}')

    def set_threshold(self, metric, warning, critical):
        """Definir threshold para uma métrica"""
        try:
            warning_val = float(warning)
            critical_val = float(critical)
        except ValueError:
            self.stdout.write(self.style.ERROR('❌ Valores devem ser numéricos'))
            return
        
        # Obter configuração atual
        alert_config = cache.get('alert_config', {})
        
        if 'thresholds' not in alert_config:
            alert_config['thresholds'] = {}
        
        alert_config['thresholds'][metric] = {
            'warning': warning_val,
            'critical': critical_val
        }
        
        alert_config['last_updated'] = timezone.now().isoformat()
        
        # Salvar configuração
        cache.set('alert_config', alert_config, 60 * 60 * 24 * 365)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Threshold definido para {metric}:'))
        self.stdout.write(f'  • Warning: {warning_val}')
        self.stdout.write(f'  • Critical: {critical_val}')

    def enable_notifications(self):
        """Habilitar notificações por email"""
        alert_config = cache.get('alert_config', {})
        alert_config['enabled'] = True
        alert_config['last_updated'] = timezone.now().isoformat()
        
        cache.set('alert_config', alert_config, 60 * 60 * 24 * 365)
        
        self.stdout.write(self.style.SUCCESS('✅ Notificações por email habilitadas'))

    def disable_notifications(self):
        """Desabilitar notificações por email"""
        alert_config = cache.get('alert_config', {})
        alert_config['enabled'] = False
        alert_config['last_updated'] = timezone.now().isoformat()
        
        cache.set('alert_config', alert_config, 60 * 60 * 24 * 365)
        
        self.stdout.write(self.style.SUCCESS('✅ Notificações por email desabilitadas'))

    def show_status(self):
        """Mostrar status das configurações"""
        self.stdout.write(self.style.SUCCESS('=== STATUS DAS CONFIGURAÇÕES ==='))
        
        # Status do email
        email_ok = self.check_email_config()
        self.stdout.write(f'\n📧 Configuração de Email: {"✅ OK" if email_ok else "❌ Erro"}')
        
        if email_ok:
            self.stdout.write(f'  • Servidor: {getattr(settings, "EMAIL_HOST", "Não configurado")}')
            self.stdout.write(f'  • Porta: {getattr(settings, "EMAIL_PORT", "Não configurado")}')
            self.stdout.write(f'  • From: {getattr(settings, "DEFAULT_FROM_EMAIL", "Não configurado")}')
        
        # Status dos alertas
        alert_config = cache.get('alert_config', {})
        self.stdout.write(f'\n🚨 Alertas: {"✅ Habilitados" if alert_config.get("enabled", False) else "❌ Desabilitados"}')
        
        if alert_config:
            self.stdout.write(f'  • Cooldown: {alert_config.get("cooldown_minutes", 0)} minutos')
            self.stdout.write(f'  • Thresholds: {len(alert_config.get("thresholds", {}))}')
            self.stdout.write(f'  • Última atualização: {alert_config.get("last_updated", "Nunca")}')
        
        # Status dos administradores
        admin_count = User.objects.filter(is_staff=True, is_active=True).count()
        alert_emails = self.get_alert_emails()
        
        self.stdout.write(f'\n👥 Administradores: {admin_count} no sistema')
        self.stdout.write(f'📧 Emails de Alerta: {len(alert_emails)} configurados')
        
        # Teste de conectividade
        self.stdout.write(f'\n🔗 Teste de Conectividade:')
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
            connection.close()
            self.stdout.write('  ✅ Conexão com servidor de email OK')
        except Exception as e:
            self.stdout.write(f'  ❌ Erro na conexão: {str(e)}')

    def show_help(self):
        """Mostrar ajuda"""
        self.stdout.write(self.style.SUCCESS('=== GERENCIAMENTO DE ALERTAS POR EMAIL ==='))
        self.stdout.write('')
        self.stdout.write('Comandos disponíveis:')
        self.stdout.write('')
        self.stdout.write('📋 Listagem:')
        self.stdout.write('  --list-admins          Listar administradores')
        self.stdout.write('  --status               Mostrar status das configurações')
        self.stdout.write('')
        self.stdout.write('👥 Gerenciamento:')
        self.stdout.write('  --add-admin EMAIL      Adicionar email de administrador')
        self.stdout.write('  --remove-admin EMAIL   Remover email de administrador')
        self.stdout.write('')
        self.stdout.write('🧪 Testes:')
        self.stdout.write('  --test-email EMAIL     Testar envio de email')
        self.stdout.write('')
        self.stdout.write('⚙️  Configuração:')
        self.stdout.write('  --configure-alerts     Configurar alertas por email')
        self.stdout.write('  --set-threshold METRIC WARNING CRITICAL')
        self.stdout.write('  --enable-notifications  Habilitar notificações')
        self.stdout.write('  --disable-notifications Desabilitar notificações')
        self.stdout.write('')
        self.stdout.write('📝 Exemplos:')
        self.stdout.write('  python manage.py configure_email_alerts --add-admin admin@exemplo.com')
        self.stdout.write('  python manage.py configure_email_alerts --test-email admin@exemplo.com')
        self.stdout.write('  python manage.py configure_email_alerts --set-threshold cpu_usage 70 85')

    def validate_email(self, email):
        """Validar formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def check_email_config(self):
        """Verificar se a configuração de email está OK"""
        try:
            return (
                hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST and
                hasattr(settings, 'EMAIL_PORT') and settings.EMAIL_PORT and
                hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL
            )
        except Exception:
            return False

    def get_alert_emails(self):
        """Obter lista de emails de alerta"""
        return cache.get('alert_emails', [])

    def save_alert_emails(self, emails):
        """Salvar lista de emails de alerta"""
        cache.set('alert_emails', emails, 60 * 60 * 24 * 365)  # 1 ano
