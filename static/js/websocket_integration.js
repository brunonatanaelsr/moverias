/**
 * WebSocket Integration para Chat em Tempo Real
 * Sistema completo de comunicação WebSocket para o módulo de chat
 */

class ChatWebSocket {
    constructor() {
        this.socket = null;
        this.currentChannelId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.messageQueue = [];
        this.isConnected = false;
        this.eventListeners = new Map();
        
        // Estado do usuário
        this.userId = this.getCurrentUserId();
        this.isTyping = false;
        this.typingTimer = null;
        
        // Callbacks
        this.onMessage = null;
        this.onTyping = null;
        this.onUserStatus = null;
        this.onConnectionChange = null;
        
        this.init();
    }

    init() {
        // Configurar event listeners globais
        this.setupEventListeners();
        
        // Conectar se há canal ativo
        const channelId = this.getActiveChannelId();
        if (channelId) {
            this.connect(channelId);
        }
    }

    setupEventListeners() {
        // Detectar mudanças de canal
        window.addEventListener('channelChanged', (e) => {
            this.switchChannel(e.detail.channelId);
        });
        
        // Detectar desconexão da internet
        window.addEventListener('online', () => {
            if (this.currentChannelId && !this.isConnected) {
                this.connect(this.currentChannelId);
            }
        });
        
        window.addEventListener('offline', () => {
            this.disconnect();
        });
        
        // Cleanup ao sair da página
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }

    /**
     * Conectar ao canal WebSocket
     */
    connect(channelId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.disconnect();
        }

