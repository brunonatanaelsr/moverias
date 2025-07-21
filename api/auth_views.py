"""
Views de autenticação da API
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer, 
    LoginSerializer, 
    ChangePasswordSerializer,
    ResetPasswordSerializer
)

User = get_user_model()


class LoginAPIView(APIView):
    """
    API view para login de usuários
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login realizado com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Dados inválidos",
            401: "Credenciais inválidas"
        }
    )
    def post(self, request):
        """Login de usuário"""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user:
                if user.is_active:
                    token, created = Token.objects.get_or_create(user=user)
                    
                    return Response({
                        'token': token.key,
                        'user': UserSerializer(user).data,
                        'message': 'Login realizado com sucesso'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Conta desativada'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'error': 'Credenciais inválidas'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API view para logout de usuários
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Logout realizado com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )
    def post(self, request):
        """Logout de usuário"""
        try:
            # Deletar o token do usuário
            request.user.auth_token.delete()
            return Response({
                'message': 'Logout realizado com sucesso'
            }, status=status.HTTP_200_OK)
        except:
            return Response({
                'error': 'Erro ao realizar logout'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
    API view para perfil do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: UserSerializer
        }
    )
    def get(self, request):
        """Obter perfil do usuário"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Dados inválidos"
        }
    )
    def put(self, request):
        """Atualizar perfil do usuário"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPIView(APIView):
    """
    API view para alterar senha
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Senha alterada com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Dados inválidos"
        }
    )
    def post(self, request):
        """Alterar senha do usuário"""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Verificar senha atual
            if not request.user.check_password(old_password):
                return Response({
                    'error': 'Senha atual incorreta'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar nova senha
            try:
                validate_password(new_password, request.user)
            except ValidationError as e:
                return Response({
                    'error': list(e.messages)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Alterar senha
            request.user.set_password(new_password)
            request.user.save()
            
            return Response({
                'message': 'Senha alterada com sucesso'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    """
    API view para reset de senha
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Email de reset enviado",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Dados inválidos"
        }
    )
    def post(self, request):
        """Solicitar reset de senha"""
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Aqui você implementaria o envio de email
                # Por enquanto, apenas retornamos sucesso
                
                return Response({
                    'message': 'Email de reset de senha enviado'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Por segurança, não revelamos se o email existe
                return Response({
                    'message': 'Se o email existir, um link de reset foi enviado'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
