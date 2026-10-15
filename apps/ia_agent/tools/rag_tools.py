from . import register


SEARCH_PLATFORM_DOCUMENTS_SCHEMA = {
    'type': 'object',
    'properties': {
        'query': {
            'type': 'string',
            'description': 'Question ou termes à rechercher dans les documents et données indexés.',
        },
        'limit': {
            'type': 'integer',
            'description': 'Nombre maximal de passages cités, entre 1 et 20.',
        },
        'source_kind': {
            'type': 'string',
            'enum': ['DOCUMENT', 'NORME', 'NORME_VERSION', 'EXPERT_CV'],
            'description': 'Limiter la recherche à un type de source (optionnel).',
        },
    },
    'required': ['query'],
}


@register(
    'search_platform_documents',
    'Recherche dans les documents et données métier indexés de la plateforme. Retourne des '
    'passages autorisés avec source, page ou section et identifiant de citation. Ne jamais '
    'présenter un résultat non cité comme une information officielle.',
    SEARCH_PLATFORM_DOCUMENTS_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def search_platform_documents(session, query, limit=8, source_kind=None):
    from ..services.rag import search

    results = search(
        user=session.user,
        query=query,
        limit=limit,
        source_kind=source_kind,
    )
    return {
        'query': query,
        'total': len(results),
        'results': results,
        'citation_rule': 'Citer source_id, titre et page/section lorsque disponibles.',
    }
