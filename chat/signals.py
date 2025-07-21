from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatMessage, ChatChannel, ChatAnalytics

User = get_user_model()
ChatRoom = ChatChannel  # Alias for backward compatibility


@receiver(post_save, sender=ChatMessage)
def create_message_analytics(sender, instance, created, **kwargs):
    """Create analytics when a new message is sent"""
    if created and instance.message_type != 'system':
        # Get or create analytics entry for today
        today = timezone.now().date()
        analytics, created = ChatAnalytics.objects.get_or_create(
            channel=instance.channel,
            date=today,
            defaults={
                'message_count': 0,
                'active_users': 0,
                'file_shares': 0,
                'reactions_count': 0,
                'thread_count': 0,
            }
        )
        
        # Update message count
        analytics.message_count += 1
        analytics.save()


@receiver(post_save, sender=User)
def create_user_chat_analytics(sender, instance, created, **kwargs):
    """Create initial analytics when a user is created"""
    if created:
        # Don't create analytics for new users in the chat app
        # as they don't have channels yet
        pass
