/**
 * Sistema de Progress Bars para Uploads
 * Integração com Django Forms e HTMX
 */

class UploadProgressSystem {
    constructor() {
        this.activeUploads = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.createProgressTemplate();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.bindUploadForms();
        });

        // HTMX integration
        document.addEventListener('htmx:afterSwap', () => {
            this.bindUploadForms();
        });
    }

    bindUploadForms() {
        // Bind to file input changes
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileSelection(e.target);
            });
        });

        // Bind to form submissions with file uploads
        document.querySelectorAll('form[enctype="multipart/form-data"]').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmission(e);
            });
        });

        // Bind to specific module forms
        this.bindModuleSpecificForms();
    }

    bindModuleSpecificForms() {
        // Formulários específicos por módulo
        const moduleFormSelectors = [
            // Core uploads
            '#upload-form',
            '#document-form',
            
            // Beneficiários
            '#beneficiary-form',
            '#beneficiary-document-form',
            
            // Workshops
            '#workshop-form',
            '#workshop-material-form',
            '#evaluation-form',
            
            // Projects
            '#project-form',
            '#project-document-form',
            '#enrollment-form',
            
            // Users
            '#user-form',
            '#user-avatar-form',
            
            // Certificates
            '#certificate-form',
            '#certificate-template-form',
            
            // Social
            '#anamnesis-form',
            '#social-document-form',
            
            // HR
            '#hr-document-form',
            '#employee-form'
        ];

        moduleFormSelectors.forEach(selector => {
            const form = document.querySelector(selector);
            if (form) {
                this.attachProgressToForm(form);
            }
        });

        // HTMX forms que podem ter upload de arquivos
        const htmxForms = document.querySelectorAll('form[hx-post], form[hx-put], form[hx-patch]');
        htmxForms.forEach(form => {
            const fileInputs = form.querySelectorAll('input[type="file"]');
            if (fileInputs.length > 0) {
                this.attachProgressToForm(form);
            }
        });
    }

    attachProgressToForm(form) {
        // Anexar eventos de progresso a formulários específicos
        const fileInputs = form.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileSelection(e.target);
            });
        });

        form.addEventListener('submit', (e) => {
            this.handleFormSubmission(e);
        });
    }

    handleFileSelection(fileInput) {
        const files = Array.from(fileInput.files);
        const container = this.findOrCreateProgressContainer(fileInput);
        
        files.forEach(file => {
            this.createFilePreview(file, container);
        });
    }

    handleFormSubmission(event) {
        const form = event.target;
        const fileInputs = form.querySelectorAll('input[type="file"]');
        
        if (fileInputs.length === 0) return;

        // Check if form has files
        const hasFiles = Array.from(fileInputs).some(input => input.files.length > 0);
        if (!hasFiles) return;

        // Prevent default submission
        event.preventDefault();

        // Start upload with progress
        this.uploadWithProgress(form);
    }

    async uploadWithProgress(form) {
        const formData = new FormData(form);
        const uploadId = this.generateUploadId();
        const progressContainer = this.findOrCreateProgressContainer(form);
        
        // Create main progress bar
        const mainProgress = this.createProgressBar(uploadId, 'Enviando arquivos...');
        progressContainer.appendChild(mainProgress);

        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Enviando...';

        try {
            const response = await this.uploadWithProgressTracking(form.action, formData, uploadId);
            
            if (response.ok) {
                this.showSuccess(progressContainer, 'Upload concluído com sucesso!');
                
                // Redirect or update page
                const result = await response.json();
                if (result.redirect) {
                    window.location.href = result.redirect;
                } else if (result.reload) {
                    window.location.reload();
                }
            } else {
                throw new Error('Erro no upload');
            }
        } catch (error) {
            this.showError(progressContainer, 'Erro no upload: ' + error.message);
        } finally {
            // Restore submit button
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    }

    uploadWithProgressTracking(url, formData, uploadId) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(uploadId, percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(xhr);
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Erro de rede'));
            });

            xhr.addEventListener('abort', () => {
                reject(new Error('Upload cancelado'));
            });

            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            formData.append('csrfmiddlewaretoken', csrfToken);

            xhr.open('POST', url);
            xhr.send(formData);
        });
    }

    createProgressBar(id, label) {
        const container = document.createElement('div');
        container.className = 'progress-item mb-4';
        container.dataset.uploadId = id;

        container.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">${label}</span>
                <span class="text-sm text-gray-500 progress-percentage">0%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 progress-bar" 
                     style="width: 0%"></div>
            </div>
            <div class="mt-2 text-xs text-gray-500 progress-status">Preparando...</div>
        `;

        return container;
    }

    createFilePreview(file, container) {
        const previewId = this.generateUploadId();
        const preview = document.createElement('div');
        preview.className = 'file-preview bg-gray-50 p-3 rounded-lg mb-3';
        preview.dataset.fileId = previewId;

        const fileSize = this.formatFileSize(file.size);
        const fileIcon = this.getFileIcon(file.type);

        preview.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0 mr-3">
                    <i class="fas ${fileIcon} text-gray-400 text-lg"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${file.name}</p>
                    <p class="text-xs text-gray-500">${fileSize}</p>
                </div>
                <div class="flex-shrink-0">
                    <button type="button" class="text-red-400 hover:text-red-600 remove-file"
                            onclick="this.closest('.file-preview').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        container.appendChild(preview);
    }

    updateProgress(uploadId, percentage) {
        const container = document.querySelector(`[data-upload-id="${uploadId}"]`);
        if (!container) return;

        const progressBar = container.querySelector('.progress-bar');
        const progressText = container.querySelector('.progress-percentage');
        const statusText = container.querySelector('.progress-status');

        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${Math.round(percentage)}%`;

        if (percentage < 100) {
            statusText.textContent = 'Enviando...';
            progressBar.className = 'bg-blue-600 h-2.5 rounded-full transition-all duration-300 progress-bar';
        } else {
            statusText.textContent = 'Processando...';
            progressBar.className = 'bg-green-600 h-2.5 rounded-full transition-all duration-300 progress-bar';
        }
    }

    showSuccess(container, message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'mt-4 p-4 bg-green-50 border border-green-200 rounded-lg';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                <span class="text-green-800">${message}</span>
            </div>
        `;
        container.appendChild(successDiv);
    }

    showError(container, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'mt-4 p-4 bg-red-50 border border-red-200 rounded-lg';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
                <span class="text-red-800">${message}</span>
            </div>
        `;
        container.appendChild(errorDiv);
    }

    findOrCreateProgressContainer(element) {
        // Look for existing container
        let container = element.closest('.upload-form-container')?.querySelector('.upload-progress-container');
        
        if (!container) {
            // Create new container
            container = document.createElement('div');
            container.className = 'upload-progress-container mt-4';
            
            // Insert after the form or file input
            const target = element.closest('form') || element.closest('.form-group') || element;
            target.parentNode.insertBefore(container, target.nextSibling);
        }

        return container;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getFileIcon(mimeType) {
        if (mimeType.startsWith('image/')) return 'fa-image';
        if (mimeType.startsWith('video/')) return 'fa-video';
        if (mimeType.startsWith('audio/')) return 'fa-music';
        if (mimeType.includes('pdf')) return 'fa-file-pdf';
        if (mimeType.includes('word')) return 'fa-file-word';
        if (mimeType.includes('excel')) return 'fa-file-excel';
        if (mimeType.includes('powerpoint')) return 'fa-file-powerpoint';
        if (mimeType.includes('zip') || mimeType.includes('rar')) return 'fa-file-archive';
        return 'fa-file';
    }

    generateUploadId() {
        return 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    createProgressTemplate() {
        // Add CSS if not already present
        if (!document.getElementById('upload-progress-styles')) {
            const style = document.createElement('style');
            style.id = 'upload-progress-styles';
            style.textContent = `
                .upload-progress-container {
                    transition: all 0.3s ease;
                }
                
                .progress-item {
                    animation: slideIn 0.3s ease-out;
                }
                
                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .file-preview {
                    transition: all 0.2s ease;
                }
                
                .file-preview:hover {
                    background-color: #f9fafb;
                }
                
                .remove-file {
                    transition: all 0.2s ease;
                }
                
                .remove-file:hover {
                    transform: scale(1.1);
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Initialize the upload progress system
document.addEventListener('DOMContentLoaded', () => {
    window.uploadProgressSystem = new UploadProgressSystem();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UploadProgressSystem;
}
