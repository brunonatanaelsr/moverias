/**
 * Sistema de Notificações em Tempo Real
 * Gerencia conexão SSE e exibição de notificações
 */

class RealTimeNotifications {
    constructor() {
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1 segundo
        this.notificationCount = 0;
        this.notifications = [];
        
        this.init();
    }
    
    init() {
        this.setupEventSource();
        this.setupNotificationUI();
        this.bindEvents();
        this.loadInitialCount();
    }
    
    setupEventSource() {
        if (typeof(EventSource) === "undefined") {
            console.warn('Server-Sent Events não suportado neste navegador');
            this.fallbackToPolling();
            return;
        }
        
        const streamUrl = '/notifications/stream/';
        this.eventSource = new EventSource(streamUrl);
        
        this.eventSource.onopen = (event) => {
            console.log('Conexão SSE estabelecida');
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };
        
        this.eventSource.onmessage = (event) => {
            console.log('Mensagem SSE recebida:', event.data);
        };
        
        this.eventSource.onerror = (event) => {
            console.error('Erro na conexão SSE:', event);
            this.updateConnectionStatus(false);
            this.handleReconnect();
        };
        
        // Event listeners específicos
        this.eventSource.addEventListener('connected', (event) => {
            const data = JSON.parse(event.data);
            console.log('Conectado ao stream de notificações:', data);
        });
        
        this.eventSource.addEventListener('notification', (event) => {
            const notification = JSON.parse(event.data);
            this.handleNewNotification(notification);
        });
        
        this.eventSource.addEventListener('heartbeat', (event) => {
            const data = JSON.parse(event.data);
            console.log('Heartbeat:', data.timestamp);
        });
        
        this.eventSource.addEventListener('error', (event) => {
            const error = JSON.parse(event.data);
            console.error('Erro no stream:', error);
            this.showErrorToast(error.message);
        });
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Tentativa de reconexão ${this.reconnectAttempts}/${this.maxReconnectAttempts} em ${delay}ms`);
            
            setTimeout(() => {
                this.eventSource.close();
                this.setupEventSource();
            }, delay);
        } else {
            console.error('Máximo de tentativas de reconexão atingido');
            this.fallbackToPolling();
        }
    }
    
    fallbackToPolling() {
        console.log('Usando polling como fallback');
        this.startPolling();
    }
    
    startPolling() {
        setInterval(() => {
            this.fetchNotificationCount();
        }, 30000); // Poll a cada 30 segundos
    }
    
    setupNotificationUI() {
        // Criar elementos da UI se não existirem
        this.ensureNotificationElements();
        this.updateNotificationDisplay();
    }
    
    ensureNotificationElements() {
        // Badge de contagem
        if (!document.getElementById('notification-badge')) {
            const bellIcon = document.querySelector('.notification-bell');
            if (bellIcon) {
                const badge = document.createElement('span');
                badge.id = 'notification-badge';
                badge.className = 'absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center hidden';
                badge.textContent = '0';
                bellIcon.appendChild(badge);
            }
        }
        
        // Container de notificações
        if (!document.getElementById('notifications-container')) {
            const dropdown = document.getElementById('notification-dropdown');
            if (dropdown) {
                const container = document.createElement('div');
                container.id = 'notifications-container';
                container.className = 'max-h-96 overflow-y-auto';
                dropdown.appendChild(container);
            }
        }
        
        // Indicador de conexão
        if (!document.getElementById('connection-status')) {
            const statusBar = document.createElement('div');
            statusBar.id = 'connection-status';
            statusBar.className = 'fixed top-0 left-0 right-0 z-50 bg-green-500 text-white text-center py-1 text-sm hidden';
            statusBar.innerHTML = '<i class="fas fa-wifi mr-2"></i>Conectado às notificações em tempo real';
            document.body.appendChild(statusBar);
        }
    }
    
    bindEvents() {
        // Botão de marcar todas como lidas
        const markAllButton = document.getElementById('mark-all-read-btn');
        if (markAllButton) {
            markAllButton.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
        
        // Eventos de clique em notificações
        document.addEventListener('click', (event) => {
            if (event.target.matches('.notification-item') || event.target.closest('.notification-item')) {
                const notificationElement = event.target.closest('.notification-item');
                const notificationId = notificationElement.dataset.notificationId;
                if (notificationId) {
                    this.markAsRead(notificationId);
                }
            }
        });
        
        // Auto-refresh ao focar na janela
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.fetchNotificationCount();
            }
        });
    }
    
    handleNewNotification(notification) {
        console.log('Nova notificação recebida:', notification);
        
        // Adicionar à lista
        this.notifications.unshift(notification);
        this.notificationCount++;
        
        // Atualizar UI
        this.updateNotificationDisplay();
        this.addNotificationToList(notification);
        
        // Mostrar toast
        this.showNotificationToast(notification);
        
        // Tocar som (se permitido)
        this.playNotificationSound();
        
        // Mostrar notificação do navegador (se permitido)
        this.showBrowserNotification(notification);
    }
    
    updateNotificationDisplay() {
        const badge = document.getElementById('notification-badge');
        const countElement = document.getElementById('notification-count');
        
        if (badge) {
            if (this.notificationCount > 0) {
                badge.textContent = this.notificationCount > 99 ? '99+' : this.notificationCount;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
        
        if (countElement) {
            countElement.textContent = this.notificationCount;
        }
    }
    
    addNotificationToList(notification) {
        const container = document.getElementById('notifications-container');
        if (!container) return;
        
        const notificationElement = this.createNotificationElement(notification);
        container.insertBefore(notificationElement, container.firstChild);
        
        // Animar entrada
        notificationElement.style.opacity = '0';
        notificationElement.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            notificationElement.style.transition = 'all 0.3s ease';
            notificationElement.style.opacity = '1';
            notificationElement.style.transform = 'translateY(0)';
        }, 10);
        
        // Limitar número de notificações exibidas
        const notifications = container.querySelectorAll('.notification-item');
        if (notifications.length > 10) {
            notifications[notifications.length - 1].remove();
        }
    }
    
    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = 'notification-item px-4 py-3 hover:bg-gray-50 border-b border-gray-100 cursor-pointer transition-colors';
        element.dataset.notificationId = notification.id;
        
        const typeIcons = {
            'info': 'fas fa-info-circle text-blue-500',
            'success': 'fas fa-check-circle text-green-500',
            'warning': 'fas fa-exclamation-triangle text-yellow-500',
            'error': 'fas fa-times-circle text-red-500'
        };
        
        const icon = typeIcons[notification.type] || typeIcons.info;
        const timeAgo = this.formatTimeAgo(new Date(notification.timestamp));
        
        element.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="${icon}"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">
                        ${this.escapeHtml(notification.title)}
                    </p>
                    <p class="text-sm text-gray-500 truncate">
                        ${this.escapeHtml(notification.message)}
                    </p>
                    <p class="text-xs text-gray-400 mt-1">
                        ${timeAgo}
                    </p>
                </div>
                <div class="flex-shrink-0">
                    <span class="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                </div>
            </div>
        `;
        
        return element;
    }
    
