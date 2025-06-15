from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from members.models import Beneficiary
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados de exemplo para demonstração do sistema'

    def handle(self, *args, **options):
        # Criar usuárias técnicas de exemplo
        tecnica_group = Group.objects.get(name='Tecnica')
        
        user_maria, created = User.objects.get_or_create(
            username='maria.silva',
            defaults={
                'email': 'maria.silva@movemarias.org',
                'first_name': 'Maria',
                'last_name': 'Silva',
                'is_staff': True
            }
        )
        if created:
            user_maria.set_password('movemarias2025')
            user_maria.save()
            user_maria.groups.add(tecnica_group)
            self.stdout.write(self.style.SUCCESS('Usuária Maria Silva criada'))

        # Criar beneficiárias de exemplo
        beneficiaries_data = [
            {
                'full_name': 'Joana Santos',
                'dob': date(1990, 3, 15),
                'nis': '12345678901',
                'phone_1': '(11) 98765-4321',
                'phone_2': '(11) 3456-7890',
                'rg': '12.345.678-9',
                'cpf': '123.456.789-01',
                'address': 'Rua das Flores, 123, Apt 45',
                'neighbourhood': 'Cidade Tiradentes',
                'reference': 'Próximo ao mercado central'
            },
            {
                'full_name': 'Rosa Silva',
                'dob': date(1985, 7, 22),
                'nis': '98765432109',
                'phone_1': '(11) 91234-5678',
                'phone_2': '',
                'rg': '98.765.432-1',
                'cpf': '987.654.321-09',
                'address': 'Av. Principal, 456',
                'neighbourhood': 'Guaianases',
                'reference': 'Em frente à escola municipal'
            },
            {
                'full_name': 'Carmen Oliveira',
                'dob': date(1978, 11, 5),
                'nis': '11122233344',
                'phone_1': '(11) 95555-1234',
                'phone_2': '(11) 2222-3333',
                'rg': '11.222.333-4',
                'cpf': '111.222.333-44',
                'address': 'Rua do Sol, 789',
                'neighbourhood': 'Itaquera',
                'reference': 'Casa azul na esquina'
            }
        ]

        for beneficiary_data in beneficiaries_data:
            beneficiary, created = Beneficiary.objects.get_or_create(
                full_name=beneficiary_data['full_name'],
                defaults=beneficiary_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Beneficiária {beneficiary.full_name} criada')
                )

        self.stdout.write(
            self.style.SUCCESS('\n✅ Dados de exemplo criados com sucesso!')
        )
        self.stdout.write('📧 Credenciais de acesso:')
        self.stdout.write('   Admin: admin / admin123')
        self.stdout.write('   Técnica: maria.silva / movemarias2025')
        self.stdout.write('🌐 Acesse: http://127.0.0.1:8000')
