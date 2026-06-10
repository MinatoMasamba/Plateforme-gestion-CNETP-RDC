"""
Commande de peuplement du Plan de Production Semestriel (6 mois) des normes
techniques, conformément à la "NOTE TECHNIQUE COMPLÉMENTAIRE : PLANIFICATION DU
PROGRAMME DE PRODUCTION (6 MOIS)" (Réf. CNE-ITP/CTC/PPT-2026).

Pour chacun des 24 Groupes de Travail (GT 1.1 à GT 8.3) décrits dans la Section I
du document, crée 2 enregistrements `Norme` (statut DRAFT) :
  - 1 "lot NCD" (Normes Nationales Congolaises) avec sa cible chiffrée (target_count)
    et son thème de production,
  - 1 norme nommée de catégorie CA / DIR / REC (target_count=1).

Cas particuliers traités :
  - SC4 (PDF) ne définit que GT4.1 et GT4.2 : le WG 4.3 "Conformité OACI" (CTM4)
    n'a pas d'équivalent dans ce plan et reste volontairement sans entrée.
  - SC5 (PDF) définit GT5.1 à GT5.4 alors que CTM5 n'avait que 3 WG : le WG 5.4
    "Équipements, Signalisation et Sécurité des Corridors" est créé par cette
    commande (get_or_create) avant le peuplement des normes.

Idempotente : `update_or_create` sur `reference_number`.
"""

from django.core.management.base import BaseCommand
from apps.governance.models import CTM, WG
from apps.norms.models import Norme


