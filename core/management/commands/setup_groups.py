# Copilot: migration para criar grupos e permissões iniciais.
# - Criar grupos: Admin, Tecnica, Educadora, Voluntaria.
# - Atribuir permissões de model conforme necessidade.

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from members.models import Beneficiary, Consent
from social.models import SocialAnamnesis
from projects.models import ProjectEnrollment
from evolution.models import EvolutionRecord
from coaching.models import ActionPlan, WheelOfLife


class Command(BaseCommand):
    help = 'Cria grupos e permissões iniciais do sistema'

    def handle(self, *args, **options):
        # Criar grupos
        groups_data = {
            'Admin': 'Administradoras - acesso total',
            'Tecnica': 'Técnicas - acesso completo aos beneficiários',
            'Educadora': 'Educadoras - acesso aos projetos e evoluções',
            'Voluntaria': 'Voluntárias - acesso limitado para consulta'
        }
        
        created_groups = {}
        for group_name, description in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            created_groups[group_name] = group
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Grupo "{group_name}" criado com sucesso')
                )
            else:
                self.stdout.write(f'Grupo "{group_name}" já existe')

        # Definir permissões por grupo
        models_permissions = {
            'Admin': ['add', 'change', 'delete', 'view'],
            'Tecnica': ['add', 'change', 'view'],
            'Educadora': ['add', 'change', 'view'],
            'Voluntaria': ['view']
        }

        models = [
            Beneficiary, Consent, SocialAnamnesis, 
            ProjectEnrollment, EvolutionRecord, ActionPlan, WheelOfLife
        ]

        # Atribuir permissões
        for group_name, permissions_list in models_permissions.items():
            group = created_groups[group_name]
            
            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                
                for perm_type in permissions_list:
                    # Técnicas não podem deletar
                    if group_name == 'Tecnica' and perm_type == 'delete':
                        continue
                    
                    # Educadoras têm acesso limitado
                    if group_name == 'Educadora':
                        # Só podem acessar projetos, evoluções e ações
                        if model not in [ProjectEnrollment, EvolutionRecord, ActionPlan, WheelOfLife]:
                            if perm_type in ['add', 'change']:
                                continue
                    
                    perm_codename = f'{perm_type}_{model._meta.model_name}'
                    try:
                        permission = Permission.objects.get(
                            codename=perm_codename,
                            content_type=content_type
                        )
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Permissão {perm_codename} não encontrada')
                        )

        self.stdout.write(
            self.style.SUCCESS('Grupos e permissões configurados com sucesso!')
        )
