from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Usuários
    path('', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    
    # Perfil próprio
    path('profile/', views.profile_view, name='profile'),
    
    # Funções do sistema
    path('roles/', views.SystemRoleListView.as_view(), name='role_list'),
    path('roles/create/', views.SystemRoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views.SystemRoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', views.SystemRoleDeleteView.as_view(), name='role_delete'),
    
    # Atividades
    path('activities/', views.UserActivityListView.as_view(), name='activity_list'),
]
