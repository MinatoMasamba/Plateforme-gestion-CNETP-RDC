import React, { useState } from "react";
import { 
  Users, 
  CheckCircle, 
  Award, 
  MapPin, 
  Building, 
  ShieldCheck, 
  Mail, 
  Phone, 
  BookOpen, 
  Trash2, 
  Briefcase, 
  Layers, 
  CheckSquare, 
  Calendar, 
  TrendingUp, 
  AlertTriangle,
  FileText
} from "lucide-react";

interface ExpertsModuleProps {
  experts: any[];
  setExperts: React.Dispatch<React.SetStateAction<any[]>>;
  workingGroups: any[];
  setWorkingGroups?: React.Dispatch<React.SetStateAction<any[]>>;
  selectedWorkingGroupId?: string;
  setSelectedWorkingGroupId?: (id: string) => void;
  selectedExpertId?: string;
  setSelectedExpertId?: (id: string) => void;
  expertSelectionType?: "wg" | "expert";
  setExpertSelectionType?: (type: "wg" | "expert") => void;
  onOpenChat?: (expertId: string) => void;
  isLoading?: boolean;
}

export default function ExpertsModule({
  experts,
  setExperts,
  workingGroups,
  setWorkingGroups,
  selectedWorkingGroupId,
  setSelectedWorkingGroupId,
  selectedExpertId,
  setSelectedExpertId,
  expertSelectionType,
  setExpertSelectionType,
  onOpenChat,
  isLoading = false,
}: ExpertsModuleProps) {

  // Local state for WG draft tasks / progress
  const [wgTasks, setWgTasks] = useState([
    { id: "task-1", wgCode: "WG 8.1", title: "Collecte des terres argileuses locales (Kongo-Central, Kwilu)", status: "Completed", progress: 100 },
    { id: "task-2", wgCode: "WG 8.1", title: "Détermination mécanique d'absorption d'eau blocs de terre BTC", status: "In Progress", progress: 75 },
    { id: "task-3", wgCode: "WG 8.1", title: "Publication des tables de dosages thermiques", status: "Planned", progress: 15 },
    
    { id: "task-4", wgCode: "WG 1.1", title: "Classification géotechnique des sols latéritiques", status: "Completed", progress: 100 },
    { id: "task-5", wgCode: "WG 1.1", title: "Établissement des courbes de portance CBR RDC", status: "In Progress", progress: 40 },
    
    { id: "task-6", wgCode: "WG 2.3", title: "Analyse comparative du ciment standard vs pouzzolanes", status: "Completed", progress: 100 },
    { id: "task-7", wgCode: "WG 2.3", title: "Formulation des bétons de classe minimum C25/30", status: "In Progress", progress: 90 },

    { id: "task-8", wgCode: "WG 3.1", title: "Recensement des essences d'arbres structuraux (Tola, Kambala)", status: "Completed", progress: 100 },
    { id: "task-9", wgCode: "WG 3.1", title: "Visserie et assemblage sous climat équatorial humide", status: "Planned", progress: 0 },

    { id: "task-10", wgCode: "WG 6.2", title: "Débit de crue de retour 10 ans pour collecteurs primaires", status: "Completed", progress: 100 },
    { id: "task-11", wgCode: "WG 6.2", title: "Dimensionnement des filtres d'assainissement décentralisés", status: "In Progress", progress: 55 }
  ]);

  // Handle task status quick toggle
  const toggleTaskStatus = (taskId: string) => {
    setWgTasks(prev => prev.map(task => {
      if (task.id === taskId) {
        const nextStatus = task.status === "Completed" ? "In Progress" : task.status === "In Progress" ? "Planned" : "Completed";
        const nextProgress = nextStatus === "Completed" ? 100 : nextStatus === "In Progress" ? 50 : 0;
        return { ...task, status: nextStatus, progress: nextProgress };
      }
      return task;
    }));
  };

  // List of active Comités Techniques Miroirs (for information panel)
  const ctmInfoList = [
    { code: "CTM 1", title: "Géotechnique & Risques", focus: "Eurocode 7, Sols du Bassin du Congo" },
    { code: "CTM 2", title: "Ouvrages d’Art", focus: "Ponts en béton précontraint et charpentes mixtes" },
    { code: "CTM 3", title: "Bâtiment & Transition Numérique", focus: "ISO 19650 BIM, efficacité thermique" },
    { code: "CTM 5", title: "Infrastructures de Transport", focus: "Normes routières régionales SADEC & CEEAC" },
    { code: "CTM 8", title: "Sciences des Matériaux", focus: "Valorisation des ressources de latérite et argile locale" }
  ];

  // Actions on Experts
  const approveExpert = (id: string) => {
    setExperts((prev: any[]) => prev.map(exp => exp.id === id ? { ...exp, isApproved: true } : exp));
  };

  const deleteExpert = (id: string) => {
    if (confirm("Voulez-vous vraiment retirer cet expert du CNETP RDC ?")) {
      setExperts((prev: any[]) => prev.filter(exp => exp.id !== id));
      // Switch back or select any remaining expert
      const remaining = experts.filter(exp => exp.id !== id);
      if (remaining.length > 0) {
        setSelectedExpertId(remaining[0].id);
      } else {
        setExpertSelectionType("wg");
      }
    }
  };

  const activeWg = workingGroups.find(w => w.id === selectedWorkingGroupId) || workingGroups[0];
  const activeExpert = experts.find(e => e.id === selectedExpertId) || experts[0];

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full text-slate-300">
      
      {/* Title Header */}
      <div className="border-b border-white/10 pb-5">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Users className="h-6 w-6 text-emerald-400" />
            <h2 className="text-xl font-extrabold text-white tracking-tight uppercase">
              Gestion de la Co-Gouvernance CNETP
            </h2>
          </div>
          <div className="flex bg-black/40 border border-white/10 rounded-lg p-0.5 text-xs font-semibold">
            <button
              onClick={() => setExpertSelectionType("wg")}
              className={`px-3 py-1.5 rounded-md transition-all ${
                expertSelectionType === "wg" 
                  ? "bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Vue Groupe (WG)
            </button>
            <button
              onClick={() => setExpertSelectionType("expert")}
              className={`px-3 py-1.5 rounded-md transition-all ${
                expertSelectionType === "expert" 
                  ? "bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Fiche Expert
            </button>
          </div>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl leading-relaxed mt-2">
          Sélectionnez un Groupe de Travail (WG) ou un Expert dans la barre de navigation gauche pour consulter ses attributions, fiches de conformités et d'accréditations au sein de la République Démocratique du Congo.
        </p>
      </div>

      {/* DYNAMIC SHIFT VIEW */}
      {expertSelectionType === "wg" ? (
        activeWg ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
            
            {/* WG Main Info Panel - Left 2 cols */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Card Title Box */}
              <div className="bg-black/30 border border-white/10 rounded-xl p-5 relative overflow-hidden backdrop-blur-md">
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full filter blur-xl pointer-events-none"></div>
                <div className="flex items-center gap-2 mb-2 font-mono text-[10.5px]">
                  <span className="bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-md font-bold text-xs">
                    {activeWg.code}
                  </span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-400 font-bold">STATUT LOCAL :</span>
                  <span className="text-emerald-400 font-bold uppercase">{activeWg.tag}</span>
                </div>
                
                <h3 className="text-xl font-extrabold text-white mt-2 leading-snug">
                  {activeWg.title}
                </h3>
                
                <p className="text-xs text-slate-400 mt-4 leading-relaxed">
                  Ce groupe d'étude de co-gouvernance CNETP a pour vocation d'analyser les technologies d'exploitation, de mise en œuvre et d'établissement des limites réglementaires nationales de RDC de second œuvre ou de gros œuvre correspondantes.
                </p>

                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-white/5 pt-4 text-xs font-semibold">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-slate-500" />
                    <span className="text-slate-500">Comité de Rapprochement :</span>
                    <span className="text-slate-200">CTC Miroir RDC</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-emerald-500" />
                    <span className="text-slate-500">Norme Directrice :</span>
                    <span className="text-slate-200">ISO/CD National</span>
                  </div>
                </div>
              </div>

              {/* Checklist Dynamic Progress */}
              <div className="bg-black/25 border border-white/10 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-emerald-400" />
                    Livrables techniques en cours d'évaluation
                  </h4>
                  <span className="text-[10px] font-mono text-slate-500">Cliquez pour basculer le statut</span>
                </div>

                <div className="space-y-3">
                  {wgTasks.filter(t => t.wgCode === activeWg.code).length === 0 ? (
                    <p className="text-xs text-slate-500 italic py-4 text-center">
                      Aucune programmation pour l'avant-projet de ce groupe d'étude spécifique.
                    </p>
                  ) : (
                    wgTasks.filter(t => t.wgCode === activeWg.code).map((task) => (
                      <div 
                        key={task.id}
                        onClick={() => toggleTaskStatus(task.id)}
                        className="bg-black/30 border border-white/5 hover:border-emerald-500/25 p-3.5 rounded-lg transition-all flex items-start gap-3.5 cursor-pointer hover:bg-white/[0.02]"
                      >
                        <div className="mt-0.5">
                          {task.status === "Completed" ? (
                            <div className="h-4 w-4 rounded-full bg-emerald-500 flex items-center justify-center text-black font-extrabold text-[10px]">
                              ✓
                            </div>
                          ) : task.status === "In Progress" ? (
                            <div className="h-4 w-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin"></div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border border-slate-600"></div>
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className={`text-xs font-bold ${task.status === "Completed" ? "line-through text-slate-500" : "text-slate-200"}`}>
                              {task.title}
                            </p>
                            <span className={`text-[9px] px-1.5 py-0.5 font-bold rounded shrink-0 ${
                              task.status === "Completed" ? "bg-emerald-500/10 text-emerald-400" : task.status === "In Progress" ? "bg-amber-500/10 text-amber-400" : "bg-white/5 text-slate-400"
                            }`}>
                              {task.status}
                            </span>
                          </div>

                          {/* Percent bar */}
                          <div className="mt-2.5 w-full h-1 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all duration-500 ${task.status === "Completed" ? "bg-emerald-500" : task.status === "In Progress" ? "bg-amber-500" : "bg-slate-600"}`}
                              style={{ width: `${task.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>

            {/* Side info - Right 1 col (Members list) */}
            <div className="space-y-6">
              
              {/* Members of this WG */}
              <div className="bg-black/25 border border-white/10 rounded-xl p-5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 pb-2 border-b border-white/5 flex items-center gap-2">
                  <Users className="h-4 w-4 text-slate-400" />
                  Membres Officiels ({experts.filter(exp => exp.wg && exp.wg.includes(activeWg.code)).length})
                </h4>

                <div className="space-y-3">
                  {experts.filter(exp => exp.wg && exp.wg.includes(activeWg.code)).length === 0 ? (
                    <div className="text-center py-6 text-slate-500 text-xs italic">
                      Aucun membre rattaché à ce bureau.
                    </div>
                  ) : (
                    experts.filter(exp => exp.wg && exp.wg.includes(activeWg.code)).map((exp) => (
                      <div 
                        key={exp.id}
                        onClick={() => {
                          setExpertSelectionType("expert");
                          setSelectedExpertId(exp.id);
                        }}
                        className="p-3 bg-black/45 border border-white/5 rounded-lg hover:border-emerald-500/30 transition-all cursor-pointer flex items-center gap-3.5 group"
                      >
                        <div className="h-9 w-9 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg flex items-center justify-center font-extrabold text-xs">
                          {exp.name.split(" ").map((n: string) => n[0]).join("")}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-bold text-white group-hover:text-emerald-400 transition-colors truncate">{exp.name}</p>
                          <p className="text-[10px] text-slate-500 mt-0.5 truncate">{exp.role} • {exp.province}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* ISO Regulatory Context */}
              <div className="bg-black/35 border border-white/10 rounded-xl p-5 text-xs space-y-3">
                <h4 className="font-bold text-white flex items-center gap-1.5 uppercase text-[10.5px]">
                  <BookOpen className="h-4 w-4 text-emerald-400" />
                  Alignement Légistique
                </h4>
                <p className="text-slate-400 leading-normal text-[11px]">
                  Tous les livrables d'avant-projets techniques rédigés par ce WG transitent par une relecture du Secrétariat CTC RDC avant homologation nationale sous forme de décret au Journal Officiel.
                </p>
                <div className="pt-2 border-t border-white/5 font-mono text-[9px] text-slate-500">
                  <p>• Droit de vote réglementaire : Oui</p>
                  <p>• Quorum Requis : 2/3 des votants</p>
                  <p>• Période d'enquête publique : 90 jours</p>
                </div>
              </div>

            </div>

          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs">
            Sélectionnez un groupe de travail pour afficher ses rapports techniques.
          </div>
        )
      ) : (
        activeExpert ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
            
            {/* Expert Detail - Left 2 cols */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Profile Main block */}
              <div className="bg-black/30 border border-white/10 rounded-xl p-5 relative overflow-hidden backdrop-blur-md">
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full filter blur-xl pointer-events-none"></div>
                
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="h-14 w-14 rounded-full bg-emerald-500 text-black flex items-center justify-center font-extrabold text-lg shadow-[0_0_20px_rgba(16,185,129,0.3)] border-2 border-emerald-400">
                      {activeExpert.name.split(" ").map((n: string) => n[0]).join("")}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-lg font-extrabold text-white">{activeExpert.name}</h3>
                        <span className={`text-[8.5px] px-2 py-0.5 rounded-full font-bold uppercase ${
                          activeExpert.role.includes("Président") 
                            ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                            : activeExpert.role.includes("Secrétaire")
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        }`}>
                          {activeExpert.role}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 font-medium">{activeExpert.structure}</p>
                    </div>
                  </div>

                  {/* Accredit status badge */}
                  <div>
                    {activeExpert.isApproved ? (
                      <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5 uppercase">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Agréé CTC RDC
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold bg-amber-500/15 text-amber-500 border border-amber-500/25 px-3 py-1.5 rounded-lg flex items-center gap-1.5 uppercase animate-pulse">
                        <AlertTriangle className="h-3.5 w-3.5 animate-spin" />
                        Accréditation en attente
                      </span>
                    )}
                  </div>
                </div>

                {/* Sub details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-white/5 pt-5 mt-5 text-xs text-slate-300">
                  <div className="space-y-2.5">
                    <div className="flex items-center gap-2">
                      <Building className="h-4 w-4 text-slate-500 shrink-0" />
                      <span className="text-slate-500 font-bold">Institution :</span>
                      <span className="text-white font-semibold truncate max-w-[200px]">{activeExpert.structure}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-slate-500 shrink-0" />
                      <span className="text-slate-500 font-bold">Province :</span>
                      <span className="text-white font-semibold">{activeExpert.province}</span>
                    </div>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-center gap-2">
                      <Award className="h-4 w-4 text-emerald-500/60 shrink-0" />
                      <span className="text-slate-500 font-bold">Comité CTM :</span>
                      <span className="text-emerald-400 font-bold truncate max-w-[200px]">{activeExpert.ctm}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-slate-500 shrink-0" />
                      <span className="text-slate-500 font-bold">Groupe de Travail :</span>
                      <span className="text-white font-semibold truncate max-w-[200px]">{activeExpert.wg}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Administrative Actions block */}
              <div className="bg-black/25 border border-white/10 rounded-xl p-5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 pb-2 border-b border-white/5">
                  Vérification Juridique & Accréditation CTC
                </h4>

                <div className="space-y-4">
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Avant de pouvoir valider ou amender un écrit au sein des comités CTC, la présence légale et technique des experts doit être validée par arrêté ministériel conjoint. Cet expert possède des droits {activeExpert.isApproved ? "actifs de vote et de co-gouvernance." : "temporaires en lecture seule."}
                  </p>

                  <div className="flex items-center gap-3 pt-2">
                    {!activeExpert.isApproved ? (
                      <button
                        type="button"
                        onClick={() => approveExpert(activeExpert.id)}
                        className="px-4.5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-extrabold text-xs flex items-center gap-2 transition-all cursor-pointer shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        Valider et Accréditer l'Expert
                      </button>
                    ) : (
                      <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold rounded-lg flex items-center gap-2 w-full">
                        <CheckCircle className="h-4 w-4" />
                        Titre accrédité d'expert pour la République Démocratique du Congo validé par l'assemblée extraordinaire.
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={() => deleteExpert(activeExpert.id)}
                      className="px-4 py-2.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer ml-auto"
                      title="Supprimer définitivement la fiche expert"
                    >
                      <Trash2 className="h-4 w-4" />
                      Détacher du CNETP
                    </button>
                  </div>
                </div>
              </div>

            </div>

            {/* Side Contact card - Right 1 col */}
            <div className="space-y-6">
              
              {/* Contact Panel */}
              <div className="bg-black/25 border border-white/10 rounded-xl p-5 space-y-4.5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-white/5">
                  Canal Direct Sécurisé
                </h4>

                <div className="space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <span className="text-slate-500 text-[10px] font-bold block uppercase">Courriel Officiel</span>
                    <span className="text-slate-200 block break-all font-semibold select-all">
                      {activeExpert.email}
                    </span>
                  </div>
                  <div className="space-y-1 pt-1">
                    <span className="text-slate-500 text-[10px] font-bold block uppercase font-mono">Ligne Téléphonique</span>
                    <span className="text-slate-200 block font-semibold select-all">
                      {activeExpert.phone}
                    </span>
                  </div>
                </div>

                 <button
                  type="button"
                  onClick={() => {
                    if (onOpenChat) {
                      onOpenChat(activeExpert.id);
                    } else {
                      alert(`Envoi de courrier électronique crypté transmis à ${activeExpert.name} via le portail de co-gouvernance.`);
                    }
                  }}
                  className="w-full py-2.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-extrabold text-xs transition-all cursor-pointer block text-center"
                >
                  💬 Discuter via Messagerie
                </button>
              </div>

              {/* Associated Committee Focus */}
              <div className="bg-black/35 border border-white/10 rounded-xl p-5 text-xs space-y-3">
                <h4 className="font-bold text-white flex items-center gap-1.5 uppercase text-[10.5px]">
                  <Layers className="h-4 w-4 text-emerald-400" />
                  Profil CTM Affecté
                </h4>
                <div className="p-3 bg-white/[0.02] border border-white/5 rounded-lg space-y-2">
                  <p className="font-bold text-white text-[11px] leading-tight">
                    {activeExpert.ctm.split("–")[0]}
                  </p>
                  <p className="text-[10px] text-slate-400 leading-normal">
                    {activeExpert.ctm.split("–")[1] || activeExpert.ctm}
                  </p>
                </div>
                <p className="text-[10px] text-slate-500 leading-relaxed pt-1">
                  Les nominations à ce comité sont renouvelables tous les 3 ans après audit des rapports d'activités techniques par le conseil légistique supérieur.
                </p>
              </div>

            </div>

          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs">
            Sélectionnez une fiche d'expert pour afficher ses informations de profil.
          </div>
        )
      )}

      {/* FOOTER METRICS INFO BANNER */}
      <div className="bg-black/25 border border-white/10 rounded-xl p-5">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 pb-2 border-b border-white/5 flex items-center gap-1.5">
          <TrendingUp className="h-4 w-4 text-emerald-400" />
          Indicateurs Clés de la Commission CNETP RDC
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Comités Techniques Miroirs</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">8 / 8 CTM</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-emerald-500 h-1 rounded-full" style={{ width: "100%" }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Groupes d'Études Actifs</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">14 Bureaux (WG)</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-emerald-500 h-1 rounded-full" style={{ width: "70%" }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Experts Certifiés Accrédités</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">
              {experts.filter(e => e.isApproved).length} Experts
            </span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${(experts.filter(e => e.isApproved).length / experts.length) * 100}%` }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Taux d'Avancement des Normes</span>
            <span className="text-xl font-mono font-extrabold text-emerald-400 mt-1 block">84.2 %</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-emerald-400 h-1 rounded-full" style={{ width: "84.2%" }}></div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
