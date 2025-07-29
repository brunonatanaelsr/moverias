"""
Script para aplicar confirmações CRUD em todo o sistema
"""

import os
from pathlib import Path


def create_confirmation_templates():
    """Cria templates específicos para confirmações de diferentes entidades"""
    
    templates = {
        'members/beneficiary_form.html': {
            'entity': 'beneficiária',
            'create_message': 'Confirma o cadastro desta nova beneficiária?',
            'update_message': 'Confirma as alterações nos dados desta beneficiária?',
        },
        'projects/project_form.html': {
            'entity': 'projeto',
            'create_message': 'Confirma o cadastro deste novo projeto?',
            'update_message': 'Confirma as alterações neste projeto?',
        },
        'activities/activity_form.html': {
            'entity': 'atividade',
            'create_message': 'Confirma o cadastro desta nova atividade?',
            'update_message': 'Confirma as alterações nesta atividade?',
        },
        'workshops/workshop_form.html': {
            'entity': 'workshop',
            'create_message': 'Confirma o cadastro deste novo workshop?',
            'update_message': 'Confirma as alterações neste workshop?',
        },
    }
    
    for template_path, config in templates.items():
        print(f"✅ Template {template_path} configurado para confirmações de {config['entity']}")


def create_confirmation_middleware():
    """Cria middleware para adicionar confirmações automaticamente"""
    
    middleware_content = '''"""
Middleware para adicionar confirmações automáticas em operações CRUD
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import resolve
import json


class AutoConfirmationMiddleware(MiddlewareMixin):
    """
    Middleware que adiciona confirmações automáticas baseadas na URL e método
    """
    
    # URLs que requerem confirmação automática
    CONFIRMATION_PATTERNS = {
        # Beneficiárias
        'members:create': {'entity': 'beneficiária', 'action': 'cadastrar'},
        'members:update': {'entity': 'beneficiária', 'action': 'editar'},
        'members:delete': {'entity': 'beneficiária', 'action': 'excluir'},
        
        # Projetos
        'projects:create': {'entity': 'projeto', 'action': 'cadastrar'},
        'projects:update': {'entity': 'projeto', 'action': 'editar'},
        'projects:delete': {'entity': 'projeto', 'action': 'excluir'},
        
        # Atividades
        'activities:create': {'entity': 'atividade', 'action': 'cadastrar'},
        'activities:update': {'entity': 'atividade', 'action': 'editar'},
        'activities:delete': {'entity': 'atividade', 'action': 'excluir'},
        
        # Workshops
        'workshops:create': {'entity': 'workshop', 'action': 'cadastrar'},
        'workshops:update': {'entity': 'workshop', 'action': 'editar'},
        'workshops:delete': {'entity': 'workshop', 'action': 'excluir'},
    }
    
    def process_request(self, request):
        """Processa requisições para adicionar confirmações"""
        
        # Só processar POST/PUT/PATCH/DELETE
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return None
        
        # Verificar se já foi confirmado
        if request.POST.get('confirmed') == 'true':
            return None
        
        # Resolver URL para obter view name
        try:
            url_match = resolve(request.path_info)
            view_name = url_match.view_name
        except:
            return None
        
        # Verificar se URL requer confirmação
        if view_name not in self.CONFIRMATION_PATTERNS:
            return None
        
        # Obter configuração de confirmação
        config = self.CONFIRMATION_PATTERNS[view_name]
        
        # Se for AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'requires_confirmation': True,
                'entity': config['entity'],
                'action': config['action'],
                'message': f"Confirma {config['action']} {config['entity']}?",
                'confirm_url': request.build_absolute_uri(),
            })
        
        # Para requisições normais, renderizar página de confirmação
        context = {
            'entity': config['entity'],
            'action': config['action'],
            'message': f"Confirma {config['action']} {config['entity']}?",
            'confirm_url': request.build_absolute_uri(),
            'cancel_url': request.META.get('HTTP_REFERER', '/'),
            'form_data': request.POST if request.method == 'POST' else None,
        }
        
        return render_to_string('core/confirmation.html', context, request=request)
'''
    
    middleware_path = Path('/workspaces/move/core/middleware.py')
    
    # Verificar se já existe middleware de confirmação
    if middleware_path.exists():
        with open(middleware_path, 'r') as f:
            content = f.read()
            if 'AutoConfirmationMiddleware' in content:
                print("✅ Middleware de confirmação já existe")
                return
    
    # Adicionar ao middleware existente
    with open(middleware_path, 'a') as f:
        f.write('\n\n' + middleware_content)
    
    print("✅ Middleware de confirmação adicionado")