# Chaque entrée correspond à un GT (CTM n° . WG n°) de la Section I du document.
PRODUCTION_PLAN = [
    {
        'ctm': 1, 'wg': 1,
        'ncd_count': 10,
        'ncd_theme': "Méthodes d'essais d'identification, granulométrie, limites d'Atterberg, "
                      "essais Proctor et CBR adaptés aux sols latéritiques tropicaux.",
        'other_type': 'DIR',
        'other_title': "Protocole obligatoire de prélèvement et de conservation des échantillons "
                        "géotechniques sensibles",
        'other_desc': "Protocole obligatoire de prélèvement et de conservation des échantillons "
                       "géotechniques sensibles.",
    },
    {
        'ctm': 1, 'wg': 2,
        'ncd_count': 8,
        'ncd_theme': "Paramètres de calcul de la capacité portante, tassements des fondations "
                      "superficielles, et dimensionnement des pieux.",
        'other_type': 'CA',
        'other_title': "Code National des Fondations de la RDC",
        'other_desc': "Code National des Fondations de la RDC (opposable aux bureaux d'études).",
    },
    {
        'ctm': 1, 'wg': 3,
        'ncd_count': 7,
        'ncd_theme': "Classification des géo-matériaux pour remblais, compactage lourd, et "
                      "critères de stabilité des talus.",
        'other_type': 'REC',
        'other_title': "Guide de Stabilisation Biologique et Mécanique des Érosions Urbaines en RDC",
        'other_desc': "Guide de Stabilisation Biologique et Mécanique des Érosions Urbaines en RDC.",
    },
    {
        'ctm': 2, 'wg': 1,
        'ncd_count': 12,
        'ncd_theme': "Règles de calcul de la fatigue des aciers, ponts suspendus, ponts-cadres et "
                      "viaducs en béton précontraint.",
        'other_type': 'CA',
        'other_title': "Code National des Charges, Gabarits et Surcharges Routières Mobiles",
        'other_desc': "Code National des Charges, Gabarits et Surcharges Routières Mobiles.",
    },
    {
        'ctm': 2, 'wg': 2,
        'ncd_count': 10,
        'ncd_theme': "Spécifications d'étanchéité des digues de retenue, évacuateurs de crue, et "
                      "auscultation des barrages hydroélectriques.",
        'other_type': 'DIR',
        'other_title': "Protocole d'évaluation des crues de projet et risques hydro-tectoniques",
        'other_desc': "Protocole d'évaluation des crues de projet et risques hydro-tectoniques.",
    },
    {
        'ctm': 2, 'wg': 3,
        'ncd_count': 8,
        'ncd_theme': "Durabilité face à la carbonatation, formulation des bétons de haute "
                      "performance, et adjuvants en milieu tropical humide.",
        'other_type': 'REC',
        'other_title': "Manuel de mise en œuvre et de cure du béton de masse en climat chaud",
        'other_desc': "Manuel de mise en œuvre et de cure du béton de masse en climat chaud.",
    },
    {
        'ctm': 3, 'wg': 1,
        'ncd_count': 15,
        'ncd_theme': "Règles de calcul mécanique du béton armé (transposition Eurocode 2), "
                      "charpentes métalliques et structures en bois d'œuvre.",
        'other_type': 'CA',
        'other_title': "Code National de Dimensionnement du Gros Œuvre des Bâtiments",
        'other_desc': "Code National de Dimensionnement du Gros Œuvre des Bâtiments.",
    },
    {
        'ctm': 3, 'wg': 2,
        'ncd_count': 10,
        'ncd_theme': "Éclairage naturel minimal, étanchéité des façades, isolation thermique "
                      "passive, et valorisation de la norme africaine ARS 1333 (éco-matériaux).",
        'other_type': 'DIR',
        'other_title': "Règlementation thermique et d'efficacité énergétique des bâtiments "
                        "administratifs du giron étatique",
        'other_desc': "Règlementation thermique et d'efficacité énergétique des bâtiments "
                       "administratifs du giron étatique.",
    },
    {
        'ctm': 3, 'wg': 3,
        'ncd_count': 10,
        'ncd_theme': "Résistance au feu des cloisons, dimensionnement des voies d'évacuation, "
                      "et rampes PMR.",
        'other_type': 'REC',
        'other_title': "Guide de mise en conformité d'accessibilité universelle pour les "
                        "Établissements Recevant du Public (ERP)",
        'other_desc': "Guide de mise en conformité d'accessibilité universelle pour les "
                       "Établissements Recevant du Public (ERP).",
    },
    {
        'ctm': 4, 'wg': 1,
        'ncd_count': 8,
        'ncd_theme': "Dimensionnement structurel des pistes sous fortes charges d'aéronefs, "
                      "enrobés aéronautiques et traitement des sols d'assise.",
        'other_type': 'CA',
        'other_title': "Règlement National des Infrastructures de Surface Aéroportuaires",
        'other_desc': "Règlement National des Infrastructures de Surface Aéroportuaires "
                       "(Alignement OACI).",
    },
    {
        'ctm': 4, 'wg': 2,
        'ncd_count': 7,
        'ncd_theme': "Géométrie des aires de mouvement, résistance des terminaux de fret, et "
                      "structures de balisage.",
        'other_type': 'REC',
        'other_title': "Directives de maintenance et de stabilisation des pistes d'atterrissage "
                        "secondaires en terre",
        'other_desc': "Directives de maintenance et de stabilisation des pistes d'atterrissage "
                       "secondaires en terre.",
    },
    # WG 4.3 "Conformité OACI" : pas de GT correspondant dans ce plan (laissé vide).
    {
        'ctm': 5, 'wg': 1,
        'ncd_count': 12,
        'ncd_theme': "Structures de chaussées bitumineuses, comportement des graves-latérites "
                      "améliorées au ciment, et pistes en terre de l'OVDA.",
        'other_type': 'CA',
        'other_title': "Catalogue National de Dimensionnement des Structures de Chaussées de la RDC",
        'other_desc': "Catalogue National de Dimensionnement des Structures de Chaussées de la RDC.",
    },
    {
        'ctm': 5, 'wg': 2,
        'ncd_count': 8,
        'ncd_theme': "Profils des rails, traverses en béton armé, ballast de haute résistance, "
                      "et tolérances d'alignement géométrique.",
        'other_type': 'DIR',
        'other_title': "Directives d'interopérabilité des réseaux ferroviaires à écartement SADC "
                        "(1067 mm)",
        'other_desc': "Directives d'interopérabilité des réseaux ferroviaires à écartement SADC "
                       "(1067 mm).",
    },
    {
        'ctm': 5, 'wg': 3,
        'ncd_count': 6,
        'ncd_theme': "Murs de quais, ducs-d'albe, structures d'accostage fluviales et défenses "
                      "élastiques.",
        'other_type': 'REC',
        'other_title': "Guide technique d'aménagement des débarcadères et raccordements "
                        "logistiques ruraux",
        'other_desc': "Guide technique d'aménagement des débarcadères et raccordements "
                       "logistiques ruraux.",
    },
    {
        'ctm': 5, 'wg': 4,
        'ncd_count': 4,
        'ncd_theme': "Marquages routiers rétroréfléchissants, barrières de sécurité et "
                      "signalisation verticale (Transposition Manuel SADC RTSM).",
        'other_type': 'DIR',
        'other_title': "Règlementation nationale des stations de pesage et de contrôle de la "
                        "charge à l'essieu",
        'other_desc': "Règlementation nationale des stations de pesage et de contrôle de la "
                       "charge à l'essieu (limite à 13 tonnes SADC).",
    },
    {
        'ctm': 6, 'wg': 1,
        'ncd_count': 9,
        'ncd_theme': "Canalisations sous pression (PEHD, fonte), réservoirs de stockage en béton "
                      "armé, et stations de traitement de la REGIDESO.",
        'other_type': 'CA',
        'other_title': "Code National de Distribution d'Eau Potable en Milieux Urbain et Périurbain",
        'other_desc': "Code National de Distribution d'Eau Potable en Milieux Urbain et Périurbain.",
    },
    {
        'ctm': 6, 'wg': 2,
        'ncd_count': 7,
        'ncd_theme': "Diamètres de tubage, cimentation sanitaire, crépines, et étanchéité des "
                      "têtes de puits profonds.",
        'other_type': 'DIR',
        'other_title': "Cadre d'obligation technique des forages profonds et de préservation des "
                        "nappes phréatiques",
        'other_desc': "Cadre d'obligation technique des forages profonds et de préservation des "
                       "nappes phréatiques.",
    },
    {
        'ctm': 6, 'wg': 3,
        'ncd_count': 4,
        'ncd_theme': "Gabarit des canaux d'irrigation à ciel ouvert, vannes de régulation, et "
                      "stations de pompage agricole.",
        'other_type': 'REC',
        'other_title': "Guide de conception technique des micro-retenues d'eau à vocation "
                        "agro-pastorale",
        'other_desc': "Guide de conception technique des micro-retenues d'eau à vocation "
                       "agro-pastorale.",
    },
    {
        'ctm': 7, 'wg': 1,
        'ncd_count': 6,
        'ncd_theme': "Dimensions, pentes de pose des collecteurs maçonnés, et exutoires de "
                      "décharge urbaine (OVD).",
        'other_type': 'CA',
        'other_title': "Règlement National du Drainage Pluvial et de Prévention des Inondations "
                        "Urbaines",
        'other_desc': "Règlement National du Drainage Pluvial et de Prévention des Inondations "
                       "Urbaines.",
    },
    {
        'ctm': 7, 'wg': 2,
        'ncd_count': 5,
        'ncd_theme': "Stations d'épuration autonomes, fosses septiques toutes eaux, et réseaux "
                      "d'égouts collectifs.",
        'other_type': 'DIR',
        'other_title': "Norme obligatoire de rejet des eaux usées domestiques et pré-traitement "
                        "des effluents industriels",
        'other_desc': "Norme obligatoire de rejet des eaux usées domestiques et pré-traitement "
                       "des effluents industriels.",
    },
    {
        'ctm': 7, 'wg': 3,
        'ncd_count': 4,
        'ncd_theme': "Systèmes d'étanchéité par géo-membranes, captage des lixiviats et réseaux "
                      "de dégazage des Centres d'Enfouissement Technique (CET).",
        'other_type': 'REC',
        'other_title': "Guide technique d'ingénierie civile pour la réhabilitation des décharges "
                        "sauvages",
        'other_desc': "Guide technique d'ingénierie civile pour la réhabilitation des décharges "
                       "sauvages.",
    },
    {
        'ctm': 8, 'wg': 1,
        'ncd_count': 6,
        'ncd_theme': "Étalonnage des presses d'écrasement de béton, capteurs de charge pour "
                      "essais sur ponts, et métrologie légale (OCC, BTC).",
        'other_type': 'DIR',
        'other_title': "Protocole national obligatoire de certification des laboratoires "
                        "d'essais BTP selon l'ISO 17025",
        'other_desc': "Protocole national obligatoire de certification des laboratoires "
                       "d'essais BTP selon l'ISO 17025.",
    },
    {
        'ctm': 8, 'wg': 2,
        'ncd_count': 5,
        'ncd_theme': "Essais de rupture, fiches d'homologation mécanique des essences de bois "
                      "(Wenge, Sapelli, Iroko) et roches de carrières.",
        'other_type': 'REC',
        'other_title': "Fiches de caractérisation et d'équivalence technique des gisements de "
                        "granulats par province",
        'other_desc': "Fiches de caractérisation et d'équivalence technique des gisements de "
                       "granulats par province.",
    },
    {
        'ctm': 8, 'wg': 3,
        'ncd_count': 4,
        'ncd_theme': "Standards d'interopérabilité des maquettes numériques IFC, et protocoles "
                      "d'analyse non linéaire sur progiciels de structure.",
        'other_type': 'DIR',
        'other_title': "Charte Nationale du BIM d'État pour l'encadrement de la transition "
                        "numérique dans la commande publique",
        'other_desc': "Charte Nationale du BIM d'État pour l'encadrement de la transition "
                       "numérique dans la commande publique.",
    },
]

