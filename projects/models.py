# Copilot: modelo ProjectEnrollment.
# Campos: beneficiary FK, project_name Char(80), weekday PositiveSmallInteger choices 0-6,
# shift Char choices MANHA/TARDE/NOITE, start_time TimeField,
# status Char choices ATIVO/DESLIGADO,
# enrollment_code SlugField(unique, editable=False), created_at auto_now_add.
# Método save(): gerar enrollment_code = slugify(f"{project_name}-{beneficiary.id}-{created_at.timestamp()}").

from django.db import models
from django.utils.text import slugify
from members.models import Beneficiary


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
    project_name = models.CharField('Nome do Projeto', max_length=80)
    # project_manager = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True,
    #                                   related_name='managed_projects', 
    #                                   verbose_name='Gerente do Projeto',
    #                                   help_text='Funcionário responsável pela gestão do projeto')  # HR DESABILITADO
    weekday = models.PositiveSmallIntegerField('Dia da Semana', choices=WEEKDAY_CHOICES)
    shift = models.CharField('Turno', max_length=10, choices=SHIFT_CHOICES)
    start_time = models.TimeField('Horário de Início')
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ATIVO')
    enrollment_code = models.SlugField('Código de Matrícula', unique=True, editable=False)
    created_at = models.DateTimeField('Data de Matrícula', auto_now_add=True)

    class Meta:
        ordering = ['project_name', 'weekday', 'start_time']
        verbose_name = 'Matrícula em Projeto'
        verbose_name_plural = 'Matrículas em Projetos'

    def __str__(self):
        return f"{self.beneficiary.full_name} - {self.project_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.enrollment_code:
            # Salvar primeiro para obter o created_at
            super().save(*args, **kwargs)
            # Gerar código único baseado nos dados
            timestamp = int(self.created_at.timestamp())
            code_base = f"{self.project_name}-{self.beneficiary.id}-{timestamp}"
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
