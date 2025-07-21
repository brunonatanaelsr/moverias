# Copilot: serializers Beneficiary, SocialAnamnesis, ProjectEnrollment, EvolutionRecord
# usando HyperlinkedModelSerializer, depth=1.
# ViewSets com permissions IsAuthenticated & DjangoModelPermissions.
# Router padrão em urls.py /api/.

from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from django.shortcuts import get_object_or_404
import zipfile
import tempfile
import json
import os

from .serializers import (
    BeneficiarySerializer, SocialAnamnesisSerializer,
    ProjectEnrollmentSerializer, EvolutionRecordSerializer,
    ActionPlanSerializer, WheelOfLifeSerializer
)
from members.models import Beneficiary
from social.models import SocialAnamnesis
from projects.models import ProjectEnrollment
from evolution.models import EvolutionRecord
from coaching.models import ActionPlan, WheelOfLife


class BeneficiaryViewSet(viewsets.ModelViewSet):
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['neighbourhood', 'created_at']
    search_fields = ['full_name', 'nis']
    ordering_fields = ['full_name', 'created_at']
    ordering = ['full_name']


class SocialAnamnesisViewSet(viewsets.ModelViewSet):
    queryset = SocialAnamnesis.objects.all()
    serializer_class = SocialAnamnesisSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'locked', 'signed_by_beneficiary']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']


class ProjectEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectEnrollment.objects.all()
    serializer_class = ProjectEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'project_name', 'status', 'weekday']
    search_fields = ['project_name', 'beneficiary__full_name']
    ordering_fields = ['project_name', 'created_at']
    ordering = ['project_name', 'weekday']


class EvolutionRecordViewSet(viewsets.ModelViewSet):
    queryset = EvolutionRecord.objects.all()
    serializer_class = EvolutionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'author', 'signature_required', 'signed_by_beneficiary']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']


class ActionPlanViewSet(viewsets.ModelViewSet):
    queryset = ActionPlan.objects.all()
    serializer_class = ActionPlanSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class WheelOfLifeViewSet(viewsets.ModelViewSet):
    queryset = WheelOfLife.objects.all()
    serializer_class = WheelOfLifeSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']


class BeneficiaryExportView(APIView):
    """
    Copilot: endpoint /api/beneficiaries/{id}/export/ (APIView).
    Gera ZIP com PDFs + JSON dump dos registros,
    devolve FileResponse; permitido a própria beneficiária ou staff.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        beneficiary = get_object_or_404(Beneficiary, pk=pk)
        
        # Verificar permissões
        if not (request.user.is_staff or request.user == beneficiary.user):
            return Response(
                {'error': 'Você não tem permissão para exportar estes dados.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Criar arquivo ZIP temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                # Dados JSON da beneficiária
                beneficiary_data = {
                    'beneficiary': BeneficiarySerializer(beneficiary).data,
                    'social_anamnesis': SocialAnamnesisSerializer(
                        beneficiary.social_anamneses.all(), many=True
                    ).data,
                    'project_enrollments': ProjectEnrollmentSerializer(
                        beneficiary.project_enrollments.all(), many=True
                    ).data,
                    'evolution_records': EvolutionRecordSerializer(
                        beneficiary.evolution_records.all(), many=True
                    ).data,
                    'action_plans': ActionPlanSerializer(
                        beneficiary.action_plans.all(), many=True
                    ).data,
                    'wheel_of_life': WheelOfLifeSerializer(
                        beneficiary.wheel_of_life.all(), many=True
                    ).data,
                }
                
                # Adicionar JSON ao ZIP
                zip_file.writestr(
                    f'dados_{beneficiary.full_name.replace(" ", "_")}.json',
                    json.dumps(beneficiary_data, indent=2, ensure_ascii=False)
                )
                
                # Adicionar PDFs de consentimento se existirem
                for consent in beneficiary.consents.all():
                    if consent.pdf and os.path.exists(consent.pdf.path):
                        zip_file.write(
                            consent.pdf.path,
                            f'termos/termo_{consent.signed_at.strftime("%Y%m%d_%H%M%S")}.pdf'
                        )

            # Retornar arquivo ZIP
            response = FileResponse(
                open(temp_zip.name, 'rb'),
                as_attachment=True,
                filename=f'export_{beneficiary.full_name.replace(" ", "_")}_{beneficiary.id}.zip'
            )
            
            # Limpar arquivo temporário após o download
            def cleanup():
                try:
                    os.unlink(temp_zip.name)
                except OSError:
                    pass
            
            response.close = cleanup
            return response
