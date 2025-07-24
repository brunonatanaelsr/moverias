from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import TaskBoard, Task, TaskColumn, TaskComment, TaskActivity
from .forms import TaskBoardForm, TaskForm, TaskCommentForm
import json


@login_required
def board_list(request):
    """Lista todos os quadros de tarefas"""
    boards = TaskBoard.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct().order_by('-updated_at')
    
    context = {
        'boards': boards,
        'total_boards': boards.count(),
    }
    return render(request, 'tasks/board_list.html', context)


@login_required
def board_detail(request, board_id):
    """Visualização do quadro Kanban"""
    board = get_object_or_404(TaskBoard, id=board_id)
    
    # Verificar se o usuário tem acesso ao quadro
    if board.owner != request.user and not board.members.filter(id=request.user.id).exists():
        messages.error(request, 'Você não tem acesso a este quadro.')
        return redirect('tasks:board_list')
    
    # Buscar colunas e tarefas
    columns = board.columns.all().order_by('order')
    
    # Filtros
    assignee_filter = request.GET.get('assignee')
    priority_filter = request.GET.get('priority')
    
    # Membros do quadro para filtros
    board_members = board.members.all()
    
    context = {
        'board': board,
        'columns': columns,
        'board_members': board_members,
        'priority_choices': Task.PRIORITY_CHOICES,
        'assignee_filter': assignee_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'tasks/board_kanban.html', context)


@login_required
def board_create(request):
    """Criar novo quadro"""
    if request.method == 'POST':
        form = TaskBoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.owner = request.user
            board.save()
            board.members.add(request.user)
            messages.success(request, 'Quadro criado com sucesso!')
            return redirect('tasks:board_detail', board_id=board.id)
    else:
        form = TaskBoardForm()
    
    return render(request, 'tasks/board_form.html', {'form': form, 'title': 'Criar Quadro'})


@login_required
def board_edit(request, board_id):
    """Editar quadro"""
    board = get_object_or_404(TaskBoard, id=board_id, owner=request.user)
    
    if request.method == 'POST':
        form = TaskBoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quadro atualizado com sucesso!')
            return redirect('tasks:board_detail', board_id=board.id)
    else:
        form = TaskBoardForm(instance=board)
    
    return render(request, 'tasks/board_form.html', {'form': form, 'title': 'Editar Quadro', 'board': board})


@login_required
def task_create(request, board_id):
    """Criar nova tarefa"""
    board = get_object_or_404(TaskBoard, id=board_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, board=board)
        if form.is_valid():
            task = form.save(commit=False)
            task.board = board
            task.reporter = request.user
            # Colocar na primeira coluna por padrão
            task.column = board.columns.first()
            task.save()
            messages.success(request, 'Tarefa criada com sucesso!')
            return redirect('tasks:board_detail', board_id=board.id)
    else:
        form = TaskForm(board=board)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Criar Tarefa', 'board': board})


@login_required
def task_detail(request, task_id):
    """Detalhes da tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar acesso
    if not (task.board.owner == request.user or 
            task.board.members.filter(id=request.user.id).exists()):
        messages.error(request, 'Você não tem acesso a esta tarefa.')
        return redirect('tasks:board_list')
    
    # Comentários
    comments = task.comments.all().order_by('-created_at')
    comment_form = TaskCommentForm()
    
    # Atividades
    activities = task.activities.all().order_by('-created_at')[:10]
    
    context = {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'activities': activities,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_edit(request, task_id):
    """Editar tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, board=task.board)
        if form.is_valid():
            form.save()
            
            # Criar atividade
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='updated',
                description=f'Tarefa "{task.title}" foi atualizada'
            )
            
            messages.success(request, 'Tarefa atualizada com sucesso!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task, board=task.board)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Editar Tarefa', 'task': task})


@login_required
@require_http_methods(["POST"])
def add_comment(request, task_id):
    """Adicionar comentário à tarefa"""
    task = get_object_or_404(Task, id=task_id)
    form = TaskCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        
        # Criar atividade
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            activity_type='commented',
            description=f'Comentário adicionado por {request.user.get_full_name()}'
        )
        
        messages.success(request, 'Comentário adicionado com sucesso!')
    
    return redirect('tasks:task_detail', task_id=task_id)


