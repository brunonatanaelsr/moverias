from django.urls import path
from .views import (
    BeneficiaryListView, BeneficiaryCreateView, BeneficiaryDetailView,
    BeneficiaryUpdateView, BeneficiaryDeleteView, toggle_beneficiary_status
)

app_name = 'members'

urlpatterns = [
    path('', BeneficiaryListView.as_view(), name='beneficiary-list'),
    path('create/', BeneficiaryCreateView.as_view(), name='beneficiary-create'),
    path('<int:pk>/', BeneficiaryDetailView.as_view(), name='beneficiary-detail'),
    path('<int:pk>/edit/', BeneficiaryUpdateView.as_view(), name='beneficiary-update'),
    path('<int:pk>/delete/', BeneficiaryDeleteView.as_view(), name='beneficiary-delete'),
    path('<int:pk>/toggle-status/', toggle_beneficiary_status, name='beneficiary-toggle-status'),
]
