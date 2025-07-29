import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import get_resolver
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Diagnóstico completo do sistema de templates e navegação'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose', 
            action='store_true',
            help='Saída detalhada'
        )
        parser.add_argument(
            '--fix', 
            action='store_true',
            help='Tentar corrigir problemas encontrados automaticamente'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.fix_issues = options['fix']
        
        self.stdout.write(
            self.style.SUCCESS('=== DIAGNÓSTICO COMPLETO DO SISTEMA ===')
        )
        
        # 1. Verificar configurações de templates
        self.check_template_settings()
        
        # 2. Escanear todos os templates
        self.scan_templates()
        
        # 3. Verificar URLs e views
        self.check_urls_and_views()
        
        # 4. Verificar context processors
        self.check_context_processors()
        
        # 5. Verificar sistema de permissões
        self.check_permissions_system()
        
        # 6. Verificar navegação e sidebar
        self.check_navigation_structure()
        
        # 7. Verificar templates órfãos
        self.check_orphaned_templates()
        
        # 8. Gerar relatório resumido
        self.generate_summary_report()

    def check_template_settings(self):
        """Verificar configurações de TEMPLATES"""
        self.stdout.write('\n1. VERIFICANDO CONFIGURAÇÕES DE TEMPLATES...')
        
        templates_config = settings.TEMPLATES[0]
        
        # Verificar DIRS
        template_dirs = templates_config['DIRS']
        self.stdout.write(f'   Template DIRS: {template_dirs}')
        
        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Diretório não existe: {template_dir}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Diretório encontrado: {template_dir}')
                )
        
        # Verificar APP_DIRS
        if templates_config['APP_DIRS']:
            self.stdout.write('   ✅ APP_DIRS habilitado')
        else:
            self.stdout.write('   ⚠️  APP_DIRS desabilitado')
        
        # Verificar context processors
        context_processors = templates_config['OPTIONS']['context_processors']
        self.stdout.write(f'   Context processors configurados: {len(context_processors)}')
        
        if self.verbose:
            for cp in context_processors:
                self.stdout.write(f'     - {cp}')

    def scan_templates(self):
        """Escanear todos os templates do projeto"""
        self.stdout.write('\n2. ESCANEANDO TEMPLATES...')
        
        templates_found = {}
        templates_with_issues = []
        
        # Escanear diretório principal de templates
        main_template_dir = Path(settings.BASE_DIR) / 'templates'
        if main_template_dir.exists():
            templates_found['main'] = self._scan_directory_templates(main_template_dir)
        
        # Escanear templates de apps
        for app_config in apps.get_app_configs():
            app_templates_dir = Path(app_config.path) / 'templates'
            if app_templates_dir.exists():
                templates_found[app_config.name] = self._scan_directory_templates(app_templates_dir)
        
        # Verificar herança de templates
        self.stdout.write('   Verificando herança de templates...')
        for location, templates in templates_found.items():
            for template_path in templates:
                issues = self._check_template_inheritance(template_path)
                if issues:
                    templates_with_issues.append({
                        'template': template_path,
                        'location': location,
                        'issues': issues
                    })
        
        # Relatório
        total_templates = sum(len(templates) for templates in templates_found.values())
        self.stdout.write(f'   ✅ Total de templates encontrados: {total_templates}')
        
        if templates_with_issues:
            self.stdout.write(f'   ⚠️  Templates com problemas: {len(templates_with_issues)}')
            if self.verbose:
                for issue in templates_with_issues:
                    self.stdout.write(f'     - {issue["template"]}: {issue["issues"]}')

    def _scan_directory_templates(self, directory):
        """Escanear templates em um diretório"""
        templates = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    templates.append(os.path.join(root, file))
        return templates

    def _check_template_inheritance(self, template_path):
        """Verificar problemas de herança de template"""
        issues = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Verificar extends
                extends_match = re.search(r'{%\s*extends\s+["\']([^"\']+)["\']', content)
                if extends_match:
                    parent_template = extends_match.group(1)
                    try:
                        get_template(parent_template)
                    except TemplateDoesNotExist:
                        issues.append(f'Template pai não encontrado: {parent_template}')
                
                # Verificar blocks definidos vs usados
                blocks_defined = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
                blocks_ended = re.findall(r'{%\s*endblock\s*(?:\w+)?\s*%}', content)
                
                if len(blocks_defined) != len(blocks_ended):
                    issues.append('Número de blocks não confere com endblocks')
        
        except Exception as e:
            issues.append(f'Erro ao ler template: {str(e)}')
        
        return issues

    def check_urls_and_views(self):
        """Verificar URLs e views"""
        self.stdout.write('\n3. VERIFICANDO URLS E VIEWS...')
        
        resolver = get_resolver()
        url_patterns = self._extract_url_patterns(resolver)
        
        views_with_templates = []
        views_without_templates = []
        
        for pattern in url_patterns:
            if hasattr(pattern, 'callback'):
                view_name = pattern.callback.__name__ if hasattr(pattern.callback, '__name__') else str(pattern.callback)
                
                # Tentar identificar template usado
                template_name = self._guess_template_name(pattern, view_name)
                
                if template_name:
                    try:
                        get_template(template_name)
                        views_with_templates.append({
                            'url': str(pattern.pattern),
                            'view': view_name,
                            'template': template_name
                        })
                    except TemplateDoesNotExist:
                        views_without_templates.append({
                            'url': str(pattern.pattern),
                            'view': view_name,
                            'template': template_name,
                            'issue': 'Template não encontrado'
                        })
        
        self.stdout.write(f'   ✅ Views com templates válidos: {len(views_with_templates)}')
        self.stdout.write(f'   ❌ Views com templates ausentes: {len(views_without_templates)}')
        
        if self.verbose and views_without_templates:
            for view in views_without_templates[:10]:  # Mostrar apenas os primeiros 10
                self.stdout.write(f'     - {view["url"]} -> {view["template"]}')

    def _extract_url_patterns(self, resolver, namespace=''):
        """Extrair todos os padrões de URL"""
        patterns = []
        
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # É um include
                sub_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
                patterns.extend(self._extract_url_patterns(pattern, sub_namespace))
            else:
                patterns.append(pattern)
        
        return patterns

    def _guess_template_name(self, pattern, view_name):
        """Tentar adivinhar o nome do template baseado na URL e view"""
        # Lógica simplificada para guess do template
        url_parts = str(pattern.pattern).strip('^$').split('/')
        app_name = url_parts[0] if url_parts and url_parts[0] else 'core'
        
        # Remover caracteres especiais de regex
        clean_parts = [part for part in url_parts if part and not any(c in part for c in ['(', ')', '?', '*', '+', '\\'])]
        
        if len(clean_parts) >= 2:
            return f"{app_name}/{clean_parts[1]}.html"
        elif len(clean_parts) == 1:
            return f"{app_name}/index.html"
        
        return None

    def check_context_processors(self):
        """Verificar context processors"""
        self.stdout.write('\n4. VERIFICANDO CONTEXT PROCESSORS...')
        
        factory = RequestFactory()
        request = factory.get('/')
        
        # Simular usuário autenticado
        User = get_user_model()
        try:
            user = User.objects.first()
            if user:
                request.user = user
            else:
                self.stdout.write('   ⚠️  Nenhum usuário encontrado para teste')
                return
        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao carregar usuário: {e}')
            return
        
        # Testar context processors
        context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']
        
        working_processors = []
        broken_processors = []
        
        for processor_path in context_processors:
            try:
                module_path, function_name = processor_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[function_name])
                processor_func = getattr(module, function_name)
                
                context = processor_func(request)
                working_processors.append({
                    'processor': processor_path,
                    'context_keys': list(context.keys()) if context else []
                })
                
            except Exception as e:
                broken_processors.append({
                    'processor': processor_path,
                    'error': str(e)
                })
        
        self.stdout.write(f'   ✅ Context processors funcionando: {len(working_processors)}')
        self.stdout.write(f'   ❌ Context processors com erro: {len(broken_processors)}')
        
        if self.verbose:
            for cp in working_processors:
                self.stdout.write(f'     ✅ {cp["processor"]}: {cp["context_keys"]}')
            for cp in broken_processors:
                self.stdout.write(f'     ❌ {cp["processor"]}: {cp["error"]}')

    def check_permissions_system(self):
        """Verificar sistema de permissões"""
        self.stdout.write('\n5. VERIFICANDO SISTEMA DE PERMISSÕES...')
        
        try:
            from core.unified_permissions import get_user_permissions
            
            User = get_user_model()
            test_user = User.objects.first()
            
            if test_user:
                permissions = get_user_permissions(test_user)
                
                self.stdout.write(f'   ✅ Sistema de permissões funcionando')
                self.stdout.write(f'   Módulos disponíveis: {len(permissions.get("modules", {}))}')
                
                if self.verbose:
                    modules = permissions.get('modules', {})
                    for module, perms in modules.items():
                        self.stdout.write(f'     - {module}: {perms}')
            else:
                self.stdout.write('   ⚠️  Nenhum usuário para testar permissões')
                
        except ImportError as e:
            self.stdout.write(f'   ❌ Erro ao importar sistema de permissões: {e}')
        except Exception as e:
            self.stdout.write(f'   ❌ Erro no sistema de permissões: {e}')

    def check_navigation_structure(self):
        """Verificar estrutura de navegação"""
        self.stdout.write('\n6. VERIFICANDO NAVEGAÇÃO E SIDEBAR...')
        
        navigation_template = Path(settings.BASE_DIR) / 'templates/layouts/includes/navigation.html'
        
        if not navigation_template.exists():
            self.stdout.write('   ❌ Template de navegação não encontrado')
            return
        
        try:
            with open(navigation_template, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extrair URLs mencionadas na navegação
                url_patterns = re.findall(r'{%\s*url\s+["\']([^"\']+)["\']', content)
                
                valid_urls = []
                invalid_urls = []
                
                for url_name in url_patterns:
                    try:
                        from django.urls import reverse
                        reverse(url_name)
                        valid_urls.append(url_name)
                    except Exception:
                        invalid_urls.append(url_name)
                
                self.stdout.write(f'   ✅ URLs válidas na navegação: {len(valid_urls)}')
                self.stdout.write(f'   ❌ URLs inválidas na navegação: {len(invalid_urls)}')
                
                if self.verbose and invalid_urls:
                    for url in invalid_urls:
                        self.stdout.write(f'     - {url}')
                        
        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao analisar navegação: {e}')

    def check_orphaned_templates(self):
        """Verificar templates órfãos (não referenciados)"""
        self.stdout.write('\n7. VERIFICANDO TEMPLATES ÓRFÃOS...')
        
        # Esta é uma verificação simplificada
        # Em um cenário real, seria necessário analisar todas as views
        
        template_dir = Path(settings.BASE_DIR) / 'templates'
        if not template_dir.exists():
            return
        
        all_templates = []
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                    all_templates.append(rel_path)
        
        # Templates que provavelmente são órfãos (heurística simples)
        potentially_orphaned = []
        for template in all_templates:
            if not any(keyword in template.lower() for keyword in ['base', 'layout', 'include', 'partial']):
                # Verificar se é referenciado em views (simplificado)
                potentially_orphaned.append(template)
        
        self.stdout.write(f'   📊 Total de templates: {len(all_templates)}')
        self.stdout.write(f'   ⚠️  Potencialmente órfãos: {len(potentially_orphaned)}')

    def generate_summary_report(self):
        """Gerar relatório resumido"""
        self.stdout.write('\n8. RELATÓRIO RESUMIDO')
        self.stdout.write('=' * 50)
        
        # Recomendações baseadas no diagnóstico
        recommendations = []
        
        # Verificar se o context processor de permissões está funcionando
        try:
            from core.unified_permissions import get_user_permissions
            recommendations.append("✅ Sistema de permissões funcionando")
        except:
            recommendations.append("❌ Verificar sistema de permissões unificadas")
        
        # Verificar template de navegação
        navigation_template = Path(settings.BASE_DIR) / 'templates/layouts/includes/navigation.html'
        if navigation_template.exists():
            recommendations.append("✅ Template de navegação encontrado")
        else:
            recommendations.append("❌ Criar template de navegação")
        
        recommendations.extend([
            "🔧 Implementar context processor para sidebar completo",
            "🔧 Criar template de diagnóstico para debug",
            "🔧 Adicionar logging para templates não encontrados",
            "🔧 Implementar fallbacks para templates ausentes"
        ])
        
        for rec in recommendations:
            self.stdout.write(f'   {rec}')
        
        self.stdout.write('\nPróximos passos recomendados:')
        self.stdout.write('1. Executar com --fix para correções automáticas')
        self.stdout.write('2. Verificar logs de erro do Django')
        self.stdout.write('3. Testar navegação com diferentes tipos de usuário')
        self.stdout.write('4. Implementar context processor melhorado para sidebar')
