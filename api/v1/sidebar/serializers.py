"""
Sérialiseurs optimisés pour la Sidebar et l'Interface de Co-Gouvernance
Structure JSON exacte du cahier des charges
"""
from rest_framework import serializers
from apps.experts.models import Expert
from apps.governance.models import WG, CTM, Tache
from apps.norms.models import Norme
from apps.meetings.models import Reunion
from apps.payments.models import Cotisation
from django.contrib.auth.models import User


# =========================================================================
# WORKING GROUPS & NORMES PARALLÈLES
# =========================================================================
class WorkingGroupSidebarSerializer(serializers.ModelSerializer):
    """Groupe de travail avec normes parallèles imbriquées"""
    id = serializers.CharField(source='id', read_only=True)
    code = serializers.SerializerMethodField()
    title = serializers.CharField(source='name')
    tag = serializers.SerializerMethodField()
    ctmId = serializers.PrimaryKeyRelatedField(source='ctm.id', read_only=True, allow_null=True)
    expert_count = serializers.IntegerField(read_only=True)
    parallel_norms = serializers.SerializerMethodField()
    tasks_progress = serializers.SerializerMethodField()

    class Meta:
        model = WG
        fields = ['id', 'code', 'title', 'tag', 'ctmId', 'expert_count', 'parallel_norms', 'tasks_progress']

    def get_code(self, obj):
        """Générer le code WG.X.Y"""
        if obj.ctm and obj.number:
            return f"WG {obj.ctm.number}.{obj.number}"
        return ""

    def get_tag(self, obj):
        """Tag du statut du WG"""
        return 'Actif'

    def get_parallel_norms(self, obj):
        """Normes parallèles associées"""
        return []

    def get_tasks_progress(self, obj):
        """Progression des tâches"""
        tasks = obj.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status='COMPLETED').count()
        avg_progress = int((completed / total) * 100) if total > 0 else 0

        return {
            'total': total,
            'completed': completed,
            'average_progress': avg_progress
        }


# =========================================================================
# EXPERTS & ACCRÉDITATIONS
# =========================================================================
class ExpertSidebarSerializer(serializers.ModelSerializer):
    """Expert avec infos d'accréditation"""
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.CharField(source='telephone', allow_null=True)
    province = serializers.CharField(source='province_origin', allow_null=True)
    structure = serializers.SerializerMethodField()
    ctm = serializers.SerializerMethodField()
    wg = serializers.SerializerMethodField()
    role = serializers.CharField(source='role_id')
    isApproved = serializers.SerializerMethodField()
    avatarColor = serializers.SerializerMethodField()

    class Meta:
        model = Expert
        fields = ['id', 'name', 'email', 'phone', 'province', 'structure',
                  'ctm', 'wg', 'role', 'isApproved', 'avatarColor']

    def get_id(self, obj):
        return f"exp-{obj.id}"

    def get_name(self, obj):
        return obj.user.get_full_name()

    def get_email(self, obj):
        return obj.user.email

    def get_structure(self, obj):
        return obj.structure.name if obj.structure else ""

    def get_ctm(self, obj):
        return obj.ctm.name if obj.ctm else ""

    def get_wg(self, obj):
        """Working group principal"""
        affectation = obj.governance_affectations.first()
        return affectation.working_group.title if affectation else ""

    def get_isApproved(self, obj):
        return obj.status == 'ACTIVE'

    def get_avatarColor(self, obj):
        """Couleur d'avatar déterministe basée sur l'ID"""
        colors = [
            "#3b82f6",  # blue
            "#ec4899",  # pink
            "#8b5cf6",  # purple
            "#06b6d4",  # cyan
            "#10b981",  # emerald
            "#f59e0b",  # amber
            "#ef4444",  # red
            "#6366f1",  # indigo
        ]
        return colors[obj.id % len(colors)]


