# Plano de Implementação - Módulo SOCIAL
## Sistema Move Marias - Anamneses Sociais

### 📋 **OVERVIEW**
O módulo SOCIAL possui um **sistema wizard complexo** para anamneses sociais com apenas **interface básica** implementada. Backend robusto com formulários multi-etapas e sistema de assinatura digital.

---

## 🏗️ **ARQUITETURA DE MODELOS (Disponível)**

### ✅ Modelos Principais Implementados:
```python
# Sistema completo de anamnese social:
- SocialAnamnesis (Anamnese principal)
  * Vínculo com beneficiária
  * Informações familiares e socioeconômicas
  * Rede de apoio social
  * Status (draft, completed, requires_update)
  * Sistema de assinatura (técnica + beneficiária)
  * Controle de bloqueio para edição
  * Auditoria completa

- FamilyMember (Membros da família)
  * Composição familiar detalhada
  * Relacionamentos e dependentes
  * Situação profissional de cada membro

- IdentifiedVulnerability (Vulnerabilidades)
  * Vulnerabilidades sociais identificadas
  * Categorização por tipo
  * Grau de risco/prioridade

- VulnerabilityCategory (Categorias)
  * Categorização padronizada
  * Sistema de classificação

- SocialAnamnesisEvolution (Evolução)
  * Acompanhamento temporal
  * Mudanças na situação social
  * Intervenções realizadas
```

### 🔧 Funcionalidades Backend Completas:
```python
# Sistema wizard avançado:
- SocialAnamnesisWizard (3 etapas) ✅
  * Step 1: Dados básicos e família
  * Step 2: Situação socioeconômica
  * Step 3: Vulnerabilidades e rede de apoio

# Views implementadas:
- SocialAnamnesisListView ✅
- SocialAnamnesisDetailView ✅
- SocialAnamnesisUpdateView ✅
- SocialAnamnesisDeleteView ✅
- lock_anamnesis() ✅
- add_evolution() ✅
- vulnerability_categories_api() ✅
```

---

## 🎯 **STATUS ATUAL vs NECESSÁRIO**

### ✅ **Templates Existentes (1/12):**
```
templates/social/
└── anamnesis_list.html ✅ (Muito básico)
```

### ❌ **Templates CRÍTICOS Faltando (11):**

#### **WIZARD SYSTEM (Prioridade MÁXIMA)**
```
1. anamnesis_wizard.html ⭐⭐⭐ - Wizard multi-etapas principal
2. wizard_step1.html ⭐⭐⭐ - Etapa 1: Dados pessoais/família
3. wizard_step2.html ⭐⭐⭐ - Etapa 2: Situação socioeconômica
4. wizard_step3.html ⭐⭐⭐ - Etapa 3: Vulnerabilidades e apoio
5. wizard_review.html ⭐⭐⭐ - Revisão antes de finalizar
6. wizard_signature.html ⭐⭐⭐ - Página de assinatura digital
```

#### **GESTÃO & VISUALIZAÇÃO (Prioridade ALTA)**
```
7. anamnesis_detail.html ⭐⭐⭐ - Visualização completa
8. anamnesis_dashboard.html ⭐⭐ - Dashboard de anamneses
9. anamnesis_edit.html ⭐⭐ - Edição simplificada
10. anamnesis_evolution.html ⭐⭐ - Acompanhamento evolução
```

#### **RELATÓRIOS & ANALYTICS (Prioridade MÉDIA)**
```
11. social_reports.html ⭐ - Relatórios sociais
12. vulnerability_analytics.html ⭐ - Analytics de vulnerabilidades
```

---

## 🔧 **FUNCIONALIDADES ESPECIAIS NECESSÁRIAS**

### **1. Sistema Wizard Multi-Etapas:**
```html
<!-- anamnesis_wizard.html -->
- Progress bar visual das etapas
- Navegação entre etapas
- Salvamento automático (draft)
- Validação por etapa
- Preview final antes de submeter
- Botões Anterior/Próximo/Salvar
```

### **2. Sistema de Assinatura Digital:**
```html
<!-- wizard_signature.html -->
- Canvas de assinatura para beneficiária
- Campos de confirmação
- Assinatura eletrônica da técnica
- Timestamp e certificação
- Download do documento assinado
```

### **3. Visualização Rica de Dados:**
```html
<!-- anamnesis_detail.html -->
- Timeline de informações coletadas
- Gráficos de composição familiar
- Mapa de vulnerabilidades
- Rede de apoio visual
- Histórico de evolução
- Documentos anexados
```

### **4. Dashboard Analítico:**
```html
<!-- anamnesis_dashboard.html -->
- Anamneses por status
- Vulnerabilidades mais frequentes
- Distribuição socioeconômica
- Técnicas mais produtivas
- Tempo médio de conclusão
```

---

## 🎨 **ESPECIFICAÇÕES DE DESIGN**

