"""
Modelo unificado para atividades dos beneficiários.
Este modelo substitui e integra os modelos de Projects e Tasks,
criando uma visão centrada no beneficiário.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from datetime import date, timedelta
import uuid

from members.models import Beneficiary
from social.models import SocialAnamnesis


class BeneficiaryActivity(models.Model):
    """
    Modelo principal para atividades dos beneficiários.
    Substitui os modelos Project e Task, centralizando na beneficiária.
    """
    
    ACTIVITY_TYPES = [
        ('WORKSHOP', 'Workshop'),
        ('COURSE', 'Curso'),
        ('THERAPY', 'Terapia'),
        ('COUNSELING', 'Aconselhamento'),
        ('VOCATIONAL', 'Profissionalizante'),
        ('RECREATIONAL', 'Recreativa'),
        ('HEALTH', 'Saúde'),
        ('LEGAL', 'Jurídica'),
        ('SOCIAL', 'Social'),
        ('EDUCATIONAL', 'Educacional'),
        ('OTHER', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('PLANNED', 'Planejada'),
        ('ACTIVE', 'Ativa'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
        ('PAUSED', 'Pausada'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Baixa'),
        ('MEDIUM', 'Média'),
        ('HIGH', 'Alta'),
        ('URGENT', 'Urgente'),
    ]
    
    FREQUENCY_CHOICES = [
        ('UNIQUE', 'Única'),
        ('DAILY', 'Diária'),
        ('WEEKLY', 'Semanal'),
        ('BIWEEKLY', 'Quinzenal'),
        ('MONTHLY', 'Mensal'),
        ('QUARTERLY', 'Trimestral'),
        ('CUSTOM', 'Personalizada'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Beneficiária'
    )
    
    # Informações básicas
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    activity_type = models.CharField(
        'Tipo de Atividade',
        max_length=20,
        choices=ACTIVITY_TYPES,
        default='OTHER'
    )
    
    # Status e prioridade
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED'
    )
    priority = models.CharField(
        'Prioridade',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    
    # Programação
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Término', null=True, blank=True)
    frequency = models.CharField(
        'Frequência',
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='UNIQUE'
    )
    
    # Recursos e responsáveis
    facilitator = models.CharField('Facilitador/Responsável', max_length=100)
    location = models.CharField('Local', max_length=200)
    materials_needed = models.TextField('Materiais Necessários', blank=True)
    
    # Objetivos e resultados
    objectives = models.TextField('Objetivos')
    expected_outcomes = models.TextField('Resultados Esperados')
    
    # Integração com evolução social
    social_anamnesis = models.ForeignKey(
        SocialAnamnesis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name='Anamnese Social'
    )
    
    # Metadados
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_activities'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    # Campos para relatórios e métricas
    impact_score = models.IntegerField(
        'Pontuação de Impacto',
        default=0,
        help_text='Pontuação de impacto social (0-100)'
    )
    completion_percentage = models.IntegerField(
        'Percentual de Conclusão',
        default=0,
        help_text='Percentual de conclusão da atividade'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Atividade do Beneficiário'
        verbose_name_plural = 'Atividades dos Beneficiários'
        indexes = [
            models.Index(fields=['beneficiary', 'status']),
            models.Index(fields=['activity_type', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.beneficiary.full_name} - {self.title}"
    
    def clean(self):
        """Validações customizadas"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Data de início deve ser anterior à data de término")
        
        if self.completion_percentage < 0 or self.completion_percentage > 100:
            raise ValidationError("Percentual de conclusão deve estar entre 0 e 100")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    # Propriedades calculadas
    @property
    def is_active(self):
        """Verifica se a atividade está ativa"""
        return self.status == 'ACTIVE'
    
    @property
    def is_completed(self):
        """Verifica se a atividade está concluída"""
        return self.status == 'COMPLETED'
    
    @property
    def is_overdue(self):
        """Verifica se a atividade está atrasada"""
        if self.end_date and self.status not in ['COMPLETED', 'CANCELLED']:
            return self.end_date < date.today()
        return False
    
    @property
    def days_remaining(self):
        """Dias restantes para conclusão"""
        if self.end_date:
            return (self.end_date - date.today()).days
        return None
    
    @property
    def duration_days(self):
        """Duração em dias"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    @property
    def total_sessions(self):
        """Total de sessões"""
        return self.sessions.count()
    
    @property
    def completed_sessions(self):
        """Sessões concluídas"""
        return self.sessions.filter(status='COMPLETED').count()
    
    @property
    def attendance_rate(self):
        """Taxa de presença"""
        total_sessions = self.total_sessions
        if total_sessions == 0:
            return 0
        attended_sessions = self.sessions.filter(
            attendance__attended=True
        ).distinct().count()
        return (attended_sessions / total_sessions) * 100
    
    # Métodos de ação
    def activate(self):
        """Ativa a atividade"""
        self.status = 'ACTIVE'
        self.save(update_fields=['status'])
    
    def complete(self):
        """Marca como concluída"""
        self.status = 'COMPLETED'
        self.completion_percentage = 100
        self.save(update_fields=['status', 'completion_percentage'])
    
    def cancel(self):
        """Cancela a atividade"""
        self.status = 'CANCELLED'
        self.save(update_fields=['status'])
    
    def pause(self):
        """Pausa a atividade"""
        self.status = 'PAUSED'
        self.save(update_fields=['status'])
    
    def get_absolute_url(self):
        """URL absoluta da atividade"""
        return reverse('activities:detail', kwargs={'pk': self.pk})
    
    def calculate_impact_score(self):
        """Calcula pontuação de impacto baseada em métricas"""
        score = 0
        
        # Pontuação por presença
        if self.attendance_rate >= 80:
            score += 30
        elif self.attendance_rate >= 60:
            score += 20
        elif self.attendance_rate >= 40:
            score += 10
        
        # Pontuação por conclusão
        if self.completion_percentage >= 90:
            score += 25
        elif self.completion_percentage >= 70:
            score += 20
        elif self.completion_percentage >= 50:
            score += 15
        
        # Pontuação por tipo de atividade (algumas têm mais impacto)
        high_impact_types = ['THERAPY', 'COUNSELING', 'VOCATIONAL', 'LEGAL']
        if self.activity_type in high_impact_types:
            score += 15
        
        # Pontuação por feedback positivo
        positive_feedback = self.feedback_entries.filter(rating__gte=4).count()
        total_feedback = self.feedback_entries.count()
        if total_feedback > 0:
            feedback_rate = (positive_feedback / total_feedback) * 100
            if feedback_rate >= 80:
                score += 15
            elif feedback_rate >= 60:
                score += 10
        
        # Pontuação por evolução social
        if self.social_anamnesis:
            evolutions = self.social_anamnesis.evolutions.filter(
                evolution_date__gte=self.start_date
            ).count()
            if evolutions > 0:
                score += 15
        
        self.impact_score = min(score, 100)  # Máximo 100
        self.save(update_fields=['impact_score'])
        return self.impact_score


class ActivitySession(models.Model):
    """
    Sessão individual de uma atividade.
    Representa cada encontro/sessão da atividade.
    """
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Agendada'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
        ('RESCHEDULED', 'Reagendada'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Atividade'
    )
    
    # Informações da sessão
    session_number = models.PositiveIntegerField('Número da Sessão')
    title = models.CharField('Título da Sessão', max_length=200)
    description = models.TextField('Descrição', blank=True)
    
    # Programação
    session_date = models.DateField('Data da Sessão')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    
    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    # Recursos
    facilitator = models.CharField('Facilitador', max_length=100)
    location = models.CharField('Local', max_length=200)
    materials_used = models.TextField('Materiais Utilizados', blank=True)
    
    # Conteúdo e resultados
    content_covered = models.TextField('Conteúdo Abordado', blank=True)
    objectives_achieved = models.TextField('Objetivos Alcançados', blank=True)
    observations = models.TextField('Observações', blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        ordering = ['session_date', 'start_time']
        verbose_name = 'Sessão da Atividade'
        verbose_name_plural = 'Sessões das Atividades'
        unique_together = ['activity', 'session_number']
        indexes = [
            models.Index(fields=['activity', 'session_date']),
            models.Index(fields=['status', 'session_date']),
        ]
    
    def __str__(self):
        return f"{self.activity.title} - Sessão {self.session_number}"
    
    def clean(self):
        """Validações customizadas"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Horário de início deve ser anterior ao horário de término")
    
    @property
    def duration_minutes(self):
        """Duração em minutos"""
        if self.start_time and self.end_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    @property
    def is_completed(self):
        """Verifica se a sessão foi concluída"""
        return self.status == 'COMPLETED'
    
    @property
    def is_past_due(self):
        """Verifica se a sessão passou do prazo"""
        if self.session_date < date.today() and self.status not in ['COMPLETED', 'CANCELLED']:
            return True
        return False
    
    def complete(self):
        """Marca sessão como concluída"""
        self.status = 'COMPLETED'
        self.save(update_fields=['status'])
    
    def cancel(self):
        """Cancela a sessão"""
        self.status = 'CANCELLED'
        self.save(update_fields=['status'])
    
    def reschedule(self, new_date, new_start_time, new_end_time):
        """Reagenda a sessão"""
        self.session_date = new_date
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.status = 'RESCHEDULED'
        self.save(update_fields=['session_date', 'start_time', 'end_time', 'status'])


