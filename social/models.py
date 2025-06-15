# Copilot: modelo SocialAnamnesis.
# FK beneficiary; date auto_now_add; family_composition JSONField;
# income DecimalField(10,2); vulnerabilities Text; substance_use Text;
# observations Text; signed_by_technician FK(User);
# signed_by_beneficiary Boolean; locked Boolean (default False).
# save(): se locked=True e usuário não superuser, levantar ValidationError.

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from members.models import Beneficiary


class SocialAnamnesis(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='social_anamnesis')
    date = models.DateTimeField('Data da Anamnese', auto_now_add=True)
    family_composition = models.TextField('Composição Familiar', help_text="Descrição da composição familiar")
    income = models.DecimalField('Renda Familiar', max_digits=10, decimal_places=2)
    vulnerabilities = models.TextField('Vulnerabilidades Identificadas')
    substance_use = models.TextField('Uso de Substâncias', blank=True)
    observations = models.TextField('Observações Gerais', blank=True)
    signed_by_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='social_anamnesis_signed')
    # responsible_employee = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, 
    #                                        related_name='social_anamnesis_responsible', 
    #                                        verbose_name='Funcionário Responsável',
    #                                        help_text='Funcionário do RH responsável pelo atendimento')  # HR DESABILITADO
    signed_by_beneficiary = models.BooleanField('Assinado pela Beneficiária', default=False)
    locked = models.BooleanField('Bloqueado para Edição', default=False)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Anamnese Social'
        verbose_name_plural = 'Anamneses Sociais'

    def __str__(self):
        return f"Anamnese de {self.beneficiary.full_name} - {self.date.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        # Verificar se está tentando editar um registro bloqueado
        if self.pk and self.locked:
            # Buscar o estado anterior do objeto
            old_instance = SocialAnamnesis.objects.get(pk=self.pk)
            # Se já estava bloqueado e o usuário não é superuser, impedir edição
            if old_instance.locked and not getattr(self, '_current_user', None) or not self._current_user.is_superuser:
                raise ValidationError("Este registro está bloqueado e não pode ser editado.")
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.income is not None and self.income < 0:
            raise ValidationError({'income': 'A renda não pode ser negativa.'})
        super().clean()
