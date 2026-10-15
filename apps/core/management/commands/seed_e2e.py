"""Seed complet pour la campagne de tests E2E.

Crée, de façon idempotente :
  * les structures officielles, 8 CTM + 24 WG, le Comité de Pilotage, la CTC ;
  * les 27+20 postes nominatifs ;
  * les comptes des rôles : expert (/app/), secrétariat CTC (/ctc/), pilotage
    (/pilotage/...), ministre (publication JO) ;
  * 5 normes + 1 norme support d'historique, des versions, paiements,
    réunions, jetons et 10 conversations de messagerie.

Usage :
    python manage.py seed_e2e
    python manage.py seed_e2e --password 'MonPass123!'
"""
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


PASSWORD_DEFAULT = 'Cnetp2026!'

ROLE_ACCOUNTS = [
    # (username/email, first, last, flags)
    ('expert1@cnetp.cd', 'Expert', 'Un', {'is_expert': True}),
    ('ctc1@cnetp.cd', 'Secrétariat', 'Technique', {'is_expert': True, 'is_ctc_staff': True}),
    ('pilote1@cnetp.cd', 'Président', 'Pilotage', {'is_expert': True}),
    ('ministre1@cnetp.cd', 'Ministre', 'Tutelle', {'is_expert': True, 'is_minister': True}),
]

MESSAGE_TEXTE = (
    "Bonjour, pouvez-vous confirmer la section 2 de la norme en cours de rédaction ? "
    "Merci."
)


