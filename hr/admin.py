from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Department, JobPosition, Employee, EmployeeDocument, PerformanceReview, TrainingRecord


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'employee_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()
    employee_count.short_description = 'Funcionários Ativos'


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'employee_count', 'salary_range', 'is_active']
    list_filter = ['department', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'requirements']
    readonly_fields = ['created_at', 'updated_at']
    
    def employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()
    employee_count.short_description = 'Funcionários'
    
    def salary_range(self, obj):
        if obj.salary_range_min and obj.salary_range_max:
            return f"R$ {obj.salary_range_min:,.2f} - R$ {obj.salary_range_max:,.2f}"
        return "Não informado"
    salary_range.short_description = 'Faixa Salarial'


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


class PerformanceReviewInline(admin.TabularInline):
    model = PerformanceReview
    extra = 0
    readonly_fields = ['overall_rating', 'created_at']


class TrainingRecordInline(admin.TabularInline):
    model = TrainingRecord
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_number', 'full_name', 'job_position', 'department', 
        'employment_status', 'employment_type', 'hire_date', 'age_display'
    ]
    list_filter = [
        'employment_status', 'employment_type', 'department', 
        'job_position', 'gender', 'hire_date'
    ]
    search_fields = ['full_name', 'employee_number', 'cpf', 'user__email']
    readonly_fields = [
        'age_display', 'years_of_service_display', 'created_at', 
        'updated_at', 'created_by'
    ]
    
    fieldsets = (
        ('Informações do Sistema', {
            'fields': ('user', 'employee_number', 'created_by')
        }),
        ('Informações Pessoais', {
            'fields': (
                'full_name', 'cpf', 'rg', 'birth_date', 'gender', 
                'marital_status', 'age_display'
            )
        }),
        ('Contato', {
            'fields': (
                'phone', 'personal_email', 'address', 'city', 'state', 'zip_code'
            )
        }),
        ('Contato de Emergência', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_relationship', 
                'emergency_contact_phone'
            )
        }),
        ('Informações Profissionais', {
            'fields': (
                'job_position', 'department', 'direct_supervisor', 
                'employment_type', 'employment_status', 'hire_date', 
                'termination_date', 'salary', 'years_of_service_display'
            )
        }),
        ('Documentos e Benefícios', {
            'fields': (
                'pis_pasep', 'work_permit', 'has_health_insurance', 
                'has_dental_insurance', 'has_life_insurance'
            )
        }),
        ('Formação e Competências', {
            'fields': ('education_level', 'skills', 'certifications', 'languages')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [EmployeeDocumentInline, PerformanceReviewInline, TrainingRecordInline]
    
    def age_display(self, obj):
        return f"{obj.age} anos"
    age_display.short_description = 'Idade'
    
    def years_of_service_display(self, obj):
        years = obj.years_of_service
        return f"{years} ano{'s' if years != 1 else ''}"
    years_of_service_display.short_description = 'Tempo de Serviço'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'document_type', 'uploaded_by', 'uploaded_at', 'is_confidential']
    list_filter = ['document_type', 'is_confidential', 'uploaded_at']
    search_fields = ['title', 'employee__full_name', 'description']
    readonly_fields = ['uploaded_at', 'uploaded_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'review_type', 'review_date', 'overall_rating_display', 
        'reviewed_by', 'is_final'
    ]
    list_filter = ['review_type', 'is_final', 'review_date', 'reviewed_by']
    search_fields = ['employee__full_name']
    readonly_fields = ['overall_rating_display', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Avaliação', {
            'fields': (
                'employee', 'review_type', 'review_period_start', 
                'review_period_end', 'review_date', 'reviewed_by'
            )
        }),
        ('Critérios de Avaliação', {
            'fields': (
                'technical_skills', 'communication', 'teamwork', 
                'leadership', 'punctuality', 'productivity', 'overall_rating_display'
            )
        }),
        ('Comentários', {
            'fields': (
                'strengths', 'areas_for_improvement', 'goals_for_next_period', 
                'employee_comments'
            )
        }),
        ('Status', {
            'fields': ('is_final',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def overall_rating_display(self, obj):
        rating = obj.overall_rating
        if rating >= 4.5:
            color = 'green'
        elif rating >= 3.5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}/5.0</span>',
            color, rating
        )
    overall_rating_display.short_description = 'Nota Geral'


@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = [
        'training_name', 'employee', 'training_type', 'start_date', 
        'status', 'certificate_obtained', 'cost'
    ]
    list_filter = [
        'training_type', 'status', 'certificate_obtained', 
        'start_date', 'created_at'
    ]
    search_fields = ['training_name', 'employee__full_name', 'provider']
    readonly_fields = ['created_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
