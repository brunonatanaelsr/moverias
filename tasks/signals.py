from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Task, TaskActivity, TaskBoard, TaskColumn

User = get_user_model()


@receiver(post_save, sender=Task)
def create_task_activity(sender, instance, created, **kwargs):
    """Criar atividade quando uma tarefa é criada ou atualizada"""
    if created:
        TaskActivity.objects.create(
            task=instance,
            user=instance.reporter,
            activity_type='created',
            description=f'Tarefa "{instance.title}" foi criada'
        )
    else:
        # Verificar se foi atribuída a alguém
        if instance.assignee:
            TaskActivity.objects.create(
                task=instance,
                user=instance.assignee,
                activity_type='assigned',
                description=f'Tarefa "{instance.title}" foi atribuída a {instance.assignee.get_full_name()}'
            )


@receiver(post_save, sender=TaskBoard)
def create_default_columns(sender, instance, created, **kwargs):
    """Criar colunas padrão quando um quadro é criado"""
    if created:
        default_columns = [
            {'name': 'A Fazer', 'color': '#EF4444', 'order': 1},
            {'name': 'Em Andamento', 'color': '#F59E0B', 'order': 2},
            {'name': 'Em Revisão', 'color': '#3B82F6', 'order': 3},
            {'name': 'Concluído', 'color': '#10B981', 'order': 4},
        ]
        
        for col_data in default_columns:
            TaskColumn.objects.create(
                board=instance,
                name=col_data['name'],
                color=col_data['color'],
                order=col_data['order'],
                is_default=True
            )


@receiver(post_delete, sender=Task)
def log_task_deletion(sender, instance, **kwargs):
    """Log quando uma tarefa é excluída"""
    TaskActivity.objects.create(
        task=None,  # Tarefa foi excluída
        user=instance.reporter,
        activity_type='deleted',
        description=f'Tarefa "{instance.title}" foi excluída'
    )
