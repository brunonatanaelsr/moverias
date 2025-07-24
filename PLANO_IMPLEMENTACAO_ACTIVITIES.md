# Plano de Implementação - Módulo ACTIVITIES
## Sistema Move Marias - Sistema de Atividades Unificado

### 📋 **OVERVIEW**
O módulo ACTIVITIES é um **sistema completamente novo** que unifica e substitui funcionalidades de Projects e Tasks, centralizando nas beneficiárias. Possui apenas 1 template básico implementado.

---

## 🏗️ **ARQUITETURA DE MODELOS (Disponível)**

### ✅ Modelos Principais Implementados:
```python
# Sistema unificado e robusto:
- BeneficiaryActivity (Atividade principal)
  * 11 tipos: WORKSHOP, COURSE, THERAPY, COUNSELING, etc.
  * 5 status: PLANNED, ACTIVE, COMPLETED, CANCELLED, PAUSED
  * 4 prioridades: LOW, MEDIUM, HIGH, URGENT
  * 7 frequências: UNIQUE, DAILY, WEEKLY, etc.
  * Programação completa (datas, duração, frequência)
  * Responsáveis e facilitadores
  * Sistema de metas e objetivos
  * Recursos necessários
  * Local e modalidade

- ActivitySession (Sessões/Encontros)
  * Sessões individuais da atividade
  * Controle de presença
  * Notas e observações por sessão
  * Anexos e materiais

- ActivityAttendance (Controle de Presença)
  * Presença detalhada por sessão
  * Status: present, absent, late, justified
  * Justificativas de faltas
  * Tempo de permanência

- ActivityFeedback (Feedback e Avaliação)
  * Feedback de beneficiárias
  * Avaliação de facilitadores
  * Notas numéricas e comentários
  * Sistema de satisfação

- ActivityNote (Notas e Observações)
  * Anotações dos técnicos
  * Evolução da beneficiária
  * Incidentes e ocorrências
  * Acompanhamento contínuo
```

### 🔧 Funcionalidades Backend Completas:
```python
# Views robustas implementadas:
- activities_dashboard() ✅
- beneficiary_activities_dashboard() ✅
- activities_list() ✅
- BeneficiaryActivityCreateView ✅
- BeneficiaryActivityDetailView ✅
- BeneficiaryActivityUpdateView ✅
- activity_session_create() ✅
- attendance_record() ✅
- activity_feedback() ✅
- activity_notes() ✅
- activities_calendar() ✅
- activities_analytics() ✅
```

---

## 🎯 **STATUS ATUAL vs NECESSÁRIO**

### ✅ **Templates Existentes (1/15):**
```
activities/templates/activities/
└── dashboard.html ✅ (Muito básico)
```

### ❌ **Templates CRÍTICOS Faltando (14):**

#### **DASHBOARD & OVERVIEW (Prioridade MÁXIMA)**
```
1. activities_dashboard.html ⭐⭐⭐ - Dashboard principal do sistema
2. beneficiary_dashboard.html ⭐⭐⭐ - Dashboard por beneficiária
3. activities_calendar.html ⭐⭐⭐ - Calendário de atividades
4. activities_timeline.html ⭐⭐⭐ - Timeline temporal
```

#### **GESTÃO DE ATIVIDADES (Prioridade MÁXIMA)**
```
5. activity_list.html ⭐⭐⭐ - Lista de atividades
6. activity_form.html ⭐⭐⭐ - Criar/editar atividade
7. activity_detail.html ⭐⭐⭐ - Detalhes completos da atividade
8. activity_sessions.html ⭐⭐ - Gestão de sessões
```

#### **CONTROLE DE PRESENÇA (Prioridade ALTA)**
```
9. attendance_record.html ⭐⭐ - Registro de presença
10. attendance_report.html ⭐⭐ - Relatório de frequência
```

#### **FEEDBACK & AVALIAÇÃO (Prioridade ALTA)**
```
11. activity_feedback.html ⭐⭐ - Sistema de feedback
12. activity_evaluation.html ⭐⭐ - Avaliação da atividade
```

