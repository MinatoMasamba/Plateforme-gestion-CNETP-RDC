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
# Champs attendus : "nom", "email" ou "mail" (optionnel) et "telephone" ou
# "numero" (optionnel, format local 0XXXXXXXXX ou international +243XXXXXXXXX).
# ---------------------------------------------------------------------------
EXPERTS =  [
  {
    "nom": "Gisele Miezi Nsiangani",
    "mail": "etudes@miezihomedesigns.fr",
    "numero": "0749994076"
  },
  {
    "nom": "Richard  MBIVANGA  VIBILA ",
    "mail": "ricvibila@gmail.com",
    "numero": "0815013531"
  },
  {
    "nom": "Meck Mukendi  Mukendi",
    "mail": "mukendimeck25@gmail.com",
    "numero": "0999976719"
  },
  {
    "nom": "Meck Mukendi  Mukendi",
    "mail": "mukendimeck25@gmail.com",
    "numero": "0999976719"
  },
  {
    "nom": "Luc Miteo Mwamba",
    "mail": "lucmwamba77@gmail.com",
    "numero": "8200022792"
  },
  {
    "nom": "PAPY MAYOYE KANGUDI",
    "mail": "mayoye@langageo.co.za",
    "numero": "0832557444"
  },
  {
    "nom": "Gradi KEBWIJINA  BANINGIME ",
    "mail": "gradibaningime@gmail.com",
    "numero": "0811629997"
  },
  {
    "nom": "Alex Lungili Katembo",
    "mail": "katembo.lungili@inbtp.ca.cd",
    "numero": "0974543722"
  },
  {
    "nom": "Obed Sido Dawily",
    "mail": "ddawinobed@gmail.com",
    "numero": "0822650564"
  },
  {
    "nom": "GABAIN Kankolongo MULOWAYI",
    "mail": "gabaindgmk@hotmail.com",
    "numero": "0849116196"
  },
  {
    "nom": "GAËL  MASSAMBA  MULUA",
    "mail": "gagabeatitude@gmail.com",
    "numero": "0896001751"
  },
  {
    "nom": "John BAKONGO MUTUMBI",
    "mail": "johnmutumbi3@gmail.com",
    "numero": "0812927172"
  },
  {
    "nom": "ANDRE TAYEYE NTELA",
    "mail": "atayeye@gmx.com",
    "numero": "8733557798"
  },
  {
    "nom": "ANDRE TAYEYE NTELA",
    "mail": "atayeye@gmx.com",
    "numero": "8733557798"
  },
  {
    "nom": "ANDRE TAYEYE NTELA",
    "mail": "atayeye@gmx.com",
    "numero": "8733557798"
  },
  {
    "nom": "ANDRE TAYEYE NTELA",
    "mail": "atayeye@gmx.com",
    "numero": "8733557798"
  },
  {
    "nom": "ANDRE TAYEYE NTELA",
    "mail": "atayeye@gmx.com",
    "numero": "8733557798"
  },
  {
    "nom": "MARTIN  MALAMBA SHIMBULA ",
    "mail": "shimbulam@gmail.com",
    "numero": "2438989171"
  },
  {
    "nom": "Kevine Mwamba  Mukoko ",
    "mail": "kevinemukoko8@gmail.com",
    "numero": "0892539045"
  },
  {
    "nom": "Elias BYAKISAKA  KISEMBO ",
    "mail": "kisemboelias640@gmail.com",
    "numero": "0816948165"
  },
  {
    "nom": "Pierrot Mwamba Ilunga",
    "mail": "pierrot.ilunga@gmail.com",
    "numero": "0818593518"
  },
  {
    "nom": "Pierrot Mwamba Ilunga",
    "mail": "pierrot.ilunga@gmail.com",
    "numero": "0818593518"
  },
  {
    "nom": "Pierrot Mwamba Ilunga",
    "mail": "pierrot.ilunga@gmail.com",
    "numero": "0818593518"
  },
  {
    "nom": "Pierrot Mwamba Ilunga",
    "mail": "pierrot.ilunga@gmail.com",
    "numero": "0818593518"
  },
  {
    "nom": "Pierre Kwagba  Asabi ",
    "mail": "asabipierre3@gmail.com",
    "numero": "0817128897"
  },
  {
    "nom": "Hector  Monaka  Mbuse ",
    "mail": "hectormbuse@gmail.com",
    "numero": "0810152325"
  },
  {
    "nom": "Hector  Monaka  Mbuse ",
    "mail": "hectormbuse@gmail.com",
    "numero": "0810152325"
  },
  {
    "nom": "Zatus MBULU  KIAKU ",
    "mail": "zatuskiakuzk@gmail.com",
    "numero": "0898979000"
  },
  {
    "nom": "Frédéric  MAFUTA BAWILU ",
    "mail": "bamafuta@gmail.com",
    "numero": "0783986340"
  },
  {
    "nom": "Serge Makoy Banza",
    "mail": "sergebanza@gmail.com",
    "numero": "0830280514"
  },
  {
    "nom": "AMBROISE LUA MBOZI LUKOKI",
    "mail": "ambluambozi@gmail.com",
    "numero": "0822992654"
  },
  {
    "nom": "Glody  Basele  Baang’osema ",
    "mail": "glodybasele@gmail.com",
    "numero": "0820460206"
  },
  {
    "nom": "MICHEL BOFOTOLA WANGU",
    "mail": "michewangu243@gmail.com",
    "numero": "0891037682"
  },
  {
    "nom": "LIONNEL TSHIMBALANGA MUSANGU",
    "mail": "musangulionnel@gmail.com",
    "numero": "0990022153"
  },
  {
    "nom": "Simon Barnabas MATONDO PAKU",
    "mail": "pakumatondosimon@yahoo.com",
    "numero": "0998178399"
  },
  {
    "nom": "Judith  Wabenia  Bwalelo ",
    "mail": "judith.bwalelo@foner.cd",
    "numero": "0821242490"
  },
  {
    "nom": "Pascal PYANA YUNDI BULONGO",
    "mail": "bulongopasca6@gmail.com",
    "numero": "0813288894"
  },
  {
    "nom": "Noviski Matimbia  Mathe ",
    "mail": "noviski.mathe20@gmail.com",
    "numero": "0997494039"
  },
  {
    "nom": "Alain Musindo Selembe",
    "mail": "selembealain7@gmail.com",
    "numero": "0822976334"
  },
  {
    "nom": "RUDY KYATANGALWA ALONDA",
    "mail": "rudyalonda@gmail.com",
    "numero": "0812759238"
  },
  {
    "nom": "Steve  Wa TSHITENDE  TSHITENDE ",
    "mail": "stevetshitende6@gmail.com",
    "numero": "0998884114"
  },
  {
    "nom": "THEONESTE KANANI RUVIRI",
    "mail": "theoneste.ruviri@acgt.cd",
    "numero": "0998278888"
  },
  {
    "nom": "Vital Tshitundu Musungaie",
    "mail": "xyzconceptinfo@gmail.com",
    "numero": "0906763694"
  },
  {
    "nom": "Lucien NKASANGALI BATULI",
    "mail": "lucien.batuli@celluleinfra.org",
    "numero": "0814002009"
  },
  {
    "nom": "Flore Langabay Wondozu",
    "mail": "falngosl@gmail.com",
    "numero": "0811908890"
  },
  {
    "nom": "Azarias Fiston  Ligbakelo  Mwatoike ",
    "mail": "aligbakelo@gmail.com",
    "numero": "0814164199"
  },
  {
    "nom": "Xavier  NGALA SAKA-SAKA ",
    "mail": "entrecarconstruct2@gmail.com",
    "numero": "0851319382"
  },
  {
    "nom": "Theophile  Mbungu  Matondo ",
    "mail": "matondotheo@gmail.com",
    "numero": "0999945694"
  },
  {
    "nom": "Kizito  KIZITO MATABARO ",
    "mail": "kizito.matabaro@anat.gouv.cd",
    "numero": "0995797970"
  },
  {
    "nom": "Kizito  KIZITO MATABARO",
    "mail": "kizito.matabaro@anat.gouv.cd",
    "numero": "0995797970"
  },
  {
    "nom": "Kizito  KIZITO MATABARO ",
    "mail": "kizito.matabaro@anat.gouv.cd",
    "numero": "0995797970"
  },
  {
    "nom": "Steve Wa Tshitende Tshitende",
    "mail": "stevetshitende6@gmail.com",
    "numero": "0998884114"
  },
  {
    "nom": "Christian  Mfumu  Mafolo ",
    "mail": "chogamaf@gmail.com",
    "numero": "0824045905"
  },
  {
    "nom": "Espérant Daniel  MANGENDA  KAMBULU ",
    "mail": "edkambulu@gmail.com",
    "numero": "0998601800"
  },
  {
    "nom": "Kizito  KIZITO MATABARO ",
    "mail": "kizito.matabaro@anat.gouv.cd",
    "numero": "0995797970"
  },
  {
    "nom": "Fabien  NDASA  LASANGA ",
    "mail": "fabienlasanga@gmail.com",
    "numero": "0988667133"
  },
  {
    "nom": "Jean Paul  Tampakanya  Nyembo ",
    "mail": "nyembojeanpaul@gmail.com",
    "numero": "2438137652"
  },
  {
    "nom": "Yves  NZUNDU  UTUBULA ",
    "mail": "yves.utubula@anat.gouv.cd",
    "numero": "0998322446"
  },
  {
    "nom": "Leroi Zola  KANGULUMBA ",
    "mail": "leroi.kangulumba@unikin.ac.cd",
    "numero": "0810387724"
  },
  {
    "nom": "Guelord SIMISI MBUNGA",
    "mail": "guelordmbunga@gmail.com",
    "numero": "0821016667"
  },
  {
    "nom": "Josaphat Mulumba Mukala",
    "mail": "josaphatmukala@gmail.com",
    "numero": "0814217332"
  },
  {
    "nom": "Josaphat Mulumba Mukala",
    "mail": "josaphatmukala@gmail.com",
    "numero": "0814217332"
  },
  {
    "nom": "Josué Owamba Wandje",
    "mail": "josuewandje.340@gmail.com",
    "numero": "0844369608"
  },
  {
    "nom": "Freddy KAMUANGA KAZADI",
    "mail": "eceat.rdc@gmail.com",
    "numero": "0815112881"
  },
  {
    "nom": "Rosine  KALANDA  NGALULA ",
    "mail": "rosinengalula@gmail.com",
    "numero": "0990736426"
  },
  {
    "nom": "Patrick  Mampuya  Kibangu ",
    "mail": "kbgm2002@gmail.com",
    "numero": "0899222367"
  },
  {
    "nom": "CHRISPIN MUHIRWA ZIGABE",
    "mail": "zigabe.muhirwa@ucbukavu.ac.cd",
    "numero": "0991760057"
  },
  {
    "nom": "BOBO BONGOY BONKOTSHI",
    "mail": "bobobonkotshi@gmail.com",
    "numero": "0811414379"
  },
  {
    "nom": "ChrisBardol Wa ngindu  Ngindu",
    "mail": "chrisbardolngindu@gmail.com",
    "numero": "0998147738"
  },
  {
    "nom": "Joseph Kuelumuenamo Bamenikio",
    "mail": "bamenikioj@gmail.com",
    "numero": "0899808307"
  },
  {
    "nom": "Christ  MASSAMBA NSIMBULU ",
    "mail": "nsimbuluc@gmail.com",
    "numero": "0822208148"
  },
  {
    "nom": "CHARLES NGAL MIKWARI",
    "mail": "mikwaricharles01@gmail.com",
    "numero": "0815016982"
  },
  {
    "nom": "Rosine  KALANDA  NGALULA ",
    "mail": "rosinengalula@gmail.com",
    "numero": "0990736426"
  },
  {
    "nom": "René Mazembe Mpuru",
    "mail": "rempuru@yaoo.fr",
    "numero": "0998173334"
  },
  {
    "nom": "Delmas Biaya Ntendayi",
    "mail": "delmasntendayi@gmail.com",
    "numero": "0998143261"
  },
  {
    "nom": "Samuel Monzele Ndengani ",
    "mail": "samy_ndengani@yahoo.fr",
    "numero": "0999949330"
  },
  {
    "nom": "Papy Lukumu  Fataki ",
    "mail": "pafataki@gmail.com",
    "numero": "0816917321"
  },
  {
    "nom": "Parfait  Muaba  Mutambay ",
    "mail": "romanickparfait@gmail.com",
    "numero": "0824988937"
  },
  {
    "nom": "Enock MALONDA WASOLUA  SANGANA ",
    "mail": "sanganaenock@gmail.com",
    "numero": "0981439157"
  },
  {
    "nom": "Papy LELO ODIMBA KABADI ",
    "mail": "papykabadi8@gmail.com",
    "numero": "0823849427"
  },
  {
    "nom": "Flory  Mutumba  Mbuyi ",
    "mail": "mbuyiflory320@gmail.com",
    "numero": "0812018713"
  },
  {
    "nom": "Corneille  Iboy  Muntenge ",
    "mail": "corneillemuntenge@gmail.com",
    "numero": "0812199270"
  },
  {
    "nom": "Julien  GBANZI SANIMOTO ",
    "mail": "juliensanimoto@gmail.com",
    "numero": "0810085089"
  },
  {
    "nom": "Delmas Biaya Ntendayi",
    "mail": "delmasntendayi@gmail.com",
    "numero": "0998143261"
  },
  {
    "nom": "Julien  GBANZI SANIMOTO ",
    "mail": "juliensanimoto@gmail.com",
    "numero": "0810085089"
  },
  {
    "nom": "CHRISTIAN  LESUYA MUNIAMPALA ",
    "mail": "muniampalalesuya@yahoo.fr",
    "numero": "0896074153"
  },
  {
    "nom": "Floribert  Mpoyi Floribert MUKENDI",
    "mail": "floribertmukendi61@gmail.com",
    "numero": "0819942091"
  },
  {
    "nom": "Michel Mubake Miseka",
    "mail": "michelmiseka6@gmail.com",
    "numero": "0813339200"
  },
  {
    "nom": "Michel Bofotola WANGU",
    "mail": "michelwangu243@gmail.com",
    "numero": "0891037682"
  },
  {
    "nom": "Joseph Lumbanzu Nkayilu",
    "mail": "josephnkayilu0@gmail.com",
    "numero": "0815048488"
  },
  {
    "nom": "Jean Marie  Diakiese Bena ",
    "mail": "Jeanmarie_bena@yahoo.fr",
    "numero": "0815024801"
  },
  {
    "nom": "Désire Babongola Loole",
    "mail": "omeringconstruction@yahoo.com",
    "numero": "0814264302"
  },
  {
    "nom": "Yannick  Matondo  Kindimbu ",
    "mail": "yanarckindimbu@gmail.com",
    "numero": "0821001669"
  },
  {
    "nom": "Innocent LOMEMA LOHAYO ",
    "mail": "innocentlomema@gmail.com",
    "numero": "0813311773"
  },
  {
    "nom": "Belinda  Nkoy  Betuku ",
    "mail": "belindabetuku1@gmail.com",
    "numero": "0828462360"
  },
  {
    "nom": "Jérôme  Ditu Kazambu ",
    "mail": "jerokaz01@gmail.com",
    "numero": "0815795201"
  },
  {
    "nom": "Tshise KALADI TSHISEKEDI",
    "mail": "tshisetshisekedi864@gmail.com",
    "numero": "0903455085"
  },
  {
    "nom": "Freddy KAMUANGA KAZADI",
    "mail": "eceat.rdc@gmail.com",
    "numero": "0815112881"
  },
  {
    "nom": "Flory NSANGA MAMPIA",
    "mail": "mampiaflory@gmail.com",
    "numero": "0817675875"
  },
  {
    "nom": "Dieudonné  Ndombasi  Bambu ",
    "mail": "dieudonnebambu72@gmail.com",
    "numero": "0993406486"
  },
  {
    "nom": "Daniel  CIBUMBU  KAZADI ",
    "mail": "kazadidaniel676@gmail.com",
    "numero": "0818503677"
  },
  {
    "nom": "Azarias Fiston  Ligbakelo  Mwatoike ",
    "mail": "aligbakelo@gmail.com",
    "numero": "0814164199"
  },
  {
    "nom": "Parfait  Muaba  Mutambay ",
    "mail": "romanickparfait@gmail.com",
    "numero": "0824988937"
  },
  {
    "nom": "Arnhold Kabanga  MUKEBAYI",
    "mail": "arnholdmukebayi@gmail.com",
    "numero": "0811637879"
  },
  {
    "nom": "Péguy  Ngalamulume Malu",
    "mail": "peguymalu@gmail.com",
    "numero": "0859001747"
  },
  {
    "nom": "Annie  Lusamba  Ntumba ",
    "mail": "anniellakadima28@gmail.com",
    "numero": "0986118610"
  },
  {
    "nom": "Alexandre Wa Tshiamala Tshiamala",
    "mail": "alextshamala@gmail.com",
    "numero": "0998119854"
  },
  {
    "nom": "Leon Nakanza   Levo ",
    "mail": "levo.leon@gmail.com",
    "numero": "0810061018"
  },
  {
    "nom": "Christian Yolo Esiki",
    "mail": "sydneyesiki@gmail.com",
    "numero": "0819517278"
  },
  {
    "nom": "GUY LAROCHE  PERO NGWAMA",
    "mail": "larochengwama@gmail.com",
    "numero": "0892102765"
  },
  {
    "nom": "Mymmon Nsenga Kilunga",
    "mail": "perspective.afr@gmail.com",
    "numero": "0816890271"
  },
  {
    "nom": "Anatol Mpungu  Mpungu ",
    "mail": "mpunguanatol@gmail.com",
    "numero": "0817121076"
  },
  {
    "nom": "Christian Yolo Esiki",
    "mail": "sydneyesiki@gmail.com",
    "numero": "0819517278"
  },
  {
    "nom": "Patrick Kituba Ilho",
    "mail": "archikituba@gmail.com",
    "numero": "0851320482"
  },
  {
    "nom": "Patrick  MAKAMBO  KAKU ",
    "mail": "kakupatrick87@gmail.com",
    "numero": "0896480552"
  },
  {
    "nom": "Joseph Nono NANA NKIERE",
    "mail": "nkierenana@yahoo.com",
    "numero": "0823051460"
  },
  {
    "nom": "Jeancy Kumwamba Tshiamala",
    "mail": "Kumwamba2006@gmail.com",
    "numero": "0820871187"
  },
  {
    "nom": "François Kanku Kangela",
    "mail": "francoiskangela2@gmail.com",
    "numero": "0897000135"
  },
  {
    "nom": "DANIEL LUIZI KIBIKONDA",
    "mail": "daniel.kibikonda@gmail.com",
    "numero": "0991808379"
  },
  {
    "nom": "Nkashamba  N'as  Kazadi",
    "mail": "tjflykazadi@gmail.com",
    "numero": "0815829861"
  },
  {
    "nom": "MULAMBULA CIAKATUMBA KADIMA-MBUYI",
    "mail": "s2001k14@gmail.com",
    "numero": "0814315127"
  },
  {
    "nom": "GUY LAROCHE  PERO NGWAMA",
    "mail": "larochengwama@gmail.com",
    "numero": "0892102765"
  },
  {
    "nom": "Eric  NKELE LUAYI",
    "mail": "ericluayi2016@gmail.com",
    "numero": "0855280363"
  },
  {
    "nom": "Z Zola Vangu",
    "mail": "vanguzola@gmail.com",
    "numero": "0818008067"
  },
  {
    "nom": "Blaise MAMONIKA  LUEMBA ",
    "mail": "luembablaiseluemba@gmail.com",
    "numero": "0898011141"
  },
  {
    "nom": "Deborah pongombo Omoyi",
    "mail": "omoyiandrea@gmail.com",
    "numero": "0820182497"
  },
  {
    "nom": "Parfait  Muaba  Mutambay ",
    "mail": "romanickparfait@gmail.com",
    "numero": "0824988937"
  },
  {
    "nom": "Israël-Tshany  MUSANGANI  BENDERA ",
    "mail": "istshany_bend@yahoo.fr",
    "numero": "0998193627"
  },
  {
    "nom": "RODRIGUE  NTIMANSIEMI MAMBUENI ",
    "mail": "rmnsj1@gmail.com",
    "numero": "0815844637"
  },
  {
    "nom": "Emmanuel Kibwe Mwila",
    "mail": "emmanuel.mwila@foner.cd",
    "numero": "0814067413"
  },
  {
    "nom": "Patrick  MAKAMBO  KAKU ",
    "mail": "kakupatrick87@gmail.com",
    "numero": "0896480552"
  },
  {
    "nom": "Michel Soko longe Uyumbu",
    "mail": "micheluyumbu2021@gmail.com",
    "numero": "0817793505"
  },
  {
    "nom": "Ben  NGOY CIEPELA ",
    "mail": "bengoy@outlook.com",
    "numero": "0999997290"
  },
  {
    "nom": "Winner Balinga Mapanda",
    "mail": "winner.mapanda@foner.cd",
    "numero": "0973006030"
  },
  {
    "nom": "Winner Balinga Mapanda",
    "mail": "winner.mapanda@foner.cd",
    "numero": "0973006030"
  },
  {
    "nom": "Jules KABOFI NKOMBWA",
    "mail": "gectopoplus@gmail.com",
    "numero": "0815007746"
  },
  {
    "nom": "CHRISTIAN CUBAKA ACIZA",
    "mail": "christianaciza@gmail.com",
    "numero": "0994577416"
  },
  {
    "nom": "Guelord BOLIPUA MPIA",
    "mail": "guelordboli@gmail.com",
    "numero": "0811485775"
  },
  {
    "nom": "Jean Marie  KUMWAMBA  N'SAPU ",
    "mail": "gtnconstruct@gmail.com",
    "numero": "0991003456"
  },
  {
    "nom": "Christian Makindu Kyalumba ",
    "mail": "chkyamak1@gmail.com",
    "numero": "0999927990"
  },
  {
    "nom": "Joseph Nono NANA NKIERE",
    "mail": "nkierenana@yahoo.com",
    "numero": "0823051460"
  },
  {
    "nom": "Jean de Dieu KOEBONI BOBO",
    "mail": "bobojeandedieu@gmail.com",
    "numero": "0816422014"
  },
  {
    "nom": "Roger Kandu Mayi Vibila",
    "mail": "rgvibila@holops.com",
    "numero": "0816861660"
  },
  {
    "nom": "ERIC  PALA KIBALA ",
    "mail": "kibalaeric01@gmail.com",
    "numero": "0999943140"
  },
  {
    "nom": "Yves Muzola Ngoma",
    "mail": "yvesmuzola@gmail.com",
    "numero": "0991407271"
  },
  {
    "nom": "Gabriel Zaatcha KAZADI MUHOLA LASER",
    "mail": "laser.muhola@anat.gouv.cd",
    "numero": "0891558686"
  },
  {
    "nom": "Alpha Memidra  Mapoko Isongo Egbango",
    "mail": "alpha.egbango@celluleinfra.org",
    "numero": "0819823416"
  },
  {
    "nom": "WIREN KITSHIAKA  MONDU",
    "mail": "wiren.mondu@celluleinfra.org",
    "numero": "0810722822"
  },
  {
    "nom": "CHICO VUZUNGA MWADI",
    "mail": "mwadivuzungachico@gmail.com",
    "numero": "0819090470"
  },
  {
    "nom": "Blaise MAMONIKA  LUEMBA ",
    "mail": "luembablaiseluemba@gmail.com",
    "numero": "0898011141"
  },
  {
    "nom": "Guycele  Mpioko Malabi",
    "mail": "celemalabi@gmail.com",
    "numero": "0810622671"
  },
  {
    "nom": "Jean Bosco  Malele Bifulu ",
    "mail": "bifuluscolie2014@gmail.com",
    "numero": "0814029156"
  },
  {
    "nom": "Olivier  PASHO-LAWATA  ROGHO",
    "mail": "oliverutche@gmail.com",
    "numero": "0824376306"
  },
  {
    "nom": "Ralph Désiré  Bizongo",
    "mail": "desire.bizongo@celluleinfra.org",
    "numero": "0979059000"
  },
  {
    "nom": "Romain Mbule Bussa",
    "mail": "romainlandry.bussa@gmail.com",
    "numero": "0853683861"
  },
  {
    "nom": "Alpha Memidra  Mapoko Isongo Egbango",
    "mail": "alpha.egbango@celluleinfra.org",
    "numero": "0819823416"
  },
  {
    "nom": "Didier Mukendi Kamunga ",
    "mail": "kamungadidier@yahoo.fr",
    "numero": "0994744092"
  },
  {
    "nom": "Willy MANGA VALE",
    "mail": "willy.vale@inbtp.ac.cd",
    "numero": "0971550108"
  },
  {
    "nom": "Pires TOFOFA  LISINGO",
    "mail": "pireslisingo@gmail.com",
    "numero": "0812153345"
  },
  {
    "nom": "Doris  Kilungu  Kayamba ",
    "mail": "kayambakilungudoris@gmail.com",
    "numero": "0897956637"
  },
  {
    "nom": "Pires TOFOFA LISINGO",
    "mail": "pireslisingo@gmail.com",
    "numero": "0812153345"
  },
  {
    "nom": "Chadrack  Mutambayi  Ngoie",
    "mail": "ngoiechadrack2@gmail.com",
    "numero": "0892256018"
  },
  {
    "nom": "Chadrack  Mutambayi  Ngoie",
    "mail": "ngoiechadrack2@gmail.com",
    "numero": "0892256018"
  }


  
]



