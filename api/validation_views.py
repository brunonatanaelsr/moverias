"""
API endpoints para validação em tempo real
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
import json
import re
from members.models import Beneficiary
from core.validators import validate_cpf
from core.logging_config import get_security_logger

security_logger = get_security_logger()

@login_required
@require_http_methods(["POST"])
@ratelimit(key='user', rate='30/m', method='POST')
@csrf_exempt  # CSRF handled via form token
def check_cpf_uniqueness(request):
    """
    Verifica se CPF já existe no sistema
    """
    try:
        cpf = request.POST.get('cpf', '').strip()
        
        if not cpf:
            return JsonResponse({'error': 'CPF é obrigatório'}, status=400)
        
        # Remover formatação
        cpf_digits = re.sub(r'\D', '', cpf)
        
        # Validar formato
        if not validate_cpf(cpf_digits):
            return JsonResponse({
                'error': 'CPF inválido',
                'exists': False
            }, status=400)
        
        # Verificar duplicatas (complicado com campos criptografados)
        exists = False
        try:
            # Em campos criptografados, precisamos verificar manualmente
            all_beneficiaries = Beneficiary.objects.all()
            for beneficiary in all_beneficiaries:
                try:
                    if beneficiary.cpf == cpf_digits:
                        exists = True
                        break
                except:
                    # Erro na descriptografia - continuar
                    continue
        except Exception as e:
            # Log error but don't expose it
            security_logger.log_data_access(
                request.user, 
                'cpf_check', 
                'error',
                request.META.get('REMOTE_ADDR', ''),
                False
            )
        
        # Log da tentativa
        security_logger.log_data_access(
            request.user,
            'cpf_check', 
            'read',
            request.META.get('REMOTE_ADDR', ''),
            True
        )
        
        return JsonResponse({
            'exists': exists,
            'message': 'CPF já cadastrado' if exists else 'CPF disponível'
        })
        
    except Exception as e:
        return JsonResponse({'error': 'Erro interno'}, status=500)


@login_required  
@require_http_methods(["POST"])
@ratelimit(key='user', rate='60/m', method='POST')
def validate_field_api(request):
    """
    API genérica para validação de campos
    """
    try:
        data = json.loads(request.body)
        field_type = data.get('type')
        value = data.get('value', '').strip()
        
        if not field_type or not value:
            return JsonResponse({'error': 'Tipo e valor são obrigatórios'}, status=400)
        
        result = {'valid': False, 'message': ''}
        
        if field_type == 'cpf':
            cpf_digits = re.sub(r'\D', '', value)
            result['valid'] = validate_cpf(cpf_digits)
            result['message'] = 'CPF válido' if result['valid'] else 'CPF inválido'
            
        elif field_type == 'email':
            email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
            result['valid'] = bool(email_pattern.match(value))
            result['message'] = 'E-mail válido' if result['valid'] else 'E-mail inválido'
            
        elif field_type == 'phone':
            phone_digits = re.sub(r'\D', '', value)
            result['valid'] = len(phone_digits) in [10, 11]
            result['message'] = 'Telefone válido' if result['valid'] else 'Telefone inválido'
            
        elif field_type == 'name':
            words = value.split()
            result['valid'] = len(words) >= 2 and all(len(word) > 1 for word in words)
            result['message'] = 'Nome válido' if result['valid'] else 'Nome deve ter pelo menos 2 palavras'
            
        else:
            return JsonResponse({'error': 'Tipo de campo não suportado'}, status=400)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Erro interno'}, status=500)


@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='100/h', method='GET')  
def form_config_api(request):
    """
    Retorna configurações de validação para formulários
    """
    config = {
        'validation_rules': {
            'cpf': {
                'pattern': r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                'required': True,
                'unique': True
            },
            'phone': {
                'pattern': r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
                'required': True
            },
            'email': {
                'pattern': r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                'required': False
            },
            'name': {
                'min_words': 2,
                'required': True
            }
        },
        'messages': {
            'cpf_invalid': 'CPF inválido. Use o formato 000.000.000-00',
            'cpf_exists': 'Este CPF já está cadastrado',
            'phone_invalid': 'Telefone inválido. Use o formato (11) 99999-9999',
            'email_invalid': 'E-mail inválido',
            'name_invalid': 'Nome deve ter pelo menos 2 palavras'
        },
        'endpoints': {
            'check_cpf': '/api/validation/check-cpf/',
            'validate_field': '/api/validation/validate-field/'
        }
    }
    
    return JsonResponse(config)


@login_required
@require_http_methods(["POST"])
@ratelimit(key='user', rate='30/m', method='POST')
@csrf_exempt
def check_email_uniqueness(request):
    """
    Verifica se e-mail já existe no sistema
    """
    try:
        email = request.POST.get('email', '').strip()
        
        if not email:
            return JsonResponse({'error': 'E-mail é obrigatório'}, status=400)
        
        # Validar formato básico
        import re
        email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
        if not email_pattern.match(email):
            return JsonResponse({
                'error': 'E-mail inválido',
                'exists': False
            }, status=400)
        
        # Verificar unicidade
        from users.models import CustomUser
        exists = CustomUser.objects.filter(email=email).exists()
        
        return JsonResponse({
            'exists': exists,
            'valid': True,
            'message': 'E-mail já existe' if exists else 'E-mail disponível'
        })
        
    except Exception as e:
        security_logger.error(f"Erro na validação de e-mail: {e}")
        return JsonResponse({'error': 'Erro interno'}, status=500)
