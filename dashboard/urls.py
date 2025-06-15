from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('beneficiaries/', views.beneficiaries_list, name='beneficiaries_list'),
    path('beneficiaries/<int:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
    path('beneficiaries/create/', views.beneficiary_create, name='beneficiary_create'),
    path('beneficiaries/<int:pk>/edit/', views.beneficiary_edit, name='beneficiary_edit'),
]
