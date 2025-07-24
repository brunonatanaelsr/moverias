from django.urls import path
from members.views import (
    BeneficiaryListView, BeneficiaryCreateView, BeneficiaryDetailView,
    BeneficiaryUpdateView, BeneficiaryDeleteView, BeneficiaryDashboardView
)

app_name = 'members'

urlpatterns = [
    path('', BeneficiaryListView.as_view(), name='list'),
    path('create/', BeneficiaryCreateView.as_view(), name='create'),
    path('<int:pk>/', BeneficiaryDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', BeneficiaryUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', BeneficiaryDeleteView.as_view(), name='delete'),
    path('dashboard/', BeneficiaryDashboardView.as_view(), name='dashboard'),
]
