from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Quadros
    path('boards/', views.board_list, name='board_list'),
    path('boards/create/', views.board_create, name='board_create'),
    path('boards/<int:board_id>/', views.board_detail, name='board_detail'),
    path('boards/<int:board_id>/edit/', views.board_edit, name='board_edit'),
    
    # Tarefas
    path('tasks/', views.task_list, name='task_list'),
    path('boards/<int:board_id>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<uuid:task_id>/comment/', views.add_comment, name='add_comment'),
    
    # Relatórios
    path('reports/', views.task_reports, name='reports'),
    
    # Export URLs
    path('export/', views.tasks_export, name='tasks_export'),
    path('boards/<int:board_id>/export/', views.board_tasks_export, name='board_tasks_export'),
    path('export/user/<int:user_id>/', views.user_tasks_export, name='user_tasks_export'),
    path('export/my-tasks/', views.user_tasks_export, name='my_tasks_export'),
    
    # AJAX Endpoints
    path('api/task/create/', views.task_create_ajax, name='task_create_ajax'),
    path('api/task/update-column/', views.task_update_column, name='task_update_column'),
    path('api/task/<uuid:task_id>/detail/', views.task_detail_ajax, name='task_detail_ajax'),
    path('api/task/<uuid:task_id>/update/', views.task_update_ajax, name='task_update_ajax'),
    path('api/task/<uuid:task_id>/delete/', views.task_delete_ajax, name='task_delete_ajax'),
    path('api/task/<uuid:task_id>/comment/', views.task_comment_add, name='task_comment_add'),
    path('api/task/<uuid:task_id>/label/add/', views.task_label_add, name='task_label_add'),
    path('api/task/<uuid:task_id>/label/remove/', views.task_label_remove, name='task_label_remove'),
    path('api/task/<uuid:task_id>/watcher/add/', views.task_watcher_add, name='task_watcher_add'),
    path('api/task/<uuid:task_id>/watcher/remove/', views.task_watcher_remove, name='task_watcher_remove'),
    
    # Busca
    path('search/', views.task_search, name='search'),
]
