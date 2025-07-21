from django.contrib import admin
from .models import (
    SocialAnamnesis, 
    FamilyMember, 
    VulnerabilityCategory, 
    IdentifiedVulnerability, 
    SocialAnamnesisEvolution
)


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1
    fields = ('name', 'relationship', 'age', 'gender', 'education_level', 'occupation', 'income')


class IdentifiedVulnerabilityInline(admin.TabularInline):
    model = IdentifiedVulnerability
    extra = 1
    fields = ('category', 'description', 'severity', 'status', 'priority_date')


class SocialAnamnesisEvolutionInline(admin.TabularInline):
    model = SocialAnamnesisEvolution
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('evolution_date', 'description', 'created_by', 'created_at')


@admin.register(SocialAnamnesis)
class SocialAnamnesisAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'created_at', 'family_income', 'status', 'signed_by_technician', 'locked')
    list_filter = ('created_at', 'status', 'locked', 'signed_by_beneficiary', 'signed_by_technician')
    search_fields = ('beneficiary__name', 'housing_situation', 'support_network')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [FamilyMemberInline, IdentifiedVulnerabilityInline, SocialAnamnesisEvolutionInline]
    
    fieldsets = (
        ('Beneficiária', {
            'fields': ('beneficiary', 'created_by', 'created_at', 'updated_at')
        }),
        ('Dados Familiares', {
            'fields': ('family_income', 'housing_situation')
        }),
        ('Rede de Apoio', {
            'fields': ('support_network',)
        }),
        ('Observações', {
            'fields': ('observations',)
        }),
        ('Status e Assinaturas', {
            'fields': ('status', 'signed_by_technician', 'signed_by_beneficiary', 'locked')
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'anamnesis', 'relationship', 'age', 'gender', 'occupation', 'income')
    list_filter = ('relationship', 'gender', 'education_level')
    search_fields = ('name', 'anamnesis__beneficiary__name', 'occupation')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('anamnesis', 'name', 'relationship', 'age', 'gender')
        }),
        ('Educação e Trabalho', {
            'fields': ('education_level', 'occupation', 'income')
        }),
        ('Saúde', {
            'fields': ('health_conditions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(VulnerabilityCategory)
class VulnerabilityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority_level', 'color', 'created_at')
    list_filter = ('priority_level', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'priority_level', 'color')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(IdentifiedVulnerability)
class IdentifiedVulnerabilityAdmin(admin.ModelAdmin):
    list_display = ('anamnesis', 'category', 'severity', 'status', 'priority_date', 'created_at')
    list_filter = ('category', 'severity', 'status', 'priority_date', 'created_at')
    search_fields = ('anamnesis__beneficiary__name', 'category__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('anamnesis', 'category', 'description')
        }),
        ('Classificação', {
            'fields': ('severity', 'status', 'priority_date')
        }),
        ('Intervenção', {
            'fields': ('intervention_needed',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SocialAnamnesisEvolution)
class SocialAnamnesisEvolutionAdmin(admin.ModelAdmin):
    list_display = ('anamnesis', 'evolution_date', 'created_by', 'created_at')
    list_filter = ('evolution_date', 'created_by', 'created_at')
    search_fields = ('anamnesis__beneficiary__name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('anamnesis', 'evolution_date', 'created_by', 'description')
        }),
        ('Mudanças Específicas', {
            'fields': ('changes_in_family', 'changes_in_vulnerabilities', 'changes_in_support_network')
        }),
        ('Anexos', {
            'fields': ('attachments',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
