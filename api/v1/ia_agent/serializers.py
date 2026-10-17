from rest_framework import serializers

from apps.ia_agent.models import AgentArtifact, AgentMessage, AgentSession


class AgentSessionSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(required=False, default='deepseek', max_length=20, allow_blank=True)

    class Meta:
        model = AgentSession
        fields = ['id', 'scope', 'provider', 'title', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_provider(self, value):
        """Accepte les anciennes valeurs (gemini/anthropic) et les ramène à DeepSeek.

        Des sessions créées avant la migration DeepSeek ont laissé des valeurs
        obsolètes dans le localStorage des navigateurs. Sans cette normalisation,
        la création d'une nouvelle session renvoie 400 et l'assistant ne démarre pas.
        """
        allowed = {choice[0] for choice in AgentSession.PROVIDER_CHOICES}
        if not value or value not in allowed:
            return 'deepseek'
        return value


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = ['id', 'role', 'content', 'tool_name', 'tool_input', 'tool_output', 'created_at']


class AgentArtifactSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = AgentArtifact
        fields = [
            'id', 'session', 'message', 'artifact_type', 'title', 'payload', 'status',
            'created_at', 'updated_at', 'links',
        ]
        read_only_fields = fields

    def get_links(self, obj):
        """Retourne uniquement des liens internes générés côté serveur."""
        payload = obj.payload or {}
        links = payload.get('links') if isinstance(payload.get('links'), list) else []

        if not links and obj.artifact_type == 'WG_REQUEST':
            if payload.get('expert_id'):
                links.append({
                    'label': f"Voir l'expert {payload.get('expert_name', '')}".strip(),
                    'url': f"/api/v1/experts/{payload['expert_id']}/",
                })
            if payload.get('wg_id'):
                links.append({
                    'label': payload.get('wg_label', 'Voir le groupe de travail'),
                    'url': f"/api/v1/wg/{payload['wg_id']}/",
                })
        elif not links and obj.artifact_type == 'NORM_OVERLAP':
            if payload.get('ctm_id'):
                links.append({
                    'label': f"Voir le CTM {payload.get('ctm_number', payload['ctm_id'])}",
                    'url': f"/api/v1/ctm/{payload['ctm_id']}/",
                })
            for key in ('wg_a', 'wg_b'):
                group = payload.get(key) or {}
                if group.get('id'):
                    links.append({
                        'label': group.get('label', f"Voir le groupe {group['id']}"),
                        'url': f"/api/v1/wg/{group['id']}/",
                    })
        elif not links and obj.artifact_type == 'EXTERNAL_PROPOSAL':
            if payload.get('norme_id'):
                links.append({
                    'label': payload.get('norme_reference', 'Voir la norme'),
                    'url': f"/api/v1/norms/{payload['norme_id']}/",
                })
            if payload.get('ctm_id'):
                links.append({
                    'label': f"Voir le CTM {payload['ctm_id']}",
                    'url': f"/api/v1/ctm/{payload['ctm_id']}/",
                })

        return [
            {'label': str(item.get('label') or 'Ouvrir'), 'url': item['url']}
            for item in links
            if isinstance(item, dict)
            and isinstance(item.get('url'), str)
            and item['url'].startswith('/')
        ]
