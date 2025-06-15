from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from members.models import Beneficiary


class Workshop(models.Model):
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
        total_possible = sum(session.enrollments.count() for session in self.sessions.all())
        total_present = sum(session.attendances.filter(present=True).count() for session in self.sessions.all())
        return (total_present / total_possible * 100) if total_possible > 0 else 0


class WorkshopSession(models.Model):
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.PositiveIntegerField('Número da Sessão')
    date = models.DateField('Data da Sessão')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    topic = models.CharField('Tópico/Tema', max_length=200)
    content_covered = models.TextField('Conteúdo Abordado', blank=True)
    materials_used = models.TextField('Materiais Utilizados', blank=True)
    observations = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['session_number']
        verbose_name = 'Sessão da Oficina'
        verbose_name_plural = 'Sessões da Oficina'
        unique_together = ['workshop', 'session_number']

    def __str__(self):
        return f"{self.workshop.name} - Sessão {self.session_number}"

    @property
    def attendance_count(self):
        return self.attendances.filter(present=True).count()

    @property
    def attendance_percentage(self):
        total = self.attendances.count()
        present = self.attendances.filter(present=True).count()
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
    completion_date = models.DateField('Data de Conclusão', null=True, blank=True)
    final_grade = models.DecimalField('Nota Final', max_digits=4, decimal_places=2, null=True, blank=True,
                                    validators=[MinValueValidator(0), MaxValueValidator(10)])
    certificate_issued = models.BooleanField('Certificado Emitido', default=False)
    observations = models.TextField('Observações', blank=True)
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
        present_sessions = self.attendances.filter(present=True).count()
        return (present_sessions / total_sessions * 100) if total_sessions > 0 else 0


class SessionAttendance(models.Model):
    session = models.ForeignKey(WorkshopSession, on_delete=models.CASCADE, related_name='attendances')
    enrollment = models.ForeignKey(WorkshopEnrollment, on_delete=models.CASCADE, related_name='attendances')
    present = models.BooleanField('Presente', default=False)
    late = models.BooleanField('Chegou Atrasado', default=False)
    left_early = models.BooleanField('Saiu Mais Cedo', default=False)
    participation_quality = models.CharField('Qualidade da Participação', max_length=20, choices=[
        ('excelente', 'Excelente'),
        ('boa', 'Boa'),
        ('regular', 'Regular'),
        ('baixa', 'Baixa'),
    ], blank=True)
    notes = models.TextField('Observações sobre a Participação', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['session__session_number']
        verbose_name = 'Presença em Sessão'
        verbose_name_plural = 'Presenças em Sessões'
        unique_together = ['session', 'enrollment']

    def __str__(self):
        status = "Presente" if self.present else "Ausente"
        return f"{self.enrollment.beneficiary.full_name} - {self.session} - {status}"


class WorkshopEvaluation(models.Model):
    EVALUATION_TYPES = [
        ('inicial', 'Avaliação Inicial'),
        ('processual', 'Avaliação Processual'),
        ('final', 'Avaliação Final'),
    ]

    enrollment = models.ForeignKey(WorkshopEnrollment, on_delete=models.CASCADE, related_name='evaluations')
    evaluation_type = models.CharField('Tipo de Avaliação', max_length=20, choices=EVALUATION_TYPES)
    date = models.DateField('Data da Avaliação')
    
    # Critérios de avaliação (escala 1-5)
    technical_skills = models.PositiveIntegerField('Habilidades Técnicas', 
                                                 validators=[MinValueValidator(1), MaxValueValidator(5)])
    creativity = models.PositiveIntegerField('Criatividade',
                                           validators=[MinValueValidator(1), MaxValueValidator(5)])
    participation = models.PositiveIntegerField('Participação',
                                              validators=[MinValueValidator(1), MaxValueValidator(5)])
    collaboration = models.PositiveIntegerField('Colaboração',
                                              validators=[MinValueValidator(1), MaxValueValidator(5)])
    punctuality = models.PositiveIntegerField('Pontualidade',
                                            validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    strengths = models.TextField('Pontos Fortes')
    improvement_areas = models.TextField('Áreas para Melhoria')
    recommendations = models.TextField('Recomendações', blank=True)
    evaluator = models.CharField('Avaliador', max_length=100)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Avaliação de Oficina'
        verbose_name_plural = 'Avaliações de Oficinas'

    def __str__(self):
        return f"{self.enrollment} - {self.get_evaluation_type_display()} - {self.date}"

    @property
    def overall_score(self):
        return (self.technical_skills + self.creativity + self.participation + 
                self.collaboration + self.punctuality) / 5
