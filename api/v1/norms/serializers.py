import difflib
from django.db import transaction
from rest_framework import serializers
from apps.norms.models import (
    Norme, NormeVersion, ChangementVersion, NormeVote, NormeComment,
    NormeContentBlock, parse_norme_structure, structured_content_summary,
    build_content_blocks
)
from ..experts.serializers import ExpertBasicSerializer


class ChangementVersionSerializer(serializers.ModelSerializer):
    """Serializer pour les changements de version"""
    class Meta:
        model = ChangementVersion
        fields = [
            'id', 'version', 'section', 'old_text', 'new_text',
            'change_type', 'change_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NormeVoteSerializer(serializers.ModelSerializer):
    """Serializer pour les votes liés directement à une norme."""
    voter_name = serializers.CharField(source='voter.user.get_full_name', read_only=True)
    voter_structure = serializers.CharField(source='voter.structure.acronym', read_only=True)

    class Meta:
        model = NormeVote
        fields = ['id', 'norme', 'voter', 'voter_name', 'voter_structure', 'vote', 'justification', 'vote_date']
        read_only_fields = ['id', 'norme', 'voter', 'voter_name', 'voter_structure', 'vote_date']


class NormeCommentSerializer(serializers.ModelSerializer):
    """Serializer pour les commentaires internes sur une norme."""
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = NormeComment
        fields = ['id', 'norme', 'author', 'author_name', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'norme', 'author', 'author_name', 'created_at', 'updated_at']


class NormeContentBlockSerializer(serializers.ModelSerializer):
    """Serializer pour les blocs éditoriaux structurés."""

    class Meta:
        model = NormeContentBlock
        fields = ['id', 'version', 'parent', 'kind', 'code', 'title', 'body', 'position', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']


class NormeVersionSerializer(serializers.ModelSerializer):
    """Serializer pour les versions de normes"""
    author_name = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source='version_author.email', read_only=True)
    changes = ChangementVersionSerializer(many=True, read_only=True)
    structured_content = serializers.SerializerMethodField()
    content_blocks = NormeContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = NormeVersion
        fields = [
            'id', 'norme', 'version_number', 'title', 'content',
            'document', 'summary', 'is_draft', 'version_author',
            'author_name', 'author_email', 'created_at', 'changes',
            'structured_content', 'content_blocks'
        ]
        read_only_fields = ['id', 'version_number', 'created_at', 'author_name', 'author_email']

    def get_author_name(self, obj):
        """Retourner le nom complet de l'auteur ou 'Inconnu' si vide."""
        if obj.version_author and obj.version_author.get_full_name():
            return obj.version_author.get_full_name()
        return "Inconnu"

    def get_structured_content(self, obj):
        return parse_norme_structure(obj.content)


class NormeBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les normes"""
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    votes_summary = serializers.SerializerMethodField()

    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description', 'status', 'standard_family', 'norm_type', 'target_count',
            'ctm', 'ctm_name', 'wg', 'wg_name', 'is_public', 'created_at', 'votes_summary'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at', 'votes_summary']

    def get_votes_summary(self, obj):
        votes = list(obj.votes.all())
        total = len(votes)
        for_votes = sum(1 for v in votes if v.vote == 'FOR')
        against_votes = sum(1 for v in votes if v.vote == 'AGAINST')
        abstain_votes = sum(1 for v in votes if v.vote == 'ABSTAIN')
        percent_for = round((for_votes / total) * 100, 2) if total else 0
        return {
            'total': total,
            'for': for_votes,
            'against': against_votes,
            'abstain': abstain_votes,
            'percent_for': percent_for,
            'passes_threshold': total > 0 and percent_for > 50,
        }


class NormeDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les normes"""
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    latest_version = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    structured_summary = serializers.SerializerMethodField()

    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description', 'status',
            'standard_family',
            'norm_type', 'target_count',
            'ctm', 'ctm_name', 'wg', 'wg_name',
            'iso_reference', 'arso_reference',
            'start_date', 'ctm_submission_date', 'legistic_review_date',
            'public_inquiry_start', 'public_inquiry_end', 'pilotage_validation_date',
            'adoption_date', 'homologation_date',
            'publication_date', 'jo_reference', 'jo_file',
            'current_version', 'tags', 'is_public',
            'latest_version', 'version_count', 'structured_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at', 'updated_at']

    def get_latest_version(self, obj):
        latest = obj.get_latest_version()
        if latest:
            return NormeVersionSerializer(latest).data
        return None

    def get_version_count(self, obj):
        return obj.versions.count()

    def get_structured_summary(self, obj):
        latest = obj.get_latest_version()
        return structured_content_summary(latest.content if latest else obj.description)


class NormeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour une norme"""
    reference_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description',
            'standard_family', 'category',
            'norm_type', 'target_count',
            'ctm', 'wg', 'iso_reference', 'arso_reference',
            'tags', 'is_public'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """Vérifier que WG appartient au CTM"""
        wg = data.get('wg')
        ctm = data.get('ctm')

        if wg and wg.ctm != ctm:
            raise serializers.ValidationError(
                "Le groupe de travail doit appartenir au comité technique sélectionné."
            )
        return data


class NormeStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le statut d'une norme"""
    class Meta:
        model = Norme
        fields = ['status']

    def validate_status(self, value):
        """Vérifier la transition de statut valide"""
        instance = self.instance
        if instance:
            if not instance.can_transition_to(value):
                allowed_statuses = instance.workflow_transitions().get(instance.status, [])
                raise serializers.ValidationError(
                    f"Transition invalide de {instance.status} à {value}. "
                    f"Transitions valides: {', '.join(allowed_statuses)}"
                )
        return value

    def update(self, instance, validated_data):
        instance.transition_to(validated_data['status'])
        return instance


class NormeVersionCreateSerializer(serializers.Serializer):
    """Serializer pour créer une nouvelle version de norme (simplifié pour éviter les erreurs de validation)"""
    title = serializers.CharField(max_length=500)
    content = serializers.CharField()
    comment = serializers.CharField(required=False, allow_blank=True)
    document = serializers.FileField(required=False, allow_null=True)

    @transaction.atomic
    def create(self, validated_data):
        """Créer une nouvelle version avec numéro auto-incrémenté et détection des changements"""
        norme = self.context.get('norme')
        if not norme:
            raise serializers.ValidationError("Norme not provided in context")

        # Calculer le prochain numéro de version
        latest = norme.versions.order_by('-version_number').first()
        next_version_number = (latest.version_number + 1) if latest else 1

        summary = validated_data.pop('comment', '')

        # 1. Créer la nouvelle version
        new_version = NormeVersion.objects.create(
            norme=norme,
            version_number=next_version_number,
            version_author=self.context.get('request').user,
            created_by=self.context.get('request').user,
            updated_by=self.context.get('request').user,
            summary=summary,
            **validated_data
        )

        norme.refresh_current_version(new_version, save=True)
        NormeContentBlock.objects.filter(version=new_version).delete()
        NormeContentBlock.objects.bulk_create(build_content_blocks(new_version))

        # 2. Détecter les changements si une version précédente existe
        if latest:
            old_paragraphs = [block['content'] for block in parse_norme_structure(latest.content)] or latest.content.split('\n\n')
            new_paragraphs = [block['content'] for block in parse_norme_structure(new_version.content)] or new_version.content.split('\n\n')

            matcher = difflib.SequenceMatcher(None, old_paragraphs, new_paragraphs)

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    # On traite les remplacements comme une modification de paragraphe
                    for idx in range(max(i2 - i1, j2 - j1)):
                        old_p = old_paragraphs[i1 + idx] if (i1 + idx) < i2 else ""
                        new_p = new_paragraphs[j1 + idx] if (j1 + idx) < j2 else ""
                        ChangementVersion.objects.create(
                            version=new_version,
                            previous_version=latest,
                            section=f"Paragraphe {i1 + idx + 1}",
                            old_text=old_p,
                            new_text=new_p,
                            change_type='MODIFY',
                            change_reason="Modification de paragraphe"
                        )
                elif tag == 'delete':
                    for idx in range(i1, i2):
                        ChangementVersion.objects.create(
                            version=new_version,
                            previous_version=latest,
                            section=f"Paragraphe {idx + 1}",
                            old_text=old_paragraphs[idx],
                            change_type='REMOVE',
                            change_reason="Suppression de paragraphe"
                        )
                elif tag == 'insert':
                    for idx in range(j1, j2):
                        ChangementVersion.objects.create(
                            version=new_version,
                            previous_version=latest,
                            section=f"Bloc {idx + 1}",
                            new_text=new_paragraphs[idx],
                            change_type='ADD',
                            change_reason="Ajout de paragraphe"
                        )

        return new_version


class NormeFullHistorySerializer(serializers.ModelSerializer):
    """Serializer avec historique complet"""
    versions = NormeVersionSerializer(many=True, read_only=True)
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)

    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description',
            'ctm', 'ctm_name', 'wg', 'wg_name', 'status',
            'norm_type', 'target_count',
            'iso_reference', 'arso_reference', 'tags', 'is_public',
            'versions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at', 'updated_at']
