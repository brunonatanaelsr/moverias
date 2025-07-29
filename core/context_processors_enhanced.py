from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.apps import apps
from django.contrib.auth.models import Group
import logging

logger = logging.getLogger(__name__)

def enhanced_sidebar_context(request):
    """
    Context processor melhorado para sidebar completo
    Garante que todos os módulos sejam exibidos corretamente
    """
    if not request.user.is_authenticated:
        return {'sidebar_modules': []}
    
    # Módulos base do sistema
    modules = [
        {
            'name': 'Dashboard',
            'icon': 'dashboard',
            'url_name': 'dashboard:home',
            'permission': None,  # Sempre visível para usuários autenticados
            'children': [
                {'name': 'Visão Geral', 'url_name': 'dashboard:home'},
                {'name': 'Beneficiárias', 'url_name': 'dashboard:beneficiaries-list'},
                {'name': 'Relatórios', 'url_name': 'dashboard:reports'},
                {'name': 'Relatórios Personalizados', 'url_name': 'dashboard:custom-reports'},
            ]
        },
        {
            'name': 'Beneficiárias',
            'icon': 'users',
            'url_name': 'members:list',
            'permission': 'members.view_beneficiary',
            'children': [
                {'name': 'Lista de Beneficiárias', 'url_name': 'members:list'},
                {'name': 'Cadastrar Beneficiária', 'url_name': 'members:create'},
                {'name': 'Importar Dados', 'url_name': 'members:import'},
                {'name': 'Relatórios', 'url_name': 'members:reports'},
            ]
        },
        {
            'name': 'Anamnese Social',
            'icon': 'clipboard-list',
            'url_name': 'social:list',
            'permission': 'social.view_socialanamnesis',
            'children': [
                {'name': 'Lista de Anamneses', 'url_name': 'social:list'},
                {'name': 'Nova Anamnese', 'url_name': 'social:create'},
                {'name': 'Relatórios', 'url_name': 'social:reports'},
            ]
        },
        {
            'name': 'Projetos',
            'icon': 'folder',
            'url_name': 'projects:list',
            'permission': 'projects.view_project',
            'children': [
                {'name': 'Lista de Projetos', 'url_name': 'projects:list'},
                {'name': 'Criar Projeto', 'url_name': 'projects:create'},
                {'name': 'Inscrições', 'url_name': 'projects:enrollments'},
                {'name': 'Relatórios', 'url_name': 'projects:reports'},
            ]
        },
        {
            'name': 'Coaching',
            'icon': 'chart-bar',
            'url_name': 'coaching:list',
            'permission': 'coaching.view_actionplan',
            'children': [
                {'name': 'Planos de Ação', 'url_name': 'coaching:list'},
                {'name': 'Roda da Vida', 'url_name': 'coaching:wheel_of_life'},
                {'name': 'Sessões', 'url_name': 'coaching:sessions'},
                {'name': 'Relatórios', 'url_name': 'coaching:reports'},
            ]
        },
        {
            'name': 'Evolução',
            'icon': 'trending-up',
            'url_name': 'evolution:list',
            'permission': 'evolution.view_evolutionrecord',
            'children': [
                {'name': 'Registros de Evolução', 'url_name': 'evolution:list'},
                {'name': 'Novo Registro', 'url_name': 'evolution:create'},
                {'name': 'Análises', 'url_name': 'evolution:analysis'},
                {'name': 'Relatórios', 'url_name': 'evolution:reports'},
            ]
        },
        {
            'name': 'Workshops',
            'icon': 'academic-cap',
            'url_name': 'workshops:list',
            'permission': 'workshops.view_workshop',
            'children': [
                {'name': 'Lista de Workshops', 'url_name': 'workshops:list'},
                {'name': 'Criar Workshop', 'url_name': 'workshops:create'},
                {'name': 'Participantes', 'url_name': 'workshops:participants'},
                {'name': 'Certificados', 'url_name': 'workshops:certificates'},
            ]
        },
        {
            'name': 'Certificados',
            'icon': 'badge-check',
            'url_name': 'certificates:list',
            'permission': 'certificates.view_certificate',
            'children': [
                {'name': 'Lista de Certificados', 'url_name': 'certificates:list'},
                {'name': 'Gerar Certificado', 'url_name': 'certificates:create'},
                {'name': 'Templates', 'url_name': 'certificates:templates'},
                {'name': 'Relatórios', 'url_name': 'certificates:reports'},
            ]
        },
        {
            'name': 'Notificações',
            'icon': 'bell',
            'url_name': 'notifications:list',
            'permission': 'notifications.view_notification',
            'children': [
                {'name': 'Todas as Notificações', 'url_name': 'notifications:list'},
                {'name': 'Criar Notificação', 'url_name': 'notifications:create'},
                {'name': 'Configurações', 'url_name': 'notifications:settings'},
            ]
        },
        {
            'name': 'Recursos Humanos',
            'icon': 'user-group',
            'url_name': 'hr:dashboard',
            'permission': 'hr.view_employee',
            'children': [
                {'name': 'Dashboard RH', 'url_name': 'hr:dashboard'},
                {'name': 'Funcionários', 'url_name': 'hr:employees'},
                {'name': 'Contratos', 'url_name': 'hr:contracts'},
                {'name': 'Relatórios', 'url_name': 'hr:reports'},
            ]
        },
        {
            'name': 'Tarefas',
            'icon': 'clipboard-check',
            'url_name': 'tasks:board',
            'permission': 'tasks.view_task',
            'children': [
                {'name': 'Quadro Kanban', 'url_name': 'tasks:board'},
                {'name': 'Minhas Tarefas', 'url_name': 'tasks:my_tasks'},
                {'name': 'Criar Tarefa', 'url_name': 'tasks:create'},
                {'name': 'Relatórios', 'url_name': 'tasks:reports'},
            ]
        },
        {
            'name': 'Chat',
            'icon': 'chat',
            'url_name': 'chat:room_list',
            'permission': 'chat.view_chatroom',
            'children': [
                {'name': 'Salas de Chat', 'url_name': 'chat:room_list'},
                {'name': 'Mensagens', 'url_name': 'chat:messages'},
                {'name': 'Configurações', 'url_name': 'chat:settings'},
            ]
        },
        {
            'name': 'Comunicação',
            'icon': 'megaphone',
            'url_name': 'communication:dashboard',
            'permission': 'communication.view_announcement',
            'children': [
                {'name': 'Dashboard', 'url_name': 'communication:dashboard'},
                {'name': 'Comunicados', 'url_name': 'communication:announcements'},
                {'name': 'Eventos', 'url_name': 'communication:events'},
                {'name': 'Newsletter', 'url_name': 'communication:newsletter'},
            ]
        },
        {
            'name': 'Atividades',
            'icon': 'calendar',
            'url_name': 'activities:list',
            'permission': 'activities.view_activity',
            'children': [
                {'name': 'Lista de Atividades', 'url_name': 'activities:list'},
                {'name': 'Nova Atividade', 'url_name': 'activities:create'},
                {'name': 'Participações', 'url_name': 'activities:participations'},
                {'name': 'Relatórios', 'url_name': 'activities:reports'},
            ]
        },
    ]
    
    # Módulos administrativos (apenas para staff/admin)
    if request.user.is_staff or request.user.is_superuser:
        admin_modules = [
            {
                'name': 'Administração',
                'icon': 'cog',
                'url_name': 'admin:index',
                'permission': None,
                'children': [
                    {'name': 'Painel Admin', 'url_name': 'admin:index'},
                    {'name': 'Usuários', 'url_name': 'users:list'},
                    {'name': 'Grupos', 'url_name': 'admin:auth_group_changelist'},
                    {'name': 'Permissões', 'url_name': 'admin:auth_permission_changelist'},
                ]
            },
            {
                'name': 'Sistema',
                'icon': 'server',
                'url_name': 'core:diagnostics',
                'permission': None,
                'children': [
                    {'name': 'Diagnóstico', 'url_name': 'core:diagnostics'},
                    {'name': 'Logs', 'url_name': 'core:logs'},
                    {'name': 'Configurações', 'url_name': 'core:settings'},
                ]
            }
        ]
        modules.extend(admin_modules)
    
    # Filtrar módulos baseado nas permissões do usuário
    accessible_modules = []
    
    for module in modules:
        # Verificar permissão do módulo principal
        if module['permission'] and not request.user.has_perm(module['permission']):
            # Verificar se é admin/staff para módulos administrativos
            if module['name'] in ['Administração', 'Sistema']:
                if not (request.user.is_staff or request.user.is_superuser):
                    continue
            else:
                continue
        
        # Verificar se a URL existe
        try:
            if module['url_name']:
                reverse(module['url_name'])
            module['url_exists'] = True
        except NoReverseMatch:
            module['url_exists'] = False
            logger.warning(f"URL não encontrada para módulo {module['name']}: {module['url_name']}")
        
        # Filtrar children baseado em permissões e URLs existentes
        accessible_children = []
        for child in module.get('children', []):
            try:
                reverse(child['url_name'])
                child['url_exists'] = True
                accessible_children.append(child)
            except NoReverseMatch:
                child['url_exists'] = False
                logger.warning(f"URL não encontrada para submenu {child['name']}: {child['url_name']}")
        
        module['children'] = accessible_children
        accessible_modules.append(module)
    
    # Informações adicionais do usuário para o sidebar
    user_info = {
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'groups': list(request.user.groups.values_list('name', flat=True)),
    }
    
    # Contadores para badges (notificações, tarefas pendentes, etc.)
    counters = get_sidebar_counters(request.user)
    
    return {
        'sidebar_modules': accessible_modules,
        'sidebar_user_info': user_info,
        'sidebar_counters': counters,
    }

