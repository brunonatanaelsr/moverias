"""
Views otimizadas para o módulo de atividades dos beneficiários.
Implementa dashboard centralizado e navegação focada na beneficiária.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Q, Avg, Max, Min
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import date, timedelta, datetime

from core.decorators import CreateConfirmationMixin, EditConfirmationMixin, DeleteConfirmationMixin

@login_required
def activities_dashboard(request):
    """
    Dashboard principal com visão geral das atividades do programa.
    """
    context = {
        'title': 'Dashboard de Atividades',
    }
    return render(request, 'activities/dashboard.html', context)

import json

from members.models import Beneficiary
from social.models import SocialAnamnesis
from .models import (
    BeneficiaryActivity,
    ActivitySession,
    ActivityAttendance,
    ActivityFeedback,
    ActivityNote
)
from .forms import (
    BeneficiaryActivityForm,
    ActivitySessionForm,
    ActivityAttendanceForm,
    ActivityFeedbackForm,
    ActivityNoteForm
)


@login_required
def beneficiary_activities_dashboard(request, beneficiary_id):
    """
    Dashboard unificado de atividades da beneficiária.
    Visão centralizada com métricas e informações relevantes.
    """
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    # Cache key para otimização
    cache_key = f'beneficiary_dashboard_{beneficiary_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        context = cached_data
    else:
        # Otimização: Uma única query com prefetch
        activities = BeneficiaryActivity.objects.filter(
            beneficiary=beneficiary
        ).select_related(
            'created_by', 'social_anamnesis'
        ).prefetch_related(
            'sessions__attendance',
            'feedback_entries',
            'notes'
        ).annotate(
            sessions_count=Count('sessions'),
            attended_count=Count(
                'sessions__attendance', 
                filter=Q(sessions__attendance__attended=True)
            ),
            feedback_count=Count('feedback_entries')
        ).order_by('-created_at')
        
        # Métricas agregadas
        total_activities = activities.count()
        active_activities = activities.filter(status='ACTIVE').count()
        completed_activities = activities.filter(status='COMPLETED').count()
        
        completion_rate = (
            (completed_activities / total_activities * 100) 
            if total_activities > 0 else 0
        )
        
        # Cálculo da taxa de presença geral
        overall_attendance = 0
        if activities.exists():
            attendance_rates = [
                activity.attendance_rate for activity in activities 
                if activity.attendance_rate > 0
            ]
            overall_attendance = (
                sum(attendance_rates) / len(attendance_rates) 
                if attendance_rates else 0
            )
        
        # Próximas sessões
        upcoming_sessions = ActivitySession.objects.filter(
            activity__beneficiary=beneficiary,
            session_date__gte=date.today(),
            status='SCHEDULED'
        ).select_related(
            'activity'
        ).order_by('session_date', 'start_time')[:5]
        
        # Sessões recentes
        recent_sessions = ActivitySession.objects.filter(
            activity__beneficiary=beneficiary,
            session_date__lt=date.today()
        ).select_related(
            'activity'
        ).prefetch_related(
            'attendance'
        ).order_by('-session_date')[:5]
        
        # Evolução social resumida
        social_evolution = get_social_evolution_summary(beneficiary)
        
        # Notas recentes
        recent_notes = ActivityNote.objects.filter(
            activity__beneficiary=beneficiary
        ).select_related(
            'activity', 'created_by'
        ).order_by('-created_at')[:5]
        
        # Métricas por tipo de atividade
        activity_types_metrics = activities.values('activity_type').annotate(
            count=Count('id'),
            avg_completion=Avg('completion_percentage'),
            avg_attendance=Avg('attendance_rate')
        ).order_by('-count')
        
        context = {
            'beneficiary': beneficiary,
            'activities': activities,
            'metrics': {
                'total_activities': total_activities,
                'active_activities': active_activities,
                'completed_activities': completed_activities,
                'completion_rate': completion_rate,
                'overall_attendance': overall_attendance,
                'average_impact_score': activities.aggregate(
                    avg_impact=Avg('impact_score')
                )['avg_impact'] or 0,
            },
            'upcoming_sessions': upcoming_sessions,
            'recent_sessions': recent_sessions,
            'social_evolution': social_evolution,
            'recent_notes': recent_notes,
            'activity_types_metrics': activity_types_metrics,
        }
        
        # Cache por 5 minutos
        cache.set(cache_key, context, 300)
    
    return render(request, 'activities/beneficiary_dashboard.html', context)


@login_required
def activities_list(request):
    """
    Lista todas as atividades com filtros.
    """
    activities = BeneficiaryActivity.objects.select_related(
        'beneficiary', 'created_by', 'social_anamnesis'
    ).prefetch_related(
        'sessions'
    ).annotate(
        sessions_count=Count('sessions')
    )
    
    # Filtros
    status_filter = request.GET.get('status')
    activity_type_filter = request.GET.get('activity_type')
    beneficiary_filter = request.GET.get('beneficiary')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        activities = activities.filter(status=status_filter)
    
    if activity_type_filter:
        activities = activities.filter(activity_type=activity_type_filter)
    
    if beneficiary_filter:
        activities = activities.filter(
            beneficiary__full_name__icontains=beneficiary_filter
        )
    
    if date_from:
        activities = activities.filter(start_date__gte=date_from)
    
    if date_to:
        activities = activities.filter(start_date__lte=date_to)
    
    # Paginação
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas para a página
    stats = {
        'total': activities.count(),
        'active': activities.filter(status='ACTIVE').count(),
        'completed': activities.filter(status='COMPLETED').count(),
        'planned': activities.filter(status='PLANNED').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_choices': BeneficiaryActivity.STATUS_CHOICES,
        'activity_type_choices': BeneficiaryActivity.ACTIVITY_TYPES,
        'filters': {
            'status': status_filter,
            'activity_type': activity_type_filter,
            'beneficiary': beneficiary_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'activities/activities_list.html', context)


class BeneficiaryActivityDetailView(LoginRequiredMixin, DetailView):
    """
    Detalhes de uma atividade específica.
    """
    model = BeneficiaryActivity
    template_name = 'activities/activity_detail.html'
    context_object_name = 'activity'
    
    def get_queryset(self):
        return BeneficiaryActivity.objects.select_related(
            'beneficiary', 'created_by', 'social_anamnesis'
        ).prefetch_related(
            'sessions__attendance',
            'feedback_entries',
            'notes__created_by'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = self.object
        
        # Estatísticas da atividade
        context['sessions_stats'] = {
            'total': activity.sessions.count(),
            'completed': activity.sessions.filter(status='COMPLETED').count(),
            'scheduled': activity.sessions.filter(status='SCHEDULED').count(),
            'cancelled': activity.sessions.filter(status='CANCELLED').count(),
        }
        
        # Próximas sessões
        context['upcoming_sessions'] = activity.sessions.filter(
            session_date__gte=date.today(),
            status='SCHEDULED'
        ).order_by('session_date', 'start_time')[:5]
        
        # Histórico de presença
        context['attendance_history'] = ActivityAttendance.objects.filter(
            session__activity=activity
        ).select_related(
            'session', 'recorded_by'
        ).order_by('-session__session_date')[:10]
        
        # Feedback
        context['feedback'] = activity.feedback_entries.first()
        
        # Notas recentes
        context['recent_notes'] = activity.notes.select_related(
            'created_by'
        ).order_by('-created_at')[:5]
        
        return context


class BeneficiaryActivityCreateView(CreateConfirmationMixin, LoginRequiredMixin, CreateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro deste novo atividade?"
    confirmation_entity = "atividade"  # Criação de nova atividade para beneficiária.
    model = BeneficiaryActivity
    form_class = BeneficiaryActivityForm
    template_name = 'activities/activity_form.html'
    
    # Configurações da confirmação
    confirmation_message = "Confirma o cadastro desta nova atividade?"
    confirmation_entity = "atividade"
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            f'Atividade "{form.instance.title}" criada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy(
            'activities:beneficiary_dashboard',
            kwargs={'beneficiary_id': self.object.beneficiary.id}
        )


class BeneficiaryActivityUpdateView(EditConfirmationMixin, LoginRequiredMixin, UpdateView):
    
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações neste atividade?"
    confirmation_entity = "atividade"  # Atualização de atividade existente.
    model = BeneficiaryActivity
    form_class = BeneficiaryActivityForm
    template_name = 'activities/activity_form.html'
    
    # Configurações da confirmação
    confirmation_message = "Confirma as alterações nesta atividade?"
    confirmation_entity = "atividade"
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Atividade "{form.instance.title}" atualizada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy(
            'activities:activity_detail',
            kwargs={'pk': self.object.pk}
        )


@login_required
def activity_session_create(request, activity_id):
    """
    Criação de sessão para uma atividade.
    """
    activity = get_object_or_404(BeneficiaryActivity, id=activity_id)
    
    if request.method == 'POST':
        form = ActivitySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.activity = activity
            session.save()
            
            # Criar registro de presença
            ActivityAttendance.objects.create(
                session=session,
                recorded_by=request.user
            )
            
            messages.success(
                request,
                f'Sessão "{session.title}" criada com sucesso!'
            )
            
            return redirect('activities:activity_detail', pk=activity.pk)
    else:
        form = ActivitySessionForm()
    
    context = {
        'form': form,
        'activity': activity,
        'title': f'Nova Sessão - {activity.title}'
    }
    
    return render(request, 'activities/session_form.html', context)


@login_required
def attendance_record(request, session_id):
    """
    Registro de presença para uma sessão.
    """
    session = get_object_or_404(ActivitySession, id=session_id)
    
    try:
        attendance = session.attendance.get()
    except ActivityAttendance.DoesNotExist:
        attendance = ActivityAttendance.objects.create(
            session=session,
            recorded_by=request.user
        )
    
    if request.method == 'POST':
        form = ActivityAttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            
            # Atualizar progresso da atividade
            session.activity.calculate_impact_score()
            
            messages.success(
                request,
                'Presença registrada com sucesso!'
            )
            
            return redirect('activities:activity_detail', pk=session.activity.pk)
    else:
        form = ActivityAttendanceForm(instance=attendance)
    
    context = {
        'form': form,
        'session': session,
        'attendance': attendance,
        'title': f'Presença - {session.title}'
    }
    
    return render(request, 'activities/attendance_form.html', context)


@login_required
def activity_feedback(request, activity_id):
    """
    Feedback sobre uma atividade.
    """
    activity = get_object_or_404(BeneficiaryActivity, id=activity_id)
    
    try:
        feedback = activity.feedback_entries.get()
    except ActivityFeedback.DoesNotExist:
        feedback = None
    
    if request.method == 'POST':
        form = ActivityFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.activity = activity
            feedback.save()
            
            # Atualizar score de impacto
            activity.calculate_impact_score()
            
            messages.success(
                request,
                'Feedback registrado com sucesso!'
            )
            
            return redirect('activities:activity_detail', pk=activity.pk)
    else:
        form = ActivityFeedbackForm(instance=feedback)
    
    context = {
        'form': form,
        'activity': activity,
        'feedback': feedback,
        'title': f'Feedback - {activity.title}'
    }
    
    return render(request, 'activities/feedback_form.html', context)


@login_required
def activity_note_create(request, activity_id):
    """
    Criação de nota para uma atividade.
    """
    activity = get_object_or_404(BeneficiaryActivity, id=activity_id)
    
    if request.method == 'POST':
        form = ActivityNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.activity = activity
            note.created_by = request.user
            note.save()
            
            messages.success(
                request,
                'Nota adicionada com sucesso!'
            )
            
            return redirect('activities:activity_detail', pk=activity.pk)
    else:
        form = ActivityNoteForm()
    
    context = {
        'form': form,
        'activity': activity,
        'title': f'Nova Nota - {activity.title}'
    }
    
    return render(request, 'activities/note_form.html', context)


# API Views para dados dinâmicos
@login_required
def beneficiary_activities_api(request, beneficiary_id):
    """
    API para atividades de uma beneficiária.
    """
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    # Cache por 5 minutos
    cache_key = f'beneficiary_activities_api_{beneficiary_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data, safe=False)
    
    activities = BeneficiaryActivity.objects.filter(
        beneficiary=beneficiary
    ).select_related('created_by').values(
        'id', 'title', 'activity_type', 'status', 'start_date', 'end_date',
        'completion_percentage', 'impact_score', 'facilitator',
        'created_by__username'
    ).order_by('-created_at')
    
    data = []
    for activity in activities:
        activity_obj = BeneficiaryActivity.objects.get(id=activity['id'])
        data.append({
            **activity,
            'attendance_rate': activity_obj.attendance_rate,
            'total_sessions': activity_obj.total_sessions,
            'completed_sessions': activity_obj.completed_sessions,
            'is_overdue': activity_obj.is_overdue,
            'days_remaining': activity_obj.days_remaining,
        })
    
    cache.set(cache_key, data, 300)  # 5 minutos
    
    return JsonResponse(data, safe=False)


@login_required
def activities_metrics_api(request):
    """
    API para métricas gerais das atividades.
    """
    # Métricas gerais
    total_activities = BeneficiaryActivity.objects.count()
    active_activities = BeneficiaryActivity.objects.filter(status='ACTIVE').count()
    completed_activities = BeneficiaryActivity.objects.filter(status='COMPLETED').count()
    
    # Métricas por tipo
    activities_by_type = BeneficiaryActivity.objects.values(
        'activity_type'
    ).annotate(
        count=Count('id'),
        avg_completion=Avg('completion_percentage'),
        avg_impact=Avg('impact_score')
    ).order_by('-count')
    
    # Métricas mensais
    monthly_data = BeneficiaryActivity.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        completed=Count('id', filter=Q(status='COMPLETED'))
    ).order_by('month')
    
    # Taxa de presença geral
    all_activities = BeneficiaryActivity.objects.all()
    attendance_rates = [
        activity.attendance_rate for activity in all_activities
        if activity.attendance_rate > 0
    ]
    overall_attendance = (
        sum(attendance_rates) / len(attendance_rates)
        if attendance_rates else 0
    )
    
    data = {
        'total_activities': total_activities,
        'active_activities': active_activities,
        'completed_activities': completed_activities,
        'completion_rate': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
        'overall_attendance': overall_attendance,
        'activities_by_type': list(activities_by_type),
        'monthly_data': [
            {
                'month': item['month'].strftime('%Y-%m'),
                'count': item['count'],
                'completed': item['completed']
            }
            for item in monthly_data
        ]
    }
    
    return JsonResponse(data)


# Função auxiliar para evolução social
def get_social_evolution_summary(beneficiary):
    """
    Resumo da evolução social da beneficiária.
    """
    try:
        anamnesis = beneficiary.social_anamneses.latest('created_at')
        evolutions = anamnesis.evolutions.order_by('-evolution_date')[:3]
        
        return {
            'latest_anamnesis': anamnesis,
            'recent_evolutions': evolutions,
            'total_evolutions': anamnesis.evolutions.count(),
            'activities_linked': BeneficiaryActivity.objects.filter(
                beneficiary=beneficiary,
                social_anamnesis=anamnesis
            ).count()
        }
    except:
        return None


# View para relatórios
@login_required
def activities_report(request):
    """
    Relatório de atividades.
    """
    # Filtros de data
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    activities = BeneficiaryActivity.objects.select_related(
        'beneficiary', 'created_by'
    ).prefetch_related('sessions__attendance')
    
    if date_from:
        activities = activities.filter(start_date__gte=date_from)
    if date_to:
        activities = activities.filter(start_date__lte=date_to)
    
    # Estatísticas do relatório
    report_stats = {
        'total_activities': activities.count(),
        'total_beneficiaries': activities.values('beneficiary').distinct().count(),
        'average_attendance': activities.aggregate(
            avg_attendance=Avg('attendance_rate')
        )['avg_attendance'] or 0,
        'average_completion': activities.aggregate(
            avg_completion=Avg('completion_percentage')
        )['avg_completion'] or 0,
        'average_impact': activities.aggregate(
            avg_impact=Avg('impact_score')
        )['avg_impact'] or 0,
    }
    
    # Dados por beneficiária
    beneficiary_data = {}
    for activity in activities:
        beneficiary = activity.beneficiary
        if beneficiary not in beneficiary_data:
            beneficiary_data[beneficiary] = {
                'activities': [],
                'total_sessions': 0,
                'attended_sessions': 0,
                'average_impact': 0,
            }
        
        beneficiary_data[beneficiary]['activities'].append(activity)
        beneficiary_data[beneficiary]['total_sessions'] += activity.total_sessions
        beneficiary_data[beneficiary]['attended_sessions'] += activity.completed_sessions
        beneficiary_data[beneficiary]['average_impact'] += activity.impact_score
    
    # Calcular médias
    for beneficiary, data in beneficiary_data.items():
        activity_count = len(data['activities'])
        if activity_count > 0:
            data['average_impact'] = data['average_impact'] / activity_count
        
        data['attendance_rate'] = (
            (data['attended_sessions'] / data['total_sessions'] * 100)
            if data['total_sessions'] > 0 else 0
        )
    
    context = {
        'report_stats': report_stats,
        'beneficiary_data': beneficiary_data,
        'date_from': date_from,
        'date_to': date_to,
        'activities': activities,
    }
    
    return render(request, 'activities/report.html', context)
