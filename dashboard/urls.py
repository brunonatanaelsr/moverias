from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('beneficiaries/', views.beneficiaries_list, name='beneficiaries-list'),
    path('beneficiaries/export/', views.beneficiaries_export, name='beneficiaries-export'),
    path('beneficiaries/<int:pk>/', views.beneficiary_detail, name='beneficiary-detail'),
    path('beneficiaries/create/', views.beneficiary_create, name='beneficiary-create'),
    path('beneficiaries/<int:pk>/edit/', views.beneficiary_edit, name='beneficiary-edit'),
    path('reports/', views.reports, name='reports'),
    path('custom-reports/', views.custom_reports, name='custom-reports'),
    path('advanced-analytics/', views.advanced_analytics, name='advanced-analytics'),
]
