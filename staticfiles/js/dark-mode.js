/**
 * Dark Mode System
 * MoveMarias - Dark/Light theme toggle functionality
 */

class DarkModeManager {
    constructor() {
        this.darkMode = localStorage.getItem('darkMode') === 'true';
        this.init();
    }
    
    init() {
        // Apply initial theme
        this.applyTheme();
        
        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (!localStorage.getItem('darkMode')) {
                this.darkMode = e.matches;
                this.applyTheme();
            }
        });
        
        // Create toggle button if it doesn't exist
        this.createToggleButton();
    }
    
    applyTheme() {
        const html = document.documentElement;
        
        if (this.darkMode) {
            html.classList.add('dark');
            html.setAttribute('data-theme', 'dark');
        } else {
            html.classList.remove('dark');
            html.setAttribute('data-theme', 'light');
        }
        
        // Update meta theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.content = this.darkMode ? '#1f2937' : '#ffffff';
        }
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themechange', {
            detail: { darkMode: this.darkMode }
        }));
    }
    
    toggle() {
        this.darkMode = !this.darkMode;
        localStorage.setItem('darkMode', this.darkMode);
        this.applyTheme();
        
        // Show toast notification
        if (window.Alpine && window.Alpine.store) {
            const message = this.darkMode ? 'Modo escuro ativado' : 'Modo claro ativado';
            window.Alpine.store('global').showToast(message, 'info', 2000);
        }
    }
    
    createToggleButton() {
        const existingButton = document.querySelector('[data-dark-mode-toggle]');
        if (existingButton) {
            existingButton.addEventListener('click', () => this.toggle());
            return;
        }
        
        // Create floating toggle button
        const button = document.createElement('button');
        button.className = 'fixed bottom-4 right-4 w-12 h-12 bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 z-50 flex items-center justify-center';
        button.innerHTML = `
            <i class="fas fa-sun dark:hidden"></i>
            <i class="fas fa-moon hidden dark:block"></i>
        `;
        button.setAttribute('data-dark-mode-toggle', '');
        button.setAttribute('aria-label', 'Alternar modo escuro/claro');
        
        button.addEventListener('click', () => this.toggle());
        document.body.appendChild(button);
    }
    
    // Public methods
    isDarkMode() {
        return this.darkMode;
    }
    
    setDarkMode(enabled) {
        this.darkMode = enabled;
        localStorage.setItem('darkMode', enabled);
        this.applyTheme();
    }
    
    getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
}

// Initialize dark mode manager
const darkModeManager = new DarkModeManager();

// Global functions
window.toggleDarkMode = () => darkModeManager.toggle();
window.setDarkMode = (enabled) => darkModeManager.setDarkMode(enabled);
window.isDarkMode = () => darkModeManager.isDarkMode();

// Theme-aware image loading
document.addEventListener('DOMContentLoaded', () => {
    const themeImages = document.querySelectorAll('[data-theme-src]');
    
    function updateThemeImages() {
        themeImages.forEach(img => {
            const lightSrc = img.dataset.lightSrc;
            const darkSrc = img.dataset.darkSrc;
            
            if (lightSrc && darkSrc) {
                img.src = darkModeManager.isDarkMode() ? darkSrc : lightSrc;
            }
        });
    }
    
    // Update images on theme change
    window.addEventListener('themechange', updateThemeImages);
    
    // Initial update
    updateThemeImages();
});

// CSS custom properties for theme
document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    
    function updateCSSVariables() {
        if (darkModeManager.isDarkMode()) {
            root.style.setProperty('--bg-primary', '#1f2937');
            root.style.setProperty('--bg-secondary', '#374151');
            root.style.setProperty('--text-primary', '#f9fafb');
            root.style.setProperty('--text-secondary', '#d1d5db');
            root.style.setProperty('--border-color', '#4b5563');
        } else {
            root.style.setProperty('--bg-primary', '#ffffff');
            root.style.setProperty('--bg-secondary', '#f9fafb');
            root.style.setProperty('--text-primary', '#111827');
            root.style.setProperty('--text-secondary', '#6b7280');
            root.style.setProperty('--border-color', '#e5e7eb');
        }
    }
    
    // Update CSS variables on theme change
    window.addEventListener('themechange', updateCSSVariables);
    
    // Initial update
    updateCSSVariables();
});

console.log('Dark mode system initialized');
