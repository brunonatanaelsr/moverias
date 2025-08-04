# 🌟 Move Marias - Sistema de Gestão de Beneficiárias

## 📋 Sobre o Sistema

O **Move Marias** é um sistema completo de gestão de beneficiárias desenvolvido para organizações sociais que trabalham com empoderamento feminino. O sistema oferece uma plataforma integrada para gerenciar desde o cadastro inicial até o acompanhamento contínuo do desenvolvimento das beneficiárias.

### 🎯 Objetivo
Proporcionar uma ferramenta robusta e intuitiva para o acompanhamento integral de beneficiárias, facilitando o trabalho das equipes técnicas e maximizando o impacto dos programas sociais.

### 👥 Público-Alvo
- Organizações sociais
- ONGs focadas em empoderamento feminino
- Projetos de desenvolvimento social
- Equipes técnicas e coordenadores

---

## 🏗️ Arquitetura do Sistema

### **Stack Tecnológica**
- **Backend**: Django 4.2 LTS (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, HTMX
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Cache**: Redis
- **Real-time**: Django Channels (WebSockets)
- **Tarefas**: Celery + Redis
- **Autenticação**: Django Allauth + OTP
- **API**: Django REST Framework
- **Documentação**: drf-spectacular (OpenAPI/Swagger)

### **Arquitetura Modular**
```
move-marias/
├── 🏠 Core (Núcleo)
├── 👥 Members (Beneficiárias)
├── 🎓 Workshops (Oficinas)
├── 🎯 Activities (Atividades)
├── 📋 Tasks (Tarefas)
├── 🎯 Coaching (Coaching)
├── 📢 Communication (Comunicação)
├── 🏆 Certificates (Certificados)
├── 📁 Projects (Projetos)
├── 🏥 Social (Anamnese Social)
├── 📊 Evolution (Evolução)
├── 💬 Chat (Chat em Tempo Real)
├── 📊 Dashboard (Painel Administrativo)
├── 🔔 Notifications (Notificações)
├── 👤 Users (Usuários)
└── 🏢 HR (Recursos Humanos)
```

---

## 📦 Módulos do Sistema

### 🏠 **Core (Núcleo)**
**Funcionalidades:**
- Sistema de permissões unificado
- Upload de arquivos integrado
- Sistema de exportação centralizado
- Utilitários compartilhados
- Middlewares personalizados

**Tecnologias:**
- Sistema de permissões baseado em grupos
- Upload com validação de tipos MIME
- Exportação CSV/Excel/PDF
- Cache Redis integrado

---

### 👥 **Members (Beneficiárias)**
**Funcionalidades:**
- ✅ Cadastro completo de beneficiárias
- ✅ Gestão de dados pessoais e familiares
- ✅ Histórico de participação
- ✅ Relatórios individuais
- ✅ Exportação de dados (CSV/Excel/PDF)

**Principais Campos:**
- Dados pessoais (nome, documento, contato)
- Endereço completo
- Informações familiares
- Status (ativa/inativa)
- Histórico de atividades

**Permissões:**
- Técnica: CRUD completo
- Coordenação: Visualização e relatórios

---

### 🎓 **Workshops (Oficinas)**
**Funcionalidades:**
- ✅ Criação e gestão de workshops
- ✅ Controle de vagas e inscrições
- ✅ Gestão de sessões
- ✅ Controle de frequência
- ✅ Avaliações e feedback
- ✅ Relatórios de participação
- ✅ Exportação completa (CSV/Excel/PDF)

**Tipos de Workshop:**
- Capacitação profissional
- Desenvolvimento pessoal
- Empreendedorismo
- Educação financeira
- Saúde e bem-estar

**Recursos Avançados:**
- Limite de participantes
- Sessões múltiplas
- Controle de presença por sessão
- Certificados automáticos
- Dashboard com métricas

---

### 🎯 **Activities (Atividades)**
**Funcionalidades:**
- ✅ Atividades individuais por beneficiária
- ✅ Sessões de acompanhamento
- ✅ Registro de presença
- ✅ Feedback e avaliações
- ✅ Notas e observações
- ✅ Dashboard centralizado
- ✅ Relatórios de evolução
- ✅ Exportação detalhada

**Tipos de Atividade:**
- Atendimento individual
- Acompanhamento psicossocial
- Orientação profissional
- Suporte familiar
- Mentoria

**Métricas:**
- Taxa de participação
- Evolução individual
- Frequência de atendimentos
- Efetividade dos programas

---

### 📋 **Tasks (Tarefas)**
**Funcionalidades:**
- ✅ Sistema Kanban completo
- ✅ Quadros personalizáveis
- ✅ Gestão de tarefas por projeto
- ✅ Atribuição de responsáveis
- ✅ Controle de prazos
- ✅ Comentários e anexos
- ✅ Relatórios de produtividade
- ✅ Exportação por quadro/usuário

**Recursos:**
- Drag & Drop entre colunas
- Filtros avançados
- Prioridades e tags
- Notificações automáticas
- Dashboard de métricas
- API para integrações

---

### 🎯 **Coaching (Coaching)**
**Funcionalidades:**
- ✅ Planos de ação personalizados
- ✅ Roda da Vida (Wheel of Life)
- ✅ Sessões de coaching
- ✅ Acompanhamento de metas
- ✅ Relatórios de progresso
- ✅ Dashboard de resultados
- ✅ Exportação completa

**Ferramentas:**
- Definição de objetivos SMART
- Avaliação de áreas da vida
- Planos de desenvolvimento
- Métricas de progresso
- Histórico de sessões

---

### 📢 **Communication (Comunicação)**
**Funcionalidades:**
- ✅ Comunicados internos
- ✅ Sistema de mensagens
- ✅ Newsletters
- ✅ Caixa de sugestões
- ✅ Políticas e procedimentos
- ✅ Analytics de engajamento
- ✅ Exportação de dados

**Recursos:**
- Comunicação segmentada
- Agendamento de envios
- Templates personalizáveis
- Métricas de abertura
- Feedback integrado

---

### 🏆 **Certificates (Certificados)**
**Funcionalidades:**
- ✅ Geração automática de certificados
- ✅ Templates personalizáveis
- ✅ Assinatura digital
- ✅ Controle de autenticidade
- ✅ Histórico de emissões
- ✅ Exportação PDF profissional

**Tipos de Certificado:**
- Conclusão de workshop
- Participação em atividades
- Reconhecimento de mérito
- Declarações de comparecimento
- Recibos de benefícios

---

### 📁 **Projects (Projetos)**
**Funcionalidades:**
- ✅ Gestão de projetos sociais
- ✅ Matrículas de beneficiárias
- ✅ Acompanhamento de progresso
- ✅ Relatórios de impacto
- ✅ Exportação de dados

**Métricas:**
- Número de beneficiárias atendidas
- Taxa de conclusão
- Impacto por projeto
- ROI social

---

### 🏥 **Social (Anamnese Social)**
**Funcionalidades:**
- ✅ Anamnese social completa
- ✅ Histórico familiar
- ✅ Situação socioeconômica
- ✅ Planos de intervenção
- ✅ Relatórios sociais
- ✅ Exportação PDF

**Campos Principais:**
- Composição familiar
- Situação habitacional
- Renda familiar
- Saúde e educação
- Vulnerabilidades
- Recursos disponíveis

---

### 📊 **Evolution (Evolução)**
**Funcionalidades:**
- ✅ Registros de evolução individual
- ✅ Acompanhamento temporal
- ✅ Métricas de desenvolvimento
- ✅ Relatórios de progresso
- ✅ Exportação Excel/PDF

**Indicadores:**
- Desenvolvimento pessoal
- Progressão profissional
- Autonomia financeira
- Bem-estar psicossocial

---

### 💬 **Chat (Chat em Tempo Real)**
**Funcionalidades:**
- ✅ Mensagens instantâneas
- ✅ Salas por projeto/workshop
- ✅ Arquivos e mídia
- ✅ Notificações push
- ✅ Histórico de conversas
- ✅ Moderação automática

**Tecnologia:**
- WebSockets (Django Channels)
- Redis para sessões
- Upload de arquivos
- Emoji e reações
- Status online/offline

---

### 📊 **Dashboard (Painel Administrativo)**
**Funcionalidades:**
- ✅ Visão geral do sistema
- ✅ Métricas em tempo real
- ✅ Gráficos interativos
- ✅ Alertas e notificações
- ✅ Relatórios executivos
- ✅ Exportação de dados

**Métricas Principais:**
- Total de beneficiárias ativas
- Workshops em andamento
- Taxa de participação
- Evolução mensal
- Indicadores de impacto

---

### 🔔 **Notifications (Notificações)**
**Funcionalidades:**
- ✅ Notificações em tempo real
- ✅ Email automático
- ✅ Push notifications
- ✅ Agendamento de envios
- ✅ Templates personalizáveis
- ✅ Relatórios de entrega

**Tipos:**
- Lembretes de workshop
- Vencimento de tarefas
- Novas mensagens
- Atualizações do sistema
- Alertas administrativos

---

### 👤 **Users (Usuários)**
**Funcionalidades:**
- ✅ Gestão de usuários
- ✅ Perfis e permissões
- ✅ Autenticação 2FA
- ✅ Histórico de atividades
- ✅ Relatórios de uso
- ✅ Exportação de dados

**Tipos de Usuário:**
- **Administrador**: Acesso total
- **Coordenação**: Gestão e relatórios
- **Técnica**: Operações diárias
- **Suporte**: Funcionalidades limitadas

---

### 🏢 **HR (Recursos Humanos)**
**Funcionalidades:**
- ✅ Gestão de colaboradores
- ✅ Documentos e contratos
- ✅ Avaliações de desempenho
- ✅ Treinamentos
- ✅ Relatórios de RH
- ✅ Analytics organizacional

---

## 🔐 Sistema de Segurança

### **Autenticação e Autorização**
- ✅ Login seguro com Django Allauth
- ✅ Autenticação de dois fatores (2FA)
- ✅ Controle de sessões
- ✅ Logout automático por inatividade
- ✅ Senhas com política de segurança

### **Permissões**
- ✅ Sistema baseado em grupos
- ✅ Permissões granulares por módulo
- ✅ Controle de acesso a dados sensíveis
- ✅ Auditoria de ações

### **Proteção de Dados**
- ✅ Criptografia de dados sensíveis
- ✅ Backup automático
- ✅ Logs de segurança
- ✅ Compliance com LGPD

---

## 📊 Sistema de Exportação

### **Formatos Suportados**
- **CSV**: Compatibilidade universal, ideal para análises
- **Excel (XLSX)**: Formatação profissional com cores e estilos
- **PDF**: Relatórios profissionais com paginação automática

### **Funcionalidades**
- ✅ Exportação centralizada e unificada
- ✅ Templates profissionais para PDF
- ✅ Formatação automática de dados
- ✅ Filtros avançados
- ✅ Tratamento robusto de erros
- ✅ Cache para performance

### **Módulos com Exportação**
Todos os 12 módulos possuem funcionalidade completa de exportação:
- Dashboard, Evolution, Workshops, Activities, Tasks
- Coaching, Communication, Certificates, Projects
- Social, Notifications, Users, HR

---

## 🚀 Tecnologias e Dependências

### **Principais Dependências**
```python
# Framework Principal
Django==4.2.13               # Framework web LTS
djangorestframework==3.14.0  # API REST

# Autenticação e Segurança
django-allauth==0.57.0       # Sistema de autenticação
django-otp==1.2.0           # Two-factor authentication
argon2-cffi==23.1.0         # Hash de senhas
django-ratelimit==4.1.0     # Rate limiting

# Real-time e Background
channels==4.0.0              # WebSockets
celery==5.3.4               # Tarefas em background
redis>=4.5.0                # Cache e broker

# Exportação e Relatórios
openpyxl==3.1.2             # Excel
xlsxwriter==3.1.9           # Excel avançado
WeasyPrint==60.2            # PDF
reportlab==4.0.7            # PDF alternativo

# Upload e Mídia
Pillow>=10.0.0              # Processamento de imagens
python-magic>=0.4.24       # Detecção de tipos de arquivo

# Frontend e UI
django-crispy-forms==2.1     # Formulários
django-htmx==1.17.0         # HTMX para UI dinâmica
django-widget-tweaks==1.5.0 # Customização de widgets

# Produção
gunicorn==21.2.0            # Servidor WSGI
whitenoise>=6.6.0           # Arquivos estáticos
psycopg2-binary             # PostgreSQL (produção)
```

### **Ferramentas de Desenvolvimento**
```python
# Teste e Qualidade
pytest>=7.4.0              # Framework de testes
pytest-django>=4.5.0       # Integração Django
coverage>=7.0.0            # Cobertura de testes
factory-boy>=3.2.0         # Fixtures de teste

# Debug e Desenvolvimento
django-debug-toolbar==4.2.0 # Debug toolbar
django-extensions==3.2.3    # Utilitários extras

# Documentação da API
drf-spectacular==0.26.5      # OpenAPI/Swagger
```

---

## 📈 Métricas e Analytics

### **Dashboard Principal**
- Total de beneficiárias ativas
- Workshops em andamento
- Taxa de participação geral
- Evolução mensal
- Aniversariantes do dia
- Atividades recentes

### **Métricas por Módulo**
- **Workshops**: Taxa de conclusão, frequência média
- **Activities**: Sessões por beneficiária, engajamento
- **Tasks**: Produtividade, tempo médio de conclusão
- **Coaching**: Progresso de metas, áreas de desenvolvimento
- **Communication**: Taxa de abertura, engajamento

### **Relatórios Executivos**
- Impacto dos programas
- ROI social
- Efetividade das intervenções
- Evolução das beneficiárias
- Performance da equipe

---

## 🔧 Instalação e Configuração

### **Pré-requisitos**
- Python 3.10+
- Redis Server
- PostgreSQL (produção)
- Node.js (para assets)

### **Instalação Rápida**
```bash
# Clone o repositório
git clone [repository-url]
cd move-marias

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure banco de dados
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Execute o servidor
python manage.py runserver
```

### **Configuração de Produção**
```bash
# Configurar variáveis de ambiente
export DJANGO_SETTINGS_MODULE=movemarias.settings.production
export DATABASE_URL=postgresql://user:pass@localhost/dbname
export REDIS_URL=redis://localhost:6379
export SECRET_KEY=your-secret-key

# Coletar arquivos estáticos
python manage.py collectstatic

# Executar com Gunicorn
gunicorn movemarias.wsgi:application
```

---

## 📚 Documentação da API

### **Endpoints Principais**
```
GET /api/v1/beneficiaries/     # Lista beneficiárias
POST /api/v1/beneficiaries/    # Cria beneficiária
GET /api/v1/workshops/         # Lista workshops
POST /api/v1/workshops/        # Cria workshop
GET /api/v1/activities/        # Lista atividades
POST /api/v1/activities/       # Cria atividade
```

### **Autenticação**
```
Authorization: Bearer [JWT_TOKEN]
```

### **Documentação Interativa**
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **Schema**: `/api/schema/`

---

## 🧪 Testes

### **Executar Testes**
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=.

# Módulo específico
pytest tests/test_members.py

# Com relatório HTML
pytest --cov=. --cov-report=html
```

### **Cobertura de Testes**
- ✅ Models: 95%+
- ✅ Views: 90%+
- ✅ Forms: 95%+
- ✅ Utils: 100%
- ✅ APIs: 90%+

---

## 🚀 Deploy e Produção

### **Ambientes Suportados**
- ✅ Heroku
- ✅ AWS (EC2, ECS, Lambda)
- ✅ Google Cloud Platform
- ✅ DigitalOcean
- ✅ VPS tradicional

### **Docker Support**
```dockerfile
# Dockerfile incluído para containerização
docker build -t move-marias .
docker run -p 8000:8000 move-marias
```

### **Checklist de Produção**
- ✅ SSL/HTTPS configurado
- ✅ Backup automático do banco
- ✅ Monitoramento de erros (Sentry)
- ✅ Logs centralizados
- ✅ Cache Redis configurado
- ✅ CDN para arquivos estáticos
- ✅ Firewall e segurança

---

## 📞 Suporte e Contribuição

### **Reportar Issues**
- Usar o sistema de Issues do GitHub
- Incluir logs e informações do ambiente
- Descrever passos para reproduzir

### **Contribuir**
1. Fork do repositório
2. Criar branch para feature
3. Implementar com testes
4. Pull Request com descrição detalhada

### **Coding Standards**
- PEP 8 para Python
- Testes obrigatórios
- Documentação atualizada
- Code review aprovado

---

## 📜 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 🏆 Status do Projeto

### **Versão Atual**: 2.0
### **Status**: ✅ Produção
### **Cobertura de Testes**: 95%+
### **Funcionalidades**: 100% implementadas
### **Documentação**: ✅ Completa

### **Próximas Versões**
- [ ] Mobile App (React Native)
- [ ] Integração com WhatsApp Business
- [ ] Machine Learning para predições
- [ ] Dashboard público para beneficiárias

---

## 👥 Equipe

Desenvolvido com ❤️ pela equipe Move Marias para empoderar mulheres através da tecnologia.

**Contato**: [seu-email@exemplo.com]
**Website**: [https://movemarias.org]
**GitHub**: [https://github.com/brunonatanaelsr/moverias]

---

*"Tecnologia a serviço da transformação social"* 🌟