def get_sidebar_counters(user):
    """
    Obter contadores para badges do sidebar
    """
    counters = {}
    
    try:
        # Notificações não lidas
        from notifications.models import Notification
        counters['notifications'] = Notification.objects.filter(
            recipient=user,
            status='pending'
        ).count()
    except:
        counters['notifications'] = 0
    
    try:
        # Tarefas pendentes
        from tasks.models import Task
        counters['tasks'] = Task.objects.filter(
            assigned_to=user,
            status='pending'
        ).count()
    except:
        counters['tasks'] = 0
    
    try:
        # Mensagens não lidas do chat
        from chat.models import ChatMessage
        counters['messages'] = ChatMessage.objects.filter(
            room__participants=user,
            is_read=False
        ).exclude(sender=user).count()
    except:
        counters['messages'] = 0
    
    return counters

def enhanced_navigation_context(request):
    """
    Context processor aprimorado para navegação
    Inclui informações de debugging e fallbacks
    """
    context = sidebar_context_processor(request)
    
    # Adicionar informações de debugging em modo DEBUG
    if settings.DEBUG:
        context['navigation_debug'] = {
            'total_modules': len(context['sidebar_modules']),
            'user_permissions_count': request.user.get_all_permissions() if request.user.is_authenticated else 0,
            'missing_urls': [],
        }
        
        # Identificar URLs ausentes
        for module in context['sidebar_modules']:
            if not module.get('url_exists', True):
                context['navigation_debug']['missing_urls'].append({
                    'module': module['name'],
                    'url_name': module['url_name']
                })
            
            for child in module.get('children', []):
                if not child.get('url_exists', True):
                    context['navigation_debug']['missing_urls'].append({
                        'module': f"{module['name']} > {child['name']}",
                        'url_name': child['url_name']
                    })
    
    return context
