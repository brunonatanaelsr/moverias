/**
 * Sistema de Acessibilidade (ARIA) - Expandido
 * Melhora a navegação por teclado e leitores de tela
 * Implementa WCAG 2.1 AA compliance
 */

class AccessibilityManager {
    constructor() {
        this.focusableElements = [];
        this.currentFocusIndex = -1;
        this.announcements = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.enhanceFormAccessibility();
        this.setupKeyboardNavigation();
        this.injectAccessibilityStyles();
        this.setupScreenReaderSupport();
        this.setupHighContrastMode();
        this.setupReducedMotion();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeAccessibility();
        });

        // HTMX integration
        document.addEventListener('htmx:afterSwap', () => {
            this.initializeAccessibility();
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        // Focus management
        document.addEventListener('focusin', (e) => {
            this.handleFocusIn(e);
        });

        document.addEventListener('focusout', (e) => {
            this.handleFocusOut(e);
        });

        // Screen reader announcements
        document.addEventListener('announce', (e) => {
            this.announce(e.detail.message, e.detail.priority);
        });
    }

    initializeAccessibility() {
        this.enhanceFormAccessibility();
        this.addARIALabels();
        this.setupSkipLinks();
        this.enhanceTableAccessibility();
        this.setupLiveRegions();
        this.setupErrorHandling();
        this.enhanceButtonAccessibility();
        this.setupModalAccessibility();
        this.setupProgressBarAccessibility();
    }

    setupScreenReaderSupport() {
        // Create screen reader only announcements area
        if (!document.getElementById('sr-announcements')) {
            const announceArea = document.createElement('div');
            announceArea.id = 'sr-announcements';
            announceArea.setAttribute('aria-live', 'polite');
            announceArea.setAttribute('aria-atomic', 'true');
            announceArea.className = 'sr-only';
            document.body.appendChild(announceArea);
        }

        // Create urgent announcements area
        if (!document.getElementById('sr-urgent')) {
            const urgentArea = document.createElement('div');
            urgentArea.id = 'sr-urgent';
            urgentArea.setAttribute('aria-live', 'assertive');
            urgentArea.setAttribute('aria-atomic', 'true');
            urgentArea.className = 'sr-only';
            document.body.appendChild(urgentArea);
        }
    }

    setupHighContrastMode() {
        // Detect high contrast mode preference
        const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
        
        if (prefersHighContrast) {
            document.body.classList.add('high-contrast-mode');
        }

        // Add toggle button for high contrast
        const toggleButton = document.createElement('button');
        toggleButton.id = 'high-contrast-toggle';
        toggleButton.className = 'accessibility-toggle';
        toggleButton.innerHTML = '🔳 Alto Contraste';
        toggleButton.setAttribute('aria-label', 'Alternar modo de alto contraste');
        toggleButton.addEventListener('click', this.toggleHighContrast.bind(this));
        
        // Add to accessibility toolbar
        this.addToAccessibilityToolbar(toggleButton);
    }

    setupReducedMotion() {
        // Detect reduced motion preference
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        if (prefersReducedMotion) {
            document.body.classList.add('reduced-motion');
        }

        // Add toggle button for reduced motion
        const toggleButton = document.createElement('button');
        toggleButton.id = 'reduced-motion-toggle';
        toggleButton.className = 'accessibility-toggle';
        toggleButton.innerHTML = '⏸️ Menos Animações';
        toggleButton.setAttribute('aria-label', 'Alternar modo de movimento reduzido');
        toggleButton.addEventListener('click', this.toggleReducedMotion.bind(this));
        
        // Add to accessibility toolbar
        this.addToAccessibilityToolbar(toggleButton);
    }

    addToAccessibilityToolbar(element) {
        let toolbar = document.getElementById('accessibility-toolbar');
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.id = 'accessibility-toolbar';
            toolbar.className = 'accessibility-toolbar';
            toolbar.setAttribute('role', 'toolbar');
            toolbar.setAttribute('aria-label', 'Ferramentas de acessibilidade');
            document.body.appendChild(toolbar);
        }
        toolbar.appendChild(element);
    }

    toggleHighContrast() {
        document.body.classList.toggle('high-contrast-mode');
        const isActive = document.body.classList.contains('high-contrast-mode');
        
        // Store preference
        localStorage.setItem('highContrast', isActive);
        
        // Announce change
        this.announce(isActive ? 'Modo de alto contraste ativado' : 'Modo de alto contraste desativado');
    }

    toggleReducedMotion() {
        document.body.classList.toggle('reduced-motion');
        const isActive = document.body.classList.contains('reduced-motion');
        
        // Store preference
        localStorage.setItem('reducedMotion', isActive);
        
        // Announce change
        this.announce(isActive ? 'Animações reduzidas ativadas' : 'Animações reduzidas desativadas');
    }

    setupErrorHandling() {
        // Enhanced error handling with ARIA
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('invalid', (e) => {
                e.preventDefault();
                this.handleFormErrors(form);
            }, true);
        });
    }

    handleFormErrors(form) {
        const errors = form.querySelectorAll(':invalid');
        if (errors.length > 0) {
            const firstError = errors[0];
            
            // Create error summary if not exists
            this.createErrorSummary(form, errors);
            
            // Focus first error
            firstError.focus();
            
            // Announce error
            this.announce(`Erro no formulário: ${errors.length} campo(s) precisam ser corrigidos`, 'assertive');
        }
    }

    createErrorSummary(form, errors) {
        let summary = form.querySelector('.error-summary');
        if (!summary) {
            summary = document.createElement('div');
            summary.className = 'error-summary';
            summary.setAttribute('role', 'alert');
            summary.setAttribute('aria-live', 'assertive');
            form.insertBefore(summary, form.firstChild);
        }

        const errorList = document.createElement('ul');
        errorList.setAttribute('role', 'list');
        
        errors.forEach((error, index) => {
            const listItem = document.createElement('li');
            listItem.setAttribute('role', 'listitem');
            
            const link = document.createElement('a');
            link.href = `#${error.id}`;
            link.textContent = this.getErrorMessage(error);
            link.addEventListener('click', (e) => {
                e.preventDefault();
                error.focus();
            });
            
            listItem.appendChild(link);
            errorList.appendChild(listItem);
        });

        summary.innerHTML = `
            <h3>Corrija os seguintes erros:</h3>
        `;
        summary.appendChild(errorList);
    }

    getErrorMessage(field) {
        const label = document.querySelector(`label[for="${field.id}"]`);
        const fieldName = label ? label.textContent.trim() : field.name;
        
        if (field.validity.valueMissing) {
            return `${fieldName} é obrigatório`;
        } else if (field.validity.typeMismatch) {
            return `${fieldName} deve ter um formato válido`;
        } else if (field.validity.patternMismatch) {
            return `${fieldName} não está no formato correto`;
        } else if (field.validity.tooShort) {
            return `${fieldName} deve ter pelo menos ${field.minLength} caracteres`;
        } else if (field.validity.tooLong) {
            return `${fieldName} não pode ter mais de ${field.maxLength} caracteres`;
        }
        
        return `${fieldName} contém um erro`;
    }

    enhanceButtonAccessibility() {
        const buttons = document.querySelectorAll('button, [role="button"]');
        buttons.forEach(button => {
            // Ensure buttons have proper ARIA attributes
            if (!button.hasAttribute('aria-label') && !button.textContent.trim()) {
                button.setAttribute('aria-label', 'Botão');
            }
            
            // Add pressed state for toggle buttons
            if (button.hasAttribute('aria-pressed')) {
                button.addEventListener('click', () => {
                    const isPressed = button.getAttribute('aria-pressed') === 'true';
                    button.setAttribute('aria-pressed', !isPressed);
                });
            }
            
            // Add loading state support
            if (button.hasAttribute('data-loading')) {
                button.addEventListener('click', () => {
                    button.setAttribute('aria-busy', 'true');
                    button.setAttribute('aria-disabled', 'true');
                });
            }
        });
    }

    setupModalAccessibility() {
        // Enhanced modal accessibility
        const modals = document.querySelectorAll('[role="dialog"], .modal');
        modals.forEach(modal => {
            this.enhanceModalAccessibility(modal);
        });
    }

    enhanceModalAccessibility(modal) {
        if (!modal.hasAttribute('aria-labelledby')) {
            const title = modal.querySelector('h1, h2, h3, h4, h5, h6, .modal-title');
            if (title) {
                const titleId = title.id || `modal-title-${Date.now()}`;
                title.id = titleId;
                modal.setAttribute('aria-labelledby', titleId);
            }
        }

        if (!modal.hasAttribute('aria-describedby')) {
            const description = modal.querySelector('.modal-body, .modal-description');
            if (description) {
                const descId = description.id || `modal-desc-${Date.now()}`;
                description.id = descId;
                modal.setAttribute('aria-describedby', descId);
            }
        }

        // Focus management
        modal.addEventListener('shown', () => {
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
    }

    setupProgressBarAccessibility() {
        const progressBars = document.querySelectorAll('[role="progressbar"], .progress-bar');
        progressBars.forEach(bar => {
            if (!bar.hasAttribute('aria-valuemin')) {
                bar.setAttribute('aria-valuemin', '0');
            }
            if (!bar.hasAttribute('aria-valuemax')) {
                bar.setAttribute('aria-valuemax', '100');
            }
            if (!bar.hasAttribute('aria-valuenow')) {
                bar.setAttribute('aria-valuenow', '0');
            }
            
            // Add live region for progress updates
            if (!bar.hasAttribute('aria-live')) {
                bar.setAttribute('aria-live', 'polite');
            }
        });
    }

    announce(message, priority = 'polite') {
        const announceArea = priority === 'assertive' ? 
            document.getElementById('sr-urgent') : 
            document.getElementById('sr-announcements');
            
        if (announceArea) {
            announceArea.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                announceArea.textContent = '';
            }, 1000);
        }
    }
        this.enhanceButtonAccessibility();
        this.enhanceModalAccessibility();
        this.enhanceNavigationAccessibility();
        this.enhanceCardAccessibility();
        this.setupAnnouncementSystem();
        this.updateFocusableElements();
    }

    enhanceFormAccessibility() {
        // Enhance form fields
        document.querySelectorAll('input, textarea, select').forEach(field => {
            this.enhanceFormField(field);
        });

        // Enhance form groups
        document.querySelectorAll('.form-group, .field-group').forEach(group => {
            this.enhanceFormGroup(group);
        });

        // Add form validation announcements
        document.querySelectorAll('form').forEach(form => {
            this.enhanceFormValidation(form);
        });
    }

    enhanceFormField(field) {
        // Add ARIA attributes
        if (!field.hasAttribute('aria-describedby')) {
            const describedBy = [];
            
            // Link to help text
            const helpText = field.parentElement.querySelector('.help-text, .form-text');
            if (helpText) {
                if (!helpText.id) {
                    helpText.id = `help-${this.generateId()}`;
                }
                describedBy.push(helpText.id);
            }

            // Link to error messages
            const errorText = field.parentElement.querySelector('.error-text, .invalid-feedback');
            if (errorText) {
                if (!errorText.id) {
                    errorText.id = `error-${this.generateId()}`;
                }
                describedBy.push(errorText.id);
            }

            if (describedBy.length > 0) {
                field.setAttribute('aria-describedby', describedBy.join(' '));
            }
        }

        // Add required indicator
        if (field.required && !field.hasAttribute('aria-required')) {
            field.setAttribute('aria-required', 'true');
        }

        // Add invalid state for validation
        if (field.classList.contains('is-invalid')) {
            field.setAttribute('aria-invalid', 'true');
        }

        // Enhance specific field types
        this.enhanceFieldType(field);
    }

    enhanceFieldType(field) {
        switch (field.type) {
            case 'password':
                this.enhancePasswordField(field);
                break;
            case 'email':
                field.setAttribute('aria-description', 'Digite um endereço de e-mail válido');
                break;
            case 'tel':
                field.setAttribute('aria-description', 'Digite um número de telefone válido');
                break;
            case 'date':
                field.setAttribute('aria-description', 'Use as setas para navegar ou digite no formato DD/MM/AAAA');
                break;
        }

        // Add validation feedback
        if (field.hasAttribute('data-validate')) {
            this.addValidationFeedback(field);
        }
    }

    enhancePasswordField(field) {
        // Add password visibility toggle
        const wrapper = field.parentElement;
        if (!wrapper.querySelector('.password-toggle')) {
            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'password-toggle absolute right-2 top-2 text-gray-500 hover:text-gray-700';
            toggle.innerHTML = '<i class="fas fa-eye"></i>';
            toggle.setAttribute('aria-label', 'Mostrar senha');
            toggle.setAttribute('aria-pressed', 'false');
            
            toggle.addEventListener('click', () => {
                const isVisible = field.type === 'text';
                field.type = isVisible ? 'password' : 'text';
                toggle.innerHTML = isVisible ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
                toggle.setAttribute('aria-label', isVisible ? 'Mostrar senha' : 'Ocultar senha');
                toggle.setAttribute('aria-pressed', isVisible ? 'false' : 'true');
            });

            wrapper.style.position = 'relative';
            wrapper.appendChild(toggle);
        }
    }

    addValidationFeedback(field) {
        // Create live region for validation feedback
        if (!field.parentElement.querySelector('.validation-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.className = 'validation-live-region sr-only';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            field.parentElement.appendChild(liveRegion);
        }

        // Listen for validation events
        field.addEventListener('input', () => {
            this.announceValidation(field);
        });

        field.addEventListener('blur', () => {
            this.announceValidation(field);
        });
    }

    announceValidation(field) {
        const liveRegion = field.parentElement.querySelector('.validation-live-region');
        if (!liveRegion) return;

        const isValid = field.checkValidity();
        const validationMessage = field.validationMessage;

        if (!isValid && validationMessage) {
            liveRegion.textContent = `Erro: ${validationMessage}`;
        } else if (isValid && field.value) {
            liveRegion.textContent = 'Campo válido';
        } else {
            liveRegion.textContent = '';
        }
    }

    enhanceFormGroup(group) {
        const label = group.querySelector('label');
        const field = group.querySelector('input, textarea, select');
        
        if (label && field) {
            // Ensure proper association
            if (!label.hasAttribute('for') && !field.hasAttribute('aria-labelledby')) {
                if (!field.id) {
                    field.id = `field-${this.generateId()}`;
                }
                label.setAttribute('for', field.id);
            }

            // Add required indicator to label
            if (field.required && !label.querySelector('.required-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'required-indicator text-red-500 ml-1';
                indicator.innerHTML = '*';
                indicator.setAttribute('aria-label', 'obrigatório');
                label.appendChild(indicator);
            }
        }
    }

    enhanceFormValidation(form) {
        // Add form validation announcements
        form.addEventListener('submit', (e) => {
            const errors = form.querySelectorAll('.is-invalid, [aria-invalid="true"]');
            if (errors.length > 0) {
                this.announceFormErrors(errors);
                e.preventDefault();
            }
        });

        // Add form-level error summary
        this.addErrorSummary(form);
    }

    addErrorSummary(form) {
        if (!form.querySelector('.error-summary')) {
            const summary = document.createElement('div');
            summary.className = 'error-summary hidden p-4 mb-4 bg-red-50 border border-red-200 rounded';
            summary.setAttribute('role', 'alert');
            summary.setAttribute('aria-live', 'assertive');
            
            summary.innerHTML = `
                <h3 class="text-red-800 font-semibold mb-2">Corrija os seguintes erros:</h3>
                <ul class="error-list text-red-700 list-disc list-inside"></ul>
            `;

            form.insertBefore(summary, form.firstChild);
        }
    }

    announceFormErrors(errors) {
        const form = errors[0].closest('form');
        const summary = form.querySelector('.error-summary');
        const errorList = summary.querySelector('.error-list');
        
        if (!summary || !errorList) return;

        // Clear existing errors
        errorList.innerHTML = '';

        // Add current errors
        errors.forEach(field => {
            const label = form.querySelector(`label[for="${field.id}"]`);
            const fieldName = label ? label.textContent.replace('*', '').trim() : field.name;
            const message = field.validationMessage || 'Campo inválido';
            
            const listItem = document.createElement('li');
            listItem.innerHTML = `<a href="#${field.id}" class="text-red-600 hover:text-red-800">${fieldName}: ${message}</a>`;
            errorList.appendChild(listItem);
        });

        // Show summary
        summary.classList.remove('hidden');
        summary.focus();
    }

    addARIALabels() {
        // Add ARIA labels to buttons without text
        document.querySelectorAll('button:not([aria-label])').forEach(button => {
            if (!button.textContent.trim()) {
                const icon = button.querySelector('i');
                if (icon) {
                    const ariaLabel = this.getIconLabel(icon.className);
                    if (ariaLabel) {
                        button.setAttribute('aria-label', ariaLabel);
                    }
                }
            }
        });

        // Add ARIA labels to links
        document.querySelectorAll('a:not([aria-label])').forEach(link => {
            if (!link.textContent.trim()) {
                const icon = link.querySelector('i');
                if (icon) {
                    const ariaLabel = this.getIconLabel(icon.className);
                    if (ariaLabel) {
                        link.setAttribute('aria-label', ariaLabel);
                    }
                }
            }
        });

        // Add ARIA labels to form controls
        document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(input => {
            if (!input.labels.length && !input.hasAttribute('aria-label')) {
                const label = input.parentElement.textContent.trim();
                if (label) {
                    input.setAttribute('aria-label', label);
                }
            }
        });
    }

    getIconLabel(className) {
        const iconMap = {
            'fa-edit': 'Editar',
            'fa-pencil': 'Editar',
            'fa-trash': 'Excluir',
            'fa-delete': 'Excluir',
            'fa-plus': 'Adicionar',
            'fa-minus': 'Remover',
            'fa-search': 'Pesquisar',
            'fa-eye': 'Visualizar',
            'fa-download': 'Baixar',
            'fa-upload': 'Enviar',
            'fa-save': 'Salvar',
            'fa-print': 'Imprimir',
            'fa-share': 'Compartilhar',
            'fa-close': 'Fechar',
            'fa-times': 'Fechar',
            'fa-check': 'Confirmar',
            'fa-arrow-left': 'Voltar',
            'fa-arrow-right': 'Avançar',
            'fa-home': 'Início',
            'fa-user': 'Usuário',
            'fa-settings': 'Configurações',
            'fa-cog': 'Configurações'
        };

        for (const [iconClass, label] of Object.entries(iconMap)) {
            if (className.includes(iconClass)) {
                return label;
            }
        }

        return null;
    }

    setupSkipLinks() {
        // Add skip to main content link
        if (!document.querySelector('#skip-to-main')) {
            const skipLink = document.createElement('a');
            skipLink.id = 'skip-to-main';
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link';
            skipLink.textContent = 'Pular para o conteúdo principal';
            
            document.body.insertBefore(skipLink, document.body.firstChild);
        }

        // Ensure main content area exists
        let mainContent = document.querySelector('#main-content');
        if (!mainContent) {
            mainContent = document.querySelector('main') || document.querySelector('.main-content');
            if (mainContent) {
                mainContent.id = 'main-content';
            }
        }

        // Add tabindex for focus
        if (mainContent) {
            mainContent.setAttribute('tabindex', '-1');
        }
    }

    enhanceTableAccessibility() {
        document.querySelectorAll('table').forEach(table => {
            // Add table caption if missing
            if (!table.querySelector('caption')) {
                const caption = document.createElement('caption');
                caption.className = 'sr-only';
                caption.textContent = 'Tabela de dados';
                table.insertBefore(caption, table.firstChild);
            }

            // Add scope to headers
            table.querySelectorAll('th').forEach(th => {
                if (!th.hasAttribute('scope')) {
                    const isRowHeader = th.parentElement.querySelector('th:first-child') === th;
                    th.setAttribute('scope', isRowHeader ? 'row' : 'col');
                }
            });

            // Add table role if needed
            if (!table.hasAttribute('role')) {
                table.setAttribute('role', 'table');
            }
        });
    }

    setupLiveRegions() {
        // Create global live regions for announcements
        if (!document.querySelector('#aria-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'aria-live-region';
            liveRegion.className = 'sr-only';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            document.body.appendChild(liveRegion);
        }

        if (!document.querySelector('#aria-alert-region')) {
            const alertRegion = document.createElement('div');
            alertRegion.id = 'aria-alert-region';
            alertRegion.className = 'sr-only';
            alertRegion.setAttribute('role', 'alert');
            alertRegion.setAttribute('aria-live', 'assertive');
            document.body.appendChild(alertRegion);
        }
    }

    handleKeyboardNavigation(event) {
        // Handle Tab navigation
        if (event.key === 'Tab') {
            this.handleTabNavigation(event);
        }

        // Handle Escape key
        if (event.key === 'Escape') {
            this.handleEscapeKey(event);
        }

        // Handle Enter key for buttons
        if (event.key === 'Enter' && event.target.tagName === 'BUTTON') {
            event.target.click();
        }

        // Handle arrow keys in form groups
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
            this.handleArrowKeys(event);
        }
    }

    handleTabNavigation(event) {
        // Update focusable elements
        this.updateFocusableElements();

        // Handle modal/dialog focus trapping
        const modal = document.querySelector('.modal:not(.hidden)');
        if (modal) {
            this.trapFocus(event, modal);
        }
    }

    handleEscapeKey(event) {
        // Close modals
        const modal = document.querySelector('.modal:not(.hidden)');
        if (modal) {
            const closeButton = modal.querySelector('.modal-close, [data-dismiss="modal"]');
            if (closeButton) {
                closeButton.click();
            }
        }

        // Close dropdowns
        const dropdown = document.querySelector('.dropdown.show');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }

    handleArrowKeys(event) {
        // Handle radio group navigation
        if (event.target.type === 'radio') {
            this.handleRadioGroupNavigation(event);
        }

        // Handle menu navigation
        if (event.target.closest('.menu, .dropdown-menu')) {
            this.handleMenuNavigation(event);
        }
    }

    handleRadioGroupNavigation(event) {
        const radioGroup = event.target.closest('fieldset') || 
                          document.querySelectorAll(`input[name="${event.target.name}"]`);
        
        if (radioGroup) {
            const radios = Array.from(radioGroup.querySelectorAll ? 
                radioGroup.querySelectorAll('input[type="radio"]') : radioGroup);
            
            const currentIndex = radios.indexOf(event.target);
            let nextIndex;

            if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
                nextIndex = currentIndex > 0 ? currentIndex - 1 : radios.length - 1;
            } else {
                nextIndex = currentIndex < radios.length - 1 ? currentIndex + 1 : 0;
            }

            radios[nextIndex].focus();
            radios[nextIndex].checked = true;
            event.preventDefault();
        }
    }

    updateFocusableElements() {
        const focusableSelector = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
        this.focusableElements = Array.from(document.querySelectorAll(focusableSelector));
    }

    trapFocus(event, container) {
        const focusableElements = container.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
            if (document.activeElement === firstFocusable) {
                lastFocusable.focus();
                event.preventDefault();
            }
        } else {
            if (document.activeElement === lastFocusable) {
                firstFocusable.focus();
                event.preventDefault();
            }
        }
    }

    handleFocusIn(event) {
        // Add visual focus indicator
        event.target.classList.add('focus-visible');
        
        // Update current focus index
        this.currentFocusIndex = this.focusableElements.indexOf(event.target);
    }

    handleFocusOut(event) {
        // Remove visual focus indicator
        event.target.classList.remove('focus-visible');
    }

    injectAccessibilityStyles() {
        if (!document.getElementById('accessibility-styles')) {
            const style = document.createElement('style');
            style.id = 'accessibility-styles';
            style.textContent = `
                /* Screen reader only content */
                .sr-only {
                    position: absolute !important;
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    margin: -1px !important;
                    overflow: hidden !important;
                    clip: rect(0, 0, 0, 0) !important;
                    white-space: nowrap !important;
                    border: 0 !important;
                }

                .sr-only-focusable:focus {
                    position: static !important;
                    width: auto !important;
                    height: auto !important;
                    padding: 0.5rem !important;
                    margin: 0 !important;
                    overflow: visible !important;
                    clip: auto !important;
                    white-space: normal !important;
                    background-color: #000 !important;
                    color: #fff !important;
                    z-index: 9999 !important;
                }

                /* Skip link */
                .skip-link {
                    position: absolute;
                    top: -40px;
                    left: 6px;
                    background: #000;
                    color: #fff;
                    padding: 8px 16px;
                    text-decoration: none;
                    z-index: 100000;
                    border-radius: 4px;
                    font-weight: bold;
                    transition: top 0.3s;
                }

                .skip-link:focus {
                    top: 6px;
                }

                /* Focus indicators */
                *:focus {
                    outline: 2px solid #4F46E5 !important;
                    outline-offset: 2px !important;
                }

                .focus-visible {
                    outline: 2px solid #007cba;
                    outline-offset: 2px;
                }

                /* Error summary */
                .error-summary {
                    border: 2px solid #EF4444;
                    background-color: #FEF2F2;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border-radius: 4px;
                }

                .error-summary h3 {
                    color: #DC2626;
                    margin: 0 0 0.5rem 0;
                    font-size: 1.1rem;
                }

                .error-summary ul {
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }

                .error-summary li {
                    margin: 0.25rem 0;
                }

                .error-summary a {
                    color: #DC2626;
                    text-decoration: underline;
                }

                .error-summary a:hover,
                .error-summary a:focus {
                    text-decoration: none;
                }

                /* High contrast mode */
                .high-contrast-mode {
                    filter: contrast(200%) brightness(150%);
                }

                .high-contrast-mode * {
                    text-shadow: none !important;
                    box-shadow: none !important;
                }

                .high-contrast-mode button,
                .high-contrast-mode .btn {
                    border: 2px solid #000 !important;
                    background: #fff !important;
                    color: #000 !important;
                }

                .high-contrast-mode button:hover,
                .high-contrast-mode .btn:hover {
                    background: #000 !important;
                    color: #fff !important;
                }

                .high-contrast-mode input,
                .high-contrast-mode select,
                .high-contrast-mode textarea {
                    border: 2px solid #000 !important;
                    background: #fff !important;
                    color: #000 !important;
                }

                /* Reduced motion */
                .reduced-motion *,
                .reduced-motion *::before,
                .reduced-motion *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                    scroll-behavior: auto !important;
                }

                /* Accessibility toolbar */
                .accessibility-toolbar {
                    position: fixed;
                    top: 0;
                    right: 0;
                    background: #1F2937;
                    color: #fff;
                    padding: 0.5rem;
                    display: flex;
                    gap: 0.5rem;
                    z-index: 10000;
                    border-radius: 0 0 0 8px;
                }

                .accessibility-toggle {
                    background: transparent;
                    border: 1px solid #fff;
                    color: #fff;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.875rem;
                    transition: all 0.2s;
                }

                .accessibility-toggle:hover,
                .accessibility-toggle:focus {
                    background: #fff;
                    color: #1F2937;
                }

                /* Form validation states */
                .form-field-valid {
                    border-color: #10B981 !important;
                    background-color: #F0FDF4 !important;
                }

                .form-field-invalid {
                    border-color: #EF4444 !important;
                    background-color: #FEF2F2 !important;
                }

                .validation-message {
                    font-size: 0.875rem;
                    margin-top: 0.25rem;
                    padding: 0.25rem;
                    border-radius: 4px;
                }

                .validation-message.valid {
                    color: #059669;
                    background-color: #D1FAE5;
                }

                .validation-message.invalid {
                    color: #DC2626;
                    background-color: #FEE2E2;
                }

                /* Progress bar accessibility */
                .progress-bar-container {
                    position: relative;
                }

                .progress-bar-label {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 0.25rem;
                    font-size: 0.875rem;
                }

                .progress-bar {
                    background-color: #E5E7EB;
                    border-radius: 9999px;
                    height: 0.5rem;
                    overflow: hidden;
                    position: relative;
                }

                .progress-bar-fill {
                    background-color: #4F46E5;
                    height: 100%;
                    transition: width 0.3s ease;
                    position: relative;
                }

                /* Loading states */
                .loading-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }

                .loading-spinner {
                    width: 2rem;
                    height: 2rem;
                    border: 2px solid #E5E7EB;
                    border-top: 2px solid #4F46E5;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                /* Touch targets */
                button,
                .btn,
                a,
                input[type="button"],
                input[type="submit"],
                input[type="reset"] {
                    min-height: 44px;
                    min-width: 44px;
                    padding: 0.5rem 1rem;
                }

                /* High contrast mode support */
                @media (prefers-contrast: high) {
                    .focus-visible {
                        outline: 3px solid;
                        outline-offset: 3px;
                    }
                }

                /* Reduced motion support */
                @media (prefers-reduced-motion: reduce) {
                    *, ::before, ::after {
                        animation-delay: -1ms !important;
                        animation-duration: 1ms !important;
                        animation-iteration-count: 1 !important;
                        background-attachment: initial !important;
                        scroll-behavior: auto !important;
                        transition-duration: 0s !important;
                        transition-delay: 0s !important;
                    }
                }

                /* Required field indicators */
                .required-indicator {
                    color: #dc3545;
                    font-weight: bold;
                }

                /* Password toggle */
                .password-toggle {
                    background: none;
                    border: none;
                    cursor: pointer;
                    z-index: 10;
                }

                .password-toggle:focus {
                    outline: 2px solid #007cba;
                    outline-offset: 2px;
                }

                /* Print styles */
                @media print {
                    .accessibility-toolbar,
                    .skip-link {
                        display: none !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }

    // Public API methods
    announce(message, priority = 'polite') {
        const region = priority === 'assertive' ? 
            document.querySelector('#aria-alert-region') : 
            document.querySelector('#aria-live-region');
        
        if (region) {
            region.textContent = message;
            
            // Clear after a delay to allow re-announcement
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }

    focusElement(elementOrSelector) {
        const element = typeof elementOrSelector === 'string' ? 
            document.querySelector(elementOrSelector) : elementOrSelector;
        
        if (element) {
            element.focus();
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    addLiveRegion(element, priority = 'polite') {
        element.setAttribute('aria-live', priority);
        element.setAttribute('aria-atomic', 'true');
    }
}

// Initialize the accessibility manager
document.addEventListener('DOMContentLoaded', () => {
    window.accessibilityManager = new AccessibilityManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityManager;
}