class ActivityAttendance(models.Model):
    """
    Controle de presença nas sessões.
    """
    
    # Identificação
    session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        related_name='attendance',
        verbose_name='Sessão'
    )
    
    # Presença
    attended = models.BooleanField('Presente', default=False)
    arrival_time = models.TimeField('Horário de Chegada', null=True, blank=True)
    departure_time = models.TimeField('Horário de Saída', null=True, blank=True)
    
    # Observações
    notes = models.TextField('Observações', blank=True)
    excuse_reason = models.TextField('Motivo da Falta', blank=True)
    
    # Metadados
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_attendances'
    )
    recorded_at = models.DateTimeField('Registrado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Presença na Atividade'
        verbose_name_plural = 'Presenças nas Atividades'
        unique_together = ['session']  # Um registro por sessão
    
    def __str__(self):
        status = "Presente" if self.attended else "Ausente"
        return f"{self.session.activity.beneficiary.full_name} - {self.session.title} - {status}"
    
    @property
    def duration_present(self):
        """Tempo presente em minutos"""
        if self.attended and self.arrival_time and self.departure_time:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.arrival_time)
            end = datetime.combine(date.today(), self.departure_time)
            return int((end - start).total_seconds() / 60)
        return 0


class ActivityFeedback(models.Model):
    """
    Feedback sobre a atividade.
    """
    
    RATING_CHOICES = [
        (1, 'Muito Insatisfeito'),
        (2, 'Insatisfeito'),
        (3, 'Neutro'),
        (4, 'Satisfeito'),
        (5, 'Muito Satisfeito'),
    ]
    
    # Identificação
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='feedback_entries',
        verbose_name='Atividade'
    )
    
    # Avaliação
    rating = models.IntegerField(
        'Avaliação Geral',
        choices=RATING_CHOICES,
        default=5
    )
    content_quality = models.IntegerField(
        'Qualidade do Conteúdo',
        choices=RATING_CHOICES,
        default=5
    )
    facilitator_rating = models.IntegerField(
        'Avaliação do Facilitador',
        choices=RATING_CHOICES,
        default=5
    )
    
    # Comentários
    positive_aspects = models.TextField('Aspectos Positivos', blank=True)
    improvements_suggested = models.TextField('Sugestões de Melhoria', blank=True)
    additional_comments = models.TextField('Comentários Adicionais', blank=True)
    
    # Recomendação
    would_recommend = models.BooleanField('Recomendaria para outros', default=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback da Atividade'
        verbose_name_plural = 'Feedbacks das Atividades'
        unique_together = ['activity']  # Um feedback por atividade
    
    def __str__(self):
        return f"{self.activity.title} - {self.rating}/5"
    
    @property
    def average_rating(self):
        """Média das avaliações"""
        return (self.rating + self.content_quality + self.facilitator_rating) / 3


class ActivityNote(models.Model):
    """
    Notas e observações sobre a atividade.
    """
    
    NOTE_TYPES = [
        ('GENERAL', 'Geral'),
        ('PROGRESS', 'Progresso'),
        ('CONCERN', 'Preocupação'),
        ('ACHIEVEMENT', 'Conquista'),
        ('FOLLOW_UP', 'Acompanhamento'),
    ]
    
    # Identificação
    activity = models.ForeignKey(
        BeneficiaryActivity,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Atividade'
    )
    
    # Conteúdo
    note_type = models.CharField(
        'Tipo de Nota',
        max_length=20,
        choices=NOTE_TYPES,
        default='GENERAL'
    )
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    
    # Visibilidade
    is_confidential = models.BooleanField('Confidencial', default=False)
    
    # Metadados
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_notes'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nota da Atividade'
        verbose_name_plural = 'Notas das Atividades'
    
    def __str__(self):
        return f"{self.activity.title} - {self.title}"
