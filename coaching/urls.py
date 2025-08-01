from django.urls import path
from . import views

app_name = 'coaching'

urlpatterns = [
    # Action Plans
    path('action-plans/', views.ActionPlanListView.as_view(), name='action-plan-list'),
    path('action-plans/create/', views.ActionPlanCreateView.as_view(), name='action-plan-create'),
    path('action-plans/<int:pk>/', views.ActionPlanDetailView.as_view(), name='action-plan-detail'),
    path('action-plans/<int:pk>/edit/', views.ActionPlanUpdateView.as_view(), name='action-plan-edit'),
    path('action-plans/<int:pk>/delete/', views.ActionPlanDeleteView.as_view(), name='action-plan-delete'),
    
    # Wheel of Life
    path('wheel-of-life/', views.WheelOfLifeListView.as_view(), name='wheel-list'),
    path('wheel-of-life/create/', views.WheelOfLifeCreateView.as_view(), name='wheel-create'),
    path('wheel-of-life/<int:pk>/', views.WheelOfLifeDetailView.as_view(), name='wheel-detail'),
    path('wheel-of-life/<int:pk>/edit/', views.WheelOfLifeUpdateView.as_view(), name='wheel-edit'),
    path('wheel-of-life/<int:pk>/delete/', views.WheelOfLifeDeleteView.as_view(), name='wheel-delete'),
    
    # Sessions
    path('sessions/', views.CoachingSessionListView.as_view(), name='sessions'),
    path('sessions/create/', views.CoachingSessionCreateView.as_view(), name='session-create'),
    path('sessions/<int:pk>/', views.CoachingSessionDetailView.as_view(), name='session-detail'),
    
    # Reports
    path('reports/', views.CoachingReportsView.as_view(), name='reports'),
]
