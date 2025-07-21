"""
Configuração do app de certificados
"""
from django.apps import AppConfig


class CertificatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certificates'
    verbose_name = 'Certificados'
    
    def ready(self):
        # Importar signals se necessário
        try:
            import certificates.signals
        except ImportError:
            pass
