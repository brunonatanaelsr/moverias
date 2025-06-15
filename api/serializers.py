from rest_framework import serializers
from members.models import Beneficiary, Consent
from social.models import SocialAnamnesis
from projects.models import ProjectEnrollment
from evolution.models import EvolutionRecord
from coaching.models import ActionPlan, WheelOfLife


class ConsentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Consent
        fields = ['url', 'lgpd_agreement', 'image_use_agreement', 'signed_at', 'signed_ip', 'pdf']
        depth = 1


class BeneficiarySerializer(serializers.HyperlinkedModelSerializer):
    consents = ConsentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'url', 'id', 'full_name', 'dob', 'nis', 'phone_1', 'phone_2',
            'address', 'neighbourhood', 'reference', 'created_at', 'consents'
        ]
        depth = 1


class SocialAnamnesisSerializer(serializers.HyperlinkedModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)
    technician_name = serializers.CharField(source='signed_by_technician.get_full_name', read_only=True)
    
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
