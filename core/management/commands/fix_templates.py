import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige automaticamente problemas comuns do sistema de templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', 
            action='store_true',
            help='Simular correções sem aplicar mudanças'
        )
        parser.add_argument(
            '--backup', 
            action='store_true',
            help='Criar backup antes das correções'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.backup = options['backup']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('=== MODO DRY-RUN: Simulando correções ===')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('=== APLICANDO CORREÇÕES AUTOMÁTICAS ===')
            )
        
        corrections_applied = 0
        
        # 1. Criar templates base faltantes
        corrections_applied += self.create_missing_base_templates()
        
        # 2. Criar templates de fallback
        corrections_applied += self.create_fallback_templates()
        
        # 3. Criar includes ausentes
        corrections_applied += self.fix_missing_includes()
        
        # 4. Criar templates de erro customizados
        corrections_applied += self.create_error_templates()
        
        # Resumo
        if corrections_applied > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nTotal de correções aplicadas: {corrections_applied}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nNenhuma correção necessária. Sistema OK!')
            )

    def create_missing_base_templates(self):
        """Criar templates base faltantes"""
        self.stdout.write('\n1. VERIFICANDO TEMPLATES BASE...')
        
        corrections = 0
        base_templates = [
            'base.html',
            'base_app.html',
            'layouts/base_dashboard.html',
        ]
        
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        
        for template_name in base_templates:
            template_path = templates_dir / template_name
            
            if not template_path.exists():
                self.stdout.write(f'   Template ausente: {template_name}')
                
                if not self.dry_run:
                    template_path.parent.mkdir(parents=True, exist_ok=True)
                    content = self.get_base_template_content(template_name)
                    template_path.write_text(content, encoding='utf-8')
                    corrections += 1
                    self.stdout.write(f'   Criado: {template_name}')
            else:
                self.stdout.write(f'   Existe: {template_name}')
        
        return corrections

    def get_base_template_content(self, template_name):
        """Obter conteúdo para template base"""
        if template_name == 'base_app.html':
            return '''{% extends 'base.html' %}

{% block content %}
<div class="min-h-full">
    <main>
        <div class="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
            {% block app_content %}
            <div class="px-4 py-6 sm:px-0">
                <p class="text-gray-500">Conteúdo da aplicação aqui</p>
            </div>
            {% endblock %}
        </div>
    </main>
</div>
{% endblock %}'''
        
        return '<!-- Template criado automaticamente -->'

    def create_fallback_templates(self):
        """Criar templates de fallback"""
        self.stdout.write('\n2. CRIANDO TEMPLATES DE FALLBACK...')
        
        corrections = 0
        fallback_templates = [
            ('core/index.html', 'Core - Página Inicial'),
            ('dashboard/index.html', 'Dashboard - Início'),
            ('members/list.html', 'Beneficiárias - Lista'),
        ]
        
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        
        for template_path, title in fallback_templates:
            full_path = templates_dir / template_path
            
            if not full_path.exists():
                self.stdout.write(f'   Template ausente: {template_path}')
                
                if not self.dry_run:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    content = self.get_fallback_template_content(title)
                    full_path.write_text(content, encoding='utf-8')
                    corrections += 1
                    self.stdout.write(f'   Criado: {template_path}')
        
        return corrections

    def get_fallback_template_content(self, title):
        """Obter conteúdo para template de fallback"""
        template_content = '''{% extends 'base.html' %}

{% block title %}''' + title + ''' - MoveMarias{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <div class="px-4 py-6 sm:px-0">
        <h1 class="text-2xl font-bold text-gray-900 mb-4">''' + title + '''</h1>
        <p class="text-gray-600">Template criado automaticamente.</p>
    </div>
</div>
{% endblock %}'''
        return template_content

    def fix_missing_includes(self):
        """Corrigir includes ausentes"""
        self.stdout.write('\n3. CORRIGINDO INCLUDES AUSENTES...')
        
        corrections = 0
        includes_dir = Path(settings.BASE_DIR) / 'templates' / 'layouts' / 'includes'
        
        if not self.dry_run:
            includes_dir.mkdir(parents=True, exist_ok=True)
        
        nav_file = includes_dir / 'navigation.html'
        if not nav_file.exists():
            self.stdout.write('   Navigation include ausente')
            
            if not self.dry_run:
                nav_content = '''<!-- Navigation placeholder -->
<li>
    <div class="text-xs font-semibold leading-6 text-pink-200">Menu Principal</div>
    <ul role="list" class="-mx-2 mt-2 space-y-1">
        <li>
            <a href="{% url 'core:home' %}" 
               class="text-pink-200 hover:text-white hover:bg-pink-700 group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold">
                🏠 Início
            </a>
        </li>
    </ul>
</li>'''
                nav_file.write_text(nav_content, encoding='utf-8')
                corrections += 1
                self.stdout.write('   Criado navigation include')
        
        return corrections

    def create_error_templates(self):
        """Criar templates de erro customizados"""
        self.stdout.write('\n4. CRIANDO TEMPLATES DE ERRO...')
        
        corrections = 0
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        
        error_templates = ['404.html', '500.html']
        
        for error_template in error_templates:
            template_path = templates_dir / error_template
            
            if not template_path.exists():
                self.stdout.write(f'   Template de erro ausente: {error_template}')
                
                if not self.dry_run:
                    content = self.get_error_template_content(error_template)
                    template_path.write_text(content, encoding='utf-8')
                    corrections += 1
                    self.stdout.write(f'   Criado: {error_template}')
        
        return corrections

    def get_error_template_content(self, error_file):
        """Obter conteúdo para template de erro"""
        error_code = error_file.replace('.html', '').upper()
        
        template_content = '''{% extends 'base.html' %}

{% block title %}Erro ''' + error_code + ''' - MoveMarias{% endblock %}

{% block content %}
<div class="min-h-full flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full text-center">
        <h1 class="text-6xl font-bold text-gray-900">''' + error_code + '''</h1>
        <h2 class="mt-4 text-2xl font-semibold text-gray-600">Erro ''' + error_code + '''</h2>
        <div class="mt-8">
            <a href="{% url 'core:home' %}" 
               class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-pink-600 hover:bg-pink-700">
                Voltar ao início
            </a>
        </div>
    </div>
</div>
{% endblock %}'''
        
        return template_content
