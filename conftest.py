"""
Configurações globais para testes
"""
import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

# Configurar Django para testes
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Setup do banco de dados para testes"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """Cliente para testes de API"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_user():
    """Usuário autenticado para testes"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        full_name='Test User'
    )
    return user


@pytest.fixture
def admin_user():
    """Usuário administrador para testes"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        full_name='Admin User'
    )
    return user


@pytest.fixture
def sample_beneficiary():
    """Beneficiária de exemplo para testes"""
    from members.models import Beneficiary
    from datetime import date
    # Use optimized_objects if available, fallback to objects
    manager = getattr(Beneficiary, 'optimized_objects', Beneficiary.objects)
    return manager.create(
        full_name='Maria Silva',
        dob=date(1990, 5, 15),
        nis='12345678901',
        phone_1='(11) 99999-9999',
        cpf='12345678901',
        rg='123456789',
        address='Rua das Flores, 123',
        neighbourhood='Centro',
        status='ATIVA'
    )


@pytest.fixture
def sample_project():
    """Projeto de exemplo para testes"""
    from projects.models import Project
    from datetime import date, timedelta
    # Use optimized_objects if available, fallback to objects
    manager = getattr(Project, 'optimized_objects', Project.objects)
    return manager.create(
        name='Projeto Teste',
        description='Descrição do projeto teste',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status='ATIVO'
    )


@pytest.fixture
def sample_activity(sample_beneficiary, authenticated_user):
    """Atividade de exemplo para testes"""
    from activities.models import BeneficiaryActivity
    from datetime import date, timedelta
    # Use optimized_objects if available, fallback to objects
    manager = getattr(BeneficiaryActivity, 'optimized_objects', BeneficiaryActivity.objects)
    return manager.create(
        beneficiary=sample_beneficiary,
        title='Atividade Teste',
        description='Descrição da atividade teste',
        activity_type='WORKSHOP',
        status='ACTIVE',
        priority='MEDIUM',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=15),
        facilitator='Facilitador Teste',
        location='Sala 1',
        objectives='Objetivos da atividade',
        expected_outcomes='Resultados esperados',
        created_by=authenticated_user
    )


@pytest.fixture
def client_with_csrf():
    """Cliente com CSRF token para testes de formulários"""
    from django.test import Client
    from django.middleware.csrf import get_token
    
    client = Client(enforce_csrf_checks=True)
    # Simular primeira requisição para obter CSRF token
    response = client.get('/')
    return client


# Markers personalizados
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.api = pytest.mark.api
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance
pytest.mark.smoke = pytest.mark.smoke
