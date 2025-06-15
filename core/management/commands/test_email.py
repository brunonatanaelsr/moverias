from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Testa o envio de email SMTP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Email do destinatário para teste',
            required=True
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='Teste de Email - Move Marias',
            help='Assunto do email de teste'
        )

    def handle(self, *args, **options):
        to_email = options['to']
        subject = options['subject']
        
        message = """
        Este é um email de teste do sistema Move Marias.
        
        Se você recebeu este email, significa que a configuração SMTP está funcionando corretamente.
        
        Configurações atuais:
        - EMAIL_BACKEND: {backend}
        - EMAIL_HOST: {host}
        - EMAIL_PORT: {port}
        - EMAIL_USE_TLS: {tls}
        - DEFAULT_FROM_EMAIL: {from_email}
        
        Data/Hora: {datetime}
        
        ---
        Sistema Move Marias
        """.format(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            tls=settings.EMAIL_USE_TLS,
            from_email=settings.DEFAULT_FROM_EMAIL,
            datetime=timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        )
        
        try:
            self.stdout.write(
                self.style.WARNING(f'Enviando email de teste para: {to_email}')
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Email enviado com sucesso para {to_email}!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao enviar email: {str(e)}')
            )
            self.stdout.write(
                self.style.WARNING('Verifique as configurações SMTP no arquivo .env')
            )


# Adicionar import necessário
from django.utils import timezone
