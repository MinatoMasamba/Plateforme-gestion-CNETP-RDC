import React from "react";
import { X, Users, BookOpen, Layers, CheckCircle2, Award, Calendar, ChevronRight } from "lucide-react";

interface CtmWorkingGroupsModalProps {
  isOpen: boolean;
  onClose: () => void;
  ctmName: string;
  isDarkMode: boolean;
}

export default function CtmWorkingGroupsModal({
  isOpen,
  onClose,
  ctmName,
  isDarkMode
}: CtmWorkingGroupsModalProps) {
  if (!isOpen) return null;

  // Extract sub-commission number for matching (e.g., 8 from "CTM 8")
  const numMatch = ctmName.match(/(\d+)/);
  const ctmIdStr = numMatch ? numMatch[1] : "8";
  const ctmCode = `CTM ${ctmIdStr}`;

  // Complete official list of 8 technical sub-commissions with their precise parameters
  const subCommissionsDetails: Record<string, { name: string; expertsCount: number; mission: string; president: string; mandate: string; focus: string }> = {
    "1": {
      name: "Sous-Commission 1 : Géotechnique",
      expertsCount: 19,
      mission: "Reconnaissance systématique des sols, stabilité de terrain face aux glissements, et élaboration des règles de fondation en climat humide équatorial.",
      president: "Ir. Godefroid Munongo (Office des Routes)",
      mandate: "2024 - 2028",
      focus: "Eurocode 7, Sols tropicaux, glissements de Kinshasa et fondations profondes."
    },
    "2": {
      name: "Sous-Commission 2 : Ouvrages d'art",
      expertsCount: 19,
      mission: "Vérification des calculs mécaniques, auscultation technique de barrages hydroélectriques, dimensionnement structurel de ponts d'intérêt national et portiques.",
      president: "Prof. Hubert Makengo (ISTA Kinshasa)",
      mandate: "2025 - 2029",
      focus: "Ponts en béton précontraint, structures mixtes acier-béton, fatigue des ouvrages."
    },
    "3": {
      name: "Sous-Commission 3 : Bâtiments",
      expertsCount: 19,
      mission: "Validation des normes d'habitations individuelles, immeubles administratifs et complexes industriels. Fixation des règles structurelles et de transition énergétique bioclimatique.",
      president: "Arch. Sylvain Lukusa (Ordre National des Architectes)",
      mandate: "2024 - 2028",
      focus: "Performance thermique des enveloppes, éco-construction, règles parasismiques."
    },
    "4": {
      name: "Sous-Commission 4 : Aéroports",
      expertsCount: 19,
      mission: "Harmonisation réglementaire systématique avec les standards internationaux de l'OACI, résistance mécanique des pistes d'atterrissage lourdes et tarmacs provinciaux.",
      president: "Ir. Jeanne Kabeya (Régie des Voies Aériennes)",
      mandate: "2025 - 2029",
      focus: "Pistes de roulement de grand tonnage, infrastructures aéroportuaires, signalisation."
    },
    "5": {
      name: "Sous-Commission 5 : Routes, Chemins de fer et Ports",
      expertsCount: 19,
      mission: "Détermination des clauses de calculs d'épaisseurs des chaussées bitumineuses, dures ou souples, supervision des plateformes ferroviaires et dalles de ports fluviaux.",
      president: "Ir. Chantal Mwamba (Office des Voiries et Drainage)",
      mandate: "2025 - 2027",
      focus: "Enrobés bitumineux à forte résistance, asphalte de Lualaba, plateformes multimodales."
    },
    "6": {
      name: "Sous-Commission 6 : Ressources en eau et Ingénierie hydraulique",
      expertsCount: 19,
      mission: "Encadrement technique des réseaux d'infrastructures de captage d'eau brute, adductions, stations de désinfection de la REGIDESO et projets d'agro-hydraulique régionale.",
      president: "Ir. Dieudonné Bemba (REGIDESO RDC)",
      mandate: "2024 - 2028",
      focus: "Tuyaux PEHD de grand diamètre, forages ruraux, captages et stockages hydro-agricoles."
    },
    "7": {
      name: "Sous-Commission 7 : Assainissement",
      expertsCount: 19,
      mission: "Normalisation de la collecte des fluides pluviaux urbains, des collecteurs gravitaires d'égouts, gestion autonome des eaux usées domestiques et des rejets solides communaux.",
      president: "Ir. Mireille Tschite (OVD Assainissement)",
      mandate: "2025 - 2029",
      focus: "Biodégradabilité, dimensionnement de caniveaux, bassins de rétention des crues."
    },
    "8": {
      name: "Sous-Commission 8 : Recherche, Simulation et Sciences des matériaux",
      expertsCount: 20,
      mission: "Normalisation scientifique de la caractérisation des sols congolais, formulation de bétons géopolymères, simulation numérique de structures et valorisation systématique des matériaux locaux.",
      president: "Prof. Masamba Édouard (Université de Kinshasa)",
      mandate: "2024 - 2028",
      focus: "Blocs de terre comprimée (BTC), granulats recyclés, latérites et argiles locales."
    }
  };

  const selectedCne = subCommissionsDetails[ctmIdStr] || subCommissionsDetails["8"];

  const getCtmDescription = () => {
    return {
      mission: selectedCne.mission,
      president: selectedCne.president,
      mandate: selectedCne.mandate,
      status: "Actif"
    };
  };

  const details = getCtmDescription();

  // Unified list of groups attachable to all 8 sub-commissions
  const getCtmWorkingGroups = () => {
    const list = [
      // SC 1
      {
        id: "wg-1.1",
        code: "WG 1.1",
        title: "Sols Tropicaux & Géo-mécanique (CTM 1)",
        desc: "Analyse granulométrique fine sur sables côtiers et détermination des coefficients de portance Proctor des latérites.",
        status: "Actif",
        expertsCount: 4,
        deliverable: "Spécification mécanique des sols ferrallitiques"
      },
      {
        id: "wg-1.2",
        code: "WG 1.2",
        title: "Stabilité & Érosions Fluviales (CTM 1)",
        desc: "Modélisation de parade contre les glissements de terrain et lissage d'avis pour le remblayage des têtes d'érosions.",
        status: "Rédaction",
        expertsCount: 7,
        deliverable: "Note de calcul de stabilité des digues"
      },
      // SC 2
      {
        id: "wg-2.1",
        code: "WG 2.1",
        title: "Calcul Structural & Eurocodes (CTM 2)",
        desc: "Définition de la carte des accélérations sismiques nationales pour la conception structurelle parasismique.",
        status: "Actif",
        expertsCount: 5,
        deliverable: "Arrêté sur les calculs parasismiques RDC"
      },
      {
        id: "wg-2.2",
        code: "WG 2.2",
        title: "Auscultation & Auscultation Ponts RDC (CTM 2)",
        desc: "Monitoring rhéologique des grands ouvrages d'art en République Démocratique du Congo.",
        status: "Evaluation",
        expertsCount: 4,
        deliverable: "Guide méthodologique d'auscultation active"
      },
      // SC 3
      {
        id: "wg-3.1",
        code: "WG 3.1",
        title: "BIM & Transition Numérique (CTM 3)",
        desc: "Gouvernance de la maquette virtuelle 3D selon la norme internationale ISO 19650.",
        status: "Actif",
        expertsCount: 6,
        deliverable: "Plan national de numérisation Bâtiment"
      },
      {
        id: "wg-3.2",
        code: "WG 3.2",
        title: "Bâtiment Durable & Isolation (CTM 3)",
        desc: "Spécifications thermiques pour réduire la climatisation forcée sous climat équatorial d'Afrique Centrale.",
        status: "En rédaction",
        expertsCount: 5,
        deliverable: "Code bioclimatique d'enveloppe résidentielle"
      },
      // SC 4
      {
        id: "wg-4.1",
        code: "WG 4.1",
        title: "Alignement OACI de Pistes (CTM 4)",
        desc: "L'organisation des exigences de sécurité aéroportuaire et le lissage avec l'OACI des caractéristiques géométriques.",
        status: "Actif",
        expertsCount: 4,
        deliverable: "Standard de frottement de surface de piste (OACI)"
      },
      // SC 5
      {
        id: "wg-5.1",
        code: "WG 5.1",
        title: "Ingénierie Routière & Revêtement (CTM 5)",
        desc: "Élaboration de formulations d'enrobés bitumineux à forte résistance thermique adaptés aux surcharges.",
        status: "Stable",
        expertsCount: 8,
        deliverable: "Cahier des clauses d'asphalte naturel lualabais"
      },
      // SC 6
      {
        id: "wg-6.1",
        code: "WG 6.1",
        title: "Réseaux Adduction d'Eau REGIDESO (CTM 6)",
        desc: "Standardisation technique de tuyaux d'adduction en PEHD de grand diamètre pour limiter les casses.",
        status: "Rédaction",
        expertsCount: 5,
        deliverable: "Cahier d'étanchéité des réseaux de distribution"
      },
      // SC 7
      {
        id: "wg-7.1",
        code: "WG 7.1",
        title: "Collecteurs Pluviaux & Gravitaires (CTM 7)",
        desc: "Détermination des sections de collecteurs de dalles et dimensionnement optimal de caniveaux à fort débit.",
        status: "Actif",
        expertsCount: 4,
        deliverable: "Standard de calcul hydrologique urbain"
      },
      // SC 8
      {
        id: "wg-8.1",
        code: "WG 8.1",
        title: "Caractérisation d'Argiles Locales (CTM 8)",
        desc: "Formulation scientifique brevetée des Blocs de Terre Comprimée (BTC40) stabilisés au ciment et à la chaux.",
        status: "Actif",
        expertsCount: 5,
        deliverable: "Standard de compression d'argile locale v1"
      },
      {
        id: "wg-8.2",
        code: "WG 8.2",
        title: "Métrologie & Étalons de Chantiers (CTM 8)",
        desc: "L'étalonnage des appareils d'essais en compression et étirements des éprouvettes rattachées au CNE.",
        status: "Évaluation",
        expertsCount: 3,
        deliverable: "Régulation métrologique CNETP-8"
      },
      {
        id: "wg-8.3",
        code: "WG 8.3",
        title: "Lissage des Procédures d'Essais (CTM 8)",
        desc: "Normalisation internationale des protocoles d'écrasement mécanique au pressiomètre.",
        status: "Exigences",
        expertsCount: 4,
        deliverable: "Guide d'essais physiques de pressiométrie"
      }
    ];

    // Filter by ctmCode (e.g. CTM 8 or CTM 3)
    return list.filter(wg => wg.title.toUpperCase().includes(ctmCode.toUpperCase()));
  };

  const currentWgs = getCtmWorkingGroups();

  const overlayBg = "bg-black/80 backdrop-blur-sm";
  const modalBg = isDarkMode 
    ? "bg-[#05050b] border-white/10 text-white" 
    : "bg-[#ffffff] border-slate-200 text-slate-800 shadow-xl";

  const statusBadge = (status: string) => {
    switch (status) {
      case "Actif":
      case "Stable":
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
      case "Évaluation":
      case "En rédaction":
      case "Rédaction":
        return "bg-amber-500/10 text-amber-500 border border-amber-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
    }
  };

  return (
    <div className={`fixed inset-0 z-[100] flex items-center justify-center p-4 transition-all duration-300 ${overlayBg}`}>
      <div className={`w-full max-w-3xl rounded-2xl border flex flex-col max-h-[90vh] overflow-hidden ${modalBg}`}>
        
        {/* Banner header RDC styled */}
        <div id="ctm-modal-top-banner" className="bg-gradient-to-r from-blue-700 via-yellow-500 to-red-650 p-1 flex justify-between items-center shrink-0">
          <span className="text-[10px] uppercase font-bold text-white px-2 tracking-widest bg-black/40 rounded">
            RDC - Cabinet Interministériel de Co-Gouvernance
          </span>
          <span className="text-[10px] text-white/90 font-medium font-mono mr-2">Secrétariat National CNETP</span>
        </div>

        {/* Header containing name and close */}
        <div className="p-6 border-b border-white/10 dark:border-white/5 flex items-start justify-between gap-4 shrink-0">
          <div className="flex gap-3">
            <div className="h-12 w-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0">
              <Layers className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-bold text-blue-500 bg-blue-500/15 border border-blue-500/20 px-2 py-0.5 rounded">
                  {ctmCode} (Actif)
                </span>
                <span className="text-[10px] font-bold text-slate-500">• Sous-Commission CNETP</span>
              </div>
              <h2 className="text-lg font-bold tracking-tight text-blue-450 dark:text-blue-400 mt-1">
                {ctmName}
              </h2>
            </div>
          </div>
          <button 
            type="button" 
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          
          {/* CTM description card */}
          <div className={`p-5 rounded-xl border ${
            isDarkMode ? "bg-white/[0.01] border-white/5" : "bg-slate-50 border-slate-200"
          } space-y-4`}>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Mission Scientifique</h3>
              <p className="text-xs leading-relaxed font-semibold mt-1">
                {details.mission}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1.5 border-t border-white/10 dark:border-white/5">
              <div>
                <span className="text-[10px] text-slate-400 block font-medium uppercase tracking-wide">Rapporteur / Président</span>
                <span className="text-xs font-bold text-slate-200 dark:text-slate-300 mt-0.5 block">{details.president}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-medium uppercase tracking-wide">Mandat d'accréditation</span>
                <span className="text-xs font-bold text-slate-200 dark:text-slate-300 mt-0.5 block">{details.mandate}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-medium uppercase tracking-wide">Groupes de Travail</span>
                <span className="text-xs font-bold text-slate-200 dark:text-slate-300 mt-0.5 block">{currentWgs.length} comités d'experts</span>
              </div>
            </div>
          </div>

          {/* List of working groups */}
          <div className="space-y-3.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Groupes Techniques (WGs) Opérationnels d'Études</span>
              <span className="text-[10px] font-mono text-blue-450 uppercase">{currentWgs.length} Actifs</span>
            </h3>

            {currentWgs.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-white/10 dark:border-white/5 rounded-xl">
                Aucun groupe technique pour l'instant rattaché à cette sous-commission.
              </div>
            ) : (
              <div className="space-y-3">
                {currentWgs.map((wg) => (
                  <div 
                    key={wg.id}
                    className={`p-4 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all duration-150 hover:bg-white/[0.02] ${
                      isDarkMode ? "border-white/5" : "border-slate-150 bg-white"
                    }`}
                  >
                    <div className="space-y-1.5 min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-[10px] font-bold text-slate-200 bg-slate-500/10 px-2 py-0.5 rounded border border-slate-500/25">
                          {wg.code}
                        </span>
                        <h4 className="text-xs font-bold text-slate-300 leading-none">
                          {wg.title}
                        </h4>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-extrabold font-mono tracking-wider uppercase leading-none ${statusBadge(wg.status)}`}>
                          {wg.status}
                        </span>
                      </div>
                      
                      <p className="text-[11px] text-slate-400 leading-normal">
                        {wg.desc}
                      </p>

                      <div className="flex items-center gap-3.5 text-[9px] text-slate-500 pt-1">
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {wg.expertsCount} experts enregistrés
                        </span>
                        <span className="text-slate-650">•</span>
                        <span className="flex items-center gap-1">
                          <BookOpen className="h-3 w-3" />
                          Livrable: <strong>{wg.deliverable}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="shrink-0 flex items-center gap-2">
                      <span className="text-[10px] text-blue-500 bg-blue-500/5 px-2.5 py-1 rounded-lg border border-blue-500/10 font-bold flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Accrédité
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 dark:border-white/5 flex items-center justify-between shrink-0">
          <p className="text-[10.5px] text-slate-500 leading-relaxed max-w-lg">
            Les experts rattachés à ces groupes travaillent sous le régime du CNETP pour le lissage et dépôt des avant-projets de normes de la république démocratique du Congo.
          </p>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 font-bold text-black rounded-lg text-xs leading-none transition-colors duration-200 cursor-pointer shadow-lg shrink-0"
          >
            Fermer l'Aperçu CTM
          </button>
        </div>

      </div>
    </div>
  );
}
