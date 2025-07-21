/**
 * Alpine.js Setup and Configuration
 * MoveMarias - Modern JavaScript Framework Setup
 */

// Alpine.js global configuration
document.addEventListener('alpine:init', () => {
    // Global Alpine data
    Alpine.data('globalState', () => ({
        // Dark mode state
        darkMode: localStorage.getItem('darkMode') === 'true',
        
        // Mobile menu state
        mobileMenuOpen: false,
        
        // Loading state
        loading: false,
        
        // Toast notifications
        toasts: [],
        
        // Form states
        formData: {},
        formErrors: {},
        
        // Toggle dark mode
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);
            
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },
        
        // Show toast notification
        showToast(message, type = 'info', duration = 5000) {
            const id = Date.now();
            const toast = {
                id,
                message,
                type,
                visible: true
            };
            
            this.toasts.push(toast);
            
            // Auto-hide toast
            setTimeout(() => {
                this.hideToast(id);
            }, duration);
        },
        
        // Hide toast notification
        hideToast(id) {
            const index = this.toasts.findIndex(toast => toast.id === id);
            if (index > -1) {
                this.toasts[index].visible = false;
                
                // Remove from array after animation
                setTimeout(() => {
                    this.toasts.splice(index, 1);
                }, 300);
            }
        },
        
        // Set loading state
        setLoading(state) {
            this.loading = state;
        },
        
        // Handle form submission
        submitForm(formElement, options = {}) {
            this.setLoading(true);
            this.formErrors = {};
            
            const formData = new FormData(formElement);
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken.value);
            }
            
            fetch(formElement.action || window.location.href, {
                method: formElement.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showToast(data.message || 'Operação realizada com sucesso!', 'success');
                    
                    // Redirect if specified
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    }
                    
                    // Reset form if specified
                    if (options.resetOnSuccess) {
                        formElement.reset();
                    }
                } else {
                    // Handle form errors
                    if (data.errors) {
                        this.formErrors = data.errors;
                    }
                    
                    this.showToast(data.message || 'Erro ao processar formulário', 'error');
                }
            })
            .catch(error => {
                console.error('Form submission error:', error);
                this.showToast('Erro interno do servidor', 'error');
            })
            .finally(() => {
                this.setLoading(false);
            });
        }
    }));
    
    // Sidebar component
    Alpine.data('sidebar', () => ({
        open: false,
        
        toggle() {
            this.open = !this.open;
        },
        
        close() {
            this.open = false;
        }
    }));
    
    // Modal component
    Alpine.data('modal', (initialState = false) => ({
        open: initialState,
        
        show() {
            this.open = true;
            document.body.classList.add('overflow-hidden');
        },
        
        hide() {
            this.open = false;
            document.body.classList.remove('overflow-hidden');
        },
        
        toggle() {
            if (this.open) {
                this.hide();
            } else {
                this.show();
            }
        }
    }));
    
    // Dropdown component
    Alpine.data('dropdown', () => ({
        open: false,
        
        toggle() {
            this.open = !this.open;
        },
        
        close() {
            this.open = false;
        }
    }));
    
    // Tabs component
    Alpine.data('tabs', (defaultTab = 0) => ({
        activeTab: defaultTab,
        
        setActiveTab(index) {
            this.activeTab = index;
        },
        
        isActive(index) {
            return this.activeTab === index;
        }
    }));
    
    // Form validation
    Alpine.data('formValidation', () => ({
        errors: {},
        touched: {},
        
        validate(fieldName, value, rules) {
            const fieldErrors = [];
            
            if (rules.required && (!value || value.trim() === '')) {
                fieldErrors.push('Este campo é obrigatório');
            }
            
            if (rules.email && value && !this.isValidEmail(value)) {
                fieldErrors.push('Email inválido');
            }
            
            if (rules.minLength && value && value.length < rules.minLength) {
                fieldErrors.push(`Mínimo de ${rules.minLength} caracteres`);
            }
            
            if (rules.maxLength && value && value.length > rules.maxLength) {
                fieldErrors.push(`Máximo de ${rules.maxLength} caracteres`);
            }
            
            if (rules.pattern && value && !new RegExp(rules.pattern).test(value)) {
                fieldErrors.push('Formato inválido');
            }
            
            this.errors[fieldName] = fieldErrors;
            this.touched[fieldName] = true;
            
            return fieldErrors.length === 0;
        },
        
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        hasError(fieldName) {
            return this.errors[fieldName] && this.errors[fieldName].length > 0;
        },
        
        getErrors(fieldName) {
            return this.errors[fieldName] || [];
        },
        
        isValid() {
            return Object.values(this.errors).every(errors => errors.length === 0);
        }
    }));
});

// Initialize Alpine.js
document.addEventListener('DOMContentLoaded', () => {
    // Apply dark mode on load
    if (localStorage.getItem('darkMode') === 'true') {
        document.documentElement.classList.add('dark');
    }
    
    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.mm-alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.mm-alert-dismiss');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'mm-tooltip';
            tooltip.textContent = e.target.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
        });
        
        element.addEventListener('mouseleave', () => {
            document.querySelectorAll('.mm-tooltip').forEach(tooltip => {
                tooltip.remove();
            });
        });
    });
    
    console.log('Alpine.js setup complete');
});
