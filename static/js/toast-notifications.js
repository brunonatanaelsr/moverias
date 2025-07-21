/**
 * Toast Notifications System
 * MoveMarias - Modern notification system
 */

class ToastManager {
    constructor() {
        this.toasts = [];
        this.container = null;
        this.init();
    }
    
    init() {
        // Create toast container
        this.createContainer();
        
        // Listen for Django messages
        this.processDjangoMessages();
        
        // Listen for HTMX events
        this.setupHTMXListeners();
    }
    
    createContainer() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
            document.body.appendChild(this.container);
        }
    }
    
    show(message, type = 'info', duration = 5000, options = {}) {
        const id = Date.now() + Math.random();
        const toast = {
            id,
            message,
            type,
            duration,
            options,
            element: null
        };
        
        // Create toast element
        toast.element = this.createElement(toast);
        
        // Add to container
        this.container.appendChild(toast.element);
        
        // Add to tracking array
        this.toasts.push(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.element.classList.add('mm-toast-show');
        });
        
        // Auto-hide if duration is set
        if (duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }
        
        // Limit number of toasts
        if (this.toasts.length > 5) {
            this.hide(this.toasts[0].id);
        }
        
        return id;
    }
    
    createElement(toast) {
        const element = document.createElement('div');
        element.className = `mm-toast mm-toast-${toast.type} mm-toast-enter`;
        element.setAttribute('data-toast-id', toast.id);
        
        const icon = this.getIcon(toast.type);
        const actions = toast.options.actions || [];
        
        element.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="${icon} ${this.getIconColor(toast.type)}"></i>
                </div>
                <div class="ml-3 flex-1">
                    ${toast.options.title ? `<h4 class="text-sm font-medium">${toast.options.title}</h4>` : ''}
                    <div class="text-sm ${toast.options.title ? 'mt-1' : ''}">
                        ${message}
                    </div>
                    ${actions.length > 0 ? this.createActions(actions) : ''}
                </div>
                <div class="ml-4 flex-shrink-0">
                    <button type="button" class="mm-toast-close" onclick="toastManager.hide(${toast.id})">
                        <span class="sr-only">Fechar</span>
                        <i class="fas fa-times w-4 h-4"></i>
                    </button>
                </div>
            </div>
        `;
        
        return element;
    }
    
    createActions(actions) {
        const actionsHtml = actions.map(action => {
            const onclick = action.onclick || `toastManager.handleAction('${action.id}')`;
            return `<button type="button" class="mm-toast-action" onclick="${onclick}">${action.text}</button>`;
        }).join('');
        
        return `<div class="mt-3 flex space-x-2">${actionsHtml}</div>`;
    }
    
    getIcon(type) {
        switch (type) {
            case 'success': return 'fas fa-check-circle';
            case 'error': return 'fas fa-exclamation-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            case 'info': return 'fas fa-info-circle';
            default: return 'fas fa-info-circle';
        }
    }
    
    getIconColor(type) {
        switch (type) {
            case 'success': return 'text-green-500';
            case 'error': return 'text-red-500';
            case 'warning': return 'text-yellow-500';
            case 'info': return 'text-blue-500';
            default: return 'text-blue-500';
        }
    }
    
    hide(id) {
        const toast = this.toasts.find(t => t.id === id);
        if (!toast) return;
        
        // Add exit animation
        toast.element.classList.add('mm-toast-exit');
        
        // Remove after animation
        setTimeout(() => {
            if (toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            
            // Remove from tracking array
            this.toasts = this.toasts.filter(t => t.id !== id);
        }, 300);
    }
    
    hideAll() {
        this.toasts.forEach(toast => {
            this.hide(toast.id);
        });
    }
    
    processDjangoMessages() {
        // Process Django messages on page load
        const messages = document.querySelectorAll('.django-message');
        messages.forEach(message => {
            const type = message.dataset.type || 'info';
            const text = message.textContent.trim();
            
            if (text) {
                this.show(text, type);
            }
            
            // Remove original message
            message.remove();
        });
    }
    
    setupHTMXListeners() {
        // Listen for HTMX events
        document.addEventListener('htmx:responseError', (e) => {
            this.show('Erro na requisição', 'error');
        });
        
        document.addEventListener('htmx:sendError', (e) => {
            this.show('Erro de conexão', 'error');
        });
        
        document.addEventListener('htmx:afterSwap', (e) => {
            // Process any new Django messages
            this.processDjangoMessages();
        });
    }
    
    handleAction(actionId) {
        // Handle custom toast actions
        const event = new CustomEvent('toastAction', {
            detail: { actionId }
        });
        document.dispatchEvent(event);
    }
    
    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', 4000, options);
    }
    
    error(message, options = {}) {
        return this.show(message, 'error', 6000, options);
    }
    
    warning(message, options = {}) {
        return this.show(message, 'warning', 5000, options);
    }
    
    info(message, options = {}) {
        return this.show(message, 'info', 4000, options);
    }
    
    loading(message, options = {}) {
        return this.show(message, 'info', 0, {
            ...options,
            title: 'Carregando...'
        });
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

// Global functions
window.showToast = (message, type, duration, options) => {
    return toastManager.show(message, type, duration, options);
};

window.hideToast = (id) => {
    toastManager.hide(id);
};

window.hideAllToasts = () => {
    toastManager.hideAll();
};

// Convenience global functions
window.toast = {
    success: (message, options) => toastManager.success(message, options),
    error: (message, options) => toastManager.error(message, options),
    warning: (message, options) => toastManager.warning(message, options),
    info: (message, options) => toastManager.info(message, options),
    loading: (message, options) => toastManager.loading(message, options)
};

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    // Process any existing Django messages
    toastManager.processDjangoMessages();
    
    console.log('Toast notification system initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}