REF_PREFIX = "CNETP-PPT2026"


class Command(BaseCommand):
    help = (
        "Peuple les Normes du Plan de Production Semestriel (CNE-ITP/CTC/PPT-2026) "
        "pour les 24 Groupes de Travail (NOTE TECHNIQUE N°1 COMPLÉMENT DIRCAB)."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Peuplement du Plan de Production Semestriel (185 NCD + 7 CA + 9 DIR + 8 REC) ==="
        ))

        # 1. S'assurer que le WG 5.4 (manquant) existe.
        ctm5 = CTM.objects.get(number=5)
        wg54, created = WG.objects.get_or_create(
            ctm=ctm5,
            number=4,
            defaults={
                'name': "Équipements, Signalisation et Sécurité des Corridors",
                'description': (
                    "GT 5.4 — Marquages routiers, barrières de sécurité, signalisation "
                    "verticale et stations de pesage à l'essieu (créé pour aligner CTM5 "
                    "sur les 4 GT du Plan de Production Semestriel CNE-ITP/CTC/PPT-2026)."
                ),
            }
        )
        status = "✓ créé" if created else "• déjà présent"
        self.stdout.write(f"   {status} : WG 5.4 — {wg54.name}")

        created_count = 0
        updated_count = 0
        totals = {'NCD': 0, 'CA': 0, 'DIR': 0, 'REC': 0}

        for entry in PRODUCTION_PLAN:
            ctm_num, wg_num = entry['ctm'], entry['wg']
            try:
                ctm = CTM.objects.get(number=ctm_num)
                wg = WG.objects.get(ctm=ctm, number=wg_num)
            except (CTM.DoesNotExist, WG.DoesNotExist):
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️ CTM {ctm_num} / WG {ctm_num}.{wg_num} introuvable, entrée ignorée."
                ))
                continue

            gt_label = f"GT {ctm_num}.{wg_num}"

            # Lot NCD
            ncd_ref = f"{REF_PREFIX}-SC{ctm_num}-GT{ctm_num}.{wg_num}-NCD"
            ncd_obj, ncd_created = Norme.objects.update_or_create(
                reference_number=ncd_ref,
                defaults={
                    'title': f"{gt_label} — Lot de {entry['ncd_count']} Normes Nationales (NCD)",
                    'description': entry['ncd_theme'],
                    'ctm': ctm,
                    'wg': wg,
                    'norm_type': 'NCD',
                    'target_count': entry['ncd_count'],
                    'status': 'DRAFT',
                }
            )
            created_count += int(ncd_created)
            updated_count += int(not ncd_created)
            totals['NCD'] += entry['ncd_count']

            # Code Applicatif / Directive / Recommandation
            other_type = entry['other_type']
            other_ref = f"{REF_PREFIX}-SC{ctm_num}-GT{ctm_num}.{wg_num}-{other_type}"
            other_obj, other_created = Norme.objects.update_or_create(
                reference_number=other_ref,
                defaults={
                    'title': entry['other_title'],
                    'description': entry['other_desc'],
                    'ctm': ctm,
                    'wg': wg,
                    'norm_type': other_type,
                    'target_count': 1,
                    'status': 'DRAFT',
                }
            )
            created_count += int(other_created)
            updated_count += int(not other_created)
            totals[other_type] += 1

            self.stdout.write(
                f"   {gt_label} ({wg.name}) : "
                f"{entry['ncd_count']} NCD + 1 {other_type}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Plan de production : {created_count} norme(s) créée(s), "
            f"{updated_count} mise(s) à jour."
        ))
        self.stdout.write(
            f"   Totaux : NCD={totals['NCD']} (cible 185), CA={totals['CA']} (cible 7), "
            f"DIR={totals['DIR']} (cible 9, le document annonce 10 — incohérence interne du PDF), "
            f"REC={totals['REC']} (cible 8)."
        )
        self.stdout.write(
            "   ℹ️  WG 4.3 « Conformité OACI » (CTM4) ne reçoit aucune entrée : "
            "pas de GT correspondant en SC4 dans ce plan (point d'arbitrage)."
        )
