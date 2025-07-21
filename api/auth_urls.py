"""
URLs de autenticação da API
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import auth_views

app_name = 'api_auth'

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Custom auth endpoints
    path('login/', auth_views.LoginAPIView.as_view(), name='login'),
    path('logout/', auth_views.LogoutAPIView.as_view(), name='logout'),
    path('profile/', auth_views.UserProfileAPIView.as_view(), name='profile'),
    path('change-password/', auth_views.ChangePasswordAPIView.as_view(), name='change_password'),
    path('reset-password/', auth_views.ResetPasswordAPIView.as_view(), name='reset_password'),
]
