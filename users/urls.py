from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Gestão de usuários
    path('', views.UserListView.as_view(), name='user-list'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('create/', views.UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/edit/', views.UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('<int:pk>/permissions/', views.PermissionManagementView.as_view(), name='user-permissions'),
    path('<int:pk>/toggle-status/', views.toggle_user_status, name='toggle-user-status'),
    path('<int:pk>/activity-log/', views.user_activity_log, name='user-activity-log'),
    path('<int:pk>/reset-password/', views.user_reset_password, name='user-reset-password'),
    
    # Ações em lote
    path('bulk-actions/', views.bulk_user_actions, name='bulk-actions'),
    path('export/', views.user_export, name='user-export'),
    
    # Gerenciamento de grupos
    path('groups/', views.group_management, name='group-management'),
    path('groups/create/', views.create_group, name='create-group'),
    path('groups/<int:pk>/edit/', views.edit_group, name='edit-group'),
    path('groups/<int:pk>/delete/', views.delete_group, name='delete-group'),
    
    # Perfil do usuário - TODO: implementar views
    # path('profile/', views.user_profile_edit, name='profile'),
    # path('change-password/', views.change_password, name='change_password'),
]
