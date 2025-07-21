"""
URLs da API para certificados
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import certificate_views

router = DefaultRouter()
router.register(r'certificates', certificate_views.CertificateViewSet)
router.register(r'requests', certificate_views.CertificateRequestViewSet)
router.register(r'templates', certificate_views.CertificateTemplateViewSet)

app_name = 'api_certificates'

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints adicionais
    path('generate/', certificate_views.GenerateCertificateAPIView.as_view(), name='generate'),
    path('download/<uuid:certificate_id>/', certificate_views.DownloadCertificateAPIView.as_view(), name='download'),
    path('verify/<str:verification_code>/', certificate_views.VerifyCertificateAPIView.as_view(), name='verify'),
    path('stats/', certificate_views.CertificateStatsAPIView.as_view(), name='stats'),
]
