"""
Utilitários de validação para o sistema Move Marias
"""
import re
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


def validate_cpf(cpf):
    """
    Validação robusta de CPF com verificação de dígitos verificadores
    """
    if not cpf:
        return False
    
    # Remove formatação
    cpf = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se não são todos iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    
    resto = 11 - (soma % 11)
    if resto in (10, 11):
        resto = 0
    
    if resto != int(cpf[9]):
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    
    resto = 11 - (soma % 11)
    if resto in (10, 11):
        resto = 0
    
    if resto != int(cpf[10]):
        return False
    
    return True


def validate_phone(phone):
    """
    Validação de telefone brasileiro
    """
    if not phone:
        return False
    
    # Remove formatação
    phone = re.sub(r'\D', '', phone)
    
    # Verifica se tem pelo menos 10 dígitos e no máximo 11
    if len(phone) < 10 or len(phone) > 11:
        return False
    
    # Verifica se não são todos iguais
    if phone == phone[0] * len(phone):
        return False
    
    # Verifica se é um número válido (não começa com 0 ou 1)
    if phone[0] in ['0', '1']:
        return False
    
    # Se tem 11 dígitos, verifica se o terceiro dígito é 9 (celular)
    if len(phone) == 11 and phone[2] != '9':
        return False
    
    return True


def validate_rg(rg):
    """
    Validação básica de RG
    """
    if not rg:
        return False
    
    # Remove formatação
    rg = re.sub(r'\D', '', rg)
    
    # Verifica se tem entre 7 e 9 dígitos
    if len(rg) < 7 or len(rg) > 9:
        return False
    
    # Verifica se não são todos iguais
    if rg == rg[0] * len(rg):
        return False
    
    return True


def validate_email_unique(email, exclude_user=None):
    """
    Validação de email único no sistema
    """
    if not email:
        return False
    
    queryset = User.objects.filter(email=email)
    
    if exclude_user:
        queryset = queryset.exclude(pk=exclude_user.pk)
    
    return not queryset.exists()


def validate_password_strength(password):
    """
    Validação de força da senha
    """
    if not password:
        return False, "Senha é obrigatória"
    
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    # Verificar senhas comuns
    common_passwords = [
        '12345678', '123456789', 'password', 'senha123',
        'admin123', 'movemarias', 'qwerty123'
    ]
    
    if password.lower() in common_passwords:
        return False, "Senha muito comum, escolha uma mais segura"
    
    return True, "Senha válida"


def validate_full_name(name):
    """
    Validação de nome completo
    """
    if not name:
        return False, "Nome é obrigatório"
    
    name = name.strip()
    
    if len(name) < 3:
        return False, "Nome deve ter pelo menos 3 caracteres"
    
    # Verifica se tem pelo menos nome e sobrenome
    name_parts = name.split()
    if len(name_parts) < 2:
        return False, "Por favor, informe nome e sobrenome"
    
    # Verifica se não contém números
    if re.search(r'\d', name):
        return False, "Nome não pode conter números"
    
    # Verifica se não contém caracteres especiais (exceto hífen e apóstrofe)
    if re.search(r'[^\w\s\-\']', name):
        return False, "Nome contém caracteres inválidos"
    
    return True, "Nome válido"


def sanitize_input(text):
    """
    Sanitização básica de entrada de texto
    """
    if not text:
        return text
    
    # Remove tags HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove scripts
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove caracteres de controle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()
