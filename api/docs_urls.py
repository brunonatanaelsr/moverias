"""
URLs para documentação da API com Swagger
"""
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings

# Schema view para Swagger
schema_view = get_schema_view(
    openapi.Info(
        title=settings.API_INFO['title'],
        default_version=settings.API_INFO['version'],
        description=settings.API_INFO['description'],
        terms_of_service=settings.API_INFO['terms_of_service'],
        contact=openapi.Contact(
            name=settings.API_INFO['contact']['name'],
            email=settings.API_INFO['contact']['email'],
            url=settings.API_INFO['contact']['url']
        ),
        license=openapi.License(
            name=settings.API_INFO['license']['name'],
            url=settings.API_INFO['license']['url']
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

app_name = 'api_docs'

urlpatterns = [
    # Swagger UI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # ReDoc UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('v1/', include([
        path('auth/', include('api.auth_urls')),
        path('members/', include('api.members_urls')),
        path('workshops/', include('api.workshops_urls')),
        path('projects/', include('api.projects_urls')),
        path('certificates/', include('api.certificates_urls')),
        path('notifications/', include('api.notifications_urls')),
        path('dashboard/', include('api.dashboard_urls')),
    ])),
]