class Command(BaseCommand):
    help = "Crée le jeu de données et les comptes nécessaires aux tests E2E."

    def add_arguments(self, parser):
        parser.add_argument('--password', default=PASSWORD_DEFAULT,
                            help="Mot de passe commun aux comptes de test.")

    def handle(self, *args, **options):
        password = options['password']

        from django.contrib.auth import get_user_model
        from apps.experts.models import Expert, Structure
        from apps.governance.models import (CTM, WG, Affectation, TechnicalCell,
                                            CTCMembership, ComitePilotage,
                                            PilotageMembreship)
        from apps.norms.models import Norme, NormeVersion
        from apps.payments.models import Cotisation, JetonPresence
        from apps.meetings.models import Reunion
        from apps.messaging.models import Message

        User = get_user_model()

        # 1) Seeds de structure ------------------------------------------------
        for cmd in ['seed_official_structures', 'create_ctm_structure',
                    'seed_ctm_working_groups', 'init_pilotage_and_ctc',
                    'seed_pilotage_postes', 'seed_ctc_postes']:
            try:
                call_command(cmd, verbosity=0)
            except Exception as exc:  # pragma: no cover - dépend de l'ordre
                self.stdout.write(self.style.WARNING(f'  seed {cmd}: {exc}'))

        structure = Structure.objects.first()
        if structure is None:
            structure = Structure.objects.create(
                name='Structure E2E', acronym='E2E', category='ADMIN')

        ctm = CTM.objects.order_by('number').first()
        wg = WG.objects.filter(ctm=ctm).order_by('number').first()
        ctc = TechnicalCell.objects.first()
        comite = ComitePilotage.objects.first()

        # 2) Comptes de rôle ---------------------------------------------------
        def get_or_create_user(email, first, last, flags):
            user, _ = User.objects.get_or_create(username=email, defaults={'email': email})
            user.email = email
            user.first_name = first
            user.last_name = last
            for k, v in flags.items():
                setattr(user, k, v)
            user.set_password(password)
            user.save()
            return user

        users = {}
        for email, first, last, flags in ROLE_ACCOUNTS:
            users[email] = get_or_create_user(email, first, last, flags)

        experts = {}
        for email, user in users.items():
            expert, _ = Expert.objects.get_or_create(
                user=user, defaults={'structure': structure, 'status': 'ACTIVE'})
            if expert.status != 'ACTIVE':
                expert.status = 'ACTIVE'
            expert.structure = expert.structure or structure
            expert.ctm = expert.ctm or ctm
            expert.save()
            experts[email] = expert

        # 3) Membreships -------------------------------------------------------
        if ctc and not CTCMembership.objects.filter(expert=experts['ctc1@cnetp.cd']).exists():
            CTCMembership.objects.create(ctc=ctc, expert=experts['ctc1@cnetp.cd'],
                                         role='COORDINATOR')
        if comite and not PilotageMembreship.objects.filter(expert=experts['pilote1@cnetp.cd']).exists():
            PilotageMembreship.objects.create(comite=comite, expert=experts['pilote1@cnetp.cd'],
                                              role='PRESIDENT')
        if ctm and wg:
            Affectation.objects.get_or_create(expert=experts['expert1@cnetp.cd'], ctm=ctm, wg=wg)

        # 4) 10 experts supplémentaires dans le même CTM (messagerie) ----------
        extra_experts = []
        for i in range(2, 12):
            email = f'expert{i}@cnetp.cd'
            u = get_or_create_user(email, f'Expert{i}', 'CTM', {'is_expert': True})
            ex, _ = Expert.objects.get_or_create(
                user=u, defaults={'structure': structure, 'status': 'ACTIVE', 'ctm': ctm})
            ex.status = 'ACTIVE'
            ex.save()
            if ctm and wg:
                Affectation.objects.get_or_create(expert=ex, ctm=ctm, wg=wg)
            extra_experts.append(ex)
            experts[email] = ex

        # 5) Normes ------------------------------------------------------------
        normes = []
        for i in range(1, 6):
            n, created = Norme.objects.get_or_create(
                reference_number=f'E2E-NORME-{i:03d}',
                defaults={
                    'title': f'Norme E2E {i}',
                    'description': f'Norme de test E2E numéro {i}.',
                    'ctm': ctm, 'wg': wg, 'status': 'DRAFT',
                })
            normes.append(n)
            if created:
                NormeVersion.objects.create(
                    norme=n, version_number=1, title=n.title,
                    content=("Section 1 Objet\nContenu initial de la norme E2E.\n\n"
                             "Section 2 Domaine d'application\nÀ compléter."),
                    summary='Version initiale', is_draft=True,
                    version_author=users['expert1@cnetp.cd'])
                n.refresh_current_version()

        # Norme support d'historique (20 éditions)
        history_norme, created = Norme.objects.get_or_create(
            reference_number='E2E-HISTORIQUE-001',
            defaults={'title': 'Norme historique E2E', 'description': 'Support des 20 éditions.',
                      'ctm': ctm, 'wg': wg, 'status': 'DRAFT'})
        if not history_norme.versions.exists():
            NormeVersion.objects.create(
                norme=history_norme, version_number=1, title=history_norme.title,
                content='Ligne 1 : état initial.\nLigne 2 : invariante.\nLigne 3 : à modifier.',
                summary='Init', is_draft=True, version_author=users['expert1@cnetp.cd'])

        # 6) Paiements ---------------------------------------------------------
        for j, struct in enumerate(list(Structure.objects.all()[:3])):
            Cotisation.objects.get_or_create(
                structure=struct, annee=2026,
                defaults={'montant': 1000 + j * 500, 'status': 'PENDING',
                          'due_date': (timezone.now() + timedelta(days=30)).date()})

        # 7) Réunions + jetons -------------------------------------------------
        reunions = []
        for k in range(2):
            r, _ = Reunion.objects.get_or_create(
                titre=f'Réunion E2E {k + 1}',
                defaults={'type': 'CTM', 'ctm': ctm, 'wg': wg,
                          'date': timezone.now() + timedelta(days=k + 1),
                          'status': 'PLANNED', 'organisateur': experts['expert1@cnetp.cd']})
            reunions.append(r)
        if reunions:
            JetonPresence.objects.get_or_create(
                expert=experts['expert1@cnetp.cd'], reunion=reunions[0],
                defaults={'montant': 50, 'status': 'PENDING'})

        # 8) 10 conversations --------------------------------------------------
        conv_count = 0
        for ex in extra_experts:
            pair = Message.objects.filter(
                sender__in=[users['expert1@cnetp.cd'], ex.user],
                recipient__in=[users['expert1@cnetp.cd'], ex.user])
            if pair.exists():
                continue
            Message.objects.create(sender=users['expert1@cnetp.cd'], recipient=ex.user,
                                   content=MESSAGE_TEXTE)
            Message.objects.create(sender=ex.user, recipient=users['expert1@cnetp.cd'],
                                   content="Bien reçu, je vérifie et je reviens vers vous.")
            conv_count += 1

        # 9) Récapitulatif -----------------------------------------------------
        self.stdout.write(self.style.SUCCESS('\n=== Seed E2E terminé ==='))
        self.stdout.write(f'Comptes (mot de passe : {password}) :')
        for email in ['expert1@cnetp.cd', 'ctc1@cnetp.cd', 'pilote1@cnetp.cd', 'ministre1@cnetp.cd']:
            self.stdout.write(f'  - {email}')
        self.stdout.write(f'Experts supplémentaires : {len(extra_experts)}')
        self.stdout.write(f'Normes : {len(normes)} + historique (E2E-HISTORIQUE-001)')
        self.stdout.write(f'Nouvelles conversations : {conv_count}')
        self.stdout.write('URLs : /se-connecter/ (login), /app/ (expert), /ctc/, /pilotage/')