@login_required
@csrf_exempt
def move_task(request):
    """Mover tarefa entre colunas (AJAX)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        column_id = data.get('column_id')
        new_order = data.get('order', 0)
        
        try:
            task = Task.objects.get(id=task_id)
            new_column = TaskColumn.objects.get(id=column_id)
            
            # Verificar se o usuário tem acesso
            if not (task.board.owner == request.user or 
                    task.board.members.filter(id=request.user.id).exists()):
                return JsonResponse({'success': False, 'message': 'Acesso negado'})
            
            # Mover tarefa
            old_column = task.column
            task.column = new_column
            task.order = new_order
            task.save()
            
            # Criar atividade
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='moved',
                description=f'Tarefa movida de "{old_column.name}" para "{new_column.name}"'
            )
            
            return JsonResponse({'success': True})
            
        except (Task.DoesNotExist, TaskColumn.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Tarefa ou coluna não encontrada'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def dashboard(request):
    """Dashboard de tarefas"""
    # Tarefas atribuídas ao usuário
    my_tasks = Task.objects.filter(assignee=request.user, status__in=['todo', 'in_progress'])
    
    # Tarefas em atraso
    overdue_tasks = [task for task in my_tasks if task.is_overdue()]
    
    # Tarefas por prioridade
    urgent_tasks = my_tasks.filter(priority='urgent')
    high_priority_tasks = my_tasks.filter(priority='high')
    
    # Quadros que o usuário participa
    user_boards = TaskBoard.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()
    
    # Estatísticas
    total_tasks = my_tasks.count()
    completed_tasks = Task.objects.filter(
        assignee=request.user,
        status='completed',
        completed_at__date=timezone.now().date()
    ).count()
    
    context = {
        'my_tasks': my_tasks[:5],  # Últimas 5 tarefas
        'overdue_tasks': overdue_tasks,
        'urgent_tasks': urgent_tasks,
        'high_priority_tasks': high_priority_tasks,
        'user_boards': user_boards,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_count': len(overdue_tasks),
    }
    
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_search(request):
    """Buscar tarefas"""
    query = request.GET.get('q', '')
    board_id = request.GET.get('board')
    
    tasks = Task.objects.all()
    
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    if board_id:
        tasks = tasks.filter(board_id=board_id)
    
    # Filtrar por acesso do usuário
    user_boards = TaskBoard.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()
    
    tasks = tasks.filter(board__in=user_boards)
    
    # Paginação
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tasks': page_obj,
        'query': query,
        'board_id': board_id,
        'user_boards': user_boards,
    }
    
    return render(request, 'tasks/search.html', context)


# Add these new AJAX endpoints after the existing views

@login_required
@require_http_methods(["POST"])
def task_create_ajax(request):
    """Criar tarefa via AJAX"""
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        board = get_object_or_404(TaskBoard, id=data.get('board_id'))
        column = get_object_or_404(TaskColumn, id=data.get('column_id'), board=board)
        
        # Verificar se o usuário tem acesso ao quadro
        if board.owner != request.user and not board.members.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Acesso negado'})
        
        task = Task.objects.create(
            title=data.get('title'),
            description=data.get('description', ''),
            board=board,
            column=column,
            assignee_id=data.get('assignee') if data.get('assignee') else None,
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date') if data.get('due_date') else None,
            estimated_hours=data.get('estimated_hours') if data.get('estimated_hours') else None,
            estimated_cost=data.get('estimated_cost') if data.get('estimated_cost') else None,
            reporter=request.user
        )
        
        # Adicionar labels se fornecidas
        if data.get('labels'):
            label_ids = data.get('labels') if isinstance(data.get('labels'), list) else [data.get('labels')]
            task.labels.set(label_ids)
        
        # Registrar atividade
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='created',
            description=f'Tarefa criada por {request.user.get_full_name()}'
        )
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': 'Tarefa criada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_update_column(request):
    """Mover tarefa para outra coluna via AJAX"""
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        task = get_object_or_404(Task, id=data.get('task_id'))
        column = get_object_or_404(TaskColumn, id=data.get('column_id'))
        
        # Verificar se o usuário tem acesso
        if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Acesso negado'})
        
        old_column = task.column
        task.column = column
        task.save()
        
        # Registrar atividade
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='moved',
            description=f'Tarefa movida de {old_column.name} para {column.name}'
        )
        
        return JsonResponse({'success': True, 'message': 'Tarefa movida com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def task_detail_ajax(request, task_id):
    """Detalhes da tarefa via AJAX"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    context = {
        'task': task,
    }
    return render(request, 'tasks/task_detail_modal.html', context)


