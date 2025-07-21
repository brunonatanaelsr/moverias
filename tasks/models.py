from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta
import uuid


class TaskBoard(models.Model):
    """Quadro de Tarefas (Kanban Board)"""
    name = models.CharField('Nome do Quadro', max_length=100)
    description = models.TextField('Descrição', blank=True)
    department = models.ForeignKey(
        'hr.Department', 
        on_delete=models.CASCADE,
        related_name='task_boards',
        verbose_name='Departamento',
        null=True, blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_boards',
        verbose_name='Responsável'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='task_boards',
        verbose_name='Membros',
        blank=True
    )
    is_active = models.BooleanField('Ativo', default=True)
    is_template = models.BooleanField('É Template', default=False)
    background_color = models.CharField('Cor de Fundo', max_length=7, default='#FFFFFF')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Quadro de Tarefas'
        verbose_name_plural = 'Quadros de Tarefas'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_total_tasks(self):
        return self.tasks.count()

    def get_completed_tasks(self):
        return self.tasks.filter(status='completed').count()

    def get_progress_percentage(self):
        total = self.get_total_tasks()
        if total == 0:
            return 0
        return (self.get_completed_tasks() / total) * 100

    def get_overdue_tasks(self):
        return self.tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress', 'review']
        ).count()


class TaskColumn(models.Model):
    """Colunas do Quadro Kanban"""
    name = models.CharField('Nome da Coluna', max_length=50)
    board = models.ForeignKey(
        TaskBoard,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name='Quadro'
    )
    order = models.IntegerField('Ordem', default=0)
    color = models.CharField('Cor', max_length=7, default='#6B7280')  # Hex color
    is_default = models.BooleanField('Coluna Padrão', default=False)
    wip_limit = models.PositiveIntegerField('Limite WIP', null=True, blank=True, help_text='Work In Progress limit')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Coluna'
        verbose_name_plural = 'Colunas'
        ordering = ['board', 'order']

    def __str__(self):
        return f"{self.board.name} - {self.name}"

    def get_tasks_count(self):
        return self.tasks.count()

    def is_over_wip_limit(self):
        if self.wip_limit:
            return self.get_tasks_count() > self.wip_limit
        return False


class TaskTemplate(models.Model):
    """Templates de tarefas para automação"""
    name = models.CharField('Nome do Template', max_length=200)
    description = models.TextField('Descrição', blank=True)
    title_template = models.CharField('Modelo de Título', max_length=200)
    description_template = models.TextField('Modelo de Descrição', blank=True)
    priority = models.CharField('Prioridade', max_length=20, choices=[
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ], default='medium')
    estimated_hours = models.DecimalField('Horas Estimadas', max_digits=5, decimal_places=2, null=True, blank=True)
    tags = models.CharField('Tags', max_length=500, blank=True, help_text='Separadas por vírgula')
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.CASCADE,
        related_name='task_templates',
        verbose_name='Departamento',
        null=True, blank=True
    )
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_task_templates',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Template de Tarefa'
        verbose_name_plural = 'Templates de Tarefas'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TaskAutomation(models.Model):
    """Automações de tarefas"""
    TRIGGER_CHOICES = [
        ('task_created', 'Tarefa Criada'),
        ('task_moved', 'Tarefa Movida'),
        ('task_completed', 'Tarefa Concluída'),
        ('due_date_approaching', 'Prazo Próximo'),
        ('overdue', 'Atrasada'),
    ]

    ACTION_CHOICES = [
        ('create_task', 'Criar Tarefa'),
        ('assign_user', 'Atribuir Usuário'),
        ('send_notification', 'Enviar Notificação'),
        ('change_priority', 'Alterar Prioridade'),
        ('move_to_column', 'Mover para Coluna'),
        ('add_comment', 'Adicionar Comentário'),
    ]

    name = models.CharField('Nome da Automação', max_length=200)
    description = models.TextField('Descrição', blank=True)
    board = models.ForeignKey(
        TaskBoard,
        on_delete=models.CASCADE,
        related_name='automations',
        verbose_name='Quadro'
    )
    trigger = models.CharField('Gatilho', max_length=30, choices=TRIGGER_CHOICES)
    action = models.CharField('Ação', max_length=30, choices=ACTION_CHOICES)
    conditions = models.JSONField('Condições', default=dict, blank=True)
    action_data = models.JSONField('Dados da Ação', default=dict, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_automations',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Automação'
        verbose_name_plural = 'Automações'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.board.name}"

