from django.urls import path

from members.views import BeneficiaryListView, BeneficiaryCreateView, BeneficiaryDetailView, BeneficiaryUpdateView, BeneficiaryDeleteView, toggle_beneficiary_status, BeneficiaryReportView, BeneficiaryReportDashboardView, beneficiary_complete_report, beneficiary_export_report, BeneficiaryDashboardView

app_name = 'members'

urlpatterns = [
    path('', BeneficiaryListView.as_view(), name='beneficiary-list'),
    path('create/', BeneficiaryCreateView.as_view(), name='beneficiary-create'),
    path('<int:pk>/', BeneficiaryDetailView.as_view(), name='beneficiary-detail'),
    path('<int:pk>/dashboard/', BeneficiaryDashboardView.as_view(), name='beneficiary-dashboard'),
    path('<int:pk>/edit/', BeneficiaryUpdateView.as_view(), name='beneficiary-update'),
    path('<int:pk>/delete/', BeneficiaryDeleteView.as_view(), name='beneficiary-delete'),
    path('<int:pk>/toggle-status/', toggle_beneficiary_status, name='beneficiary-toggle-status'),
    path('<int:pk>/report/', beneficiary_complete_report, name='beneficiary-complete-report'),
    path('<int:pk>/report/export/', beneficiary_export_report, name='beneficiary-export-report'),
    path('beneficiary/<int:pk>/relatorio/', BeneficiaryReportView.as_view(), name='beneficiary-report'),
    path('relatorios/', BeneficiaryReportDashboardView.as_view(), name='beneficiary-report-dashboard'),
]
