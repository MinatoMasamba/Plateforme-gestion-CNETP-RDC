"""Données de recette exclusivement dans /tmp/expert_beta_review.sqlite3."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
os.environ['SQLITE_NAME'] = '/tmp/expert_beta_review.sqlite3'
os.environ['APPSTORE_PACKAGES_ROOT'] = '/tmp/expert_beta_packages'
os.environ['CLIENT_DIAGNOSTICS_DIR'] = '/tmp/expert_beta_diagnostics'
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG, Affectation
from apps.meetings.models import Reunion, ReunionParticipant
from apps.norms.models import Norme, NormeVersion

assert str(settings.DATABASES['default']['NAME']) == '/tmp/expert_beta_review.sqlite3'
call_command('migrate', verbosity=1)
user, _ = User.objects.get_or_create(username='beta_review', defaults={'email': 'beta_review@example.test', 'first_name': 'Amina', 'last_name': 'Recette', 'is_expert': True})
user.set_password('BetaReview2026!')
user.save()
structure, _ = Structure.objects.get_or_create(name='Structure de recette', defaults={'acronym': 'REC', 'category': 'ADMIN'})
expert, _ = Expert.objects.get_or_create(user=user, defaults={'structure': structure, 'status': 'ACTIVE'})
organizer_user, _ = User.objects.get_or_create(username='beta_meeting_organizer', defaults={'email': 'organizer@example.test', 'first_name': 'Jean', 'last_name': 'Recette', 'is_expert': True})
organizer, _ = Expert.objects.get_or_create(user=organizer_user, defaults={'structure': structure, 'status': 'ACTIVE'})
ctm = CTM.objects.order_by('number').first()
if ctm is None:
    ctm = CTM.objects.create(name='Sous-commission de recette', number=1, description='Recette isolée')
if ctm.number > 8 and ctm.name == 'Sous-commission de recette':
    ctm.number = 1
    ctm.save(update_fields=['number'])
wg, _ = WG.objects.get_or_create(name='Groupe de recette', ctm=ctm, defaults={'number': 1})
Affectation.objects.get_or_create(expert=expert, ctm=ctm, wg=wg)
norm, _ = Norme.objects.get_or_create(reference_number='BETA-RECETTE-001', defaults={'title': 'Projet de norme — sécurité des ouvrages', 'description': 'Document de recette isolé', 'ctm': ctm, 'wg': wg, 'created_by': user})
NormeVersion.objects.get_or_create(norme=norm, version_number=1, defaults={'title': norm.title, 'content': '1. Objet\nExigences de sécurité des ouvrages.\n2. Domaine d’application\nTravaux de construction.', 'version_author': user})
for day in range(3):
    meeting, _ = Reunion.objects.get_or_create(titre=f'Recette — session technique {day + 1}', defaults={'type': 'WG', 'wg': wg, 'ctm': ctm, 'organisateur': expert, 'date': timezone.now() + timezone.timedelta(days=day, minutes=10), 'mode': 'EXTERNE', 'lien_reunion_virtuelle': 'https://meet.google.com/abc-defg-hij', 'ordre_jour': 'Relecture du projet\nContributions des membres\nProchaines échéances'})
    ReunionParticipant.objects.get_or_create(reunion=meeting, expert=expert)
    meeting.organisateur = organizer if day == 0 else expert
    meeting.date = timezone.now() + timezone.timedelta(days=day, minutes=10)
    meeting.question_vote = 'Approuver les conclusions de la séance ?'
    meeting.save(update_fields=['organisateur', 'date', 'question_vote'])
print('Recette préparée : compte beta_review@example.test, base isolée /tmp/expert_beta_review.sqlite3')