LIEN_INSCRIPTION_PAR_DEFAUT = "[Insérer le lien ici]"

SUJET_EMAIL = "🇨🇩 CNE-ITP — Invitation à votre inscription de test (Collège des 200 Experts)"

MESSAGE_TEMPLATE = """🇨🇩 MINISTERE DES INFRASTRUCTURES ET TRAVAUX PUBLICS 🇨🇩
Commission Nationale pour la création des Normes de Construction (CNE-ITP)
Pour les Honorables Experts Mandatés (Collège des 200)

Honorables Experts, Chers Collègues,

Au nom de la Haute Coordination Générale et du Secrétariat Général aux ITP, nous vous invitons, suite à votre désignation officielle, à finaliser votre mise en place administrative au sein de la CNE-ITP.

Vous êtes priés de procéder ce jour à votre inscription de test sur la plateforme numérique afin de valider votre affectation fonctionnelle dans vos instances respectives (Comité de Pilotage, Cellule Technique ou Comités Miroirs - CTM).

🔗 Lien pour votre inscription : 👉 {lien}

Note importante : Veillez à renseigner avec exactitude votre structure de provenance et votre profil technique. Votre participation constitue le garant scientifique du futur Référentiel Normatif National du Génie Civil en RDC.

Le Service de Support Technique reste à votre entière disposition.

Veuillez agréer, Honorables Experts, notre haute considération patriotique.

La Cellule Technique de Coordination (CTC)
Secrétariat Général aux ITP / Direction de la Réglementation et des Normes.
📍 Kinshasa, RDC."""


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
        parser.add_argument(
            "--skip",
            type=int,
            default=0,
            help="Ignore les N premiers experts de la liste (utile pour reprendre un envoi interrompu).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Ne traite que les N experts suivants (après --skip).",
        )
        parser.add_argument(
            "--whatsapp-only",
            action="store_true",
            help="N'envoie que le WhatsApp (n'envoie pas l'email).",
        )
        parser.add_argument(
            "--email-only",
            action="store_true",
            help="N'envoie que l'email (n'envoie pas le WhatsApp).",
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

        skip = options["skip"]
        limit = options["limit"]
        whatsapp_only = options["whatsapp_only"]
        email_only = options["email_only"]

        experts_a_traiter = EXPERTS[skip:]
        if limit is not None:
            experts_a_traiter = experts_a_traiter[:limit]

        if skip or limit is not None:
            self.stdout.write(self.style.WARNING(
                f"ℹ️  {len(experts_a_traiter)} expert(s) traité(s) "
                f"(skip={skip}, limit={limit}) sur {len(EXPERTS)} au total."
            ))

        emails_ok, emails_ko = 0, 0
        wa_ok, wa_ko = 0, 0

        for expert in experts_a_traiter:
            nom = expert.get("nom", "Honorable Expert")
            email = (expert.get("email") or expert.get("mail") or "").strip()
            telephone = (expert.get("telephone") or expert.get("numero") or "").strip()

            if email and not whatsapp_only:
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

            if telephone and not email_only:
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
