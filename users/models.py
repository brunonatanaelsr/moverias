from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    """Modelo de usuário personalizado"""
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('tecnica', 'Técnica'),
        ('facilitador', 'Facilitador'),
        ('coordenador', 'Coordenador'),
        ('voluntario', 'Voluntário'),
    ]
    
    email = models.EmailField('E-mail', unique=True)
    full_name = models.CharField('Nome Completo', max_length=150)
    role = models.CharField('Função', max_length=20, choices=ROLE_CHOICES, default='voluntario')
    phone = models.CharField('Telefone', max_length=15, blank=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Formato: '+999999999'")
    ])
    department = models.CharField('Departamento', max_length=100, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    last_login_ip = models.GenericIPAddressField('Último IP de Login', null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split(' ')[0] if self.full_name else self.username

    @property
    def role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, 'Não definido')


class UserProfile(models.Model):
    """Perfil adicional do usuário"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField('Biografia', blank=True, max_length=500)
    birth_date = models.DateField('Data de Nascimento', null=True, blank=True)
    address = models.TextField('Endereço', blank=True)
    emergency_contact = models.CharField('Contato de Emergência', max_length=100, blank=True)
    emergency_phone = models.CharField('Telefone de Emergência', max_length=15, blank=True)
    skills = models.TextField('Habilidades', blank=True, help_text="Separadas por vírgula")
    availability = models.TextField('Disponibilidade', blank=True)
    notes = models.TextField('Observações', blank=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"Perfil de {self.user.full_name}"


class UserActivity(models.Model):
    """Log de atividades do usuário"""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Criação'),
        ('update', 'Atualização'),
        ('delete', 'Exclusão'),
        ('view', 'Visualização'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField('Ação', max_length=20, choices=ACTION_CHOICES)
    description = models.TextField('Descrição')
    ip_address = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Atividade de Usuário'
        verbose_name_plural = 'Atividades de Usuários'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_action_display()} - {self.timestamp}"


class SystemRole(models.Model):
    """Funções personalizadas do sistema"""
    name = models.CharField('Nome', max_length=50, unique=True)
    description = models.TextField('Descrição')
    permissions = models.ManyToManyField(Permission, verbose_name='Permissões', blank=True)
    is_active = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField('Criada em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Função do Sistema'
        verbose_name_plural = 'Funções do Sistema'
        ordering = ['name']

    def __str__(self):
        return self.name
