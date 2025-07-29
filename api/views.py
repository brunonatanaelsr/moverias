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
    BeneficiarySerializer,
    SocialAnamnesisSerializer,
    ProjectEnrollmentSerializer,
    EvolutionRecordSerializer,
    ActionPlanSerializer,
    WheelOfLifeSerializer
)

from members.models import Beneficiary
from social.models import SocialAnamnesis
from projects.models import ProjectEnrollment
from evolution.models import EvolutionRecord
from coaching.models import ActionPlan, WheelOfLife


class BeneficiaryViewSet(viewsets.ModelViewSet):
    queryset = Beneficiary.optimized_objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['neighbourhood', 'created_at']
    search_fields = ['full_name', 'nis']
    ordering_fields = ['full_name', 'created_at']


class SocialAnamnesisViewSet(viewsets.ModelViewSet):
    queryset = SocialAnamnesis.optimized_objects.all()
    serializer_class = SocialAnamnesisSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'housing_situation', 'marital_status']
    search_fields = ['beneficiary__full_name', 'housing_situation']
    ordering_fields = ['created_at', 'updated_at']


class ProjectEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectEnrollment.objects.all()  # ProjectEnrollment não tem manager otimizado
    serializer_class = ProjectEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['project_name', 'weekday', 'shift', 'status']
    search_fields = ['project_name', 'beneficiary__full_name']
    ordering_fields = ['project_name', 'created_at']


class EvolutionRecordViewSet(viewsets.ModelViewSet):
    queryset = EvolutionRecord.optimized_objects.all()
    serializer_class = EvolutionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'status', 'created_at']
    search_fields = ['beneficiary__full_name', 'notes']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


class ActionPlanViewSet(viewsets.ModelViewSet):
    queryset = ActionPlan.objects.all()  # ActionPlan não tem manager otimizado
    serializer_class = ActionPlanSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ['beneficiary', 'status']
    ordering_fields = ['created_at', 'target_date']
    ordering = ['-created_at']


class WheelOfLifeViewSet(viewsets.ModelViewSet):
    queryset = WheelOfLife.objects.all()  # WheelOfLife não tem manager otimizado
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
        """Exporta dados da beneficiária em formato ZIP"""
        try:
            beneficiary = get_object_or_404(Beneficiary, pk=pk)
            
            # Verificar permissões - só staff ou a própria beneficiária
            if not (request.user.is_staff or request.user == beneficiary.user):
                return Response(
                    {'error': 'Você não tem permissão para exportar estes dados'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                    
                    # Dados da beneficiária em JSON
                    beneficiary_data = {
                        'id': beneficiary.id,
                        'full_name': beneficiary.full_name,
                        'nis': beneficiary.nis,
                        'cpf': beneficiary.cpf,
                        'phone': beneficiary.phone,
                        'neighbourhood': beneficiary.neighbourhood,
                        'created_at': beneficiary.created_at.isoformat() if beneficiary.created_at else None,
                    }
                    
                    zip_file.writestr(
                        'beneficiaria.json',
                        json.dumps(beneficiary_data, indent=2, ensure_ascii=False)
                    )
                    
                    # Anamnese social se existir
                    try:
                        anamnesis = beneficiary.socialanamnesis
                        anamnesis_data = {
                            'housing_situation': anamnesis.housing_situation,
                            'marital_status': anamnesis.marital_status,
                            'family_income': str(anamnesis.family_income) if anamnesis.family_income else None,
                            'created_at': anamnesis.created_at.isoformat() if anamnesis.created_at else None,
                        }
                        zip_file.writestr(
                            'anamnese_social.json',
                            json.dumps(anamnesis_data, indent=2, ensure_ascii=False)
                        )
                    except SocialAnamnesis.DoesNotExist:
                        pass
                    
                    # Registros de evolução
                    evolution_records = EvolutionRecord.objects.filter(beneficiary=beneficiary)
                    if evolution_records.exists():
                        evolution_data = []
                        for record in evolution_records:
                            evolution_data.append({
                                'id': record.id,
                                'notes': record.notes,
                                'status': record.status,
                                'created_at': record.created_at.isoformat() if record.created_at else None,
                            })
                        
                        zip_file.writestr(
                            'registros_evolucao.json',
                            json.dumps(evolution_data, indent=2, ensure_ascii=False)
                        )
            
            # Retornar arquivo
            response = FileResponse(
                open(temp_file.name, 'rb'),
                as_attachment=True,
                filename=f'dados_beneficiaria_{beneficiary.id}.zip'
            )
            
            # Limpar arquivo temporário após envio
            def cleanup():
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass
            
            response.close = cleanup
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao exportar dados: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
