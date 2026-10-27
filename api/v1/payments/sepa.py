"""Génération des ordres de virement ISO 20022 pain.001."""
import re
from datetime import date
from decimal import Decimal
from uuid import uuid4
from xml.etree import ElementTree as ET

from django.conf import settings


NAMESPACE = 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'
ET.register_namespace('', NAMESPACE)


def _tag(name):
    return f'{{{NAMESPACE}}}{name}'


def _child(parent, name, text=None, **attributes):
    node = ET.SubElement(parent, _tag(name), attributes)
    if text is not None:
        node.text = str(text)
    return node


def _identifier(value):
    return re.sub(r'\s+', '', str(value or '')).strip()


def _agent(parent, bank_name):
    agent = _child(parent, 'FinInstnId')
    normalized = _identifier(bank_name).upper()
    if re.fullmatch(r'[A-Z0-9]{8}|[A-Z0-9]{11}', normalized):
        _child(agent, 'BIC', normalized)
    else:
        _child(agent, 'Nm', bank_name)


def build_pain_001(
    jetons,
    *,
    debtor_name,
    debtor_iban,
    debtor_bic,
    currency='USD',
    execution_date=None,
    message_id=None,
):
    """Construit le XML pain.001.001.03 pour les jetons fournis."""
    jetons = list(jetons)
    total = sum((jeton.montant for jeton in jetons), Decimal('0'))
    execution_date = execution_date or date.today()
    message_id = message_id or (
        f"CNETP-{execution_date:%Y%m%d}-{uuid4().hex[:10].upper()}"
    )

    document = ET.Element(_tag('Document'))
    initiation = _child(document, 'CstmrCdtTrfInitn')

    header = _child(initiation, 'GrpHdr')
    _child(header, 'MsgId', message_id)
    _child(header, 'CreDtTm', f"{execution_date.isoformat()}T00:00:00")
    _child(header, 'NbOfTxs', len(jetons))
    _child(header, 'CtrlSum', f'{total:.2f}')
    _child(_child(header, 'InitgPty'), 'Nm', debtor_name)

    payment_info = _child(initiation, 'PmtInf')
    _child(payment_info, 'PmtInfId', message_id)
    _child(payment_info, 'PmtMtd', 'TRF')
    _child(payment_info, 'BtchBookg', 'true')
    _child(payment_info, 'NbOfTxs', len(jetons))
    _child(payment_info, 'CtrlSum', f'{total:.2f}')
    _child(_child(_child(payment_info, 'PmtTpInf'), 'SvcLvl'), 'Cd', 'SEPA')
    _child(payment_info, 'ReqdExctnDt', execution_date.isoformat())
    _child(_child(payment_info, 'Dbtr'), 'Nm', debtor_name)
    _child(_child(_child(payment_info, 'DbtrAcct'), 'Id'), 'IBAN', _identifier(debtor_iban))
    _agent(_child(payment_info, 'DbtrAgt'), debtor_bic)
    _child(payment_info, 'ChrgBr', 'SLEV')

    for jeton in jetons:
        expert = jeton.expert
        name = expert.user.get_full_name() or expert.user.username
        transaction = _child(payment_info, 'CdtTrfTxInf')
        _child(_child(transaction, 'PmtId'), 'EndToEndId', f'JETON-{jeton.pk}')
        _child(
            _child(transaction, 'Amt'),
            'InstdAmt',
            f'{jeton.montant:.2f}',
            Ccy=currency,
        )
        _child(_child(transaction, 'Cdtr'), 'Nm', name[:140])
        _child(
            _child(_child(transaction, 'CdtrAcct'), 'Id'),
            'IBAN',
            _identifier(expert.bank_account),
        )
        _agent(_child(transaction, 'CdtrAgt'), expert.bank_name)
        _child(
            _child(transaction, 'RmtInf'),
            'Ustrd',
            f'Jeton de présence — {jeton.reunion.titre} — {name}'[:140],
        )

    ET.indent(document, space='  ')
    return ET.tostring(
        document,
        encoding='utf-8',
        xml_declaration=True,
    )


def sepa_settings():
    """Coordonnées du débiteur CNETP, ou erreur de configuration lisible."""
    debtor_name = getattr(settings, 'CNETP_SEPA_DEBTOR_NAME', 'CNETP').strip()
    debtor_iban = _identifier(getattr(settings, 'CNETP_SEPA_DEBTOR_IBAN', ''))
    debtor_bic = _identifier(getattr(settings, 'CNETP_SEPA_DEBTOR_BIC', ''))
    currency = str(getattr(settings, 'CNETP_SEPA_CURRENCY', 'USD')).upper()
    missing = []
    if not debtor_name:
        missing.append('CNETP_SEPA_DEBTOR_NAME')
    if not debtor_iban:
        missing.append('CNETP_SEPA_DEBTOR_IBAN')
    if not re.fullmatch(r'[A-Z0-9]{8}|[A-Z0-9]{11}', debtor_bic):
        missing.append('CNETP_SEPA_DEBTOR_BIC')
    if not re.fullmatch(r'[A-Z]{3}', currency):
        missing.append('CNETP_SEPA_CURRENCY')
    return {
        'debtor_name': debtor_name,
        'debtor_iban': debtor_iban,
        'debtor_bic': debtor_bic,
        'currency': currency,
        'missing': missing,
    }