class Task(models.Model):
    """Tarefas individuais"""
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    STATUS_CHOICES = [
        ('todo', 'A Fazer'),
        ('in_progress', 'Em Andamento'),
        ('review', 'Em Revisão'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
    ]

    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    
    # Organização
    board = models.ForeignKey(
        TaskBoard,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Quadro'
    )
    column = models.ForeignKey(
        TaskColumn,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Coluna'
    )
    
    # Atribuição
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tasks',
        verbose_name='Responsável'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reported_tasks',
        verbose_name='Criado por'
    )
    
    # Propriedades
    priority = models.CharField('Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='todo')
    
    # Prazos
    due_date = models.DateField('Data de Vencimento', null=True, blank=True)
    estimated_hours = models.DecimalField('Horas Estimadas', max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField('Horas Reais', max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Preços e Custos
    estimated_cost = models.DecimalField('Custo Estimado', max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField('Custo Real', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Posicionamento
    order = models.IntegerField('Ordem na Coluna', default=0)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['column', 'order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Atualizar timestamps baseado no status
        if self.status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return self.due_date < date.today()
        return False

    def get_priority_color(self):
        colors = {
            'low': '#10B981',      # Green
            'medium': '#F59E0B',   # Yellow
            'high': '#EF4444',     # Red
            'urgent': '#7C2D12',   # Dark Red
        }
        return colors.get(self.priority, '#6B7280')

    def get_days_remaining(self):
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None


class TaskComment(models.Model):
    """Comentários em tarefas"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Tarefa'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_comments',
        verbose_name='Autor'
    )
    content = models.TextField('Comentário')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comentário de {self.author.get_full_name()} em {self.task.title}"


class TaskAttachment(models.Model):
    """Anexos das tarefas"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Tarefa'
    )
    file = models.FileField('Arquivo', upload_to='tasks/attachments/')
    name = models.CharField('Nome', max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_attachments',
        verbose_name='Enviado por'
    )
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} - {self.task.title}"

    def get_file_size(self):
        if self.file:
            return self.file.size
        return 0


class TaskActivity(models.Model):
    """Log de atividades das tarefas"""
    ACTIVITY_TYPES = [
        ('created', 'Criada'),
        ('updated', 'Atualizada'),
        ('assigned', 'Atribuída'),
        ('moved', 'Movida'),
        ('commented', 'Comentada'),
        ('completed', 'Concluída'),
        ('deleted', 'Excluída'),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Tarefa'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_activities',
        verbose_name='Usuário'
    )
    activity_type = models.CharField('Tipo', max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField('Descrição')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} {self.get_activity_type_display()} - {self.task.title}"


class TaskTimeEntry(models.Model):
    """Registro de tempo gasto em tarefas"""
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Tarefa'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Usuário'
    )
    start_time = models.DateTimeField('Início')
    end_time = models.DateTimeField('Fim', null=True, blank=True)
    duration_minutes = models.PositiveIntegerField('Duração (minutos)', default=0)
    description = models.TextField('Descrição', blank=True)
    is_billable = models.BooleanField('Faturável', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Tempo'
        verbose_name_plural = 'Registros de Tempo'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.task.title} - {self.user.get_full_name()} ({self.duration_minutes}min)"

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        return self.duration_minutes / 60


class TaskDependency(models.Model):
    """Dependências entre tarefas"""
    DEPENDENCY_TYPE_CHOICES = [
        ('blocks', 'Bloqueia'),
        ('depends_on', 'Depende de'),
        ('related', 'Relacionada'),
    ]

    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='dependencies',
        verbose_name='Tarefa'
    )
    depends_on = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='blocked_by',
        verbose_name='Depende de'
    )
    dependency_type = models.CharField('Tipo', max_length=20, choices=DEPENDENCY_TYPE_CHOICES, default='depends_on')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_dependencies',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Dependência'
        verbose_name_plural = 'Dependências'
        unique_together = ['task', 'depends_on']

    def __str__(self):
        return f"{self.task.title} → {self.depends_on.title}"


class TaskLabel(models.Model):
    """Labels/Tags para categorização de tarefas"""
    name = models.CharField('Nome', max_length=50)
    color = models.CharField('Cor', max_length=7, default='#6B7280')
    board = models.ForeignKey(
        TaskBoard,
        on_delete=models.CASCADE,
        related_name='labels',
        verbose_name='Quadro'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Label'
        verbose_name_plural = 'Labels'
        unique_together = ['name', 'board']

    def __str__(self):
        return f"{self.name} ({self.board.name})"


class TaskRecurrence(models.Model):
    """Tarefas recorrentes"""
    FREQUENCY_CHOICES = [
        ('daily', 'Diária'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]

    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='recurrences',
        verbose_name='Template'
    )
    board = models.ForeignKey(
        TaskBoard,
        on_delete=models.CASCADE,
        related_name='recurrences',
        verbose_name='Quadro'
    )
    frequency = models.CharField('Frequência', max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Fim', null=True, blank=True)
    next_occurrence = models.DateField('Próxima Ocorrência')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Tarefa Recorrente'
        verbose_name_plural = 'Tarefas Recorrentes'

    def __str__(self):
        return f"{self.task_template.name} - {self.get_frequency_display()}"
