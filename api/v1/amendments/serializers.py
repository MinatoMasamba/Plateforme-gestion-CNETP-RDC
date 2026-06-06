from rest_framework import serializers
from apps.amendments.models import Amendement, Vote, ResultatVote
from ..norms.serializers import NormeBasicSerializer, NormeVersionSerializer


class VoteSerializer(serializers.ModelSerializer):
    """Serializer pour les votes"""
    voter_name = serializers.CharField(source='voter.user.get_full_name', read_only=True)

    class Meta:
        model = Vote
        fields = [
            'id', 'amendement', 'voter', 'voter_name', 'vote',
            'justification', 'vote_date'
        ]
        read_only_fields = ['id', 'voter_name', 'vote_date']


class ResultatVoteSerializer(serializers.ModelSerializer):
    """Serializer pour les résultats de vote"""
    class Meta:
        model = ResultatVote
        fields = [
            'id', 'amendement', 'total_votes', 'votes_for', 'votes_against',
            'votes_abstain', 'quorum_reached', 'approval_percentage', 'vote_closed_at'
        ]
        read_only_fields = [
            'id', 'total_votes', 'votes_for', 'votes_against',
            'votes_abstain', 'approval_percentage'
        ]


class AmendementBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les amendements"""
    norme_reference = serializers.CharField(source='norme.reference_number', read_only=True)
    proposed_by_name = serializers.CharField(
        source='proposed_by.user.get_full_name',
        read_only=True
    )

    class Meta:
        model = Amendement
        fields = [
            'id', 'norme', 'norme_reference', 'title', 'status',
            'proposed_by', 'proposed_by_name', 'proposal_date'
        ]
        read_only_fields = ['id', 'norme_reference', 'proposed_by_name', 'proposal_date']


class AmendementDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les amendements"""
    norme = NormeBasicSerializer(read_only=True)
    version = NormeVersionSerializer(read_only=True)
    proposed_by_name = serializers.CharField(
        source='proposed_by.user.get_full_name',
        read_only=True
    )
    votes = VoteSerializer(many=True, read_only=True)
    resultat_vote = ResultatVoteSerializer(read_only=True)
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = Amendement
        fields = [
            'id', 'norme', 'version', 'proposed_by', 'proposed_by_name',
            'title', 'description', 'section', 'old_text', 'proposed_text',
            'justification', 'status', 'proposal_date', 'review_deadline',
            'votes', 'vote_count', 'resultat_vote', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'proposed_by_name', 'votes', 'resultat_vote',
            'created_at', 'updated_at'
        ]

    def get_vote_count(self, obj):
        return obj.votes.count()


class AmendementCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour un amendement"""
    class Meta:
        model = Amendement
        fields = [
            'norme', 'version', 'title', 'description',
            'section', 'old_text', 'proposed_text', 'justification'
        ]

    def create(self, validated_data):
        """Créer un amendement et initialiser le résultat de vote"""
        amendement = Amendement.objects.create(**validated_data)
        # Créer le ResultatVote associé
        ResultatVote.objects.create(amendement=amendement)
        return amendement


class AmendementStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le statut d'un amendement"""
    class Meta:
        model = Amendement
        fields = ['status']

    def validate_status(self, value):
        """Vérifier les transitions de statut valides"""
        instance = self.instance
        if instance:
            valid_transitions = {
                'PROPOSED': ['UNDER_REVIEW', 'WITHDRAWN'],
                'UNDER_REVIEW': ['ACCEPTED', 'REJECTED', 'WITHDRAWN'],
                'ACCEPTED': [],
                'REJECTED': [],
                'WITHDRAWN': [],
            }

            allowed_statuses = valid_transitions.get(instance.status, [])
            if value not in allowed_statuses:
                raise serializers.ValidationError(
                    f"Transition invalide de {instance.status} à {value}. "
                    f"Transitions valides: {', '.join(allowed_statuses)}"
                )
        return value


class VoteCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un vote"""
    class Meta:
        model = Vote
        fields = ['vote', 'justification']

    def create(self, validated_data):
        """Créer un vote et mettre à jour les résultats"""
        amendement = self.context.get('amendement')
        voter = self.context.get('voter')

        # Vérifier l'unicité du vote
        if Vote.objects.filter(amendement=amendement, voter=voter).exists():
            raise serializers.ValidationError(
                "Cet expert a déjà voté sur cet amendement."
            )

        vote = Vote.objects.create(
            amendement=amendement,
            voter=voter,
            **validated_data
        )

        # Recalculer les résultats
        if hasattr(amendement, 'resultat_vote'):
            amendement.resultat_vote.calculate_results()

        return vote


class AmendementSummarySerializer(serializers.Serializer):
    """Serializer pour un résumé des amendements et votes"""
    amendment_id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    votes_for = serializers.IntegerField()
    votes_against = serializers.IntegerField()
    votes_abstain = serializers.IntegerField()
    approval_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class AmendementStatsSerializer(serializers.Serializer):
    """Statistiques sur les amendements"""
    total_amendments = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_norme = serializers.DictField(child=serializers.IntegerField())
    average_approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
