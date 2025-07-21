from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from members.models import Beneficiary


class SocialAnamnesis(models.Model):
    """Modelo para armazenar informações da anamnese social"""
    
    beneficiary = models.ForeignKey(
        Beneficiary, 
        on_delete=models.CASCADE, 
        related_name='social_anamneses'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_social_anamnesis'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Informações familiares (mudamos para campos mais específicos)
    family_income = models.DecimalField(
        'Renda familiar', 
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True
    )
    
    housing_situation = models.TextField(
        'Situação habitacional',
        help_text='Descreva a situação habitacional da beneficiária'
    )
    
    # Rede de apoio
    support_network = models.TextField(
        'Rede de apoio',
        help_text='Descreva a rede de apoio social da beneficiária'
    )
    
    # Observações gerais
    observations = models.TextField(
        'Observações',
        blank=True,
        help_text='Observações adicionais sobre a anamnese'
    )
    
    # Status da anamnese
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('completed', 'Concluída'),
        ('requires_update', 'Requer Atualização'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Controle de assinatura e bloqueio (mantendo compatibilidade)
    signed_by_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='social_anamneses_signed',
        null=True,
        blank=True
    )
    signed_by_beneficiary = models.BooleanField('Assinado pela Beneficiária', default=False)
    locked = models.BooleanField('Bloqueado para Edição', default=False)
    
    class Meta:
        verbose_name = 'Anamnese Social'
        verbose_name_plural = 'Anamneses Sociais'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Anamnese Social - {self.beneficiary.name} ({self.created_at.strftime('%d/%m/%Y')})"
    
    def save(self, *args, **kwargs):
        # Verificar se está tentando editar um registro bloqueado
        if self.pk and self.locked:
            # Buscar o estado anterior do objeto
            old_instance = SocialAnamnesis.objects.get(pk=self.pk)
            current_user = kwargs.pop('current_user', None)
            # Se já estava bloqueado e o usuário não é superuser, impedir edição
            if old_instance.locked and (not current_user or not current_user.is_superuser):
                raise ValidationError("Este registro está bloqueado e não pode ser editado.")
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.family_income is not None and self.family_income < 0:
            raise ValidationError({'family_income': 'A renda não pode ser negativa.'})
        super().clean()


class FamilyMember(models.Model):
    """Modelo para armazenar informações sobre membros da família"""
    
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Cônjuge/Companheiro(a)'),
        ('child', 'Filho(a)'),
        ('parent', 'Pai/Mãe'),
        ('sibling', 'Irmão/Irmã'),
        ('grandparent', 'Avô/Avó'),
        ('grandchild', 'Neto(a)'),
        ('other', 'Outro'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('none', 'Sem escolaridade'),
        ('elementary_incomplete', 'Ensino fundamental incompleto'),
        ('elementary_complete', 'Ensino fundamental completo'),
        ('high_school_incomplete', 'Ensino médio incompleto'),
        ('high_school_complete', 'Ensino médio completo'),
        ('higher_education_incomplete', 'Ensino superior incompleto'),
        ('higher_education_complete', 'Ensino superior completo'),
        ('postgraduate', 'Pós-graduação'),
    ]
    
    anamnesis = models.ForeignKey(
        SocialAnamnesis,
        on_delete=models.CASCADE,
        related_name='family_members'
    )
    
    name = models.CharField('Nome', max_length=100)
    relationship = models.CharField(
        'Parentesco',
        max_length=20,
        choices=RELATIONSHIP_CHOICES
    )
    age = models.PositiveIntegerField('Idade', null=True, blank=True)
    gender = models.CharField(
        'Gênero',
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )
    education_level = models.CharField(
        'Nível de escolaridade',
        max_length=30,
        choices=EDUCATION_LEVEL_CHOICES,
        null=True,
        blank=True
    )
    occupation = models.CharField(
        'Ocupação',
        max_length=100,
        null=True,
        blank=True
    )
    income = models.DecimalField(
        'Renda individual',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    health_conditions = models.TextField(
        'Condições de saúde',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Membro da Família'
        verbose_name_plural = 'Membros da Família'
        ordering = ['relationship', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_relationship_display()}"


class VulnerabilityCategory(models.Model):
    """Categorias de vulnerabilidades sociais"""
    
    name = models.CharField('Nome', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    color = models.CharField(
        'Cor identificadora',
        max_length=7,
        default='#6B7280',
        help_text='Cor em formato hexadecimal (#000000)'
    )
    priority_level = models.PositiveIntegerField(
        'Nível de prioridade',
        default=1,
        help_text='1 = Baixa, 2 = Média, 3 = Alta'
    )
    is_active = models.BooleanField('Ativo', default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria de Vulnerabilidade'
        verbose_name_plural = 'Categorias de Vulnerabilidades'
        ordering = ['-priority_level', 'name']
    
    def __str__(self):
        return self.name


class IdentifiedVulnerability(models.Model):
    """Vulnerabilidades identificadas na anamnese"""
    
    SEVERITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('identified', 'Identificada'),
        ('in_progress', 'Em Acompanhamento'),
        ('resolved', 'Resolvida'),
        ('requires_attention', 'Requer Atenção'),
    ]
    
    anamnesis = models.ForeignKey(
        SocialAnamnesis,
        on_delete=models.CASCADE,
        related_name='vulnerabilities'
    )
    
    category = models.ForeignKey(
        VulnerabilityCategory,
        on_delete=models.CASCADE,
        related_name='identified_vulnerabilities'
    )
    
    description = models.TextField('Descrição detalhada')
    severity = models.CharField(
        'Gravidade',
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='identified'
    )
    
    intervention_needed = models.TextField(
        'Intervenção necessária',
        blank=True,
        help_text='Descreva que tipo de intervenção é necessária'
    )
    
    priority_date = models.DateField(
        'Data de prioridade',
        null=True,
        blank=True,
        help_text='Data até quando esta vulnerabilidade deve ser abordada'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vulnerabilidade Identificada'
        verbose_name_plural = 'Vulnerabilidades Identificadas'
        ordering = ['-priority_date', '-created_at']
    
    def __str__(self):
        category_name = self.category.name if self.category else "Sem categoria"
        return f"{category_name} - {self.get_severity_display()}"


class SocialAnamnesisEvolution(models.Model):
    """Evolução da anamnese social ao longo do tempo"""
    
    anamnesis = models.ForeignKey(
        SocialAnamnesis,
        on_delete=models.CASCADE,
        related_name='evolutions'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_anamnesis_evolutions'
    )
    
    evolution_date = models.DateTimeField(default=timezone.now)
    description = models.TextField('Descrição da evolução')
    
    # Mudanças específicas
    changes_in_family = models.TextField(
        'Mudanças na família',
        blank=True,
        help_text='Descreva mudanças na composição familiar'
    )
    
    changes_in_vulnerabilities = models.TextField(
        'Mudanças nas vulnerabilidades',
        blank=True,
        help_text='Descreva mudanças nas vulnerabilidades'
    )
    
    changes_in_support_network = models.TextField(
        'Mudanças na rede de apoio',
        blank=True,
        help_text='Descreva mudanças na rede de apoio'
    )
    
    attachments = models.FileField(
        'Anexos',
        upload_to='social_anamnesis_evolutions/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Evolução da Anamnese'
        verbose_name_plural = 'Evoluções da Anamnese'
        ordering = ['-evolution_date']
    
    def __str__(self):
        return f"Evolução - {self.anamnesis.beneficiary.name} ({self.evolution_date.strftime('%d/%m/%Y')})"
