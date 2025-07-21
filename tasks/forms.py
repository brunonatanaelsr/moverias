from django import forms
from django.contrib.auth import get_user_model
from .models import TaskBoard, Task, TaskComment, TaskColumn

User = get_user_model()


class TaskBoardForm(forms.ModelForm):
    class Meta:
        model = TaskBoard
        fields = ['name', 'description', 'department']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Nome do quadro'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Descrição do quadro',
                'rows': 3
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            })
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assignee', 'priority', 'due_date',
            'estimated_hours', 'estimated_cost', 'column'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Título da tarefa'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Descrição detalhada da tarefa',
                'rows': 4
            }),
            'assignee': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'type': 'date'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': '0.00',
                'step': '0.25'
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'column': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
            })
        }

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        
        if board:
            # Filtrar membros do quadro para o campo assignee
            self.fields['assignee'].queryset = board.members.all()
            # Filtrar colunas do quadro
            self.fields['column'].queryset = board.columns.all()


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Adicione um comentário...',
                'rows': 3
            })
        }


class TaskColumnForm(forms.ModelForm):
    class Meta:
        model = TaskColumn
        fields = ['name', 'color', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': 'Nome da coluna'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'type': 'color'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
                'placeholder': '1'
            })
        }


class TaskFilterForm(forms.Form):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="Todos os responsáveis",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'Todas as prioridades')] + Task.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Task.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent'
        })
    )
    
    due_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
            'type': 'date'
        })
    )
    
    due_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-move-purple-500 focus:border-transparent',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        
        if board:
            self.fields['assignee'].queryset = board.members.all()
