// Chat Widget JavaScript
class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.currentConversation = null;
        this.currentUser = null;
        this.activeTab = 'messages';
        this.conversations = [];
        this.users = [];
        this.unreadCount = 0;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCurrentUser();
        this.loadConversations();
        this.loadUsers();
        this.startPolling();
    }

    bindEvents() {
        // Toggle chat
        document.getElementById('chat-toggle').addEventListener('click', () => {
            this.toggleChat();
        });

        // Close chat
        document.getElementById('chat-close').addEventListener('click', () => {
            this.closeChat();
        });

        // Minimize chat
        document.getElementById('chat-minimize').addEventListener('click', () => {
            this.minimizeChat();
        });

        // Tab switching
        document.querySelectorAll('.chat-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Back to chat
        document.getElementById('back-to-chat').addEventListener('click', () => {
            this.showChatPanel();
        });

        // Close conversation
        document.getElementById('conversation-close').addEventListener('click', () => {
            this.closeConversation();
        });

        // Send message
        document.getElementById('send-message-btn').addEventListener('click', () => {
            this.sendMessage();
        });

        // Send conversation message
        document.getElementById('conversation-send-btn').addEventListener('click', () => {
            this.sendConversationMessage();
        });

        // Enter key to send
        document.getElementById('new-message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        document.getElementById('conversation-message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendConversationMessage();
            }
        });
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        document.getElementById('chat-panel').classList.remove('hidden');
        this.isOpen = true;
        this.loadConversations();
    }

    closeChat() {
        document.getElementById('chat-panel').classList.add('hidden');
        document.getElementById('conversation-panel').classList.add('hidden');
        this.isOpen = false;
        this.currentConversation = null;
    }

    minimizeChat() {
        document.getElementById('chat-panel').classList.add('hidden');
        this.isOpen = false;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.chat-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.chat-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');

        this.activeTab = tabName;

        // Load data for active tab
        if (tabName === 'messages') {
            this.loadConversations();
        } else if (tabName === 'users') {
            this.loadUsers();
        }
    }

    showConversationPanel(user) {
        this.currentConversation = user;
        document.getElementById('chat-panel').classList.add('hidden');
        document.getElementById('conversation-panel').classList.remove('hidden');
        
        // Update conversation header
        document.getElementById('conversation-title').textContent = user.name;
        document.getElementById('conversation-subtitle').textContent = user.is_online ? 'Online' : 'Offline';
        
        this.loadConversationMessages(user.id);
    }

    showChatPanel() {
        document.getElementById('conversation-panel').classList.add('hidden');
        document.getElementById('chat-panel').classList.remove('hidden');
        this.currentConversation = null;
    }

    closeConversation() {
        this.showChatPanel();
    }

    loadCurrentUser() {
        fetch('/api/auth/current-user/')
            .then(response => response.json())
            .then(data => {
                this.currentUser = data;
            })
            .catch(error => {
                console.error('Erro ao carregar usuário atual:', error);
            });
    }

    loadConversations() {
        const loading = document.getElementById('conversations-loading');
        const list = document.getElementById('conversations-list');
        
        loading.classList.remove('hidden');
        
        fetch('/api/chat/conversations/')
            .then(response => response.json())
            .then(data => {
                this.conversations = data;
                this.renderConversations();
                loading.classList.add('hidden');
            })
            .catch(error => {
                console.error('Erro ao carregar conversas:', error);
                loading.innerHTML = '<p class="text-red-500 text-center">Erro ao carregar conversas</p>';
            });
    }

    loadUsers() {
        const loading = document.getElementById('users-loading');
        const list = document.getElementById('users-list');
        
        loading.classList.remove('hidden');
        
        fetch('/api/users/active/')
            .then(response => response.json())
            .then(data => {
                this.users = data;
                this.renderUsers();
                loading.classList.add('hidden');
            })
            .catch(error => {
                console.error('Erro ao carregar usuários:', error);
                loading.innerHTML = '<p class="text-red-500 text-center">Erro ao carregar usuários</p>';
            });
    }

    renderConversations() {
        const list = document.getElementById('conversations-list');
        
        if (this.conversations.length === 0) {
            list.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-comments text-gray-300 text-3xl mb-2"></i>
                    <p class="text-gray-500">Nenhuma conversa ainda</p>
                    <p class="text-gray-400 text-sm">Clique em "Usuários" para iniciar uma conversa</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.conversations.map(conversation => `
            <div class="conversation-item flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors" 
                 onclick="chatWidget.showConversationPanel({id: ${conversation.user.id}, name: '${conversation.user.name}', is_online: ${conversation.user.is_online}})">
                <div class="flex-shrink-0 relative">
                    <div class="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-semibold">
                        ${conversation.user.name.charAt(0).toUpperCase()}
                    </div>
                    ${conversation.user.is_online ? '<div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>' : ''}
                </div>
                <div class="ml-3 flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                        <p class="font-medium text-gray-900 truncate">${conversation.user.name}</p>
                        <span class="text-xs text-gray-500">${this.formatTime(conversation.last_message_time)}</span>
                    </div>
                    <p class="text-sm text-gray-600 truncate">${conversation.last_message || 'Sem mensagens'}</p>
                </div>
                ${conversation.unread_count > 0 ? `<div class="ml-2 bg-purple-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">${conversation.unread_count}</div>` : ''}
            </div>
        `).join('');
    }

    renderUsers() {
        const list = document.getElementById('users-list');
        
        if (this.users.length === 0) {
            list.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-users text-gray-300 text-3xl mb-2"></i>
                    <p class="text-gray-500">Nenhum usuário encontrado</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.users.map(user => `
            <div class="user-item flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors" 
                 onclick="chatWidget.showConversationPanel({id: ${user.id}, name: '${user.name}', is_online: ${user.is_online}})">
                <div class="flex-shrink-0 relative">
                    <div class="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-semibold">
                        ${user.name.charAt(0).toUpperCase()}
                    </div>
                    ${user.is_online ? '<div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>' : ''}
                </div>
                <div class="ml-3 flex-1 min-w-0">
                    <p class="font-medium text-gray-900 truncate">${user.name}</p>
                    <p class="text-sm text-gray-600">${user.department || 'Sem departamento'}</p>
                </div>
                <div class="ml-2 text-sm text-gray-500">
                    ${user.is_online ? '<i class="fas fa-circle text-green-500"></i>' : '<i class="fas fa-circle text-gray-300"></i>'}
                </div>
            </div>
        `).join('');
    }

    loadConversationMessages(userId) {
        const messagesContainer = document.getElementById('conversation-messages');
        const loading = document.getElementById('messages-loading');
        
        loading.classList.remove('hidden');
        messagesContainer.innerHTML = '<div id="messages-loading" class="text-center py-8"><i class="fas fa-spinner fa-spin text-gray-400"></i><p class="text-gray-500 mt-2">Carregando mensagens...</p></div>';
        
        fetch(`/api/chat/messages/${userId}/`)
            .then(response => response.json())
            .then(data => {
                this.renderMessages(data);
                loading.classList.add('hidden');
                this.scrollToBottom();
            })
            .catch(error => {
                console.error('Erro ao carregar mensagens:', error);
                messagesContainer.innerHTML = '<p class="text-red-500 text-center">Erro ao carregar mensagens</p>';
            });
    }

    renderMessages(messages) {
        const container = document.getElementById('conversation-messages');
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-comment text-gray-300 text-3xl mb-2"></i>
                    <p class="text-gray-500">Nenhuma mensagem ainda</p>
                    <p class="text-gray-400 text-sm">Envie uma mensagem para começar a conversa</p>
                </div>
            `;
            return;
        }

        container.innerHTML = messages.map(message => `
            <div class="chat-message ${message.sender.id === this.currentUser.id ? 'own' : 'other'} p-3 rounded-lg">
                <div class="flex items-start space-x-2">
                    ${message.sender.id !== this.currentUser.id ? `
                        <div class="w-6 h-6 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                            ${message.sender.name.charAt(0).toUpperCase()}
                        </div>
                    ` : ''}
                    <div class="flex-1">
                        <p class="text-sm">${message.content}</p>
                        <p class="text-xs opacity-75 mt-1">${this.formatTime(message.created_at)}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    sendMessage() {
        const input = document.getElementById('new-message-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Implementar envio de mensagem
        console.log('Enviando mensagem:', message);
        input.value = '';
    }

    sendConversationMessage() {
        const input = document.getElementById('conversation-message-input');
        const message = input.value.trim();
        
        if (!message || !this.currentConversation) return;
        
        // Enviar mensagem via API
        fetch('/api/chat/send-message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                recipient_id: this.currentConversation.id,
                content: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Adicionar mensagem à conversa
                this.addMessageToConversation(data.message);
                input.value = '';
            }
        })
        .catch(error => {
            console.error('Erro ao enviar mensagem:', error);
        });
    }

    addMessageToConversation(message) {
        const container = document.getElementById('conversation-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.sender.id === this.currentUser.id ? 'own' : 'other'} p-3 rounded-lg`;
        messageElement.innerHTML = `
            <div class="flex items-start space-x-2">
                ${message.sender.id !== this.currentUser.id ? `
                    <div class="w-6 h-6 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                        ${message.sender.name.charAt(0).toUpperCase()}
                    </div>
                ` : ''}
                <div class="flex-1">
                    <p class="text-sm">${message.content}</p>
                    <p class="text-xs opacity-75 mt-1">${this.formatTime(message.created_at)}</p>
                </div>
            </div>
        `;
        
        container.appendChild(messageElement);
        this.scrollToBottom();
    }

    scrollToBottom() {
        const container = document.getElementById('conversation-messages');
        container.scrollTop = container.scrollHeight;
    }

    updateUnreadCount() {
        const badge = document.getElementById('chat-badge');
        const totalUnread = this.conversations.reduce((total, conv) => total + conv.unread_count, 0);
        
        if (totalUnread > 0) {
            badge.textContent = totalUnread > 99 ? '99+' : totalUnread;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    startPolling() {
        // Atualizar conversas a cada 30 segundos
        setInterval(() => {
            if (this.isOpen) {
                this.loadConversations();
            }
        }, 30000);

        // Atualizar mensagens da conversa atual a cada 5 segundos
        setInterval(() => {
            if (this.currentConversation) {
                this.loadConversationMessages(this.currentConversation.id);
            }
        }, 5000);
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // < 1 minuto
            return 'Agora';
        } else if (diff < 3600000) { // < 1 hora
            return Math.floor(diff / 60000) + 'min';
        } else if (diff < 86400000) { // < 1 dia
            return Math.floor(diff / 3600000) + 'h';
        } else {
            return date.toLocaleDateString();
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Inicializar o chat widget quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    window.chatWidget = new ChatWidget();
});