### **Layout Base:**
```html
<!-- Wizard Layout especializado -->
{% extends 'layouts/base.html' %}
{% load static %}

{% block title %}Anamnese Social - {{ title }}{% endblock %}

{% block extra_css %}
<link href="{% static 'css/social-wizard.css' %}" rel="stylesheet">
<link href="{% static 'css/signature-pad.css' %}" rel="stylesheet">
<link href="{% static 'css/form-steps.css' %}" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="wizard-container">
    <!-- Wizard específico content -->
</div>
{% endblock %}
```

### **Componentes Especiais Necessários:**
1. **Wizard Steps** - Indicador visual de progresso
2. **Family Tree** - Árvore genealógica interativa
3. **Vulnerability Map** - Mapa visual de vulnerabilidades
4. **Signature Pad** - Canvas de assinatura
5. **Auto-save** - Salvamento automático
6. **Form Validation** - Validação avançada por etapa
7. **Document Viewer** - Visualizador de documentos
8. **Timeline Component** - Timeline de evolução

---

## 📊 **TEMPLATES DETALHADOS**

### **1. anamnesis_wizard.html (CRÍTICO)**
```html
<!-- Wizard principal com navegação: -->
- Header com logo e título
- Progress bar das 3 etapas
- Container do formulário atual
- Botões de navegação contextuais
- Indicadores de validação
- Auto-save feedback
- Sidebar com resumo (opcional)
- Footer com informações legais
```

### **2. wizard_step1.html (CRÍTICO)**
```html
<!-- Etapa 1 - Dados pessoais e família: -->
- Confirmação dos dados da beneficiária
- Formulário de composição familiar
- Adicionar/remover membros da família
- Relacionamento e idades
- Situação profissional de cada membro
- Validação de campos obrigatórios
- Botão "Próximo" habilitado condicionalmente
```

### **3. wizard_step2.html (CRÍTICO)**
```html
<!-- Etapa 2 - Situação socioeconômica: -->
- Renda familiar detalhada
- Situação habitacional
- Benefícios sociais recebidos
- Despesas principais
- Situação de emprego
- Escolaridade dos membros
- Acesso a serviços básicos
```

### **4. wizard_step3.html (CRÍTICO)**
```html
<!-- Etapa 3 - Vulnerabilidades e apoio: -->
- Checklist de vulnerabilidades
- Grau de risco para cada item
- Rede de apoio familiar
- Rede de apoio social/comunitária
- Acesso a serviços públicos
- Necessidades prioritárias identificadas
- Observações adicionais
```

### **5. wizard_signature.html (CRÍTICO)**
```html
<!-- Página de assinatura: -->
- Resumo completo da anamnese
- Canvas de assinatura da beneficiária
- Campos de confirmação
- Assinatura eletrônica da técnica
- Termos de consentimento
- Botão finalizar (irreversível)
- Download do documento
```

### **6. anamnesis_detail.html (CRÍTICO)**
```html
<!-- Visualização completa: -->
- Header com dados da beneficiária
- Seções colapsáveis por categoria
- Timeline de preenchimento
- Status de assinatura visual
- Botões de ação (editar, evoluir, reimprimir)
- Anexos e documentos relacionados
- Histórico de alterações
```

---

## 🛠️ **RECURSOS TÉCNICOS NECESSÁRIOS**

### **JavaScript/Bibliotecas:**
```javascript
// Funcionalidades críticas:
- Form wizard navigation
- Auto-save functionality
- Signature pad (signature_pad.js)
- Form validation (real-time)
- LocalStorage para drafts
- AJAX form submission
- Dynamic form fields (família)
- Progress calculation
- Canvas manipulation
- PDF generation (client-side preview)
```

### **CSS/Tailwind Específicos:**
```css
/* Componentes especiais: */
.wizard-container { }
.wizard-steps { }
.wizard-progress { }
.form-section { }
.signature-pad { }
.family-member-card { }
.vulnerability-grid { }
.anamnesis-timeline { }
```

### **Django Específico:**
```python
# Features necessárias:
- SessionWizardView customizado
- Form validation por etapa
- File upload handling
- Digital signature processing
- PDF generation
- Draft auto-save
- Version control
```

---

## 📈 **MÉTRICAS E KPIs**

### **Dashboard deve mostrar:**
- Total de anamneses por status
- Tempo médio de preenchimento
- Taxa de conclusão por técnica
- Vulnerabilidades mais identificadas
- Distribuição de renda familiar
- Anamneses pendentes de assinatura
- Evolução temporal dos casos
- Beneficiárias sem anamnese
- Anamneses que precisam atualização

---

## 🔐 **PERMISSÕES E SEGURANÇA**

### **Níveis de Acesso:**
```python
# Permissões específicas:

TECHNICIAN: # Técnica Social
- Criar nova anamnese
- Preencher wizard completo
- Assinar eletronicamente
- Ver anamneses próprias
- Editar antes da assinatura
- Adicionar evoluções

COORDINATOR: # Coordenadora
- Todas as funções de técnica
- Ver todas as anamneses
- Desbloquear para edição (casos especiais)
- Relatórios analíticos
- Supervisionar assinaturas

ADMIN: # Administrador
- Acesso completo
- Editar anamneses bloqueadas
- Configurar vulnerabilidades
- Auditoria completa
- Backup e restauração

BENEFICIARY: # Beneficiária (limitado)
- Ver própria anamnese (resumo)
- Confirmar dados pessoais
- Assinar digitalmente
```

