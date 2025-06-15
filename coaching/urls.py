from django.urls import path
from . import views

app_name = 'coaching'

urlpatterns = [
    # Action Plans
    path('action-plans/', views.ActionPlanListView.as_view(), name='action_plan_list'),
    path('action-plans/create/', views.ActionPlanCreateView.as_view(), name='action_plan_create'),
    path('action-plans/<int:pk>/', views.ActionPlanDetailView.as_view(), name='action_plan_detail'),
    path('action-plans/<int:pk>/edit/', views.ActionPlanUpdateView.as_view(), name='action_plan_edit'),
    
    # Wheel of Life
    path('wheel-of-life/', views.WheelOfLifeListView.as_view(), name='wheel_list'),
    path('wheel-of-life/create/', views.WheelOfLifeCreateView.as_view(), name='wheel_create'),
    path('wheel-of-life/<int:pk>/', views.WheelOfLifeDetailView.as_view(), name='wheel_detail'),
    path('wheel-of-life/<int:pk>/edit/', views.WheelOfLifeUpdateView.as_view(), name='wheel_edit'),
]
