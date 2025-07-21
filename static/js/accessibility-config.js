/**
 * Configuração de Acessibilidade
 * Gerencia preferências e configurações de acessibilidade do usuário
 */

class AccessibilityConfig {
    constructor() {
        this.preferences = {
            highContrast: false,
            reducedMotion: false,
            fontSize: 'normal',
            screenReader: false,
            keyboardNavigation: true
        };
        
        this.loadPreferences();
        this.applyPreferences();
    }

    loadPreferences() {
        // Carregar preferências do localStorage
        const saved = localStorage.getItem('accessibility-preferences');
        if (saved) {
            this.preferences = { ...this.preferences, ...JSON.parse(saved) };
        }

        // Detectar preferências do sistema
        this.detectSystemPreferences();
    }

    detectSystemPreferences() {
        // Detectar preferência de movimento reduzido
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.preferences.reducedMotion = true;
        }

        // Detectar preferência de alto contraste
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            this.preferences.highContrast = true;
        }

        // Detectar se está usando leitor de tela
        if (window.speechSynthesis) {
            this.preferences.screenReader = true;
        }

        // Monitorar mudanças nas preferências do sistema
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.preferences.reducedMotion = e.matches;
            this.applyPreferences();
        });

        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.preferences.highContrast = e.matches;
            this.applyPreferences();
        });
    }

    applyPreferences() {
        const body = document.body;

        // Aplicar alto contraste
        if (this.preferences.highContrast) {
            body.classList.add('high-contrast-mode');
        } else {
            body.classList.remove('high-contrast-mode');
        }

        // Aplicar movimento reduzido
        if (this.preferences.reducedMotion) {
            body.classList.add('reduced-motion');
        } else {
            body.classList.remove('reduced-motion');
        }

        // Aplicar tamanho da fonte
        body.classList.remove('font-small', 'font-normal', 'font-large', 'font-xlarge');
        body.classList.add(`font-${this.preferences.fontSize}`);

        // Aplicar configurações de navegação por teclado
        if (this.preferences.keyboardNavigation) {
            body.classList.add('keyboard-navigation');
        } else {
            body.classList.remove('keyboard-navigation');
        }
    }

    savePreferences() {
        localStorage.setItem('accessibility-preferences', JSON.stringify(this.preferences));
    }

    setPreference(key, value) {
        this.preferences[key] = value;
        this.applyPreferences();
        this.savePreferences();
        
        // Anunciar mudança para leitores de tela
        this.announceChange(key, value);
    }

    announceChange(key, value) {
        const messages = {
            highContrast: value ? 'Alto contraste ativado' : 'Alto contraste desativado',
            reducedMotion: value ? 'Movimento reduzido ativado' : 'Movimento reduzido desativado',
            fontSize: `Tamanho da fonte alterado para ${value}`,
            screenReader: value ? 'Modo leitor de tela ativado' : 'Modo leitor de tela desativado',
            keyboardNavigation: value ? 'Navegação por teclado ativada' : 'Navegação por teclado desativada'
        };

        if (window.accessibilityManager) {
            window.accessibilityManager.announce(messages[key] || 'Configuração alterada');
        }
    }

    getPreference(key) {
        return this.preferences[key];
    }

    getAllPreferences() {
        return { ...this.preferences };
    }

    resetPreferences() {
        this.preferences = {
            highContrast: false,
            reducedMotion: false,
            fontSize: 'normal',
            screenReader: false,
            keyboardNavigation: true
        };
        
        this.applyPreferences();
        this.savePreferences();
        
        if (window.accessibilityManager) {
            window.accessibilityManager.announce('Configurações de acessibilidade resetadas');
        }
    }

    // Métodos de conveniência
    toggleHighContrast() {
        this.setPreference('highContrast', !this.preferences.highContrast);
    }

    toggleReducedMotion() {
        this.setPreference('reducedMotion', !this.preferences.reducedMotion);
    }

    increaseFontSize() {
        const sizes = ['small', 'normal', 'large', 'xlarge'];
        const current = sizes.indexOf(this.preferences.fontSize);
        const next = Math.min(current + 1, sizes.length - 1);
        this.setPreference('fontSize', sizes[next]);
    }

    decreaseFontSize() {
        const sizes = ['small', 'normal', 'large', 'xlarge'];
        const current = sizes.indexOf(this.preferences.fontSize);
        const prev = Math.max(current - 1, 0);
        this.setPreference('fontSize', sizes[prev]);
    }

    // Criar interface de controle de acessibilidade
    createAccessibilityPanel() {
        const panel = document.createElement('div');
        panel.id = 'accessibility-panel';
        panel.className = 'accessibility-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-labelledby', 'accessibility-panel-title');
        panel.setAttribute('aria-modal', 'true');
        
        panel.innerHTML = `
            <div class="accessibility-panel-header">
                <h3 id="accessibility-panel-title">Configurações de Acessibilidade</h3>
                <button type="button" class="accessibility-panel-close" aria-label="Fechar painel">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
            
            <div class="accessibility-panel-content">
                <div class="accessibility-option">
                    <label class="accessibility-label">
                        <input type="checkbox" id="toggle-high-contrast" ${this.preferences.highContrast ? 'checked' : ''}>
                        <span>Alto Contraste</span>
                    </label>
                </div>
                
                <div class="accessibility-option">
                    <label class="accessibility-label">
                        <input type="checkbox" id="toggle-reduced-motion" ${this.preferences.reducedMotion ? 'checked' : ''}>
                        <span>Movimento Reduzido</span>
                    </label>
                </div>
                
                <div class="accessibility-option">
                    <label class="accessibility-label">
                        <span>Tamanho da Fonte</span>
                        <select id="font-size-selector">
                            <option value="small" ${this.preferences.fontSize === 'small' ? 'selected' : ''}>Pequeno</option>
                            <option value="normal" ${this.preferences.fontSize === 'normal' ? 'selected' : ''}>Normal</option>
                            <option value="large" ${this.preferences.fontSize === 'large' ? 'selected' : ''}>Grande</option>
                            <option value="xlarge" ${this.preferences.fontSize === 'xlarge' ? 'selected' : ''}>Muito Grande</option>
                        </select>
                    </label>
                </div>
                
                <div class="accessibility-option">
                    <label class="accessibility-label">
                        <input type="checkbox" id="toggle-keyboard-nav" ${this.preferences.keyboardNavigation ? 'checked' : ''}>
                        <span>Navegação por Teclado</span>
                    </label>
                </div>
                
                <div class="accessibility-actions">
                    <button type="button" id="reset-preferences" class="accessibility-button">
                        Restaurar Padrões
                    </button>
                </div>
            </div>
        `;
        
        // Adicionar event listeners
        panel.querySelector('#toggle-high-contrast').addEventListener('change', (e) => {
            this.setPreference('highContrast', e.target.checked);
        });
        
        panel.querySelector('#toggle-reduced-motion').addEventListener('change', (e) => {
            this.setPreference('reducedMotion', e.target.checked);
        });
        
        panel.querySelector('#font-size-selector').addEventListener('change', (e) => {
            this.setPreference('fontSize', e.target.value);
        });
        
        panel.querySelector('#toggle-keyboard-nav').addEventListener('change', (e) => {
            this.setPreference('keyboardNavigation', e.target.checked);
        });
        
        panel.querySelector('#reset-preferences').addEventListener('click', () => {
            this.resetPreferences();
            this.updatePanel();
        });
        
        panel.querySelector('.accessibility-panel-close').addEventListener('click', () => {
            this.closePanel();
        });
        
        return panel;
    }

    openPanel() {
        let panel = document.getElementById('accessibility-panel');
        if (!panel) {
            panel = this.createAccessibilityPanel();
            document.body.appendChild(panel);
        }
        
        panel.style.display = 'block';
        panel.querySelector('.accessibility-panel-close').focus();
    }

    closePanel() {
        const panel = document.getElementById('accessibility-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    updatePanel() {
        const panel = document.getElementById('accessibility-panel');
        if (panel) {
            panel.querySelector('#toggle-high-contrast').checked = this.preferences.highContrast;
            panel.querySelector('#toggle-reduced-motion').checked = this.preferences.reducedMotion;
            panel.querySelector('#font-size-selector').value = this.preferences.fontSize;
            panel.querySelector('#toggle-keyboard-nav').checked = this.preferences.keyboardNavigation;
        }
    }
}

// Inicializar configuração de acessibilidade
document.addEventListener('DOMContentLoaded', () => {
    window.accessibilityConfig = new AccessibilityConfig();
    
    // Adicionar botão de acessibilidade
    const accessibilityButton = document.createElement('button');
    accessibilityButton.id = 'accessibility-button';
    accessibilityButton.className = 'accessibility-button fixed';
    accessibilityButton.innerHTML = '♿ Acessibilidade';
    accessibilityButton.setAttribute('aria-label', 'Abrir configurações de acessibilidade');
    accessibilityButton.addEventListener('click', () => {
        window.accessibilityConfig.openPanel();
    });
    
    document.body.appendChild(accessibilityButton);
});

// Exportar para uso em outros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityConfig;
}
