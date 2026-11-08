"""Référentiel retenu du 31 octobre 2026 ; aucune identité de compte déduite."""
from django.core.exceptions import ValidationError
from django.db import transaction
from .phoenix_models import OrganisationVersion, Organe, PosteOrganisation, JournalMigration

VERSION = 'st-matrice-v3-2026-10-31'
REFERENCE = 'Matrice ST v3 du 31/10/2026 — communiqué 003/CNE-ITP/ST/2026 du 24/10/2026'
POLES = {
    'ST': 'Coordination du Secrétariat technique',
    'ST-P1': 'Planification et suivi',
    'ST-P2': 'Documentation, codification et PTN',
    'ST-P3': 'Juridique, administratif et financier',
    'ST-P4': 'Appui techniques et Formation',
}
# numéro, organe, fonction, sous-rôle, titulaire, institution, chef
POSTS = [
    (1, 'ST', 'Coordonnateur du ST', 'coordonnateur_principal', "Firmin KIALA KI-N'SOKI", 'Dircab / Cabinet', False),
    (2, 'ST', 'Coordonnateur du ST', 'coordonnateur_adjoint', 'Georges KOSHI YUMA', 'SG / ITP', False),
    (3, 'ST', 'Coordonnateur du ST', 'coordonnateur_adjoint', 'Donatien SONGHU KAYUMBA', 'SG / RECO', False),
    (4, 'ST', 'Coordonnateur du ST', 'coordonnateur_adjoint', 'Papy LABILA NKALIM', 'Dircab / Cabinet', False),
    (5, 'ST', 'Coordonnateur du ST', 'coordonnateur_adjoint', 'Alexi BONDELI', 'Financier', False),
    (6, 'ST', 'Assistant de direction et secrétaire de séance', 'assistant_executif', 'Pius NGOIE ONOMBA', 'Cabinet', False),
    (7, 'ST', 'Chef de pôle Logistique', 'chef_logistique', 'Emany LUWENGA MUANA', 'Indépendant', False),
    (8, 'ST-P1', 'Chef de pôle Planification et suivi', 'chef_planification', 'Reagan NDOY PUKUTA', 'Cabinet', True),
    (9, 'ST-P1', 'Chargé du suivi et des indicateurs', 'suivi_indicateurs', 'Flavien YANGOTIKALA', 'Indépendant', False),
    (10, 'ST-P2', 'Chef du pôle Documentation, codification et PTN', 'chef_documentation', 'Modeste KALISIKI', 'Secrétariat / TP', True),
    (11, 'ST-P2', 'Gestionnaire GED (documents, codification, versions)', 'operateur_saisie', 'Rosine NGALULA', 'Secrétariat / TP', False),
    (12, 'ST-P2', 'Gestionnaire du registre des paramètres techniques nationaux', 'gestionnaire_ptn', 'Agnès KITSONI-TSHONI', 'Secrétariat / TP', False),
    (13, 'ST-P3', 'Juriste, chef de pôle Juridique, administratif et financier', 'expert_juridique', 'Thyty MAWETE MA LONGIDIKA', 'Cabinet', True),
    (14, 'ST-P3', 'Juriste, chef de pôle Juridique, administratif et financier', 'expert_juridique', 'Medi PINDI', 'Secrétariat / RECO', True),
    (15, 'ST-P3', 'Chargé administratif et financier', 'gaf', 'Alain MUKANGU NADIA', 'Cabinet', False),
    (16, 'ST-P3', 'Chargé administratif et financier', 'gaf', 'Sympho KAYEMBE MPOY', 'Cabinet', False),
    (17, 'ST-P4', 'Chef de pôle Appui techniques et Formation', 'chef_appui', 'François ERHAZIKA MIRINDI', 'Cabinet', True),
    (18, 'ST-P4', "Chargé de l’appui techniques (informatique)", 'it_sg_itp', 'Hochéa Josué PONGO-PONGO KALANG', 'Indépendant', False),
    (19, 'ST-P4', 'Chargé de communication et relations usagers', 'communicateur', 'Patrick KAKU MAKAMBO', 'Secrétariat / RECO', False),
]
ROLE_POLES = {row[3]: row[1] for row in POSTS}
ROLE_POLES.update({name: 'ST' for name in ('liaison_fec', 'responsable_enquetes')})
ROLE_POLES.update({name: 'expertise' for name in ('sig_beau', 'sig_ovd', 'veille_acgt', 'veille_sg', 'sauvegardes_ci', 'planification_recons', 'economiste_foner', 'scientifique_inbtp')})
ROLE_POLES['it_btc'] = 'ST-P4'


@transaction.atomic
def prepare_matrix():
    """Prépare un référentiel suspendu : ne bascule jamais l'organisation en service."""
    version, created = OrganisationVersion.objects.get_or_create(code=VERSION, defaults={
        'name': 'CNE-ITP — Matrice ST v3', 'source_document': REFERENCE, 'status': 'SUSPENDED',
    })
    if not created:
        if version.source_document != REFERENCE:
            raise ValidationError('La référence de cette version ne correspond pas à la matrice v3.')
        return version
    st = None
    for code, label in POLES.items():
        organ = Organe.objects.create(version=version, code=code, name=label,
            type='ST' if code == 'ST' else 'ST_POLE', parent=st,
            status='VALIDATED', source_reference=REFERENCE)
        if code == 'ST':
            st = organ
        for number, pole, title, sub_role, name, origin, head in POSTS:
            if pole != code:
                continue
            PosteOrganisation.objects.create(organe=organ, code=f'ST-V3-{number:02}',
                category='POLE_HEAD' if head else ('COORDINATION' if number <= 5 else 'MEMBER'),
                title=title, st_sub_role=sub_role, nominated_name=name, origin_label=origin,
                status='VALIDATED', source_reference=REFERENCE)
    JournalMigration.objects.create(version=version, operation='PREPARE_ST_V3', target=VERSION,
        after={'posts': 19, 'poles': 4, 'accounts_activated': 0}, reason=REFERENCE)
    return version


def mandate_capabilities(mandate):
    """Capacités explicites ; aucune interprétation d'un nom ou d'une institution."""
    if not mandate or not mandate.poste.st_sub_role:
        return {}
    post = mandate.poste
    pole = post.organe.code
    head = post.category == 'POLE_HEAD'
    role = post.st_sub_role
    return {
        'st_matrix_v3': True, 'st_post_code': post.code,
        'st_is_pole_head': head, 'st_can_confirm': head,
        'st_can_follow': pole == 'ST-P1',
        'st_can_manage_ptn': role == 'gestionnaire_ptn' or (head and pole == 'ST-P2'),
        'st_can_audit_st': head and pole == 'ST-P3',
        'st_can_audit_sc': pole == 'ST-P1',
        'can_fast_entry': role == 'operateur_saisie' or (head and pole == 'ST-P2'),
        'can_grand_livre': pole == 'ST-P3',
        'can_legistique_ctc': pole == 'ST-P3' and head,
        'can_admin_system': role in ('it_btc', 'it_sg_itp') or (head and pole == 'ST-P4'),
        'can_route_documents': role in ('coordonnateur_principal', 'coordonnateur_adjoint'),
        'can_approve_ctc_requests': role == 'assistant_executif',
    }
