"""
Views para upload seguro de arquivos
"""

import json
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django_ratelimit.decorators import ratelimit  # ENHANCED: Rate limiting

from .file_upload import SecureFileUploader
from .integrated_upload import UploadedFile, IntegratedFileUploadHandler, process_file_upload
from .logging_config import get_security_logger  # ENHANCED: Security logging

logger = logging.getLogger(__name__)
security_logger = get_security_logger()


@method_decorator(login_required, name='dispatch')
class FileUploadView(View):
    """
    View base para upload de arquivos
    """
    
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))  # ENHANCED: Rate limit
    def post(self, request, *args, **kwargs):
        """Handle file upload"""
        try:
            # Verificar se há arquivo
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhum arquivo enviado'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            file_type = request.POST.get('type', 'document')
            subfolder = request.POST.get('subfolder', '')
            
            # Verificar tipo válido
            if file_type not in SecureFileUploader.ALLOWED_FILE_TYPES:
                return JsonResponse({
                    'success': False,
                    'error': f'Tipo de arquivo inválido: {file_type}'
                }, status=400)
            
            # Fazer upload
            uploader = SecureFileUploader(file_type)
            result = uploader.upload_file(uploaded_file, subfolder)
            
            # Log de segurança
            security_logger.info(f"Arquivo enviado: {result['filename']} ({result['size']} bytes) - Usuário: {request.user.id}")
            
            return JsonResponse({
                'success': True,
                'file': {
                    'name': result['filename'],
                    'original_name': result['original_name'],
                    'url': result['url'],
                    'size': result['size'],
                    'type': result['type'],
                    'hash': result['hash']
                }
            })
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }, status=500)


@method_decorator(login_required, name='dispatch')
class FileValidationView(View):
    """
    View para validação de arquivos sem upload
    """
    
    def post(self, request, *args, **kwargs):
        """Validate file without uploading"""
        try:
            if 'file' not in request.FILES:
                return JsonResponse({
                    'valid': False,
                    'error': 'Nenhum arquivo enviado'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            file_type = request.POST.get('type', 'document')
            
            if file_type not in SecureFileUploader.ALLOWED_FILE_TYPES:
                return JsonResponse({
                    'valid': False,
                    'error': f'Tipo de arquivo inválido: {file_type}'
                }, status=400)
            
            # Validar arquivo
            uploader = SecureFileUploader(file_type)
            is_valid, message = uploader.validate_file(uploaded_file)
            
            response_data = {
                'valid': is_valid,
                'message': message
            }
            
            if is_valid:
                response_data['file_info'] = {
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'type': uploaded_file.content_type
                }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'error': f'Erro na validação: {str(e)}'
            }, status=500)