#### **RELATÓRIOS & ANALYTICS (Prioridade MÉDIA)**
```
13. activities_analytics.html ⭐ - Analytics de atividades
14. activities_reports.html ⭐ - Relatórios personalizados
15. beneficiary_progress.html ⭐ - Progresso da beneficiária
```

---

## 🔧 **FUNCIONALIDADES ESPECIAIS NECESSÁRIAS**

### **1. Dashboard Centralizado:**
```html
<!-- activities_dashboard.html -->
- Visão geral de todas as atividades
- Atividades por status (planejadas, ativas, concluídas)
- Beneficiárias mais ativas
- Próximas sessões agendadas
- Relatórios de frequência
- Alertas e notificações
- Acesso rápido às funcionalidades
```

### **2. Calendário Interativo:**
```html
<!-- activities_calendar.html -->
- Calendário mensal/semanal/diário
- Código de cores por tipo de atividade
- Drag-and-drop para reagendar
- Popup com detalhes rápidos
- Filtros por beneficiária/tipo/status
- Integração com Google Calendar
```

### **3. Timeline de Progresso:**
```html
<!-- activities_timeline.html -->
- Timeline cronológica por beneficiária
- Marcos importantes destacados
- Evolução visual do progresso
- Anotações e observações
- Anexos e documentos
- Compartilhamento com equipe
```

### **4. Sistema de Avaliação:**
```html
<!-- activity_evaluation.html -->
- Avaliação em tempo real
- Múltiplos critérios de avaliação
- Escala de satisfação
- Comentários estruturados
- Upload de evidências
- Comparação temporal
```

---

## 🎨 **ESPECIFICAÇÕES DE DESIGN**

### **Layout Base:**
```html
<!-- Layout focado em atividades -->
{% extends 'layouts/base.html' %}
{% load static %}

{% block title %}Atividades - {{ title }}{% endblock %}

{% block extra_css %}
<link href="{% static 'css/activities-module.css' %}" rel="stylesheet">
<link href="{% static 'css/calendar.css' %}" rel="stylesheet">
<link href="{% static 'css/timeline.css' %}" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="activities-container">
    <!-- Content específico de atividades -->
</div>
{% endblock %}
```

### **Componentes Especiais Necessários:**
1. **Activity Card** - Card de atividade com status visual
2. **Calendar Widget** - Calendário interativo
3. **Timeline Component** - Timeline de progresso
4. **Attendance Tracker** - Controle de presença
5. **Progress Bar** - Barra de progresso visual
6. **Rating System** - Sistema de avaliação
7. **Session Manager** - Gestor de sessões
8. **Notification Panel** - Painel de notificações

---

## 📊 **TEMPLATES DETALHADOS**

### **1. activities_dashboard.html (CRÍTICO)**
```html
<!-- Dashboard principal completo: -->
- Header com estatísticas principais
- Cards de resumo (total, ativas, concluídas, canceladas)
- Gráficos de distribuição por tipo
- Lista de próximas atividades
- Beneficiárias com mais atividades
- Alertas de atividades atrasadas
- Facilitadores mais ativos
- Acesso rápido para criar nova atividade
- Filtros de período e tipo
```

### **2. beneficiary_dashboard.html (CRÍTICO)**
```html
<!-- Dashboard específico da beneficiária: -->
- Header com foto e dados da beneficiária
- Timeline de atividades realizadas
- Atividades atuais em andamento
- Próximas atividades agendadas
- Progresso geral visual
- Notas e observações recentes
- Frequência e assiduidade
- Certificados obtidos
- Botões de ação (nova atividade, relatório)
```

### **3. activities_calendar.html (CRÍTICO)**
```html
<!-- Calendário interativo: -->
- Visualizações: mês, semana, dia
- Código de cores por tipo de atividade
- Eventos clicáveis com popups
- Drag-and-drop para reagendar
- Filtros por beneficiária, tipo, facilitador
- Legenda de cores e status
- Navegação entre períodos
- Botão para criar nova atividade
- Sincronização com calendários externos
```

