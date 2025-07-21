"""
URLs para upload de arquivos
"""

from django.urls import path
from . import upload_views

app_name = 'core'

urlpatterns = [
    # Upload de arquivos - formulário web
    path('upload/', upload_views.FileUploadFormView.as_view(), name='file-upload'),
    
    # Upload via API/AJAX
    path('upload/api/', upload_views.upload_api_view, name='file-upload-api'),
    path('upload/validate/', upload_views.upload_validate_api, name='file-validate-api'),
    
    # Gerenciamento de uploads
    path('files/', upload_views.UploadListView.as_view(), name='upload-list'),
    path('files/<int:pk>/', upload_views.UploadDetailView.as_view(), name='upload-detail'),
    path('files/<int:pk>/delete/', upload_views.UploadDeleteView.as_view(), name='upload-delete'),
    path('files/<int:upload_id>/download/', upload_views.upload_download_view, name='upload-download'),
    
    # Estatísticas
    path('upload/stats/', upload_views.upload_stats_api, name='upload-stats'),
    path('stats/', upload_views.UploadStatsView.as_view(), name='upload-stats-page'),
    
    # Ações em lote
    path('files/bulk-delete/', upload_views.BulkDeleteView.as_view(), name='bulk-delete'),
    path('files/update-status/', upload_views.FileStatusUpdateView.as_view(), name='update-status'),
]
