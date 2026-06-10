"""
Commande de peuplement des normes ISO de la Miroiterie du Bâtiment, conformément
au "Rapport d'expertise technologique : Caractérisation physique, mécanique et
sécuritaire des vitrages selon les référentiels ISO du comité technique de la
miroiterie pour le bâtiment" (Normes ISO Miroiterie (CTM) Bâtiment.pdf).

Les 20 normes ISO/TC 160 "Glass in building" présentées dans le rapport sont
rattachées au CTM 3 "Bâtiment, Urbanisme et Transition Numérique" (ISO/TC 163)
et réparties par pertinence thématique entre ses 3 WG :

  - WG 3.1 "Habitabilité & Sécurité" (10 normes) : verre de sécurité (feuilleté,
    trempé, Heat Soak), résistance aux chocs/effractions/tempêtes — toutes les
    normes dont l'objet premier est la sécurité des personnes et des ouvrages.
  - WG 3.2 "BIM & Transition Numérique" (6 normes) : propriétés physiques de
    base, qualité dimensionnelle (verre float, verre bombé), résistance à la
    flexion et conception des façades collées (VEC) — données et méthodes de
    calcul utilisées pour la modélisation numérique des façades vitrées.
  - WG 3.3 "Performance Énergétique & Coûts" (4 normes) : caractérisation
    optique/solaire, calcul du coefficient U et durabilité de l'isolation des
    vitrages isolants.

Idempotente : `update_or_create` sur `reference_number` (préfixe
"CNETP-CTM3-ISO-").
"""

from django.core.management.base import BaseCommand
from apps.governance.models import CTM, WG
from apps.norms.models import Norme


REF_PREFIX = "CNETP-CTM3-ISO-"

