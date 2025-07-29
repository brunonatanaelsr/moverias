"""
Sistema de Validação JavaScript Inteligente
Parte da Fase 2 do Plano de Melhorias Incrementais - Usabilidade
"""

# JavaScript para validações em tempo real
FORM_VALIDATION_JS = """
// Sistema de Validação Inteligente para Forms
class MoveFormsValidator {
    constructor() {
        this.validators = {};
        this.messages = {};
        this.isValid = true;
        this.init();
    }
    
    init() {
        this.setupValidators();
        this.setupMessages();
        this.bindEvents();
        this.enhanceUX();
    }
    
    setupValidators() {
        // Validadores específicos do sistema
        this.validators = {
            cpf: (value) => {
                if (!value) return true; // Campo opcional
                const cpf = value.replace(/[^\\d]/g, '');
                if (cpf.length !== 11) return false;
                
                // Verificar se todos os dígitos são iguais
                if (/^(\\d)\\1{10}$/.test(cpf)) return false;
                
                // Algoritmo de validação do CPF
                let sum = 0;
                for (let i = 0; i < 9; i++) {
                    sum += parseInt(cpf.charAt(i)) * (10 - i);
                }
                let digit1 = (sum * 10) % 11;
                if (digit1 === 10) digit1 = 0;
                
                if (parseInt(cpf.charAt(9)) !== digit1) return false;
                
                sum = 0;
                for (let i = 0; i < 10; i++) {
                    sum += parseInt(cpf.charAt(i)) * (11 - i);
                }
                let digit2 = (sum * 10) % 11;
                if (digit2 === 10) digit2 = 0;
                
                return parseInt(cpf.charAt(10)) === digit2;
            },
            
            phone: (value) => {
                if (!value) return true;
                const phone = value.replace(/[^\\d]/g, '');
                return phone.length >= 10 && phone.length <= 11;
            },
            
            email: (value) => {
                if (!value) return true;
                const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
                return emailRegex.test(value);
            },
            
            date: (value) => {
                if (!value) return true;
                const date = new Date(value);
                return !isNaN(date.getTime());
            },
            
            futureDate: (value) => {
                if (!value) return true;
                const date = new Date(value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                return date >= today;
            },
            
            pastDate: (value) => {
                if (!value) return true;
                const date = new Date(value);
                const today = new Date();
                return date <= today;
            },
            
            minLength: (value, min) => {
                return !value || value.length >= min;
            },
            
            maxLength: (value, max) => {
                return !value || value.length <= max;
            },
            
            required: (value) => {
                return value && value.trim().length > 0;
            },
            
            number: (value) => {
                if (!value) return true;
                return !isNaN(parseFloat(value)) && isFinite(value);
            },
            
            positiveNumber: (value) => {
                if (!value) return true;
                const num = parseFloat(value);
                return !isNaN(num) && num > 0;
            },
            
            age: (value) => {
                if (!value) return true;
                const num = parseInt(value);
                return !isNaN(num) && num >= 0 && num <= 120;
            }
        };
    }
    
    setupMessages() {
        this.messages = {
            cpf: 'CPF inválido. Verifique os números digitados.',
            phone: 'Telefone deve ter entre 10 e 11 dígitos.',
            email: 'E-mail inválido. Use o formato: exemplo@email.com',
            date: 'Data inválida.',
            futureDate: 'A data deve ser hoje ou no futuro.',
            pastDate: 'A data não pode ser no futuro.',
            minLength: 'Muito curto. Mínimo de {min} caracteres.',
            maxLength: 'Muito longo. Máximo de {max} caracteres.',
            required: 'Este campo é obrigatório.',
            number: 'Digite apenas números.',
            positiveNumber: 'Digite um número maior que zero.',
            age: 'Idade deve estar entre 0 e 120 anos.'
        };
    }
    
    bindEvents() {
        // Validação em tempo real
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.validateField(e.target);
            }
        });
        
        // Validação ao sair do campo
        document.addEventListener('blur', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.validateField(e.target);
            }
        }, true);
        
        // Validação no submit
        document.addEventListener('submit', (e) => {
            if (!this.validateForm(e.target)) {
                e.preventDefault();
                this.showFormErrors(e.target);
            }
        });
        
        // Máscaras dinâmicas
        this.setupMasks();
    }
    
    validateField(field) {
        const rules = this.getValidationRules(field);
        const value = field.value;
        let isValid = true;
        let errorMessage = '';
        
        for (const rule of rules) {
            const [validatorName, params] = rule.split(':');
            const validator = this.validators[validatorName];
            
            if (validator) {
                const result = params ? 
                    validator(value, ...params.split(',')) : 
                    validator(value);
                
                if (!result) {
                    isValid = false;
                    errorMessage = this.formatMessage(validatorName, params);
                    break;
                }
            }
        }
        
        this.showFieldValidation(field, isValid, errorMessage);
        return isValid;
    }
    
    getValidationRules(field) {
        const rules = [];
        
        // Regras baseadas em atributos HTML
        if (field.hasAttribute('required')) {
            rules.push('required');
        }
        
        if (field.type === 'email') {
            rules.push('email');
        }
        
        if (field.type === 'number') {
            rules.push('number');
        }
        
        if (field.type === 'date') {
            rules.push('date');
        }
        
        if (field.minLength > 0) {
            rules.push(`minLength:${field.minLength}`);
        }
        
        if (field.maxLength > 0) {
            rules.push(`maxLength:${field.maxLength}`);
        }
        
        // Regras baseadas em classes CSS
        if (field.classList.contains('cpf-field')) {
            rules.push('cpf');
        }
        
        if (field.classList.contains('phone-field')) {
            rules.push('phone');
        }
        
        if (field.classList.contains('future-date')) {
            rules.push('futureDate');
        }
        
        if (field.classList.contains('past-date')) {
            rules.push('pastDate');
        }
        
        if (field.classList.contains('positive-number')) {
            rules.push('positiveNumber');
        }
        
        if (field.classList.contains('age-field')) {
            rules.push('age');
        }
        
        // Regras customizadas via data-validate
        const customRules = field.getAttribute('data-validate');
        if (customRules) {
            rules.push(...customRules.split('|'));
        }
        
        return rules;
    }
    
    formatMessage(validatorName, params) {
        let message = this.messages[validatorName] || 'Valor inválido';
        
        if (params) {
            const paramArray = params.split(',');
            message = message.replace('{min}', paramArray[0]);
            message = message.replace('{max}', paramArray[0]);
        }
        
        return message;
    }
    
    showFieldValidation(field, isValid, message) {
        // Remover validações anteriores
        this.clearFieldValidation(field);
        
        if (isValid) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
        } else {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            
            // Criar elemento de erro
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = message;
            
            // Inserir após o campo
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
        }
    }
    
    clearFieldValidation(field) {
        field.classList.remove('is-valid', 'is-invalid');
        
        // Remover mensagens de erro
        const nextElement = field.nextSibling;
        if (nextElement && nextElement.classList.contains('invalid-feedback')) {
            nextElement.remove();
        }
    }
    
    validateForm(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        let formIsValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                formIsValid = false;
            }
        });
        
        return formIsValid;
    }
    
    showFormErrors(form) {
        const firstInvalidField = form.querySelector('.is-invalid');
        if (firstInvalidField) {
            firstInvalidField.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
            firstInvalidField.focus();
        }
        
        // Mostrar notificação geral
        this.showNotification(
            'Existem campos com erros no formulário. Verifique os campos destacados.',
            'error'
        );
    }
    
    setupMasks() {
        // Máscara para CPF
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('cpf-field')) {
                e.target.value = this.maskCPF(e.target.value);
            }
        });
        
        // Máscara para telefone
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('phone-field')) {
                e.target.value = this.maskPhone(e.target.value);
            }
        });
        
        // Máscara para CEP
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('cep-field')) {
                e.target.value = this.maskCEP(e.target.value);
            }
        });
    }
    
    maskCPF(value) {
        return value
            .replace(/\\D/g, '')
            .replace(/(\\d{3})(\\d)/, '$1.$2')
            .replace(/(\\d{3})(\\d)/, '$1.$2')
            .replace(/(\\d{3})(\\d{1,2})/, '$1-$2')
            .replace(/(-\\d{2})\\d+?$/, '$1');
    }
    
    maskPhone(value) {
        return value
            .replace(/\\D/g, '')
            .replace(/(\\d{2})(\\d)/, '($1) $2')
            .replace(/(\\d{4})(\\d)/, '$1-$2')
            .replace(/(\\d{4})-\\d+?$/, '$1');
    }
    
    maskCEP(value) {
        return value
            .replace(/\\D/g, '')
            .replace(/(\\d{5})(\\d)/, '$1-$2')
            .replace(/(-\\d{3})\\d+?$/, '$1');
    }
    
    enhanceUX() {
        // Auto-completar endereço via CEP
        this.setupCEPAutoComplete();
        
        // Tooltips informativos
        this.setupTooltips();
        
        // Indicador de força de senha
        this.setupPasswordStrength();
        
        // Preview de uploads
        this.setupFilePreview();
    }
    
    setupCEPAutoComplete() {
        document.addEventListener('input', async (e) => {
            if (e.target.classList.contains('cep-field')) {
                const cep = e.target.value.replace(/\\D/g, '');
                
                if (cep.length === 8) {
                    try {
                        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
                        const data = await response.json();
                        
                        if (!data.erro) {
                            this.fillAddressFields(data);
                        }
                    } catch (error) {
                        console.log('Erro ao buscar CEP:', error);
                    }
                }
            }
        });
    }
    
    fillAddressFields(addressData) {
        const mappings = {
            'logradouro': ['street', 'endereco', 'logradouro'],
            'bairro': ['neighborhood', 'bairro'],
            'localidade': ['city', 'cidade'],
            'uf': ['state', 'estado', 'uf']
        };
        
        Object.keys(mappings).forEach(key => {
            const value = addressData[key];
            if (value) {
                mappings[key].forEach(fieldName => {
                    const field = document.querySelector(`[name="${fieldName}"]`);
                    if (field && !field.value) {
                        field.value = value;
                        field.dispatchEvent(new Event('input'));
                    }
                });
            }
        });
    }
    
    setupTooltips() {
        // Adicionar tooltips para campos com validação
        document.querySelectorAll('[data-validate]').forEach(field => {
            if (!field.hasAttribute('title')) {
                const rules = field.getAttribute('data-validate').split('|');
                const hints = rules.map(rule => this.getHintForRule(rule));
                field.title = hints.join(' ');
            }
        });
    }
    
    getHintForRule(rule) {
        const hints = {
            'cpf': 'Digite um CPF válido (11 dígitos)',
            'phone': 'Digite um telefone válido (10-11 dígitos)',
            'email': 'Digite um e-mail válido',
            'required': 'Campo obrigatório',
            'futureDate': 'Data deve ser hoje ou no futuro',
            'pastDate': 'Data não pode ser no futuro'
        };
        
        return hints[rule] || '';
    }
    
    setupPasswordStrength() {
        document.querySelectorAll('input[type="password"]').forEach(field => {
            if (field.classList.contains('password-strength')) {
                this.addPasswordStrengthIndicator(field);
            }
        });
    }
    
    addPasswordStrengthIndicator(field) {
        const indicator = document.createElement('div');
        indicator.className = 'password-strength-indicator';
        indicator.innerHTML = `
            <div class="strength-bar">
                <div class="strength-fill"></div>
            </div>
            <div class="strength-text">Digite uma senha</div>
        `;
        
        field.parentNode.insertBefore(indicator, field.nextSibling);
        
        field.addEventListener('input', () => {
            const strength = this.calculatePasswordStrength(field.value);
            this.updatePasswordStrengthIndicator(indicator, strength);
        });
    }
    
    calculatePasswordStrength(password) {
        let score = 0;
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /\\d/.test(password),
            special: /[^\\w\\s]/.test(password)
        };
        
        score = Object.values(checks).filter(Boolean).length;
        
        const levels = ['Muito fraca', 'Fraca', 'Regular', 'Boa', 'Muito boa'];
        const colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997'];
        
        return {
            score,
            level: levels[score - 1] || levels[0],
            color: colors[score - 1] || colors[0],
            percentage: (score / 5) * 100
        };
    }
    
    updatePasswordStrengthIndicator(indicator, strength) {
        const fill = indicator.querySelector('.strength-fill');
        const text = indicator.querySelector('.strength-text');
        
        fill.style.width = `${strength.percentage}%`;
        fill.style.backgroundColor = strength.color;
        text.textContent = strength.level;
        text.style.color = strength.color;
    }
    
    setupFilePreview() {
        document.querySelectorAll('input[type="file"]').forEach(input => {
            if (input.accept && input.accept.includes('image/')) {
                input.addEventListener('change', (e) => {
                    this.showImagePreview(e.target);
                });
            }
        });
    }
    
    showImagePreview(input) {
        const file = input.files[0];
        if (!file) return;
        
        // Remover preview anterior
        const existingPreview = input.parentNode.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Criar novo preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            preview.innerHTML = `
                <img src="${e.target.result}" 
                     style="max-width: 200px; max-height: 200px; border-radius: 4px;" 
                     alt="Preview da imagem">
                <p class="text-muted small mt-1">${file.name} (${this.formatFileSize(file.size)})</p>
            `;
            
            input.parentNode.insertBefore(preview, input.nextSibling);
        };
        
        reader.readAsDataURL(file);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showNotification(message, type = 'info') {
        // Criar notificação toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.moveValidator = new MoveFormsValidator();
});

// CSS para melhorar a aparência das validações
const validationCSS = `
<style>
.is-valid {
    border-color: #28a745 !important;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
}

.is-invalid {
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}

.invalid-feedback {
    display: block;
    width: 100%;
    margin-top: 0.25rem;
    font-size: 0.875em;
    color: #dc3545;
}

.password-strength-indicator {
    margin-top: 0.5rem;
}

.strength-bar {
    height: 4px;
    background-color: #e9ecef;
    border-radius: 2px;
    overflow: hidden;
}

.strength-fill {
    height: 100%;
    transition: width 0.3s ease, background-color 0.3s ease;
    border-radius: 2px;
}

.strength-text {
    font-size: 0.75rem;
    margin-top: 0.25rem;
    font-weight: 500;
}

.form-control:focus {
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.image-preview img {
    border: 2px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Animações suaves */
.alert {
    animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Loading spinner para campos com validação assíncrona */
.field-loading {
    position: relative;
}

.field-loading::after {
    content: '';
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: translateY(-50%) rotate(0deg); }
    100% { transform: translateY(-50%) rotate(360deg); }
}
</style>
`;

// Inserir CSS no head
document.head.insertAdjacentHTML('beforeend', validationCSS);
"""

