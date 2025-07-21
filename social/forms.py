from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column
from .models import (
    SocialAnamnesis, 
    FamilyMember, 
    VulnerabilityCategory, 
    IdentifiedVulnerability,
    SocialAnamnesisEvolution
)


class SocialAnamnesisStep1Form(forms.ModelForm):
    """Primeiro passo: Dados básicos"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['beneficiary', 'family_income', 'housing_situation']
        widgets = {
            'housing_situation': forms.Textarea(attrs={'rows': 4}),
            'family_income': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Familiares',
                Column('beneficiary'),
                Column('family_income'),
                Row(
                    Column(
                        'family_income',
                        css_class='relative',
                        css_id='family_income_tooltip',
                    ),
                ),
                Column(
                    'housing_situation',
                    css_class='relative',
                    css_id='housing_situation_tooltip',
                ),
                # Tooltips explicativos
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_family_income',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Informe a renda total da família (soma de todos os rendimentos mensais).</span>'
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_housing_situation',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva a situação de moradia (ex: própria, aluguel, cedida).</span>'
                ),
            ),
            Submit('submit', 'Próximo', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )

    def clean_family_income(self):
        income = self.cleaned_data.get('family_income')
        if income is not None and income < 0:
            raise ValidationError('A renda não pode ser negativa.')
        return income


class SocialAnamnesisStep2Form(forms.ModelForm):
    """Segundo passo: Rede de apoio"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['support_network']
        widgets = {
            'support_network': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Rede de Apoio Social',
                Column('support_network'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_support_network',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva pessoas, grupos ou instituições que apoiam a beneficiária (ex: família, amigos, igreja, serviços públicos).</span>'
                ),
            ),
            Row(
                Column(Submit('prev_step', 'Anterior', css_class='bg-gray-500 text-white px-4 py-2 rounded'), css_class='w-1/2 px-2'),
                Column(Submit('submit', 'Próximo', css_class='bg-move-purple-600 text-white px-4 py-2 rounded'), css_class='w-1/2 px-2')
            )
        )


class SocialAnamnesisStep3Form(forms.ModelForm):
    """Terceiro passo: Finalização"""
    
    class Meta:
        model = SocialAnamnesis
        fields = ['observations', 'signed_by_beneficiary']
        widgets = {
            'observations': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Observações e Assinatura',
                Column('observations'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_observations',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Inclua informações relevantes sobre a situação da beneficiária que não foram contempladas nos campos anteriores.</span>'
                ),
                Column('signed_by_beneficiary'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_signed_by_beneficiary',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Confirmação de que a beneficiária está ciente e concorda com as informações registradas.</span>'
                ),
            ),
            Row(
                Column(Submit('prev_step', 'Anterior', css_class='bg-gray-500 text-white px-4 py-2 rounded'), css_class='w-1/2 px-2'),
                Column(Submit('submit', 'Finalizar', css_class='bg-green-600 text-white px-4 py-2 rounded'), css_class='w-1/2 px-2')
            )
        )


class SocialAnamnesisUpdateForm(forms.ModelForm):
    """Formulário completo para edição"""
    
    class Meta:
        model = SocialAnamnesis
        fields = [
            'family_income', 'housing_situation', 'support_network', 
            'observations', 'signed_by_beneficiary'
        ]
        widgets = {
            'housing_situation': forms.Textarea(attrs={'rows': 4}),
            'support_network': forms.Textarea(attrs={'rows': 6}),
            'observations': forms.Textarea(attrs={'rows': 4}),
            'family_income': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Familiares',
                Row(
                    Column('family_income', css_class='w-1/2 px-2'),
                    Column('housing_situation', css_class='w-1/2 px-2')
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_family_income_update',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Informe a renda total da família (soma de todos os rendimentos mensais).</span>'
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_housing_situation_update',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva a situação de moradia (ex: própria, aluguel, cedida).</span>'
                ),
            ),
            Fieldset(
                'Rede de Apoio',
                Column('support_network'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_support_network_update',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva pessoas, grupos ou instituições que apoiam a beneficiária (ex: família, amigos, igreja, serviços públicos).</span>'
                ),
            ),
            Fieldset(
                'Finalização',
                Column('observations'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_observations_update',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Inclua informações relevantes sobre a situação da beneficiária que não foram contempladas nos campos anteriores.</span>'
                ),
                Column('signed_by_beneficiary'),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_signed_by_beneficiary_update',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Confirmação de que a beneficiária está ciente e concorda com as informações registradas.</span>'
                ),
            ),
            Submit('submit', 'Salvar Alterações', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )

    def clean_family_income(self):
        income = self.cleaned_data.get('family_income')
        if income is not None and income < 0:
            raise ValidationError('A renda não pode ser negativa.')
        return income


