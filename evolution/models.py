# Copilot: modelo EvolutionRecord.
# FK beneficiary; date; description Text; author FK(User);
# signature_required Boolean; signed_by_beneficiary Boolean.
# __str__ -> f"{beneficiary} – {date:%d/%m/%Y}".

from django.db import models
from django.conf import settings
from members.models import Beneficiary


class EvolutionRecord(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='evolution_records')
    date = models.DateField('Data do Registro')
    description = models.TextField('Descrição da Evolução')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evolution_records_authored')
    # responsible_employee = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True,
    #                                        related_name='evolution_records_responsible', 
    #                                        verbose_name='Funcionário Responsável',
    #                                        help_text='Funcionário do RH responsável pelo acompanhamento')  # HR DESABILITADO
    signature_required = models.BooleanField('Requer Assinatura da Beneficiária', default=False)
    signed_by_beneficiary = models.BooleanField('Assinado pela Beneficiária', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Registro de Evolução'
        verbose_name_plural = 'Registros de Evolução'

    def __str__(self):
        return f"{self.beneficiary} – {self.date.strftime('%d/%m/%Y')}"

    @property
    def is_signed(self):
        """Verifica se o registro está assinado quando necessário"""
        if self.signature_required:
            return self.signed_by_beneficiary
        return True  # Se não requer assinatura, considera como "assinado"

    @property
    def pending_signature(self):
        """Verifica se há assinatura pendente"""
        return self.signature_required and not self.signed_by_beneficiary