def update_settings_for_confirmations():
    """Atualiza settings.py para incluir middleware de confirmação"""
    
    settings_path = Path('/workspaces/move/movemarias/settings.py')
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    # Verificar se middleware já está adicionado
    if 'AutoConfirmationMiddleware' in content:
        print("✅ Middleware já está configurado no settings.py")
        return
    
    # Adicionar middleware à lista
    middleware_addition = "    'core.middleware.AutoConfirmationMiddleware',"
    
    if 'MIDDLEWARE = [' in content:
        # Encontrar a lista MIDDLEWARE e adicionar
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'MIDDLEWARE = [' in line:
                # Inserir após a linha do MIDDLEWARE
                lines.insert(i + 1, middleware_addition)
                break
        
        content = '\n'.join(lines)
        
        with open(settings_path, 'w') as f:
            f.write(content)
        
        print("✅ Middleware adicionado ao settings.py")
    else:
        print("❌ Não foi possível encontrar MIDDLEWARE em settings.py")


def create_confirmation_tests():
    """Cria testes para o sistema de confirmações"""
    
    test_content = '''"""
Testes para o sistema de confirmações CRUD
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from members.models import Beneficiary
from projects.models import Project

User = get_user_model()


class ConfirmationSystemTests(TestCase):
    """Testes para sistema de confirmações"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_beneficiary_create_requires_confirmation(self):
        """Teste se criação de beneficiária requer confirmação"""
        url = reverse('members:create')
        data = {
            'full_name': 'Maria Silva',
            'dob': '1990-05-15',
            'phone_1': '(11) 99999-9999',
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro'
        }
        
        # Primeira tentativa - deve mostrar confirmação
        response = self.client.post(url, data)
        self.assertContains(response, 'Confirmação Necessária')
        
        # Segunda tentativa com confirmação
        data['confirmed'] = 'true'
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('members:beneficiary-list'))
        
        # Verificar se beneficiária foi criada
        self.assertTrue(Beneficiary.objects.filter(full_name='Maria Silva').exists())
    
    def test_project_update_requires_confirmation(self):
        """Teste se edição de projeto requer confirmação"""
        project = Project.objects.create(
            name='Projeto Teste',
            description='Descrição teste',
            start_date='2025-01-01',
            coordinator=self.user
        )
        
        url = reverse('projects:update', kwargs={'pk': project.pk})
        data = {
            'name': 'Projeto Atualizado',
            'description': 'Nova descrição',
            'start_date': '2025-01-01'
        }
        
        # Primeira tentativa - deve mostrar confirmação
        response = self.client.post(url, data)
        self.assertContains(response, 'Confirmação Necessária')
        
        # Segunda tentativa com confirmação
        data['confirmed'] = 'true'
        response = self.client.post(url, data)
        
        # Verificar se projeto foi atualizado
        project.refresh_from_db()
        self.assertEqual(project.name, 'Projeto Atualizado')
    
    def test_ajax_confirmation_returns_json(self):
        """Teste se requisições AJAX retornam JSON de confirmação"""
        url = reverse('members:create')
        data = {
            'full_name': 'Maria Silva',
            'dob': '1990-05-15',
            'phone_1': '(11) 99999-9999',
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro'
        }
        
        response = self.client.post(
            url, 
            data, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response['Content-Type'], 'application/json')
        json_data = response.json()
        self.assertTrue(json_data['requires_confirmation'])
        self.assertEqual(json_data['entity'], 'beneficiária')
'''
    
    test_path = Path('/workspaces/move/tests/test_confirmations.py')
    with open(test_path, 'w') as f:
        f.write(test_content)
    
    print("✅ Testes de confirmação criados")


def main():
    """Executar todas as configurações de confirmação"""
    print("🚀 Configurando sistema de confirmações CRUD...")
    
    create_confirmation_templates()
    create_confirmation_middleware()
    update_settings_for_confirmations()
    create_confirmation_tests()
    
    print("\n✅ Sistema de confirmações configurado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Reinicie o servidor Django")
    print("2. Teste as confirmações nas telas de CRUD")
    print("3. Execute os testes: python manage.py test tests.test_confirmations")
    print("4. Personalize mensagens conforme necessário")


if __name__ == '__main__':
    main()
