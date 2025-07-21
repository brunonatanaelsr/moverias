"""
Sistema de upload seguro de arquivos para o MoveMarias
Implementa validação de tipos, tamanhos e proteção contra malware
"""

import os
import mimetypes
import hashlib
from typing import List, Optional, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone

# Importação condicional do magic
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class SecureFileUploader:
    """
    Classe para upload seguro de arquivos com validação e proteção
    """
    
    # Tipos de arquivo permitidos
    ALLOWED_FILE_TYPES = {
        'image': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'mimetypes': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'max_size': 5 * 1024 * 1024,  # 5MB
        },
        'document': {
            'extensions': ['.pdf', '.doc', '.docx', '.txt', '.odt'],
            'mimetypes': [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain',
                'application/vnd.oasis.opendocument.text'
            ],
            'max_size': 10 * 1024 * 1024,  # 10MB
        },
        'spreadsheet': {
            'extensions': ['.xls', '.xlsx', '.csv', '.ods'],
            'mimetypes': [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/vnd.oasis.opendocument.spreadsheet'
            ],
            'max_size': 10 * 1024 * 1024,  # 10MB
        },
        'video': {
            'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.webm'],
            'mimetypes': [
                'video/mp4',
                'video/x-msvideo',
                'video/quicktime',
                'video/x-ms-wmv',
                'video/webm'
            ],
            'max_size': 100 * 1024 * 1024,  # 100MB
        },
        'audio': {
            'extensions': ['.mp3', '.wav', '.ogg', '.m4a'],
            'mimetypes': [
                'audio/mpeg',
                'audio/wav',
                'audio/ogg',
                'audio/mp4'
            ],
            'max_size': 50 * 1024 * 1024,  # 50MB
        }
    }
    
    # Assinaturas de arquivo maliciosas (magic bytes)
    MALICIOUS_SIGNATURES = [
        b'MZ',  # Windows executable
        b'PK\x03\x04',  # ZIP (pode conter executáveis)
        b'\x7fELF',  # Linux executable
        b'\xfe\xed\xfa',  # macOS executable
    ]
    
    def __init__(self, upload_type: str = 'document'):
        """
        Inicializa o uploader com o tipo de arquivo especificado
        
        Args:
            upload_type: Tipo de arquivo ('image', 'document', 'spreadsheet', 'video', 'audio')
        """
        if upload_type not in self.ALLOWED_FILE_TYPES:
            raise ValueError(f"Tipo de upload '{upload_type}' não é válido")
        
        self.upload_type = upload_type
        self.config = self.ALLOWED_FILE_TYPES[upload_type]
    
    def validate_file(self, uploaded_file: UploadedFile) -> Tuple[bool, str]:
        """
        Valida um arquivo enviado
        
        Args:
            uploaded_file: Arquivo enviado
            
        Returns:
            Tuple com (é_válido, mensagem_erro)
        """
        try:
            # Validar tamanho
            if not self._validate_size(uploaded_file):
                return False, f"Arquivo muito grande. Tamanho máximo: {self._format_size(self.config['max_size'])}"
            
            # Validar extensão
            if not self._validate_extension(uploaded_file.name):
                return False, f"Extensão não permitida. Extensões aceitas: {', '.join(self.config['extensions'])}"
            
            # Validar MIME type
            if not self._validate_mimetype(uploaded_file):
                return False, "Tipo de arquivo não permitido"
            
            # Validar conteúdo (magic bytes)
            if not self._validate_content(uploaded_file):
                return False, "Conteúdo do arquivo não é válido ou pode ser malicioso"
            
            # Verificar assinaturas maliciosas
            if self._check_malicious_signatures(uploaded_file):
                return False, "Arquivo contém assinaturas maliciosas"
            
            return True, "Arquivo válido"
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    def upload_file(self, uploaded_file: UploadedFile, subfolder: str = '') -> dict:
        """
        Faz upload de um arquivo validado
        
        Args:
            uploaded_file: Arquivo a ser enviado
            subfolder: Subpasta de destino
            
        Returns:
            Dicionário com informações do arquivo salvo
        """
        # Validar arquivo
        is_valid, error_message = self.validate_file(uploaded_file)
        if not is_valid:
            raise ValidationError(error_message)
        
        # Gerar nome seguro
        safe_filename = self._generate_safe_filename(uploaded_file.name)
        
        # Definir caminho de destino
        upload_path = self._get_upload_path(subfolder)
        file_path = os.path.join(upload_path, safe_filename)
        
        # Criar diretório se não existir
        os.makedirs(upload_path, exist_ok=True)
        
        # Salvar arquivo
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Calcular hash
        file_hash = self._calculate_file_hash(full_path)
        
        return {
            'filename': safe_filename,
            'original_name': uploaded_file.name,
            'path': file_path,
            'url': f"{settings.MEDIA_URL}{file_path}",
            'size': uploaded_file.size,
            'content_type': uploaded_file.content_type,
            'hash': file_hash,
            'upload_date': timezone.now(),
            'type': self.upload_type
        }
    
    def _validate_size(self, uploaded_file: UploadedFile) -> bool:
        """Valida o tamanho do arquivo"""
        return uploaded_file.size <= self.config['max_size']
    
    def _validate_extension(self, filename: str) -> bool:
        """Valida a extensão do arquivo"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.config['extensions']
    
    def _validate_mimetype(self, uploaded_file: UploadedFile) -> bool:
        """Valida o MIME type do arquivo"""
        # Verificar MIME type declarado
        if uploaded_file.content_type not in self.config['mimetypes']:
            return False
        
        # Verificar MIME type real usando python-magic se disponível
        try:
            uploaded_file.seek(0)
            file_content = uploaded_file.read(1024)  # Ler apenas o início
            uploaded_file.seek(0)
            
            if HAS_MAGIC:
                detected_type = magic.from_buffer(file_content, mime=True)
                return detected_type in self.config['mimetypes']
            else:
                # Se python-magic não estiver disponível, usar mimetypes do Python
                guessed_type, _ = mimetypes.guess_type(uploaded_file.name)
                return guessed_type in self.config['mimetypes']
        except:
            # Se houver erro, usar mimetypes do Python
            guessed_type, _ = mimetypes.guess_type(uploaded_file.name)
            return guessed_type in self.config['mimetypes']
    
    def _validate_content(self, uploaded_file: UploadedFile) -> bool:
        """Valida o conteúdo do arquivo"""
        try:
            uploaded_file.seek(0)
            header = uploaded_file.read(512)  # Ler header
            uploaded_file.seek(0)
            
            # Verificar se o header corresponde ao tipo esperado
            if self.upload_type == 'image':
                # Headers de imagem
                image_headers = [
                    b'\xff\xd8\xff',  # JPEG
                    b'\x89PNG\r\n\x1a\n',  # PNG
                    b'GIF87a',  # GIF87a
                    b'GIF89a',  # GIF89a
                    b'RIFF',  # WebP (contains RIFF)
                ]
                return any(header.startswith(h) for h in image_headers)
            
            elif self.upload_type == 'document':
                # Headers de documentos
                doc_headers = [
                    b'%PDF',  # PDF
                    b'\xd0\xcf\x11\xe0',  # MS Office (DOC, XLS)
                    b'PK\x03\x04',  # Office Open XML (DOCX, XLSX)
                ]
                return any(header.startswith(h) for h in doc_headers) or header.isascii()
            
            return True
            
        except:
            return False
    
    def _check_malicious_signatures(self, uploaded_file: UploadedFile) -> bool:
        """Verifica assinaturas maliciosas"""
        try:
            uploaded_file.seek(0)
            header = uploaded_file.read(512)
            uploaded_file.seek(0)
            
            return any(header.startswith(sig) for sig in self.MALICIOUS_SIGNATURES)
        except:
            return False
    
    def _generate_safe_filename(self, original_name: str) -> str:
        """Gera um nome seguro para o arquivo"""
        name, ext = os.path.splitext(original_name)
        
        # Limpar nome
        safe_name = slugify(name)[:50]  # Limitar tamanho
        
        # Adicionar timestamp para unicidade
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{safe_name}_{timestamp}{ext.lower()}"
    
    def _get_upload_path(self, subfolder: str) -> str:
        """Gera o caminho de upload baseado no tipo e data"""
        date_folder = timezone.now().strftime('%Y/%m')
        
        if subfolder:
            return os.path.join('uploads', self.upload_type, date_folder, subfolder)
        else:
            return os.path.join('uploads', self.upload_type, date_folder)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash SHA-256 do arquivo"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para string legível"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


# Funções auxiliares para uso fácil
def upload_image(uploaded_file: UploadedFile, subfolder: str = '') -> dict:
    """Upload de imagem"""
    uploader = SecureFileUploader('image')
    return uploader.upload_file(uploaded_file, subfolder)


def upload_document(uploaded_file: UploadedFile, subfolder: str = '') -> dict:
    """Upload de documento"""
    uploader = SecureFileUploader('document')
    return uploader.upload_file(uploaded_file, subfolder)


def upload_video(uploaded_file: UploadedFile, subfolder: str = '') -> dict:
    """Upload de vídeo"""
    uploader = SecureFileUploader('video')
    return uploader.upload_file(uploaded_file, subfolder)


def validate_file(uploaded_file: UploadedFile, file_type: str = 'document') -> Tuple[bool, str]:
    """
    Valida um arquivo
    
    Args:
        uploaded_file: Arquivo a ser validado
        file_type: Tipo do arquivo
        
    Returns:
        Tuple com (é_válido, mensagem)
    """
    uploader = SecureFileUploader(file_type)
    return uploader.validate_file(uploaded_file)