@login_required
def get_upload_config(request):
    """
    Retorna configurações de upload para o frontend
    """
    try:
        file_type = request.GET.get('type', 'document')
        
        if file_type not in SecureFileUploader.ALLOWED_FILE_TYPES:
            return JsonResponse({
                'error': f'Tipo de arquivo inválido: {file_type}'
            }, status=400)
        
        config = SecureFileUploader.ALLOWED_FILE_TYPES[file_type]
        
        return JsonResponse({
            'success': True,
            'config': {
                'type': file_type,
                'max_size': config['max_size'],
                'max_size_mb': config['max_size'] / (1024 * 1024),
                'allowed_extensions': config['extensions'],
                'allowed_mimetypes': config['mimetypes']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erro ao obter configuração: {str(e)}'
        }, status=500)


class UploadedFileListView(LoginRequiredMixin, ListView):
    """Lista de arquivos enviados pelo usuário"""
    model = UploadedFile
    template_name = 'core/upload_list.html'
    context_object_name = 'files'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar arquivos do usuário atual"""
        qs = UploadedFile.objects.filter(uploaded_by=self.request.user)
        
        # Filtros
        file_type = self.request.GET.get('type')
        if file_type:
            qs = qs.filter(file_type=file_type)
        
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(original_filename__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return qs.order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_types'] = UploadedFile.FILE_TYPE_CHOICES
        context['statuses'] = UploadedFile.UPLOAD_STATUS_CHOICES
        return context


class UploadedFileDetailView(LoginRequiredMixin, DetailView):
    """Detalhes de arquivo enviado"""
    model = UploadedFile
    template_name = 'core/upload_detail.html'
    context_object_name = 'file'
    
    def get_queryset(self):
        """Apenas arquivos do usuário atual ou públicos"""
        return UploadedFile.objects.filter(
            Q(uploaded_by=self.request.user) | Q(is_public=True)
        )


class UploadedFileDeleteView(LoginRequiredMixin, DeleteView):
    """Excluir arquivo enviado"""
    model = UploadedFile
    template_name = 'core/upload_confirm_delete.html'
    success_url = reverse_lazy('core:upload-list')
    
    def get_queryset(self):
        """Apenas arquivos do usuário atual"""
        return UploadedFile.objects.filter(uploaded_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Excluir arquivo físico também"""
        self.object = self.get_object()
        
        # Excluir arquivo físico
        self.object.delete_file()
        
        # Excluir registro
        response = super().delete(request, *args, **kwargs)
        
        messages.success(request, f'Arquivo "{self.object.original_filename}" excluído com sucesso.')
        return response


@login_required
def upload_file_view(request):
    """View para upload de arquivos"""
    if request.method == 'POST':
        result = process_file_upload(request)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('core:upload-list')
        else:
            messages.error(request, result.get('message', 'Erro ao enviar arquivo'))
    
    return render(request, 'core/upload_form.html')


@login_required
@csrf_exempt
def upload_ajax_view(request):
    """View AJAX para upload de arquivos"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    result = process_file_upload(request)
    return JsonResponse(result)


@login_required
def upload_validate_view(request):
    """Validar arquivo antes do upload"""
    if request.method != 'POST' or 'file' not in request.FILES:
        return JsonResponse({'valid': False, 'errors': ['Nenhum arquivo enviado']})
    
    file_obj = request.FILES['file']
    handler = IntegratedFileUploadHandler(request.user)
    
    try:
        handler._validate_file_basic(file_obj)
        return JsonResponse({'valid': True, 'message': 'Arquivo válido'})
    except ValueError as e:
        return JsonResponse({'valid': False, 'errors': [str(e)]})


@login_required
def upload_progress_view(request, file_id):
    """Verificar progresso do upload"""
    try:
        uploaded_file = UploadedFile.objects.get(
            id=file_id,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'status': uploaded_file.status,
            'filename': uploaded_file.original_filename,
            'progress': 100 if uploaded_file.status == 'completed' else 50,
            'message': uploaded_file.get_status_display()
        })
    except UploadedFile.DoesNotExist:
        return JsonResponse({'error': 'Arquivo não encontrado'}, status=404)


class FileUploadFormView(LoginRequiredMixin, View):
    """View para formulário de upload"""
    
    template_name = 'core/upload_form.html'
    
    def get(self, request):
        """Exibir formulário de upload"""
        return render(request, self.template_name, {
            'title': 'Upload de Arquivos',
            'max_file_size': getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440),  # 2.5MB default
            'allowed_types': list(SecureFileUploader.ALLOWED_FILE_TYPES.keys())
        })
    
    def post(self, request):
        """Processar upload via formulário"""
        try:
            if 'file' not in request.FILES:
                messages.error(request, 'Nenhum arquivo selecionado.')
                return redirect('core:file-upload')
            
            uploaded_file = request.FILES['file']
            description = request.POST.get('description', '')
            file_type = request.POST.get('type', 'document')
            
            # Processar upload usando IntegratedFileUploadHandler
            result = process_file_upload(uploaded_file, request.user, file_type, description)
            
            if result['success']:
                messages.success(request, f'Arquivo "{uploaded_file.name}" enviado com sucesso!')
                return redirect('core:upload-list')
            else:
                messages.error(request, result.get('error', 'Erro no upload'))
                return redirect('core:file-upload')
                
        except Exception as e:
            logger.error(f"Erro no upload via formulário: {e}")
            messages.error(request, f'Erro no upload: {str(e)}')
            return redirect('core:file-upload')


class UploadListView(LoginRequiredMixin, ListView):
    """View para listar uploads do usuário"""
    
    model = UploadedFile
    template_name = 'core/upload_list.html'
    context_object_name = 'uploads'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar apenas uploads do usuário atual"""
        queryset = UploadedFile.objects.filter(uploaded_by=self.request.user)
        
        # Filtros
        search = self.request.GET.get('search')
        file_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(original_filename__icontains=search) |
                Q(description__icontains=search)
            )
        
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Meus Arquivos',
            'search': self.request.GET.get('search', ''),
            'current_type': self.request.GET.get('type', ''),
            'current_status': self.request.GET.get('status', ''),
            'file_types': UploadedFile.FILE_TYPE_CHOICES,
            'status_choices': UploadedFile.UPLOAD_STATUS_CHOICES,
            'total_uploads': self.get_queryset().count(),
            'total_size': sum(upload.file_size for upload in self.get_queryset())
        })
        return context