# Template HTML para demonstração das validações
FORM_EXAMPLE_HTML = """
<!-- Exemplo de formulário com validações JavaScript -->
<form class="needs-validation" novalidate>
    <div class="row">
        <!-- Campo Nome (obrigatório) -->
        <div class="col-md-6 mb-3">
            <label for="name" class="form-label">Nome Completo *</label>
            <input type="text" class="form-control" id="name" name="name" 
                   required minlength="3" maxlength="100"
                   data-validate="required|minLength:3">
        </div>
        
        <!-- Campo CPF -->
        <div class="col-md-6 mb-3">
            <label for="cpf" class="form-label">CPF</label>
            <input type="text" class="form-control cpf-field" id="cpf" name="cpf"
                   placeholder="000.000.000-00" maxlength="14">
        </div>
    </div>
    
    <div class="row">
        <!-- Campo Email -->
        <div class="col-md-6 mb-3">
            <label for="email" class="form-label">E-mail</label>
            <input type="email" class="form-control" id="email" name="email"
                   placeholder="exemplo@email.com">
        </div>
        
        <!-- Campo Telefone -->
        <div class="col-md-6 mb-3">
            <label for="phone" class="form-label">Telefone</label>
            <input type="text" class="form-control phone-field" id="phone" name="phone"
                   placeholder="(00) 00000-0000" maxlength="15">
        </div>
    </div>
    
    <div class="row">
        <!-- Campo Data de Nascimento -->
        <div class="col-md-6 mb-3">
            <label for="birth_date" class="form-label">Data de Nascimento</label>
            <input type="date" class="form-control past-date" id="birth_date" name="birth_date">
        </div>
        
        <!-- Campo Idade -->
        <div class="col-md-6 mb-3">
            <label for="age" class="form-label">Idade</label>
            <input type="number" class="form-control age-field" id="age" name="age" 
                   min="0" max="120">
        </div>
    </div>
    
    <div class="row">
        <!-- Campo CEP com auto-complete -->
        <div class="col-md-4 mb-3">
            <label for="cep" class="form-label">CEP</label>
            <input type="text" class="form-control cep-field" id="cep" name="cep"
                   placeholder="00000-000" maxlength="9">
        </div>
        
        <!-- Campo Endereço (preenchido automaticamente) -->
        <div class="col-md-8 mb-3">
            <label for="street" class="form-label">Endereço</label>
            <input type="text" class="form-control" id="street" name="street">
        </div>
    </div>
    
    <div class="row">
        <!-- Campo Bairro -->
        <div class="col-md-4 mb-3">
            <label for="neighborhood" class="form-label">Bairro</label>
            <input type="text" class="form-control" id="neighborhood" name="neighborhood">
        </div>
        
        <!-- Campo Cidade -->
        <div class="col-md-4 mb-3">
            <label for="city" class="form-label">Cidade</label>
            <input type="text" class="form-control" id="city" name="city">
        </div>
        
        <!-- Campo Estado -->
        <div class="col-md-4 mb-3">
            <label for="state" class="form-label">Estado</label>
            <input type="text" class="form-control" id="state" name="state" maxlength="2">
        </div>
    </div>
    
    <!-- Campo Senha com indicador de força -->
    <div class="row">
        <div class="col-md-6 mb-3">
            <label for="password" class="form-label">Senha</label>
            <input type="password" class="form-control password-strength" id="password" name="password"
                   minlength="8" data-validate="required|minLength:8">
        </div>
        
        <!-- Upload de foto com preview -->
        <div class="col-md-6 mb-3">
            <label for="photo" class="form-label">Foto</label>
            <input type="file" class="form-control" id="photo" name="photo" 
                   accept="image/*">
        </div>
    </div>
    
    <!-- Campo de observações -->
    <div class="mb-3">
        <label for="notes" class="form-label">Observações</label>
        <textarea class="form-control" id="notes" name="notes" rows="3" maxlength="500"></textarea>
        <div class="form-text">Máximo 500 caracteres</div>
    </div>
    
    <!-- Checkbox obrigatório -->
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" id="terms" name="terms" required>
        <label class="form-check-label" for="terms">
            Aceito os termos e condições *
        </label>
    </div>
    
    <div class="d-grid gap-2 d-md-flex justify-content-md-end">
        <button type="button" class="btn btn-secondary me-md-2">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
    </div>
</form>
"""

def create_validation_files():
    """Cria os arquivos JavaScript de validação"""
    import os
    from pathlib import Path
    
    base_dir = Path(__file__).resolve().parent
    static_js_dir = base_dir / 'static' / 'js'
    
    # Criar diretório se não existir
    static_js_dir.mkdir(parents=True, exist_ok=True)
    
    # Escrever arquivo JavaScript
    js_file = static_js_dir / 'form-validation.js'
    js_file.write_text(FORM_VALIDATION_JS.strip())
    
    # Criar template de exemplo
    templates_dir = base_dir / 'templates' / 'examples'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    example_file = templates_dir / 'form_validation_example.html'
    example_file.write_text(FORM_EXAMPLE_HTML.strip())
    
    print(f"✅ Arquivos de validação criados:")
    print(f"   📄 {js_file}")
    print(f"   📄 {example_file}")
    
    return js_file, example_file

if __name__ == '__main__':
    create_validation_files()