# =========================================================================
# TÂCHES & PROGRESS
# =========================================================================
class TaskSerializer(serializers.ModelSerializer):
    """Tâche avec statut et progression"""
    id = serializers.CharField(read_only=True)
    normCode = serializers.SerializerMethodField()
    normTitle = serializers.SerializerMethodField()
    title = serializers.CharField(source='titre')
    status = serializers.SerializerMethodField()
    progress = serializers.IntegerField()

    class Meta:
        model = Tache
        fields = ['id', 'normCode', 'normTitle', 'title', 'status', 'progress']

    def get_normCode(self, obj):
        return obj.norme.code if obj.norme else ""

    def get_normTitle(self, obj):
        return obj.norme.title if obj.norme else ""

    def get_status(self, obj):
        """Mapper le statut interne au statut frontend"""
        status_map = {
            'PLANNED': 'Planned',
            'IN_PROGRESS': 'In Progress',
            'COMPLETED': 'Completed'
        }
        return status_map.get(obj.status, 'Planned')


# =========================================================================
# DOCUMENTS & NORMES
# =========================================================================
class DocumentSidebarSerializer(serializers.ModelSerializer):
    """Document/Norme pour la sidebar"""
    id = serializers.CharField(read_only=True)
    code = serializers.CharField()
    title = serializers.CharField()
    category = serializers.SerializerMethodField()
    updatedBy = serializers.SerializerMethodField()

    class Meta:
        model = Norme
        fields = ['id', 'code', 'title', 'category', 'updatedBy']

    def get_category(self, obj):
        """Catégorie de la norme"""
        category_map = {
            'QUALITE': 'Qualité',
            'SECURITE': 'Sécurité',
            'ETHIQUE': 'Éthique',
            'ENVIRONNEMENT': 'Environnement'
        }
        return category_map.get(obj.category, 'Qualité')

    def get_updatedBy(self, obj):
        """Dernier éditeur"""
        if obj.created_by:
            return obj.created_by.get_full_name()
        return "Système"


# =========================================================================
# RÉUNIONS
# =========================================================================
class MeetingSidebarSerializer(serializers.ModelSerializer):
    """Réunion pour la sidebar"""
    id = serializers.CharField(read_only=True)
    date = serializers.SerializerMethodField()
    title = serializers.CharField(source='sujet')
    status = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = ['id', 'date', 'title', 'status']

    def get_date(self, obj):
        """Format de date français"""
        if obj.date_reunion:
            return obj.date_reunion.strftime('%d %b %Y')
        return ""

    def get_status(self, obj):
        """Mapper le statut"""
        status_map = {
            'PLANNED': 'Planifié',
            'IN_PROGRESS': 'En cours',
            'COMPLETED': 'Terminé',
            'CANCELLED': 'Annulé'
        }
        return status_map.get(obj.status, 'Planifié')


# =========================================================================
# BUDGETS & COTISATIONS
# =========================================================================
class BudgetSidebarSerializer(serializers.ModelSerializer):
    """Budget/Cotisation pour la sidebar"""
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(source='description')
    amount = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Cotisation
        fields = ['id', 'title', 'amount', 'status']

    def get_amount(self, obj):
        """Formater le montant"""
        if obj.montant:
            return f"{obj.montant:,.0f} CDF"
        return "À définir"

    def get_status(self, obj):
        """Mapper le statut de paiement"""
        status_map = {
            'PAID': 'Payé',
            'PENDING': 'En attente',
            'OVERDUE': 'Retard',
            'PARTIAL': 'Partiellement payé',
            'CANCELLED': 'Annulé'
        }
        return status_map.get(obj.statut, 'En attente')


# =========================================================================
# HISTORIQUE & ÉDITEURS
# =========================================================================
class EditorHistorySerializer(serializers.Serializer):
    """Éditeur d'une norme avec comptage des éditions"""
    name = serializers.CharField()
    email = serializers.CharField()
    role = serializers.CharField()
    count = serializers.IntegerField()


# =========================================================================
# UTILISATEUR CONNECTÉ
# =========================================================================
class UserProfileSerializer(serializers.Serializer):
    """Profil utilisateur pour le contexte global"""
    id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.CharField()
    roleId = serializers.CharField()
    ctm = serializers.CharField()
    ctmId = serializers.IntegerField(allow_null=True)
    wg = serializers.CharField()
    wgCode = serializers.CharField()
    theme_preference = serializers.CharField()
