from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Wizard para criar nova anamnese
    path('anamnesis/new/', views.SocialAnamnesisWizard.as_view(), name='anamnesis_create'),
    path('anamnesis/new/<int:beneficiary_id>/', views.SocialAnamnesisWizard.as_view(), name='anamnesis_create_for_beneficiary'),
    
    # CRUD anamnese
    path('anamnesis/<int:pk>/', views.SocialAnamnesisDetailView.as_view(), name='detail'),
    path('anamnesis/<int:pk>/edit/', views.SocialAnamnesisUpdateView.as_view(), name='edit'),
    path('anamnesis/<int:pk>/delete/', views.SocialAnamnesisDeleteView.as_view(), name='delete'),
    path('anamnesis/<int:pk>/lock/', views.lock_anamnesis, name='lock'),
    path('anamnesis/', views.SocialAnamnesisListView.as_view(), name='list'),
]
