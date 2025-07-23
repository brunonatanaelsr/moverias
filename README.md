# MoveMarias - Sistema de Gestão Social

Sistema Django para gestão e acompanhamento social das beneficiárias do projeto Move Marias.

## Instalação

1. Ative o ambiente virtual:
```bash
source venv/bin/activate
```

2. Execute o servidor:
```bash
python manage.py runserver
```

3. Acesse o sistema:
- Dashboard: http://127.0.0.1:8000/dashboard/
- Admin: http://127.0.0.1:8000/admin/

## Login
- Email: admin@movemarias.org
- Senha: admin123

## Estrutura
- **users/**: Sistema de usuários e autenticação
- **core/**: Funcionalidades centrais e uploads
- **dashboard/**: Painel principal
- **members/**: Gestão de beneficiários
- **projects/**: Gestão de projetos
- **workshops/**: Sistema de workshops
- **certificates/**: Emissão de certificados
- **coaching/**: Sistema de coaching
- **notifications/**: Sistema de notificações
- **social/**: Anamnese social

## Tecnologias
- Django 4.2 LTS
- Python 3.10.4
- SQLite
- TailwindCSS
- HTMX
# move
