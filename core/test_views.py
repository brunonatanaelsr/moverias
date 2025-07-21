from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

@ensure_csrf_cookie
def test_csrf(request):
    """View para testar CSRF"""
    context = {
        'page_title': 'Teste CSRF',
        'request': request,
    }
    return render(request, 'test_csrf.html', context)
