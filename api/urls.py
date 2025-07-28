# Copilot: serializers Beneficiary, SocialAnamnesis, ProjectEnrollment, EvolutionRecord
# usando HyperlinkedModelSerializer, depth=1.
# ViewSets com permissions IsAuthenticated & DjangoModelPermissions.
# Router padrão em urls.py /api/.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import validation_views

app_name = 'api'

router = DefaultRouter()
router.register(r'beneficiaries', views.BeneficiaryViewSet)
router.register(r'social-anamnesis', views.SocialAnamnesisViewSet)
router.register(r'project-enrollments', views.ProjectEnrollmentViewSet)
router.register(r'evolution-records', views.EvolutionRecordViewSet)
router.register(r'action-plans', views.ActionPlanViewSet)
router.register(r'wheel-of-life', views.WheelOfLifeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('beneficiaries/<int:pk>/export/', views.BeneficiaryExportView.as_view(), name='beneficiary-export'),
    
    # Endpoints de validação real-time
    path('validate/cpf/', validation_views.check_cpf_uniqueness, name='validate-cpf'),
    path('validate/field/', validation_views.validate_field_api, name='validate-field'),
    path('validate/email/', validation_views.check_email_uniqueness, name='validate-email'),
    
    # Chat interno API
    path('chat/', include('api.chat_urls')),
]
