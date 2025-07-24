# Copilot: rotas admin/, accounts/ (allauth), api/ (router), dashboard/ (HTMX views).
# Decorar dashboard views com login_required + user_passes_test grupo técnico.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
        path('accounts/', include('allauth.urls')),  # login, logout, signup, etc.
    path('api/', include('api.urls')),  # API endpoints
    path('dashboard/', include('dashboard.urls')),  # HTMX dashboard views
    path('users/', include('users.urls')),  # User management
    path('social/', include('social.urls')),  # Social anamnesis
    path('projects/', include('projects.urls')),  # Projects and enrollments
    path('members/', include('members.urls')),  # Beneficiary management
    path('evolution/', include('evolution.urls')),  # Evolution records
    path('coaching/', include('coaching.urls')),  # Action plans and wheel of life
    path('workshops/', include('workshops.urls')),  # Workshop management
    path('certificates/', include('certificates.urls')),  # Certificates system
    path('notifications/', include('notifications.urls')),  # Notifications system
    path('hr/', include('hr.urls')),  # Human Resources module
    path('tasks/', include('tasks.urls')),  # Task Management (Kanban)
    path('chat/', include('chat.urls')),  # Internal Chat
    path('communication/', include('communication.urls')),  # Internal Communication
    path('activities/', include('activities.urls')),  # Unified activities system
    path('uploads/', include('core.upload_simple_urls')),  # File upload system - simplified
    path('', include('core.urls')),  # Home page and core views
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