# Chaque entrée correspond à l'une des 20 normes ISO du rapport d'expertise.
MIROITERIE_NORMES = [
    {
        'iso': 'ISO 12543-2:2021', 'wg': 1,
        'title': "Verre dans la construction — Verre feuilleté et verre feuilleté de "
                 "sécurité — Partie 2 : Verre feuilleté de sécurité",
        'description': "Spécifie les exigences de performance pour le verre feuilleté de "
                        "sécurité, caractérisé par sa capacité à maintenir la cohésion des "
                        "fragments en cas de rupture accidentelle ou intentionnelle. "
                        "S'applique aux vitrages exposés à des risques d'impact corporel, "
                        "de chute dans le vide ou d'effraction : base technique pour les "
                        "garde-corps vitrés, dalles de sol en verre et parois d'ascenseur.",
    },
    {
        'iso': 'ISO 12543-4:2021', 'wg': 1,
        'title': "Verre dans la construction — Verre feuilleté et verre feuilleté de "
                 "sécurité — Partie 4 : Méthodes d'essai concernant la durabilité",
        'description': "Définit les protocoles d'essais de vieillissement accéléré "
                        "(résistance à la chaleur, à l'humidité et au rayonnement UV) "
                        "nécessaires pour évaluer la stabilité thermique et chimique des "
                        "vitrages feuilletés dans le temps, en garantissant l'absence de "
                        "délamination, de bulles ou de jaunissement de l'intercalaire.",
    },
    {
        'iso': 'ISO 20492-1:2008', 'wg': 3,
        'title': "Verre dans la construction — Vitrages isolants — Partie 1 : Durabilité "
                 "des barrières d'étanchéité par essais climatiques",
        'description': "Traite de la capacité des barrières d'étanchéité périphériques des "
                        "vitrages isolants à résister à la pénétration permanente de la "
                        "vapeur d'eau, par des cycles climatiques de gel-dégel et "
                        "d'humidité élevée. Un échec présage une perte rapide des "
                        "performances d'isolation thermique par condensation interne.",
    },
    {
        'iso': 'ISO 20492-3:2010', 'wg': 3,
        'title': "Verre dans la construction — Vitrages isolants — Partie 3 : "
                 "Concentration de gaz et taux de fuite de gaz",
        'description': "Encadre la qualité de remplissage et la rétention à long terme des "
                        "gaz rares (argon, krypton, SF6) insérés dans les lames d'air des "
                        "vitrages isolants thermo-acoustiques, afin de garantir la "
                        "pérennité de l'isolation thermique globale (coefficient U) du "
                        "bâtiment.",
    },
    {
        'iso': 'ISO 11485-2:2011', 'wg': 2,
        'title': "Verre dans la construction — Verre bombé — Partie 2 : Exigences de "
                 "qualité",
        'description': "Fixe les critères de qualité d'aspect et les tolérances "
                        "géométriques (rectitude des bords, exactitude du profil de "
                        "courbure, vrillage, distorsion optique) des vitrages bombés "
                        "destinés aux façades tridimensionnelles complexes. Mesures par "
                        "gabarits d'étalonnage ou systèmes de balayage laser 3D.",
    },
    {
        'iso': 'ISO 11485-3:2014', 'wg': 1,
        'title': "Verre dans la construction — Verre bombé — Partie 3 : Exigences pour le "
                 "verre bombé trempé et le verre bombé feuilleté de sécurité",
        'description': "Spécifie les caractéristiques de sécurité et de comportement "
                        "mécanique après rupture des vitrages bombés ayant fait l'objet "
                        "d'un traitement de sécurité, pour la réception technique des "
                        "ouvrages vitrés incurvés en zones critiques (garde-corps, "
                        "verrières rampantes, ascenseurs panoramiques).",
    },
    {
        'iso': 'ISO 16293-1:2008', 'wg': 2,
        'title': "Verre dans la construction — Produits de base à partir de verre de "
                 "silicate sodo-calcique — Partie 1 : Définitions et propriétés "
                 "physiques et mécaniques générales",
        'description': "Établit les caractéristiques intrinsèques physiques et chimiques "
                        "de référence du verre sodo-calcique brut de miroiterie (masse "
                        "volumique, module d'élasticité, dureté, coefficient de dilatation "
                        "linéaire) : le dictionnaire de propriétés à partir duquel sont "
                        "paramétrées les modélisations par éléments finis des façades "
                        "vitrées.",
    },
    {
        'iso': 'ISO 16293-2:2017', 'wg': 2,
        'title': "Verre dans la construction — Produits de base à partir de verre de "
                 "silicate sodo-calcique — Partie 2 : Verre float",
        'description': "Encadre la qualité de fabrication industrielle du verre plat "
                        "transparent obtenu par flottaison (tolérances d'épaisseur et "
                        "d'équerrage, sévérité admissible des défauts ponctuels et "
                        "linéaires). Régule la qualité du substrat de base en amont de "
                        "toute transformation ultérieure (trempe, couches minces).",
    },
    {
        'iso': 'ISO 9050:2003', 'wg': 3,
        'title': "Verre dans la construction — Détermination de la transmission "
                 "lumineuse, de la transmission solaire directe, de la transmission "
                 "d'énergie solaire totale, de la transmission de l'ultraviolet et des "
                 "facteurs de vitrage connexes",
        'description': "Texte clé de la caractérisation spectrophotométrique des vitrages "
                        "(facteur solaire g, transmission lumineuse Tv, transmission UV) "
                        "pour l'analyse thermique et lumineuse des bâtiments. Fournit les "
                        "entrées indispensables à la simulation thermique dynamique et à "
                        "l'évaluation du confort d'été et d'hiver.",
    },
    {
        'iso': 'ISO 10292:1994', 'wg': 3,
        'title': "Verre dans la construction — Calcul des coefficients de transmission "
                 "thermique U en régime stationnaire des vitrages multiples",
        'description': "Décrit les règles théoriques fondamentales permettant de calculer "
                        "le coefficient de transfert thermique U en partie courante d'un "
                        "vitrage isolant, en intégrant la conduction du gaz de la cavité et "
                        "le rayonnement de surface. Permet la comparaison neutre des "
                        "performances d'isolation pour la labellisation des bâtiments.",
    },
    {
        'iso': 'ISO 12540:2017', 'wg': 1,
        'title': "Verre dans la construction — Verre de sécurité de silicate "
                 "sodo-calcique trempé thermiquement",
        'description': "Régit le verre ayant subi un procédé de chauffage suivi d'un "
                        "refroidissement brusque induisant des contraintes de compression "
                        "de surface. Définit les tolérances de déformation de trempe "
                        "(flèche locale, roller wave, edge lift) et le schéma de rupture en "
                        "fragments de petite taille et émoussés.",
    },
    {
        'iso': 'ISO 20657:2017', 'wg': 1,
        'title': "Verre dans la construction — Verre de sécurité de silicate "
                 "sodo-calcique trempé et traité Heat Soak",
        'description': "Réglemente le protocole d'essai thermique de traitement Heat Soak "
                        "(HST), appliqué au verre trempé pour éliminer le risque de casse "
                        "spontanée causée par les inclusions de sulfure de nickel. "
                        "Indispensable pour les vitrages trempés extérieurs posés en "
                        "hauteur (façades suspendues, verrières).",
    },
    {
        'iso': 'ISO 29584:2015', 'wg': 1,
        'title': "Verre dans la construction — Essais d'impact au pendule et "
                 "classification du verre de sécurité pour une utilisation dans les "
                 "bâtiments",
        'description': "Standardise les méthodes d'évaluation mécanique directe de la "
                        "sécurité des verres lors d'un choc dynamique accidentel "
                        "représentant un corps humain. Classe les verres selon la hauteur "
                        "de chute maximale résistée, pour une sélection rationnelle du "
                        "type de vitrage de sécurité selon la hauteur d'allège et "
                        "l'exposition au public.",
    },
    {
        'iso': 'ISO 28278-1:2011', 'wg': 2,
        'title': "Verre dans la construction — Produits verriers pour vitrage extérieur "
                 "collé (VEC) — Partie 1 : Produits verriers pour systèmes VEC supportés "
                 "et non supportés",
        'description': "Traite de la compatibilité et de l'aptitude à l'emploi des verres "
                        "destinés à être collés directement sur les profilés de structure "
                        "métallique sans maintien mécanique périphérique, pour la "
                        "conception et la mise en œuvre des façades rideaux en vitrage "
                        "extérieur collé (VEC). Impose des règles de rugosité et de "
                        "propreté des surfaces de collage.",
    },
    {
        'iso': 'ISO 16932:2020', 'wg': 1,
        'title': "Verre dans la construction — Vitrages de sécurité résistants aux "
                 "tempêtes de vent destructrices — Essais et classification",
        'description': "Spécifie les essais physiques requis pour s'assurer qu'un vitrage "
                        "de façade peut résister aux contraintes exceptionnelles générées "
                        "par les phénomènes cycloniques ou tornades (vent > 50 m/s) : "
                        "impact par projectile suivi de cycles de pression statique "
                        "positive et négative. Permet la construction d'infrastructures "
                        "résilientes servant d'abris d'urgence.",
    },
    {
        'iso': 'ISO 16936-1:2020', 'wg': 1,
        'title': "Verre dans la construction — Vitrages de sécurité résistants aux "
                 "infractions — Partie 1 : Essai et classification par chute répétée de "
                 "bille d'acier",
        'description': "Encadre la caractérisation de la résistance mécanique des verres "
                        "de sécurité contre les chocs d'objets durs de petite surface, par "
                        "chute répétée d'une bille d'acier de 4,11 kg depuis des hauteurs "
                        "variant de 1,5 m à 9 m. Indispensable pour la spécification "
                        "technique des vitrines de commerces et des rez-de-chaussée de "
                        "bâtiments administratifs.",
    },
    {
        'iso': 'ISO 16936-2:2005', 'wg': 1,
        'title': "Verre dans la construction — Vitrages de sécurité résistants aux "
                 "infractions — Partie 2 : Essai et classification par impacts répétés "
                 "d'un marteau et d'une hache à température ambiante",
        'description': "Régit l'évaluation de la résistance à l'effraction forcée sous "
                        "l'action d'outils à main mécaniques contondants ou tranchants, "
                        "pour les vitrages devant garantir un niveau élevé de sécurité "
                        "anti-intrusion (banques, bijouteries, sites industriels "
                        "sensibles).",
    },
    {
        'iso': 'ISO 16936-3:2005', 'wg': 1,
        'title': "Verre dans la construction — Vitrages de sécurité résistants aux "
                 "infractions — Partie 3 : Essai et classification par attaque manuelle",
        'description': "Spécifie une méthode d'évaluation physique globale simulant une "
                        "tentative d'intrusion réalisée par un opérateur humain outillé "
                        "(pied-de-biche, masses, burins), pour la qualification des "
                        "systèmes de vitrage anti-effraction hautement performants.",
    },
    {
        'iso': 'ISO 1288-2:2016', 'wg': 2,
        'title': "Verre dans la construction — Détermination de la résistance du verre à "
                 "la flexion — Partie 2 : Essai d'anneau double coaxial sur éprouvettes "
                 "planes avec de grandes surfaces d'essai",
        'description': "Définit un protocole précis d'essai de rupture pour quantifier la "
                        "résistance mécanique à la traction-flexion intrinsèque du verre, "
                        "en dehors de toute influence des bords. Fournit les données de "
                        "résistance utilisées en R&D, en contrôle qualité et pour "
                        "calibrer les coefficients de calcul élastique et les lois "
                        "statistiques de Weibull.",
    },
    {
        'iso': 'ISO 1288-3:2016', 'wg': 2,
        'title': "Verre dans la construction — Détermination de la résistance du verre à "
                 "la flexion — Partie 3 : Essai sur éprouvette supportée en deux points "
                 "(flexion en quatre points)",
        'description': "Décrit l'évaluation de la résistance mécanique à la flexion du "
                        "verre plat en intégrant explicitement l'influence de la qualité "
                        "de façonnage des bords de l'éprouvette (joints plats polis, "
                        "joints abattus, trous, découpes). Fondamentale pour valider que "
                        "le façonnage industriel des bords n'introduit pas de "
                        "microfissures susceptibles de provoquer une rupture.",
    },
]


