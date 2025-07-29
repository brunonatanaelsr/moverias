# Otimizações de Performance - Models com Managers Inteligentes

from django.db import models
from django.db.models import Count, Q, F, Case, When, Avg, Sum
from django.utils import timezone
from datetime import timedelta, date


class OptimizedManager(models.Manager):
    """Manager base com otimizações comuns"""
    
    def with_related(self):
        """Carrega relacionamentos básicos"""
        return self.select_related().prefetch_related()
    
    def active(self):
        """Filtra apenas registros ativos"""
        return self.filter(status__in=['ATIVO', 'ATIVA', 'ativo'])


class BeneficiaryManager(OptimizedManager):
    """Manager otimizado para Beneficiárias"""
    
    def with_statistics(self):
        """Carrega beneficiárias com estatísticas calculadas"""
        return self.annotate(
            # Contar projetos ativos
            active_projects=Count(
                'project_enrollments',
                filter=Q(project_enrollments__status='ATIVO')
            ),
            # Contar workshops ativos
            active_workshops=Count(
                'workshop_enrollments',
                filter=Q(workshop_enrollments__status='ATIVO')
            ),
            # Últimas evoluções
            recent_evolutions=Count(
                'evolution_records',
                filter=Q(evolution_records__date__gte=timezone.now().date() - timedelta(days=30))
            ),
            # Score de vulnerabilidade (se existir anamnese)
            vulnerability_score=Avg('social_anamneses__vulnerability_score'),
            # Dias desde última atividade
            days_since_last_evolution=Case(
                When(evolution_records__isnull=True, then=999),
                default=timezone.now().date() - F('evolution_records__date')
            )
        ).select_related().prefetch_related(
            'consents',
            'social_anamneses',
            'evolution_records'
        )
    
    def need_attention(self):
        """Beneficiárias que precisam de atenção (sem atividade recente)"""
        cutoff_date = timezone.now().date() - timedelta(days=30)
        return self.filter(
            status='ATIVA'
        ).exclude(
            evolution_records__date__gte=cutoff_date
        ).annotate(
            days_inactive=timezone.now().date() - F('evolution_records__date')
        ).order_by('-days_inactive')
    
    def by_age_group(self):
        """Agrupa beneficiárias por faixa etária"""
        today = date.today()
        return self.extra(
            select={
                'age': f"EXTRACT(year FROM AGE('{today}', dob))"
            }
        ).extra(
            select={
                'age_group': """
                    CASE 
                        WHEN EXTRACT(year FROM AGE(%s, dob)) < 18 THEN 'Menor de 18'
                        WHEN EXTRACT(year FROM AGE(%s, dob)) BETWEEN 18 AND 25 THEN '18-25 anos'
                        WHEN EXTRACT(year FROM AGE(%s, dob)) BETWEEN 26 AND 35 THEN '26-35 anos'
                        WHEN EXTRACT(year FROM AGE(%s, dob)) BETWEEN 36 AND 50 THEN '36-50 anos'
                        ELSE 'Acima de 50'
                    END
                """
            },
            select_params=[today, today, today, today]
        )


class ProjectManager(OptimizedManager):
    """Manager otimizado para Projetos"""
    
    def with_statistics(self):
        """Carrega projetos com estatísticas calculadas"""
        return self.annotate(
            # Participantes ativos
            total_participants=Count(
                'enrollments',
                filter=Q(enrollments__status='ATIVO')
            ),
            # Total de sessões
            total_sessions=Count('sessions'),
            # Sessões realizadas
            completed_sessions=Count(
                'sessions',
                filter=Q(sessions__session_date__lt=timezone.now().date())
            ),
            # Taxa de conclusão
            completion_rate=Case(
                When(total_sessions=0, then=0),
                default=F('completed_sessions') * 100.0 / F('total_sessions')
            ),
            # Taxa de presença média
            attendance_rate=Case(
                When(sessions__attendances__isnull=True, then=0),
                default=Avg(
                    Case(
                        When(sessions__attendances__attended=True, then=100),
                        default=0
                    )
                )
            ),
            # Próxima sessão
            next_session_date=models.Min(
                'sessions__session_date',
                filter=Q(sessions__session_date__gte=timezone.now().date())
            )
        ).select_related('coordinator').prefetch_related('sessions', 'enrollments')
    
    def upcoming_deadlines(self, days=7):
        """Projetos com prazo próximo"""
        deadline = timezone.now().date() + timedelta(days=days)
        return self.filter(
            status='ATIVO',
            end_date__lte=deadline,
            end_date__gte=timezone.now().date()
        ).order_by('end_date')
    
    def performance_summary(self):
        """Resumo de performance dos projetos"""
        return self.with_statistics().aggregate(
            total_active=Count('id', filter=Q(status='ATIVO')),
            avg_participants=Avg('total_participants'),
            avg_completion_rate=Avg('completion_rate'),
            avg_attendance_rate=Avg('attendance_rate')
        )


