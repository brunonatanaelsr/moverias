"""
URLs para o sistema de certificados
"""
from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    # Dashboard e visualização
    path('', views.certificates_dashboard, name='dashboard'),
    path('list/', views.certificates_dashboard, name='list'),  # Alias para dashboard
    path('certificate/<uuid:certificate_id>/', views.certificate_detail, name='detail'),
    path('certificate/<uuid:certificate_id>/download/', views.download_certificate, name='download'),
    
    # CRUD de certificados
    path('create/', views.certificate_create, name='create'),
    path('certificate/<uuid:certificate_id>/edit/', views.certificate_edit, name='edit'),
    path('certificate/<uuid:certificate_id>/delete/', views.certificate_delete, name='delete'),
    
    # Solicitações
    path('request/<int:workshop_id>/', views.request_certificate, name='request'),
    
    # Verificação
    path('verify/<str:code>/', views.verify_certificate_view, name='verify'),
    path('api/verify/', views.verify_certificate_api, name='verify_api'),
    
    # Administração
    path('admin/certificates/', views.admin_certificates_list, name='admin_certificates'),
    path('admin/requests/', views.admin_certificate_requests, name='admin_requests'),
    path('admin/approve/<int:request_id>/', views.approve_certificate_request, name='approve_request'),
    path('admin/auto-generate/', views.auto_generate_certificates_view, name='auto_generate'),
    path('admin/send-email/<uuid:certificate_id>/', views.send_certificate_email_view, name='send_email'),
    
    # Templates
    path('admin/templates/', views.CertificateTemplateListView.as_view(), name='template_list'),
    path('admin/templates/create/', views.CertificateTemplateCreateView.as_view(), name='template_create'),
    path('admin/templates/<int:pk>/edit/', views.CertificateTemplateUpdateView.as_view(), name='template_edit'),
]
