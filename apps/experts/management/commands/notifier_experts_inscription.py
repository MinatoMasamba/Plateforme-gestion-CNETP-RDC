"""
Commande de diffusion : invite les 200 Experts mandatés du Collège CNE-ITP
à procéder à leur inscription officielle sur la plateforme, par email et WhatsApp.

Usage :
    python manage.py notifier_experts_inscription
    python manage.py notifier_experts_inscription --lien https://cnetp.cd/inscription
    python manage.py notifier_experts_inscription --dry-run
"""

import json
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Liste des Experts à notifier : un dictionnaire par personne.
# Champs attendus : "nom", "email" (optionnel) et "telephone" (optionnel,
# format local 0XXXXXXXXX ou international +243XXXXXXXXX).
# ---------------------------------------------------------------------------
EXPERTS = [
    {"nom": "Gradi BANINGIME KEBWIJINA",            "email": "gradibaningime@gmail.com",           "telephone": "0811629997"},
    {"nom": "Alex Katembo Lungili",                  "email": "katembo.lungili@inbtp.ca.cd",        "telephone": "0974543722"},
    {"nom": "Obed Dawily Sido",                      "email": "ddawinobed@gmail.com",               "telephone": "0822650564"},
    {"nom": "GABAIN MULOWAYI Kankolongo",            "email": "gabaindgmk@hotmail.com",             "telephone": "0849116196"},
    {"nom": "GAËL MULUA MASSAMBA",                   "email": "gagabeatitude@gmail.com",            "telephone": "0896001751"},
    {"nom": "John MUTUMBI BAKONGO",                  "email": "johnmutumbi3@gmail.com",             "telephone": "0812927172"},
    {"nom": "ANDRE NTELA TAYEYE",                    "email": "atayeye@gmx.com",                    "telephone": "8733557798"},
    {"nom": "MARTIN SHIMBULA MALAMBA",               "email": "shimbulam@gmail.com",                "telephone": "2438989171"},
    {"nom": "Kevine Mukoko Mwamba",                  "email": "kevinemukoko8@gmail.com",            "telephone": "0892539045"},
    {"nom": "Elias KISEMBO BYAKISAKA",               "email": "kisemboelias640@gmail.com",          "telephone": "0816948165"},
    {"nom": "Pierrot Ilunga Mwamba",                 "email": "pierrot.ilunga@gmail.com",           "telephone": "0818593518"},
    {"nom": "Pierre Asabi Kwagba",                   "email": "asabipierre3@gmail.com",             "telephone": "0817128897"},
    {"nom": "Hector Mbuse Monaka",                   "email": "hectormbuse@gmail.com",              "telephone": "0810152325"},
    {"nom": "Zatus KIAKU MBULU",                     "email": "zatuskiakuzk@gmail.com",             "telephone": "0898979000"},
    {"nom": "Frédéric BAWILU MAFUTA",                "email": "bamafuta@gmail.com",                 "telephone": "0783986340"},
    {"nom": "Serge Banza Makoy",                     "email": "sergebanza@gmail.com",               "telephone": "0830280514"},
    {"nom": "AMBROISE LUKOKI LUA MBOZI",             "email": "ambluambozi@gmail.com",              "telephone": "0822992654"},
    {"nom": "Glody Baang'osema Basele",              "email": "glodybasele@gmail.com",              "telephone": "0820460206"},
    {"nom": "MICHEL WANGU BOFOTOLA",                 "email": "michewangu243@gmail.com",            "telephone": "0891037682"},
    {"nom": "LIONNEL MUSANGU TSHIMBALANGA",          "email": "musangulionnel@gmail.com",           "telephone": "0990022153"},
    {"nom": "Simon Barnabas PAKU MATONDO",           "email": "pakumatondosimon@yahoo.com",         "telephone": "0998178399"},
    {"nom": "Judith Bwalelo Wabenia",                "email": "judith.bwalelo@foner.cd",            "telephone": "0821242490"},
    {"nom": "Pascal BULONGO PYANA YUNDI",            "email": "bulongopasca6@gmail.com",            "telephone": "0813288894"},
    {"nom": "Noviski Mathe Matimbia",                "email": "noviski.mathe20@gmail.com",          "telephone": "0997494039"},
    {"nom": "Alain Selembe Musindo",                 "email": "selembealain7@gmail.com",            "telephone": "0822976334"},
    {"nom": "RUDY ALONDA KYATANGALWA",               "email": "rudyalonda@gmail.com",               "telephone": "0812759238"},
    {"nom": "Steve TSHITENDE Wa TSHITENDE",          "email": "stevetshitende6@gmail.com",          "telephone": "0998884114"},
    {"nom": "THEONESTE RUVIRI KANANI",               "email": "theoneste.ruviri@acgt.cd",           "telephone": "0998278888"},
    {"nom": "Vital Musungaie Tshitundu",             "email": "xyzconceptinfo@gmail.com",           "telephone": "0906763694"},
    {"nom": "Lucien BATULI NKASANGALI",              "email": "lucien.batuli@celluleinfra.org",     "telephone": "0814002009"},
    {"nom": "Flore Wondozu Langabay",                "email": "falngosl@gmail.com",                 "telephone": "0811908890"},
    {"nom": "Azarias Fiston Mwatoike Ligbakelo",     "email": "aligbakelo@gmail.com",               "telephone": "0814164199"},
    {"nom": "Xavier SAKA-SAKA NGALA",                "email": "entrecarconstruct2@gmail.com",       "telephone": "0851319382"},
    {"nom": "Theophile Matondo Mbungu",              "email": "matondotheo@gmail.com",              "telephone": "0999945694"},
    {"nom": "Kizito MATABARO KIZITO",                "email": "kizito.matabaro@anat.gouv.cd",       "telephone": "0995797970"},
    {"nom": "Christian Mafolo Mfumu",                "email": "chogamaf@gmail.com",                 "telephone": "0824045905"},
    {"nom": "Espérant Daniel KAMBULU MANGENDA",      "email": "edkambulu@gmail.com",                "telephone": "0998601800"},
    {"nom": "Fabien LASANGA NDASA",                  "email": "fabienlasanga@gmail.com",            "telephone": "0988667133"},
    {"nom": "Jean Paul Nyembo Tampakanya",           "email": "nyembojeanpaul@gmail.com",           "telephone": "2438137652"},
    {"nom": "Yves UTUBULA NZUNDU",                   "email": "yves.utubula@anat.gouv.cd",          "telephone": "0998322446"},
    {"nom": "Leroi KANGULUMBA Zola",                 "email": "leroi.kangulumba@unikin.ac.cd",      "telephone": "0810387724"},
    {"nom": "Guelord MBUNGA SIMISI",                 "email": "guelordmbunga@gmail.com",            "telephone": "0821016667"},
    {"nom": "Josaphat Mukala Mulumba",               "email": "josaphatmukala@gmail.com",           "telephone": "0814217332"},
    {"nom": "Josué Wandje Owamba",                   "email": "josuewandje.340@gmail.com",          "telephone": "0844369608"},
    {"nom": "Freddy KAZADI KAMUANGA",                "email": "eceat.rdc@gmail.com",                "telephone": "0815112881"},
    {"nom": "Rosine NGALULA KALANDA",                "email": "rosinengalula@gmail.com",            "telephone": "0990736426"},
    {"nom": "Patrick Kibangu Mampuya",               "email": "kbgm2002@gmail.com",                 "telephone": "0899222367"},
    {"nom": "CHRISPIN ZIGABE MUHIRWA",               "email": "zigabe.muhirwa@ucbukavu.ac.cd",      "telephone": "0991760057"},
    {"nom": "BOBO BONKOTSHI BONGOY",                 "email": "bobobonkotshi@gmail.com",            "telephone": "0811414379"},
    {"nom": "ChrisBardol Ngindu Wa ngindu",          "email": "chrisbardolngindu@gmail.com",        "telephone": "0998147738"},
    {"nom": "Joseph Bamenikio Kuelumuenamo",         "email": "bamenikioj@gmail.com",               "telephone": "0899808307"},
    {"nom": "Christ NSIMBULU MASSAMBA",              "email": "nsimbuluc@gmail.com",                "telephone": "0822208148"},
    {"nom": "CHARLES MIKWARI NGAL",                  "email": "mikwaricharles01@gmail.com",         "telephone": "0815016982"},
    {"nom": "René Mpuru Mazembe",                    "email": "rempuru@yaoo.fr",                    "telephone": "0998173334"},
    {"nom": "Delmas Ntendayi Biaya",                 "email": "delmasntendayi@gmail.com",           "telephone": "0998143261"},
    {"nom": "Samuel Ndengani Monzele",               "email": "samy_ndengani@yahoo.fr",             "telephone": "0999949330"},
    {"nom": "Papy Fataki Lukumu",                    "email": "pafataki@gmail.com",                 "telephone": "0816917321"},
    {"nom": "Parfait Mutambay Muaba",                "email": "romanickparfait@gmail.com",          "telephone": "0824988937"},
    {"nom": "Enock SANGANA MALONDA WASOLUA",         "email": "sanganaenock@gmail.com",             "telephone": "0981439157"},
    {"nom": "Papy KABADI LELO ODIMBA",               "email": "papykabadi8@gmail.com",              "telephone": "0823849427"},
    {"nom": "Flory Mbuyi Mutumba",                   "email": "mbuyiflory320@gmail.com",            "telephone": "0812018713"},
    {"nom": "Corneille Muntenge Iboy",               "email": "corneillemuntenge@gmail.com",        "telephone": "0812199270"},
    {"nom": "Julien SANIMOTO GBANZI",                "email": "juliensanimoto@gmail.com",           "telephone": "0810085089"},
    {"nom": "CHRISTIAN MUNIAMPALA LESUYA",           "email": "muniampalalesuya@yahoo.fr",          "telephone": "0896074153"},
    {"nom": "Floribert MUKENDI Mpoyi",               "email": "floribertmukendi61@gmail.com",       "telephone": "0819942091"},
    {"nom": "Michel Miseka Mubake",                  "email": "michelmiseka6@gmail.com",            "telephone": "0813339200"},
    {"nom": "Michel WANGU Bofotola",                 "email": "michelwangu243@gmail.com",           "telephone": "0891037682"},
    {"nom": "Joseph Nkayilu Lumbanzu",               "email": "josephnkayilu0@gmail.com",           "telephone": "0815048488"},
    {"nom": "Jean Marie Bena Diakiese",              "email": "Jeanmarie_bena@yahoo.fr",            "telephone": "0815024801"},
    {"nom": "Désire Loole Babongola",                "email": "omeringconstruction@yahoo.com",      "telephone": "0814264302"},
    {"nom": "Yannick Kindimbu Matondo",              "email": "yanarckindimbu@gmail.com",           "telephone": "0821001669"},
    {"nom": "Innocent LOHAYO LOMEMA",                "email": "innocentlomema@gmail.com",           "telephone": "0813311773"},
    {"nom": "Belinda Betuku Nkoy",                   "email": "belindabetuku1@gmail.com",           "telephone": "0828462360"},
    {"nom": "Jérôme Kazambu Ditu",                   "email": "jerokaz01@gmail.com",                "telephone": "0815795201"},
    {"nom": "Tshise TSHISEKEDI KALADI",              "email": "tshisetshisekedi864@gmail.com",      "telephone": "0903455085"},
    {"nom": "Flory MAMPIA NSANGA",                   "email": "mampiaflory@gmail.com",              "telephone": "0817675875"},
    {"nom": "Dieudonné Bambu Ndombasi",              "email": "dieudonnebambu72@gmail.com",         "telephone": "0993406486"},
    {"nom": "Daniel KAZADI CIBUMBU",                 "email": "kazadidaniel676@gmail.com",          "telephone": "0818503677"},
    {"nom": "Arnhold MUKEBAYI Kabanga",              "email": "arnholdmukebayi@gmail.com",          "telephone": "0811637879"},
    {"nom": "Péguy Malu Ngalamulume",                "email": "peguymalu@gmail.com",                "telephone": "0859001747"},
    {"nom": "Annie Ntumba Lusamba",                  "email": "anniellakadima28@gmail.com",         "telephone": "0986118610"},
    {"nom": "Alexandre Tshiamala Wa Tshiamala",      "email": "alextshamala@gmail.com",             "telephone": "0998119854"},
    {"nom": "Leon Levo Nakanza",                     "email": "levo.leon@gmail.com",                "telephone": "0810061018"},
    {"nom": "Christian Esiki Yolo",                  "email": "sydneyesiki@gmail.com",              "telephone": "0819517278"},
    {"nom": "GUY LAROCHE NGWAMA PERO",               "email": "larochengwama@gmail.com",            "telephone": "0892102765"},
    {"nom": "Mymmon Kilunga Nsenga",                 "email": "perspective.afr@gmail.com",          "telephone": "0816890271"},
    {"nom": "Anatol Mpungu Mpungu",                  "email": "mpunguanatol@gmail.com",             "telephone": "0817121076"},
    {"nom": "Patrick Ilho Kituba",                   "email": "archikituba@gmail.com",              "telephone": "0851320482"},
    {"nom": "Patrick KAKU MAKAMBO",                  "email": "kakupatrick87@gmail.com",            "telephone": "0896480552"},
    {"nom": "Joseph Nono NKIERE NANA",               "email": "nkierenana@yahoo.com",               "telephone": "0823051460"},
    {"nom": "Jeancy Tshiamala Kumwamba",             "email": "Kumwamba2006@gmail.com",             "telephone": "0820871187"},
    {"nom": "François Kangela Kanku",                "email": "francoiskangela2@gmail.com",         "telephone": "0897000135"},
    {"nom": "DANIEL KIBIKONDA LUIZI",                "email": "daniel.kibikonda@gmail.com",         "telephone": "0991808379"},
    {"nom": "Nkashamba Kazadi N'as",                 "email": "tjflykazadi@gmail.com",              "telephone": "0815829861"},
    {"nom": "KADIMA-MBUYI MULAMBULA CIAKATUMBA",     "email": "s2001k14@gmail.com",                 "telephone": "0814315127"},
    {"nom": "Eric LUAYI NKELE",                      "email": "ericluayi2016@gmail.com",            "telephone": "0855280363"},
    {"nom": "Z Vangu Zola",                          "email": "vanguzola@gmail.com",                "telephone": "0818008067"},
    {"nom": "Blaise LUEMBA MAMONIKA",                "email": "luembablaiseluemba@gmail.com",       "telephone": "0898011141"},
    {"nom": "Deborah Omoyi Pongombo",                "email": "omoyiandrea@gmail.com",              "telephone": "0820182497"},
    {"nom": "Israël-Tshany BENDERA MUSANGANI",       "email": "istshany_bend@yahoo.fr",             "telephone": "0998193627"},
    {"nom": "RODRIGUE MAMBUENI NTIMANSIEMI",         "email": "rmnsj1@gmail.com",                   "telephone": "0815844637"},
    {"nom": "Emmanuel Mwila Kibwe",                  "email": "emmanuel.mwila@foner.cd",            "telephone": "0814067413"},
    {"nom": "Michel Uyumbu Soko longe",              "email": "micheluyumbu2021@gmail.com",         "telephone": "0817793505"},
    {"nom": "Ben CIEPELA NGOY",                      "email": "bengoy@outlook.com",                 "telephone": "0999997290"},
    {"nom": "Winner Mapanda Balinga",                "email": "winner.mapanda@foner.cd",            "telephone": "0973006030"},
    {"nom": "Jules NKOMBWA KABOFI",                  "email": "gectopoplus@gmail.com",              "telephone": "0815007746"},
    {"nom": "CHRISTIAN ACIZA CUBAKA",                "email": "christianaciza@gmail.com",           "telephone": "0994577416"},
    {"nom": "Guelord MPIA BOLIPUA",                  "email": "guelordboli@gmail.com",              "telephone": "0811485775"},
    {"nom": "Jean Marie N'SAPU KUMWAMBA",            "email": "gtnconstruct@gmail.com",             "telephone": "0991003456"},
    {"nom": "Christian Kyalumba Makindu",            "email": "chkyamak1@gmail.com",                "telephone": "0999927990"},
    {"nom": "Jean de Dieu BOBO KOEBONI",             "email": "bobojeandedieu@gmail.com",           "telephone": "0816422014"},
    {"nom": "Roger Vibila Kandu Mayi",               "email": "rgvibila@holops.com",                "telephone": "0816861660"},
    {"nom": "ERIC KIBALA PALA",                      "email": "kibalaeric01@gmail.com",             "telephone": "0999943140"},
    {"nom": "Yves Ngoma Muzola",                     "email": "yvesmuzola@gmail.com",               "telephone": "0991407271"},
    {"nom": "Gabriel Zaatcha KAZADI MUHOLA LASER",   "email": "laser.muhola@anat.gouv.cd",          "telephone": "0891558686"},
    {"nom": "Alpha Memidra Egbango Mapoko Isongo",   "email": "alpha.egbango@celluleinfra.org",     "telephone": "0819823416"},
    {"nom": "WIREN MONDU KITSHIAKA",                 "email": "wiren.mondu@celluleinfra.org",       "telephone": "0810722822"},
    {"nom": "CHICO MWADI VUZUNGA",                   "email": "mwadivuzungachico@gmail.com",        "telephone": "0819090470"},
    {"nom": "Guycele Malabi Mpioko",                 "email": "celemalabi@gmail.com",               "telephone": "0810622671"},
    {"nom": "Jean Bosco Bifulu Malele",              "email": "bifuluscolie2014@gmail.com",         "telephone": "0814029156"},
    {"nom": "Olivier ROGHO PASHO-LAWATA",            "email": "oliverutche@gmail.com",              "telephone": "0824376306"},
    {"nom": "Ralph Bizongo Désiré",                  "email": "desire.bizongo@celluleinfra.org",    "telephone": "0979059000"},
    {"nom": "Romain Bussa Mbule",                    "email": "romainlandry.bussa@gmail.com",       "telephone": "0853683861"},
    {"nom": "Didier Kamunga Mukendi",                "email": "kamungadidier@yahoo.fr",             "telephone": "0994744092"},
    {"nom": "Willy VALE MANGA",                      "email": "willy.vale@inbtp.ac.cd",             "telephone": "0971550108"},
    {"nom": "Pires LISINGO TOFOFA",                  "email": "pireslisingo@gmail.com",             "telephone": "0812153345"},
    {"nom": "Doris Kayamba Kilungu",                 "email": "kayambakilungudoris@gmail.com",      "telephone": "0897956637"},
    {"nom": "Chadrack Ngoie Mutambayi",              "email": "ngoiechadrack2@gmail.com",           "telephone": "0892256018"},
    {"nom": "Nicolas NSAMBA KABALA",                 "email": "nsambanicolas24@gmail.com",          "telephone": "0825835007"},
]

