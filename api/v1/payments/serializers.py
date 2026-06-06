from rest_framework import serializers
from django.db import models
from apps.payments.models import Cotisation, Paiement, JetonPresence
from ..experts.serializers import ExpertBasicSerializer, StructureSerializer


class CotisationBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les cotisations"""
    structure_name = serializers.CharField(source='structure.name', read_only=True)
    montant_paye = serializers.SerializerMethodField()
    reste_payer = serializers.SerializerMethodField()

    class Meta:
        model = Cotisation
        fields = [
            'id', 'structure', 'structure_name', 'annee', 'montant',
            'status', 'due_date', 'montant_paye', 'reste_payer', 'created_at'
        ]
        read_only_fields = ['id', 'structure_name', 'montant_paye', 'reste_payer', 'created_at']

    def get_montant_paye(self, obj):
        return obj.montant_paye

    def get_reste_payer(self, obj):
        return obj.reste_payer


class CotisationDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les cotisations"""
    structure = StructureSerializer(read_only=True)
    paiements = serializers.SerializerMethodField()
    montant_paye = serializers.SerializerMethodField()
    reste_payer = serializers.SerializerMethodField()

    class Meta:
        model = Cotisation
        fields = [
            'id', 'structure', 'annee', 'montant', 'status',
            'due_date', 'paiements', 'montant_paye', 'reste_payer',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'montant_paye', 'reste_payer', 'created_at', 'updated_at'
        ]

    def get_paiements(self, obj):
        """Récupérer les paiements associés"""
        paiements = obj.paiements.all()
        return PaiementBasicSerializer(paiements, many=True).data

    def get_montant_paye(self, obj):
        """Calculer le montant total payé"""
        return obj.paiements.filter(status='CONFIRMED').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

    def get_reste_payer(self, obj):
        """Calculer le reste à payer"""
        montant_paye = obj.paiements.filter(status='CONFIRMED').aggregate(
            total=models.Sum('montant')
        )['total'] or 0
        return max(0, obj.montant - montant_paye)


class CotisationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour une cotisation"""
    class Meta:
        model = Cotisation
        fields = ['structure', 'annee', 'montant', 'due_date', 'notes']

    def validate(self, data):
        """Vérifier l'unicité structure + annee"""
        if Cotisation.objects.filter(
            structure=data['structure'],
            annee=data['annee']
        ).exists():
            raise serializers.ValidationError(
                "Une cotisation existe déjà pour cette structure et année."
            )
        return data


class PaiementBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les paiements"""
    class Meta:
        model = Paiement
        fields = [
            'id', 'cotisation', 'montant', 'status', 'numero_recu',
            'payment_date', 'created_at'
        ]
        read_only_fields = ['id', 'numero_recu', 'created_at']


class PaiementDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les paiements"""
    cotisation_info = serializers.SerializerMethodField()

    class Meta:
        model = Paiement
        fields = [
            'id', 'cotisation', 'cotisation_info', 'montant', 'status',
            'methode_paiement', 'numero_recu', 'numero_transaction',
            'proof_file', 'payment_date', 'confirmed_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'numero_recu', 'confirmed_at', 'created_at', 'updated_at'
        ]

    def get_cotisation_info(self, obj):
        """Récupérer les infos de cotisation"""
        return {
            'id': obj.cotisation.id,
            'structure': obj.cotisation.structure.name,
            'annee': obj.cotisation.annee,
            'montant_total': str(obj.cotisation.montant)
        }


class PaiementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un paiement"""
    class Meta:
        model = Paiement
        fields = [
            'cotisation', 'montant', 'methode_paiement',
            'numero_transaction', 'proof_file', 'payment_date'
        ]

    def validate_montant(self, value):
        """Vérifier que le montant ne dépasse pas le montant dû"""
        cotisation = self.initial_data.get('cotisation')
        if cotisation:
            try:
                cot = Cotisation.objects.get(id=cotisation)
                if value > cot.montant:
                    raise serializers.ValidationError(
                        f"Le montant ne peut pas dépasser {cot.montant}"
                    )
            except Cotisation.DoesNotExist:
                pass
        return value


class JetonPresenceBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les jetons de présence"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)

    class Meta:
        model = JetonPresence
        fields = [
            'id', 'expert', 'expert_name', 'reunion', 'montant',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'expert_name', 'created_at']


class JetonPresenceDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les jetons de présence"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    reunion_info = serializers.SerializerMethodField()

    class Meta:
        model = JetonPresence
        fields = [
            'id', 'expert', 'expert_name', 'reunion', 'reunion_info',
            'montant', 'status', 'payment_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'expert_name', 'created_at', 'updated_at'
        ]

    def get_reunion_info(self, obj):
        """Récupérer les infos de réunion"""
        return {
            'id': obj.reunion.id,
            'titre': obj.reunion.titre,
            'date': obj.reunion.date,
            'type': obj.reunion.type
        }


class JetonPresenceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un jeton de présence"""
    class Meta:
        model = JetonPresence
        fields = ['expert', 'reunion', 'montant']

    def validate(self, data):
        """Vérifier l'unicité expert + reunion"""
        if JetonPresence.objects.filter(
            expert=data['expert'],
            reunion=data['reunion']
        ).exists():
            raise serializers.ValidationError(
                "Un jeton existe déjà pour cet expert et cette réunion."
            )
        return data


class PaymentDashboardSerializer(serializers.Serializer):
    """Tableau de bord des paiements"""
    total_cotisations = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paye = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_en_attente = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage_paye = serializers.DecimalField(max_digits=5, decimal_places=2)
    nombre_structures = serializers.IntegerField()
    structures_payees = serializers.IntegerField()
    structures_en_retard = serializers.IntegerField()


class JetonSummarySerializer(serializers.Serializer):
    """Résumé des jetons d'un expert"""
    expert_id = serializers.IntegerField()
    expert_name = serializers.CharField()
    total_jetons = serializers.IntegerField()
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    montant_paye = serializers.DecimalField(max_digits=12, decimal_places=2)
    montant_en_attente = serializers.DecimalField(max_digits=12, decimal_places=2)


class PaymentStatsSerializer(serializers.Serializer):
    """Statistiques globales des paiements"""
    total_cotisations = serializers.DecimalField(max_digits=12, decimal_places=2)
    cotisations_payees = serializers.IntegerField()
    cotisations_partielles = serializers.IntegerField()
    cotisations_non_payees = serializers.IntegerField()
    taux_recouvrement = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_jetons_distribues = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_jetons_payes = serializers.DecimalField(max_digits=12, decimal_places=2)
