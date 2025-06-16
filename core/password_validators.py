"""
Validadores avançados de senha para Move Marias
"""
import re
import requests
from hashlib import sha1
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class AdvancedPasswordValidator:
    """Validador avançado de senhas"""
    
    def __init__(self, min_length=12):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        errors = []
        
        # Comprimento mínimo
        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    f"A senha deve ter pelo menos {self.min_length} caracteres.",
                    code='password_too_short',
                )
            )
        
        # Deve conter pelo menos uma letra maiúscula
        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    "A senha deve conter pelo menos uma letra maiúscula.",
                    code='password_no_upper',
                )
            )
        
        # Deve conter pelo menos uma letra minúscula
        if not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    "A senha deve conter pelo menos uma letra minúscula.",
                    code='password_no_lower',
                )
            )
        
        # Deve conter pelo menos um número
        if not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    "A senha deve conter pelo menos um número.",
                    code='password_no_number',
                )
            )
        
        # Deve conter pelo menos um caractere especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(
                ValidationError(
                    "A senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?\":{}|<>).",
                    code='password_no_special',
                )
            )
        
        # Não deve conter informações do usuário
        if user:
            user_info = [
                user.username.lower() if hasattr(user, 'username') and user.username else '',
                user.first_name.lower() if hasattr(user, 'first_name') and user.first_name else '',
                user.last_name.lower() if hasattr(user, 'last_name') and user.last_name else '',
                user.email.lower().split('@')[0] if hasattr(user, 'email') and user.email else '',
            ]
            
            for info in user_info:
                if info and len(info) > 2 and info in password.lower():
                    errors.append(
                        ValidationError(
                            "A senha não deve conter informações pessoais.",
                            code='password_too_similar',
                        )
                    )
        
        # Não deve ter sequências repetitivas
        if self._has_repetitive_sequences(password):
            errors.append(
                ValidationError(
                    "A senha não deve conter sequências repetitivas (ex: 123, abc, aaa).",
                    code='password_repetitive',
                )
            )
        
        if errors:
            raise ValidationError(errors)
    
    def _has_repetitive_sequences(self, password):
        # Verifica sequências numéricas
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                nums = [int(c) for c in password[i:i+3]]
                if nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1:
                    return True
        
        # Verifica caracteres repetidos
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        
        return False
    
    def get_help_text(self):
        return _(
            "Sua senha deve ter pelo menos %(min_length)d caracteres, "
            "incluindo letras maiúsculas, minúsculas, números e caracteres especiais."
        ) % {'min_length': self.min_length}


class HaveIBeenPwnedValidator:
    """Verifica se a senha foi vazada em ataques conhecidos"""
    
    def validate(self, password, user=None):
        # Hash SHA-1 da senha
        sha1_hash = sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            # Consulta a API do HaveIBeenPwned
            response = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=3
            )
            
            if response.status_code == 200:
                hashes = response.text.split('\n')
                for hash_line in hashes:
                    if ':' in hash_line:
                        hash_suffix, count = hash_line.split(':')
                        if hash_suffix.strip() == suffix:
                            raise ValidationError(
                                "Esta senha foi encontrada em vazamentos de dados. "
                                "Por favor, escolha uma senha diferente.",
                                code='password_pwned',
                            )
        except requests.RequestException:
            # Se não conseguir verificar, não impede o cadastro
            pass
    
    def get_help_text(self):
        return _("Suas senhas são verificadas contra bases de dados de senhas vazadas.")