---

## ⚡ **CRONOGRAMA DE IMPLEMENTAÇÃO**

### **Semana 1 (5 dias):**
**Dia 1:** Wizard principal e navegação (anamnesis_wizard, navigation)
**Dia 2:** Etapas do formulário (step1, step2, step3)
**Dia 3:** Sistema de assinatura (signature pad, validation)
**Dia 4:** Visualização detalhada (anamnesis_detail, timeline)
**Dia 5:** Dashboard e relatórios (dashboard, analytics)

### **Semana 2 (3 dias):**
**Dia 1:** Auto-save e validação avançada
**Dia 2:** Funcionalidades mobile e responsividade
**Dia 3:** Testes, refinamentos e integrações

---

## 🔧 **INTEGRAÇÕES NECESSÁRIAS**

### **Com Outros Módulos:**
```python
# Integrações críticas:
- MEMBERS: Dados da beneficiária
- EVOLUTION: Evolução social
- NOTIFICATIONS: Alertas para técnicas
- COACHING: Planos de ação baseados na anamnese
- ACTIVITIES: Atividades recomendadas
- CERTIFICATES: Certificados de acompanhamento
- REPORTS: Relatórios sociais integrados
```

### **Funcionalidades Especiais:**
```python
# Features avançadas:
- Auto-complete de endereços (ViaCEP API)
- Integração com CadÚnico (futuro)
- Backup automático de assinaturas
- Notificações de prazo de atualização
- Import/export de dados
- Auditoria de alterações
```

---

## ✅ **CHECKLIST DE IMPLEMENTAÇÃO**

### **Funcionalidades Core:**
- [ ] Wizard de 3 etapas funcional
- [ ] Auto-save por etapa
- [ ] Validação completa
- [ ] Sistema de assinatura digital
- [ ] Visualização rica de dados
- [ ] Sistema de bloqueio
- [ ] Controle de versões
- [ ] Dashboard analítico

### **Funcionalidades Avançadas:**
- [ ] Mobile responsivo
- [ ] Assinatura por tablet/mobile
- [ ] Geração de PDF completo
- [ ] Sistema de templates
- [ ] Bulk operations
- [ ] Advanced analytics
- [ ] Integration APIs
- [ ] Audit trail completo

### **UX/UI:**
- [ ] Interface intuitiva
- [ ] Progress indicators
- [ ] Error handling elegante
- [ ] Loading states
- [ ] Confirmation dialogs
- [ ] Keyboard navigation
- [ ] Accessibility compliant
- [ ] Print-friendly views

---

## 🚀 **RECURSOS ESPECIAIS**

### **Wizard Avançado:**
```javascript
// Features diferenciadas:
- Smart field dependencies
- Conditional form sections
- Auto-complete suggestions
- Real-time validation
- Progress calculation
- Step-by-step guidance
- Recovery from interruptions
```

### **Assinatura Digital:**
```javascript
// Recursos de segurança:
- Biometric validation (futuro)
- Timestamp certificado
- Hash verification
- Audit trail completo
- Legal compliance
- Multi-device support
```

### **Analytics Sociais:**
```html
<!-- Insights únicos: -->
- Social vulnerability mapping
- Family composition analysis
- Economic indicators tracking
- Support network visualization
- Risk assessment scoring
- Intervention effectiveness
```

---

## 📋 **DEPENDÊNCIAS TÉCNICAS**

```bash
# Python packages necessários:
pip install django-formtools     # Wizard forms
pip install signature-pad       # Digital signature
pip install reportlab          # PDF generation
pip install pillow            # Image processing
pip install django-crispy-forms # Form styling

# JavaScript libraries:
npm install signature_pad      # Signature functionality
npm install chart.js          # Analytics charts
npm install moment.js         # Date handling
npm install lodash           # Utility functions
```

---

## 🎯 **PRÓXIMOS PASSOS**

### **Fase 1 - Wizard Core:**
1. anamnesis_wizard.html
2. wizard_step1.html
3. wizard_step2.html
4. wizard_step3.html

### **Fase 2 - Assinatura:**
1. wizard_signature.html
2. Digital signature integration
3. PDF generation

### **Fase 3 - Visualização:**
1. anamnesis_detail.html
2. anamnesis_dashboard.html
3. Analytics integration

---

**⏰ Estimativa Total: 8-10 dias de desenvolvimento**
**🎯 Prioridade: CRÍTICA - Terceira prioridade**
**💼 Impacto: ALTO - Sistema fundamental para trabalho social**
**🔐 Complexidade: ALTA - Sistema wizard com assinatura digital**
