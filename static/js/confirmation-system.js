/**
 * Sistema de Confirmações para Operações CRUD
 * Fornece modais de confirmação para operações críticas
 */

class ConfirmationSystem {
    constructor() {
        this.init();
    }

    init() {
        this.createModalHTML();
        this.bindEvents();
    }

    createModalHTML() {
        const modalHTML = `
        <!-- Modal de Confirmação -->
        <div class="modal fade" id="confirmationModal" tabindex="-1" aria-labelledby="confirmationModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmationModalLabel">
                            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                            Confirmação Necessária
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex align-items-start">
                            <div class="flex-shrink-0">
                                <i class="fas fa-question-circle text-primary fa-2x me-3"></i>
                            </div>
                            <div class="flex-grow-1">
                                <p class="mb-3" id="confirmationMessage">
                                    Tem certeza que deseja realizar esta operação?
                                </p>
                                <div class="alert alert-warning d-none" id="confirmationWarning">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    <span id="warningMessage"></span>
                                </div>
                                <div class="form-check d-none" id="confirmationCheckbox">
                                    <input class="form-check-input" type="checkbox" id="confirmCheck">
                                    <label class="form-check-label fw-bold text-danger" for="confirmCheck">
                                        Confirmo que entendo as consequências desta ação
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i> Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmActionBtn">
                            <i class="fas fa-check me-1"></i> Confirmar
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // Adicionar modal ao body se não existir
        if (!document.getElementById('confirmationModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }

    bindEvents() {
        // Interceptar formulários de exclusão
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('delete-form') || form.dataset.requiresConfirmation === 'true') {
                e.preventDefault();
                this.showConfirmation(form);
            }
        });

        // Interceptar links de exclusão
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[data-confirm]');
            if (link) {
                e.preventDefault();
                this.showConfirmationForLink(link);
            }
        });

        // Interceptar botões de ação
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button[data-confirm]');
            if (button) {
                e.preventDefault();
                this.showConfirmationForButton(button);
            }
        });
    }

    showConfirmation(form) {
        const action = this.getActionFromForm(form);
        const entity = this.getEntityFromForm(form);
        const config = this.getConfirmationConfig(action, entity, form);
        
        this.displayModal(config, () => {
            form.submit();
        });
    }

    showConfirmationForLink(link) {
        const action = link.dataset.action || 'excluir';
        const entity = link.dataset.entity || 'item';
        const config = this.getConfirmationConfig(action, entity, link);
        
        this.displayModal(config, () => {
            window.location.href = link.href;
        });
    }

    showConfirmationForButton(button) {
        const action = button.dataset.action || 'executar';
        const entity = button.dataset.entity || 'operação';
        const config = this.getConfirmationConfig(action, entity, button);
        
        this.displayModal(config, () => {
            if (button.form) {
                button.form.submit();
            } else if (button.onclick) {
                button.onclick();
            }
        });
    }

    getActionFromForm(form) {
        if (form.method.toLowerCase() === 'post' && form.querySelector('input[name="_method"][value="DELETE"]')) {
            return 'excluir';
        }
        if (form.action.includes('/delete/') || form.action.includes('/excluir/')) {
            return 'excluir';
        }
        if (form.action.includes('/edit/') || form.action.includes('/editar/')) {
            return 'editar';
        }
        return 'salvar';
    }

    getEntityFromForm(form) {
        // Tentar extrair entidade da URL ou atributos
        const url = form.action;
        if (url.includes('/beneficiaries/') || url.includes('/beneficiarias/')) return 'beneficiária';
        if (url.includes('/projects/') || url.includes('/projetos/')) return 'projeto';
        if (url.includes('/activities/') || url.includes('/atividades/')) return 'atividade';
        if (url.includes('/users/') || url.includes('/usuarios/')) return 'usuário';
        if (url.includes('/workshops/')) return 'workshop';
        if (url.includes('/enrollments/') || url.includes('/matriculas/')) return 'matrícula';
        return form.dataset.entity || 'item';
    }

    getConfirmationConfig(action, entity, element) {
        const configs = {
            excluir: {
                title: `Excluir ${entity}`,
                message: `Tem certeza que deseja excluir ${this.getArticle(entity)} ${entity}?`,
                warning: `Esta ação não pode ser desfeita. Todos os dados relacionados ${this.getPreposition(entity)} ${entity} também serão removidos.`,
                buttonText: 'Excluir',
                buttonClass: 'btn-danger',
                icon: 'fas fa-trash',
                requiresCheck: true
            },
            editar: {
                title: `Editar ${entity}`,
                message: `Confirma as alterações ${this.getPreposition(entity)} ${entity}?`,
                warning: null,
                buttonText: 'Salvar Alterações',
                buttonClass: 'btn-primary',
                icon: 'fas fa-save',
                requiresCheck: false
            },
            salvar: {
                title: `Salvar ${entity}`,
                message: `Confirma o cadastro ${this.getPreposition(entity)} ${entity}?`,
                warning: null,
                buttonText: 'Salvar',
                buttonClass: 'btn-success',
                icon: 'fas fa-save',
                requiresCheck: false
            },
            desativar: {
                title: `Desativar ${entity}`,
                message: `Tem certeza que deseja desativar ${this.getArticle(entity)} ${entity}?`,
                warning: `${entity.charAt(0).toUpperCase() + entity.slice(1)} ficará inativa no sistema.`,
                buttonText: 'Desativar',
                buttonClass: 'btn-warning',
                icon: 'fas fa-ban',
                requiresCheck: false
            },
            ativar: {
                title: `Ativar ${entity}`,
                message: `Confirma a ativação ${this.getPreposition(entity)} ${entity}?`,
                warning: null,
                buttonText: 'Ativar',
                buttonClass: 'btn-success',
                icon: 'fas fa-check',
                requiresCheck: false
            }
        };

        const config = configs[action] || configs.salvar;
        
        // Personalização baseada no elemento
        if (element.dataset.confirmMessage) {
            config.message = element.dataset.confirmMessage;
        }
        if (element.dataset.confirmWarning) {
            config.warning = element.dataset.confirmWarning;
        }
        if (element.dataset.confirmTitle) {
            config.title = element.dataset.confirmTitle;
        }

        return config;
    }

    getArticle(entity) {
        const feminineEntities = ['beneficiária', 'atividade', 'matrícula'];
        return feminineEntities.includes(entity.toLowerCase()) ? 'a' : 'o';
    }

    getPreposition(entity) {
        const feminineEntities = ['beneficiária', 'atividade', 'matrícula'];
        return feminineEntities.includes(entity.toLowerCase()) ? 'da' : 'do';
    }

    displayModal(config, onConfirm) {
        const modal = document.getElementById('confirmationModal');
        const title = modal.querySelector('#confirmationModalLabel');
        const message = modal.querySelector('#confirmationMessage');
        const warning = modal.querySelector('#confirmationWarning');
        const warningMessage = modal.querySelector('#warningMessage');
        const checkboxContainer = modal.querySelector('#confirmationCheckbox');
        const confirmBtn = modal.querySelector('#confirmActionBtn');

        // Configurar título
        title.innerHTML = `<i class="${config.icon} text-warning me-2"></i>${config.title}`;

        // Configurar mensagem
        message.textContent = config.message;

        // Configurar aviso
        if (config.warning) {
            warning.classList.remove('d-none');
            warningMessage.textContent = config.warning;
        } else {
            warning.classList.add('d-none');
        }

        // Configurar checkbox de confirmação
        if (config.requiresCheck) {
            checkboxContainer.classList.remove('d-none');
            const checkbox = document.getElementById('confirmCheck');
            checkbox.checked = false;
            
            // Desabilitar botão até marcar checkbox
            confirmBtn.disabled = true;
            checkbox.addEventListener('change', () => {
                confirmBtn.disabled = !checkbox.checked;
            });
        } else {
            checkboxContainer.classList.add('d-none');
            confirmBtn.disabled = false;
        }

        // Configurar botão
        confirmBtn.className = `btn ${config.buttonClass}`;
        confirmBtn.innerHTML = `<i class="${config.icon} me-1"></i> ${config.buttonText}`;

        // Configurar evento de confirmação
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.addEventListener('click', () => {
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            bootstrapModal.hide();
            onConfirm();
        });

        // Mostrar modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    // Método para mostrar confirmação programaticamente
    static confirm(options) {
        const instance = new ConfirmationSystem();
        const config = {
            title: options.title || 'Confirmação',
            message: options.message || 'Tem certeza?',
            warning: options.warning || null,
            buttonText: options.buttonText || 'Confirmar',
            buttonClass: options.buttonClass || 'btn-primary',
            icon: options.icon || 'fas fa-question-circle',
            requiresCheck: options.requiresCheck || false
        };

        return new Promise((resolve) => {
            instance.displayModal(config, () => resolve(true));
            
            // Resolver como false se modal for fechado sem confirmação
            const modal = document.getElementById('confirmationModal');
            modal.addEventListener('hidden.bs.modal', () => resolve(false), { once: true });
        });
    }
}

// Auto-inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ConfirmationSystem();
});

// Exportar para uso global
window.ConfirmationSystem = ConfirmationSystem;
