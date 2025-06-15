# Copilot: serializers Beneficiary, SocialAnamnesis, ProjectEnrollment, EvolutionRecord
# usando HyperlinkedModelSerializer, depth=1.
# ViewSets com permissions IsAuthenticated & DjangoModelPermissions.
# Router padrão em urls.py /api/.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
]
