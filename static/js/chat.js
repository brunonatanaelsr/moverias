// ===================================
// MÓDULO DE CHAT - JAVASCRIPT
// ===================================

(function() {
    'use strict';

    // Configurações globais
    const CHAT_CONFIG = {
        wsUrl: null,
        reconnectInterval: 3000,
        typingTimeout: 3000,
        messageLimit: 50,
        fileMaxSize: 10 * 1024 * 1024, // 10MB
        allowedFileTypes: ['image/*', '.pdf', '.doc', '.docx', '.txt', '.zip'],
        reactions: ['👍', '👎', '😄', '😢', '😲', '❤️', '🚀', '👏', '🎉', '✅']
    };

    // Estado global do chat
    let chatState = {
        currentChannelId: null,
        currentUserId: null,
        wsConnection: null,
        isConnected: false,
        typingUsers: new Set(),
        messages: new Map(),
        unreadCounts: new Map(),
        lastMessageId: null,
        isLoading: false
    };

    // Utilitários
    const ChatUtils = {
        /**
         * Gera UUID v4
         */
        generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        },

        /**
         * Formatar tempo de forma relativa
         */
        formatRelativeTime(timestamp) {
            const now = new Date();
            const date = new Date(timestamp);
            const diff = now - date;
            
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (days > 0) {
                return days === 1 ? 'ontem' : `${days} dias atrás`;
            } else if (hours > 0) {
                return hours === 1 ? '1 hora atrás' : `${hours} horas atrás`;
            } else if (minutes > 0) {
                return minutes === 1 ? '1 minuto atrás' : `${minutes} minutos atrás`;
            } else {
                return 'agora mesmo';
            }
        },

        /**
         * Formatar tamanho de arquivo
         */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
         * Detectar URLs no texto
         */
        linkify(text) {
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            return text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        },

        /**
         * Detectar menções no texto
         */
        mentionify(text) {
            const mentionRegex = /@(\w+)/g;
            return text.replace(mentionRegex, '<span class="mention">@$1</span>');
        },

        /**
         * Processar texto da mensagem
         */
        processMessageText(text) {
            let processed = this.sanitizeHTML(text);
            processed = this.linkify(processed);
            processed = this.mentionify(processed);
            return processed;
        },

        /**
         * Detectar se é uma imagem
         */
        isImage(filename) {
            const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
            const extension = filename.split('.').pop().toLowerCase();
            return imageExtensions.includes(extension);
        },

        /**
         * Debounce function
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
        }
    };

    // Gerenciador de WebSocket
    const WebSocketManager = {
        connection: null,
        reconnectTimer: null,
        isReconnecting: false,

        /**
         * Conectar ao WebSocket
         */
        connect(channelId) {
            if (this.connection && this.connection.readyState === WebSocket.OPEN) {
                this.disconnect();
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${channelId}/`;
            
            try {
                this.connection = new WebSocket(wsUrl);
                this.setupEventHandlers();
                chatState.wsConnection = this.connection;
            } catch (error) {
                console.error('Erro ao conectar WebSocket:', error);
                this.scheduleReconnect(channelId);
            }
        },

        /**
         * Configurar event handlers do WebSocket
         */
        setupEventHandlers() {
            this.connection.onopen = (event) => {
                console.log('WebSocket conectado');
                chatState.isConnected = true;
                this.isReconnecting = false;
                this.clearReconnectTimer();
                UIManager.showConnectionStatus(true);
            };

            this.connection.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Erro ao processar mensagem WebSocket:', error);
                }
            };

            this.connection.onclose = (event) => {
                console.log('WebSocket desconectado:', event.code, event.reason);
                chatState.isConnected = false;
                UIManager.showConnectionStatus(false);
                
                if (!this.isReconnecting && event.code !== 1000) {
                    this.scheduleReconnect(chatState.currentChannelId);
                }
            };

            this.connection.onerror = (error) => {
                console.error('Erro WebSocket:', error);
                UIManager.showError('Erro de conexão. Tentando reconectar...');
            };
        },

        /**
         * Processar mensagens recebidas
         */
        handleMessage(data) {
            switch (data.type) {
                case 'message':
                    MessageManager.handleNewMessage(data.message);
                    break;
                    
                case 'typing':
                    TypingManager.handleTypingUpdate(data.user, data.typing);
                    break;
                    
                case 'reaction':
                    ReactionManager.handleReactionUpdate(data);
                    break;
                    
                case 'user_status':
                    UIManager.updateUserStatus(data.user_id, data.status);
                    break;
                    
                case 'channel_update':
                    UIManager.updateChannelInfo(data.channel);
                    break;
                    
                case 'error':
                    UIManager.showError(data.message);
                    break;
                    
                default:
                    console.warn('Tipo de mensagem desconhecido:', data.type);
            }
        },

        /**
         * Enviar mensagem via WebSocket
         */
        send(data) {
            if (this.connection && this.connection.readyState === WebSocket.OPEN) {
                this.connection.send(JSON.stringify(data));
                return true;
            } else {
                console.warn('WebSocket não conectado. Mensagem não enviada:', data);
                UIManager.showError('Conexão perdida. Mensagem não enviada.');
                return false;
            }
        },

        /**
         * Agendar reconexão
         */
        scheduleReconnect(channelId) {
            if (this.isReconnecting) return;
            
            this.isReconnecting = true;
            this.reconnectTimer = setTimeout(() => {
                console.log('Tentando reconectar...');
                this.connect(channelId);
            }, CHAT_CONFIG.reconnectInterval);
        },

        /**
         * Limpar timer de reconexão
         */
        clearReconnectTimer() {
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
        },

        /**
         * Desconectar
         */
        disconnect() {
            this.clearReconnectTimer();
            if (this.connection) {
                this.connection.close(1000, 'Desconexão manual');
                this.connection = null;
            }
            chatState.isConnected = false;
        }
    };

    // Gerenciador de mensagens
    const MessageManager = {
        /**
         * Enviar nova mensagem
         */
        sendMessage(content, attachments = []) {
            if (!content.trim() && attachments.length === 0) return;

            const messageId = ChatUtils.generateUUID();
            const message = {
                id: messageId,
                type: 'message',
                content: content.trim(),
                channel_id: chatState.currentChannelId,
                sender: {
                    id: chatState.currentUserId,
                    full_name: 'Você'
                },
                created_at: new Date().toISOString(),
                attachments: attachments,
                sending: true
            };

            // Adicionar mensagem localmente primeiro
            this.addMessageToUI(message);
            this.scrollToBottom();

            // Enviar via WebSocket
            const sent = WebSocketManager.send({
                type: 'message',
                content: content.trim(),
                channel_id: chatState.currentChannelId,
                temp_id: messageId,
                attachments: attachments
            });

            if (!sent) {
                this.markMessageAsFailed(messageId);
            }
        },

        /**
         * Processar nova mensagem recebida
         */
        handleNewMessage(message) {
            // Remover mensagem temporária se existir
            if (message.temp_id) {
                this.removeTemporaryMessage(message.temp_id);
            }

            this.addMessageToUI(message);
            this.updateChannelLastMessage(message);
            this.playNotificationSound();
            
            // Auto-scroll se estiver no final
            if (this.isAtBottom()) {
                this.scrollToBottom();
            } else {
                this.showNewMessageBadge();
            }
        },

        /**
         * Adicionar mensagem à interface
         */
        addMessageToUI(message) {
            const container = document.getElementById('messagesContainer');
            const messageEl = this.createMessageElement(message);
            
            // Verificar se deve agrupar com mensagem anterior
            const lastMessage = container.lastElementChild;
            if (this.shouldGroupMessages(lastMessage, message)) {
                this.groupMessages(lastMessage, messageEl);
            } else {
                container.appendChild(messageEl);
            }

            // Armazenar no cache local
            chatState.messages.set(message.id, message);
            chatState.lastMessageId = message.id;
        },

        /**
         * Criar elemento HTML da mensagem
         */
        createMessageElement(message) {
            const messageEl = document.createElement('div');
            messageEl.className = 'message-group';
            messageEl.setAttribute('data-message-id', message.id);
            
            if (message.sending) {
                messageEl.classList.add('message-sending');
            }
            
            if (message.failed) {
                messageEl.classList.add('message-failed');
            }

            const isOwn = message.sender.id === chatState.currentUserId;
            const processedContent = ChatUtils.processMessageText(message.content);
            
            messageEl.innerHTML = `
                <div class="message-avatar">
                    ${this.getAvatarText(message.sender)}
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">${message.sender.full_name}</span>
                        <span class="message-time">${this.formatMessageTime(message.created_at)}</span>
                        ${message.edited ? '<span class="message-edited">(editado)</span>' : ''}
                    </div>
                    <div class="message-text">${processedContent}</div>
                    ${this.renderAttachments(message.attachments || [])}
                    ${this.renderReactions(message.reactions || [])}
                </div>
                ${isOwn ? this.renderMessageActions(message.id) : ''}
            `;

            // Adicionar event listeners
            this.attachMessageEvents(messageEl, message);

            return messageEl;
        },

        /**
         * Renderizar anexos
         */
        renderAttachments(attachments) {
            if (!attachments || attachments.length === 0) return '';

            return attachments.map(attachment => {
                if (ChatUtils.isImage(attachment.name)) {
                    return `
                        <div class="message-attachment">
                            <img src="${attachment.url}" 
                                 alt="${attachment.name}" 
                                 class="attachment-image"
                                 onclick="openImageModal('${attachment.url}', '${attachment.name}')">
                        </div>
                    `;
                } else {
                    return `
                        <div class="message-attachment">
                            <div class="attachment-file">
                                <div class="attachment-icon">
                                    <i class="fas fa-file"></i>
                                </div>
                                <div class="attachment-info">
                                    <div class="attachment-name">${attachment.name}</div>
                                    <div class="attachment-size">${ChatUtils.formatFileSize(attachment.size)}</div>
                                </div>
                                <a href="${attachment.url}" 
                                   class="attachment-download" 
                                   target="_blank" 
                                   download="${attachment.name}">
                                    <i class="fas fa-download"></i>
                                </a>
                            </div>
                        </div>
                    `;
                }
            }).join('');
        },

        /**
         * Renderizar reações
         */
        renderReactions(reactions) {
            if (!reactions || reactions.length === 0) return '';

            const reactionGroups = this.groupReactions(reactions);
            const reactionsHtml = Object.entries(reactionGroups).map(([emoji, data]) => {
                const isActive = data.users.includes(chatState.currentUserId);
                return `
                    <div class="reaction ${isActive ? 'active' : ''}" 
                         onclick="toggleReaction('${data.messageId}', '${emoji}')">
                        ${emoji} ${data.count}
                    </div>
                `;
            }).join('');

            return `<div class="message-reactions">${reactionsHtml}</div>`;
        },

        /**
         * Agrupar reações por emoji
         */
        groupReactions(reactions) {
            const groups = {};
            reactions.forEach(reaction => {
                if (!groups[reaction.emoji]) {
                    groups[reaction.emoji] = {
                        count: 0,
                        users: [],
                        messageId: reaction.message_id
                    };
                }
                groups[reaction.emoji].count++;
                groups[reaction.emoji].users.push(reaction.user_id);
            });
            return groups;
        },

        /**
         * Renderizar ações da mensagem
         */
        renderMessageActions(messageId) {
            return `
                <div class="message-actions-menu">
                    <button class="message-action-btn" onclick="editMessage('${messageId}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="message-action-btn" onclick="deleteMessage('${messageId}')">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="message-action-btn" onclick="replyToMessage('${messageId}')">
                        <i class="fas fa-reply"></i>
                    </button>
                </div>
            `;
        },

        /**
         * Anexar eventos à mensagem
         */
        attachMessageEvents(messageEl, message) {
            // Context menu
            messageEl.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                ContextMenuManager.show(e.clientX, e.clientY, message);
            });

            // Hover effects
            messageEl.addEventListener('mouseenter', () => {
                messageEl.classList.add('message-hover');
            });

            messageEl.addEventListener('mouseleave', () => {
                messageEl.classList.remove('message-hover');
            });
        },

        /**
         * Verificar se deve agrupar mensagens
         */
        shouldGroupMessages(lastMessageEl, newMessage) {
            if (!lastMessageEl) return false;
            
            const lastMessageId = lastMessageEl.getAttribute('data-message-id');
            const lastMessage = chatState.messages.get(lastMessageId);
            
            if (!lastMessage) return false;
            
            // Agrupar se mesmo usuário e menos de 5 minutos de diferença
            const timeDiff = new Date(newMessage.created_at) - new Date(lastMessage.created_at);
            const fiveMinutes = 5 * 60 * 1000;
            
            return lastMessage.sender.id === newMessage.sender.id && timeDiff < fiveMinutes;
        },

        /**
         * Agrupar mensagens
         */
        groupMessages(lastMessageEl, newMessageEl) {
            // Adicionar apenas o conteúdo da nova mensagem
            const lastContent = lastMessageEl.querySelector('.message-content');
            const newContent = newMessageEl.querySelector('.message-content');
            
            const newMessageContent = document.createElement('div');
            newMessageContent.className = 'grouped-message';
            newMessageContent.innerHTML = `
                <div class="message-text">${newContent.querySelector('.message-text').innerHTML}</div>
                ${newContent.querySelector('.message-reactions')?.outerHTML || ''}
            `;
            
            lastContent.appendChild(newMessageContent);
        },

        /**
         * Obter texto do avatar
         */
        getAvatarText(sender) {
            if (sender.avatar) {
                return `<img src="${sender.avatar}" alt="${sender.full_name}">`;
            }
            
            const names = sender.full_name.split(' ');
            const initials = names.length > 1 ? 
                names[0][0] + names[names.length - 1][0] : 
                names[0][0] + (names[0][1] || '');
            
            return initials.toUpperCase();
        },

        /**
         * Formatar tempo da mensagem
         */
        formatMessageTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            
            if (date.toDateString() === now.toDateString()) {
                return date.toLocaleTimeString('pt-BR', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } else {
                return date.toLocaleDateString('pt-BR', { 
                    day: '2-digit', 
                    month: '2-digit',
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            }
        },

        /**
         * Marcar mensagem como falhada
         */
        markMessageAsFailed(messageId) {
            const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageEl) {
                messageEl.classList.remove('message-sending');
                messageEl.classList.add('message-failed');
            }
        },

        /**
         * Remover mensagem temporária
         */
        removeTemporaryMessage(tempId) {
            const messageEl = document.querySelector(`[data-message-id="${tempId}"]`);
            if (messageEl) {
                messageEl.remove();
            }
        },

        /**
         * Verificar se está no final do scroll
         */
        isAtBottom() {
            const container = document.getElementById('messagesContainer');
            return container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
        },

        /**
         * Rolar para o final
         */
        scrollToBottom() {
            const container = document.getElementById('messagesContainer');
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
        },

        /**
         * Mostrar badge de nova mensagem
         */
        showNewMessageBadge() {
            // Implementar badge flutuante para novas mensagens
        },

        /**
         * Atualizar última mensagem do canal
         */
        updateChannelLastMessage(message) {
            const channelEl = document.querySelector(`[data-channel-id="${message.channel_id}"]`);
            if (channelEl) {
                const statusEl = channelEl.querySelector('.channel-status');
                if (statusEl) {
                    statusEl.textContent = message.content.substring(0, 30) + 
                        (message.content.length > 30 ? '...' : '');
                }
            }
        },

        /**
         * Tocar som de notificação
         */
        playNotificationSound() {
            // Implementar som de notificação
            if ('Notification' in window && Notification.permission === 'granted') {
                // Criar notificação do navegador se necessário
            }
        }
    };

    // Gerenciador de digitação
    const TypingManager = {
        typingTimeout: null,
        isTyping: false,

        /**
         * Iniciar indicador de digitação
         */
        startTyping() {
            if (this.isTyping) return;
            
            this.isTyping = true;
            WebSocketManager.send({
                type: 'typing',
                typing: true,
                channel_id: chatState.currentChannelId
            });

            this.resetTypingTimeout();
        },

        /**
         * Parar indicador de digitação
         */
        stopTyping() {
            if (!this.isTyping) return;
            
            this.isTyping = false;
            WebSocketManager.send({
                type: 'typing',
                typing: false,
                channel_id: chatState.currentChannelId
            });

            this.clearTypingTimeout();
        },

        /**
         * Resetar timeout de digitação
         */
        resetTypingTimeout() {
            this.clearTypingTimeout();
            this.typingTimeout = setTimeout(() => {
                this.stopTyping();
            }, CHAT_CONFIG.typingTimeout);
        },

        /**
         * Limpar timeout de digitação
         */
        clearTypingTimeout() {
            if (this.typingTimeout) {
                clearTimeout(this.typingTimeout);
                this.typingTimeout = null;
            }
        },

        /**
         * Processar atualização de digitação
         */
        handleTypingUpdate(user, typing) {
            if (user.id === chatState.currentUserId) return;

            if (typing) {
                chatState.typingUsers.add(user);
            } else {
                chatState.typingUsers.delete(user);
            }

            this.updateTypingIndicator();
        },

        /**
         * Atualizar indicador de digitação
         */
        updateTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            const text = document.getElementById('typingText');
            
            if (chatState.typingUsers.size === 0) {
                indicator.classList.remove('show');
                return;
            }

            const users = Array.from(chatState.typingUsers);
            let message = '';

            if (users.length === 1) {
                message = `${users[0].full_name} está digitando...`;
            } else if (users.length === 2) {
                message = `${users[0].full_name} e ${users[1].full_name} estão digitando...`;
            } else {
                message = `${users.length} pessoas estão digitando...`;
            }

            text.textContent = message;
            indicator.classList.add('show');
        }
    };

    // Gerenciador de reações
    const ReactionManager = {
        /**
         * Alternar reação
         */
        toggleReaction(messageId, emoji) {
            WebSocketManager.send({
                type: 'reaction',
                message_id: messageId,
                emoji: emoji,
                channel_id: chatState.currentChannelId
            });
        },

        /**
         * Processar atualização de reação
         */
        handleReactionUpdate(data) {
            const messageEl = document.querySelector(`[data-message-id="${data.message_id}"]`);
            if (!messageEl) return;

            // Atualizar reações na interface
            const reactionsContainer = messageEl.querySelector('.message-reactions');
            if (reactionsContainer) {
                reactionsContainer.outerHTML = MessageManager.renderReactions(data.reactions);
            } else {
                const messageContent = messageEl.querySelector('.message-content');
                messageContent.insertAdjacentHTML('beforeend', 
                    MessageManager.renderReactions(data.reactions));
            }
        }
    };

    // Gerenciador de interface
    const UIManager = {
        /**
         * Mostrar status de conexão
         */
        showConnectionStatus(connected) {
            const statusEl = document.getElementById('connectionStatus');
            if (statusEl) {
                statusEl.className = connected ? 'connected' : 'disconnected';
                statusEl.textContent = connected ? 'Conectado' : 'Desconectado';
            }
        },

        /**
         * Mostrar erro
         */
        showError(message) {
            // Implementar toast de erro
            console.error('Chat Error:', message);
        },

        /**
         * Atualizar status do usuário
         */
        updateUserStatus(userId, status) {
            const userEls = document.querySelectorAll(`[data-user-id="${userId}"]`);
            userEls.forEach(el => {
                const statusEl = el.querySelector('.user-status');
                if (statusEl) {
                    statusEl.className = `user-status ${status}`;
                }
            });
        },

        /**
         * Atualizar informações do canal
         */
        updateChannelInfo(channel) {
            const titleEl = document.querySelector('.chat-title');
            const subtitleEl = document.querySelector('.chat-subtitle');
            
            if (titleEl) titleEl.textContent = channel.name;
            if (subtitleEl) subtitleEl.textContent = `${channel.member_count} membros`;
        }
    };

    // Gerenciador de menu de contexto
    const ContextMenuManager = {
        currentMenu: null,

        /**
         * Mostrar menu de contexto
         */
        show(x, y, message) {
            this.hide();

            const menu = document.createElement('div');
            menu.className = 'context-menu show';
            menu.style.left = x + 'px';
            menu.style.top = y + 'px';

            const items = this.getMenuItems(message);
            menu.innerHTML = items.map(item => 
                `<div class="context-menu-item ${item.class || ''}" onclick="${item.action}">
                    <i class="${item.icon}"></i>
                    ${item.label}
                </div>`
            ).join('');

            document.body.appendChild(menu);
            this.currentMenu = menu;

            // Fechar ao clicar fora
            setTimeout(() => {
                document.addEventListener('click', this.handleOutsideClick.bind(this));
            }, 0);
        },

        /**
         * Obter itens do menu
         */
        getMenuItems(message) {
            const items = [
                {
                    icon: 'fas fa-reply',
                    label: 'Responder',
                    action: `replyToMessage('${message.id}')`
                },
                {
                    icon: 'fas fa-copy',
                    label: 'Copiar texto',
                    action: `copyMessageText('${message.id}')`
                }
            ];

            // Adicionar opções para mensagens próprias
            if (message.sender.id === chatState.currentUserId) {
                items.push(
                    {
                        icon: 'fas fa-edit',
                        label: 'Editar',
                        action: `editMessage('${message.id}')`
                    },
                    {
                        icon: 'fas fa-trash',
                        label: 'Excluir',
                        action: `deleteMessage('${message.id}')`,
                        class: 'danger'
                    }
                );
            }

            return items;
        },

        /**
         * Processar clique fora do menu
         */
        handleOutsideClick(e) {
            if (!this.currentMenu.contains(e.target)) {
                this.hide();
            }
        },

        /**
         * Esconder menu
         */
        hide() {
            if (this.currentMenu) {
                this.currentMenu.remove();
                this.currentMenu = null;
                document.removeEventListener('click', this.handleOutsideClick.bind(this));
            }
        }
    };

    // Inicialização
    const ChatApp = {
        /**
         * Inicializar aplicação
         */
        init() {
            this.setupGlobalVariables();
            this.setupEventListeners();
            this.setupMessageInput();
            this.connectToChannel();
        },

        /**
         * Configurar variáveis globais
         */
        setupGlobalVariables() {
            chatState.currentChannelId = window.currentChannelId || null;
            chatState.currentUserId = window.currentUserId || null;
        },

        /**
         * Configurar event listeners
         */
        setupEventListeners() {
            // Botão de enviar
            const sendBtn = document.getElementById('sendButton');
            if (sendBtn) {
                sendBtn.addEventListener('click', this.handleSendMessage.bind(this));
            }

            // Input de mensagem
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.addEventListener('keydown', this.handleMessageInputKeydown.bind(this));
                messageInput.addEventListener('input', this.handleMessageInputChange.bind(this));
            }

            // Upload de arquivo
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.addEventListener('change', this.handleFileUpload.bind(this));
            }

            // Scroll do container de mensagens
            const messagesContainer = document.getElementById('messagesContainer');
            if (messagesContainer) {
                messagesContainer.addEventListener('scroll', 
                    ChatUtils.debounce(this.handleMessagesScroll.bind(this), 100));
            }
        },

        /**
         * Configurar input de mensagem
         */
        setupMessageInput() {
            const messageInput = document.getElementById('messageInput');
            if (!messageInput) return;

            // Auto-resize
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        },

        /**
         * Conectar ao canal
         */
        connectToChannel() {
            if (chatState.currentChannelId) {
                WebSocketManager.connect(chatState.currentChannelId);
            }
        },

        /**
         * Processar envio de mensagem
         */
        handleSendMessage() {
            const messageInput = document.getElementById('messageInput');
            const content = messageInput.value.trim();
            
            if (!content) return;

            MessageManager.sendMessage(content);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            const sendBtn = document.getElementById('sendButton');
            if (sendBtn) sendBtn.disabled = true;
        },

        /**
         * Processar teclas do input
         */
        handleMessageInputKeydown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        },

        /**
         * Processar mudança no input
         */
        handleMessageInputChange(e) {
            const content = e.target.value.trim();
            const sendBtn = document.getElementById('sendButton');
            
            if (sendBtn) {
                sendBtn.disabled = !content;
            }

            // Indicador de digitação
            if (content) {
                TypingManager.startTyping();
            } else {
                TypingManager.stopTyping();
            }
        },

        /**
         * Processar upload de arquivo
         */
        handleFileUpload(e) {
            const files = Array.from(e.target.files);
            // Implementar upload de arquivos
            console.log('Files selected:', files);
        },

        /**
         * Processar scroll das mensagens
         */
        handleMessagesScroll(e) {
            const container = e.target;
            
            // Carregar mensagens antigas se chegou no topo
            if (container.scrollTop === 0) {
                this.loadMoreMessages();
            }
        },

        /**
         * Carregar mais mensagens
         */
        loadMoreMessages() {
            if (chatState.isLoading) return;
            
            chatState.isLoading = true;
            // Implementar carregamento de mensagens antigas
        }
    };

    // Funções globais expostas
    window.ChatApp = ChatApp;
    window.selectChannel = function(channelId, type) {
        window.location.href = `/chat/?channel=${channelId}`;
    };

    window.toggleReaction = ReactionManager.toggleReaction.bind(ReactionManager);
    
    window.toggleSidebar = function() {
        const sidebar = document.getElementById('chatSidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
        }
    };

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ChatApp.init());
    } else {
        ChatApp.init();
    }

})();