### **4. activity_detail.html (CRÍTICO)**
```html
<!-- Detalhes completos da atividade: -->
- Header com título, tipo e status
- Informações básicas (datas, local, modalidade)
- Descrição e objetivos
- Responsáveis e facilitadores
- Lista de sessões planejadas/realizadas
- Controle de presença por sessão
- Notas e observações
- Anexos e materiais
- Feedback e avaliações
- Botões de ação (editar, sessão, presença)
- Timeline de eventos
```

### **5. activity_form.html (CRÍTICO)**
```html
<!-- Formulário de criação/edição: -->
- Formulário em abas organizadas:
  * Aba 1: Informações básicas
  * Aba 2: Programação e frequência
  * Aba 3: Responsáveis e recursos
  * Aba 4: Metas e objetivos
- Validação em tempo real
- Auto-complete para beneficiárias
- Seleção de facilitadores
- Upload de materiais
- Preview antes de salvar
```

### **6. attendance_record.html**
```html
<!-- Registro de presença: -->
- Lista de beneficiárias da sessão
- Checkboxes de presença rápida
- Campos para justificativas
- Tempo de chegada/saída
- Observações por beneficiária
- Fotos da sessão (opcional)
- Salvamento automático
- Relatório de presença instantâneo
```

---

## 🛠️ **RECURSOS TÉCNICOS NECESSÁRIOS**

### **JavaScript/Bibliotecas:**
```javascript
// Funcionalidades avançadas:
- FullCalendar.js (calendário interativo)
- Chart.js (gráficos e analytics)
- Sortable.js (drag-and-drop)
- Moment.js (manipulação de datas)
- Select2 (seleção avançada)
- DataTables (listas complexas)
- Cropper.js (upload de imagens)
- Print.js (impressão de relatórios)
```

### **CSS/Tailwind Específicos:**
```css
/* Componentes especiais: */
.activity-card { }
.activity-status-badge { }
.calendar-container { }
.timeline-activity { }
.attendance-grid { }
.progress-indicator { }
.rating-stars { }
.session-timeline { }
```

### **Django Específico:**
```python
# Features necessárias:
- Calendar view integration
- Complex filtering system
- Bulk operations
- Real-time notifications
- File upload handling
- Progress calculation
- Analytics aggregation
- Export functionality
```

---

## 📈 **MÉTRICAS E KPIs**

### **Dashboard deve mostrar:**
- Total de atividades por status
- Beneficiárias atendidas
- Taxa de frequência média
- Atividades por tipo
- Facilitadores mais ativos
- Atividades concluídas no prazo
- Satisfação média das atividades
- Tempo médio por atividade
- Beneficiárias com baixa frequência
- Próximos vencimentos

---

## 🔐 **PERMISSÕES E SEGURANÇA**

### **Níveis de Acesso:**
```python
# Permissões específicas:

FACILITATOR: # Facilitador
- Ver atividades que facilita
- Registrar presença
- Adicionar notas da sessão
- Upload de materiais
- Avaliar participação

TECHNICIAN: # Técnica
- Criar atividades para beneficiárias
- Gerenciar todas as etapas
- Ver relatórios de frequência
- Avaliar progresso
- Comunicar com facilitadores

COORDINATOR: # Coordenadora
- Visão geral de todas as atividades
- Analytics avançadas
- Gerenciar facilitadores
- Aprovar atividades especiais
- Relatórios estratégicos

ADMIN: # Administrador
- Configurar tipos de atividade
- Gerenciar permissões
- Backup e auditoria
- Configurações do sistema
```

---

## ⚡ **CRONOGRAMA DE IMPLEMENTAÇÃO**

### **Semana 1 (5 dias):**
**Dia 1:** Dashboard principal e beneficiária (activities_dashboard, beneficiary_dashboard)
**Dia 2:** Lista e formulário de atividades (activity_list, activity_form)
**Dia 3:** Detalhes e sessões (activity_detail, activity_sessions)
**Dia 4:** Calendário interativo (activities_calendar)
**Dia 5:** Controle de presença (attendance_record, attendance_report)

