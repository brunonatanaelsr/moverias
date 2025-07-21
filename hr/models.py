from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
import uuid


class Department(models.Model):
    """Departamentos do instituto"""
    name = models.CharField('Nome do Departamento', max_length=100)
    description = models.TextField('Descrição', blank=True)
    manager = models.ForeignKey(
        'Employee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_departments',
        verbose_name='Responsável'
    )
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['name']

    def __str__(self):
        return self.name


class JobPosition(models.Model):
    """Cargos/Posições no instituto"""
    title = models.CharField('Título do Cargo', max_length=100)
    description = models.TextField('Descrição', blank=True)
    requirements = models.TextField('Requisitos', blank=True)
    responsibilities = models.TextField('Responsabilidades', blank=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='positions',
        verbose_name='Departamento'
    )
    salary_range_min = models.DecimalField('Salário Mínimo', max_digits=10, decimal_places=2, null=True, blank=True)
    salary_range_max = models.DecimalField('Salário Máximo', max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.department.name}"


class Employee(models.Model):
    """Funcionários do instituto"""
    EMPLOYMENT_TYPE_CHOICES = [
        ('clt', 'CLT'),
        ('pj', 'Pessoa Jurídica'),
        ('volunteer', 'Voluntário'),
        ('intern', 'Estagiário'),
        ('temporary', 'Temporário'),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('vacation', 'Em Férias'),
        ('medical_leave', 'Afastamento Médico'),
        ('maternity_leave', 'Licença Maternidade'),
        ('terminated', 'Desligado'),
    ]

    GENDER_CHOICES = [
        ('F', 'Feminino'),
        ('M', 'Masculino'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Solteiro(a)'),
        ('married', 'Casado(a)'),
        ('divorced', 'Divorciado(a)'),
        ('widowed', 'Viúvo(a)'),
        ('union', 'União Estável'),
    ]

    # Informações Pessoais
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='Usuário do Sistema'
    )
    employee_number = models.CharField('Número de Matrícula', max_length=20, unique=True)
    full_name = models.CharField('Nome Completo', max_length=200)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[
        RegexValidator(regex=r'\d{3}\.\d{3}\.\d{3}-\d{2}', message='CPF deve estar no formato 000.000.000-00')
    ])
    rg = models.CharField('RG', max_length=20, blank=True)
    birth_date = models.DateField('Data de Nascimento')
    gender = models.CharField('Gênero', max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField('Estado Civil', max_length=20, choices=MARITAL_STATUS_CHOICES)
    
    # Contato
    phone = models.CharField('Telefone', max_length=20)
    personal_email = models.EmailField('Email Pessoal', blank=True)
    address = models.TextField('Endereço Completo')
    city = models.CharField('Cidade', max_length=100)
    state = models.CharField('Estado', max_length=2)
    zip_code = models.CharField('CEP', max_length=10)
    
    # Contato de Emergência
    emergency_contact_name = models.CharField('Nome do Contato de Emergência', max_length=200)
    emergency_contact_relationship = models.CharField('Parentesco', max_length=50)
    emergency_contact_phone = models.CharField('Telefone de Emergência', max_length=20)
    
    # Informações Profissionais
    job_position = models.ForeignKey(
        JobPosition, 
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Cargo'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Departamento'
    )
    direct_supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='subordinates',
        verbose_name='Supervisor Direto'
    )
    
    employment_type = models.CharField('Tipo de Vínculo', max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    employment_status = models.CharField('Status', max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    hire_date = models.DateField('Data de Admissão')
    termination_date = models.DateField('Data de Desligamento', null=True, blank=True)
    salary = models.DecimalField('Salário', max_digits=10, decimal_places=2)
    
    # Documentos e Benefícios
    pis_pasep = models.CharField('PIS/PASEP', max_length=20, blank=True)
    work_permit = models.CharField('Carteira de Trabalho', max_length=20, blank=True)
    has_health_insurance = models.BooleanField('Possui Plano de Saúde', default=False)
    has_dental_insurance = models.BooleanField('Possui Plano Odontológico', default=False)
    has_life_insurance = models.BooleanField('Possui Seguro de Vida', default=False)
    
    # Formação e Competências
    education_level = models.CharField('Escolaridade', max_length=100, blank=True)
    skills = models.TextField('Habilidades e Competências', blank=True)
    certifications = models.TextField('Certificações', blank=True)
    languages = models.TextField('Idiomas', blank=True)
    
    # Observações e Notas
    notes = models.TextField('Observações', blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_employees',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} - {self.job_position.title}"

    @property
    def age(self):
        """Calcula a idade do funcionário"""
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def years_of_service(self):
        """Calcula anos de serviço"""
        end_date = self.termination_date if self.termination_date else date.today()
        return end_date.year - self.hire_date.year - ((end_date.month, end_date.day) < (self.hire_date.month, self.hire_date.day))

    @property
    def is_supervisor(self):
        """Verifica se é supervisor de alguém"""
        return self.subordinates.exists()

    def get_subordinates(self):
        """Retorna subordinados diretos"""
        return self.subordinates.filter(employment_status='active')


class EmployeeDocument(models.Model):
    """Documentos dos funcionários"""
    DOCUMENT_TYPE_CHOICES = [
        ('contract', 'Contrato de Trabalho'),
        ('resume', 'Currículo'),
        ('id_copy', 'Cópia de Documento'),
        ('diploma', 'Diploma'),
        ('certificate', 'Certificado'),
        ('medical', 'Atestado Médico'),
        ('other', 'Outro'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Funcionário'
    )
    document_type = models.CharField('Tipo de Documento', max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    file = models.FileField('Arquivo', upload_to='hr/documents/%Y/%m/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Enviado por'
    )
    uploaded_at = models.DateTimeField('Data de Upload', auto_now_add=True)
    is_confidential = models.BooleanField('Confidencial', default=False)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"


class PerformanceReview(models.Model):
    """Avaliações de desempenho"""
    REVIEW_TYPE_CHOICES = [
        ('annual', 'Anual'),
        ('probation', 'Período de Experiência'),
        ('promotion', 'Promoção'),
        ('disciplinary', 'Disciplinar'),
        ('project', 'Por Projeto'),
    ]

    RATING_CHOICES = [
        (1, 'Insatisfatório'),
        (2, 'Abaixo da Expectativa'),
        (3, 'Atende Expectativa'),
        (4, 'Supera Expectativa'),
        (5, 'Excepcional'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='performance_reviews',
        verbose_name='Funcionário'
    )
    review_type = models.CharField('Tipo de Avaliação', max_length=20, choices=REVIEW_TYPE_CHOICES)
    review_period_start = models.DateField('Início do Período')
    review_period_end = models.DateField('Fim do Período')
    
    # Critérios de Avaliação
    technical_skills = models.IntegerField('Habilidades Técnicas', choices=RATING_CHOICES)
    communication = models.IntegerField('Comunicação', choices=RATING_CHOICES)
    teamwork = models.IntegerField('Trabalho em Equipe', choices=RATING_CHOICES)
    leadership = models.IntegerField('Liderança', choices=RATING_CHOICES, null=True, blank=True)
    punctuality = models.IntegerField('Pontualidade', choices=RATING_CHOICES)
    productivity = models.IntegerField('Produtividade', choices=RATING_CHOICES)
    
    # Comentários
    strengths = models.TextField('Pontos Fortes', blank=True)
    areas_for_improvement = models.TextField('Áreas para Melhoria', blank=True)
    goals_for_next_period = models.TextField('Metas para Próximo Período', blank=True)
    employee_comments = models.TextField('Comentários do Funcionário', blank=True)
    
    # Metadados
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_reviews',
        verbose_name='Avaliado por'
    )
    review_date = models.DateField('Data da Avaliação')
    is_final = models.BooleanField('Avaliação Finalizada', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Avaliação de Desempenho'
        verbose_name_plural = 'Avaliações de Desempenho'
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_review_type_display()} ({self.review_date.year})"

    @property
    def overall_rating(self):
        """Calcula nota geral"""
        ratings = [self.technical_skills, self.communication, self.teamwork, self.punctuality, self.productivity]
        if self.leadership:
            ratings.append(self.leadership)
        return sum(ratings) / len(ratings)


class TrainingRecord(models.Model):
    """Registro de treinamentos e capacitações"""
    TRAINING_TYPE_CHOICES = [
        ('internal', 'Treinamento Interno'),
        ('external', 'Treinamento Externo'),
        ('online', 'Curso Online'),
        ('conference', 'Conferência/Seminário'),
        ('workshop', 'Workshop'),
        ('certification', 'Certificação'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planejado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='training_records',
        verbose_name='Funcionário'
    )
    training_name = models.CharField('Nome do Treinamento', max_length=200)
    training_type = models.CharField('Tipo', max_length=20, choices=TRAINING_TYPE_CHOICES)
    provider = models.CharField('Provedor/Instituição', max_length=200, blank=True)
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Conclusão', null=True, blank=True)
    hours = models.IntegerField('Carga Horária', null=True, blank=True)
    cost = models.DecimalField('Custo', max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='planned')
    certificate_obtained = models.BooleanField('Certificado Obtido', default=False)
    notes = models.TextField('Observações', blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Registro de Treinamento'
        verbose_name_plural = 'Registros de Treinamentos'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.training_name}"


class OnboardingProgram(models.Model):
    """Programa de Onboarding para novos funcionários"""
    PROGRAM_STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('draft', 'Rascunho'),
    ]

    name = models.CharField('Nome do Programa', max_length=200)
    description = models.TextField('Descrição')
    duration_days = models.PositiveIntegerField('Duração em Dias', default=30)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='onboarding_programs',
        verbose_name='Departamento'
    )
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_onboarding_programs',
        verbose_name='Responsável'
    )
    status = models.CharField('Status', max_length=20, choices=PROGRAM_STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Programa de Onboarding'
        verbose_name_plural = 'Programas de Onboarding'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.department.name}"


class OnboardingTask(models.Model):
    """Tarefas do programa de onboarding"""
    TASK_TYPE_CHOICES = [
        ('document', 'Documento'),
        ('meeting', 'Reunião'),
        ('training', 'Treinamento'),
        ('system_access', 'Acesso ao Sistema'),
        ('tour', 'Tour pelas Instalações'),
        ('other', 'Outro'),
    ]

    program = models.ForeignKey(
        OnboardingProgram,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Programa'
    )
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    task_type = models.CharField('Tipo', max_length=20, choices=TASK_TYPE_CHOICES)
    due_day = models.PositiveIntegerField('Prazo em Dias', help_text='Dias após o início do onboarding')
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_onboarding_tasks',
        verbose_name='Responsável'
    )
    is_mandatory = models.BooleanField('Obrigatória', default=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Tarefa de Onboarding'
        verbose_name_plural = 'Tarefas de Onboarding'
        ordering = ['order', 'due_day']

    def __str__(self):
        return f"{self.title} - {self.program.name}"


class OnboardingInstance(models.Model):
    """Instância de onboarding para um funcionário específico"""
    STATUS_CHOICES = [
        ('not_started', 'Não Iniciado'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='onboarding_instances',
        verbose_name='Funcionário'
    )
    program = models.ForeignKey(
        OnboardingProgram,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name='Programa'
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='not_started')
    start_date = models.DateField('Data de Início')
    expected_completion_date = models.DateField('Data Prevista de Conclusão')
    actual_completion_date = models.DateField('Data Real de Conclusão', null=True, blank=True)
    mentor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentored_onboardings',
        verbose_name='Mentor'
    )
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Instância de Onboarding'
        verbose_name_plural = 'Instâncias de Onboarding'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.program.name}"

    @property
    def progress_percentage(self):
        total_tasks = self.task_completions.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.task_completions.filter(completed=True).count()
        return int((completed_tasks / total_tasks) * 100)


class OnboardingTaskCompletion(models.Model):
    """Acompanhamento de conclusão de tarefas de onboarding"""
    instance = models.ForeignKey(
        OnboardingInstance,
        on_delete=models.CASCADE,
        related_name='task_completions',
        verbose_name='Instância'
    )
    task = models.ForeignKey(
        OnboardingTask,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Tarefa'
    )
    completed = models.BooleanField('Concluída', default=False)
    completion_date = models.DateTimeField('Data de Conclusão', null=True, blank=True)
    notes = models.TextField('Observações', blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_onboarding_tasks',
        verbose_name='Concluído por'
    )

    class Meta:
        verbose_name = 'Conclusão de Tarefa'
        verbose_name_plural = 'Conclusões de Tarefas'
        unique_together = ['instance', 'task']

    def __str__(self):
        return f"{self.task.title} - {self.instance.employee.full_name}"


class Goal(models.Model):
    """Metas e objetivos dos funcionários"""
    GOAL_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('team', 'Equipe'),
        ('department', 'Departamento'),
        ('company', 'Empresa'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('active', 'Ativo'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
        ('overdue', 'Atrasado'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    goal_type = models.CharField('Tipo', max_length=20, choices=GOAL_TYPE_CHOICES)
    priority = models.CharField('Prioridade', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Responsáveis
    owner = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='owned_goals',
        verbose_name='Responsável'
    )
    collaborators = models.ManyToManyField(
        Employee,
        related_name='collaborative_goals',
        verbose_name='Colaboradores',
        blank=True
    )
    
    # Datas
    start_date = models.DateField('Data de Início')
    target_date = models.DateField('Data Alvo')
    completion_date = models.DateField('Data de Conclusão', null=True, blank=True)
    
    # Métricas
    target_value = models.DecimalField('Valor Alvo', max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField('Valor Atual', max_digits=10, decimal_places=2, null=True, blank=True)
    unit_measure = models.CharField('Unidade de Medida', max_length=50, blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_goals',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.owner.full_name}"

    @property
    def progress_percentage(self):
        if self.target_value and self.current_value:
            return min(int((self.current_value / self.target_value) * 100), 100)
        return 0

    @property
    def is_overdue(self):
        return self.target_date < timezone.now().date() and self.status not in ['completed', 'cancelled']


class Feedback(models.Model):
    """Sistema de feedback entre funcionários"""
    FEEDBACK_TYPE_CHOICES = [
        ('positive', 'Positivo'),
        ('constructive', 'Construtivo'),
        ('recognition', 'Reconhecimento'),
        ('suggestion', 'Sugestão'),
    ]

    VISIBILITY_CHOICES = [
        ('private', 'Privado'),
        ('manager', 'Gerência'),
        ('team', 'Equipe'),
        ('public', 'Público'),
    ]

    from_user = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='given_feedback',
        verbose_name='De'
    )
    to_user = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='received_feedback',
        verbose_name='Para'
    )
    feedback_type = models.CharField('Tipo', max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    subject = models.CharField('Assunto', max_length=200)
    content = models.TextField('Conteúdo')
    visibility = models.CharField('Visibilidade', max_length=20, choices=VISIBILITY_CHOICES, default='private')
    is_anonymous = models.BooleanField('Anônimo', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    read_at = models.DateTimeField('Lido em', null=True, blank=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        from_name = "Anônimo" if self.is_anonymous else self.from_user.full_name
        return f"{from_name} → {self.to_user.full_name}: {self.subject}"


class AdvancedTraining(models.Model):
    """Treinamentos avançados e desenvolvimento profissional"""
    TRAINING_TYPE_CHOICES = [
        ('online', 'Online'),
        ('presential', 'Presencial'),
        ('hybrid', 'Híbrido'),
        ('external', 'Externo'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planejado'),
        ('open', 'Aberto para Inscrições'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    training_type = models.CharField('Tipo', max_length=20, choices=TRAINING_TYPE_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Organização
    instructor = models.CharField('Instrutor', max_length=200)
    provider = models.CharField('Fornecedor/Instituição', max_length=200, blank=True)
    location = models.CharField('Local', max_length=200, blank=True)
    online_link = models.URLField('Link Online', blank=True)
    
    # Datas e horários
    start_date = models.DateTimeField('Data de Início')
    end_date = models.DateTimeField('Data de Fim')
    registration_deadline = models.DateField('Prazo de Inscrição', null=True, blank=True)
    
    # Capacidade e custos
    max_participants = models.PositiveIntegerField('Máximo de Participantes', default=20)
    cost_per_participant = models.DecimalField('Custo por Participante', max_digits=10, decimal_places=2, default=0)
    
    # Requisitos
    prerequisites = models.TextField('Pré-requisitos', blank=True)
    target_audience = models.CharField('Público Alvo', max_length=200, blank=True)
    
    # Certificação
    provides_certificate = models.BooleanField('Fornece Certificado', default=False)
    certificate_hours = models.PositiveIntegerField('Horas Certificadas', default=0)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_trainings',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Treinamento Avançado'
        verbose_name_plural = 'Treinamentos Avançados'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%d/%m/%Y')}"

    @property
    def available_spots(self):
        registered = self.registrations.filter(status='registered').count()
        return self.max_participants - registered

    @property
    def is_full(self):
        return self.available_spots <= 0


class TrainingRegistration(models.Model):
    """Inscrições em treinamentos"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('registered', 'Inscrito'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
        ('no_show', 'Não Compareceu'),
    ]

    training = models.ForeignKey(
        AdvancedTraining,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='Treinamento'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='training_registrations',
        verbose_name='Funcionário'
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_date = models.DateTimeField('Data de Inscrição', auto_now_add=True)
    completion_date = models.DateTimeField('Data de Conclusão', null=True, blank=True)
    grade = models.DecimalField('Nota', max_digits=4, decimal_places=2, null=True, blank=True)
    feedback = models.TextField('Feedback', blank=True)
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_registrations',
        verbose_name='Aprovado por'
    )

    class Meta:
        verbose_name = 'Inscrição em Treinamento'
        verbose_name_plural = 'Inscrições em Treinamentos'
        unique_together = ['training', 'employee']
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.training.title}"


class HRAnalytics(models.Model):
    """Métricas e analytics de RH"""
    METRIC_TYPE_CHOICES = [
        ('turnover', 'Turnover'),
        ('absenteeism', 'Absenteísmo'),
        ('satisfaction', 'Satisfação'),
        ('performance', 'Performance'),
        ('training_hours', 'Horas de Treinamento'),
        ('goal_completion', 'Conclusão de Metas'),
    ]

    metric_type = models.CharField('Tipo de Métrica', max_length=20, choices=METRIC_TYPE_CHOICES)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='Departamento',
        null=True,
        blank=True
    )
    period_start = models.DateField('Início do Período')
    period_end = models.DateField('Fim do Período')
    value = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    target_value = models.DecimalField('Valor Alvo', max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField('Unidade', max_length=20, blank=True)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_analytics',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Métrica de RH'
        verbose_name_plural = 'Métricas de RH'
        ordering = ['-period_end']

    def __str__(self):
        dept_name = self.department.name if self.department else 'Geral'
        return f"{self.get_metric_type_display()} - {dept_name} ({self.period_start} - {self.period_end})"

    @property
    def target_achievement_percentage(self):
        if self.target_value and self.target_value > 0:
            return min(int((self.value / self.target_value) * 100), 100)
        return 0
