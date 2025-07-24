from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import os
import uuid

User = get_user_model()


def upload_file_path(instance, filename):
    """Gera o caminho para upload de arquivos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', str(instance.uploaded_by.id), filename)

class SystemConfig(models.Model):
    """Model for storing system configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

class SystemLog(models.Model):
    """Model for system logs and audit trail"""
    LOG_LEVELS = (
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.level}: {self.message[:50]}..."


class FileUpload(models.Model):
    """Modelo para sistema de uploads de arquivos"""
    CATEGORY_CHOICES = [
        ('document', 'Documento'),
        ('image', 'Imagem'),
        ('certificate', 'Certificado'),
        ('report', 'Relatório'),
        ('other', 'Outro'),
    ]
    
    file = models.FileField(
        'Arquivo',
        upload_to=upload_file_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'xlsx', 'xls', 'txt']
            )
        ]
    )
    original_name = models.CharField('Nome Original', max_length=255)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES, default='other')
    file_size = models.PositiveIntegerField('Tamanho do Arquivo (bytes)', default=0)
    file_type = models.CharField('Tipo de Arquivo', max_length=50, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Enviado por')
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)
    is_public = models.BooleanField('Público', default=False, help_text='Visível para todos os usuários')
    download_count = models.PositiveIntegerField('Contagem de Downloads', default=0)
    
    class Meta:
        verbose_name = 'Upload de Arquivo'
        verbose_name_plural = 'Uploads de Arquivos'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.original_name})"
    
    @property
    def file_size_formatted(self):
        """Retorna o tamanho do arquivo formatado"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024**2:
            return f"{self.file_size/1024:.1f} KB"
        elif self.file_size < 1024**3:
            return f"{self.file_size/(1024**2):.1f} MB"
        else:
            return f"{self.file_size/(1024**3):.1f} GB"
    
    @property
    def is_image(self):
        """Verifica se o arquivo é uma imagem"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            return ext in image_extensions
        return False
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.content_type or ''
            if not self.original_name:
                self.original_name = self.file.name
        super().save(*args, **kwargs)
