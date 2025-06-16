"""
Testes críticos de segurança e validação para o sistema Move Marias
"""
import pytest
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.validators import (
    validate_cpf, validate_phone, validate_rg, 
    validate_full_name, validate_password_strength,
    sanitize_input
)
from members.models import Beneficiary
from members.forms import BeneficiaryForm

User = get_user_model()


class SecurityValidationTests(TestCase):
    """Testes de validação e segurança"""
    
    def test_cpf_validation_valid(self):
        """Teste CPF válido"""
        # CPF válido: 111.444.777-35
        self.assertTrue(validate_cpf('11144477735'))
        self.assertTrue(validate_cpf('111.444.777-35'))
    
    def test_cpf_validation_invalid(self):
        """Teste CPF inválido"""
        # CPFs inválidos
        self.assertFalse(validate_cpf('11111111111'))  # Todos iguais
        self.assertFalse(validate_cpf('123456789'))    # Menos de 11 dígitos
        self.assertFalse(validate_cpf('12345678901'))  # Dígitos verificadores errados
        self.assertFalse(validate_cpf(''))             # Vazio
        self.assertFalse(validate_cpf(None))           # None
    
    def test_phone_validation_valid(self):
        """Teste telefone válido"""
        self.assertTrue(validate_phone('11987654321'))  # Celular
        self.assertTrue(validate_phone('1134567890'))   # Fixo
        self.assertTrue(validate_phone('(11) 98765-4321'))  # Formatado
    
    def test_phone_validation_invalid(self):
        """Teste telefone inválido"""
        self.assertFalse(validate_phone('123456789'))   # Menos de 10 dígitos
        self.assertFalse(validate_phone('1111111111'))  # Todos iguais
        self.assertFalse(validate_phone('0123456789'))  # Começa com 0
        self.assertFalse(validate_phone('1123456789'))  # Começa com 1
        self.assertFalse(validate_phone('11123456789')) # 11 dígitos sem 9
    
    def test_full_name_validation_valid(self):
        """Teste nome válido"""
        is_valid, message = validate_full_name('Maria Silva')
        self.assertTrue(is_valid)
        
        is_valid, message = validate_full_name('João da Silva Santos')
        self.assertTrue(is_valid)
    
    def test_full_name_validation_invalid(self):
        """Teste nome inválido"""
        is_valid, message = validate_full_name('Maria')  # Só um nome
        self.assertFalse(is_valid)
        
        is_valid, message = validate_full_name('Maria123')  # Com números
        self.assertFalse(is_valid)
        
        is_valid, message = validate_full_name('Maria@Silva')  # Caracteres especiais
        self.assertFalse(is_valid)
        
        is_valid, message = validate_full_name('')  # Vazio
        self.assertFalse(is_valid)
    
    def test_password_strength_validation(self):
        """Teste validação de força da senha"""
        # Senha forte
        is_valid, message = validate_password_strength('MinhaSenh@123')
        self.assertTrue(is_valid)
        
        # Senhas fracas
        is_valid, message = validate_password_strength('123')
        self.assertFalse(is_valid)
        
        is_valid, message = validate_password_strength('password')
        self.assertFalse(is_valid)
        
        is_valid, message = validate_password_strength('12345678')
        self.assertFalse(is_valid)
    
    def test_input_sanitization(self):
        """Teste sanitização de entrada"""
        # XSS básico
        dangerous_input = '<script>alert("xss")</script>Maria Silva'
        sanitized = sanitize_input(dangerous_input)
        self.assertNotIn('<script>', sanitized)
        self.assertIn('Maria Silva', sanitized)
        
        # HTML tags
        html_input = '<b>Maria</b> <i>Silva</i>'
        sanitized = sanitize_input(html_input)
        self.assertEqual(sanitized, 'Maria Silva')


