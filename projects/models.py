# Copilot: modelo ProjectEnrollment.
# Campos: beneficiary FK, project_name Char(80), weekday PositiveSmallInteger choices 0-6,
# shift Char choices MANHA/TARDE/NOITE, start_time TimeField,
# status Char choices ATIVO/DESLIGADO,
# enrollment_code SlugField(unique, editable=False), created_at auto_now_add.
# Método save(): gerar enrollment_code = slugify(f"{project_name}-{beneficiary.id}-{created_at.timestamp()}").

from django.db import models
from django.utils.text import slugify
from members.models import Beneficiary
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Avg


class Project(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('PAUSADO', 'Pausado'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    name = models.CharField('Nome do Projeto', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True, null=True)
    coordinator = models.CharField('Coordenador', max_length=100)
    location = models.CharField('Local', max_length=200)
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Término', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    max_participants = models.PositiveIntegerField('Máximo de Participantes', default=30)
    objectives = models.TextField('Objetivos do Projeto')
    target_audience = models.CharField('Público Alvo', max_length=200)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return self.name
    
    @property
    def total_participants(self):
        """Número total de participantes ativos"""
        return self.enrollments.filter(status='ATIVO').count()
    
    @property
    def total_sessions(self):
        """Número total de sessões"""
        return self.sessions.count()
    
    @property
    def attendance_rate(self):
        """Taxa de presença geral do projeto"""
        total_possible = 0
        total_present = 0
        
        for session in self.sessions.all():
            attendances = session.attendances.all()
            total_possible += attendances.count()
            total_present += attendances.filter(attended=True).count()
        
        return (total_present / total_possible * 100) if total_possible > 0 else 0
    
    @property
    def is_active(self):
        """Verifica se o projeto está ativo"""
        return self.status == 'ATIVO'
    
    def get_active_participants(self):
        """Retorna participantes ativos"""
        return self.enrollments.filter(status='ATIVO')
    
    def get_completion_rate(self):
        """Taxa de conclusão do projeto"""
        total_enrollments = self.enrollments.count()
        completed_enrollments = self.enrollments.filter(status='CONCLUIDO').count()
        return (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0


class ProjectSession(models.Model):
    """Sessão de um projeto"""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Projeto'
    )
    session_date = models.DateField('Data da Sessão')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    topic = models.CharField('Tópico/Tema', max_length=200)
    description = models.TextField('Descrição da Sessão', blank=True)
    facilitator = models.CharField('Facilitador', max_length=100)
    location = models.CharField('Local', max_length=200, blank=True)
    materials_needed = models.TextField('Materiais Necessários', blank=True)
    notes = models.TextField('Observações', blank=True)
    is_mandatory = models.BooleanField('Sessão Obrigatória', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['session_date', 'start_time']
        verbose_name = 'Sessão do Projeto'
        verbose_name_plural = 'Sessões do Projeto'
        unique_together = ['project', 'session_date', 'start_time']
    
    def __str__(self):
        return f"{self.project.name} - {self.topic} ({self.session_date})"
    
    def clean(self):
        """Validações customizadas"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Horário de início deve ser anterior ao horário de término")
    
    @property
    def duration(self):
        """Duração da sessão em minutos"""
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    @property
    def attendance_count(self):
        """Número de participantes presentes"""
        return self.attendances.filter(attended=True).count()
    
    @property
    def attendance_percentage(self):
        """Percentual de presença na sessão"""
        total = self.attendances.count()
        present = self.attendances.filter(attended=True).count()
        return (present / total * 100) if total > 0 else 0
    
    @property
    def is_completed(self):
        """Verifica se a sessão já foi realizada"""
        return self.session_date < date.today()


class ProjectAttendance(models.Model):
    """Presença em sessão de projeto"""
    
    session = models.ForeignKey(
        ProjectSession,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Sessão'
    )
    enrollment = models.ForeignKey(
        'ProjectEnrollment',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Inscrição'
    )
    attended = models.BooleanField('Presente', default=False)
    arrival_time = models.TimeField('Horário de Chegada', null=True, blank=True)
    departure_time = models.TimeField('Horário de Saída', null=True, blank=True)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        ordering = ['session__session_date', 'enrollment__beneficiary__full_name']
        verbose_name = 'Presença'
        verbose_name_plural = 'Presenças'
        unique_together = ['session', 'enrollment']
    
    def __str__(self):
        status = "Presente" if self.attended else "Ausente"
        return f"{self.enrollment.beneficiary.full_name} - {self.session} - {status}"
    
    @property
    def duration_present(self):
        """Tempo presente na sessão em minutos"""
        if self.attended and self.arrival_time and self.departure_time:
            start = datetime.combine(date.today(), self.arrival_time)
            end = datetime.combine(date.today(), self.departure_time)
            return int((end - start).total_seconds() / 60)
        return 0


class ProjectEvaluation(models.Model):
    """Avaliação de projeto"""
    
    enrollment = models.ForeignKey(
        'ProjectEnrollment',
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='Inscrição'
    )
    session = models.ForeignKey(
        ProjectSession,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='Sessão',
        null=True,
        blank=True
    )
    rating = models.PositiveIntegerField(
        'Avaliação (1-5)',
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    content_quality = models.PositiveIntegerField(
        'Qualidade do Conteúdo (1-5)',
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    facilitator_rating = models.PositiveIntegerField(
        'Avaliação do Facilitador (1-5)',
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    feedback = models.TextField('Feedback')
    suggestions = models.TextField('Sugestões', blank=True)
    would_recommend = models.BooleanField('Recomendaria para outros', default=True)
    evaluation_date = models.DateTimeField('Data da Avaliação', auto_now_add=True)
    
    class Meta:
        ordering = ['-evaluation_date']
        verbose_name = 'Avaliação de Projeto'
        verbose_name_plural = 'Avaliações de Projetos'
    
    def __str__(self):
        return f"{self.enrollment} - Avaliação: {self.rating}/5"


class ProjectResource(models.Model):
    """Recursos do projeto"""
    
    RESOURCE_TYPES = [
        ('material', 'Material'),
        ('equipamento', 'Equipamento'),
        ('local', 'Local'),
        ('humano', 'Recurso Humano'),
        ('financeiro', 'Financeiro'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name='Projeto'
    )
    name = models.CharField('Nome do Recurso', max_length=100)
    resource_type = models.CharField('Tipo', max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField('Descrição')
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    cost = models.DecimalField('Custo', max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField('Fornecedor', max_length=100, blank=True)
    acquisition_date = models.DateField('Data de Aquisição', null=True, blank=True)
    is_available = models.BooleanField('Disponível', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['project__name', 'resource_type', 'name']
        verbose_name = 'Recurso do Projeto'
        verbose_name_plural = 'Recursos do Projeto'
    
    def __str__(self):
        return f"{self.project.name} - {self.name} ({self.get_resource_type_display()})"


class ProjectEnrollment(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    SHIFT_CHOICES = [
        ('MANHA', 'Manhã'),
        ('TARDE', 'Tarde'),
        ('NOITE', 'Noite'),
    ]
    
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('DESLIGADO', 'Desligado'),
    ]
    
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='project_enrollments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Projeto')
    weekday = models.PositiveSmallIntegerField('Dia da Semana', choices=WEEKDAY_CHOICES)
    shift = models.CharField('Turno', max_length=10, choices=SHIFT_CHOICES)
    start_time = models.TimeField('Horário de Início')
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ATIVO')
    enrollment_code = models.SlugField('Código de Matrícula', unique=True, editable=False)
    created_at = models.DateTimeField('Data de Matrícula', auto_now_add=True)

    class Meta:
        ordering = ['project__name', 'weekday', 'start_time']
        verbose_name = 'Matrícula em Projeto'
        verbose_name_plural = 'Matrículas em Projetos'

    def __str__(self):
        project_name_str = self.project.name if self.project_id and self.project else "Projeto não definido"
        return f"{self.beneficiary.full_name} - {project_name_str} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.enrollment_code:
            # Salvar primeiro para obter o created_at
            super().save(*args, **kwargs)
            # Gerar código único baseado nos dados
            timestamp = int(self.created_at.timestamp())
            code_base = f"{self.project.name}-{self.beneficiary.id}-{timestamp}"
            self.enrollment_code = slugify(code_base)
            # Salvar novamente com o código
            super().save(update_fields=['enrollment_code'])
        else:
            super().save(*args, **kwargs)

    @property
    def weekday_display(self):
        return self.get_weekday_display()

    @property
    def shift_display(self):
        return self.get_shift_display()

    @property
    def is_active(self):
        return self.status == 'ATIVO'
    
    @property
    def attendance_rate(self):
        """Taxa de presença do participante"""
        total_sessions = self.attendances.count()
        present_sessions = self.attendances.filter(attended=True).count()
        return (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    @property
    def total_sessions_attended(self):
        """Total de sessões presentes"""
        return self.attendances.filter(attended=True).count()
    
    @property
    def total_sessions_missed(self):
        """Total de sessões faltadas"""
        return self.attendances.filter(attended=False).count()
    
    @property
    def can_receive_certificate(self):
        """Verifica se pode receber certificado (75% de presença)"""
        return self.attendance_rate >= 75
    
    def get_monthly_attendance(self, year, month):
        """Presença mensal"""
        return self.attendances.filter(
            session__session_date__year=year,
            session__session_date__month=month,
            attended=True
        ).count()
    
    def activate(self):
        """Ativa inscrição"""
        self.status = 'ATIVO'
        self.save(update_fields=['status'])
    
    def deactivate(self):
        """Desativa inscrição"""
        self.status = 'DESLIGADO'
        self.save(update_fields=['status'])
    
    def complete(self):
        """Marca como concluída"""
        self.status = 'CONCLUIDO'
        self.save(update_fields=['status'])


class ProjectMilestone(models.Model):
    """Marcos/Metas do projeto"""
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
        ('ATRASADO', 'Atrasado'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='Projeto'
    )
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    target_date = models.DateField('Data Prevista')
    completion_date = models.DateField('Data de Conclusão', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    responsible = models.CharField('Responsável', max_length=100)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['target_date']
        verbose_name = 'Marco do Projeto'
        verbose_name_plural = 'Marcos do Projeto'
    
    def __str__(self):
        return f"{self.project.name} - {self.title}"
    
    @property
    def is_overdue(self):
        """Verifica se está atrasado"""
        return self.target_date < date.today() and self.status != 'CONCLUIDO'
    
    @property
    def days_until_deadline(self):
        """Dias até o prazo"""
        return (self.target_date - date.today()).days
    
    def mark_completed(self):
        """Marca como concluído"""
        self.status = 'CONCLUIDO'
        self.completion_date = date.today()
        self.save(update_fields=['status', 'completion_date'])


class ProjectReport(models.Model):
    """Relatório do projeto"""
    
    REPORT_TYPES = [
        ('MENSAL', 'Mensal'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
        ('FINAL', 'Final'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Projeto'
    )
    report_type = models.CharField('Tipo de Relatório', max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField('Início do Período')
    period_end = models.DateField('Fim do Período')
    summary = models.TextField('Resumo Executivo')
    achievements = models.TextField('Conquistas')
    challenges = models.TextField('Desafios')
    metrics = models.JSONField('Métricas', default=dict)
    recommendations = models.TextField('Recomendações', blank=True)
    created_by = models.CharField('Criado por', max_length=100)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['-period_end']
        verbose_name = 'Relatório do Projeto'
        verbose_name_plural = 'Relatórios do Projeto'
    
    def __str__(self):
        return f"{self.project.name} - {self.get_report_type_display()} ({self.period_start} - {self.period_end})"


class ProjectBudget(models.Model):
    """Orçamento do projeto"""
    
    CATEGORY_CHOICES = [
        ('MATERIAL', 'Material'),
        ('EQUIPAMENTO', 'Equipamento'),
        ('RECURSO_HUMANO', 'Recurso Humano'),
        ('TRANSPORTE', 'Transporte'),
        ('ALIMENTACAO', 'Alimentação'),
        ('OUTROS', 'Outros'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='budget_items',
        verbose_name='Projeto'
    )
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField('Descrição', max_length=200)
    planned_amount = models.DecimalField('Valor Planejado', max_digits=10, decimal_places=2)
    actual_amount = models.DecimalField('Valor Real', max_digits=10, decimal_places=2, default=0)
    date_planned = models.DateField('Data Planejada')
    date_actual = models.DateField('Data Real', null=True, blank=True)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        ordering = ['date_planned']
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'
    
    def __str__(self):
        return f"{self.project.name} - {self.description}"
    
    @property
    def variance(self):
        """Variação entre planejado e real"""
        return self.actual_amount - self.planned_amount
    
    @property
    def variance_percentage(self):
        """Percentual de variação"""
        return (self.variance / self.planned_amount * 100) if self.planned_amount > 0 else 0