LIEN_INSCRIPTION_PAR_DEFAUT = "[Insérer le lien ici]"

SUJET_EMAIL = "🇨🇩 CNE-ITP — Invitation à votre inscription officielle (Collège des 200 Experts)"

MESSAGE_TEMPLATE = """🇨🇩 MINISTERE DES INFRASTRUCTURES ET TRAVAUX PUBLICS 🇨🇩
Commission Nationale pour la création des Normes de Construction (CNE-ITP)
Pour les Honorables Experts Mandatés (Collège des 200)

Honorables Experts, Chers Collègues,

Au nom de la Haute Coordination Générale et du Secrétariat Général aux ITP, nous vous présentons nos civilités les plus distinguées.

Suite à votre désignation officielle par vos structures respectives (Cabinets, Secrétariats Généraux, Offices, Ordres Professionnels, Institutions Académiques et Secteur Privé), vous faites désormais partie intégrante de la configuration élargie des 200 Experts de la CNE-ITP.

Afin de finaliser la cartographie de mise en place administrative et de valider votre affectation fonctionnelle au sein de chaque instance (Comité de Pilotage, Cellule Technique de Coordination ou Comités Techniques Miroirs - CTM), vous êtes priés de procéder ce jour à votre inscription officielle sur la plateforme numérique de la Commission.

🔗 Lien pour votre inscription : 👉 {lien}

Note importante : Lors de cette démarche, veillez à renseigner avec exactitude votre structure de provenance et le profil technique correspondant au poste qui vous est réservé. Votre participation active constitue le garant scientifique du futur Référentiel Normatif National du Génie Civil en République Démocratique du Congo.

Pour toute assistance technique durant votre enregistrement, le Service de Support Technique et Numérique reste à votre entière disposition.

Avec nos remerciements anticipés pour votre promptitude et votre sens élevé du devoir national.

Veuillez agréer, Honorables Experts, notre haute considération patriotique.

La Cellule Technique de Coordination (CTC)
Secrétariat Général aux ITP / Direction de la Réglementation et des Normes.
📍 Lingwala, Kinshasa, RDC."""


