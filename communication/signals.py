from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import CommunicationSettings

User = get_user_model()


@receiver(post_save, sender=User)
def create_communication_settings(sender, instance, created, **kwargs):
    """Cria configurações de comunicação padrão para novos usuários"""
    if created:
        CommunicationSettings.objects.create(user=instance)
