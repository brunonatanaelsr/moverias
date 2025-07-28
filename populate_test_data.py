#!/usr/bin/env python
import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.contrib.auth.models import Group, User
from members.models import Beneficiary
from social.models import SocialAnamnesis

def populate_test_data():
    """Popula o banco com dados de teste"""
    
    # Criar grupo Técnica se não existir
    group, created = Group.objects.get_or_create(name='Tecnica')
    print(f'Grupo Técnica criado: {created}')
    
    # Verificar se usuário bruno existe e adicionar ao grupo
    try:
        user = User.objects.get(username='bruno')
        user.groups.add(group)
        print(f'Usuário bruno adicionado ao grupo Técnica')
    except User.DoesNotExist:
        print('Usuário bruno não encontrado')
        return
    
    # Criar algumas beneficiárias de exemplo
    beneficiaries_data = [
        {
            'full_name': 'Maria Silva Santos', 
            'date_of_birth': date(1985, 3, 15), 
            'cpf': '12345678901', 
            'phone': '(11) 99999-1111',
            'email': 'maria.silva@email.com',
            'address': 'Rua das Flores, 123'
        },
        {
            'full_name': 'Ana Paula Oliveira', 
            'date_of_birth': date(1990, 7, 22), 
            'cpf': '23456789012', 
            'phone': '(11) 99999-2222',
            'email': 'ana.paula@email.com',
            'address': 'Av. Central, 456'
        },
        {
            'full_name': 'Carla Fernanda Costa', 
            'date_of_birth': date(1987, 11, 8), 
            'cpf': '34567890123', 
            'phone': '(11) 99999-3333',
            'email': 'carla.costa@email.com',
            'address': 'Rua da Paz, 789'
        },
    ]
    
    beneficiaries = []
    for data in beneficiaries_data:
        beneficiary, created = Beneficiary.objects.get_or_create(
            cpf=data['cpf'],
            defaults=data
        )
        if created:
            print(f'Beneficiária criada: {beneficiary.full_name}')
        else:
            print(f'Beneficiária já existe: {beneficiary.full_name}')
        beneficiaries.append(beneficiary)
    
    # Criar algumas anamneses de exemplo
    for i, beneficiary in enumerate(beneficiaries):
        anamnesis_data = {
            'beneficiary': beneficiary,
            'created_by': user,
            'family_income': 1500.00 + (i * 200),
            'housing_situation': f'Casa própria com {2+i} cômodos, boa estrutura.',
            'support_network': f'Família próxima, vizinhos e igreja local. Participa de grupos comunitários.',
            'observations': f'Beneficiária {beneficiary.full_name} demonstra interesse em capacitação profissional.',
            'status': 'completed' if i % 2 == 0 else 'draft'
        }
        
        anamnesis, created = SocialAnamnesis.objects.get_or_create(
            beneficiary=beneficiary,
            defaults=anamnesis_data
        )
        if created:
            print(f'Anamnese criada para: {beneficiary.full_name}')
        else:
            print(f'Anamnese já existe para: {beneficiary.full_name}')
    
    print(f'\nResumo:')
    print(f'Total de beneficiárias: {Beneficiary.objects.count()}')
    print(f'Total de anamneses: {SocialAnamnesis.objects.count()}')
    print(f'Anamneses concluídas: {SocialAnamnesis.objects.filter(status="completed").count()}')
    print(f'Anamneses em rascunho: {SocialAnamnesis.objects.filter(status="draft").count()}')

if __name__ == '__main__':
    populate_test_data()
