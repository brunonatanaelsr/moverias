/**
 * Sistema de Loading States Avançado
 * Gerencia estados de carregamento em toda a aplicação
 */

class LoadingStateManager {
    constructor() {
        this.loadingStates = new Map();
        this.globalLoadingCount = 0;
        this.init();
    }

    init() {
        this.createLoadingTemplates();
        this.setupEventListeners();
        this.injectStyles();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.bindLoadingElements();
        });

        // HTMX integration
        document.addEventListener('htmx:beforeRequest', (e) => {
            this.showLoadingForElement(e.target);
        });

        document.addEventListener('htmx:afterRequest', (e) => {
            this.hideLoadingForElement(e.target);
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            this.showLoadingForForm(e.target);
        });

        // AJAX requests
        document.addEventListener('ajaxStart', () => {
            this.showGlobalLoading();
        });

        document.addEventListener('ajaxStop', () => {
            this.hideGlobalLoading();
        });
    }

    bindLoadingElements() {
        // Bind buttons with loading states
        document.querySelectorAll('[data-loading]').forEach(button => {
            button.addEventListener('click', (e) => {
                this.showLoadingForButton(e.target);
            });
        });

        // Bind forms with loading states
        document.querySelectorAll('form[data-loading-form]').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.showLoadingForForm(form);
            });
        });

        // Bind links with loading states
        document.querySelectorAll('a[data-loading]').forEach(link => {
            link.addEventListener('click', (e) => {
                this.showLoadingForLink(e.target);
            });
        });

        // Bind module-specific elements
        this.bindModuleSpecificElements();
    }

    bindModuleSpecificElements() {
        // Ações críticas por módulo
        const criticalActions = [
            // Dashboard
            'button[data-action="export-report"]',
            'button[data-action="generate-certificate"]',
            'button[data-action="send-notification"]',
            
            // Beneficiários
            'button[data-action="update-beneficiary"]',
            'button[data-action="delete-beneficiary"]',
            'button[data-action="bulk-update"]',
            
            // Workshops
            'button[data-action="create-workshop"]',
            'button[data-action="update-workshop"]',
            'button[data-action="register-attendance"]',
            'button[data-action="generate-evaluation"]',
            
            // Projects
            'button[data-action="create-project"]',
            'button[data-action="update-project"]',
            'button[data-action="enroll-participants"]',
            
            // Users
            'button[data-action="create-user"]',
            'button[data-action="update-user"]',
            'button[data-action="change-permissions"]',
            'button[data-action="activate-user"]',
            'button[data-action="deactivate-user"]',
            
            // Certificates
            'button[data-action="generate-certificates"]',
            'button[data-action="send-certificates"]',
            'button[data-action="verify-certificate"]',
            
            // Uploads
            'button[data-action="upload-file"]',
            'button[data-action="process-upload"]',
            'button[data-action="validate-file"]',
            
            // Social
            'button[data-action="create-anamnesis"]',
            'button[data-action="update-anamnesis"]',
            'button[data-action="generate-social-report"]',
            
            // HR
            'button[data-action="process-hr-document"]',
            'button[data-action="generate-hr-report"]'
        ];

        criticalActions.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.addEventListener('click', (e) => {
                    this.showLoadingForButton(e.target);
                });
            });
        });

        // Forms críticos
        const criticalForms = [
            '#beneficiary-form',
            '#workshop-form',
            '#project-form',
            '#user-form',
            '#certificate-form',
            '#upload-form',
            '#anamnesis-form',
            '#evaluation-form',
            '#attendance-form',
            '#notification-form',
            '#report-form'
        ];

        criticalForms.forEach(selector => {
            const form = document.querySelector(selector);
            if (form) {
                form.addEventListener('submit', (e) => {
                    this.showLoadingForForm(form);
                });
            }
        });

        // Links de navegação críticos
        const criticalLinks = [
            'a[data-action="export"]',
            'a[data-action="download"]',
            'a[data-action="generate"]',
            'a[data-action="process"]',
            'a[href*="delete"]',
            'a[href*="activate"]',
            'a[href*="deactivate"]'
        ];

        criticalLinks.forEach(selector => {
            document.querySelectorAll(selector).forEach(link => {
                link.addEventListener('click', (e) => {
                    this.showLoadingForLink(e.target);
                });
            });
        });
    }

    showLoadingForButton(button) {
        const loadingId = this.generateLoadingId();
        const originalContent = button.innerHTML;
        const loadingText = button.dataset.loadingText || 'Carregando...';
        const loadingIcon = button.dataset.loadingIcon || 'fa-spinner fa-spin';

        // Store original state
        this.loadingStates.set(loadingId, {
            element: button,
            originalContent,
            originalDisabled: button.disabled,
            type: 'button'
        });

        // Apply loading state
        button.disabled = true;
        button.innerHTML = `<i class="fas ${loadingIcon} mr-2"></i>${loadingText}`;
        button.classList.add('loading-state');
        button.dataset.loadingId = loadingId;

        return loadingId;
    }

    showLoadingForForm(form) {
        const loadingId = this.generateLoadingId();
        const submitButton = form.querySelector('button[type="submit"]');
        const formContainer = form.closest('.form-container') || form;

        // Store original state
        this.loadingStates.set(loadingId, {
            element: form,
            submitButton,
            originalSubmitText: submitButton?.textContent,
            originalSubmitDisabled: submitButton?.disabled,
            type: 'form'
        });

        // Apply loading state to submit button
        if (submitButton) {
            const loadingText = submitButton.dataset.loadingText || 'Enviando...';
            submitButton.disabled = true;
            submitButton.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;
            submitButton.classList.add('loading-state');
        }

        // Show form overlay
        this.showFormOverlay(formContainer, loadingId);
        form.dataset.loadingId = loadingId;

        return loadingId;
    }

    showLoadingForLink(link) {
        const loadingId = this.generateLoadingId();
        const originalContent = link.innerHTML;
        const loadingText = link.dataset.loadingText || 'Carregando...';

        // Store original state
        this.loadingStates.set(loadingId, {
            element: link,
            originalContent,
            type: 'link'
        });

        // Apply loading state
        link.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;
        link.classList.add('loading-state');
        link.dataset.loadingId = loadingId;

        return loadingId;
    }

    showLoadingForElement(element) {
        const loadingId = this.generateLoadingId();
        const overlay = this.createLoadingOverlay();
        
        // Store original state
        this.loadingStates.set(loadingId, {
            element,
            overlay,
            type: 'element'
        });

        // Position overlay
        const rect = element.getBoundingClientRect();
        overlay.style.position = 'absolute';
        overlay.style.top = rect.top + 'px';
        overlay.style.left = rect.left + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';

        document.body.appendChild(overlay);
        element.dataset.loadingId = loadingId;

        return loadingId;
    }

    showFormOverlay(container, loadingId) {
        const overlay = document.createElement('div');
        overlay.className = 'form-loading-overlay';
        overlay.dataset.loadingId = loadingId;
        
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border" role="status">
                    <span class="sr-only">Carregando...</span>
                </div>
                <p class="loading-text mt-2">Processando...</p>
            </div>
        `;

        container.style.position = 'relative';
        container.appendChild(overlay);
    }

    showGlobalLoading() {
        this.globalLoadingCount++;
        
        if (this.globalLoadingCount === 1) {
            const loader = document.getElementById('global-loading');
            if (loader) {
                loader.classList.remove('hidden');
                loader.classList.add('flex');
            }
        }
    }

    hideGlobalLoading() {
        this.globalLoadingCount = Math.max(0, this.globalLoadingCount - 1);
        
        if (this.globalLoadingCount === 0) {
            const loader = document.getElementById('global-loading');
            if (loader) {
                loader.classList.add('hidden');
                loader.classList.remove('flex');
            }
        }
    }

    hideLoadingForElement(element) {
        const loadingId = element.dataset.loadingId;
        if (!loadingId) return;

        this.hideLoading(loadingId);
    }

    hideLoading(loadingId) {
        const state = this.loadingStates.get(loadingId);
        if (!state) return;

        const { element, type } = state;

        switch (type) {
            case 'button':
                element.disabled = state.originalDisabled;
                element.innerHTML = state.originalContent;
                element.classList.remove('loading-state');
                break;

            case 'form':
                if (state.submitButton) {
                    state.submitButton.disabled = state.originalSubmitDisabled;
                    state.submitButton.textContent = state.originalSubmitText;
                    state.submitButton.classList.remove('loading-state');
                }
                // Remove overlay
                const overlay = element.querySelector('.form-loading-overlay');
                if (overlay) overlay.remove();
                break;

            case 'link':
                element.innerHTML = state.originalContent;
                element.classList.remove('loading-state');
                break;

            case 'element':
                if (state.overlay) {
                    state.overlay.remove();
                }
                break;
        }

        delete element.dataset.loadingId;
        this.loadingStates.delete(loadingId);
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
            </div>
        `;

        return overlay;
    }

    createLoadingTemplates() {
        // Create global loading indicator
        if (!document.getElementById('global-loading')) {
            const globalLoader = document.createElement('div');
            globalLoader.id = 'global-loading';
            globalLoader.className = 'fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 hidden items-center justify-center z-50';
            
            globalLoader.innerHTML = `
                <div class="bg-white rounded-lg p-6 shadow-lg">
                    <div class="flex items-center space-x-3">
                        <div class="spinner-border text-blue-600" role="status">
                            <span class="sr-only">Carregando...</span>
                        </div>
                        <span class="text-gray-700">Carregando...</span>
                    </div>
                </div>
            `;

            document.body.appendChild(globalLoader);
        }
    }

    injectStyles() {
        if (!document.getElementById('loading-states-styles')) {
            const style = document.createElement('style');
            style.id = 'loading-states-styles';
            style.textContent = `
                .loading-state {
                    pointer-events: none;
                    opacity: 0.8;
                }

                .loading-overlay {
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    backdrop-filter: blur(2px);
                }

                .form-loading-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 100;
                    backdrop-filter: blur(2px);
                }

                .loading-spinner {
                    text-align: center;
                }

                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                .spinner-border {
                    display: inline-block;
                    width: 2rem;
                    height: 2rem;
                    vertical-align: text-bottom;
                    border: 0.25em solid currentColor;
                    border-right-color: transparent;
                    border-radius: 50%;
                    animation: spinner-border 0.75s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                @keyframes spinner-border {
                    to { transform: rotate(360deg); }
                }

                .loading-text {
                    color: #666;
                    font-size: 14px;
                    margin-top: 10px;
                }

                /* Skeleton loading animation */
                .skeleton {
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                }

                @keyframes skeleton-loading {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }

                /* Pulse animation */
                .pulse {
                    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    generateLoadingId() {
        return 'loading_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Public API methods
    showLoading(elementOrId, options = {}) {
        const element = typeof elementOrId === 'string' ? 
            document.getElementById(elementOrId) : elementOrId;
        
        if (!element) return null;

        const type = options.type || 'element';
        
        switch (type) {
            case 'button':
                return this.showLoadingForButton(element);
            case 'form':
                return this.showLoadingForForm(element);
            case 'link':
                return this.showLoadingForLink(element);
            default:
                return this.showLoadingForElement(element);
        }
    }

    hideLoadingById(loadingId) {
        this.hideLoading(loadingId);
    }

    createSkeleton(element, lines = 3) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-container';
        
        for (let i = 0; i < lines; i++) {
            const line = document.createElement('div');
            line.className = 'skeleton h-4 bg-gray-300 rounded mb-2';
            line.style.width = `${Math.random() * 40 + 60}%`;
            skeleton.appendChild(line);
        }

        element.appendChild(skeleton);
        return skeleton;
    }

    removeSkeleton(element) {
        const skeleton = element.querySelector('.skeleton-container');
        if (skeleton) {
            skeleton.remove();
        }
    }
}

// Initialize the loading state manager
document.addEventListener('DOMContentLoaded', () => {
    window.loadingStateManager = new LoadingStateManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingStateManager;
}
