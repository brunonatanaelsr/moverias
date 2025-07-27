from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.SocialDashboardView.as_view(), name='dashboard'),
    
    # Wizard para criar nova anamnese
    path('anamnesis/new/', views.SocialAnamnesisWizard.as_view(), name='anamnesis-create'),
    path('anamnesis/new/<int:beneficiary_id>/', views.SocialAnamnesisWizard.as_view(), name='anamnesis-create-for-beneficiary'),
    
    # CRUD anamnese
    path('anamnesis/<int:pk>/', views.SocialAnamnesisDetailView.as_view(), name='detail'),
    path('anamnesis/<int:pk>/edit/', views.SocialAnamnesisUpdateView.as_view(), name='edit'),
    path('anamnesis/<int:pk>/delete/', views.SocialAnamnesisDeleteView.as_view(), name='delete'),
    path('anamnesis/<int:pk>/lock/', views.lock_anamnesis, name='lock'),
    path('anamnesis/', views.SocialAnamnesisListView.as_view(), name='list'),
    path('', views.SocialAnamnesisListView.as_view(), name='index'),  # Redirect para lista
    
    # Novas funcionalidades
    path('anamnesis/<int:pk>/evolution/', views.add_evolution, name='add-evolution'),
    path('api/vulnerability-categories/', views.vulnerability_categories_api, name='vulnerability-categories-api'),
    
    # Sistema de assinatura digital
    path('anamnesis/<int:pk>/signature/', views.wizard_signature_view, name='wizard_signature'),
    path('anamnesis/<int:pk>/pdf/', views.generate_anamnesis_pdf, name='anamnesis_pdf'),
    
    # Relatórios e Analytics
    path('reports/', views.SocialReportsView.as_view(), name='social_reports'),
    path('analytics/vulnerabilities/', views.VulnerabilityAnalyticsView.as_view(), name='vulnerability_analytics'),
]
