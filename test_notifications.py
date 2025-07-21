#!/usr/bin/env python
"""
Script para testar a funcionalidade de notificações
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from notifications.views import NotificationListView

def test_notifications():
    """Testar a view de notificações"""
    print("🔍 Testando funcionalidade de notificações...")
    
    # Criar usuário de teste
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado")
        return False
    
    print(f"✅ Usuário admin encontrado: {admin_user.email}")
    
    # Criar request factory
    factory = RequestFactory()
    request = factory.get('/notifications/')
    request.user = admin_user
    
    # Testar view
    try:
        view = NotificationListView.as_view()
        response = view(request)
        
        print(f"✅ View executada com sucesso")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Página de notificações funcionando corretamente")
            return True
        else:
            print(f"❌ Erro na página: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar view: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_notifications_data():
    """Verificar dados de notificações"""
    from notifications.models import Notification
    
    print("\n🔍 Verificando dados de notificações...")
    
    total_notifications = Notification.objects.count()
    print(f"📊 Total de notificações: {total_notifications}")
    
    if total_notifications == 0:
        print("ℹ️  Nenhuma notificação encontrada - vamos criar uma de teste")
        
        # Criar notificação de teste
        User = get_user_model()
        admin_user = User.objects.filter(is_staff=True).first()
        
        if admin_user:
            notification = Notification.objects.create(
                recipient=admin_user,
                title="Notificação de Teste",
                message="Esta é uma notificação de teste para verificar a funcionalidade.",
                type="info"
            )
            print(f"✅ Notificação de teste criada: {notification.id}")
        else:
            print("❌ Não foi possível criar notificação de teste")
    else:
        print(f"✅ {total_notifications} notificações encontradas")

if __name__ == "__main__":
    print("🚀 Iniciando teste de notificações...")
    
    # Testar funcionalidade
    success = test_notifications()
    
    # Verificar dados
    check_notifications_data()
    
    if success:
        print("\n✅ Teste de notificações concluído com sucesso!")
        print("🌐 Acesse: http://127.0.0.1:8000/notifications/")
    else:
        print("\n❌ Teste de notificações falhou!")
        sys.exit(1)
