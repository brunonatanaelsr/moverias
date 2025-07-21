"""
Sistema integrado de upload com validação avançada e notificações.
"""
import os
import hashlib
import magic
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class UploadedFile(models.Model):
    """Modelo para rastrear arquivos enviados"""
    
    UPLOAD_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhado'),
        ('virus_detected', 'Vírus Detectado'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('document', 'Documento'),
        ('image', 'Imagem'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('other', 'Outro'),
    ]
    
    # Informações básicas
    original_filename = models.CharField(max_length=255, verbose_name="Nome Original")
    sanitized_filename = models.CharField(max_length=255, verbose_name="Nome Sanitizado")
    file_path = models.CharField(max_length=500, verbose_name="Caminho do Arquivo")
    
    # Metadados
    file_size = models.PositiveIntegerField(verbose_name="Tamanho (bytes)")
    mime_type = models.CharField(max_length=100, verbose_name="Tipo MIME")
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, verbose_name="Tipo")
    file_hash = models.CharField(max_length=64, unique=True, verbose_name="Hash SHA-256")
    
    # Status e controle
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Enviado por")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Upload")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Processado em")
    
    # Validação e segurança
    virus_scan_result = models.JSONField(default=dict, verbose_name="Resultado do Scan")
    validation_errors = models.JSONField(default=list, verbose_name="Erros de Validação")
    
    # Metadados adicionais
    description = models.TextField(blank=True, verbose_name="Descrição")
    tags = models.CharField(max_length=500, blank=True, verbose_name="Tags")
    is_public = models.BooleanField(default=False, verbose_name="Público")
    
    # Relacionamento genérico (para associar a qualquer modelo)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Tipo de Conteúdo"
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID do Objeto")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        verbose_name = "Arquivo Enviado"
        verbose_name_plural = "Arquivos Enviados"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-uploaded_at']),
            models.Index(fields=['status']),
            models.Index(fields=['file_type']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_by.username})"
    
    @property
    def file_url(self):
        """URL para acessar o arquivo"""
        if self.file_path:
            return default_storage.url(self.file_path)
        return None
    
    @property
    def file_size_human(self):
        """Tamanho do arquivo em formato legível"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def mark_as_processed(self):
        """Marcar arquivo como processado"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, errors):
        """Marcar arquivo como falhado"""
        self.status = 'failed'
        self.validation_errors = errors if isinstance(errors, list) else [str(errors)]
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'validation_errors', 'processed_at'])
    
    def delete_file(self):
        """Excluir arquivo físico"""
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)
    
    def get_icon_class(self):
        """Retorna a classe do ícone baseada no tipo de arquivo"""
        extension = self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''
        
        icon_map = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'ppt': 'fa-file-powerpoint',
            'pptx': 'fa-file-powerpoint',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'svg': 'fa-file-image',
            'txt': 'fa-file-alt',
            'csv': 'fa-file-csv',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive',
            '7z': 'fa-file-archive',
            'mp3': 'fa-file-audio',
            'wav': 'fa-file-audio',
            'mp4': 'fa-file-video',
            'avi': 'fa-file-video',
            'mov': 'fa-file-video',
        }
        
        return icon_map.get(extension, 'fa-file')
    
    def get_color_class(self):
        """Retorna a classe de cor baseada no tipo de arquivo"""
        extension = self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''
        
        color_map = {
            'pdf': 'text-red-500',
            'doc': 'text-blue-500',
            'docx': 'text-blue-500',
            'xls': 'text-green-500',
            'xlsx': 'text-green-500',
            'ppt': 'text-orange-500',
            'pptx': 'text-orange-500',
            'jpg': 'text-purple-500',
            'jpeg': 'text-purple-500',
            'png': 'text-purple-500',
            'gif': 'text-purple-500',
            'svg': 'text-purple-500',
            'txt': 'text-gray-500',
            'csv': 'text-yellow-500',
            'zip': 'text-indigo-500',
            'rar': 'text-indigo-500',
            '7z': 'text-indigo-500',
            'mp3': 'text-pink-500',
            'wav': 'text-pink-500',
            'mp4': 'text-red-600',
            'avi': 'text-red-600',
            'mov': 'text-red-600',
        }
        
        return color_map.get(extension, 'text-gray-400')
    
    @property 
    def file(self):
        """Propriedade para compatibilidade com templates que esperam file.url"""
        class FileProxy:
            def __init__(self, file_path):
                self.file_path = file_path
                
            @property
            def url(self):
                if self.file_path:
                    return default_storage.url(self.file_path)
                return None
                
            @property
            def name(self):
                return self.file_path or ''
        
        return FileProxy(self.file_path)
    
    @property
    def download_count(self):
        """Contador de downloads (placeholder para funcionalidade futura)"""
        return getattr(self, '_download_count', 0)


