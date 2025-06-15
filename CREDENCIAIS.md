# 🔐 CREDENCIAIS DE ACESSO - MOVE MARIAS

## 📋 Informações de Acesso ao Sistema

### 👑 **ADMINISTRADOR**
- **Email**: `admin@movemarias.org`
- **Senha**: `admin123`
- **Permissões**: Acesso total ao sistema

### 👩‍💼 **TÉCNICA** 
- **Email**: `maria.silva@movemarias.org`
- **Senha**: `senha123`
- **Permissões**: Acesso às beneficiárias, anamneses e relatórios

---

## 🌐 **URLs de Acesso**

- **Página Principal**: http://127.0.0.1:8000/
- **Login**: http://127.0.0.1:8000/accounts/login/
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Admin Django**: http://127.0.0.1:8000/admin/
- **API**: http://127.0.0.1:8000/api/

---

## 🚀 **Como Iniciar o Servidor**

```bash
# 1. Ative o ambiente virtual
source venv/bin/activate

# 2. Execute o servidor
python manage.py runserver

# 3. Acesse no navegador
open http://127.0.0.1:8000
```

---

## 📱 **Funcionalidades Principais**

### ✅ **Implementado**
- ✅ Sistema de autenticação (Django Allauth)
- ✅ Dashboard responsivo com Tailwind CSS
- ✅ CRUD de Beneficiárias
- ✅ Anamnese Social com wizard de 3 etapas
- ✅ Projetos e Matrículas
- ✅ Registros de Evolução
- ✅ Planos de Ação e Roda da Vida
- ✅ API REST completa
- ✅ Interface HTMX para UX moderna
- ✅ Grupos de usuários com permissões
- ✅ Criptografia de dados sensíveis
- ✅ Templates responsivos

### 🔄 **Próximos Passos**
- 📝 Formulários de criação/edição
- 📊 Relatórios e dashboards
- 📄 Geração de PDFs
- 📧 Notificações por email
- 🔐 Autenticação de dois fatores

---

## 🛠️ **Comandos Úteis**

```bash
# Criar novo superusuário
python manage.py createsuperuser

# Configurar grupos e permissões
python manage.py setup_groups

# Criar dados de exemplo
python manage.py create_sample_data

# Fazer backup do banco
cp db.sqlite3 backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

---

## 🔧 **Configuração de Ambiente**

### Desenvolvimento
- Banco: SQLite (db.sqlite3)
- Debug: Ativado
- Static files: Local

### Produção
- Defina `DATABASE_URL` para PostgreSQL
- Configure `DEBUG=False`
- Configure AWS S3 para arquivos estáticos

---

## 💜 **Move Marias - Transformando Vidas**

Sistema desenvolvido para apoiar o trabalho social da organização Move Marias, facilitando o acompanhamento e desenvolvimento de beneficiárias em situação de vulnerabilidade social.

**Desenvolvido com 💜 para a transformação social.**