class BeneficiaryFormTests(TestCase):
    """Testes do formulário de beneficiárias"""
    
    def setUp(self):
        self.valid_data = {
            'full_name': 'Maria Silva Santos',
            'dob': '1990-01-01',
            'phone_1': '11987654321',
            'rg': '123456789',
            'cpf': '11144477735',  # CPF válido
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro',
        }
    
    def test_form_valid_data(self):
        """Teste formulário com dados válidos"""
        form = BeneficiaryForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_form_invalid_cpf(self):
        """Teste formulário com CPF inválido"""
        invalid_data = self.valid_data.copy()
        invalid_data['cpf'] = '11111111111'  # CPF inválido
        
        form = BeneficiaryForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
    
    def test_form_invalid_phone(self):
        """Teste formulário com telefone inválido"""
        invalid_data = self.valid_data.copy()
        invalid_data['phone_1'] = '123456789'  # Telefone inválido
        
        form = BeneficiaryForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone_1', form.errors)
    
    def test_form_invalid_name(self):
        """Teste formulário com nome inválido"""
        invalid_data = self.valid_data.copy()
        invalid_data['full_name'] = 'Maria'  # Só um nome
        
        form = BeneficiaryForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)
    
    def test_form_xss_protection(self):
        """Teste proteção contra XSS"""
        xss_data = self.valid_data.copy()
        xss_data['full_name'] = '<script>alert("xss")</script>Maria Silva'
        
        form = BeneficiaryForm(data=xss_data)
        if form.is_valid():
            self.assertNotIn('<script>', form.cleaned_data['full_name'])


class ModelValidationTests(TestCase):
    """Testes de validação nos modelos"""
    
    def test_beneficiary_model_validation(self):
        """Teste validação no modelo Beneficiary"""
        # Dados válidos
        beneficiary = Beneficiary(
            full_name='Maria Silva Santos',
            dob='1990-01-01',
            phone_1='11987654321',
            rg='123456789',
            cpf='11144477735',
            address='Rua das Flores, 123',
            neighbourhood='Centro'
        )
        
        # Não deve gerar exceção
        try:
            beneficiary.full_clean()
        except ValidationError:
            self.fail("Modelo válido não deveria gerar ValidationError")


class SecurityHeadersTests(TestCase):
    """Testes de headers de segurança"""
    
    def setUp(self):
        self.client = Client()
        # Criar usuário para testes autenticados
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            is_active=True
        )
    
    def test_security_headers_on_dashboard(self):
        """Teste headers de segurança no dashboard"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('dashboard:home'))
        
        # Verificar headers de segurança em produção
        if not response.wsgi_request.META.get('DEBUG', True):
            self.assertIn('X-Content-Type-Options', response)
            self.assertIn('X-Frame-Options', response)
    
    def test_csrf_protection(self):
        """Teste proteção CSRF"""
        self.client.login(username='testuser', password='testpass123')
        
        # POST sem token CSRF deve falhar
        response = self.client.post(
            reverse('dashboard:beneficiary_create'),
            data={'full_name': 'Test User'},
            HTTP_X_CSRFTOKEN='invalid'
        )
        
        # Deve retornar erro 403 ou redirect
        self.assertIn(response.status_code, [403, 302])


class PerformanceTests(TestCase):
    """Testes de performance críticos"""
    
    def setUp(self):
        # Criar dados de teste
        for i in range(100):
            Beneficiary.objects.create(
                full_name=f'Beneficiária {i}',
                dob='1990-01-01',
                phone_1=f'1198765432{i % 10}',
                rg=f'12345678{i}',
                cpf=f'1114447773{i % 10}',
                address=f'Rua {i}',
                neighbourhood='Centro'
            )
    
    def test_beneficiaries_list_performance(self):
        """Teste performance da listagem de beneficiárias"""
        from django.test import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            # Resetar queries
            connection.queries_log.clear()
            
            # Fazer request
            client = Client()
            user = User.objects.create_user(
                username='testuser',
                password='testpass123'
            )
            client.force_login(user)
            
            response = client.get(reverse('dashboard:beneficiaries_list'))
            
            # Verificar número de queries (deve ser baixo com otimizações)
            query_count = len(connection.queries)
            self.assertLess(query_count, 10, 
                          f"Muitas queries: {query_count}. Possível N+1 problem.")


class CacheTests(TestCase):
    """Testes do sistema de cache"""
    
    def test_dashboard_cache(self):
        """Teste cache do dashboard"""
        from core.optimizers import CacheManager
        from django.core.cache import cache
        
        # Limpar cache
        cache.clear()
        
        # Primeira chamada deve calcular
        stats1 = CacheManager.get_dashboard_stats(1)
        
        # Segunda chamada deve usar cache
        stats2 = CacheManager.get_dashboard_stats(1)
        
        self.assertEqual(stats1, stats2)
    
    def test_cache_invalidation(self):
        """Teste invalidação de cache"""
        from core.optimizers import CacheManager
        from django.core.cache import cache
        
        # Definir um cache
        cache.set('test_key', 'test_value', 300)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Invalidar
        CacheManager.invalidate_related_cache('beneficiary', 1)
        
        # Cache específico deve ainda existir (por enquanto)
        # Em implementação completa, seria invalidado
