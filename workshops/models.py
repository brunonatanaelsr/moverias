from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from members.models import Beneficiary
from core.optimized_managers import WorkshopManager


class Workshop(models.Model):

    objects = models.Manager()  # Manager padrão
    optimized_objects = WorkshopManager()

    WORKSHOP_TYPES = [
        ('artesanato', 'Artesanato'),
        ('culinaria', 'Culinária'),
        ('costura', 'Costura'),
        ('informatica', 'Informática'),
        ('empreendedorismo', 'Empreendedorismo'),
        ('capacitacao', 'Capacitação Profissional'),
        ('terapeutica', 'Terapêutica'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('planejamento', 'Em Planejamento'),
        ('ativo', 'Ativo'),
        ('pausado', 'Pausado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    name = models.CharField('Nome da Oficina', max_length=200)
    description = models.TextField('Descrição')
    workshop_type = models.CharField('Tipo de Oficina', max_length=20, choices=WORKSHOP_TYPES)
    facilitator = models.CharField('Facilitador(a)', max_length=100)
    location = models.CharField('Local', max_length=200)
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Término', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='planejamento')
    max_participants = models.PositiveIntegerField('Máximo de Participantes', default=20)
    objectives = models.TextField('Objetivos da Oficina')
    materials_needed = models.TextField('Materiais Necessários', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Oficina'
        verbose_name_plural = 'Oficinas'

    def __str__(self):
        return f"{self.name} - {self.facilitator}"

    @property
    def total_sessions(self):
        return self.sessions.count()

    @property
    def total_participants(self):
        return self.enrollments.filter(status='ativo').count()

    @property
    def attendance_rate(self):
        total_possible = 0
        total_present = 0
        for session in self.sessions.all():
            session_attendances = session.attendances.all()
            total_possible += session_attendances.count()
            total_present += session_attendances.filter(attended=True).count()
        return (total_present / total_possible * 100) if total_possible > 0 else 0


class WorkshopSession(models.Model):
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField('Data da Sessão')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    topic = models.CharField('Tópico/Tema', max_length=200)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['session_date', 'start_time']
        verbose_name = 'Sessão da Oficina'
        verbose_name_plural = 'Sessões da Oficina'

    def __str__(self):
        return f"{self.workshop.name} - {self.topic} ({self.session_date})"

    @property
    def attendance_count(self):
        return self.attendances.filter(attended=True).count()

    @property
    def attendance_percentage(self):
        total = self.attendances.count()
        present = self.attendances.filter(attended=True).count()
        return (present / total * 100) if total > 0 else 0


class WorkshopEnrollment(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('concluido', 'Concluído'),
        ('desistente', 'Desistente'),
        ('transferido', 'Transferido'),
    ]

    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='enrollments')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='workshop_enrollments')
    enrollment_date = models.DateField('Data de Inscrição')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ativo')
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-enrollment_date']
        verbose_name = 'Inscrição em Oficina'
        verbose_name_plural = 'Inscrições em Oficinas'
        unique_together = ['workshop', 'beneficiary']

    def __str__(self):
        return f"{self.beneficiary.full_name} - {self.workshop.name}"

    @property
    def attendance_rate(self):
        total_sessions = self.attendances.count()
        present_sessions = self.attendances.filter(attended=True).count()
        return (present_sessions / total_sessions * 100) if total_sessions > 0 else 0


class SessionAttendance(models.Model):
    session = models.ForeignKey(WorkshopSession, on_delete=models.CASCADE, related_name='attendances')
    enrollment = models.ForeignKey(WorkshopEnrollment, on_delete=models.CASCADE, related_name='attendances')
    attended = models.BooleanField('Presente', default=False)
    notes = models.TextField('Observações sobre a Participação', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['session__session_date']
        verbose_name = 'Presença em Sessão'
        verbose_name_plural = 'Presenças em Sessões'
        unique_together = ['session', 'enrollment']

    def __str__(self):
        status = "Presente" if self.attended else "Ausente"
        return f"{self.enrollment.beneficiary.full_name} - {self.session} - {status}"


class WorkshopEvaluation(models.Model):
    enrollment = models.ForeignKey(WorkshopEnrollment, on_delete=models.CASCADE, related_name='evaluations')
    rating = models.PositiveIntegerField('Avaliação (1-5)', 
                                       validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback = models.TextField('Feedback sobre a oficina')
    suggestions = models.TextField('Sugestões para melhorias', blank=True)
    evaluation_date = models.DateTimeField('Data da Avaliação', auto_now_add=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-evaluation_date']
        verbose_name = 'Avaliação de Oficina'
        verbose_name_plural = 'Avaliações de Oficinas'

    def __str__(self):
        return f"{self.enrollment} - Avaliação: {self.rating}/5"