        this.currentChannelId = channelId;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${channelId}/`;
        
        console.log(`🔗 Conectando ao canal ${channelId}...`);
        
        try {
            this.socket = new WebSocket(wsUrl);
            this.setupSocketEvents();
        } catch (error) {
            console.error('❌ Erro ao criar WebSocket:', error);
            this.handleConnectionError();
        }
    }

    setupSocketEvents() {
        this.socket.onopen = (event) => {
            console.log('✅ WebSocket conectado');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Processar fila de mensagens
            this.processMessageQueue();
            
            // Iniciar heartbeat
            this.startHeartbeat();
            
            // Notificar componentes
            this.emit('connected', { channelId: this.currentChannelId });
            this.updateConnectionStatus('connected');
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('❌ Erro ao processar mensagem:', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('🔌 WebSocket desconectado:', event.code, event.reason);
            this.isConnected = false;
            this.stopHeartbeat();
            
            this.emit('disconnected', { 
                channelId: this.currentChannelId,
                code: event.code,
                reason: event.reason
            });
            
            this.updateConnectionStatus('disconnected');
            
            // Tentar reconectar se não foi intencional
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('❌ Erro no WebSocket:', error);
            this.emit('error', { error, channelId: this.currentChannelId });
            this.updateConnectionStatus('error');
        };
    }

    /**
     * Processar mensagens recebidas
     */
    handleMessage(data) {
        const { type } = data;
        
        switch (type) {
            case 'chat_message':
                this.handleChatMessage(data);
                break;
                
            case 'message_update':
                this.handleMessageUpdate(data);
                break;
                
            case 'message_delete':
                this.handleMessageDelete(data);
                break;
                
            case 'typing_start':
                this.handleTypingStart(data);
                break;
                
            case 'typing_stop':
                this.handleTypingStop(data);
                break;
                
            case 'user_joined':
                this.handleUserJoined(data);
                break;
                
            case 'user_left':
                this.handleUserLeft(data);
                break;
                
            case 'user_status_change':
                this.handleUserStatusChange(data);
                break;
                
            case 'channel_update':
                this.handleChannelUpdate(data);
                break;
                
            case 'reaction_add':
            case 'reaction_remove':
                this.handleReactionChange(data);
                break;
                
            case 'heartbeat':
                this.handleHeartbeat(data);
                break;
                
            case 'error':
                this.handleError(data);
                break;
                
            default:
                console.warn('⚠️ Tipo de mensagem desconhecido:', type, data);
        }
    }

    handleChatMessage(data) {
        const { message } = data;
        
        // Adicionar à UI
        if (typeof addMessageToUI === 'function') {
            addMessageToUI(message);
        }
        
        // Notificar listeners
        this.emit('message', message);
        
        // Atualizar sidebar se necessário
        this.updateChannelLastMessage(message);
        
        // Som de notificação (se não for própria mensagem)
        if (message.author.id !== this.userId) {
            this.playNotificationSound();
        }
    }

    handleMessageUpdate(data) {
        const { message_id, content, updated_at } = data;
        
        // Atualizar mensagem na UI
        const messageElement = document.querySelector(`[data-message-id="${message_id}"]`);
        if (messageElement) {
            const textElement = messageElement.querySelector('.message-text');
            if (textElement) {
                textElement.innerHTML = this.escapeHtml(content);
            }
            
            // Adicionar indicador de edição
            const timeElement = messageElement.querySelector('.message-time');
            if (timeElement && !timeElement.querySelector('.edited-indicator')) {
                const editedSpan = document.createElement('span');
                editedSpan.className = 'edited-indicator';
                editedSpan.textContent = ' (editada)';
                editedSpan.style.fontSize = '0.75rem';
                editedSpan.style.color = '#6b7280';
                timeElement.appendChild(editedSpan);
            }
        }
        
        this.emit('messageUpdate', { message_id, content, updated_at });
    }

    handleMessageDelete(data) {
        const { message_id } = data;
        
        // Remover mensagem da UI
        const messageElement = document.querySelector(`[data-message-id="${message_id}"]`);
        if (messageElement) {
            messageElement.remove();
        }
        
        this.emit('messageDelete', { message_id });
    }

    handleTypingStart(data) {
        const { user } = data;
        
        // Não mostrar própria digitação
        if (user.id === this.userId) return;
        
        this.showTypingIndicator(user);
        this.emit('typingStart', user);
    }

    handleTypingStop(data) {
        const { user } = data;
        
        if (user.id === this.userId) return;
        
        this.hideTypingIndicator(user);
        this.emit('typingStop', user);
    }

    handleUserJoined(data) {
        const { user, online_users } = data;
        
        this.updateOnlineUsers(online_users);
        this.showUserNotification(`${user.full_name || user.username} entrou no canal`);
        this.emit('userJoined', { user, online_users });
    }

    handleUserLeft(data) {
        const { user, online_users } = data;
        
        this.updateOnlineUsers(online_users);
        this.showUserNotification(`${user.full_name || user.username} saiu do canal`);
        this.emit('userLeft', { user, online_users });
    }

    handleUserStatusChange(data) {
        const { user, status } = data;
        
        this.updateUserStatus(user.id, status);
        this.emit('userStatusChange', { user, status });
    }

    handleChannelUpdate(data) {
        const { channel } = data;
        
        // Atualizar informações do canal na UI
        this.updateChannelInfo(channel);
        this.emit('channelUpdate', channel);
    }

    handleReactionChange(data) {
        const { message_id, reactions, type } = data;
        
        // Atualizar reações na UI
        this.updateMessageReactions(message_id, reactions);
        this.emit('reactionChange', { message_id, reactions, type });
    }

    handleHeartbeat(data) {
        // Responder ao heartbeat
        this.send({
            type: 'heartbeat_response',
            timestamp: Date.now()
        });
    }

    handleError(data) {
        const { error, code } = data;
        console.error('❌ Erro do servidor:', error, code);
        
        this.showError(error);
        this.emit('serverError', { error, code });
    }

    /**
     * Enviar mensagem via WebSocket
     */
    send(data) {
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('❌ Erro ao enviar mensagem:', error);
                this.messageQueue.push(data);
                return false;
            }
        } else {
            // Adicionar à fila se não conectado
            this.messageQueue.push(data);
            return false;
        }
    }

    /**
     * Enviar mensagem de chat
     */
    sendMessage(content, replyTo = null, attachments = []) {
        const messageData = {
            type: 'chat_message',
            content,
            reply_to: replyTo,
            attachments,
            timestamp: Date.now()
        };
        
        return this.send(messageData);
    }

    /**
     * Indicadores de digitação
     */
    startTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.send({ type: 'typing_start' });
        }
        
        // Reset timer
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.stopTyping();
        }, 3000);
    }

    stopTyping() {
        if (this.isTyping) {
            this.isTyping = false;
            this.send({ type: 'typing_stop' });
        }
        
        clearTimeout(this.typingTimer);
    }

    /**
     * Reações
     */
    addReaction(messageId, emoji) {
        return this.send({
            type: 'add_reaction',
            message_id: messageId,
            emoji
        });
    }

    removeReaction(messageId, emoji) {
        return this.send({
            type: 'remove_reaction',
            message_id: messageId,
            emoji
        });
    }

    /**
     * Gerenciamento de conexão
     */
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Desconexão intencional');
            this.socket = null;
        }
        
        this.isConnected = false;
        this.stopHeartbeat();
        this.stopTyping();
    }

    switchChannel(channelId) {
        if (channelId === this.currentChannelId) return;
        
        this.disconnect();
        
        if (channelId) {
            this.connect(channelId);
        }
    }

    scheduleReconnect() {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        console.log(`🔄 Tentando reconectar em ${delay}ms (tentativa ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            this.connect(this.currentChannelId);
        }, delay);
    }

    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    /**
     * Heartbeat para manter conexão viva
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'heartbeat',
                    timestamp: Date.now()
                });
            }
        }, 30000); // 30 segundos
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Event System
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Erro no listener do evento ${event}:`, error);
                }
            });
        }
    }

    /**
     * Funções de UI
     */
    showTypingIndicator(user) {
        const indicator = document.getElementById('typingIndicator');
        const text = document.getElementById('typingText');
        
        if (indicator && text) {
            text.textContent = `${user.full_name || user.username} está digitando...`;
            indicator.style.display = 'block';
        }
    }

    hideTypingIndicator(user) {
        const indicator = document.getElementById('typingIndicator');
        
        if (indicator) {
            // Se há outros usuários digitando, manter visível
            const typingUsers = this.getTypingUsers();
            if (typingUsers.length === 0) {
                indicator.style.display = 'none';
            } else {
                const text = document.getElementById('typingText');
                if (text) {
                    if (typingUsers.length === 1) {
                        text.textContent = `${typingUsers[0].full_name || typingUsers[0].username} está digitando...`;
                    } else {
                        text.textContent = `${typingUsers.length} pessoas estão digitando...`;
                    }
                }
            }
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        
        if (statusElement) {
            statusElement.classList.remove('show', 'connected', 'disconnected', 'error');
            
            switch (status) {
                case 'connected':
                    statusElement.textContent = '✅ Conectado';
                    statusElement.classList.add('show', 'connected');
                    setTimeout(() => statusElement.classList.remove('show'), 2000);
                    break;
                    
                case 'disconnected':
                    statusElement.textContent = '🔄 Reconectando...';
                    statusElement.classList.add('show', 'disconnected');
                    break;
                    
                case 'error':
                    statusElement.textContent = '❌ Erro de conexão';
                    statusElement.classList.add('show', 'error');
                    break;
            }
        }
        
        // Callback personalizado
        if (this.onConnectionChange) {
            this.onConnectionChange(status);
        }
    }

    updateOnlineUsers(users) {
        const onlineList = document.getElementById('onlineUsersList');
        const onlineCount = document.getElementById('onlineCount');
        
        if (onlineCount) {
            onlineCount.textContent = users.length;
        }
        
        if (onlineList) {
            onlineList.innerHTML = '';
            
            users.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.className = 'online-user';
                userDiv.innerHTML = `
                    <div class="online-user-avatar">
                        ${user.first_name ? user.first_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                        <div class="user-status-dot ${user.status || 'online'}"></div>
                    </div>
                    <div class="online-user-info">
                        <div class="online-user-name">${user.full_name || user.username}</div>
                        <div class="online-user-status">${user.department || 'Disponível'}</div>
                    </div>
                `;
                
                userDiv.addEventListener('click', () => {
                    this.startDirectMessage(user.id);
                });
                
                onlineList.appendChild(userDiv);
            });
        }
    }

    updateUserStatus(userId, status) {
        const userElements = document.querySelectorAll(`[data-user-id="${userId}"]`);
        
        userElements.forEach(element => {
            const statusDot = element.querySelector('.user-status-dot, .status-indicator');
            if (statusDot) {
                statusDot.className = statusDot.className.replace(/\b(online|away|busy|offline)\b/g, '');
                statusDot.classList.add(status);
            }
        });
    }

    updateChannelLastMessage(message) {
        const channelItem = document.querySelector(`[data-channel-id="${this.currentChannelId}"]`);
        
        if (channelItem) {
            // Atualizar preview da última mensagem
            const preview = channelItem.querySelector('.channel-preview');
            if (preview) {
                preview.textContent = message.content.substring(0, 50) + 
                    (message.content.length > 50 ? '...' : '');
            }
            
            // Mover canal para o topo da lista
            const channelList = channelItem.parentElement;
            if (channelList) {
                channelList.insertBefore(channelItem, channelList.firstChild);
            }
        }
    }

    updateChannelInfo(channel) {
        const channelTitle = document.querySelector('.channel-name');
        const channelDescription = document.querySelector('.channel-description');
        
        if (channelTitle) {
            channelTitle.textContent = channel.name;
        }
        
        if (channelDescription) {
            channelDescription.textContent = channel.description || '';
        }
        
        // Atualizar sidebar
        const sidebarChannel = document.querySelector(`[data-channel-id="${channel.id}"] .channel-name`);
        if (sidebarChannel) {
            sidebarChannel.textContent = channel.name;
        }
    }

    updateMessageReactions(messageId, reactions) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        
        if (messageElement) {
            const reactionsContainer = messageElement.querySelector('.message-reactions');
            
            if (reactionsContainer) {
                reactionsContainer.innerHTML = this.createReactionsHTML(reactions);
            } else if (reactions.length > 0) {
                // Criar container de reações se não existir
                const messageContent = messageElement.querySelector('.message-content');
                const reactionsDiv = document.createElement('div');
                reactionsDiv.className = 'message-reactions';
                reactionsDiv.innerHTML = this.createReactionsHTML(reactions);
                messageContent.appendChild(reactionsDiv);
            }
        }
    }

    /**
     * Utilitários
     */
    getCurrentUserId() {
        const userIdElement = document.getElementById('currentUserId');
        return userIdElement ? userIdElement.value : null;
    }

    getActiveChannelId() {
        const channelIdElement = document.getElementById('currentChannelId');
        return channelIdElement ? channelIdElement.value : null;
    }

    getTypingUsers() {
        // Implementar lógica para rastrear usuários digitando
        return [];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    createReactionsHTML(reactions) {
        return reactions.map(reaction => 
            `<span class="reaction ${reaction.user_reacted ? 'user-reacted' : ''}" 
                   onclick="toggleReaction('${reaction.emoji}', '${reaction.message_id}')">
                ${reaction.emoji} ${reaction.count}
            </span>`
        ).join('');
    }

    showUserNotification(message) {
        // Implementar sistema de notificações discretas
        console.log('👤', message);
        
        // Notificação toast opcional
        this.showToast(message, 'info');
    }

    showError(message) {
        console.error('❌', message);
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Sistema básico de toast notifications
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'error' ? '#ef4444' : '#3b82f6',
            color: 'white',
            padding: '12px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            zIndex: '10000',
            fontSize: '0.875rem',
            maxWidth: '300px',
            wordWrap: 'break-word'
        });
        
        document.body.appendChild(toast);
        
        // Auto remover após 4 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 4000);
    }

    playNotificationSound() {
        // Som de notificação discreto
        if ('Audio' in window) {
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTSC0fPWfykF');
                audio.volume = 0.1;
                audio.play().catch(e => {
                    // Ignorar erro se não conseguir reproduzir
                });
            } catch (error) {
                // Ignorar erro de audio
            }
        }
    }

    startDirectMessage(userId) {
        // Implementar início de conversa direta
        if (typeof startDirectMessageWith === 'function') {
            startDirectMessageWith(userId);
        }
    }

    handleConnectionError() {
        console.error('❌ Erro de conexão WebSocket');
        this.updateConnectionStatus('error');
        
        // Tentar reconectar após delay
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        }
    }
}

// Instanciar e exportar globalmente
window.chatWebSocket = new ChatWebSocket();

// Funções globais para compatibilidade
window.sendMessage = function() {
    const messageInput = document.getElementById('messageInput');
    const content = messageInput?.value?.trim();
    
    if (!content) return;
    
    if (window.chatWebSocket.sendMessage(content)) {
        messageInput.value = '';
        if (typeof updateSendButton === 'function') {
            updateSendButton();
        }
        if (typeof updateCharCounter === 'function') {
            updateCharCounter();
        }
    }
};

window.startTyping = function() {
    window.chatWebSocket.startTyping();
};

window.stopTyping = function() {
    window.chatWebSocket.stopTyping();
};

window.toggleReaction = function(emoji, messageId) {
    window.chatWebSocket.addReaction(messageId, emoji);
};

window.selectChannel = function(channelId) {
    // Emitir evento de mudança de canal
    window.dispatchEvent(new CustomEvent('channelChanged', {
        detail: { channelId }
    }));
};

// Log de inicialização
console.log('🚀 Chat WebSocket carregado e pronto!');

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatWebSocket;
}