@login_required
@require_http_methods(["POST"])
def task_update_ajax(request, task_id):
    """Atualizar tarefa via AJAX"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        # Atualizar campos
        for field, value in data.items():
            if hasattr(task, field):
                if field == 'assignee' and value:
                    task.assignee_id = value
                elif field == 'due_date' and value:
                    from datetime import datetime
                    task.due_date = datetime.strptime(value, '%Y-%m-%d').date()
                elif field in ['estimated_hours', 'estimated_cost'] and value:
                    setattr(task, field, float(value))
                else:
                    setattr(task, field, value)
        
        task.save()
        
        # Registrar atividade
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='updated',
            description=f'Tarefa atualizada por {request.user.get_full_name()}'
        )
        
        return JsonResponse({'success': True, 'message': 'Tarefa atualizada com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_comment_add(request, task_id):
    """Adicionar comentário à tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    content = request.POST.get('content')
    if not content:
        return JsonResponse({'success': False, 'message': 'Comentário não pode estar vazio'})
    
    try:
        comment = TaskComment.objects.create(
            task=task,
            author=request.user,
            content=content
        )
        
        # Registrar atividade
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='commented',
            description=f'Comentário adicionado por {request.user.get_full_name()}'
        )
        
        return JsonResponse({'success': True, 'message': 'Comentário adicionado com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_label_add(request, task_id):
    """Adicionar label à tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        label_id = data.get('label_id')
        if label_id:
            task.labels.add(label_id)
            return JsonResponse({'success': True, 'message': 'Label adicionada com sucesso'})
        else:
            return JsonResponse({'success': False, 'message': 'ID da label é obrigatório'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_label_remove(request, task_id):
    """Remover label da tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        label_id = data.get('label_id')
        if label_id:
            task.labels.remove(label_id)
            return JsonResponse({'success': True, 'message': 'Label removida com sucesso'})
        else:
            return JsonResponse({'success': False, 'message': 'ID da label é obrigatório'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_watcher_add(request, task_id):
    """Adicionar observador à tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        watcher_id = data.get('watcher_id')
        if watcher_id:
            task.watchers.add(watcher_id)
            return JsonResponse({'success': True, 'message': 'Observador adicionado com sucesso'})
        else:
            return JsonResponse({'success': False, 'message': 'ID do observador é obrigatório'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def task_watcher_remove(request, task_id):
    """Remover observador da tarefa"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST.dict()
    
    try:
        watcher_id = data.get('watcher_id')
        if watcher_id:
            task.watchers.remove(watcher_id)
            return JsonResponse({'success': True, 'message': 'Observador removido com sucesso'})
        else:
            return JsonResponse({'success': False, 'message': 'ID do observador é obrigatório'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["DELETE"])
def task_delete_ajax(request, task_id):
    """Excluir tarefa via AJAX"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar se o usuário tem acesso
    if task.board.owner != request.user and not task.board.members.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    try:
        task.delete()
        return JsonResponse({'success': True, 'message': 'Tarefa excluída com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def task_list(request):
    """Lista todas as tarefas do usuário"""
    tasks = Task.objects.filter(
        Q(assignee=request.user) | Q(board__owner=request.user) | Q(board__members=request.user)
    ).select_related('board', 'assignee', 'column').distinct()
    
    # Filtros
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    board_filter = request.GET.get('board')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if board_filter:
        tasks = tasks.filter(board_id=board_filter)
    
    # Paginação
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Quadros para filtro
    boards = TaskBoard.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()
    
    context = {
        'page_obj': page_obj,
        'boards': boards,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'board_filter': board_filter,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_reports(request):
    """Relatórios de tarefas"""
    # Estatísticas gerais
    total_tasks = Task.objects.filter(
        Q(assignee=request.user) | Q(board__owner=request.user) | Q(board__members=request.user)
    ).distinct().count()
    
    completed_tasks = Task.objects.filter(
        Q(assignee=request.user) | Q(board__owner=request.user) | Q(board__members=request.user),
        status='completed'
    ).distinct().count()
    
    pending_tasks = Task.objects.filter(
        Q(assignee=request.user) | Q(board__owner=request.user) | Q(board__members=request.user),
        status__in=['todo', 'in_progress']
    ).distinct().count()
    
    # Tarefas por prioridade
    priority_stats = Task.objects.filter(
        Q(assignee=request.user) | Q(board__owner=request.user) | Q(board__members=request.user)
    ).values('priority').annotate(count=Count('id'))
    
    # Calcular percentuais para prioridades
    priority_stats_with_percentage = []
    for stat in priority_stats:
        percentage = (stat['count'] * 100 / total_tasks) if total_tasks > 0 else 0
        priority_stats_with_percentage.append({
            'priority': stat['priority'],
            'count': stat['count'],
            'percentage': round(percentage, 1)
        })
    
    # Tarefas por quadro
    board_stats = TaskBoard.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).annotate(task_count=Count('tasks')).values('name', 'task_count')
    
    # Calcular percentuais para quadros
    board_stats_with_percentage = []
    for stat in board_stats:
        percentage = (stat['task_count'] * 100 / total_tasks) if total_tasks > 0 else 0
        board_stats_with_percentage.append({
            'name': stat['name'],
            'task_count': stat['task_count'],
            'percentage': round(percentage, 1)
        })
    
    # Calcular percentual de conclusão
    completion_percentage = (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_percentage': round(completion_percentage, 1),
        'priority_stats': priority_stats_with_percentage,
        'board_stats': board_stats_with_percentage,
    }
    return render(request, 'tasks/reports.html', context)
