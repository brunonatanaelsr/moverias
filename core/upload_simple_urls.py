"""
URLs simplificadas para sistema de upload
"""
from django.urls import path
from . import upload_simple_views

app_name = 'core_uploads'

urlpatterns = [
    # Lista e gerenciamento
    path('', upload_simple_views.upload_list, name='upload_list'),
    path('upload/', upload_simple_views.upload_file, name='upload_file'),
    path('<int:pk>/', upload_simple_views.upload_detail, name='upload_detail'),
    path('<int:pk>/download/', upload_simple_views.download_file, name='download_file'),
    path('<int:pk>/delete/', upload_simple_views.delete_upload, name='delete_upload'),
    
    # Meus uploads
    path('my/', upload_simple_views.my_uploads, name='my_uploads'),
    
    # Upload rápido via AJAX
    path('quick/', upload_simple_views.quick_upload, name='quick_upload'),
]