class Command(BaseCommand):
    help = (
        "Peuple les 20 normes ISO de la Miroiterie du Bâtiment (CTM3), réparties "
        "entre WG3.1 (Habitabilité & Sécurité), WG3.2 (BIM & Transition Numérique) "
        "et WG3.3 (Performance Énergétique & Coûts) selon le rapport d'expertise "
        "« Normes ISO Miroiterie (CTM) Bâtiment »."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Peuplement des normes ISO de la Miroiterie du Bâtiment (CTM3) ==="
        ))

        ctm3 = CTM.objects.get(number=3)

        created_count = 0
        updated_count = 0
        per_wg = {}

        for entry in MIROITERIE_NORMES:
            wg_num = entry['wg']
            try:
                wg = WG.objects.get(ctm=ctm3, number=wg_num)
            except WG.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️ WG 3.{wg_num} introuvable, norme {entry['iso']} ignorée."
                ))
                continue

            ref = REF_PREFIX + entry['iso'].replace('ISO ', '').replace(':', '-')
            obj, created = Norme.objects.update_or_create(
                reference_number=ref,
                defaults={
                    'title': entry['title'],
                    'description': entry['description'],
                    'ctm': ctm3,
                    'wg': wg,
                    'iso_reference': entry['iso'],
                    'norm_type': 'NCD',
                    'target_count': 1,
                    'status': 'DRAFT',
                    'tags': 'Miroiterie, Vitrage, Verre, ISO/TC 160, Bâtiment',
                }
            )
            created_count += int(created)
            updated_count += int(not created)
            per_wg[wg_num] = per_wg.get(wg_num, 0) + 1

            status = "✓ créée" if created else "• mise à jour"
            self.stdout.write(f"   {status} : {entry['iso']} -> WG 3.{wg_num} ({wg.name})")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Miroiterie : {created_count} norme(s) créée(s), "
            f"{updated_count} mise(s) à jour."
        ))
        self.stdout.write(
            "   Répartition : "
            + ", ".join(f"WG3.{wg_num}={count}" for wg_num, count in sorted(per_wg.items()))
        )
