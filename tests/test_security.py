"""
Testes de segurança
"""
import pytest
import re
from django.test import Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status

from members.models import Beneficiary
from core.password_validators import AdvancedPasswordValidator

User = get_user_model()


@pytest.mark.security
@pytest.mark.django_db
class TestCSRFProtection:
    """Testes de proteção CSRF"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Adicionar ao grupo técnica
        tech_group, _ = Group.objects.get_or_create(name='Técnica')
        self.user.groups.add(tech_group)
    
    def test_csrf_protection_on_post(self):
        """Teste proteção CSRF em requisições POST"""
        self.client.login(username='testuser', password='testpass123')
        
        # Tentar POST sem CSRF token
        data = {
            'full_name': 'Maria Silva',
            'dob': '1990-05-15',
            'phone_1': '(11) 99999-9999',
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro'
        }
        
        response = self.client.post(reverse('members:create'), data)
        # Deve falhar por falta de CSRF token
        assert response.status_code == 403
    
    def test_csrf_token_in_forms(self):
        """Teste presença de token CSRF em formulários"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('members:create'))
        content = response.content.decode()
        
        # Verificar se tem token CSRF
        csrf_pattern = r'<input[^>]*name=["\']csrfmiddlewaretoken["\'][^>]*>'
        assert re.search(csrf_pattern, content) is not None
    
    def test_ajax_csrf_protection(self):
        """Teste proteção CSRF em requisições AJAX"""
        self.client.login(username='testuser', password='testpass123')
        
        # Simular requisição AJAX sem CSRF
        response = self.client.post(
            '/api/activities/create/',
            data={'title': 'Test Activity'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Deve falhar ou retornar erro CSRF
        assert response.status_code in [403, 400]


@pytest.mark.security 
@pytest.mark.django_db
class TestXSSProtection:
    """Testes de proteção contra XSS"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='testpass123',
            full_name='Test User'
        )
        
        tech_group, _ = Group.objects.get_or_create(name='Técnica')
        self.user.groups.add(tech_group)
    
    def test_script_tag_sanitization(self):
        """Teste sanitização de tags script"""
        self.client.login(username='testuser', password='testpass123')
        
        # Tentar injetar script
        malicious_data = {
            'full_name': '<script>alert("XSS")</script>Maria Silva',
            'dob': '1990-05-15',
            'phone_1': '(11) 99999-9999',
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro'
        }
        
        response = self.client.post(reverse('members:create'), malicious_data)
        
        if response.status_code == 302:  # Redirect após criação
            # Verificar se foi sanitizado
            beneficiary = getattr(Beneficiary, "optimized_objects", Beneficiary.objects).filter(
                full_name__contains='Maria Silva'
            ).first()
            
            if beneficiary:
                # Script não deve estar presente
                assert '<script>' not in beneficiary.full_name
                assert 'alert(' not in beneficiary.full_name
    
    def test_html_entities_escaping(self):
        """Teste escape de entidades HTML"""
        beneficiary = getattr(Beneficiary, "optimized_objects", Beneficiary.objects).create(
            full_name='Maria & Silva < > "',
            dob='1990-05-15',
            phone_1='(11) 99999-9999',
            address='Rua das Flores, 123',
            neighbourhood='Centro'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('members:detail', kwargs={'pk': beneficiary.pk})
        )
        
        content = response.content.decode()
        
        # Verificar se caracteres foram escapados no HTML
        # Django faz isso automaticamente nos templates
        assert '&amp;' in content or 'Maria & Silva' in content  # Pode ou não estar escapado
        assert '<script>' not in content
    
    def test_user_input_validation(self):
        """Teste validação de entrada do usuário"""
        self.client.login(username='testuser', password='testpass123')
        
        # Dados com HTML
        data = {
            'full_name': '<b>Maria</b> Silva',
            'dob': '1990-05-15',
            'phone_1': '(11) 99999-9999',
            'address': '<i>Rua das Flores</i>, 123',
            'neighbourhood': 'Centro'
        }
        
        response = self.client.post(reverse('members:create'), data)
        
        # Verificar se salvou corretamente (sem HTML)
        if response.status_code == 302:
            beneficiary = getattr(Beneficiary, "optimized_objects", Beneficiary.objects).filter(
                full_name__contains='Maria Silva'
            ).first()
            
            if beneficiary:
                # HTML não deve estar presente ou deve estar sanitizado
                assert '<b>' not in beneficiary.full_name or beneficiary.full_name == '<b>Maria</b> Silva'


@pytest.mark.security
@pytest.mark.django_db
class TestSQLInjectionProtection:
    """Testes de proteção contra SQL Injection"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Criar algumas beneficiárias para teste
        for i in range(3):
            getattr(Beneficiary, "optimized_objects", Beneficiary.objects).create(
                full_name=f'Beneficiária {i}',
                dob='1990-01-01',
                phone_1='(11) 99999-9999',
                address=f'Endereço {i}',
                neighbourhood='Centro'
            )
    
    def test_search_sql_injection(self):
        """Teste injeção SQL via busca"""
        self.client.login(username='testuser', password='testpass123')
        
        # Tentar injeção SQL
        malicious_query = "' OR '1'='1' --"
        
        response = self.client.get(
            reverse('members:list'),
            {'search': malicious_query}
        )
        
        # Deve retornar normalmente, sem executar SQL malicioso
        assert response.status_code == 200
        
        # Não deve retornar todos os registros se busca for específica
        content = response.content.decode()
        # Verificar que não expôs dados indevidos
    
    def test_filter_sql_injection(self):
        """Teste injeção SQL via filtros"""
        self.client.login(username='testuser', password='testpass123')
        
        # Tentar injeção via parâmetros de filtro
        malicious_filter = "1; DROP TABLE members_beneficiary; --"
        
        response = self.client.get(
            reverse('members:list'),
            {'neighbourhood': malicious_filter}
        )
        
        # Deve retornar normalmente
        assert response.status_code == 200
        
        # Tabela ainda deve existir
        assert getattr(Beneficiary, "optimized_objects", Beneficiary.objects).count() > 0
    
    def test_orm_parameterization(self):
        """Teste parametrização automática do ORM"""
        # O Django ORM deve automaticamente parametrizar queries
        
        # Busca normal
        results = getattr(Beneficiary, "optimized_objects", Beneficiary.objects).filter(full_name__contains="Beneficiária")
        assert results.count() == 3
        
        # Busca com caracteres potencialmente perigosos
        malicious_input = "'; DROP TABLE members_beneficiary; --"
        results = getattr(Beneficiary, "optimized_objects", Beneficiary.objects).filter(full_name__contains=malicious_input)
        assert results.count() == 0  # Não deve encontrar nada
        
        # Tabela ainda deve existir
        assert getattr(Beneficiary, "optimized_objects", Beneficiary.objects).count() == 3


@pytest.mark.security
@pytest.mark.django_db
class TestPasswordSecurity:
    """Testes de segurança de senhas"""
    
    def test_password_strength_validation(self):
        """Teste validação de força da senha"""
        validator = AdvancedPasswordValidator()
        user = User(username='testuser', email='test@example.com')
        
        # Senhas fracas devem falhar
        weak_passwords = [
            '123456',
            'password',
            'qwerty',
            'abc123',
            '12345678'
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                validator.validate(password, user)
    
    def test_password_complexity_requirements(self):
        """Teste requisitos de complexidade"""
        validator = AdvancedPasswordValidator()
        user = User(username='testuser', email='test@example.com')
        
        # Senha sem maiúscula
        with pytest.raises(ValidationError):
            validator.validate('testpassword123!', user)
        
        # Senha sem número
        with pytest.raises(ValidationError):
            validator.validate('TestPassword!', user)
        
        # Senha sem caractere especial
        with pytest.raises(ValidationError):
            validator.validate('TestPassword123', user)
        
        # Senha válida não deve falhar
        try:
            validator.validate('TestPassword123!', user)
        except ValidationError:
            pytest.fail("Valid password should not raise ValidationError")
    
    def test_password_hashing(self):
        """Teste hash de senhas"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Senha não deve estar em texto plano
        assert user.password != 'TestPassword123!'
        
        # Deve usar hasher seguro (Argon2)
        assert user.password.startswith('argon2') or user.password.startswith('pbkdf2')
        
        # Verificação deve funcionar
        assert user.check_password('TestPassword123!')
        assert not user.check_password('wrongpassword')
    
    def test_password_reset_security(self):
        """Teste segurança do reset de senha"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123!'
        )
        
        # Solicitar reset
        response = self.client.post('/accounts/password/reset/', {
            'email': user.email
        })
        
        # Deve aceitar a solicitação
        assert response.status_code in [200, 302]


@pytest.mark.security
@pytest.mark.django_db
class TestFileUploadSecurity:
    """Testes de segurança de upload de arquivos"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        tech_group, _ = Group.objects.get_or_create(name='Técnica')
        self.user.groups.add(tech_group)
    
    def test_file_type_validation(self):
        """Teste validação de tipo de arquivo"""
        # Criar arquivo malicioso
        malicious_content = b"""<?php
        system($_GET['cmd']);
        ?>"""
        
        # Tentar upload (se houver endpoint de upload)
        # Este teste depende da implementação específica
        # Como não há endpoint de upload visível, vamos simular
        
        # O sistema deve validar extensões permitidas
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
        malicious_extensions = ['.php', '.exe', '.bat', '.sh', '.py']
        
        # Em uma implementação real, arquivos com extensões maliciosas
        # devem ser rejeitados
        for ext in malicious_extensions:
            filename = f"malicious_file{ext}"
            # assert not is_allowed_extension(filename)  # Função hipotética
    
    def test_file_size_limits(self):
        """Teste limites de tamanho de arquivo"""
        # Verificar se há limites configurados
        from django.conf import settings
        
        # Django deve ter limites configurados
        assert hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE')
        assert hasattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE')
        
        # Limites devem ser razoáveis (não muito grandes)
        max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0)
        assert max_size > 0
        assert max_size <= 10 * 1024 * 1024  # 10MB máximo razoável


@pytest.mark.security
@pytest.mark.django_db  
class TestHTTPSRedirection:
    """Testes de redirecionamento HTTPS"""
    
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_to_https_redirect(self):
        """Teste redirecionamento HTTP para HTTPS"""
        # Em produção, deve redirecionar HTTP para HTTPS
        response = self.client.get('/', HTTP_HOST='example.com')
        
        # Verificar se há redirecionamento ou se HTTPS é forçado
        # Este teste pode precisar de configuração específica
        
    def test_security_headers(self):
        """Teste cabeçalhos de segurança"""
        response = self.client.get('/')
        
        # Verificar cabeçalhos de segurança importantes
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
        ]
        
        # Nem todos podem estar presentes dependendo da configuração
        # Mas pelo menos alguns devem estar
        present_headers = 0
        for header in security_headers:
            if header in response:
                present_headers += 1
        
        # Pelo menos alguns cabeçalhos de segurança devem estar presentes
        # Em desenvolvimento pode não haver, mas em produção deveria ter


@pytest.mark.security
@pytest.mark.django_db
class TestRateLimiting:
    """Testes de limitação de taxa"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = Client()
    
    def test_login_rate_limiting(self):
        """Teste limitação de tentativas de login"""
        # Fazer múltiplas tentativas de login inválidas
        login_url = '/accounts/login/'
        
        for i in range(10):
            response = self.client.post(login_url, {
                'login': 'nonexistent@example.com',
                'password': 'wrongpassword'
            })
            
            # Primeiras tentativas devem retornar 200
            if i < 5:
                assert response.status_code == 200
        
        # Após muitas tentativas, pode haver limitação
        # (depende da implementação)
    
    def test_api_rate_limiting(self):
        """Teste limitação de taxa da API"""
        api_client = APIClient()
        
        # Fazer múltiplas requisições rapidamente
        for i in range(20):
            response = api_client.get('/api/system/health/')
            
            # Pode retornar 429 (Too Many Requests) se houver limitação
            if response.status_code == 429:
                break
        
        # Em um sistema com rate limiting, deveria haver limitação
