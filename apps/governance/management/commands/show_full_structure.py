"""
Commande d'affichage (lecture seule, ne modifie rien) de l'arborescence complète
de la structure organisationnelle CNETP : Comité de Pilotage, Cellule Technique
de Coordination, puis les 8 CTM avec leurs WG, bureaux et affectations d'experts —
en faisant apparaître les liens (structure d'origine, titulaire) de chaque branche
et sous-branche.

Usage : python manage.py show_full_structure
"""

from django.core.management.base import BaseCommand

from apps.governance.models import (
    CTM, WG, Affectation, ComitePilotage, TechnicalCell,
    PosteNominatif, PosteNominatifCTC,
)


class Command(BaseCommand):
    help = "Affiche (lecture seule) l'arborescence complète : Pilotage / CTC / CTM / WG / affectations, avec leurs liens"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "\n" + "=" * 84 +
            "\n  ARBORESCENCE COMPLÈTE DE LA STRUCTURE ORGANISATIONNELLE CNETP"
            "\n" + "=" * 84
        ))

        self._print_pilotage()
        self._print_ctc()
        self._print_ctm_tree()

    # ------------------------------------------------------------------ #
    def _holder_label(self, poste):
        if poste.holder:
            return self.style.SUCCESS(f"✓ {poste.holder.full_name}")
        return self.style.WARNING("⏳ vacant")

    def _structure_label(self, structure):
        if structure:
            return f"{structure.name} ({structure.acronym})" if hasattr(structure, 'acronym') else structure.name
        return "—"

    # ------------------------------------------------------------------ #
    def _print_pilotage(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n▸ COMITÉ DE PILOTAGE"))
        comite = ComitePilotage.objects.first()
        if not comite:
            self.stdout.write(self.style.WARNING("   (non initialisé)"))
            return
        self.stdout.write(f"   {comite.name}")
        postes = (
            PosteNominatif.objects.filter(comite=comite)
            .select_related('required_structure', 'holder')
            .order_by('order')
        )
        for p in postes:
            structure = (
                f"{p.required_structure.name} ({p.required_structure.acronym})"
                if p.required_structure else "— (structure non définie)"
            )
            ligne = f"Ligne {p.quota_line}" if p.quota_line else "—"
            self.stdout.write(f"     [{p.order:2d}] {p.title}")
            self.stdout.write(f"           → {structure}  ·  {ligne}  ·  {self._holder_label(p)}")
        self.stdout.write(f"   TOTAL : {postes.count()} poste(s)")

    # ------------------------------------------------------------------ #
    def _print_ctc(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n▸ CELLULE TECHNIQUE DE COORDINATION (CTC)"))
        ctc = TechnicalCell.objects.first()
        if not ctc:
            self.stdout.write(self.style.WARNING("   (non initialisée)"))
            return
        self.stdout.write(f"   {ctc.name}")
        postes = (
            PosteNominatifCTC.objects.filter(ctc=ctc)
            .select_related('required_structure', 'holder')
            .order_by('order')
        )
        for p in postes:
            structure = (
                f"{p.required_structure.name} ({p.required_structure.acronym})"
                if p.required_structure else "— (structure non définie)"
            )
            ligne = f"Ligne {p.quota_line}" if p.quota_line else "—"
            self.stdout.write(f"     [{p.order:2d}] {p.title}")
            self.stdout.write(f"           → {structure}  ·  {ligne}  ·  {self._holder_label(p)}")
        self.stdout.write(f"   TOTAL : {postes.count()} poste(s)")

    # ------------------------------------------------------------------ #
    def _print_ctm_tree(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n▸ LES 8 COMITÉS TECHNIQUES MIROIRS (CTM)"))

        for ctm in CTM.objects.all().order_by('number'):
            self.stdout.write(
                f"\n   ━━━ CTM {ctm.number} — {ctm.name}  "
                f"[{ctm.iso_reference} / {ctm.arso_reference}] ━━━"
            )
            self.stdout.write(
                f"     Bureau : Président scientifique = "
                f"{ctm.scientific_president.full_name if ctm.scientific_president else self.style.WARNING('vacant')}"
                f"  ·  Rapporteur = "
                f"{ctm.rapporteur.full_name if ctm.rapporteur else self.style.WARNING('vacant')}"
                f"  ·  Secrétaire = "
                f"{ctm.secretary.full_name if ctm.secretary else self.style.WARNING('vacant')}"
            )

            wgs = WG.objects.filter(ctm=ctm).order_by('number')
            for wg in wgs:
                self.stdout.write(f"\n     ▸ WG {ctm.number}.{wg.number} — {wg.name}")
                self.stdout.write(
                    f"         Bureau : Président = "
                    f"{wg.president.full_name if wg.president else '—'}"
                    f"  ·  Rapporteur = "
                    f"{wg.rapporteur.full_name if wg.rapporteur else '—'}"
                    f"  ·  Secrétaire = "
                    f"{wg.secretary.full_name if wg.secretary else '—'}"
                )
                affectations = sorted(
                    Affectation.objects.filter(wg=wg).select_related('expert', 'expert__structure'),
                    key=lambda a: a.expert.full_name,
                )
                if affectations:
                    self.stdout.write(f"         Membres affectés ({len(affectations)}) :")
                    for a in affectations:
                        structure = getattr(a.expert, 'structure', None)
                        lien_structure = f" — {structure.name} ({structure.acronym})" if structure else ""
                        primaire = " [principal]" if a.is_primary_wg else ""
                        self.stdout.write(f"           • {a.expert.full_name}{lien_structure}{primaire}")
                else:
                    self.stdout.write("         Membres affectés : aucun")

            ctm_affectations = Affectation.objects.filter(ctm=ctm)
            self.stdout.write(
                f"\n     TOTAL CTM {ctm.number} : {wgs.count()} WG  ·  "
                f"{ctm_affectations.count()} expert(s) affecté(s) au CTM"
            )

        self.stdout.write(
            "\n" + "=" * 84 +
            f"\nTOTAL GÉNÉRAL : {CTM.objects.count()} CTM  ·  {WG.objects.count()} WG  ·  "
            f"{Affectation.objects.count()} affectation(s)\n"
        )
