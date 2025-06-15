# Copilot: modelo ActionPlan.
# FK beneficiary; main_goal Text; priority_areas ArrayField(Char(30)) ou JSONField;
# actions JSONField; institute_support Text; semester_review Text blank.

from django.db import models
from members.models import Beneficiary


class ActionPlan(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='action_plans')
    main_goal = models.TextField('Objetivo Principal')
    priority_areas = models.TextField('Áreas Prioritárias', help_text="Lista de áreas prioritárias (separadas por vírgula ou quebra de linha)")
    actions = models.TextField('Plano de Ações', help_text="Detalhamento das ações planejadas")
    institute_support = models.TextField('Apoio Institucional Necessário')
    semester_review = models.TextField('Revisão Semestral', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Plano de Ação'
        verbose_name_plural = 'Planos de Ação'

    def __str__(self):
        return f"Plano de Ação - {self.beneficiary.full_name} ({self.created_at.strftime('%m/%Y')})"


class WheelOfLife(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='wheel_of_life')
    date = models.DateField('Data da Avaliação')
    
    # 12 áreas da Roda da Vida (0-10)
    family = models.FloatField('Família', help_text="Avaliação de 0 a 10")
    finance = models.FloatField('Finanças', help_text="Avaliação de 0 a 10")
    health = models.FloatField('Saúde', help_text="Avaliação de 0 a 10")
    career = models.FloatField('Carreira', help_text="Avaliação de 0 a 10")
    relationships = models.FloatField('Relacionamentos', help_text="Avaliação de 0 a 10")
    personal_growth = models.FloatField('Crescimento Pessoal', help_text="Avaliação de 0 a 10")
    leisure = models.FloatField('Lazer', help_text="Avaliação de 0 a 10")
    spirituality = models.FloatField('Espiritualidade', help_text="Avaliação de 0 a 10")
    education = models.FloatField('Educação', help_text="Avaliação de 0 a 10")
    environment = models.FloatField('Meio Ambiente', help_text="Avaliação de 0 a 10")
    contribution = models.FloatField('Contribuição Social', help_text="Avaliação de 0 a 10")
    emotions = models.FloatField('Equilíbrio Emocional', help_text="Avaliação de 0 a 10")

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Roda da Vida'
        verbose_name_plural = 'Rodas da Vida'

    def __str__(self):
        return f"Roda da Vida - {self.beneficiary.full_name} ({self.date.strftime('%d/%m/%Y')})"

    @property
    def average_score(self):
        """Retorna a média das áreas avaliadas"""
        scores = [
            self.family, self.finance, self.health, self.career,
            self.relationships, self.personal_growth, self.leisure,
            self.spirituality, self.education, self.environment,
            self.contribution, self.emotions
        ]
        return sum(scores) / len(scores)

    @property
    def areas_dict(self):
        """Retorna um dicionário com todas as áreas e suas pontuações"""
        return {
            'Família': self.family,
            'Finanças': self.finance,
            'Saúde': self.health,
            'Carreira': self.career,
            'Relacionamentos': self.relationships,
            'Crescimento Pessoal': self.personal_growth,
            'Lazer': self.leisure,
            'Espiritualidade': self.spirituality,
            'Educação': self.education,
            'Meio Ambiente': self.environment,
            'Contribuição Social': self.contribution,
            'Equilíbrio Emocional': self.emotions,
        }

    def clean(self):
        """Validação para garantir que todas as pontuações estão entre 0 e 10"""
        from django.core.exceptions import ValidationError
        
        areas = [
            ('family', self.family), ('finance', self.finance), ('health', self.health),
            ('career', self.career), ('relationships', self.relationships),
            ('personal_growth', self.personal_growth), ('leisure', self.leisure),
            ('spirituality', self.spirituality), ('education', self.education),
            ('environment', self.environment), ('contribution', self.contribution),
            ('emotions', self.emotions)
        ]
        
        errors = {}
        for field_name, value in areas:
            if value < 0 or value > 10:
                errors[field_name] = 'A pontuação deve estar entre 0 e 10.'
        
        if errors:
            raise ValidationError(errors)
