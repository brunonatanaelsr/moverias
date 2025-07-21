"""
Views da API para certificados
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from certificates.models import Certificate, CertificateRequest, CertificateTemplate
from .serializers import (
    CertificateSerializer,
    CertificateRequestSerializer, 
    CertificateTemplateSerializer,
    CertificateStatsSerializer
)


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para certificados
    """
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'template__category', 'issued_date']
    search_fields = ['title', 'member__full_name', 'description']
    ordering_fields = ['issued_date', 'created_at']
    ordering = ['-issued_date']
    
    def get_queryset(self):
        """Filtrar certificados do usuário ou todos se for staff"""
        if self.request.user.is_staff:
            return Certificate.objects.all()
        return Certificate.objects.filter(member__user=self.request.user)
    
    @swagger_auto_schema(
        responses={200: CertificateSerializer}
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download do PDF do certificado"""
        certificate = self.get_object()
        
        if certificate.pdf_file:
            response = HttpResponse(
                certificate.pdf_file.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="certificado_{certificate.id}.pdf"'
            return response
        
        return Response({'error': 'PDF não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Certificado verificado')}
    )
    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        """Verificar autenticidade do certificado"""
        certificate = self.get_object()
        
        return Response({
            'valid': True,
            'certificate': CertificateSerializer(certificate).data,
            'verification_date': certificate.issued_date
        })


class CertificateRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para solicitações de certificado
    """
    queryset = CertificateRequest.objects.all()
    serializer_class = CertificateRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'workshop']
    search_fields = ['member__full_name', 'workshop__name']
    ordering_fields = ['created_at', 'approved_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar solicitações do usuário ou todas se for staff"""
        if self.request.user.is_staff:
            return CertificateRequest.objects.all()
        return CertificateRequest.objects.filter(member__user=self.request.user)
    
    @swagger_auto_schema(
        responses={200: CertificateRequestSerializer}
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprovar solicitação de certificado"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Apenas administradores podem aprovar certificados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        certificate_request = self.get_object()
        
        try:
            certificate = certificate_request.approve()
            return Response({
                'message': 'Certificado aprovado e gerado com sucesso',
                'certificate': CertificateSerializer(certificate).data
            })
        except Exception as e:
            return Response(
                {'error': f'Erro ao aprovar certificado: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: CertificateRequestSerializer}
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeitar solicitação de certificado"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Apenas administradores podem rejeitar certificados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        certificate_request = self.get_object()
        reason = request.data.get('reason', 'Não especificado')
        
        certificate_request.reject(reason)
        
        return Response({
            'message': 'Certificado rejeitado',
            'request': CertificateRequestSerializer(certificate_request).data
        })


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para templates de certificado
    """
    queryset = CertificateTemplate.objects.filter(is_active=True)
    serializer_class = CertificateTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        """Apenas staff pode criar/editar templates"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class GenerateCertificateAPIView(APIView):
    """
    API para gerar certificado
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'member_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'workshop_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'template_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['member_id', 'workshop_id']
        ),
        responses={
            201: CertificateSerializer,
            400: 'Dados inválidos',
            403: 'Sem permissão'
        }
    )
    def post(self, request):
        """Gerar novo certificado"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Apenas administradores podem gerar certificados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Implementar lógica de geração
        # Por enquanto, retorna erro
        return Response(
            {'error': 'Funcionalidade em desenvolvimento'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DownloadCertificateAPIView(APIView):
    """
    API para download de certificado
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response('PDF do certificado'),
            404: 'Certificado não encontrado'
        }
    )
    def get(self, request, certificate_id):
        """Download do PDF do certificado"""
        try:
            certificate = Certificate.objects.get(id=certificate_id)
            
            # Verificar permissão
            if not request.user.is_staff and certificate.member.user != request.user:
                return Response(
                    {'error': 'Sem permissão para acessar este certificado'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if certificate.pdf_file:
                response = HttpResponse(
                    certificate.pdf_file.read(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="certificado_{certificate.id}.pdf"'
                return response
            
            return Response(
                {'error': 'PDF não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Certificate.DoesNotExist:
            raise Http404("Certificado não encontrado")


class VerifyCertificateAPIView(APIView):
    """
    API para verificar certificado
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response('Certificado verificado'),
            404: 'Certificado não encontrado'
        }
    )
    def get(self, request, verification_code):
        """Verificar autenticidade do certificado pelo código"""
        try:
            certificate = Certificate.objects.get(verification_code=verification_code)
            
            return Response({
                'valid': True,
                'certificate': {
                    'title': certificate.title,
                    'member_name': certificate.member.full_name,
                    'issued_date': certificate.issued_date,
                    'workshop_name': certificate.workshop.name if certificate.workshop else None,
                    'description': certificate.description
                },
                'verification_date': certificate.issued_date
            })
            
        except Certificate.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Certificado não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class CertificateStatsAPIView(APIView):
    """
    API para estatísticas de certificados
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        responses={200: CertificateStatsSerializer}
    )
    def get(self, request):
        """Obter estatísticas de certificados"""
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Estatísticas gerais
        total_certificates = Certificate.objects.count()
        total_requests = CertificateRequest.objects.count()
        pending_requests = CertificateRequest.objects.filter(status='pending').count()
        approved_requests = CertificateRequest.objects.filter(status='approved').count()
        
        # Certificados por mês (últimos 12 meses)
        now = datetime.now()
        monthly_stats = []
        
        for i in range(12):
            month_start = now.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)
            
            count = Certificate.objects.filter(
                issued_date__range=[month_start, month_end]
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        # Certificados por categoria
        category_stats = Certificate.objects.values(
            'template__category'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        data = {
            'total_certificates': total_certificates,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'monthly_stats': monthly_stats,
            'category_stats': list(category_stats)
        }
        
        serializer = CertificateStatsSerializer(data)
        return Response(serializer.data)
