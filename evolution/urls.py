from django.urls import path
from . import views

app_name = 'evolution'

urlpatterns = [
    # Lista de registros de evolução
    path('', views.EvolutionRecordListView.as_view(), name='list'),
    
    # CRUD registros de evolução
    path('create/', views.EvolutionRecordCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EvolutionRecordDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.EvolutionRecordUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.EvolutionRecordDeleteView.as_view(), name='delete'),
    # Exportação de relatórios
    path('export/excel/', views.EvolutionExportExcelView.as_view(), name='export_excel'),
    path('export/pdf/', views.EvolutionExportPDFView.as_view(), name='export_pdf'),
]
