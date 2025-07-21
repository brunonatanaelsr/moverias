from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from certificates.models import CertificateTemplate
import os
from django.core.files import File
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria templates padrão para certificados'

    def handle(self, *args, **options):
        # Buscar usuário admin
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('Nenhum usuário admin encontrado. Crie um usuário admin primeiro.')
            )
            return

        # Templates padrão
        templates_data = [
            {
                'name': 'Template Moderno',
                'type': 'workshop',
                'description': 'Template moderno com gradiente azul'
            },
            {
                'name': 'Template Clássico',
                'type': 'course',
                'description': 'Template clássico e elegante'
            },
            {
                'name': 'Template Participação',
                'type': 'participation',
                'description': 'Template para certificados de participação'
            }
        ]

        created_count = 0
        for template_data in templates_data:
            # Verificar se já existe
            if CertificateTemplate.objects.filter(name=template_data['name']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Template "{template_data["name"]}" já existe.')
                )
                continue

            # Criar template
            template = CertificateTemplate.objects.create(
                name=template_data['name'],
                type=template_data['type'],
                is_active=True
            )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✅ Template "{template.name}" criado com sucesso!')
            )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\\n🎉 {created_count} templates criados com sucesso!')
            )
            self.stdout.write(
                self.style.SUCCESS('Acesse /certificates/admin/templates/ para gerenciar os templates.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Nenhum template novo foi criado.')
            )
