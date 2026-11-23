from datetime import datetime

import pytest
from rest_framework.test import APIClient

from apps.messaging.models import Message


@pytest.mark.django_db
def test_conversations_expose_latest_message_and_unread_count(
    expert_factory,
    user_factory,
    ctm_factory,
):
    ctm = ctm_factory(number=12, name='SC Essais')
    current = expert_factory(ctm=ctm, user=user_factory(
        username='current-expert',
        email='current@example.test',
        first_name='Amina',
        last_name='Courant',
    ))
    contact = expert_factory(
        ctm=ctm,
        user=user_factory(
            username='other-expert',
            email='other@example.test',
            first_name='Mika',
            last_name='Ngoy',
        ),
        specialties='Qualité',
    )

    older = Message.objects.create(
        sender=current.user,
        recipient=contact.user,
        content='Premier message',
    )
    latest = Message.objects.create(
        sender=contact.user,
        recipient=current.user,
        content='Dernier message',
        is_clause_share=True,
        clause_code='NCD-12',
        clause_excerpt='Extrait partagé',
    )

    client = APIClient()
    client.force_authenticate(current.user)
    response = client.get('/api/v1/messages/conversations/')

    assert response.status_code == 200
    assert len(response.data) == 1
    row = response.data[0]
    assert row['user_id'] == contact.user_id
    assert row['structure_name'] == contact.structure.name
    assert row['ctm_name'] == ctm.name
    assert row['unread_count'] == 1
    assert row['last_message'] == {
        'id': latest.id,
        'content': 'Dernier message',
        'sender': contact.user_id,
        'timestamp': row['last_message']['timestamp'],
        'is_read': False,
        'is_clause_share': True,
        'clause_code': 'NCD-12',
        'clause_excerpt': 'Extrait partagé',
    }
    assert (
        datetime.fromisoformat(row['last_message']['timestamp']) == latest.timestamp
    )
    assert older.id != latest.id


@pytest.mark.django_db
def test_mark_conversation_as_read_updates_status(
    expert_factory,
    user_factory,
    ctm_factory,
):
    ctm = ctm_factory(number=13)
    current = expert_factory(ctm=ctm)
    contact = expert_factory(
        ctm=ctm,
        user=user_factory(
            username='sender-expert',
            email='sender@example.test',
        ),
    )
    message = Message.objects.create(
        sender=contact.user,
        recipient=current.user,
        content='À lire',
    )

    client = APIClient()
    client.force_authenticate(current.user)
    response = client.post(
        '/api/v1/messages/mark_conversation_as_read/',
        {'participant_id': contact.user_id},
        format='json',
    )

    assert response.status_code == 200
    assert response.data == {'marked_read': 1}
    message.refresh_from_db()
    assert message.is_read is True
    assert message.status == Message.STATUS_READ
