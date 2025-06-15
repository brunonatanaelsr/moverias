"""
Advanced dashboard utilities for Move Marias
"""
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.cache import cache
import json

class DashboardMetrics:
    """Advanced metrics calculation for dashboard"""
    
    def __init__(self, user=None, cache_timeout=1800):
        self.user = user
        self.cache_timeout = cache_timeout
        self.cache_prefix = f"dashboard_{user.id if user else 'global'}"
    
    def get_beneficiaries_overview(self):
        """Get comprehensive beneficiaries overview"""
        cache_key = f"{self.cache_prefix}_beneficiaries_overview"
        data = cache.get(cache_key)
        
        if data is None:
            from members.models import Beneficiary
            from projects.models import ProjectEnrollment
            from social.models import SocialAssistance
            
            total = Beneficiary.objects.count()
            active_in_projects = Beneficiary.objects.filter(
                project_enrollments__status='ATIVO'
            ).distinct().count()
            
            receiving_assistance = Beneficiary.objects.filter(
                social_assistances__status='ATIVO'
            ).distinct().count()
            
            # Age distribution
            age_groups = self._calculate_age_distribution()
            
            # Monthly registrations
            monthly_registrations = self._get_monthly_registrations()
            
            data = {
                'total': total,
                'active_in_projects': active_in_projects,
                'receiving_assistance': receiving_assistance,
                'participation_rate': (active_in_projects / total * 100) if total > 0 else 0,
                'assistance_rate': (receiving_assistance / total * 100) if total > 0 else 0,
                'age_groups': age_groups,
                'monthly_registrations': monthly_registrations
            }
            
            cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_projects_analytics(self):
        """Get projects analytics"""
        cache_key = f"{self.cache_prefix}_projects_analytics"
        data = cache.get(cache_key)
        
        if data is None:
            from projects.models import ProjectEnrollment
            
            # Projects by status
            status_distribution = ProjectEnrollment.objects.values('status').annotate(
                count=Count('id')
            )
            
            # Projects by shift
            shift_distribution = ProjectEnrollment.objects.values('shift').annotate(
                count=Count('id')
            )
            
            # Most popular projects
            popular_projects = ProjectEnrollment.objects.values('project_name').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Weekly enrollment trends
            weekly_trends = self._get_weekly_enrollment_trends()
            
            data = {
                'status_distribution': list(status_distribution),
                'shift_distribution': list(shift_distribution),
                'popular_projects': list(popular_projects),
                'weekly_trends': weekly_trends,
                'total_enrollments': ProjectEnrollment.objects.count(),
                'active_enrollments': ProjectEnrollment.objects.filter(
                    status='ATIVO'
                ).count()
            }
            
            cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_workshops_analytics(self):
        """Get workshops analytics"""
        cache_key = f"{self.cache_prefix}_workshops_analytics"
        data = cache.get(cache_key)
        
        if data is None:
            from workshops.models import Workshop, WorkshopEnrollment
            
            # Workshops by status
            status_distribution = Workshop.objects.values('status').annotate(
                count=Count('id')
            )
            
            # Average attendance rate
            avg_attendance = WorkshopEnrollment.objects.filter(
                attended=True
            ).count() / max(WorkshopEnrollment.objects.count(), 1) * 100
            
            # Upcoming workshops
            upcoming = Workshop.objects.filter(
                date__gte=timezone.now().date(),
                status='AGENDADO'
            ).count()
            
            # Monthly workshop trends
            monthly_trends = Workshop.objects.filter(
                date__gte=timezone.now().date() - timedelta(days=365)
            ).extra(
                select={'month': "strftime('%%Y-%%m', date)"}
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            data = {
                'status_distribution': list(status_distribution),
                'avg_attendance_rate': round(avg_attendance, 2),
                'upcoming_workshops': upcoming,
                'monthly_trends': list(monthly_trends),
                'total_workshops': Workshop.objects.count()
            }
            
            cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_social_assistance_analytics(self):
        """Get social assistance analytics"""
        cache_key = f"{self.cache_prefix}_social_analytics"
        data = cache.get(cache_key)
        
        if data is None:
            from social.models import SocialAssistance
            
            # Assistance by type
            type_distribution = SocialAssistance.objects.values('assistance_type').annotate(
                count=Count('id')
            )
            
            # Monthly assistance trends
            monthly_trends = SocialAssistance.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=365)
            ).extra(
                select={'month': "strftime('%%Y-%%m', created_at)"}
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            # Active assistance count
            active_assistance = SocialAssistance.objects.filter(
                status='ATIVO'
            ).count()
            
            data = {
                'type_distribution': list(type_distribution),
                'monthly_trends': list(monthly_trends),
                'active_assistance': active_assistance,
                'total_assistance': SocialAssistance.objects.count()
            }
            
            cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def _calculate_age_distribution(self):
        """Calculate age distribution of beneficiaries"""
        from members.models import Beneficiary
        from django.db.models import Case, When, IntegerField
        
        today = timezone.now().date()
        
        age_groups = Beneficiary.objects.extra(
            select={
                'age': f"(julianday('now') - julianday(dob)) / 365.25"
            }
        ).aggregate(
            children=Count(Case(When(dob__gt=today - timedelta(days=18*365), then=1))),
            youth=Count(Case(When(
                dob__lte=today - timedelta(days=18*365),
                dob__gt=today - timedelta(days=30*365),
                then=1
            ))),
            adults=Count(Case(When(
                dob__lte=today - timedelta(days=30*365),
                dob__gt=today - timedelta(days=60*365),
                then=1
            ))),
            seniors=Count(Case(When(dob__lte=today - timedelta(days=60*365), then=1)))
        )
        
        return age_groups
    
    def _get_monthly_registrations(self):
        """Get monthly registration trends"""
        from members.models import Beneficiary
        
        monthly_data = Beneficiary.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        ).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        return list(monthly_data)
    
    def _get_weekly_enrollment_trends(self):
        """Get weekly enrollment trends"""
        from projects.models import ProjectEnrollment
        
        weekly_data = ProjectEnrollment.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=90)
        ).extra(
            select={'week': "strftime('%%Y-%%W', created_at)"}
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')
        
        return list(weekly_data)
    
    def get_performance_indicators(self):
        """Get key performance indicators"""
        cache_key = f"{self.cache_prefix}_kpis"
        data = cache.get(cache_key)
        
        if data is None:
            from members.models import Beneficiary
            from projects.models import ProjectEnrollment
            from workshops.models import WorkshopEnrollment
            
            # Calculate various KPIs
            total_beneficiaries = Beneficiary.objects.count()
            active_projects = ProjectEnrollment.objects.filter(
                status='ATIVO'
            ).count()
            
            # Workshop attendance rate
            total_enrollments = WorkshopEnrollment.objects.count()
            attended = WorkshopEnrollment.objects.filter(attended=True).count()
            attendance_rate = (attended / total_enrollments * 100) if total_enrollments > 0 else 0
            
            # Growth rates (compare to previous month)
            current_month = timezone.now().replace(day=1)
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_beneficiaries = Beneficiary.objects.filter(
                created_at__gte=current_month
            ).count()
            previous_beneficiaries = Beneficiary.objects.filter(
                created_at__gte=previous_month,
                created_at__lt=current_month
            ).count()
            
            beneficiary_growth = (
                (current_beneficiaries - previous_beneficiaries) / 
                max(previous_beneficiaries, 1) * 100
            )
            
            data = {
                'total_beneficiaries': total_beneficiaries,
                'active_projects': active_projects,
                'attendance_rate': round(attendance_rate, 2),
                'beneficiary_growth': round(beneficiary_growth, 2),
                'engagement_score': self._calculate_engagement_score()
            }
            
            cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def _calculate_engagement_score(self):
        """Calculate overall engagement score"""
        from members.models import Beneficiary
        from projects.models import ProjectEnrollment
        from workshops.models import WorkshopEnrollment
        from social.models import SocialAssistance
        
        total_beneficiaries = Beneficiary.objects.count()
        if total_beneficiaries == 0:
            return 0
        
        # Count beneficiaries with multiple interactions
        engaged_beneficiaries = Beneficiary.objects.filter(
            Q(project_enrollments__isnull=False) |
            Q(workshop_enrollments__isnull=False) |
            Q(social_assistances__isnull=False)
        ).distinct().count()
        
        return round((engaged_beneficiaries / total_beneficiaries * 100), 2)
    
    def generate_report_data(self, report_type='summary', date_range=30):
        """Generate comprehensive report data"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=date_range)
        
        reports = {
            'summary': self._generate_summary_report(start_date, end_date),
            'detailed': self._generate_detailed_report(start_date, end_date),
            'comparative': self._generate_comparative_report(start_date, end_date)
        }
        
        return reports.get(report_type, reports['summary'])
    
    def _generate_summary_report(self, start_date, end_date):
        """Generate summary report"""
        return {
            'period': f"{start_date} to {end_date}",
            'beneficiaries': self.get_beneficiaries_overview(),
            'projects': self.get_projects_analytics(),
            'workshops': self.get_workshops_analytics(),
            'social_assistance': self.get_social_assistance_analytics(),
            'kpis': self.get_performance_indicators()
        }
    
    def _generate_detailed_report(self, start_date, end_date):
        """Generate detailed report with breakdowns"""
        # Implementation for detailed reporting
        pass
    
    def _generate_comparative_report(self, start_date, end_date):
        """Generate comparative report with historical data"""
        # Implementation for comparative reporting
        pass