class WorkshopManager(OptimizedManager):
    """Manager otimizado para Workshops"""
    
    def with_statistics(self):
        """Carrega workshops com estatísticas calculadas"""
        return self.annotate(
            # Participantes inscritos
            total_participants=Count('enrollments'),
            # Participantes ativos
            active_participants=Count(
                'enrollments',
                filter=Q(enrollments__status='ATIVO')
            ),
            # Sessões realizadas
            completed_sessions=Count(
                'sessions',
                filter=Q(sessions__session_date__lt=timezone.now().date())
            ),
            # Avaliação média
            average_rating=Avg('evaluations__rating'),
            # Taxa de ocupação
            occupancy_rate=Case(
                When(max_participants=0, then=0),
                default=F('active_participants') * 100.0 / F('max_participants')
            ),
            # Próxima sessão
            next_session=models.Min(
                'sessions__session_date',
                filter=Q(sessions__session_date__gte=timezone.now().date())
            )
        ).select_related('facilitator').prefetch_related('sessions', 'enrollments')
    
    def need_evaluation(self):
        """Workshops que precisam de avaliação"""
        return self.filter(
            status='concluido'
        ).annotate(
            evaluation_count=Count('evaluations')
        ).filter(evaluation_count=0)
    
    def popular_workshops(self):
        """Workshops mais populares por número de inscrições"""
        return self.with_statistics().filter(
            active_participants__gte=1
        ).order_by('-active_participants', '-average_rating')


class EvolutionManager(OptimizedManager):
    """Manager otimizado para Registros de Evolução"""
    
    def recent(self, days=30):
        """Evoluções recentes"""
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return self.filter(date__gte=cutoff_date).select_related(
            'beneficiary', 'created_by'
        ).order_by('-date')
    
    def by_beneficiary_summary(self, beneficiary):
        """Resumo de evoluções por beneficiária"""
        return self.filter(beneficiary=beneficiary).aggregate(
            total_records=Count('id'),
            first_record=models.Min('date'),
            last_record=models.Max('date'),
            positive_records=Count(
                'id',
                filter=Q(description__icontains=['progresso', 'melhora', 'evolução', 'sucesso'])
            )
        )
    
    def trends_analysis(self):
        """Análise de tendências nas evoluções"""
        from django.db.models import TruncMonth
        
        return self.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_records=Count('id'),
            unique_beneficiaries=Count('beneficiary', distinct=True)
        ).order_by('month')


class SocialAnamnesisManager(OptimizedManager):
    """Manager otimizado para Anamneses Sociais"""
    
    def completed(self):
        """Anamneses finalizadas (locked)"""
        return self.filter(locked=True).select_related('beneficiary')
    
    def high_vulnerability(self):
        """Casos de alta vulnerabilidade"""
        return self.filter(
            vulnerability_score__gte=70,
            locked=True
        ).select_related('beneficiary').order_by('-vulnerability_score')
    
    def need_review(self):
        """Anamneses que precisam revisão (antigas)"""
        cutoff_date = timezone.now().date() - timedelta(days=365)  # 1 ano
        return self.filter(
            locked=True,
            created_at__date__lt=cutoff_date
        ).select_related('beneficiary')


# Exemplo de uso em views otimizadas
class OptimizedViewExamples:
    """Exemplos de como usar os managers otimizados nas views"""
    
    @staticmethod
    def beneficiary_dashboard_data():
        """Dados otimizados para dashboard de beneficiárias"""
        # Uma única query com todas as estatísticas
        beneficiaries = Beneficiary.objects.with_statistics().filter(
            status='ATIVA'
        )[:20]  # Top 20 com mais dados
        
        # Estatísticas gerais
        summary = Beneficiary.objects.aggregate(
            total_active=Count('id', filter=Q(status='ATIVA')),
            need_attention=Count('id', filter=Q(
                status='ATIVA',
                evolution_records__date__lt=timezone.now().date() - timedelta(days=30)
            )),
            with_anamnesis=Count('id', filter=Q(social_anamneses__locked=True)),
            high_vulnerability=Count('id', filter=Q(
                social_anamneses__vulnerability_score__gte=70
            ))
        )
        
        return {
            'beneficiaries': beneficiaries,
            'summary': summary
        }
    
    @staticmethod
    def project_performance_data():
        """Dados de performance dos projetos"""
        # Projetos com estatísticas
        projects = Project.objects.with_statistics().filter(
            status='ATIVO'
        )
        
        # Projetos com prazo próximo
        upcoming_deadlines = Project.objects.upcoming_deadlines(days=14)
        
        # Resumo geral
        performance = Project.objects.performance_summary()
        
        return {
            'projects': projects,
            'upcoming_deadlines': upcoming_deadlines,
            'performance': performance
        }
    
    @staticmethod
    def workshop_analytics_data():
        """Analytics dos workshops"""
        # Workshops populares
        popular = Workshop.objects.popular_workshops()[:10]
        
        # Workshops que precisam avaliação
        need_evaluation = Workshop.objects.need_evaluation()
        
        # Estatísticas gerais
        stats = Workshop.objects.with_statistics().aggregate(
            total_active=Count('id', filter=Q(status='ativo')),
            avg_rating=Avg('average_rating'),
            total_participants=Sum('active_participants'),
            avg_occupancy=Avg('occupancy_rate')
        )
        
        return {
            'popular_workshops': popular,
            'need_evaluation': need_evaluation,
            'statistics': stats
        }


# Como aplicar nos modelos existentes:

# Em members/models.py - adicionar:
# objects = BeneficiaryManager()

# Em projects/models.py - adicionar:
# objects = ProjectManager()

# Em workshops/models.py - adicionar:
# objects = WorkshopManager()

# Em evolution/models.py - adicionar:
# objects = EvolutionManager()

# Em social/models.py - adicionar:
# objects = SocialAnamnesisManager()