class IntegratedFileUploadHandler:
    """Handler integrado para upload de arquivos com validação avançada"""
    
    def __init__(self, user, **config):
        self.user = user
        self.config = {
            'max_size': 50 * 1024 * 1024,  # 50MB
            'allowed_types': ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'csv'],
            'enable_virus_scan': True,
            'enable_duplicate_check': True,
            'enable_notifications': True,
            'quarantine_suspicious': True,
            **config
        }
    
    def process_upload(self, file_obj, description='', tags='', content_object=None):
        """Processar upload completo com validação e notificações"""
        try:
            # 1. Validações iniciais
            self._validate_file_basic(file_obj)
            
            # 2. Calcular hash
            file_hash = self._calculate_hash(file_obj)
            
            # 3. Verificar duplicatas
            if self.config['enable_duplicate_check']:
                duplicate = self._check_duplicate(file_hash)
                if duplicate:
                    return self._handle_duplicate(duplicate, file_obj)
            
            # 4. Sanitizar nome
            sanitized_name = self._sanitize_filename(file_obj.name)
            
            # 5. Detectar tipo de arquivo
            file_type = self._detect_file_type(file_obj)
            
            # 6. Salvar arquivo
            file_path = self._save_file(file_obj, sanitized_name)
            
            # 7. Criar registro no banco
            uploaded_file = UploadedFile.objects.create(
                original_filename=file_obj.name,
                sanitized_filename=sanitized_name,
                file_path=file_path,
                file_size=file_obj.size,
                mime_type=file_obj.content_type or 'application/octet-stream',
                file_type=file_type,
                file_hash=file_hash,
                uploaded_by=self.user,
                description=description,
                tags=tags,
                content_object=content_object,
                status='processing'
            )
            
            # 8. Validações avançadas (assíncrono)
            self._process_advanced_validation(uploaded_file)
            
            # 9. Notificar usuário
            if self.config['enable_notifications']:
                self._send_upload_notification(uploaded_file)
            
            return {
                'success': True,
                'file_id': uploaded_file.id,
                'file_url': uploaded_file.file_url,
                'message': 'Arquivo enviado com sucesso'
            }
            
        except Exception as e:
            logger.error(f"Erro no upload para usuário {self.user.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao processar arquivo'
            }
    
    def _validate_file_basic(self, file_obj):
        """Validações básicas do arquivo"""
        # Tamanho
        if file_obj.size > self.config['max_size']:
            raise ValueError(f"Arquivo muito grande. Máximo: {self.config['max_size']//1024//1024}MB")
        
        # Extensão
        extension = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
        if extension not in self.config['allowed_types']:
            raise ValueError(f"Tipo de arquivo não permitido: {extension}")
        
        # Nome do arquivo
        if not file_obj.name or len(file_obj.name) > 255:
            raise ValueError("Nome de arquivo inválido")
    
    def _calculate_hash(self, file_obj):
        """Calcular hash SHA-256 do arquivo"""
        hash_sha256 = hashlib.sha256()
        
        # Reset do ponteiro do arquivo
        file_obj.seek(0)
        
        # Ler em chunks para arquivos grandes
        for chunk in iter(lambda: file_obj.read(4096), b""):
            hash_sha256.update(chunk)
        
        # Reset do ponteiro
        file_obj.seek(0)
        
        return hash_sha256.hexdigest()
    
    def _check_duplicate(self, file_hash):
        """Verificar se arquivo já existe"""
        return UploadedFile.objects.filter(
            file_hash=file_hash,
            uploaded_by=self.user
        ).first()
    
    def _handle_duplicate(self, duplicate, file_obj):
        """Lidar com arquivo duplicado"""
        return {
            'success': False,
            'is_duplicate': True,
            'existing_file': {
                'id': duplicate.id,
                'filename': duplicate.original_filename,
                'uploaded_at': duplicate.uploaded_at.isoformat(),
                'url': duplicate.file_url
            },
            'message': 'Arquivo já existe'
        }
    
    def _sanitize_filename(self, filename):
        """Sanitizar nome do arquivo"""
        import re
        import unicodedata
        
        # Remover acentos
        filename = unicodedata.normalize('NFKD', filename)
        filename = filename.encode('ascii', 'ignore').decode('ascii')
        
        # Substituir caracteres especiais
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Múltiplos underscores
        filename = re.sub(r'_{2,}', '_', filename)
        
        # Remover underscores no início/fim
        filename = filename.strip('_')
        
        # Garantir que não está vazio
        if not filename:
            filename = f"file_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        return filename
    
    def _detect_file_type(self, file_obj):
        """Detectar tipo de arquivo baseado no conteúdo"""
        # Reset do ponteiro
        file_obj.seek(0)
        
        # Ler primeiros bytes
        header = file_obj.read(1024)
        file_obj.seek(0)
        
        # Usar python-magic se disponível
        try:
            mime_type = magic.from_buffer(header, mime=True)
            
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type in ['application/pdf', 'application/msword', 
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return 'document'
        except:
            pass
        
        # Fallback para extensão
        extension = os.path.splitext(file_obj.name)[1].lower()
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return 'image'
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.csv']:
            return 'document'
        elif extension in ['.mp4', '.avi', '.mov']:
            return 'video'
        elif extension in ['.mp3', '.wav', '.ogg']:
            return 'audio'
        
        return 'other'
    
    def _save_file(self, file_obj, sanitized_name):
        """Salvar arquivo no storage"""
        # Gerar caminho único
        timestamp = timezone.now().strftime('%Y/%m/%d')
        user_dir = f"uploads/{self.user.id}/{timestamp}"
        
        # Garantir nome único
        base_name, extension = os.path.splitext(sanitized_name)
        counter = 1
        final_name = sanitized_name
        
        while default_storage.exists(f"{user_dir}/{final_name}"):
            final_name = f"{base_name}_{counter}{extension}"
            counter += 1
        
        file_path = f"{user_dir}/{final_name}"
        
        # Salvar arquivo
        saved_path = default_storage.save(file_path, file_obj)
        
        return saved_path
    
    def _process_advanced_validation(self, uploaded_file):
        """Processamento avançado (assíncrono)"""
        try:
            # Scan de vírus (se habilitado)
            if self.config['enable_virus_scan']:
                scan_result = self._virus_scan(uploaded_file)
                uploaded_file.virus_scan_result = scan_result
                
                if not scan_result.get('clean', True):
                    uploaded_file.status = 'virus_detected'
                    uploaded_file.save()
                    self._quarantine_file(uploaded_file)
                    return
            
            # Validação de conteúdo específica por tipo
            self._validate_file_content(uploaded_file)
            
            # Marcar como concluído
            uploaded_file.mark_as_processed()
            
        except Exception as e:
            logger.error(f"Erro na validação avançada do arquivo {uploaded_file.id}: {e}")
            uploaded_file.mark_as_failed(str(e))
    
    def _virus_scan(self, uploaded_file):
        """Simular scan de vírus (implementar com ClamAV)"""
        # Placeholder para integração com antivírus
        return {
            'clean': True,
            'scanner': 'mock',
            'scanned_at': timezone.now().isoformat()
        }
    
    def _validate_file_content(self, uploaded_file):
        """Validar conteúdo específico por tipo"""
        if uploaded_file.file_type == 'image':
            self._validate_image_content(uploaded_file)
        elif uploaded_file.file_type == 'document':
            self._validate_document_content(uploaded_file)
    
    def _validate_image_content(self, uploaded_file):
        """Validar conteúdo de imagem"""
        try:
            from PIL import Image
            
            with default_storage.open(uploaded_file.file_path, 'rb') as f:
                img = Image.open(f)
                img.verify()  # Verificar integridade
                
        except Exception as e:
            raise ValueError(f"Imagem corrompida: {e}")
    
    def _validate_document_content(self, uploaded_file):
        """Validar conteúdo de documento"""
        # Verificar assinaturas de arquivo
        with default_storage.open(uploaded_file.file_path, 'rb') as f:
            header = f.read(10)
            
            # PDF
            if uploaded_file.original_filename.lower().endswith('.pdf'):
                if not header.startswith(b'%PDF'):
                    raise ValueError("Arquivo PDF inválido")
    
    def _quarantine_file(self, uploaded_file):
        """Colocar arquivo em quarentena"""
        quarantine_path = f"quarantine/{uploaded_file.file_path}"
        
        if default_storage.exists(uploaded_file.file_path):
            # Mover para quarentena
            with default_storage.open(uploaded_file.file_path, 'rb') as f:
                default_storage.save(quarantine_path, ContentFile(f.read()))
            
            # Remover original
            default_storage.delete(uploaded_file.file_path)
            
            # Atualizar caminho
            uploaded_file.file_path = quarantine_path
            uploaded_file.save()
    
    def _send_upload_notification(self, uploaded_file):
        """Enviar notificação de upload"""
        try:
            from notifications.realtime import create_and_send_notification
            
            create_and_send_notification(
                user=self.user,
                title="Arquivo Enviado",
                message=f"O arquivo '{uploaded_file.original_filename}' foi enviado com sucesso.",
                notification_type='success'
            )
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de upload: {e}")


def process_file_upload(request, file_field_name='file', **kwargs):
    """Função helper para processar upload em views"""
    if request.method != 'POST':
        return {'success': False, 'error': 'Método não permitido'}
    
    if file_field_name not in request.FILES:
        return {'success': False, 'error': 'Nenhum arquivo enviado'}
    
    file_obj = request.FILES[file_field_name]
    description = request.POST.get('description', '')
    tags = request.POST.get('tags', '')
    
    handler = IntegratedFileUploadHandler(request.user)
    return handler.process_upload(file_obj, description, tags, **kwargs)
