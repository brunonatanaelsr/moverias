// ===================================
// MÓDULO DE COMUNICAÇÃO - JAVASCRIPT
// ===================================

(function() {
    'use strict';

    // Constantes e Configurações
    const COMMUNICATION_CONFIG = {
        apiEndpoints: {
            announcements: '/api/communication/announcements/',
            memos: '/api/communication/memos/',
            newsletters: '/api/communication/newsletters/',
            dashboardStats: '/api/communication/dashboard-stats/',
            markAsRead: '/api/communication/mark-as-read/',
            search: '/api/communication/search/',
            upload: '/api/communication/upload/',
        },
        pagination: {
            itemsPerPage: 12,
            maxPages: 10
        },
        uploads: {
            maxFileSize: 10 * 1024 * 1024, // 10MB
            allowedTypes: ['image/*', 'application/pdf', '.doc', '.docx', '.txt']
        },
        notifications: {
            autoHide: 5000,
            position: 'top-right'
        }
    };

    // Utilitários
    const Utils = {
        /**
         * Faz requisição AJAX com token CSRF
         */
        async request(url, options = {}) {
            const token = this.getCSRFToken();
            const defaultOptions = {
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            };

            const config = { ...defaultOptions, ...options };
            if (config.headers['Content-Type'] === 'multipart/form-data') {
                delete config.headers['Content-Type'];
            }

            try {
                const response = await fetch(url, config);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Request error:', error);
                NotificationManager.error('Erro na comunicação com o servidor');
                throw error;
            }
        },

        /**
         * Obtém o token CSRF
         */
        getCSRFToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                   document.querySelector('meta[name=csrf-token]')?.content ||
                   '';
        },

        /**
         * Debounce para otimizar pesquisas
         */
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Formatar data para exibição
         */
        formatDate(dateString, options = {}) {
            const date = new Date(dateString);
            const defaultOptions = {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            return date.toLocaleDateString('pt-BR', { ...defaultOptions, ...options });
        },

        /**
         * Sanitizar HTML
         */
        sanitizeHTML(str) {
            const temp = document.createElement('div');
            temp.textContent = str;
            return temp.innerHTML;
        },

        /**
         * Validar arquivo de upload
         */
        validateFile(file) {
            const { maxFileSize, allowedTypes } = COMMUNICATION_CONFIG.uploads;
            
            if (file.size > maxFileSize) {
                return { valid: false, error: 'Arquivo muito grande (máximo 10MB)' };
            }

            const isValidType = allowedTypes.some(type => {
                if (type.includes('*')) {
                    return file.type.startsWith(type.replace('*', ''));
                }
                return file.name.toLowerCase().endsWith(type) || file.type === type;
            });

            if (!isValidType) {
                return { valid: false, error: 'Tipo de arquivo não permitido' };
            }

            return { valid: true };
        }
    };

    // Gerenciador de Notificações
    const NotificationManager = {
        container: null,

        init() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'comm-notifications';
                this.container.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    pointer-events: none;
                `;
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info', duration = COMMUNICATION_CONFIG.notifications.autoHide) {
            this.init();
            
            const notification = document.createElement('div');
            notification.className = `comm-alert ${type} comm-fade-in`;
            notification.style.cssText = `
                margin-bottom: 10px;
                pointer-events: auto;
                min-width: 300px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;
            notification.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>${message}</span>
                    <button type="button" style="background: none; border: none; font-size: 18px; cursor: pointer; padding: 0; margin-left: 10px;" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
            `;

            this.container.appendChild(notification);

            if (duration > 0) {
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, duration);
            }
        },

        success(message, duration) {
            this.show(message, 'success', duration);
        },

        error(message, duration) {
            this.show(message, 'error', duration);
        },

        warning(message, duration) {
            this.show(message, 'warning', duration);
        },

        info(message, duration) {
            this.show(message, 'info', duration);
        }
    };

    // Gerenciador de Modais
    const ModalManager = {
        stack: [],

        open(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;

            modal.classList.add('show');
            this.stack.push(modalId);
            document.body.style.overflow = 'hidden';

            // Event listeners
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close(modalId);
                }
            });

            const closeBtn = modal.querySelector('.comm-modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.close(modalId));
            }
        },

        close(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;

            modal.classList.remove('show');
            this.stack = this.stack.filter(id => id !== modalId);
            
            if (this.stack.length === 0) {
                document.body.style.overflow = '';
            }
        },

        closeAll() {
            this.stack.forEach(modalId => this.close(modalId));
        }
    };

    // Gerenciador de Upload de Arquivos
    const FileUploadManager = {
        init() {
            const uploadInputs = document.querySelectorAll('input[type="file"]');
            uploadInputs.forEach(input => this.setupFileInput(input));
        },

        setupFileInput(input) {
            const wrapper = input.closest('.file-upload-wrapper') || this.createWrapper(input);
            const preview = wrapper.querySelector('.file-preview') || this.createPreview(wrapper);
            
            input.addEventListener('change', (e) => {
                this.handleFileSelect(e.target, preview);
            });

            // Drag and drop
            wrapper.addEventListener('dragover', (e) => {
                e.preventDefault();
                wrapper.classList.add('dragover');
            });

            wrapper.addEventListener('dragleave', () => {
                wrapper.classList.remove('dragover');
            });

            wrapper.addEventListener('drop', (e) => {
                e.preventDefault();
                wrapper.classList.remove('dragover');
                
                const files = Array.from(e.dataTransfer.files);
                if (input.multiple) {
                    input.files = e.dataTransfer.files;
                } else if (files.length > 0) {
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    input.files = dt.files;
                }
                
                this.handleFileSelect(input, preview);
            });
        },

        createWrapper(input) {
            const wrapper = document.createElement('div');
            wrapper.className = 'file-upload-wrapper';
            wrapper.style.cssText = `
                border: 2px dashed #d1d5db;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                transition: all 0.2s ease;
                position: relative;
            `;
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            
            return wrapper;
        },

        createPreview(wrapper) {
            const preview = document.createElement('div');
            preview.className = 'file-preview';
            preview.style.cssText = `
                margin-top: 10px;
                display: grid;
                gap: 10px;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            `;
            wrapper.appendChild(preview);
            return preview;
        },

        handleFileSelect(input, preview) {
            const files = Array.from(input.files);
            preview.innerHTML = '';

            files.forEach((file, index) => {
                const validation = Utils.validateFile(file);
                
                if (!validation.valid) {
                    NotificationManager.error(validation.error);
                    return;
                }

                const fileItem = this.createFilePreview(file, index, input);
                preview.appendChild(fileItem);
            });
        },

        createFilePreview(file, index, input) {
            const item = document.createElement('div');
            item.className = 'file-preview-item';
            item.style.cssText = `
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 10px;
                position: relative;
                background: white;
            `;

            const isImage = file.type.startsWith('image/');
            let content = '';

            if (isImage) {
                const url = URL.createObjectURL(file);
                content = `
                    <img src="${url}" alt="${file.name}" style="width: 100%; height: 80px; object-fit: cover; border-radius: 4px;">
                `;
            } else {
                content = `
                    <div style="height: 80px; display: flex; align-items: center; justify-content: center; background: #f3f4f6; border-radius: 4px;">
                        <i class="fas fa-file" style="font-size: 24px; color: #6b7280;"></i>
                    </div>
                `;
            }

            item.innerHTML = `
                ${content}
                <div style="margin-top: 8px; font-size: 12px; color: #6b7280; text-align: center;">
                    <div style="font-weight: 500; truncate;">${file.name}</div>
                    <div>${this.formatFileSize(file.size)}</div>
                </div>
                <button type="button" class="remove-file" data-index="${index}" style="
                    position: absolute;
                    top: -8px;
                    right: -8px;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: #ef4444;
                    color: white;
                    border: none;
                    cursor: pointer;
                    font-size: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">×</button>
            `;

            // Remover arquivo
            item.querySelector('.remove-file').addEventListener('click', () => {
                this.removeFile(input, index);
            });

            return item;
        },

        removeFile(input, indexToRemove) {
            const dt = new DataTransfer();
            const files = Array.from(input.files);
            
            files.forEach((file, index) => {
                if (index !== indexToRemove) {
                    dt.items.add(file);
                }
            });
            
            input.files = dt.files;
            
            // Atualizar preview
            const wrapper = input.closest('.file-upload-wrapper');
            const preview = wrapper.querySelector('.file-preview');
            this.handleFileSelect(input, preview);
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    };

    // Gerenciador de Formulários
    const FormManager = {
        init() {
            this.setupFormValidation();
            this.setupAutoSave();
            this.setupTinyMCE();
        },

        setupFormValidation() {
            const forms = document.querySelectorAll('form[data-validate="true"]');
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                    }
                });

                // Validação em tempo real
                const inputs = form.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    input.addEventListener('blur', () => this.validateField(input));
                });
            });
        },

        validateForm(form) {
            let isValid = true;
            const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            
            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            return isValid;
        },

        validateField(field) {
            const value = field.value.trim();
            const isRequired = field.hasAttribute('required');
            let isValid = true;
            let message = '';

            // Campo obrigatório
            if (isRequired && !value) {
                isValid = false;
                message = 'Este campo é obrigatório';
            }

            // Email
            if (field.type === 'email' && value && !this.isValidEmail(value)) {
                isValid = false;
                message = 'Email inválido';
            }

            // Comprimento mínimo
            const minLength = field.getAttribute('minlength');
            if (minLength && value.length < parseInt(minLength)) {
                isValid = false;
                message = `Mínimo de ${minLength} caracteres`;
            }

            // Comprimento máximo
            const maxLength = field.getAttribute('maxlength');
            if (maxLength && value.length > parseInt(maxLength)) {
                isValid = false;
                message = `Máximo de ${maxLength} caracteres`;
            }

            this.showFieldError(field, message);
            return isValid;
        },

        showFieldError(field, message) {
            // Remover erro anterior
            const existingError = field.parentNode.querySelector('.comm-form-error');
            if (existingError) {
                existingError.remove();
            }

            field.classList.remove('error');

            if (message) {
                field.classList.add('error');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'comm-form-error';
                errorDiv.textContent = message;
                field.parentNode.appendChild(errorDiv);
            }
        },

        isValidEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },

        setupAutoSave() {
            const autoSaveForms = document.querySelectorAll('form[data-autosave="true"]');
            autoSaveForms.forEach(form => {
                const formId = form.id || `form_${Date.now()}`;
                const inputs = form.querySelectorAll('input, textarea, select');
                
                // Carregar dados salvos
                this.loadAutoSaveData(formId, inputs);

                // Salvar automaticamente
                const debouncedSave = Utils.debounce(() => {
                    this.saveAutoSaveData(formId, inputs);
                }, 1000);

                inputs.forEach(input => {
                    input.addEventListener('input', debouncedSave);
                    input.addEventListener('change', debouncedSave);
                });
            });
        },

        saveAutoSaveData(formId, inputs) {
            const data = {};
            inputs.forEach(input => {
                if (input.name) {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        data[input.name] = input.checked;
                    } else {
                        data[input.name] = input.value;
                    }
                }
            });
            
            localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
        },

        loadAutoSaveData(formId, inputs) {
            try {
                const savedData = localStorage.getItem(`autosave_${formId}`);
                if (savedData) {
                    const data = JSON.parse(savedData);
                    inputs.forEach(input => {
                        if (input.name && data.hasOwnProperty(input.name)) {
                            if (input.type === 'checkbox' || input.type === 'radio') {
                                input.checked = data[input.name];
                            } else {
                                input.value = data[input.name];
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Erro ao carregar dados salvos:', error);
            }
        },

        clearAutoSaveData(formId) {
            localStorage.removeItem(`autosave_${formId}`);
        },

        setupTinyMCE() {
            if (typeof tinymce !== 'undefined') {
                tinymce.init({
                    selector: '.wysiwyg-editor',
                    plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount',
                    toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table | align lineheight | numlist bullist indent outdent | emoticons charmap | removeformat',
                    tinycomments_mode: 'embedded',
                    tinycomments_author: 'Author name',
                    mergetags_list: [
                        { value: 'First.Name', title: 'First Name' },
                        { value: 'Email', title: 'Email' },
                    ],
                    language: 'pt_BR',
                    height: 400,
                    setup: function(editor) {
                        editor.on('change', function() {
                            editor.save();
                        });
                    }
                });
            }
        }
    };

    // Gerenciador de Pesquisa
    const SearchManager = {
        init() {
            const searchInputs = document.querySelectorAll('.search-input');
            searchInputs.forEach(input => this.setupSearch(input));
        },

        setupSearch(input) {
            const resultsContainer = input.getAttribute('data-results') || 
                                   input.parentNode.querySelector('.search-results');
            
            if (!resultsContainer) return;

            const debouncedSearch = Utils.debounce(async (query) => {
                if (query.length < 2) {
                    this.hideResults(resultsContainer);
                    return;
                }

                try {
                    const results = await this.performSearch(query, input.getAttribute('data-type'));
                    this.showResults(resultsContainer, results, query);
                } catch (error) {
                    console.error('Search error:', error);
                }
            }, 300);

            input.addEventListener('input', (e) => {
                debouncedSearch(e.target.value.trim());
            });

            // Fechar resultados ao clicar fora
            document.addEventListener('click', (e) => {
                if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                    this.hideResults(resultsContainer);
                }
            });
        },

        async performSearch(query, type = 'all') {
            const url = `${COMMUNICATION_CONFIG.apiEndpoints.search}?q=${encodeURIComponent(query)}&type=${type}`;
            return await Utils.request(url);
        },

        showResults(container, results, query) {
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }

            if (!container) return;

            container.innerHTML = '';
            container.style.display = 'block';

            if (results.length === 0) {
                container.innerHTML = '<div class="search-no-results">Nenhum resultado encontrado</div>';
                return;
            }

            results.forEach(result => {
                const item = this.createResultItem(result, query);
                container.appendChild(item);
            });
        },

        createResultItem(result, query) {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.style.cssText = `
                padding: 10px;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
                transition: background-color 0.15s ease;
            `;

            const highlightedTitle = this.highlightText(result.title, query);
            const highlightedContent = this.highlightText(result.content, query);

            item.innerHTML = `
                <div style="font-weight: 500; margin-bottom: 4px;">${highlightedTitle}</div>
                <div style="font-size: 0.875rem; color: #6b7280; line-height: 1.4;">${highlightedContent}</div>
                <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 4px;">
                    ${result.type} • ${Utils.formatDate(result.created_at)}
                </div>
            `;

            item.addEventListener('click', () => {
                window.location.href = result.url;
            });

            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f3f4f6';
            });

            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = '';
            });

            return item;
        },

        hideResults(container) {
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }
            if (container) {
                container.style.display = 'none';
            }
        },

        highlightText(text, query) {
            if (!query || !text) return text;
            
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        }
    };

    // Gerenciador de Dashboard
    const DashboardManager = {
        async init() {
            await this.loadStats();
            this.setupRefresh();
        },

        async loadStats() {
            try {
                const stats = await Utils.request(COMMUNICATION_CONFIG.apiEndpoints.dashboardStats);
                this.updateStatsDisplay(stats);
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
            }
        },

        updateStatsDisplay(stats) {
            // Atualizar contadores
            Object.entries(stats).forEach(([key, value]) => {
                const element = document.querySelector(`[data-stat="${key}"]`);
                if (element) {
                    this.animateCounter(element, value);
                }
            });

            // Atualizar gráficos se houver
            if (typeof Chart !== 'undefined') {
                this.updateCharts(stats);
            }
        },

        animateCounter(element, targetValue) {
            const duration = 1000;
            const startValue = parseInt(element.textContent) || 0;
            const startTime = performance.now();

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const currentValue = Math.round(startValue + (targetValue - startValue) * progress);
                element.textContent = currentValue.toLocaleString('pt-BR');

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        },

        setupRefresh() {
            const refreshButton = document.querySelector('.refresh-stats');
            if (refreshButton) {
                refreshButton.addEventListener('click', () => {
                    this.loadStats();
                    NotificationManager.success('Estatísticas atualizadas');
                });
            }

            // Auto-refresh a cada 5 minutos
            setInterval(() => {
                this.loadStats();
            }, 5 * 60 * 1000);
        },

        updateCharts(stats) {
            // Implementar gráficos conforme necessário
            console.log('Updating charts with stats:', stats);
        }
    };

    // Gerenciador de Leitura/Marcação
    const ReadTrackingManager = {
        init() {
            this.setupReadTracking();
            this.setupMarkAsRead();
        },

        setupReadTracking() {
            // Marcar como lido automaticamente após um tempo
            const trackableElements = document.querySelectorAll('[data-track-read]');
            
            trackableElements.forEach(element => {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            setTimeout(() => {
                                if (entry.isIntersecting) {
                                    this.markAsRead(element.getAttribute('data-track-read'));
                                }
                            }, 3000); // 3 segundos de visualização
                        }
                    });
                }, { threshold: 0.5 });

                observer.observe(element);
            });
        },

        setupMarkAsRead() {
            const markReadButtons = document.querySelectorAll('.mark-as-read');
            markReadButtons.forEach(button => {
                button.addEventListener('click', async (e) => {
                    e.preventDefault();
                    const id = button.getAttribute('data-id');
                    const type = button.getAttribute('data-type');
                    
                    try {
                        await this.markAsRead(id, type);
                        button.style.display = 'none';
                        NotificationManager.success('Marcado como lido');
                    } catch (error) {
                        NotificationManager.error('Erro ao marcar como lido');
                    }
                });
            });
        },

        async markAsRead(id, type = 'announcement') {
            const url = COMMUNICATION_CONFIG.apiEndpoints.markAsRead;
            await Utils.request(url, {
                method: 'POST',
                body: JSON.stringify({ id, type })
            });
        }
    };

    // Inicialização
    document.addEventListener('DOMContentLoaded', () => {
        try {
            // Inicializar todos os gerenciadores
            NotificationManager.init();
            FileUploadManager.init();
            FormManager.init();
            SearchManager.init();
            ReadTrackingManager.init();
            
            // Inicializar dashboard se estiver na página
            if (document.querySelector('.dashboard-stats')) {
                DashboardManager.init();
            }

            // Event listeners globais
            document.addEventListener('keydown', (e) => {
                // Fechar modais com ESC
                if (e.key === 'Escape') {
                    ModalManager.closeAll();
                }
            });

            // Tooltips
            const tooltipElements = document.querySelectorAll('[data-tooltip]');
            tooltipElements.forEach(element => {
                element.classList.add('comm-tooltip');
            });

            console.log('Communication module initialized successfully');
        } catch (error) {
            console.error('Error initializing communication module:', error);
        }
    });

    // Exportar para uso global
    window.CommunicationModule = {
        Utils,
        NotificationManager,
        ModalManager,
        FileUploadManager,
        FormManager,
        SearchManager,
        DashboardManager,
        ReadTrackingManager
    };

})();
