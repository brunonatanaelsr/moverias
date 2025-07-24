"""
Views simplificadas para sistema de upload de arquivos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import os
import mimetypes

from .models import FileUpload
from .upload_forms import FileUploadForm


@login_required
def upload_list(request):
    """Lista de uploads do usuário"""
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    uploads = FileUpload.objects.all()
    
    # Filtros
    if not request.user.is_staff:
        uploads = uploads.filter(Q(uploaded_by=request.user) | Q(is_public=True))
    
    if search:
        uploads = uploads.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) | 
            Q(original_name__icontains=search)
        )
    
    if category:
        uploads = uploads.filter(category=category)
    
    # Paginação
    paginator = Paginator(uploads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'categories': FileUpload.CATEGORY_CHOICES,
        'total_uploads': uploads.count(),
    }
    
    return render(request, 'core/uploads/list.html', context)


@login_required
def upload_file(request):
    """Upload de arquivo"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.uploaded_by = request.user
            upload.save()
            
            messages.success(request, f'Arquivo "{upload.title}" enviado com sucesso!')
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': f'Arquivo "{upload.title}" enviado com sucesso!',
                    'redirect': reverse('core_uploads:upload_list')
                })
            
            return redirect('core_uploads:upload_list')
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = FileUploadForm()
    
    context = {
        'form': form,
        'max_file_size': '10MB',  # Configurar conforme necessário
    }
    
    return render(request, 'core/uploads/upload.html', context)


@login_required
def download_file(request, pk):
    """Download de arquivo"""
    upload = get_object_or_404(FileUpload, pk=pk)
    
    # Verificar permissões
    if not upload.is_public and upload.uploaded_by != request.user and not request.user.is_staff:
        raise Http404("Arquivo não encontrado")
    
    # Incrementar contador de downloads
    upload.download_count += 1
    upload.save(update_fields=['download_count'])
    
    # Servir arquivo
    if upload.file:
        file_path = upload.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read())
                
            # Detectar tipo MIME
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type:
                response['Content-Type'] = content_type
            
            # Cabeçalhos para download
            response['Content-Disposition'] = f'attachment; filename="{upload.original_name}"'
            response['Content-Length'] = upload.file_size
            
            return response
    
    raise Http404("Arquivo não encontrado")


@login_required
def delete_upload(request, pk):
    """Deletar upload"""
    upload = get_object_or_404(FileUpload, pk=pk)
    
    # Verificar permissões
    if upload.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para deletar este arquivo.')
        return redirect('core_uploads:upload_list')
    
    if request.method == 'POST':
        filename = upload.title
        upload.delete()
        messages.success(request, f'Arquivo "{filename}" deletado com sucesso!')
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Arquivo "{filename}" deletado com sucesso!'
            })
        
        return redirect('core_uploads:upload_list')
    
    context = {
        'upload': upload,
    }
    
    return render(request, 'core/uploads/delete.html', context)


@login_required
def upload_detail(request, pk):
    """Detalhes do upload"""
    upload = get_object_or_404(FileUpload, pk=pk)
    
    # Verificar permissões
    if not upload.is_public and upload.uploaded_by != request.user and not request.user.is_staff:
        raise Http404("Arquivo não encontrado")
    
    context = {
        'upload': upload,
        'can_edit': upload.uploaded_by == request.user or request.user.is_staff,
    }
    
    return render(request, 'core/uploads/detail.html', context)


@login_required
@require_http_methods(["GET"])
def my_uploads(request):
    """Uploads do usuário atual"""
    uploads = FileUpload.objects.filter(uploaded_by=request.user)
    
    search = request.GET.get('search', '')
    if search:
        uploads = uploads.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) | 
            Q(original_name__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(uploads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_uploads': uploads.count(),
    }
    
    return render(request, 'core/uploads/my_uploads.html', context)


@login_required
def quick_upload(request):
    """Upload rápido via AJAX"""
    if request.method == 'POST' and request.headers.get('HX-Request'):
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.uploaded_by = request.user
            upload.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Arquivo "{upload.title}" enviado com sucesso!',
                'upload_id': upload.id,
                'file_name': upload.original_name,
                'file_size': upload.file_size_formatted,
                'download_url': reverse('core_uploads:download_file', args=[upload.id])
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})
