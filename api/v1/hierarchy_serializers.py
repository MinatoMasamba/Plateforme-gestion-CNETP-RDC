"""Serializers for CNETP hierarchy"""

from rest_framework import serializers
from apps.governance.models import (
    ExecutiveLevel, ComitePilotage, PilotageMembreship,
    TechnicalCell, CTCMembership, CTM, WG, OriginStructure
)
from .experts_serializers import ExpertBasicSerializer


class ExecutiveLevelSerializer(serializers.ModelSerializer):
    """Serialize Executive Level positions"""
    expert = ExpertBasicSerializer(read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    
    class Meta:
        model = ExecutiveLevel
        fields = ['id', 'position', 'position_display', 'expert', 'created_at', 'updated_at']


class PilotageMembershipSerializer(serializers.ModelSerializer):
    """Serialize Steering Committee membership"""
    expert = ExpertBasicSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = PilotageMembreship
        fields = ['id', 'expert', 'role', 'role_display', 'created_at']


class SteeringCommitteeSerializer(serializers.ModelSerializer):
    """Serialize Steering Committee"""
    president = ExpertBasicSerializer(read_only=True)
    vice_president = ExpertBasicSerializer(read_only=True)
    secretary = ExpertBasicSerializer(read_only=True)
    rapporteur = ExpertBasicSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = ComitePilotage
        fields = ['id', 'name', 'president', 'vice_president', 'secretary', 'rapporteur', 'members']
    
    def get_members(self, obj):
        memberships = obj.pilotagemembreship_set.all()
        return PilotageMembershipSerializer(memberships, many=True).data


class CTCMembershipSerializer(serializers.ModelSerializer):
    """Serialize Technical Cell membership"""
    expert = ExpertBasicSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CTCMembership
        fields = ['id', 'expert', 'role', 'role_display', 'created_at']


class TechnicalCellSerializer(serializers.ModelSerializer):
    """Serialize Technical Cell"""
    coordinator = ExpertBasicSerializer(read_only=True)
    vice_coordinator = ExpertBasicSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = TechnicalCell
        fields = ['id', 'name', 'coordinator', 'vice_coordinator', 'members']
    
    def get_members(self, obj):
        memberships = obj.ctcmembership_set.all()
        return CTCMembershipSerializer(memberships, many=True).data


class OriginStructureSerializer(serializers.ModelSerializer):
    """Serialize Origin Structures (Girons)"""
    giron_display = serializers.CharField(source='get_giron_display', read_only=True)
    expert_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OriginStructure
        fields = ['id', 'name', 'code', 'giron', 'giron_display', 'description', 'expected_expert_count', 'expert_count']
    
    def get_expert_count(self, obj):
        return obj.experts.count()


class HierarchyOverviewSerializer(serializers.Serializer):
    """Overview of entire CNETP hierarchy"""
    total_experts = serializers.SerializerMethodField()
    total_ctm = serializers.SerializerMethodField()
    total_wg = serializers.SerializerMethodField()
    total_structures = serializers.SerializerMethodField()
    executive_count = serializers.SerializerMethodField()
    steering_committee_members = serializers.SerializerMethodField()
    technical_cell_members = serializers.SerializerMethodField()
    
    def get_total_experts(self, obj):
        from apps.experts.models import Expert
        return Expert.objects.count()
    
    def get_total_ctm(self, obj):
        return CTM.objects.count()
    
    def get_total_wg(self, obj):
        return WG.objects.count()
    
    def get_total_structures(self, obj):
        return OriginStructure.objects.count()
    
    def get_executive_count(self, obj):
        return ExecutiveLevel.objects.count()
    
    def get_steering_committee_members(self, obj):
        return PilotageMembreship.objects.count()
    
    def get_technical_cell_members(self, obj):
        return CTCMembership.objects.count()
