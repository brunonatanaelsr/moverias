/**
 * Funcionalidades JavaScript para o sistema de notificações
 */

// Classe para gerenciar notificações
class NotificationManager {
    constructor() {
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        this.init();
    }
    
    init() {
        // Inicializar funcionalidades
        this.bindEvents();
        this.startPeriodicUpdate();
    }
    
    bindEvents() {
        // Eventos para marcar como lida
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="mark-read"]')) {
                e.preventDefault();
                const notificationId = e.target.dataset.notificationId;
                this.markAsRead(notificationId);
            }
        });
        
        // Eventos para marcar como importante
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="mark-important"]')) {
                e.preventDefault();
                const notificationId = e.target.dataset.notificationId;
                this.toggleImportant(notificationId);
            }
        });
        
        // Eventos para exclusão
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="delete"]')) {
                e.preventDefault();
                const notificationId = e.target.dataset.notificationId;
                this.deleteNotification(notificationId);
            }
        });
        
        // Eventos para ações em massa
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="bulk-mark-read"]')) {
                e.preventDefault();
                this.bulkMarkAsRead();
            }
            
            if (e.target.matches('[data-action="bulk-delete"]')) {
                e.preventDefault();
                this.bulkDelete();
            }
        });
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/notifications/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Atualizar interface
                this.updateNotificationStatus(notificationId, 'read');
                this.showMessage('Notificação marcada como lida', 'success');
                this.updateCounter();
            } else {
                this.showMessage(data.error || 'Erro ao marcar como lida', 'error');
            }
        } catch (error) {
            this.showMessage('Erro de conexão', 'error');
        }
    }
    
    async toggleImportant(notificationId) {
        try {
            const response = await fetch(`/notifications/mark-important/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Atualizar interface
                this.updateImportantStatus(notificationId, data.is_important);
                this.showMessage(data.message, 'success');
            } else {
                this.showMessage(data.error || 'Erro ao alterar status', 'error');
            }
        } catch (error) {
            this.showMessage('Erro de conexão', 'error');
        }
    }
    
    async deleteNotification(notificationId) {
        if (!confirm('Tem certeza que deseja excluir esta notificação?')) {
            return;
        }
        
        try {
            const response = await fetch(`/notifications/${notificationId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remover da interface
                this.removeNotificationFromList(notificationId);
                this.showMessage(data.message || 'Notificação excluída', 'success');
                this.updateCounter();
            } else {
                this.showMessage(data.error || 'Erro ao excluir', 'error');
            }
        } catch (error) {
            this.showMessage('Erro de conexão', 'error');
        }
    }
    
    async bulkMarkAsRead() {
        const selected = this.getSelectedNotifications();
        if (selected.length === 0) {
            this.showMessage('Selecione pelo menos uma notificação', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/notifications/bulk-mark-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'notification_ids': selected
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Atualizar interface
                selected.forEach(id => this.updateNotificationStatus(id, 'read'));
                this.showMessage(data.message, 'success');
                this.updateCounter();
            } else {
                this.showMessage(data.error || 'Erro ao marcar como lidas', 'error');
            }
        } catch (error) {
            this.showMessage('Erro de conexão', 'error');
        }
    }
    
    async bulkDelete() {
        const selected = this.getSelectedNotifications();
        if (selected.length === 0) {
            this.showMessage('Selecione pelo menos uma notificação', 'warning');
            return;
        }
        
        if (!confirm(`Tem certeza que deseja excluir ${selected.length} notificações?`)) {
            return;
        }
        
        try {
            const response = await fetch('/notifications/bulk-delete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'notification_ids': selected
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remover da interface
                selected.forEach(id => this.removeNotificationFromList(id));
                this.showMessage(data.message, 'success');
                this.updateCounter();
            } else {
                this.showMessage(data.error || 'Erro ao excluir', 'error');
            }
        } catch (error) {
            this.showMessage('Erro de conexão', 'error');
        }
    }
    
    getSelectedNotifications() {
        const checkboxes = document.querySelectorAll('input[name="notification_ids"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    updateNotificationStatus(notificationId, status) {
        const card = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (card) {
            if (status === 'read') {
                card.classList.remove('border-primary');
                const badge = card.querySelector('.badge');
                if (badge) badge.remove();
            }
        }
    }
    
    updateImportantStatus(notificationId, isImportant) {
        const card = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (card) {
            const star = card.querySelector('.notification-star');
            if (star) {
                star.classList.toggle('text-warning', isImportant);
                star.classList.toggle('text-muted', !isImportant);
            }
        }
    }
    
    removeNotificationFromList(notificationId) {
        const card = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (card) {
            card.remove();
        }
    }
    
    async updateCounter() {
        try {
            const response = await fetch('/notifications/count/');
            const data = await response.json();
            
            const counter = document.getElementById('notificationCount');
            if (counter) {
                if (data.count > 0) {
                    counter.textContent = data.count;
                    counter.style.display = 'block';
                } else {
                    counter.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar contador:', error);
        }
    }
    
    startPeriodicUpdate() {
        // Atualizar contador a cada 30 segundos
        setInterval(() => {
            this.updateCounter();
        }, 30000);
    }
    
    showMessage(message, type = 'info') {
        // Criar toast ou alerta
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type];
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Remover após 5 segundos
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new NotificationManager();
});

// Funções globais para compatibilidade
window.markAsRead = function(notificationId) {
    window.notificationManager = window.notificationManager || new NotificationManager();
    window.notificationManager.markAsRead(notificationId);
};

window.toggleImportant = function(notificationId) {
    window.notificationManager = window.notificationManager || new NotificationManager();
    window.notificationManager.toggleImportant(notificationId);
};

window.deleteNotification = function(notificationId) {
    window.notificationManager = window.notificationManager || new NotificationManager();
    window.notificationManager.deleteNotification(notificationId);
};

window.markAllAsRead = function() {
    window.notificationManager = window.notificationManager || new NotificationManager();
    window.notificationManager.bulkMarkAsRead();
};