class FamilyMemberForm(forms.ModelForm):
    """Formulário para membros da família"""
    
    class Meta:
        model = FamilyMember
        fields = [
            'name', 'relationship', 'age', 'gender', 'education_level',
            'occupation', 'income', 'health_conditions'
        ]
        widgets = {
            'health_conditions': forms.Textarea(attrs={'rows': 3}),
            'income': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Pessoais',
                Row(
                    Column('name', css_class='w-1/2 px-2'),
                    Column('relationship', css_class='w-1/2 px-2')
                ),
                Row(
                    Column('age', css_class='w-1/3 px-2'),
                    Column('gender', css_class='w-1/3 px-2'),
                    Column('education_level', css_class='w-1/3 px-2')
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_family_member_name',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Nome completo do membro da família.</span>'
                ),
            ),
            Fieldset(
                'Trabalho e Renda',
                Row(
                    Column('occupation', css_class='w-1/2 px-2'),
                    Column('income', css_class='w-1/2 px-2')
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_family_member_income',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Informe a renda individual mensal deste membro.</span>'
                ),
            ),
            Fieldset(
                'Saúde',
                'health_conditions',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_family_member_health',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva condições de saúde relevantes (ex: doenças crônicas, deficiências).</span>'
                ),
            ),
            Submit('submit', 'Salvar', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )

    def clean_income(self):
        income = self.cleaned_data.get('income')
        if income is not None and income < 0:
            raise ValidationError('A renda não pode ser negativa.')
        return income


class VulnerabilityCategoryForm(forms.ModelForm):
    """Formulário para categorias de vulnerabilidade"""
    
    class Meta:
        model = VulnerabilityCategory
        fields = ['name', 'description', 'color', 'priority_level']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'description': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Informações da Categoria',
                'name',
                'description',
                Row(
                    Column('color', css_class='w-1/2 px-2'),
                    Column('priority_level', css_class='w-1/2 px-2')
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_category_color',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Escolha uma cor para identificar visualmente a categoria.</span>'
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_category_priority',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Defina o nível de prioridade para esta categoria (quanto maior, mais urgente).</span>'
                ),
            ),
            Submit('submit', 'Salvar', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )


class IdentifiedVulnerabilityForm(forms.ModelForm):
    """Formulário para vulnerabilidades identificadas"""
    
    class Meta:
        model = IdentifiedVulnerability
        fields = [
            'category', 'description', 'severity', 'status', 
            'intervention_needed', 'priority_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'intervention_needed': forms.Textarea(attrs={'rows': 3}),
            'priority_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Identificação da Vulnerabilidade',
                'category',
                'description',
                Row(
                    Column('severity', css_class='w-1/2 px-2'),
                    Column('status', css_class='w-1/2 px-2')
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_vuln_severity',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Gravidade: quanto maior, mais impacto na vida da beneficiária.</span>'
                ),
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_vuln_status',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Status: informe se a vulnerabilidade está ativa, resolvida ou em acompanhamento.</span>'
                ),
            ),
            Fieldset(
                'Intervenção',
                'intervention_needed',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_vuln_intervention',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva a intervenção necessária para resolver ou mitigar a vulnerabilidade.</span>'
                ),
                'priority_date',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_vuln_priority_date',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Data limite para realizar a intervenção.</span>'
                ),
            ),
            Submit('submit', 'Salvar', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )


class SocialAnamnesisEvolutionForm(forms.ModelForm):
    """Formulário para evolução da anamnese"""
    
    class Meta:
        model = SocialAnamnesisEvolution
        fields = [
            'evolution_date', 'description', 'changes_in_family',
            'changes_in_vulnerabilities', 'changes_in_support_network',
            'attachments'
        ]
        widgets = {
            'evolution_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'changes_in_family': forms.Textarea(attrs={'rows': 3}),
            'changes_in_vulnerabilities': forms.Textarea(attrs={'rows': 3}),
            'changes_in_support_network': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Informações da Evolução',
                'evolution_date',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_date',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Data e hora da evolução registrada.</span>'
                ),
                'description',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_description',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva as principais mudanças ou eventos desde a última evolução.</span>'
                ),
            ),
            Fieldset(
                'Mudanças Específicas',
                'changes_in_family',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_family',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva mudanças na família (ex: novos membros, separações, falecimentos).</span>'
                ),
                'changes_in_vulnerabilities',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_vulnerabilities',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva mudanças nas vulnerabilidades identificadas.</span>'
                ),
                'changes_in_support_network',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_support_network',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Descreva mudanças na rede de apoio (ex: novos apoios, perdas).</span>'
                ),
            ),
            Fieldset(
                'Anexos',
                'attachments',
                Column(
                    None,
                    css_class='text-gray-500 italic text-xs mt-1',
                    css_id='tooltip_evolution_attachments',
                    html='<span class="inline-flex items-center"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20h.01" /></svg>Adicione documentos, fotos ou outros arquivos relevantes à evolução.</span>'
                ),
            ),
            Submit('submit', 'Salvar Evolução', css_class='bg-move-purple-600 text-white px-4 py-2 rounded')
        )
