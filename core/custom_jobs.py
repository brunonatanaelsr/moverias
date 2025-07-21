"""
Custom Jobs para necessidades específicas do negócio MoveMarias
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.core.management import call_command
from django.core.cache import cache
import logging
import json
from .background_jobs import JobScheduler

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomJobManager:
    """Manager para jobs customizados específicos do negócio"""
    
    def __init__(self):
        self.scheduler = JobScheduler()
    
    def schedule_business_jobs(self):
        """Agendar todos os jobs de negócio"""
        
        # Jobs diários
        self.scheduler.schedule_daily_job(
            'beneficiary_follow_up',
            self.beneficiary_follow_up,
            hour=9,
            minute=0,
            description="Verificar beneficiárias que precisam de acompanhamento"
        )
        
        self.scheduler.schedule_daily_job(
            'workshop_notifications',
            self.workshop_notifications,
            hour=10,
            minute=0,
            description="Notificar sobre workshops próximos"
        )
        
        self.scheduler.schedule_daily_job(
            'certificate_processing',
            self.certificate_processing,
            hour=14,
            minute=0,
            description="Processar certificados pendentes"
        )
        
        # Jobs semanais
        self.scheduler.schedule_weekly_job(
            'weekly_progress_report',
            self.weekly_progress_report,
            day_of_week=1,  # Segunda-feira
            hour=8,
            minute=0,
            description="Relatório semanal de progresso"
        )
        
        self.scheduler.schedule_weekly_job(
            'inactive_users_cleanup',
            self.inactive_users_cleanup,
            day_of_week=5,  # Sexta-feira
            hour=16,
            minute=0,
            description="Limpar usuários inativos"
        )
        
        # Jobs mensais
        self.scheduler.schedule_monthly_job(
            'monthly_analytics',
            self.monthly_analytics,
            day=1,
            hour=7,
            minute=0,
            description="Análise mensal de indicadores"
        )
        
        self.scheduler.schedule_monthly_job(
            'coaching_review_reminder',
            self.coaching_review_reminder,
            day=15,
            hour=9,
            minute=0,
            description="Lembrete de revisão de coaching"
        )
        
        logger.info("Custom business jobs scheduled successfully")
    
    def beneficiary_follow_up(self):
        """Verificar beneficiárias que precisam de acompanhamento"""
        try:
            from members.models import Beneficiary
            from coaching.models import ActionPlan
            from django.utils import timezone
            
            now = timezone.now()
            thirty_days_ago = now - timedelta(days=30)
            
            # Beneficiárias sem atividade recente
            inactive_beneficiaries = Beneficiary.objects.filter(
                created_at__lt=thirty_days_ago,
                is_active=True
            ).exclude(
                actionplan__created_at__gte=thirty_days_ago
            ).exclude(
                evolution_records__date__gte=thirty_days_ago
            )
            
            results = []
            for beneficiary in inactive_beneficiaries:
                # Verificar se já enviou notificação recentemente
                cache_key = f"follow_up_sent_{beneficiary.id}"
                if cache.get(cache_key):
                    continue
                
                # Notificar equipe de coaching
                coaching_team = User.objects.filter(
                    Q(role='coach') | Q(role='coordenador')
                ).filter(is_active=True)
                
                for coach in coaching_team:
                    self._send_follow_up_notification(coach, beneficiary)
                
                # Marcar como enviado (válido por 7 dias)
                cache.set(cache_key, True, 60 * 60 * 24 * 7)
                results.append(beneficiary.full_name)
            
            logger.info(f"Follow-up check completed. {len(results)} beneficiaries need attention")
            return {
                'success': True,
                'processed': len(results),
                'beneficiaries': results
            }
            
        except Exception as e:
            logger.error(f"Error in beneficiary follow-up: {e}")
            return {'success': False, 'error': str(e)}
    
    def workshop_notifications(self):
        """Notificar sobre workshops próximos"""
        try:
            from workshops.models import Workshop
            from django.utils import timezone
            
            now = timezone.now()
            tomorrow = now + timedelta(days=1)
            next_week = now + timedelta(days=7)
            
            # Workshops amanhã
            tomorrow_workshops = Workshop.objects.filter(
                start_date__date=tomorrow.date(),
                status='ativo'
            )
            
            # Workshops próxima semana
            next_week_workshops = Workshop.objects.filter(
                start_date__date=next_week.date(),
                status='ativo'
            )
            
            results = {'tomorrow': 0, 'next_week': 0}
            
            # Notificar workshops de amanhã
            for workshop in tomorrow_workshops:
                participants = workshop.participants.filter(is_active=True)
                for participant in participants:
                    self._send_workshop_reminder(participant.user, workshop, 'tomorrow')
                results['tomorrow'] += 1
            
            # Notificar workshops da próxima semana
            for workshop in next_week_workshops:
                participants = workshop.participants.filter(is_active=True)
                for participant in participants:
                    self._send_workshop_reminder(participant.user, workshop, 'next_week')
                results['next_week'] += 1
            
            logger.info(f"Workshop notifications sent: {results}")
            return {
                'success': True,
                'tomorrow_workshops': results['tomorrow'],
                'next_week_workshops': results['next_week']
            }
            
        except Exception as e:
            logger.error(f"Error in workshop notifications: {e}")
            return {'success': False, 'error': str(e)}
    
    def certificate_processing(self):
        """Processar certificados pendentes"""
        try:
            from certificates.models import Certificate
            from django.utils import timezone
            
            # Certificados pendentes de processamento
            pending_certificates = Certificate.objects.filter(
                status='pending',
                created_at__lt=timezone.now() - timedelta(hours=1)
            )
            
            results = []
            for certificate in pending_certificates:
                try:
                    # Processar certificado
                    certificate.process()
                    
                    # Notificar beneficiária
                    if certificate.beneficiary.user:
                        self._send_certificate_notification(
                            certificate.beneficiary.user,
                            certificate
                        )
                    
                    results.append(certificate.id)
                    
                except Exception as e:
                    logger.error(f"Error processing certificate {certificate.id}: {e}")
                    certificate.status = 'failed'
                    certificate.save()
            
            logger.info(f"Certificate processing completed. {len(results)} certificates processed")
            return {
                'success': True,
                'processed': len(results),
                'certificate_ids': results
            }
            
        except Exception as e:
            logger.error(f"Error in certificate processing: {e}")
            return {'success': False, 'error': str(e)}
    
    def weekly_progress_report(self):
        """Relatório semanal de progresso"""
        try:
            from members.models import Beneficiary
            from workshops.models import Workshop
            from projects.models import Project
            from coaching.models import ActionPlan
            from django.utils import timezone
            
            now = timezone.now()
            week_ago = now - timedelta(days=7)
            
            # Estatísticas da semana
            stats = {
                'new_beneficiaries': Beneficiary.objects.filter(
                    created_at__gte=week_ago
                ).count(),
                'new_workshops': Workshop.objects.filter(
                    created_at__gte=week_ago
                ).count(),
                'new_projects': Project.objects.filter(
                    created_at__gte=week_ago
                ).count(),
                'new_action_plans': ActionPlan.objects.filter(
                    created_at__gte=week_ago
                ).count(),
                'active_beneficiaries': Beneficiary.objects.filter(
                    is_active=True
                ).count(),
                'active_workshops': Workshop.objects.filter(
                    status='ativo'
                ).count(),
            }
            
            # Enviar relatório para coordenadores
            coordinators = User.objects.filter(
                role='coordenador',
                is_active=True
            )
            
            for coordinator in coordinators:
                self._send_weekly_report(coordinator, stats)
            
            logger.info(f"Weekly progress report sent to {coordinators.count()} coordinators")
            return {
                'success': True,
                'stats': stats,
                'recipients': coordinators.count()
            }
            
        except Exception as e:
            logger.error(f"Error in weekly progress report: {e}")
            return {'success': False, 'error': str(e)}
    
    def inactive_users_cleanup(self):
        """Limpar usuários inativos"""
        try:
            from django.utils import timezone
            
            now = timezone.now()
            six_months_ago = now - timedelta(days=180)
            
            # Usuários inativos há mais de 6 meses
            inactive_users = User.objects.filter(
                is_active=True,
                last_login__lt=six_months_ago
            ).exclude(
                role__in=['admin', 'coordenador']
            )
            
            results = []
            for user in inactive_users:
                # Desativar em vez de deletar
                user.is_active = False
                user.save()
                results.append(user.username)
            
            logger.info(f"Inactive users cleanup completed. {len(results)} users deactivated")
            return {
                'success': True,
                'deactivated': len(results),
                'usernames': results
            }
            
        except Exception as e:
            logger.error(f"Error in inactive users cleanup: {e}")
            return {'success': False, 'error': str(e)}
    
    def monthly_analytics(self):
        """Análise mensal de indicadores"""
        try:
            from members.models import Beneficiary
            from workshops.models import Workshop
            from projects.models import Project
            from coaching.models import ActionPlan, WheelOfLife
            from django.utils import timezone
            from django.db.models import Avg, Count
            
            now = timezone.now()
            month_ago = now - timedelta(days=30)
            
            # Análise mensal
            analytics = {
                'period': f"{month_ago.strftime('%B %Y')} - {now.strftime('%B %Y')}",
                'beneficiaries': {
                    'total': Beneficiary.objects.count(),
                    'new_this_month': Beneficiary.objects.filter(
                        created_at__gte=month_ago
                    ).count(),
                    'active': Beneficiary.objects.filter(is_active=True).count(),
                },
                'workshops': {
                    'total': Workshop.objects.count(),
                    'completed_this_month': Workshop.objects.filter(
                        status='completo',
                        updated_at__gte=month_ago
                    ).count(),
                    'active': Workshop.objects.filter(status='ativo').count(),
                },
                'projects': {
                    'total': Project.objects.count(),
                    'active': Project.objects.filter(is_active=True).count(),
                },
                'coaching': {
                    'action_plans': ActionPlan.objects.count(),
                    'wheel_assessments': WheelOfLife.objects.filter(
                        date__gte=month_ago
                    ).count(),
                    'avg_wheel_score': WheelOfLife.objects.filter(
                        date__gte=month_ago
                    ).aggregate(Avg('average_score'))['average_score__avg'] or 0,
                }
            }
            
            # Salvar no cache para dashboard
            cache.set('monthly_analytics', analytics, 60 * 60 * 24 * 7)  # 7 dias
            
            # Enviar para administradores
            admins = User.objects.filter(
                Q(role='admin') | Q(role='coordenador'),
                is_active=True
            )
            
            for admin in admins:
                self._send_monthly_analytics(admin, analytics)
            
            logger.info(f"Monthly analytics generated and sent to {admins.count()} administrators")
            return {
                'success': True,
                'analytics': analytics,
                'recipients': admins.count()
            }
            
        except Exception as e:
            logger.error(f"Error in monthly analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def coaching_review_reminder(self):
        """Lembrete de revisão de coaching"""
        try:
            from coaching.models import ActionPlan
            from django.utils import timezone
            
            now = timezone.now()
            six_months_ago = now - timedelta(days=180)
            
            # Planos de ação que precisam de revisão
            plans_for_review = ActionPlan.objects.filter(
                created_at__lt=six_months_ago,
                semester_review__isnull=True
            ).select_related('beneficiary')
            
            results = []
            coaches = User.objects.filter(
                role='coach',
                is_active=True
            )
            
            for plan in plans_for_review:
                # Notificar coaches
                for coach in coaches:
                    self._send_coaching_review_reminder(coach, plan)
                results.append(plan.id)
            
            logger.info(f"Coaching review reminders sent for {len(results)} plans")
            return {
                'success': True,
                'plans_for_review': len(results),
                'plan_ids': results
            }
            
        except Exception as e:
            logger.error(f"Error in coaching review reminder: {e}")
            return {'success': False, 'error': str(e)}
    
    # Métodos auxiliares para envio de notificações
    def _send_follow_up_notification(self, user, beneficiary):
        """Enviar notificação de follow-up"""
        try:
            subject = f"Acompanhamento necessário - {beneficiary.full_name}"
            message = f"""
            Olá {user.first_name},
            
            A beneficiária {beneficiary.full_name} não teve atividades recentes no sistema.
            
            Considere entrar em contato para oferecer suporte adicional.
            
            Dados da beneficiária:
            - Nome: {beneficiary.full_name}
            - Email: {getattr(beneficiary, 'email', 'Não informado')}
            - Telefone: {getattr(beneficiary, 'phone', 'Não informado')}
            - Última atividade: {getattr(beneficiary, 'last_activity', 'Não registrada')}
            
            Acesse o sistema para mais detalhes.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending follow-up notification: {e}")
    
    def _send_workshop_reminder(self, user, workshop, timing):
        """Enviar lembrete de workshop"""
        try:
            timing_text = "amanhã" if timing == 'tomorrow' else "na próxima semana"
            subject = f"Lembrete: Workshop {workshop.title} {timing_text}"
            message = f"""
            Olá {user.first_name},
            
            Lembramos que você tem um workshop agendado {timing_text}:
            
            Título: {workshop.title}
            Data: {workshop.start_date.strftime('%d/%m/%Y %H:%M')}
            Local: {getattr(workshop, 'location', 'A definir')}
            
            Não se esqueça de participar!
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending workshop reminder: {e}")
    
    def _send_certificate_notification(self, user, certificate):
        """Enviar notificação de certificado"""
        try:
            subject = f"Seu certificado está pronto!"
            message = f"""
            Parabéns {user.first_name}!
            
            Seu certificado foi processado e está disponível para download.
            
            Certificado: {certificate.title}
            Data de emissão: {certificate.issue_date.strftime('%d/%m/%Y')}
            
            Acesse o sistema para baixar seu certificado.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending certificate notification: {e}")
    
    def _send_weekly_report(self, user, stats):
        """Enviar relatório semanal"""
        try:
            subject = "Relatório Semanal - Move Marias"
            message = f"""
            Olá {user.first_name},
            
            Aqui está o relatório semanal de atividades:
            
            📊 Estatísticas da Semana:
            - Novas beneficiárias: {stats['new_beneficiaries']}
            - Novos workshops: {stats['new_workshops']}
            - Novos projetos: {stats['new_projects']}
            - Novos planos de ação: {stats['new_action_plans']}
            
            📈 Totais Atuais:
            - Beneficiárias ativas: {stats['active_beneficiaries']}
            - Workshops ativos: {stats['active_workshops']}
            
            Acesse o sistema para mais detalhes.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
    
    def _send_monthly_analytics(self, user, analytics):
        """Enviar análise mensal"""
        try:
            subject = "Análise Mensal - Move Marias"
            message = f"""
            Olá {user.first_name},
            
            Análise mensal do período: {analytics['period']}
            
            👥 Beneficiárias:
            - Total: {analytics['beneficiaries']['total']}
            - Novas este mês: {analytics['beneficiaries']['new_this_month']}
            - Ativas: {analytics['beneficiaries']['active']}
            
            🎓 Workshops:
            - Total: {analytics['workshops']['total']}
            - Concluídos este mês: {analytics['workshops']['completed_this_month']}
            - Ativos: {analytics['workshops']['active']}
            
            💼 Projetos:
            - Total: {analytics['projects']['total']}
            - Ativos: {analytics['projects']['active']}
            
            🎯 Coaching:
            - Planos de ação: {analytics['coaching']['action_plans']}
            - Avaliações Roda da Vida: {analytics['coaching']['wheel_assessments']}
            - Pontuação média: {analytics['coaching']['avg_wheel_score']:.1f}
            
            Acesse o dashboard para visualizações detalhadas.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending monthly analytics: {e}")
    
    def _send_coaching_review_reminder(self, user, plan):
        """Enviar lembrete de revisão de coaching"""
        try:
            subject = f"Revisão de Coaching - {plan.beneficiary.full_name}"
            message = f"""
            Olá {user.first_name},
            
            O plano de ação da beneficiária {plan.beneficiary.full_name} está pendente de revisão semestral.
            
            Plano criado em: {plan.created_at.strftime('%d/%m/%Y')}
            Meta principal: {plan.main_goal}
            
            Por favor, agende uma sessão de revisão para avaliar o progresso.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending coaching review reminder: {e}")


# Instância global do manager
custom_job_manager = CustomJobManager()
