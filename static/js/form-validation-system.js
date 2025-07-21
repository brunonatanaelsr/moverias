/**
 * Sistema de Validação JavaScript Real-time
 * Integração com Django Forms e HTMX
 */

class FormValidationSystem {
    constructor() {
        this.validators = new Map();
        this.initializeValidators();
        this.setupEventListeners();
    }

    initializeValidators() {
        // CPF Validator
        this.validators.set('cpf', {
            pattern: /^\d{3}\.\d{3}\.\d{3}-\d{2}$/,
            validate: this.validateCPF.bind(this),
            format: this.formatCPF.bind(this),
            message: 'CPF inválido. Use o formato 000.000.000-00'
        });

        // Phone Validator  
        this.validators.set('phone', {
            pattern: /^\(\d{2}\)\s\d{4,5}-\d{4}$/,
            validate: this.validatePhone.bind(this),
            format: this.formatPhone.bind(this),
            message: 'Telefone inválido. Use o formato (11) 99999-9999'
        });

        // Email Validator
        this.validators.set('email', {
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            validate: this.validateEmail.bind(this),
            format: this.formatEmail.bind(this),
            message: 'E-mail inválido'
        });

        // Name Validator
        this.validators.set('name', {
            validate: this.validateName.bind(this),
            message: 'Nome deve ter pelo menos 2 palavras'
        });
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.bindFormValidation();
        });

        // HTMX Integration
        document.addEventListener('htmx:afterSwap', () => {
            this.bindFormValidation();
        });
    }

    bindFormValidation() {
        // CPF fields
        document.querySelectorAll('input[name*="cpf"]').forEach(input => {
            this.bindFieldValidation(input, 'cpf');
        });

        // Phone fields
        document.querySelectorAll('input[name*="phone"], input[name*="telefone"]').forEach(input => {
            this.bindFieldValidation(input, 'phone');
        });

        // Email fields
        document.querySelectorAll('input[type="email"]').forEach(input => {
            this.bindFieldValidation(input, 'email');
        });

        // Name fields
        document.querySelectorAll('input[name*="name"], input[name*="nome"]').forEach(input => {
            this.bindFieldValidation(input, 'name');
        });

        // Form submission
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
    }

    bindFieldValidation(input, validatorType) {
        const validator = this.validators.get(validatorType);
        if (!validator) return;

        // Real-time formatting
        input.addEventListener('input', (e) => {
            if (validator.format) {
                e.target.value = validator.format(e.target.value);
            }
            this.validateField(e.target, validatorType);
        });

        // Validation on blur
        input.addEventListener('blur', (e) => {
            this.validateField(e.target, validatorType);
            
            // AJAX validation for CPF uniqueness
            if (validatorType === 'cpf' && this.isValidCPF(e.target.value)) {
                this.checkCPFUniqueness(e.target);
            }
        });
    }

    validateField(input, validatorType) {
        const validator = this.validators.get(validatorType);
        const isValid = validator.validate(input.value);
        
        this.clearFieldMessages(input);
        
        if (input.value && !isValid) {
            this.showFieldError(input, validator.message);
            return false;
        } else if (input.value && isValid) {
            this.showFieldSuccess(input);
            return true;
        }
        
        return true;
    }

    // CPF Validation
    validateCPF(cpf) {
        const cleanCPF = cpf.replace(/\D/g, '');
        if (cleanCPF.length !== 11) return false;
        
        // Check for known invalid patterns
        if (/^(\d)\1{10}$/.test(cleanCPF)) return false;
        
        // Validate check digits
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(cleanCPF.charAt(i)) * (10 - i);
        }
        let remainder = (sum * 10) % 11;
        if (remainder === 10 || remainder === 11) remainder = 0;
        if (remainder !== parseInt(cleanCPF.charAt(9))) return false;
        
        sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += parseInt(cleanCPF.charAt(i)) * (11 - i);
        }
        remainder = (sum * 10) % 11;
        if (remainder === 10 || remainder === 11) remainder = 0;
        return remainder === parseInt(cleanCPF.charAt(10));
    }

    formatCPF(value) {
        const numbers = value.replace(/\D/g, '');
        return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }

    isValidCPF(value) {
        return this.validateCPF(value);
    }

    async checkCPFUniqueness(input) {
        const cpf = input.value.replace(/\D/g, '');
        const formData = new FormData();
        formData.append('cpf', cpf);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch('/api/validate/cpf/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.exists) {
                this.showFieldError(input, 'Este CPF já está cadastrado no sistema');
            }
        } catch (error) {
            console.error('Erro ao verificar CPF:', error);
        }
    }

    // Phone Validation
    validatePhone(phone) {
        const cleanPhone = phone.replace(/\D/g, '');
        return cleanPhone.length >= 10 && cleanPhone.length <= 11;
    }

    formatPhone(value) {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 10) {
            return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        } else {
            return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        }
    }

    // Email Validation
    validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    formatEmail(value) {
        return value.toLowerCase().trim();
    }

    // Name Validation
    validateName(name) {
        return name.trim().split(' ').filter(word => word.length > 0).length >= 2;
    }

    // UI Feedback Methods
    showFieldError(input, message) {
        input.classList.remove('border-green-500', 'focus:border-green-500');
        input.classList.add('border-red-500', 'focus:border-red-500');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error mt-1 text-sm text-red-600 flex items-center';
        errorDiv.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            ${message}
        `;
        input.parentNode.appendChild(errorDiv);
    }

    showFieldSuccess(input) {
        input.classList.remove('border-red-500', 'focus:border-red-500');
        input.classList.add('border-green-500', 'focus:border-green-500');
        
        const successDiv = document.createElement('div');
        successDiv.className = 'field-success mt-1 text-sm text-green-600 flex items-center';
        successDiv.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
            Válido
        `;
        input.parentNode.appendChild(successDiv);
    }

    clearFieldMessages(input) {
        const existingMessages = input.parentNode.querySelectorAll('.field-error, .field-success');
        existingMessages.forEach(msg => msg.remove());
        
        input.classList.remove(
            'border-red-500', 'focus:border-red-500',
            'border-green-500', 'focus:border-green-500'
        );
    }

    handleFormSubmit(event) {
        const form = event.target;
        let isValid = true;

        // Validate all fields
        form.querySelectorAll('input[data-validate]').forEach(input => {
            const validatorType = input.dataset.validate;
            if (!this.validateField(input, validatorType)) {
                isValid = false;
            }
        });

        if (!isValid) {
            event.preventDefault();
            this.showFormError(form, 'Por favor, corrija os erros antes de continuar.');
        }
    }

    showFormError(form, message) {
        const existingError = form.querySelector('.form-error');
        if (existingError) existingError.remove();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded';
        errorDiv.textContent = message;
        
        form.insertBefore(errorDiv, form.firstChild);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Progress Bar System for Uploads
class UploadProgressSystem {
    constructor() {
        this.activeUploads = new Map();
        this.setupUploadHandlers();
    }

    setupUploadHandlers() {
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file' && e.target.hasAttribute('data-upload-progress')) {
                this.handleFileUpload(e.target);
            }
        });
    }

    handleFileUpload(fileInput) {
        const files = Array.from(fileInput.files);
        const progressContainer = document.getElementById('upload-progress-container');
        
        if (!progressContainer) {
            console.warn('Upload progress container not found');
            return;
        }

        files.forEach(file => this.uploadFile(file, progressContainer));
    }

    uploadFile(file, container) {
        const uploadId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const progressBar = this.createProgressBar(file.name, uploadId);
        container.appendChild(progressBar);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.updateProgress(uploadId, percentComplete);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    this.showUploadSuccess(uploadId, response);
                } catch (e) {
                    this.showUploadError(uploadId, 'Resposta inválida do servidor');
                }
            } else {
                this.showUploadError(uploadId, `Erro no upload (${xhr.status})`);
            }
        });

        xhr.addEventListener('error', () => {
            this.showUploadError(uploadId, 'Erro de conexão');
        });

        xhr.open('POST', '/core/upload/');
        xhr.send(formData);

        this.activeUploads.set(uploadId, { xhr, file });
    }

    createProgressBar(filename, uploadId) {
        const progressHTML = `
            <div class="mb-4 p-4 bg-gray-50 rounded-lg border">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700 truncate">${filename}</span>
                    <span class="text-sm text-gray-500 progress-percent">0%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full transition-all duration-300 progress-bar" style="width: 0%"></div>
                </div>
                <div class="mt-2 text-xs text-gray-500 status-text">Preparando upload...</div>
                <button class="mt-2 text-xs text-red-600 hover:text-red-800 cancel-button" onclick="uploadSystem.cancelUpload('${uploadId}')">
                    Cancelar
                </button>
            </div>
        `;
        
        const container = document.createElement('div');
        container.id = uploadId;
        container.innerHTML = progressHTML;
        return container;
    }

    updateProgress(uploadId, percent) {
        const container = document.getElementById(uploadId);
        if (!container) return;

        const progressBar = container.querySelector('.progress-bar');
        const percentText = container.querySelector('.progress-percent');
        const statusText = container.querySelector('.status-text');

        progressBar.style.width = `${percent}%`;
        percentText.textContent = `${Math.round(percent)}%`;
        statusText.textContent = percent < 100 ? 'Enviando...' : 'Processando...';
    }

    showUploadSuccess(uploadId, response) {
        const container = document.getElementById(uploadId);
        if (!container) return;

        container.className = 'mb-4 p-4 bg-green-50 rounded-lg border border-green-200';
        container.innerHTML = `
            <div class="flex items-center text-green-800">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                Upload concluído com sucesso!
            </div>
            <div class="mt-1 text-sm text-green-600">
                ${response.filename || 'Arquivo processado'}
            </div>
        `;

        // Remove after 5 seconds
        setTimeout(() => {
            container.style.opacity = '0';
            setTimeout(() => container.remove(), 300);
        }, 5000);

        this.activeUploads.delete(uploadId);
    }

    showUploadError(uploadId, message) {
        const container = document.getElementById(uploadId);
        if (!container) return;

        container.className = 'mb-4 p-4 bg-red-50 rounded-lg border border-red-200';
        container.innerHTML = `
            <div class="flex items-center text-red-800">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                Erro no upload
            </div>
            <div class="mt-1 text-sm text-red-600">${message}</div>
            <button class="mt-2 text-sm text-blue-600 hover:text-blue-800" onclick="this.parentElement.remove()">
                Remover
            </button>
        `;

        this.activeUploads.delete(uploadId);
    }

    cancelUpload(uploadId) {
        const upload = this.activeUploads.get(uploadId);
        if (upload) {
            upload.xhr.abort();
            this.activeUploads.delete(uploadId);
            document.getElementById(uploadId)?.remove();
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialize systems
const validationSystem = new FormValidationSystem();
const uploadSystem = new UploadProgressSystem();

// Global functions for template usage
window.validationSystem = validationSystem;
window.uploadSystem = uploadSystem;