class UploadDetailView(LoginRequiredMixin, DetailView):
    """View para detalhes de um upload"""
    
    model = UploadedFile
    template_name = 'core/upload_detail.html'
    context_object_name = 'upload'
    
    def get_queryset(self):
        """Apenas uploads do usuário atual"""
        return UploadedFile.objects.filter(uploaded_by=self.request.user)


class UploadDeleteView(LoginRequiredMixin, DeleteView):
    """View para excluir upload"""
    
    model = UploadedFile
    success_url = reverse_lazy('core:upload-list')
    
    def get_queryset(self):
        """Apenas uploads do usuário atual"""
        return UploadedFile.objects.filter(uploaded_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Excluir arquivo físico também"""
        upload = self.get_object()
        
        try:
            # Deletar arquivo físico
            if default_storage.exists(upload.file_path):
                default_storage.delete(upload.file_path)
            
            # Deletar registro
            upload.delete()
            
            messages.success(request, f'Arquivo "{upload.original_filename}" excluído com sucesso!')
            
        except Exception as e:
            logger.error(f"Erro ao excluir arquivo {upload.id}: {e}")
            messages.error(request, 'Erro ao excluir arquivo. Tente novamente.')
        
        return redirect(self.success_url)


@login_required
def upload_download_view(request, upload_id):
    """View para download de arquivo"""
    try:
        upload = get_object_or_404(UploadedFile, id=upload_id, uploaded_by=request.user)
        
        if not default_storage.exists(upload.file_path):
            raise Http404("Arquivo não encontrado")
        
        # Atualizar estatísticas de download
        upload.download_count += 1
        upload.last_accessed = timezone.now()
        upload.save(update_fields=['download_count', 'last_accessed'])
        
        # Servir arquivo
        from django.http import FileResponse
        file_obj = default_storage.open(upload.file_path, 'rb')
        
        response = FileResponse(
            file_obj,
            as_attachment=True,
            filename=upload.original_filename
        )
        response['Content-Type'] = upload.mime_type
        response['Content-Length'] = upload.file_size
        
        return response
        
    except Exception as e:
        logger.error(f"Erro no download do arquivo {upload_id}: {e}")
        raise Http404("Erro ao baixar arquivo")


@login_required
@csrf_exempt
@ratelimit(key='user', rate='20/m', method='POST')  # ENHANCED: Rate limiting for uploads
def upload_api_view(request):
    """API para upload via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        description = request.POST.get('description', '')
        file_type = request.POST.get('type', 'document')
        
        # Processar upload
        result = process_file_upload(uploaded_file, request.user, file_type, description)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Erro na API de upload: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def upload_validate_api(request):
    """API para validar arquivo sem fazer upload"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'valid': False,
                'errors': ['Nenhum arquivo enviado']
            })
        
        uploaded_file = request.FILES['file']
        file_type = request.POST.get('type', 'document')
        
        # Validar usando o handler
        handler = IntegratedFileUploadHandler()
        errors = handler.validate_file(uploaded_file, file_type)
        
        return JsonResponse({
            'valid': len(errors) == 0,
            'errors': errors,
            'file_info': {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'type': uploaded_file.content_type
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na validação de arquivo: {e}")
        return JsonResponse({
            'valid': False,
            'errors': [str(e)]
        })


@login_required
def upload_stats_api(request):
    """API para estatísticas de upload do usuário"""
    try:
        uploads = UploadedFile.objects.filter(uploaded_by=request.user)
        
        stats = {
            'total_uploads': uploads.count(),
            'total_size': sum(upload.file_size for upload in uploads),
            'total_downloads': sum(upload.download_count for upload in uploads),
            'by_type': {},
            'by_status': {},
            'recent_uploads': []
        }
        
        # Estatísticas por tipo
        for file_type, label in UploadedFile.FILE_TYPE_CHOICES:
            count = uploads.filter(file_type=file_type).count()
            if count > 0:
                stats['by_type'][file_type] = {
                    'label': label,
                    'count': count
                }
        
        # Estatísticas por status
        for status, label in UploadedFile.UPLOAD_STATUS_CHOICES:
            count = uploads.filter(status=status).count()
            if count > 0:
                stats['by_status'][status] = {
                    'label': label,
                    'count': count
                }
        
        # Uploads recentes
        recent = uploads.order_by('-uploaded_at')[:5]
        for upload in recent:
            stats['recent_uploads'].append({
                'id': upload.id,
                'filename': upload.original_filename,
                'uploaded_at': upload.uploaded_at.isoformat(),
                'size': upload.file_size,
                'type': upload.get_file_type_display()
            })
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return JsonResponse({'error': str(e)}, status=500)


class UploadStatsView(LoginRequiredMixin, View):
    """View para página de estatísticas de upload"""
    
    def get(self, request):
        """Exibir página de estatísticas"""
        uploads = UploadedFile.objects.filter(uploaded_by=request.user)
        
        # Calcular estatísticas
        stats = {
            'total_files': uploads.count(),
            'total_size_formatted': self._format_file_size(sum(upload.file_size for upload in uploads)),
            'completed_files': uploads.filter(status='completed').count(),
            'processing_files': uploads.filter(status='processing').count(),
            'by_type': [],
            'by_status': []
        }
        
        # Estatísticas por tipo
        type_colors = {
            'document': '#3B82F6',  # blue
            'image': '#8B5CF6',     # purple  
            'audio': '#F59E0B',     # amber
            'video': '#EF4444',     # red
            'other': '#6B7280'      # gray
        }
        
        for file_type, label in UploadedFile.FILE_TYPE_CHOICES:
            count = uploads.filter(file_type=file_type).count()
            if count > 0:
                stats['by_type'].append({
                    'type_display': label,
                    'count': count,
                    'color': type_colors.get(file_type, '#6B7280')
                })
        
        # Estatísticas por status
        status_colors = {
            'pending': '#F59E0B',      # amber
            'processing': '#3B82F6',   # blue
            'completed': '#10B981',    # green
            'failed': '#EF4444',       # red
            'virus_detected': '#DC2626' # red-600
        }
        
        for status, label in UploadedFile.UPLOAD_STATUS_CHOICES:
            count = uploads.filter(status=status).count()
            if count > 0:
                stats['by_status'].append({
                    'status_display': label,
                    'count': count,
                    'color': status_colors.get(status, '#6B7280')
                })
        
        # Arquivos recentes
        recent_files = uploads.order_by('-uploaded_at')[:10]
        
        context = {
            'stats': stats,
            'recent_files': recent_files
        }
        
        return render(request, 'core/upload_stats.html', context)
    
    def _format_file_size(self, size_bytes):
        """Formatar tamanho do arquivo em formato legível"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"


@method_decorator([csrf_exempt, login_required], name='dispatch')
class BulkDeleteView(View):
    """
    View para exclusão em lote de arquivos
    """
    
    def post(self, request, *args, **kwargs):
        """Excluir múltiplos arquivos"""
        try:
            data = json.loads(request.body)
            file_ids = data.get('file_ids', [])
            
            if not file_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhum arquivo selecionado'
                }, status=400)
            
            # Validar que os IDs são números
            try:
                file_ids = [int(id) for id in file_ids]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'IDs de arquivo inválidos'
                }, status=400)
            
            # Buscar arquivos do usuário
            files = UploadedFile.objects.filter(
                id__in=file_ids,
                uploaded_by=request.user
            )
            
            deleted_count = 0
            errors = []
            
            for file in files:
                try:
                    # Excluir arquivo físico
                    if file.file and file.file.name:
                        file.file.delete(save=False)
                    
                    # Excluir registro do banco
                    file.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    errors.append(f"Erro ao excluir {file.original_filename}: {str(e)}")
            
            response_data = {
                'success': True,
                'deleted_count': deleted_count,
                'total_requested': len(file_ids)
            }
            
            if errors:
                response_data['errors'] = errors
                response_data['partial_success'] = True
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Erro na exclusão em lote: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }, status=500)


@method_decorator([csrf_exempt, login_required], name='dispatch')
class FileStatusUpdateView(View):
    """
    View para atualizar status de arquivos
    """
    
    def post(self, request, *args, **kwargs):
        """Atualizar status de um arquivo"""
        try:
            data = json.loads(request.body)
            file_id = data.get('file_id')
            new_status = data.get('status')
            
            if not file_id or not new_status:
                return JsonResponse({
                    'success': False,
                    'error': 'ID do arquivo e status são obrigatórios'
                }, status=400)
            
            # Validar status
            valid_statuses = [choice[0] for choice in UploadedFile.UPLOAD_STATUS_CHOICES]
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'error': f'Status inválido: {new_status}'
                }, status=400)
            
            # Buscar arquivo
            file = get_object_or_404(
                UploadedFile, 
                id=file_id, 
                uploaded_by=request.user
            )
            
            # Atualizar status
            file.status = new_status
            file.save(update_fields=['status'])
            
            return JsonResponse({
                'success': True,
                'file_id': file.id,
                'new_status': file.status,
                'status_display': file.get_status_display()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }, status=500)
