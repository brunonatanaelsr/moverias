"""
Testes específicos para validações de formulários
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from members.forms import BeneficiaryForm
from members.models import Beneficiary


class BeneficiaryFormValidationTests(TestCase):
    """Testes detalhados do formulário de beneficiárias"""
    
    def setUp(self):
        self.base_data = {
            'full_name': 'Maria Silva Santos',
            'dob': '1990-01-01',
            'phone_1': '11987654321',
            'rg': '123456789',
            'cpf': '11144477735',  # CPF válido para teste
            'address': 'Rua das Flores, 123',
            'neighbourhood': 'Centro',
        }
    
    def test_cpf_validation_with_formatting(self):
        """Teste CPF com formatação"""
        data = self.base_data.copy()
        data['cpf'] = '111.444.777-35'
        
        form = BeneficiaryForm(data=data)
        self.assertTrue(form.is_valid(), f"Erros: {form.errors}")
        
        # CPF deve ser salvo sem formatação
        self.assertEqual(form.cleaned_data['cpf'], '11144477735')
    
    def test_duplicate_cpf_validation(self):
        """Teste validação de CPF duplicado"""
        # Criar beneficiária existente
        Beneficiary.objects.create(
            full_name='Beneficiária Existente',
            dob='1985-01-01',
            phone_1='11987654321',
            rg='987654321',
            cpf='11144477735',
            address='Rua A',
            neighbourhood='Bairro A'
        )
        
        # Tentar criar outra com mesmo CPF
        form = BeneficiaryForm(data=self.base_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('já está cadastrado', str(form.errors['cpf']))
    
    def test_phone_formatting_validation(self):
        """Teste validação de telefone com diferentes formatos"""
        test_cases = [
            ('11987654321', True),      # Apenas números
            ('(11) 98765-4321', True),  # Formatado
            ('11 98765-4321', True),    # Parcialmente formatado
            ('1134567890', True),       # Fixo
            ('123456789', False),       # Muito curto
            ('0123456789', False),      # Começa com 0
            ('1111111111', False),      # Todos iguais
        ]
        
        for phone, should_be_valid in test_cases:
            with self.subTest(phone=phone):
                data = self.base_data.copy()
                data['phone_1'] = phone
                
                form = BeneficiaryForm(data=data)
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Telefone {phone} deveria ser válido. Erros: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Telefone {phone} deveria ser inválido")
                    self.assertIn('phone_1', form.errors)
    
    def test_name_validation_cases(self):
        """Teste casos específicos de validação de nome"""
        test_cases = [
            ('Maria Silva', True),          # Válido básico
            ('Ana Maria da Silva', True),   # Com preposição
            ('José dos Santos', True),      # Com preposição
            ('Maria', False),               # Só um nome
            ('Maria123', False),            # Com números
            ('Maria@Silva', False),         # Caracteres especiais
            ('   Maria   Silva   ', True),  # Com espaços extras
            ('', False),                    # Vazio
            ('A B', False),                 # Nomes muito curtos
        ]
        
        for name, should_be_valid in test_cases:
            with self.subTest(name=name):
                data = self.base_data.copy()
                data['full_name'] = name
                
                form = BeneficiaryForm(data=data)
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Nome '{name}' deveria ser válido. Erros: {form.errors}")
                    # Verificar se foi capitalizado
                    if form.is_valid():
                        cleaned_name = form.cleaned_data['full_name']
                        words = cleaned_name.split()
                        for word in words:
                            if len(word) > 2:  # Preposições podem ficar minúsculas
                                self.assertTrue(word[0].isupper(), 
                                              f"Palavra '{word}' deveria começar com maiúscula")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Nome '{name}' deveria ser inválido")
                    self.assertIn('full_name', form.errors)
    
    def test_xss_sanitization(self):
        """Teste sanitização contra XSS"""
        xss_attempts = [
            '<script>alert("xss")</script>Maria Silva',
            'Maria<script>alert("xss")</script>Silva',
            'Maria Silva<img src=x onerror=alert("xss")>',
            'Maria Silva<iframe src="javascript:alert(1)"></iframe>',
        ]
        
        for xss_input in xss_attempts:
            with self.subTest(xss_input=xss_input):
                data = self.base_data.copy()
                data['full_name'] = xss_input
                
                form = BeneficiaryForm(data=data)
                # Pode ser válido ou inválido, mas não deve conter scripts
                if form.is_valid():
                    cleaned_name = form.cleaned_data['full_name']
                    self.assertNotIn('<script>', cleaned_name.lower())
                    self.assertNotIn('<iframe>', cleaned_name.lower())
                    self.assertNotIn('javascript:', cleaned_name.lower())
                    self.assertNotIn('onerror=', cleaned_name.lower())