### **Semana 2 (3 dias):**
**Dia 1:** Timeline e progresso (activities_timeline, beneficiary_progress)
**Dia 2:** Feedback e avaliação (activity_feedback, activity_evaluation)
**Dia 3:** Analytics e relatórios (activities_analytics, activities_reports)

---

## 🔧 **INTEGRAÇÕES NECESSÁRIAS**

### **Com Outros Módulos:**
```python
# Integrações críticas:
- MEMBERS: Dados das beneficiárias
- SOCIAL: Anamnese para recomendações
- COACHING: Planos de ação relacionados
- WORKSHOPS: Migração de workshops existentes
- CERTIFICATES: Certificados de conclusão
- NOTIFICATIONS: Lembretes e alertas
- EVOLUTION: Registro de evolução
- CALENDAR: Sincronização externa
```

### **APIs e Serviços:**
```python
# Integrações externas:
- Google Calendar API
- WhatsApp API (lembretes)
- Email service (notificações)
- SMS service (alertas)
- Cloud storage (anexos)
- Analytics service
```

---

## ✅ **CHECKLIST DE IMPLEMENTAÇÃO**

### **Funcionalidades Core:**
- [ ] Dashboard principal completo
- [ ] CRUD de atividades
- [ ] Calendário interativo
- [ ] Controle de presença
- [ ] Sistema de sessões
- [ ] Timeline de progresso
- [ ] Feedback e avaliação
- [ ] Relatórios básicos

### **Funcionalidades Avançadas:**
- [ ] Analytics avançadas
- [ ] Integração calendário externo
- [ ] Notificações automáticas
- [ ] Bulk operations
- [ ] Mobile app (futuro)
- [ ] Offline capability
- [ ] Real-time updates
- [ ] Advanced filtering

### **UX/UI:**
- [ ] Interface intuitiva
- [ ] Responsivo mobile
- [ ] Loading states
- [ ] Error handling
- [ ] Keyboard shortcuts
- [ ] Print-friendly
- [ ] Accessibility
- [ ] Performance otimizada

---

## 🚀 **RECURSOS ESPECIAIS**

### **Sistema Unificado:**
```javascript
// Diferencial do sistema:
- Centrado na beneficiária
- Integração total com outros módulos
- Timeline unificada de progresso
- Analytics comportamentais
- Recomendações baseadas em IA (futuro)
- Gamificação (badges, conquistas)
```

### **Calendário Avançado:**
```javascript
// Features especiais:
- Drag-and-drop scheduling
- Conflict detection
- Recurring events
- Multiple views
- External calendar sync
- Mobile-friendly interface
```

### **Analytics Inteligentes:**
```html
<!-- Insights únicos: -->
- Padrões de participação
- Efetividade por tipo de atividade
- Correlação com evolução social
- Predição de abandono
- Recomendações personalizadas
- ROI das atividades
```

---

## 📋 **DEPENDÊNCIAS TÉCNICAS**

```bash
# Python packages necessários:
pip install django-calendar        # Calendar integration
pip install django-recurrence     # Recurring events
pip install django-filter         # Advanced filtering
pip install celery               # Background tasks
pip install redis               # Caching

# JavaScript libraries:
npm install @fullcalendar/core    # Calendar
npm install chart.js             # Charts
npm install moment.js            # Date handling
npm install select2             # Advanced selects
npm install datatables          # Tables
```

---

## 🎯 **PRÓXIMOS PASSOS**

### **Fase 1 - Core System:**
1. activities_dashboard.html
2. beneficiary_dashboard.html
3. activity_list.html
4. activity_form.html

### **Fase 2 - Advanced Features:**
1. activities_calendar.html
2. activity_detail.html
3. attendance_record.html

### **Fase 3 - Analytics:**
1. activities_timeline.html
2. activities_analytics.html
3. Integration features

---

**⏰ Estimativa Total: 8-10 dias de desenvolvimento**
**🎯 Prioridade: CRÍTICA - Quarta prioridade**
**💼 Impacto: ALTO - Sistema central para acompanhamento**
**🔄 Complexidade: ALTA - Sistema unificado e integrado**
**📱 Mobile: ESSENCIAL - Uso intensivo em campo**
