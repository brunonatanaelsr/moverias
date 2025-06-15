from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date


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
