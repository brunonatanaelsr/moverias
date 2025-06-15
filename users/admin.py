from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, UserProfile, UserActivity, SystemRole


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'last_login', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'full_name', 'username']
    ordering = ['full_name']
    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('email', 'username', 'full_name', 'phone')
        }),
        ('Função e Departamento', {
            'fields': ('role', 'department')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Informações Básicas', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'birth_date', 'emergency_contact']
    search_fields = ['user__full_name', 'user__email', 'emergency_contact']
    readonly_fields = ['user']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'description_short', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__full_name', 'user__email', 'description']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'timestamp']
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descrição'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemRole)
class SystemRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_short', 'permission_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descrição'
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Nº Permissões'