    showNotificationToast(notification) {
        if (window.Toast) {
            const type = notification.type === 'error' ? 'error' : 'info';
            window.Toast[type](notification.title, notification.message);
        } else {
            // Fallback para alert
            console.log(`Nova notificação: ${notification.title} - ${notification.message}`);
        }
    }
    
    playNotificationSound() {
        try {
            // Criar ou usar elemento de áudio
            let audio = document.getElementById('notification-sound');
            if (!audio) {
                audio = document.createElement('audio');
                audio.id = 'notification-sound';
                audio.preload = 'auto';
                document.body.appendChild(audio);
            }
            
            // Usar som padrão do sistema ou arquivo de áudio
            audio.src = '/static/sounds/notification.mp3'; // Adicionar arquivo de som
            audio.volume = 0.3;
            audio.play().catch(e => {
                console.log('Não foi possível reproduzir som de notificação:', e);
            });
        } catch (e) {
            console.log('Som de notificação não disponível:', e);
        }
    }
    
    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotification = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/logo-notification.png', // Adicionar ícone
                tag: `notification-${notification.id}`,
                requireInteraction: false
            });
            
            browserNotification.onclick = () => {
                window.focus();
                this.markAsRead(notification.id);
                if (notification.url) {
                    window.location.href = notification.url;
                }
                browserNotification.close();
            };
            
            // Fechar automaticamente após 5 segundos
            setTimeout(() => {
                browserNotification.close();
            }, 5000);
        }
    }
    
    markAsRead(notificationId) {
        fetch(`/notifications/api/mark-read/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.removeNotificationFromUI(notificationId);
                this.notificationCount = Math.max(0, this.notificationCount - 1);
                this.updateNotificationDisplay();
            }
        })
        .catch(error => {
            console.error('Erro ao marcar notificação como lida:', error);
        });
    }
    
    markAllAsRead() {
        fetch('/notifications/api/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.clearAllNotifications();
                this.notificationCount = 0;
                this.updateNotificationDisplay();
                
                if (window.Toast) {
                    window.Toast.success('Sucesso', 'Todas as notificações foram marcadas como lidas');
                }
            }
        })
        .catch(error => {
            console.error('Erro ao marcar todas como lidas:', error);
        });
    }
    
    removeNotificationFromUI(notificationId) {
        const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (element) {
            element.style.transition = 'all 0.3s ease';
            element.style.opacity = '0';
            element.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                element.remove();
            }, 300);
        }
    }
    
    clearAllNotifications() {
        const container = document.getElementById('notifications-container');
        if (container) {
            const notifications = container.querySelectorAll('.notification-item');
            notifications.forEach(notification => {
                notification.style.transition = 'all 0.3s ease';
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
            });
            
            setTimeout(() => {
                container.innerHTML = '<div class="px-4 py-8 text-center text-gray-500">Nenhuma notificação</div>';
            }, 300);
        }
    }
    
    fetchNotificationCount() {
        fetch('/notifications/api/count/')
            .then(response => response.json())
            .then(data => {
                this.notificationCount = data.unread_count;
                this.updateNotificationDisplay();
            })
            .catch(error => {
                console.error('Erro ao buscar contagem de notificações:', error);
            });
    }
    
    loadInitialCount() {
        this.fetchNotificationCount();
    }
    
    updateConnectionStatus(connected) {
        const statusBar = document.getElementById('connection-status');
        if (statusBar) {
            if (connected) {
                statusBar.className = 'fixed top-0 left-0 right-0 z-50 bg-green-500 text-white text-center py-1 text-sm';
                statusBar.innerHTML = '<i class="fas fa-wifi mr-2"></i>Conectado às notificações em tempo real';
                
                // Ocultar após 3 segundos
                setTimeout(() => {
                    statusBar.classList.add('hidden');
                }, 3000);
            } else {
                statusBar.className = 'fixed top-0 left-0 right-0 z-50 bg-red-500 text-white text-center py-1 text-sm';
                statusBar.innerHTML = '<i class="fas fa-wifi mr-2"></i>Reconectando às notificações...';
                statusBar.classList.remove('hidden');
            }
        }
    }
    
    // Utility methods
    getCSRFToken() {
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        return cookie ? cookie[1] : '';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Agora mesmo';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} min atrás`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h atrás`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d atrás`;
        }
    }
    
    // Public methods
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Permissão para notificações concedida');
                } else {
                    console.log('Permissão para notificações negada');
                }
            });
        }
    }
    
    destroy() {
        if (this.eventSource) {
            this.eventSource.close();
        }
    }
}

// Inicializar sistema de notificações quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se o usuário está autenticado
    if (document.body.dataset.userAuthenticated === 'true') {
        window.realTimeNotifications = new RealTimeNotifications();
        
        // Solicitar permissão para notificações do navegador
        setTimeout(() => {
            window.realTimeNotifications.requestNotificationPermission();
        }, 2000);
    }
});

// Limpar ao sair da página
window.addEventListener('beforeunload', function() {
    if (window.realTimeNotifications) {
        window.realTimeNotifications.destroy();
    }
});

// Expor classe globalmente para uso em outros scripts
window.RealTimeNotifications = RealTimeNotifications;
