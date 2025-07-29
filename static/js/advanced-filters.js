/**
 * Sistema de Filtros Avançados
 * Parte da Fase 2 do Plano de Melhorias Incrementais - Usabilidade
 */

class AdvancedFilters {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            apiEndpoint: '/api/filter/',
            debounceTime: 300,
            maxResults: 100,
            showCount: true,
            enableExport: true,
            enableSave: true,
            ...options
        };
        
        this.filters = new Map();
        this.results = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.createFilterInterface();
        this.bindEvents();
        this.loadSavedFilters();
    }
    
    createFilterInterface() {
        this.container.innerHTML = `
            <div class="advanced-filters">
                <!-- Cabeçalho dos filtros -->
                <div class="filters-header">
                    <h5 class="filters-title">
                        <i class="fas fa-filter"></i>
                        Filtros Avançados
                    </h5>
                    <div class="filters-actions">
                        <button type="button" class="btn btn-sm btn-outline-secondary" id="clearFilters">
                            <i class="fas fa-times"></i> Limpar
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-primary" id="saveFilters">
                            <i class="fas fa-save"></i> Salvar
                        </button>
                        <button type="button" class="btn btn-sm btn-primary" id="applyFilters">
                            <i class="fas fa-search"></i> Aplicar
                        </button>
                    </div>
                </div>
                
                <!-- Container dos filtros -->
                <div class="filters-container">
                    <div class="row">
                        <!-- Filtro de texto -->
                        <div class="col-md-4 mb-3">
                            <label class="form-label">Busca Geral</label>
                            <div class="input-group">
                                <input type="text" 
                                       class="form-control" 
                                       id="searchText" 
                                       placeholder="Digite para buscar...">
                                <button class="btn btn-outline-secondary" type="button" id="clearSearch">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Filtro de status -->
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Status</label>
                            <select class="form-select" id="statusFilter" multiple>
                                <option value="">Todos</option>
                                <option value="ATIVO">Ativo</option>
                                <option value="INATIVO">Inativo</option>
                                <option value="PENDENTE">Pendente</option>
                                <option value="CONCLUIDO">Concluído</option>
                            </select>
                        </div>
                        
                        <!-- Filtro de datas -->
                        <div class="col-md-5 mb-3">
                            <label class="form-label">Período</label>
                            <div class="row">
                                <div class="col-6">
                                    <input type="date" class="form-control" id="dateFrom" placeholder="De">
                                </div>
                                <div class="col-6">
                                    <input type="date" class="form-control" id="dateTo" placeholder="Até">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Linha adicional de filtros -->
                    <div class="row filters-advanced" style="display: none;">
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Categoria</label>
                            <select class="form-select" id="categoryFilter">
                                <option value="">Todas</option>
                            </select>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Responsável</label>
                            <select class="form-select" id="responsibleFilter">
                                <option value="">Todos</option>
                            </select>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Ordenar por</label>
                            <select class="form-select" id="sortBy">
                                <option value="created_at">Data de Criação</option>
                                <option value="updated_at">Última Atualização</option>
                                <option value="name">Nome</option>
                                <option value="status">Status</option>
                            </select>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Ordem</label>
                            <select class="form-select" id="sortOrder">
                                <option value="desc">Decrescente</option>
                                <option value="asc">Crescente</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Toggle para filtros avançados -->
                    <div class="text-center">
                        <button type="button" class="btn btn-link btn-sm" id="toggleAdvanced">
                            <i class="fas fa-chevron-down"></i>
                            Filtros Avançados
                        </button>
                    </div>
                </div>
                
                <!-- Filtros ativos -->
                <div class="active-filters" style="display: none;">
                    <div class="d-flex align-items-center flex-wrap gap-2">
                        <span class="badge bg-secondary">Filtros Ativos:</span>
                        <div class="active-filters-list"></div>
                    </div>
                </div>
                
                <!-- Resultados -->
                <div class="filters-results">
                    <!-- Header dos resultados -->
                    <div class="results-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="results-info">
                                <span class="results-count">0 resultados</span>
                                <div class="results-loading" style="display: none;">
                                    <div class="spinner-border spinner-border-sm" role="status">
                                        <span class="visually-hidden">Carregando...</span>
                                    </div>
                                    Carregando...
                                </div>
                            </div>
                            
                            <div class="results-actions">
                                ${this.options.enableExport ? `
                                    <button type="button" class="btn btn-sm btn-outline-success" id="exportResults">
                                        <i class="fas fa-download"></i> Exportar
                                    </button>
                                ` : ''}
                                
                                <div class="btn-group" role="group">
                                    <button type="button" class="btn btn-sm btn-outline-secondary" id="viewGrid">
                                        <i class="fas fa-th"></i>
                                    </button>
                                    <button type="button" class="btn btn-sm btn-outline-secondary active" id="viewList">
                                        <i class="fas fa-list"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Container dos resultados -->
                    <div class="results-container">
                        <div class="results-list"></div>
                        <div class="results-empty" style="display: none;">
                            <div class="text-center py-5">
                                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                                <h5 class="text-muted">Nenhum resultado encontrado</h5>
                                <p class="text-muted">Tente ajustar os filtros ou termos de busca</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Paginação -->
                    <div class="results-pagination"></div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Busca com debounce
        const searchInput = document.getElementById('searchText');
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.setFilter('search', e.target.value);
                this.applyFilters();
            }, this.options.debounceTime);
        });
        
        // Limpar busca
        document.getElementById('clearSearch').addEventListener('click', () => {
            searchInput.value = '';
            this.removeFilter('search');
            this.applyFilters();
        });
        
        // Filtros de select
        const selects = ['statusFilter', 'categoryFilter', 'responsibleFilter', 'sortBy', 'sortOrder'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.addEventListener('change', (e) => {
                    const key = selectId.replace('Filter', '').replace('sortBy', 'sort').replace('sortOrder', 'order');
                    if (e.target.value) {
                        this.setFilter(key, e.target.value);
                    } else {
                        this.removeFilter(key);
                    }
                    this.applyFilters();
                });
            }
        });
        
        // Filtros de data
        document.getElementById('dateFrom').addEventListener('change', (e) => {
            if (e.target.value) {
                this.setFilter('date_from', e.target.value);
            } else {
                this.removeFilter('date_from');
            }
            this.applyFilters();
        });
        
        document.getElementById('dateTo').addEventListener('change', (e) => {
            if (e.target.value) {
                this.setFilter('date_to', e.target.value);
            } else {
                this.removeFilter('date_to');
            }
            this.applyFilters();
        });
        
        // Botões de ação
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());
        document.getElementById('applyFilters').addEventListener('click', () => this.applyFilters());
        document.getElementById('saveFilters').addEventListener('click', () => this.saveFilters());
        
        // Toggle filtros avançados
        document.getElementById('toggleAdvanced').addEventListener('click', () => this.toggleAdvancedFilters());
        
        // Visualização
        document.getElementById('viewGrid').addEventListener('click', () => this.setView('grid'));
        document.getElementById('viewList').addEventListener('click', () => this.setView('list'));
        
        // Exportar
        if (this.options.enableExport) {
            document.getElementById('exportResults').addEventListener('click', () => this.exportResults());
        }
    }
    
    setFilter(key, value) {
        if (value !== null && value !== undefined && value !== '') {
            this.filters.set(key, value);
        } else {
            this.filters.delete(key);
        }
        this.updateActiveFilters();
    }
    
    removeFilter(key) {
        this.filters.delete(key);
        this.updateActiveFilters();
    }
    
    clearFilters() {
        this.filters.clear();
        
        // Limpar campos do formulário
        document.getElementById('searchText').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('responsibleFilter').value = '';
        document.getElementById('dateFrom').value = '';
        document.getElementById('dateTo').value = '';
        document.getElementById('sortBy').value = 'created_at';
        document.getElementById('sortOrder').value = 'desc';
        
        this.updateActiveFilters();
        this.applyFilters();
    }
    
    updateActiveFilters() {
        const activeFiltersContainer = document.querySelector('.active-filters');
        const activeFiltersList = document.querySelector('.active-filters-list');
        
        if (this.filters.size === 0) {
            activeFiltersContainer.style.display = 'none';
            return;
        }
        
        activeFiltersContainer.style.display = 'block';
        activeFiltersList.innerHTML = '';
        
        this.filters.forEach((value, key) => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary me-1 mb-1';
            badge.innerHTML = `
                ${this.getFilterLabel(key)}: ${value}
                <button type="button" class="btn-close btn-close-white ms-1" 
                        onclick="window.filtersInstance.removeFilter('${key}'); window.filtersInstance.applyFilters();">
                </button>
            `;
            activeFiltersList.appendChild(badge);
        });
    }
    
    getFilterLabel(key) {
        const labels = {
            'search': 'Busca',
            'status': 'Status',
            'category': 'Categoria',
            'responsible': 'Responsável',
            'date_from': 'Data Inicial',
            'date_to': 'Data Final',
            'sort': 'Ordenação',
            'order': 'Ordem'
        };
        return labels[key] || key;
    }
    
    async applyFilters() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            const params = new URLSearchParams();
            this.filters.forEach((value, key) => {
                params.append(key, value);
            });
            params.append('page', this.currentPage);
            params.append('limit', this.options.maxResults);
            
            const response = await fetch(`${this.options.apiEndpoint}?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.results = data.results || [];
            this.totalPages = Math.ceil((data.total || 0) / this.options.maxResults);
            
            this.renderResults();
            this.renderPagination();
            this.updateResultsCount(data.total || 0);
            
        } catch (error) {
            console.error('Erro ao aplicar filtros:', error);
            this.showError('Erro ao carregar resultados. Tente novamente.');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }
    
    renderResults() {
        const container = document.querySelector('.results-list');
        const emptyContainer = document.querySelector('.results-empty');
        
        if (this.results.length === 0) {
            container.style.display = 'none';
            emptyContainer.style.display = 'block';
            return;
        }
        
        container.style.display = 'block';
        emptyContainer.style.display = 'none';
        
        const view = this.getCurrentView();
        
        if (view === 'grid') {
            this.renderGridView(container);
        } else {
            this.renderListView(container);
        }
    }
    
    renderListView(container) {
        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Status</th>
                            <th>Categoria</th>
                            <th>Data</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.results.map(item => `
                            <tr>
                                <td>
                                    <div class="d-flex align-items-center">
                                        ${item.avatar ? `<img src="${item.avatar}" class="avatar-sm rounded-circle me-2">` : ''}
                                        <div>
                                            <div class="fw-semibold">${item.name}</div>
                                            ${item.description ? `<small class="text-muted">${item.description}</small>` : ''}
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getStatusColor(item.status)}">
                                        ${item.status}
                                    </span>
                                </td>
                                <td>${item.category || '-'}</td>
                                <td>${this.formatDate(item.created_at)}</td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button type="button" class="btn btn-outline-primary" onclick="window.filtersInstance.viewItem(${item.id})">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary" onclick="window.filtersInstance.editItem(${item.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderGridView(container) {
        container.innerHTML = `
            <div class="row">
                ${this.results.map(item => `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card h-100">
                            ${item.image ? `
                                <img src="${item.image}" class="card-img-top" style="height: 200px; object-fit: cover;">
                            ` : ''}
                            <div class="card-body">
                                <h6 class="card-title">${item.name}</h6>
                                <p class="card-text text-muted small">${item.description || ''}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-${this.getStatusColor(item.status)}">
                                        ${item.status}
                                    </span>
                                    <small class="text-muted">${this.formatDate(item.created_at)}</small>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="btn-group w-100">
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="window.filtersInstance.viewItem(${item.id})">
                                        <i class="fas fa-eye"></i> Ver
                                    </button>
                                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="window.filtersInstance.editItem(${item.id})">
                                        <i class="fas fa-edit"></i> Editar
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderPagination() {
        const container = document.querySelector('.results-pagination');
        
        if (this.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const pagination = [];
        const current = this.currentPage;
        const total = this.totalPages;
        
        // Primeira página
        if (current > 3) {
            pagination.push(`<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`);
            if (current > 4) {
                pagination.push(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
            }
        }
        
        // Páginas próximas
        for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
            const active = i === current ? 'active' : '';
            pagination.push(`<li class="page-item ${active}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`);
        }
        
        // Última página
        if (current < total - 2) {
            if (current < total - 3) {
                pagination.push(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
            }
            pagination.push(`<li class="page-item"><a class="page-link" href="#" data-page="${total}">${total}</a></li>`);
        }
        
        container.innerHTML = `
            <nav>
                <ul class="pagination justify-content-center">
                    <li class="page-item ${current === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${current - 1}">Anterior</a>
                    </li>
                    ${pagination.join('')}
                    <li class="page-item ${current === total ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${current + 1}">Próximo</a>
                    </li>
                </ul>
            </nav>
        `;
        
        // Bind eventos de paginação
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    this.applyFilters();
                }
            });
        });
    }
    
    updateResultsCount(total) {
        document.querySelector('.results-count').textContent = `${total} resultado${total !== 1 ? 's' : ''}`;
    }
    
    showLoading(show) {
        const loading = document.querySelector('.results-loading');
        const count = document.querySelector('.results-count');
        
        if (show) {
            loading.style.display = 'block';
            count.style.display = 'none';
        } else {
            loading.style.display = 'none';
            count.style.display = 'block';
        }
    }
    
    showError(message) {
        const container = document.querySelector('.results-container');
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    }
    
    toggleAdvancedFilters() {
        const advanced = document.querySelector('.filters-advanced');
        const toggle = document.getElementById('toggleAdvanced');
        const icon = toggle.querySelector('i');
        
        if (advanced.style.display === 'none') {
            advanced.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
            toggle.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar Filtros Avançados';
        } else {
            advanced.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
            toggle.innerHTML = '<i class="fas fa-chevron-down"></i> Filtros Avançados';
        }
    }
    
    setView(view) {
        const gridBtn = document.getElementById('viewGrid');
        const listBtn = document.getElementById('viewList');
        
        if (view === 'grid') {
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
        } else {
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
        }
        
        localStorage.setItem('filters_view', view);
        this.renderResults();
    }
    
    getCurrentView() {
        return localStorage.getItem('filters_view') || 'list';
    }
    
    saveFilters() {
        const name = prompt('Nome para este conjunto de filtros:');
        if (!name) return;
        
        const savedFilters = JSON.parse(localStorage.getItem('saved_filters') || '[]');
        const filterData = {
            id: Date.now(),
            name: name,
            filters: Object.fromEntries(this.filters),
            created_at: new Date().toISOString()
        };
        
        savedFilters.push(filterData);
        localStorage.setItem('saved_filters', JSON.stringify(savedFilters));
        
        this.showNotification('Filtros salvos com sucesso!', 'success');
    }
    
    loadSavedFilters() {
        const savedFilters = JSON.parse(localStorage.getItem('saved_filters') || '[]');
        if (savedFilters.length === 0) return;
        
        // Adicionar dropdown de filtros salvos
        const headerActions = document.querySelector('.filters-actions');
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown';
        dropdown.innerHTML = `
            <button class="btn btn-sm btn-outline-info dropdown-toggle" type="button" data-bs-toggle="dropdown">
                <i class="fas fa-bookmark"></i> Salvos
            </button>
            <ul class="dropdown-menu">
                ${savedFilters.map(filter => `
                    <li>
                        <a class="dropdown-item" href="#" onclick="window.filtersInstance.loadFilter(${filter.id})">
                            ${filter.name}
                        </a>
                    </li>
                `).join('')}
                <li><hr class="dropdown-divider"></li>
                <li>
                    <a class="dropdown-item text-danger" href="#" onclick="window.filtersInstance.clearSavedFilters()">
                        <i class="fas fa-trash"></i> Limpar Salvos
                    </a>
                </li>
            </ul>
        `;
        
        headerActions.insertBefore(dropdown, headerActions.firstChild);
    }
    
    loadFilter(filterId) {
        const savedFilters = JSON.parse(localStorage.getItem('saved_filters') || '[]');
        const filter = savedFilters.find(f => f.id === filterId);
        
        if (!filter) return;
        
        this.clearFilters();
        
        Object.entries(filter.filters).forEach(([key, value]) => {
            this.setFilter(key, value);
            
            // Atualizar campos do formulário
            const field = document.getElementById(key + 'Filter') || document.getElementById(key);
            if (field) {
                field.value = value;
            }
        });
        
        this.applyFilters();
        this.showNotification(`Filtros "${filter.name}" carregados!`, 'info');
    }
    
    clearSavedFilters() {
        if (confirm('Deseja realmente limpar todos os filtros salvos?')) {
            localStorage.removeItem('saved_filters');
            location.reload();
        }
    }
    
    async exportResults() {
        if (this.results.length === 0) {
            this.showNotification('Nenhum resultado para exportar', 'warning');
            return;
        }
        
        try {
            const params = new URLSearchParams();
            this.filters.forEach((value, key) => {
                params.append(key, value);
            });
            params.append('format', 'csv');
            params.append('export', 'true');
            
            const response = await fetch(`${this.options.apiEndpoint}?${params}`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `resultados_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Exportação concluída!', 'success');
            
        } catch (error) {
            console.error('Erro na exportação:', error);
            this.showNotification('Erro ao exportar resultados', 'danger');
        }
    }
    
    // Métodos utilitários
    getStatusColor(status) {
        const colors = {
            'ATIVO': 'success',
            'INATIVO': 'secondary',
            'PENDENTE': 'warning',
            'CONCLUIDO': 'primary',
            'CANCELADO': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Métodos para sobrescrever em implementações específicas
    viewItem(id) {
        console.log('View item:', id);
        // Implementar navegação para visualização
    }
    
    editItem(id) {
        console.log('Edit item:', id);
        // Implementar navegação para edição
    }
}

// Inicialização global
window.AdvancedFilters = AdvancedFilters;

// Função para inicializar os filtros
function initAdvancedFilters(containerId, options = {}) {
    window.filtersInstance = new AdvancedFilters(containerId, options);
    return window.filtersInstance;
}

// Exportar para uso como módulo
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedFilters;
}
