# Move Marias 💜

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)

Sistema de Gestão e Acompanhamento Social desenvolvido para o **Move Marias**, uma organização dedicada ao atendimento, acompanhamento e desenvolvimento de beneficiárias em situação de vulnerabilidade social.

## 🌟 Funcionalidades

### 👥 Gestão de Beneficiárias
- Cadastro completo com dados pessoais criptografados (RG, CPF)
- Controle de documentos e termos de consentimento (LGPD)
- Histórico completo de atendimentos

### 📋 Anamnese Social
- Formulário em múltiplas etapas para avaliação social
- Coleta de dados familiares, renda e vulnerabilidades
- Bloqueio automático após finalização (apenas superusuários podem editar)

### 🎯 Projetos e Matrículas
- Gestão de projetos educacionais e profissionalizantes
- Controle de horários, turnos e status de matrícula
- Códigos únicos de matrícula gerados automaticamente

### 📈 Registros de Evolução
- Acompanhamento do progresso individual
- Sistema de assinaturas digitais
- Histórico temporal de desenvolvimento

### 🧭 Coaching e Desenvolvimento
- **Roda da Vida**: Avaliação em 12 áreas de desenvolvimento pessoal
- **Planos de Ação**: Definição de metas e estratégias personalizadas
- Revisões semestrais e acompanhamento contínuo

### 🔐 Sistema de Autenticação
- Login seguro com django-allauth
- Grupos de usuários: Admin, Técnica, Educadora, Voluntária
- Permissões granulares por tipo de usuário
- Suporte a 2FA com django-otp

### 🌐 Interface Moderna
- Dashboard responsivo com Tailwind CSS
- Busca dinâmica com HTMX
- Modais interativos para visualização rápida
- Experiência mobile-first

### 📊 API REST
- Endpoints completos para todos os recursos
- Exportação de dados em ZIP (PDF + JSON)
- Autenticação por token
- Documentação automática

## 🚀 Instalação

### Pré-requisitos
- Python 3.10+
- Git

### 1. Clone o repositório
```bash
git clone https://github.com/movemarias/sistema-gestao.git
cd sistema-gestao
```

### 2. Configure o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env conforme necessário
```

### 5. Execute as migrações
```bash
python manage.py migrate
```

### 6. Crie grupos e permissões
```bash
python manage.py setup_groups
```

### 7. Crie dados de exemplo (opcional)
```bash
python manage.py create_sample_data
```

### 8. Execute o servidor
```bash
python manage.py runserver
```

Acesse: http://localhost:8000

## 👤 Usuários de Teste

Após executar `create_sample_data`:

| Tipo | Usuário | Senha | Descrição |
|------|---------|-------|-----------|
| Admin | admin | admin123 | Acesso total ao sistema |
| Técnica | maria.silva | movemarias2025 | Acesso técnico completo |

## 🛠️ Tecnologias

### Backend
- **Django 4.2 LTS** - Framework web robusto
- **Django REST Framework** - API REST
- **django-allauth** - Autenticação avançada
- **django-cryptography** - Criptografia de dados sensíveis
- **django-otp** - Autenticação de dois fatores
- **WeasyPrint** - Geração de PDFs

### Frontend
- **Tailwind CSS** - Framework CSS utilitário
- **HTMX** - Interatividade sem JavaScript complexo
- **Crispy Forms** - Formulários estilizados

### Banco de Dados
- **SQLite** (desenvolvimento)
- **PostgreSQL** (produção via DATABASE_URL)

### Deploy
- **Django Storages + S3** - Arquivos estáticos em produção
- **Gunicorn** - Servidor WSGI
- **Docker** - Containerização (opcional)

## 📁 Estrutura do Projeto

```
movemarias/
├── api/              # API REST
├── coaching/         # Roda da Vida e Planos de Ação
├── core/             # Funcionalidades centrais
├── dashboard/        # Interface administrativa
├── evolution/        # Registros de evolução
├── members/          # Gestão de beneficiárias
├── projects/         # Projetos e matrículas
├── social/           # Anamnese social
├── static/           # Arquivos estáticos
├── templates/        # Templates HTML
└── media/            # Uploads de arquivos
```

## 🔧 Configuração para Produção

### Variáveis de Ambiente
```env
DEBUG=False
SECRET_KEY=sua-chave-secreta-super-segura
DATABASE_URL=postgresql://user:pass@host:port/dbname
DJANGO_CRYPTOGRAPHY_KEY=chave-para-criptografia
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
ENVIRONMENT=production

# AWS S3 (opcional)
AWS_ACCESS_KEY_ID=sua-access-key
AWS_SECRET_ACCESS_KEY=sua-secret-key
AWS_STORAGE_BUCKET_NAME=seu-bucket
AWS_S3_REGION_NAME=us-east-1
```

### Docker (opcional)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD gunicorn movemarias.wsgi:application --bind 0.0.0.0:$PORT
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Testar app específico
python manage.py test members

# Testar com coverage
coverage run --source='.' manage.py test
coverage report
```

### Testes Específicos Implementados
- Criptografia de dados sensíveis (CPF, RG)
- Bloqueio de anamnese para não-superusuários
- Geração de códigos de matrícula únicos
- Validações de formulários
- Permissões de acesso por grupo

## 📖 Uso da API

### Autenticação
```bash
# Login via API
curl -X POST http://localhost:8000/api-auth/login/ \
  -d "username=maria.silva&password=movemarias2025"

# Usando token
curl -H "Authorization: Token seu-token-aqui" \
  http://localhost:8000/api/beneficiaries/
```

### Endpoints Principais
- `GET /api/beneficiaries/` - Listar beneficiárias
- `POST /api/beneficiaries/` - Criar beneficiária
- `GET /api/beneficiaries/{id}/export/` - Exportar dados
- `GET /api/social-anamnesis/` - Anamneses sociais
- `GET /api/project-enrollments/` - Matrículas
- `GET /api/evolution-records/` - Registros de evolução

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código
- Seguir PEP 8
- Documentar funções e classes
- Escrever testes para novas funcionalidades
- Usar type hints quando possível

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 💖 Agradecimentos

- **Comunidade Move Marias** - Por inspirar esta solução
- **Django Community** - Pelo framework excepcional
- **Contribuidores** - Por tornarem este projeto possível

---

## 🆘 Suporte

Para dúvidas, problemas ou sugestões:

- 📧 Email: dev@movemarias.org
- 🐛 Issues: [GitHub Issues](https://github.com/movemarias/sistema-gestao/issues)
- 📖 Documentação: [Wiki do Projeto](https://github.com/movemarias/sistema-gestao/wiki)

---

**Desenvolvido com 💜 para transformação social**

*Move Marias - Movendo vidas, construindo futuros*
