"""
Views da API para notificações
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from notifications.models import Notification, NotificationPreference, NotificationTemplate, NotificationChannel
from .serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    NotificationTemplateSerializer,
    NotificationChannelSerializer,
    BulkNotificationSerializer,
    NotificationStatsSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificações
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'priority', 'is_read']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar notificações do usuário atual"""
        return Notification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Adicionar usuário atual como destinatário"""
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        responses={200: NotificationSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marcar notificação como lida"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'message': 'Notificação marcada como lida',
            'notification': NotificationSerializer(notification).data
        })
    
    @swagger_auto_schema(
        responses={200: NotificationSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Marcar notificação como não lida"""
        notification = self.get_object()
        notification.is_read = False
        notification.read_at = None
        notification.save()
        
        return Response({
            'message': 'Notificação marcada como não lida',
            'notification': NotificationSerializer(notification).data
        })
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Notificações não lidas')}
    )
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Obter notificações não lidas"""
        unread_notifications = self.get_queryset().filter(is_read=False)
        
        page = self.paginate_queryset(unread_notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Contador de notificações')}
    )
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Contar notificações por status"""
        queryset = self.get_queryset()
        
        return Response({
            'total': queryset.count(),
            'unread': queryset.filter(is_read=False).count(),
            'read': queryset.filter(is_read=True).count(),
            'today': queryset.filter(created_at__date=timezone.now().date()).count(),
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para preferências de notificação
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar preferências do usuário atual"""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Obter ou criar preferências do usuário"""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def perform_create(self, serializer):
        """Adicionar usuário atual"""
        serializer.save(user=self.request.user)


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para templates de notificação (apenas leitura)
    """
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'subject', 'content']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SendBulkNotificationAPIView(APIView):
    """
    API para envio de notificações em lote
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        request_body=BulkNotificationSerializer,
        responses={
            201: openapi.Response('Notificações enviadas'),
            400: 'Dados inválidos',
            403: 'Sem permissão'
        }
    )
    def post(self, request):
        """Enviar notificações em lote"""
        serializer = BulkNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            title = serializer.validated_data['title']
            message = serializer.validated_data['message']
            users = serializer.validated_data['users']
            category = serializer.validated_data.get('category', 'info')
            priority = serializer.validated_data.get('priority', 'medium')
            
            notifications_created = []
            
            for user in users:
                notification = Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    category=category,
                    priority=priority,
                    send_email=serializer.validated_data.get('send_email', False),
                    send_push=serializer.validated_data.get('send_push', False),
                    send_in_app=serializer.validated_data.get('send_in_app', True)
                )
                
                # Enviar notificação
                try:
                    notification.send_notification()
                    notifications_created.append(notification.id)
                except Exception as e:
                    # Log do erro, mas continua processando
                    pass
            
            return Response({
                'message': f'{len(notifications_created)} notificações enviadas com sucesso',
                'notifications_created': notifications_created
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarkAllReadAPIView(APIView):
    """
    API para marcar todas as notificações como lidas
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: openapi.Response('Notificações marcadas como lidas')}
    )
    def post(self, request):
        """Marcar todas as notificações como lidas"""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notificações marcadas como lidas',
            'updated_count': updated_count
        })


class NotificationStatsAPIView(APIView):
    """
    API para estatísticas de notificações
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: NotificationStatsSerializer}
    )
    def get(self, request):
        """Obter estatísticas de notificações do usuário"""
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        user_notifications = Notification.objects.filter(user=request.user)
        
        # Estatísticas gerais
        total_notifications = user_notifications.count()
        unread_notifications = user_notifications.filter(is_read=False).count()
        
        # Notificações dos últimos 30 dias
        last_30_days = timezone.now() - timedelta(days=30)
        recent_notifications = user_notifications.filter(
            created_at__gte=last_30_days
        ).count()
        
        # Notificações por categoria
        category_stats = user_notifications.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Notificações por prioridade
        priority_stats = user_notifications.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Taxa de leitura
        read_rate = 0
        if total_notifications > 0:
            read_count = total_notifications - unread_notifications
            read_rate = round((read_count / total_notifications) * 100, 2)
        
        data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'recent_notifications': recent_notifications,
            'read_rate': read_rate,
            'category_stats': list(category_stats),
            'priority_stats': list(priority_stats)
        }
        
        serializer = NotificationStatsSerializer(data)
        return Response(serializer.data)


class NotificationChannelListAPIView(APIView):
    """
    API para listar canais de notificação
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: NotificationChannelSerializer(many=True)}
    )
    def get(self, request):
        """Listar canais de notificação ativos"""
        channels = NotificationChannel.objects.filter(is_active=True)
        serializer = NotificationChannelSerializer(channels, many=True)
        return Response(serializer.data)
