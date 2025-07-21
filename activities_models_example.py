# activities/models.py - Novo módulo unificado
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Count, Avg
from members.models import Beneficiary
from social.models import SocialObjective
import uuid


class BeneficiaryActivity(models.Model):
    """
    Modelo central para todas as atividades da beneficiária
    Substitui Project e unifica com Tasks
    """
    
    ACTIVITY_TYPES = [
        ('WORKSHOP', 'Workshop'),
        ('COURSE', 'Curso'),
        ('MENTORING', 'Mentoria'),
        ('THERAPY', 'Terapia'),
        ('MEETING', 'Reunião'),
        ('EVENT', 'Evento'),
        ('TASK', 'Tarefa'),
        ('PROJECT', 'Projeto'),
    ]
    
    STATUS_CHOICES = [
        ('PLANEJADO', 'Planejado'),
        ('ATIVO', 'Ativo'),
        ('PAUSADO', 'Pausado'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Baixa'),
        ('MEDIUM', 'Média'),
        ('HIGH', 'Alta'),
        ('URGENT', 'Urgente'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    activity_type = models.CharField('Tipo', max_length=20, choices=ACTIVITY_TYPES)
    
    # Relacionamentos principais
    beneficiary = models.ForeignKey(
        Beneficiary, 
        on_delete=models.CASCADE, 
        related_name='activities',
        verbose_name='Beneficiária'
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coordinated_activities',
        verbose_name='Coordenador'
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervised_activities',
        verbose_name='Técnico Responsável'
    )
    
    # Status e prioridade
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PLANEJADO')
    priority = models.CharField('Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Cronograma
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Término', null=True, blank=True)
    estimated_duration_weeks = models.IntegerField('Duração Estimada (semanas)', null=True, blank=True)
    
    # Configuração de horários (JSON para flexibilidade)
    schedule = models.JSONField('Horários', default=dict, blank=True, help_text='Configuração de horários semanais')
    
    # Localização
    location = models.CharField('Local', max_length=200, blank=True)
    
    # Métricas de acompanhamento
    total_sessions = models.IntegerField('Total de Sessões', default=0)
    attended_sessions = models.IntegerField('Sessões Presentes', default=0)
    progress_percentage = models.IntegerField(
        'Progresso (%)', 
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Integração social
    social_objectives = models.ManyToManyField(
        SocialObjective, 
        blank=True,
        verbose_name='Objetivos Sociais',
        help_text='Objetivos sociais relacionados a esta atividade'
    )
    impact_areas = models.JSONField('Áreas de Impacto', default=list, blank=True)
    
    # Avaliação geral
    overall_rating = models.DecimalField(
        'Avaliação Geral',
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Observações
    notes = models.TextField('Observações', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Atividade da Beneficiária'
        verbose_name_plural = 'Atividades das Beneficiárias'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['beneficiary', 'status']),
            models.Index(fields=['coordinator', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.beneficiary.full_name} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Atualizar progresso automaticamente
        if self.total_sessions > 0:
            self.progress_percentage = int((self.attended_sessions / self.total_sessions) * 100)
        
        super().save(*args, **kwargs)
    
    # Propriedades calculadas
    @property
    def attendance_rate(self):
        """Taxa de presença"""
        if self.total_sessions == 0:
            return 0
        return (self.attended_sessions / self.total_sessions) * 100
    
    @property
    def is_active(self):
        """Verifica se a atividade está ativa"""
        return self.status == 'ATIVO'
    
    @property
    def is_overdue(self):
        """Verifica se está atrasada"""
        if self.end_date and self.status not in ['CONCLUIDO', 'CANCELADO']:
            return timezone.now().date() > self.end_date
        return False
    
    @property
    def days_remaining(self):
        """Dias restantes"""
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def social_impact_score(self):
        """Pontuação de impacto social"""
        if not self.social_objectives.exists():
            return 0
        
        # Cálculo baseado em presença e objetivos
        base_score = self.attendance_rate * 0.6  # 60% baseado em presença
        objectives_score = self.social_objectives.count() * 10  # 10 pontos por objetivo
        
        return min(base_score + objectives_score, 100)
    
    # Métodos de negócio
    def activate(self):
        """Ativa a atividade"""
        self.status = 'ATIVO'
        self.save(update_fields=['status'])
    
    def complete(self):
        """Marca como concluída"""
        self.status = 'CONCLUIDO'
        self.progress_percentage = 100
        self.save(update_fields=['status', 'progress_percentage'])
    
    def pause(self):
        """Pausa a atividade"""
        self.status = 'PAUSADO'
        self.save(update_fields=['status'])
    
    def cancel(self):
        """Cancela a atividade"""
        self.status = 'CANCELADO'
        self.save(update_fields=['status'])
    
    def add_session_attendance(self, attended=True):
        """Adiciona uma sessão e atualiza presença"""
        self.total_sessions += 1
        if attended:
            self.attended_sessions += 1
        self.save(update_fields=['total_sessions', 'attended_sessions', 'progress_percentage'])
    
    def get_recent_sessions(self, limit=5):
        """Retorna sessões recentes"""
        return self.sessions.order_by('-session_date')[:limit]
    
    def get_upcoming_sessions(self, limit=5):
        """Retorna próximas sessões"""
        today = timezone.now().date()
        return self.sessions.filter(session_date__gte=today).order_by('session_date')[:limit]


class ActivitySession(models.Model):
    """
    Sessão de atividade - modelo simplificado
    """
    
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Atividade'
    )
    
    # Informações básicas
    session_date = models.DateField('Data da Sessão')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    topic = models.CharField('Tópico/Tema', max_length=200)
    description = models.TextField('Descrição', blank=True)
    
    # Facilitação
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facilitated_sessions',
        verbose_name='Facilitador'
    )
    
    # Presença (simplificado para uma beneficiária)
    beneficiary_attended = models.BooleanField('Beneficiária Presente', default=False)
    arrival_time = models.TimeField('Horário de Chegada', null=True, blank=True)
    departure_time = models.TimeField('Horário de Saída', null=True, blank=True)
    attendance_notes = models.TextField('Observações de Presença', blank=True)
    
    # Avaliação rápida
    session_rating = models.IntegerField(
        'Avaliação da Sessão',
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    beneficiary_feedback = models.TextField('Feedback da Beneficiária', blank=True)
    facilitator_notes = models.TextField('Observações do Facilitador', blank=True)
    
    # Materiais
    materials_used = models.TextField('Materiais Utilizados', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Sessão de Atividade'
        verbose_name_plural = 'Sessões de Atividades'
        ordering = ['-session_date', '-start_time']
        unique_together = ['activity', 'session_date', 'start_time']
        indexes = [
            models.Index(fields=['activity', 'session_date']),
            models.Index(fields=['facilitator', 'session_date']),
        ]
    
    def __str__(self):
        return f"{self.activity.title} - {self.topic} ({self.session_date})"
    
    def save(self, *args, **kwargs):
        # Atualizar automaticamente a atividade pai
        super().save(*args, **kwargs)
        
        # Recalcular métricas da atividade
        self.activity.total_sessions = self.activity.sessions.count()
        self.activity.attended_sessions = self.activity.sessions.filter(beneficiary_attended=True).count()
        self.activity.save(update_fields=['total_sessions', 'attended_sessions', 'progress_percentage'])
    
    @property
    def duration_minutes(self):
        """Duração da sessão em minutos"""
        if self.start_time and self.end_time:
            start = timezone.datetime.combine(timezone.now().date(), self.start_time)
            end = timezone.datetime.combine(timezone.now().date(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    @property
    def actual_duration_minutes(self):
        """Duração real baseada em chegada e saída"""
        if self.arrival_time and self.departure_time:
            start = timezone.datetime.combine(timezone.now().date(), self.arrival_time)
            end = timezone.datetime.combine(timezone.now().date(), self.departure_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    @property
    def is_completed(self):
        """Verifica se a sessão já foi realizada"""
        return self.session_date < timezone.now().date()
    
    def mark_attendance(self, attended=True, arrival_time=None, departure_time=None, notes=''):
        """Marca presença da beneficiária"""
        self.beneficiary_attended = attended
        if arrival_time:
            self.arrival_time = arrival_time
        if departure_time:
            self.departure_time = departure_time
        if notes:
            self.attendance_notes = notes
        self.save()


class ActivityGoal(models.Model):
    """
    Objetivos específicos da atividade
    """
    
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name='Atividade'
    )
    
    title = models.CharField('Título do Objetivo', max_length=200)
    description = models.TextField('Descrição', blank=True)
    target_date = models.DateField('Data Alvo')
    is_achieved = models.BooleanField('Alcançado', default=False)
    achievement_date = models.DateField('Data de Conquista', null=True, blank=True)
    
    # Métricas
    target_value = models.DecimalField('Valor Alvo', max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField('Valor Atual', max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField('Unidade', max_length=50, blank=True)
    
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Objetivo da Atividade'
        verbose_name_plural = 'Objetivos das Atividades'
        ordering = ['target_date']
    
    def __str__(self):
        return f"{self.activity.title} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Percentual de progresso"""
        if self.target_value and self.current_value:
            return min((self.current_value / self.target_value) * 100, 100)
        return 0
    
    @property
    def is_overdue(self):
        """Verifica se está atrasado"""
        return self.target_date < timezone.now().date() and not self.is_achieved
    
    def achieve(self):
        """Marca como alcançado"""
        self.is_achieved = True
        self.achievement_date = timezone.now().date()
        self.save(update_fields=['is_achieved', 'achievement_date'])


class ActivityResource(models.Model):
    """
    Recursos utilizados na atividade
    """
    
    RESOURCE_TYPES = [
        ('MATERIAL', 'Material'),
        ('EQUIPAMENTO', 'Equipamento'),
        ('HUMANO', 'Recurso Humano'),
        ('FINANCEIRO', 'Financeiro'),
        ('DIGITAL', 'Digital'),
    ]
    
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name='Atividade'
    )
    
    name = models.CharField('Nome', max_length=200)
    resource_type = models.CharField('Tipo', max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField('Descrição', blank=True)
    quantity = models.IntegerField('Quantidade', default=1)
    cost = models.DecimalField('Custo', max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_available = models.BooleanField('Disponível', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'
        ordering = ['resource_type', 'name']
    
    def __str__(self):
        return f"{self.activity.title} - {self.name}"