def whatsapp_configure():
    return bool(
        settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM
    )


def normaliser_numero_whatsapp(numero):
    """Convertit un numéro local congolais (0XXXXXXXXX) au format E.164 (+243XXXXXXXXX)."""
    numero = numero.strip().replace(" ", "")
    if numero.startswith("+"):
        return numero
    if numero.startswith("0"):
        return "+243" + numero[1:]
    return "+" + numero


def whatsapp_from():
    expediteur = settings.TWILIO_WHATSAPP_FROM.strip()
    if expediteur.startswith("whatsapp:"):
        return expediteur
    return f"whatsapp:{expediteur}"


def envoyer_whatsapp(client, numero, message):
    client.messages.create(
        from_=whatsapp_from(),
        to=f"whatsapp:{normaliser_numero_whatsapp(numero)}",
        body=message,
    )


class Command(BaseCommand):
    help = (
        "Envoie à chaque Expert du Collège des 200 (liste EXPERTS) une invitation "
        "à s'inscrire sur la plateforme CNE-ITP, par email et par WhatsApp."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lien",
            type=str,
            default=None,
            help="Lien d'inscription à insérer dans le message (sinon valeur par défaut).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait envoyé sans rien envoyer réellement.",
        )

    def handle(self, *args, **options):
        if not EXPERTS:
            self.stdout.write(self.style.WARNING(
                "⚠️  La liste EXPERTS est vide — renseignez-la dans "
                "apps/experts/management/commands/notifier_experts_inscription.py avant de relancer."
            ))
            return

        lien = options["lien"] or LIEN_INSCRIPTION_PAR_DEFAUT
        message = MESSAGE_TEMPLATE.format(lien=lien)
        dry_run = options["dry_run"]

        client = None
        if not dry_run and whatsapp_configure():
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        elif not dry_run:
            self.stdout.write(self.style.WARNING(
                "⚠️  Twilio non configuré (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / "
                "TWILIO_WHATSAPP_FROM) — les messages WhatsApp seront seulement journalisés."
            ))

        emails_ok, emails_ko = 0, 0
        wa_ok, wa_ko = 0, 0

        for expert in EXPERTS:
            nom = expert.get("nom", "Honorable Expert")
            email = (expert.get("email") or "").strip()
            telephone = (expert.get("telephone") or "").strip()

            if email:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Email → {nom} <{email}>")
                else:
                    try:
                        send_mail(
                            subject=SUJET_EMAIL,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        emails_ok += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ Email envoyé à {nom} <{email}>"))
                    except Exception:
                        emails_ko += 1
                        logger.exception("Échec de l'envoi de l'email à %s <%s>", nom, email)
                        self.stdout.write(self.style.ERROR(f"❌ Échec email pour {nom} <{email}>"))

            if telephone:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] WhatsApp → {nom} <{telephone}>")
                else:
                    try:
                        if client is not None:
                            envoyer_whatsapp(client, telephone, message)
                        else:
                            logger.info(
                                "WhatsApp non configuré — message simulé pour %s <%s> : %s",
                                nom, telephone, message,
                            )
                        wa_ok += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp envoyé à {nom} <{telephone}>"))
                    except Exception:
                        wa_ko += 1
                        logger.exception("Échec de l'envoi WhatsApp à %s <%s>", nom, telephone)
                        self.stdout.write(self.style.ERROR(f"❌ Échec WhatsApp pour {nom} <{telephone}>"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"📧 Emails  : {emails_ok} envoyé(s), {emails_ko} échec(s)"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"📱 WhatsApp: {wa_ok} envoyé(s), {wa_ko} échec(s)"
        ))
        self.stdout.write("=" * 60 + "\n")
