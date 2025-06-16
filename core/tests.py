"""
Testes para validadores de segurança e funcionalidades do core
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from core.password_validators import AdvancedPasswordValidator, HaveIBeenPwnedValidator
from core.forms import SecureCPFField, SecurePhoneField, SecureEmailField
from django.contrib.auth import get_user_model

User = get_user_model()


class PasswordValidatorTests(TestCase):
    """Testes para validadores de senha"""
    
    def setUp(self):
        self.validator = AdvancedPasswordValidator()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='João Silva'
        )
    
    def test_password_too_short(self):
        """Senha muito curta deve falhar"""
        with self.assertRaises(ValidationError):
            self.validator.validate('123456', self.user)
    
    def test_password_no_uppercase(self):
        """Senha sem maiúscula deve falhar"""
        with self.assertRaises(ValidationError):
            self.validator.validate('testpassword123!', self.user)
    
    def test_password_no_lowercase(self):
        """Senha sem minúscula deve falhar"""
        with self.assertRaises(ValidationError):
            self.validator.validate('TESTPASSWORD123!', self.user)
    
    def test_password_no_number(self):
        """Senha sem número deve falhar"""
        with self.assertRaises(ValidationError):
            self.validator.validate('TestPassword!', self.user)
    
    def test_password_no_special_char(self):
        """Senha sem caractere especial deve falhar"""
        with self.assertRaises(ValidationError):
            self.validator.validate('TestPassword123', self.user)
    
    def test_valid_password(self):
        """Senha válida não deve lançar exceção"""
        try:
            self.validator.validate('MySecure@Password2024!', self.user)
        except ValidationError:
            self.fail("Valid password raised ValidationError")


class SecureFieldsTests(TestCase):
    """Testes para campos seguros"""
    
    def setUp(self):
        self.cpf_field = SecureCPFField()
        self.phone_field = SecurePhoneField()
        self.email_field = SecureEmailField()
    
    def test_valid_cpf(self):
        """CPF válido deve passar na validação"""
        valid_cpf = '11144477735'
        try:
            self.cpf_field.validate(valid_cpf)
        except ValidationError:
            self.fail(f"Valid CPF {valid_cpf} raised ValidationError")
    
    def test_invalid_cpf(self):
        """CPF inválido deve falhar"""
        invalid_cpf = '000.000.000-00'
        with self.assertRaises(ValidationError):
            self.cpf_field.validate(invalid_cpf)
    
    def test_valid_phone(self):
        """Telefone válido deve passar"""
        valid_phone = '(11) 99999-9999'
        try:
            self.phone_field.validate(valid_phone)
        except ValidationError:
            self.fail(f"Valid phone {valid_phone} raised ValidationError")
    
    def test_invalid_phone(self):
        """Telefone inválido deve falhar"""
        invalid_phone = '123456789'
        with self.assertRaises(ValidationError):
            self.phone_field.validate(invalid_phone)
    
    def test_temporary_email_blocked(self):
        """Email temporário deve ser bloqueado"""
        temp_email = 'test@10minutemail.com'
        with self.assertRaises(ValidationError):
            self.email_field.validate(temp_email)
