"""
Signals para automação de notificações
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from workshops.models import Enrollment
from certificates.models import Certificate
from projects.models import ProjectMember
from coaching.models import CoachingSession
from .models import send_notification, NotificationPreference

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Criar preferências de notificação para novos usuários"""
    if created:
        NotificationPreference.objects.create(user=instance)


@receiver(post_save, sender=Enrollment)
def workshop_enrollment_notification(sender, instance, created, **kwargs):
    """Notificar sobre inscrição em workshop"""
    if created:
        send_notification(
            recipient=instance.member.user,
            title=f"Inscrição confirmada: {instance.workshop.title}",
            message=f"Sua inscrição no workshop '{instance.workshop.title}' foi confirmada!",
            notification_type='workshop_enrollment',
            channel='email',
            priority=2,
            related_object=instance.workshop
        )


@receiver(pre_save, sender=Enrollment)
def workshop_status_change_notification(sender, instance, **kwargs):
    """Notificar sobre mudanças no status do workshop"""
    if instance.pk:
        try:
            old_instance = Enrollment.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == 'completed':
                    send_notification(
                        recipient=instance.member.user,
                        title=f"Workshop concluído: {instance.workshop.title}",
                        message=f"Parabéns! Você concluiu o workshop '{instance.workshop.title}'. "
                               f"Seu certificado será gerado em breve.",
                        notification_type='workshop_enrollment',
                        channel='email',
                        priority=2,
                        related_object=instance.workshop
                    )
                elif instance.status == 'cancelled':
                    send_notification(
                        recipient=instance.member.user,
                        title=f"Workshop cancelado: {instance.workshop.title}",
                        message=f"Infelizmente o workshop '{instance.workshop.title}' foi cancelado. "
                               f"Você será notificado sobre reagendamento.",
                        notification_type='workshop_enrollment',
                        channel='email',
                        priority=3,
                        related_object=instance.workshop
                    )
        except Enrollment.DoesNotExist:
            pass


@receiver(post_save, sender=Certificate)
def certificate_ready_notification(sender, instance, created, **kwargs):
    """Notificar quando certificado estiver pronto"""
    if not created and instance.status == 'generated' and instance.pdf_file:
        send_notification(
            recipient=instance.member.user,
            title="Seu certificado está pronto!",
            message=f"Seu certificado para '{instance.title}' foi gerado e está "
                   f"disponível para download.",
            notification_type='certificate_ready',
            channel='email',
            priority=2,
            related_object=instance
        )


@receiver(post_save, sender=ProjectMember)
def project_invitation_notification(sender, instance, created, **kwargs):
    """Notificar sobre convite para projeto"""
    if created:
        send_notification(
            recipient=instance.member.user,
            title=f"Convite para projeto: {instance.project.title}",
            message=f"Você foi convidado para participar do projeto '{instance.project.title}'.",
            notification_type='project_invitation',
            channel='email',
            priority=2,
            related_object=instance.project
        )


@receiver(post_save, sender=CoachingSession)
def coaching_scheduled_notification(sender, instance, created, **kwargs):
    """Notificar sobre agendamento de coaching"""
    if created:
        send_notification(
            recipient=instance.member.user,
            title=f"Coaching agendado: {instance.title}",
            message=f"Seu coaching '{instance.title}' foi agendado para "
                   f"{instance.scheduled_date} às {instance.scheduled_time}.",
            notification_type='coaching_scheduled',
            channel='email',
            priority=2,
            related_object=instance
        )


@receiver(pre_save, sender=CoachingSession)
def coaching_status_change_notification(sender, instance, **kwargs):
    """Notificar sobre mudanças no status do coaching"""
    if instance.pk:
        try:
            old_instance = CoachingSession.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == 'confirmed':
                    send_notification(
                        recipient=instance.member.user,
                        title=f"Coaching confirmado: {instance.title}",
                        message=f"Seu coaching '{instance.title}' foi confirmado para "
                               f"{instance.scheduled_date} às {instance.scheduled_time}.",
                        notification_type='coaching_scheduled',
                        channel='email',
                        priority=2,
                        related_object=instance
                    )
                elif instance.status == 'cancelled':
                    send_notification(
                        recipient=instance.member.user,
                        title=f"Coaching cancelado: {instance.title}",
                        message=f"Seu coaching '{instance.title}' foi cancelado. "
                               f"Entre em contato para reagendar.",
                        notification_type='coaching_scheduled',
                        channel='email',
                        priority=3,
                        related_object=instance
                    )
        except CoachingSession.DoesNotExist:
            pass
