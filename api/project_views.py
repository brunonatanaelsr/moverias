"""
Views da API para projetos
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import (
    Project, ProjectEnrollment, ProjectSession, 
    ProjectAttendance, ProjectEvaluation, ProjectResource
)
from .serializers import (
    ProjectSerializer,
    ProjectEnrollmentSerializer,
    ProjectSessionSerializer,
    ProjectAttendanceSerializer,
    ProjectEvaluationSerializer,
    ProjectResourceSerializer,
    ProjectStatsSerializer,
    AttendanceReportSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet para projetos
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'coordinator']
    search_fields = ['name', 'description', 'coordinator']
    ordering_fields = ['name', 'start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_permissions(self):
        """Apenas staff pode criar/editar projetos"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        responses={200: ProjectEnrollmentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Listar participantes do projeto"""
        project = self.get_object()
        enrollments = project.enrollments.filter(status='ATIVO')
        
        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = ProjectEnrollmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        responses={200: ProjectSessionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Listar sessões do projeto"""
        project = self.get_object()
        sessions = project.sessions.all()
        
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = ProjectSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Estatísticas do projeto')}
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Estatísticas do projeto"""
        project = self.get_object()
        
        return Response({
            'total_participants': project.total_participants,
            'total_sessions': project.total_sessions,
            'attendance_rate': project.attendance_rate,
            'completion_rate': project.get_completion_rate(),
            'active_participants': project.get_active_participants().count()
        })


class ProjectEnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para inscrições em projetos
    """
    queryset = ProjectEnrollment.objects.all()
    serializer_class = ProjectEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'status', 'weekday', 'shift']
    search_fields = ['beneficiary__full_name', 'project__name']
    ordering_fields = ['created_at', 'project__name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar inscrições conforme permissão do usuário"""
        if self.request.user.is_staff:
            return ProjectEnrollment.objects.all()
        # Para usuários normais, retornar suas próprias inscrições
        return ProjectEnrollment.objects.filter(beneficiary__user=self.request.user)
    
    @swagger_auto_schema(
        responses={200: ProjectAttendanceSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def attendances(self, request, pk=None):
        """Listar presenças da inscrição"""
        enrollment = self.get_object()
        attendances = enrollment.attendances.all()
        
        page = self.paginate_queryset(attendances)
        if page is not None:
            serializer = ProjectAttendanceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectAttendanceSerializer(attendances, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Taxa de presença')}
    )
    @action(detail=True, methods=['get'])
    def attendance_rate(self, request, pk=None):
        """Taxa de presença da inscrição"""
        enrollment = self.get_object()
        
        return Response({
            'enrollment_id': enrollment.id,
            'attendance_rate': enrollment.attendance_rate,
            'total_sessions': enrollment.attendances.count(),
            'attended_sessions': enrollment.attendances.filter(attended=True).count()
        })


class ProjectSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para sessões de projeto
    """
    queryset = ProjectSession.objects.all()
    serializer_class = ProjectSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'facilitator', 'is_mandatory']
    search_fields = ['topic', 'description', 'facilitator']
    ordering_fields = ['session_date', 'start_time']
    ordering = ['-session_date', '-start_time']
    
    def get_permissions(self):
        """Apenas staff pode criar/editar sessões"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @swagger_auto_schema(
        responses={200: ProjectAttendanceSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def attendances(self, request, pk=None):
        """Listar presenças da sessão"""
        session = self.get_object()
        attendances = session.attendances.all()
        
        page = self.paginate_queryset(attendances)
        if page is not None:
            serializer = ProjectAttendanceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectAttendanceSerializer(attendances, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'attendances': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'enrollment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'attended': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'notes': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            }
        ),
        responses={200: openapi.Response('Presença registrada')}
    )
    @action(detail=True, methods=['post'])
    def take_attendance(self, request, pk=None):
        """Registrar presença na sessão"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Apenas administradores podem registrar presença'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session = self.get_object()
        attendances_data = request.data.get('attendances', [])
        
        created_count = 0
        updated_count = 0
        
        for attendance_data in attendances_data:
            enrollment_id = attendance_data.get('enrollment_id')
            attended = attendance_data.get('attended', False)
            notes = attendance_data.get('notes', '')
            
            try:
                enrollment = ProjectEnrollment.objects.get(id=enrollment_id)
                attendance, created = ProjectAttendance.objects.get_or_create(
                    session=session,
                    enrollment=enrollment,
                    defaults={
                        'attended': attended,
                        'notes': notes
                    }
                )
                
                if not created:
                    attendance.attended = attended
                    attendance.notes = notes
                    attendance.save()
                    updated_count += 1
                else:
                    created_count += 1
                    
            except ProjectEnrollment.DoesNotExist:
                continue
        
        return Response({
            'message': 'Presença registrada com sucesso',
            'created': created_count,
            'updated': updated_count
        })


class ProjectAttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para presenças em projetos
    """
    queryset = ProjectAttendance.objects.all()
    serializer_class = ProjectAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session', 'enrollment', 'attended']
    search_fields = ['enrollment__beneficiary__full_name', 'session__topic']
    ordering_fields = ['session__session_date', 'created_at']
    ordering = ['-session__session_date']
    
    def get_queryset(self):
        """Filtrar presenças conforme permissão do usuário"""
        if self.request.user.is_staff:
            return ProjectAttendance.objects.all()
        # Para usuários normais, retornar suas próprias presenças
        return ProjectAttendance.objects.filter(enrollment__beneficiary__user=self.request.user)
    
    def get_permissions(self):
        """Apenas staff pode criar/editar presenças"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class ProjectEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para avaliações de projeto
    """
    queryset = ProjectEvaluation.objects.all()
    serializer_class = ProjectEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment', 'rating', 'would_recommend']
    search_fields = ['feedback', 'suggestions']
    ordering_fields = ['evaluation_date', 'rating']
    ordering = ['-evaluation_date']
    
    def get_queryset(self):
        """Filtrar avaliações conforme permissão do usuário"""
        if self.request.user.is_staff:
            return ProjectEvaluation.objects.all()
        # Para usuários normais, retornar suas próprias avaliações
        return ProjectEvaluation.objects.filter(enrollment__beneficiary__user=self.request.user)
    
    def perform_create(self, serializer):
        """Verificar se o usuário pode criar avaliação"""
        enrollment = serializer.validated_data['enrollment']
        if not self.request.user.is_staff and enrollment.beneficiary.user != self.request.user:
            raise permissions.PermissionDenied("Você não pode avaliar esta inscrição")
        
        serializer.save()


class ProjectResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para recursos de projeto
    """
    queryset = ProjectResource.objects.all()
    serializer_class = ProjectResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'resource_type', 'is_available']
    search_fields = ['name', 'description', 'supplier']
    ordering_fields = ['name', 'acquisition_date', 'cost']
    ordering = ['project__name', 'name']
    
    def get_permissions(self):
        """Apenas staff pode gerenciar recursos"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class ProjectStatsAPIView(APIView):
    """
    API para estatísticas gerais de projetos
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: ProjectStatsSerializer}
    )
    def get(self, request):
        """Obter estatísticas gerais de projetos"""
        from django.db.models import Count, Avg
        
        # Estatísticas gerais
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='ATIVO').count()
        total_enrollments = ProjectEnrollment.objects.count()
        active_enrollments = ProjectEnrollment.objects.filter(status='ATIVO').count()
        
        # Projetos por status
        project_status_stats = Project.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Taxa de presença média
        avg_attendance_rate = ProjectAttendance.objects.filter(
            attended=True
        ).count() / ProjectAttendance.objects.count() * 100 if ProjectAttendance.objects.count() > 0 else 0
        
        # Avaliação média
        avg_rating = ProjectEvaluation.objects.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        data = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'project_status_stats': list(project_status_stats),
            'avg_attendance_rate': round(avg_attendance_rate, 2),
            'avg_rating': round(avg_rating, 2)
        }
        
        serializer = ProjectStatsSerializer(data)
        return Response(serializer.data)


class ProjectParticipantsAPIView(APIView):
    """
    API para participantes de um projeto específico
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: ProjectEnrollmentSerializer(many=True)}
    )
    def get(self, request, project_id):
        """Listar participantes de um projeto"""
        project = get_object_or_404(Project, id=project_id)
        enrollments = project.enrollments.filter(status='ATIVO')
        
        serializer = ProjectEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


class AttendanceReportAPIView(APIView):
    """
    API para relatório de presença de um projeto
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        responses={200: AttendanceReportSerializer}
    )
    def get(self, request, project_id):
        """Gerar relatório de presença do projeto"""
        project = get_object_or_404(Project, id=project_id)
        
        # Dados do relatório
        sessions = project.sessions.all()
        enrollments = project.enrollments.filter(status='ATIVO')
        
        report_data = []
        
        for enrollment in enrollments:
            participant_data = {
                'enrollment_id': enrollment.id,
                'participant_name': enrollment.beneficiary.full_name,
                'total_sessions': sessions.count(),
                'attended_sessions': enrollment.attendances.filter(attended=True).count(),
                'attendance_rate': enrollment.attendance_rate,
                'sessions_detail': []
            }
            
            for session in sessions:
                try:
                    attendance = ProjectAttendance.objects.get(
                        session=session,
                        enrollment=enrollment
                    )
                    session_data = {
                        'session_id': session.id,
                        'session_date': session.session_date,
                        'topic': session.topic,
                        'attended': attendance.attended,
                        'notes': attendance.notes
                    }
                except ProjectAttendance.DoesNotExist:
                    session_data = {
                        'session_id': session.id,
                        'session_date': session.session_date,
                        'topic': session.topic,
                        'attended': False,
                        'notes': 'Não registrado'
                    }
                
                participant_data['sessions_detail'].append(session_data)
            
            report_data.append(participant_data)
        
        data = {
            'project_id': project.id,
            'project_name': project.name,
            'total_participants': len(report_data),
            'total_sessions': sessions.count(),
            'overall_attendance_rate': project.attendance_rate,
            'participants': report_data
        }
        
        serializer = AttendanceReportSerializer(data)
        return Response(serializer.data)


class TakeAttendanceAPIView(APIView):
    """
    API para registrar presença em uma sessão
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'attendances': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'enrollment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'attended': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'notes': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            }
        ),
        responses={200: openapi.Response('Presença registrada')}
    )
    def post(self, request, session_id):
        """Registrar presença em uma sessão específica"""
        session = get_object_or_404(ProjectSession, id=session_id)
        attendances_data = request.data.get('attendances', [])
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for attendance_data in attendances_data:
            enrollment_id = attendance_data.get('enrollment_id')
            attended = attendance_data.get('attended', False)
            notes = attendance_data.get('notes', '')
            
            try:
                enrollment = ProjectEnrollment.objects.get(
                    id=enrollment_id,
                    project=session.project
                )
                
                attendance, created = ProjectAttendance.objects.get_or_create(
                    session=session,
                    enrollment=enrollment,
                    defaults={
                        'attended': attended,
                        'notes': notes
                    }
                )
                
                if not created:
                    attendance.attended = attended
                    attendance.notes = notes
                    attendance.save()
                    updated_count += 1
                else:
                    created_count += 1
                    
            except ProjectEnrollment.DoesNotExist:
                errors.append(f'Inscrição {enrollment_id} não encontrada')
            except Exception as e:
                errors.append(f'Erro na inscrição {enrollment_id}: {str(e)}')
        
        response_data = {
            'message': 'Presença registrada',
            'created': created_count,
            'updated': updated_count
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data)
