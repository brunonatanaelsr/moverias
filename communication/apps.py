from django.apps import AppConfig


class CommunicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'
    verbose_name = 'Comunicação Interna'

    def ready(self):
        try:
            import communication.signals
        except ImportError:
            pass
