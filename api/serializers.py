"""
Serializers da API REST para MoveMarias
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from members.models import Beneficiary, Consent
from workshops.models import Workshop, WorkshopEnrollment, WorkshopSession, SessionAttendance
from projects.models import (
    Project, ProjectEnrollment, ProjectSession, 
    ProjectAttendance, ProjectEvaluation, ProjectResource
)
from certificates.models import Certificate, CertificateRequest, CertificateTemplate
from notifications.models import Notification, NotificationPreference, NotificationTemplate, NotificationChannel
from social.models import SocialAnamnesis
from coaching.models import ActionPlan, WheelOfLife
from evolution.models import EvolutionRecord

User = get_user_model()


# =============================================================================
# USER & AUTH SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuários"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'date_joined']


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("As senhas não coincidem")
        return data


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer para reset de senha"""
    email = serializers.EmailField()


# =============================================================================
# MEMBERS SERIALIZERS
# =============================================================================

class ConsentSerializer(serializers.ModelSerializer):
    """Serializer para termos de consentimento"""
    
    class Meta:
        model = Consent
        fields = ['id', 'lgpd_agreement', 'image_use_agreement', 'signed_at', 'signed_ip', 'pdf']
        read_only_fields = ['id', 'signed_at']


class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer para beneficiárias"""
    age = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    consents = ConsentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'full_name', 'email', 'dob', 'age', 'nis', 'phone_1', 'phone_2',
            'address', 'neighbourhood', 'reference', 'status', 'is_active', 
            'created_at', 'consents'
        ]
        read_only_fields = ['id', 'created_at']


# =============================================================================
# WORKSHOPS SERIALIZERS
# =============================================================================

class WorkshopSerializer(serializers.ModelSerializer):
    """Serializer para oficinas"""
    total_participants = serializers.ReadOnlyField()
    total_sessions = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Workshop
        fields = [
            'id', 'name', 'description', 'workshop_type', 'facilitator', 'location',
            'start_date', 'end_date', 'status', 'max_participants', 'objectives',
            'materials_needed', 'total_participants', 'total_sessions', 'attendance_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkshopEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer para inscrições em oficinas"""
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)
    attendance_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkshopEnrollment
        fields = [
            'id', 'workshop', 'workshop_name', 'beneficiary', 'beneficiary_name',
            'enrollment_date', 'status', 'notes', 'attendance_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =============================================================================
# PROJECTS SERIALIZERS
# =============================================================================

class ProjectSerializer(serializers.ModelSerializer):
    """Serializer para projetos"""
    total_participants = serializers.ReadOnlyField()
    total_sessions = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'coordinator', 'location', 'start_date',
            'end_date', 'status', 'max_participants', 'objectives', 'target_audience',
            'total_participants', 'total_sessions', 'attendance_rate', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer para inscrições em projetos"""
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    weekday_display = serializers.ReadOnlyField()
    shift_display = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ProjectEnrollment
        fields = [
            'id', 'beneficiary', 'beneficiary_name', 'project', 'project_name',
            'weekday', 'weekday_display', 'shift', 'shift_display', 'start_time',
            'status', 'enrollment_code', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'enrollment_code', 'created_at']


# =============================================================================
# CERTIFICATES SERIALIZERS
# =============================================================================

class CertificateTemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates de certificado"""
    
    class Meta:
        model = CertificateTemplate
        fields = [
            'id', 'name', 'description', 'template_file', 'category',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer para certificados"""
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'member', 'member_name', 'workshop', 'workshop_name',
            'template', 'template_name', 'title', 'description', 'issued_date',
            'verification_code', 'pdf_file', 'created_at'
        ]
        read_only_fields = ['id', 'verification_code', 'created_at']


class CertificateRequestSerializer(serializers.ModelSerializer):
    """Serializer para solicitações de certificado"""
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    workshop_name = serializers.CharField(source='workshop.name', read_only=True)
    
    class Meta:
        model = CertificateRequest
        fields = [
            'id', 'member', 'member_name', 'workshop', 'workshop_name',
            'status', 'requested_at', 'approved_at', 'approved_by',
            'rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'requested_at', 'approved_at', 'created_at']


class CertificateStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de certificados"""
    total_certificates = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    monthly_stats = serializers.ListField()
    category_stats = serializers.ListField()


# =============================================================================
# NOTIFICATIONS SERIALIZERS
# =============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificações"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'category', 'priority',
            'action_url', 'is_read', 'read_at', 'expires_at', 'send_email',
            'send_sms', 'send_push', 'send_in_app', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'read_at', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer para preferências de notificação"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'email_enabled', 'sms_enabled', 'push_enabled',
            'in_app_enabled', 'categories', 'quiet_hours_start', 'quiet_hours_end',
            'timezone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates de notificação"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'category', 'subject', 'content', 'html_content',
            'available_variables', 'is_active', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Serializer para canais de notificação"""
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'description', 'configuration',
            'is_active', 'is_default', 'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer para envio de notificações em lote"""
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True
    )
    type = serializers.ChoiceField(
        choices=[
            ('welcome', 'Boas-vindas'),
            ('workshop_enrollment', 'Inscrição em Workshop'),
            ('workshop_reminder', 'Lembrete de Workshop'),
            ('certificate_ready', 'Certificado Pronto'),
            ('project_invitation', 'Convite para Projeto'),
            ('coaching_scheduled', 'Coaching Agendado'),
            ('system_update', 'Atualização do Sistema'),
            ('password_reset', 'Redefinição de Senha'),
            ('account_verification', 'Verificação de Conta'),
            ('general', 'Geral'),
        ],
        default='general'
    )
    priority = serializers.ChoiceField(
        choices=[
            (1, 'Baixa'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        default=2
    )
    send_email = serializers.BooleanField(default=False)
    send_push = serializers.BooleanField(default=False)
    send_in_app = serializers.BooleanField(default=True)


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de notificações"""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_notifications = serializers.IntegerField()
    read_rate = serializers.FloatField()
    category_stats = serializers.ListField()
    priority_stats = serializers.ListField()


# =============================================================================
# STATS SERIALIZERS
# =============================================================================

class ProjectStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de projetos"""
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    active_enrollments = serializers.IntegerField()
    project_status_stats = serializers.ListField()
    avg_attendance_rate = serializers.FloatField()
    avg_rating = serializers.FloatField()


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer para relatórios de presença"""
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    total_participants = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    overall_attendance_rate = serializers.FloatField()
    participants = serializers.ListField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas do dashboard"""
    total_beneficiaries = serializers.IntegerField()
    active_beneficiaries = serializers.IntegerField()
    total_workshops = serializers.IntegerField()
    active_workshops = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    pending_certificate_requests = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_activities = serializers.ListField()


# =============================================================================
# SOCIAL & COACHING SERIALIZERS
# =============================================================================

class SocialAnamnesisSerializer(serializers.ModelSerializer):
    """Serializer para anamneses sociais"""
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    technician_name = serializers.CharField(source='signed_by_technician.get_full_name', read_only=True)
    
    class Meta:
        model = SocialAnamnesis
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActionPlanSerializer(serializers.ModelSerializer):
    """Serializer para planos de ação"""
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    
    class Meta:
        model = ActionPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EvolutionRecordSerializer(serializers.ModelSerializer):
    """Serializer para registros de evolução"""
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    
    class Meta:
        model = EvolutionRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# =============================================================================
# FILE UPLOAD SERIALIZERS
# =============================================================================

class FileUploadSerializer(serializers.Serializer):
    """Serializer para upload de arquivos"""
    file = serializers.FileField()
    description = serializers.CharField(max_length=255, required=False)
    category = serializers.ChoiceField(
        choices=[
            ('document', 'Documento'),
            ('image', 'Imagem'),
            ('certificate', 'Certificado'),
            ('other', 'Outro')
        ],
        default='document'
    )
    
    def validate_file(self, value):
        """Validar arquivo enviado"""
        # Verificar tamanho (máximo 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Arquivo muito grande. Máximo 10MB.")
        
        # Verificar extensão
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif']
        file_extension = value.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Extensão não permitida. Permitidas: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    class Meta:
        model = SocialAnamnesis
        fields = [
            'url', 'id', 'beneficiary', 'beneficiary_name', 'date', 'family_composition',
            'income', 'vulnerabilities', 'substance_use', 'observations',
            'signed_by_technician', 'technician_name', 'signed_by_beneficiary', 'locked'
        ]
        depth = 1


class ProjectEnrollmentSerializer(serializers.HyperlinkedModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    weekday_display = serializers.CharField(read_only=True)
    shift_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = ProjectEnrollment
        fields = [
            'url', 'id', 'beneficiary', 'beneficiary_name', 'project_name',
            'weekday', 'weekday_display', 'shift', 'shift_display',
            'start_time', 'status', 'enrollment_code', 'created_at'
        ]
        depth = 1


class EvolutionRecordSerializer(serializers.HyperlinkedModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = EvolutionRecord
        fields = [
            'url', 'id', 'beneficiary', 'beneficiary_name', 'date', 'description',
            'author', 'author_name', 'signature_required', 'signed_by_beneficiary',
            'created_at', 'updated_at'
        ]
        depth = 1


class ActionPlanSerializer(serializers.HyperlinkedModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    
    class Meta:
        model = ActionPlan
        fields = [
            'url', 'id', 'beneficiary', 'beneficiary_name', 'main_goal',
            'priority_areas', 'actions', 'institute_support', 'semester_review',
            'created_at', 'updated_at'
        ]
        depth = 1


class WheelOfLifeSerializer(serializers.HyperlinkedModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    average_score = serializers.ReadOnlyField()
    areas_dict = serializers.ReadOnlyField()
    
    class Meta:
        model = WheelOfLife
        fields = [
            'url', 'id', 'beneficiary', 'beneficiary_name', 'date',
            'family', 'finance', 'health', 'career', 'relationships',
            'personal_growth', 'leisure', 'spirituality', 'education',
            'environment', 'contribution', 'emotions', 'average_score',
            'areas_dict', 'created_at'
        ]
        depth = 1
