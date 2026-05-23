import { useState, useMemo } from "react";
import { 
  FileText, 
  Users, 
  Plus, 
  Award, 
  Calendar, 
  Coins, 
  ShieldCheck, 
  ChevronRight, 
  CheckSquare,
  Sparkles,
  Search
} from "lucide-react";
import { Document, Collaborator } from "../types";

interface SidebarProps {
  activeTab?: 'editor' | 'history' | 'experts' | 'meetings' | 'financial' | 'validation' | string;
  documents: Document[];
  selectedDocId: string;
  onSelectDoc: (id: string) => void;
  collaborators: Collaborator[];
  activeCollaborator: Collaborator | null;
  onSelectCollaborator: (col: Collaborator) => void;
  onAddNewDoc: () => void;

  // Experts/WG features
  workingGroups: { id: string; code: string; title: string; tag: string }[];
  experts: any[];
  selectedWorkingGroupId: string;
  setSelectedWorkingGroupId: (id: string) => void;
  selectedExpertId: string;
  setSelectedExpertId: (id: string) => void;
  expertSelectionType: "wg" | "expert";
  setExpertSelectionType: (type: "wg" | "expert") => void;

  // History features
  versions?: any[];
  selectedHistoryAuthorEmail?: string | null;
  onSelectHistoryAuthorEmail?: (email: string | null) => void;

  // Simulated Roles
  userRole?: string;
  onChangeRole?: (role: string) => void;
  onOpenProfileModal?: () => void;
}

export default function Sidebar({
  activeTab = "editor",
  documents,
  selectedDocId,
  onSelectDoc,
  collaborators,
  activeCollaborator,
  onSelectCollaborator,
  onAddNewDoc,

  // Experts/WG features
  workingGroups,
  experts,
  selectedWorkingGroupId,
  setSelectedWorkingGroupId,
  selectedExpertId,
  setSelectedExpertId,
  expertSelectionType,
  setExpertSelectionType,

  // History features
  versions = [],
  selectedHistoryAuthorEmail = null,
  onSelectHistoryAuthorEmail,

  // Simulated Roles
  userRole = "ADMIN",
  onChangeRole = () => {},
  onOpenProfileModal = () => {}
}: SidebarProps) {
  // Local state for searching within groups / experts in sidebar
  const [expertSearchQuery, setExpertSearchQuery] = useState("");


  // Local state for meetings tab schedule lists
  const [meetingsList, setMeetingsList] = useState([
    { id: "m-1", title: "Session CTM 8 - Argiles Locales", date: "20 Mai 2026", status: "Terminé" },
    { id: "m-2", title: "Concertation Réglementation ITP", date: "24 Mai 2026", status: "En cours" },
    { id: "m-3", title: "Commission Extraordinaire CTM 1", date: "02 Juin 2026", status: "Planifié" }
  ]);

  // Local state for budget items list
  const [budgetItems, setBudgetItems] = useState([
    { id: "b-1", title: "Cotisation Annuelle OCC 2026", amount: "78,500 CDF", status: "Payé" },
    { id: "b-2", title: "Fonds ITP Secrétariat RDC", amount: "125,000 CDF", status: "Validé" },
    { id: "b-3", title: "Subvention d'Activité ONA", amount: "45,000 CDF", status: "En attente" }
  ]);


  // Handle adding new meeting scheduled slot
  const handleAddMeeting = () => {
    const title = prompt("Sujet de la nouvelle séance de concertation à planifier :");
    if (title) {
      setMeetingsList(prev => [
        ...prev,
        {
          id: `m-${Date.now()}`,
          title,
          date: "En attente",
          status: "Planifié"
        }
      ]);
    }
  };

  // Handle adding new budget lines
  const handleAddBudget = () => {
    const title = prompt("Nom de la ligne de cotisation ou financement public à déclarer :");
    if (title) {
      setBudgetItems(prev => [
        ...prev,
        {
          id: `b-${Date.now()}`,
          title,
          amount: "À définir",
          status: "En attente"
        }
      ]);
    }
  };

  // Static list for validation steps helper
  const validationSteps = [
    { id: "s-1", title: "1. Enquête Publique 90 J.", desc: "Recueil des avis publics" },
    { id: "s-2", title: "2. Conformité de Formulation", desc: "Relit technique légistique" },
    { id: "s-3", title: "3. Vote de la CTC", desc: "Validation de co-gouvernance" },
    { id: "s-4", title: "4. Homologation Ministérielle", desc: "Dépôt J.O. de la RDC" }
  ];

  // Local state for searching within history in sidebar
  const [historySearchQuery, setHistorySearchQuery] = useState("");

  // Get unique list of editors/modifying users for the current selected document history
  const historyEditors = useMemo(() => {
    if (!versions) return [];
    
    // Create map for unique users based on email
    const unique = new Map<string, { name: string; email: string; avatarColor: string; role: string; count: number }>();
    
    versions.forEach(v => {
      const emailLower = v.email.toLowerCase();
      const existing = unique.get(emailLower);
      if (existing) {
        existing.count += 1;
      } else {
        // Find inside collaborators to get their exact role / avatarColor
        const match = collaborators.find(c => c.email.toLowerCase() === emailLower);
        unique.set(emailLower, {
          name: v.author,
          email: v.email,
          avatarColor: match?.avatarColor || "#4B5563",
          role: match?.role || "Expert Rédacteur",
          count: 1
        });
      }
    });
    
    return Array.from(unique.values());
  }, [versions, collaborators]);

  // Helper selectors based on ACTIVE TAB
  const isEditorMode = activeTab === "editor";
  const isHistoryMode = activeTab === "history";
  const isExpertsMode = activeTab === "experts";
  const isMeetingsMode = activeTab === "meetings";
  const isFinancialMode = activeTab === "financial";
  const isValidationMode = activeTab === "validation";

  return (
    <aside className="w-80 border-r border-white/10 bg-black/45 flex flex-col h-full shrink-0 backdrop-blur-md">
      {/* App Header Branding Banner */}
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 bg-emerald-500 rounded-lg flex items-center justify-center text-black font-extrabold shadow-[0_0_15px_rgba(16,185,129,0.5)]">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm tracking-tight">Portail CNETP RDC</h1>
            <p className="text-[11px] text-slate-400 font-medium">Co-gouvernance & Normes</p>
          </div>
        </div>
      </div>

      {/* Main Dynamically Rendered Navigation Lists Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* TOP DYNAMIC BLOCK */}
        {isEditorMode && (
          <div>
            <div className="flex items-center justify-between mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                Documents / Normes
              </h2>
              <button
                onClick={onAddNewDoc}
                className="text-[10px] font-bold text-emerald-400 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs"
                title="Créer une nouvelle rédaction de norme (Avant-projet)"
              >
                <Plus className="h-3 w-3" />
                Nouveau
              </button>
            </div>

            <div className="space-y-1">
              {documents.length === 0 ? (
                <p className="text-[11px] text-slate-500 italic p-3 text-center border border-dashed border-white/5 rounded-lg">
                  Aucun projet de norme disponible.
                </p>
              ) : (
                documents.map((doc) => {
                  const isSelected = doc.id === selectedDocId;
                  let categoryColor = "bg-white/5 text-slate-300 border-white/10";
                  if (doc.category === "Qualité") categoryColor = "bg-blue-500/10 text-blue-400 border-blue-500/20";
                  if (doc.category === "Sécurité") categoryColor = "bg-amber-500/10 text-amber-400 border-amber-500/20";
                  if (doc.category === "Éthique") categoryColor = "bg-purple-500/10 text-purple-400 border-purple-500/20";

                  return (
                    <button
                      key={doc.id}
                      id={`doc-item-${doc.id}`}
                      onClick={() => onSelectDoc(doc.id)}
                      className={`w-full text-left p-3.5 rounded-lg border transition-all duration-200 flex flex-col gap-1.5 leading-tight ${
                        isSelected
                          ? "bg-white/10 border-emerald-500/40 shadow-[0_4px_12px_rgba(16,185,129,0.05)] text-white"
                          : "bg-transparent border-transparent hover:bg-white/5 hover:border-white/5 text-slate-400 hover:text-white"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 w-full">
                        <span className={`font-semibold text-xs truncate max-w-[150px] ${isSelected ? "text-white" : "text-slate-300 group-hover:text-white"}`}>
                          {doc.title}
                        </span>
                        <span className={`text-[9.5px] px-1.5 py-0.5 rounded-full font-bold border shrink-0 ${categoryColor}`}>
                          {doc.category}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="font-mono bg-white/5 border border-white/5 px-1.5 rounded text-slate-400 font-semibold">
                          {doc.code}
                        </span>
                        <span className="truncate max-w-[100px] text-[10px]">Par {doc.updatedBy.split(" ")[0]}</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        )}

        {isHistoryMode && (
          <div>
            {/* Search query input for Norms under History tab */}
            <div className="px-2 mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Rechercher une norme..."
                  value={historySearchQuery}
                  onChange={(e) => setHistorySearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-lg border border-white/10 bg-black/55 text-xs text-white focus:outline-hidden placeholder-slate-500 font-semibold"
                />
              </div>
            </div>

            <div className="flex items-center justify-between mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                Documents / Normes
              </h2>
            </div>

            <div className="space-y-1">
              {documents.filter(doc => 
                doc.title.toLowerCase().includes(historySearchQuery.toLowerCase()) || 
                doc.code.toLowerCase().includes(historySearchQuery.toLowerCase())
              ).length === 0 ? (
                <p className="text-[11px] text-slate-500 italic p-3 text-center border border-dashed border-white/5 rounded-lg">
                  Aucun projet correspondant.
                </p>
              ) : (
                documents.filter(doc => 
                  doc.title.toLowerCase().includes(historySearchQuery.toLowerCase()) || 
                  doc.code.toLowerCase().includes(historySearchQuery.toLowerCase())
                ).map((doc) => {
                  const isSelected = doc.id === selectedDocId;
                  let categoryColor = "bg-white/5 text-slate-300 border-white/10";
                  if (doc.category === "Qualité") categoryColor = "bg-blue-500/10 text-blue-400 border-blue-500/20";
                  if (doc.category === "Sécurité") categoryColor = "bg-amber-500/15 text-amber-400 border-amber-500/20";
                  if (doc.category === "Éthique") categoryColor = "bg-purple-500/10 text-purple-400 border-purple-500/20";

                  return (
                    <button
                      key={doc.id}
                      id={`doc-item-hist-${doc.id}`}
                      onClick={() => {
                        onSelectDoc(doc.id);
                        if (onSelectHistoryAuthorEmail) {
                          onSelectHistoryAuthorEmail(null); // click in doc: reset filter to see entire history
                        }
                      }}
                      className={`w-full text-left p-3.5 rounded-lg border transition-all duration-200 flex flex-col gap-1.5 leading-tight cursor-pointer ${
                        isSelected
                          ? "bg-white/10 border-emerald-500/40 shadow-[0_4px_12px_rgba(16,185,129,0.05)] text-white"
                          : "bg-transparent border-transparent hover:bg-white/5 hover:border-white/5 text-slate-400 hover:text-white"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 w-full">
                        <span className={`font-semibold text-xs truncate max-w-[150px] ${isSelected ? "text-white" : "text-slate-300 group-hover:text-white"}`}>
                          {doc.title}
                        </span>
                        <span className={`text-[9.5px] px-1.5 py-0.5 rounded-full font-bold border shrink-0 ${categoryColor}`}>
                          {doc.category}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="font-mono bg-white/5 border border-white/5 px-1.5 rounded text-slate-400 font-semibold">
                          {doc.code}
                        </span>
                        <span className="truncate max-w-[100px] text-[10px]">Par {doc.updatedBy.split(" ")[0]}</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        )}

        {isExpertsMode && (
          <div className="space-y-4">
            {/* Search query input replacing create buttons */}
            <div className="px-2">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Rechercher groupe ou expert..."
                  value={expertSearchQuery}
                  onChange={(e) => setExpertSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-lg border border-white/10 bg-black/55 text-xs text-white focus:outline-hidden placeholder-slate-500 font-semibold"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3 px-2">
                <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                  <Award className="h-3.5 w-3.5 text-slate-400" />
                  Groupes de Travail (WG)
                </h2>
              </div>

              <div className="space-y-1.5">
                {workingGroups.filter(wg => 
                  wg.code.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                  wg.title.toLowerCase().includes(expertSearchQuery.toLowerCase())
                ).length === 0 ? (
                  <p className="text-[11px] text-slate-500 italic p-3 text-center border border-dashed border-white/5 rounded-lg">
                    Aucun groupe trouvé.
                  </p>
                ) : (
                  workingGroups.filter(wg => 
                    wg.code.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                    wg.title.toLowerCase().includes(expertSearchQuery.toLowerCase())
                  ).map((wg) => {
                    const isSelected = expertSelectionType === "wg" && wg.id === selectedWorkingGroupId;
                    return (
                      <button
                        key={wg.id}
                        type="button"
                        onClick={() => {
                          setExpertSelectionType("wg");
                          setSelectedWorkingGroupId(wg.id);
                        }}
                        className={`w-full p-3 rounded-lg border transition-all duration-200 text-left block cursor-pointer ${
                          isSelected
                            ? "bg-emerald-500/10 border-emerald-500/35 text-emerald-400 shadow-[0_4px_12px_rgba(16,185,129,0.05)]"
                            : "bg-white/[0.02] hover:bg-white/[0.05] border-white/5 hover:border-white/10 text-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1.5">
                          <span className={`font-mono text-[9.5px] font-bold px-1.5 rounded ${
                            isSelected 
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" 
                              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          }`}>
                            {wg.code}
                          </span>
                          <span className="text-[9px] font-bold text-slate-500 bg-white/5 px-1.5 py-0.5 rounded-full uppercase tracking-tight">
                            {wg.tag}
                          </span>
                        </div>
                        <p className={`text-xs font-semibold mt-1.5 line-clamp-1 ${isSelected ? "text-white" : "text-slate-200"}`}>{wg.title}</p>
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {isMeetingsMode && (
          <div>
            <div className="flex items-center justify-between mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-400" />
                Réunions Planifiées
              </h2>
              <button
                type="button"
                onClick={handleAddMeeting}
                className="text-[10px] font-bold text-emerald-400 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs"
              >
                <Plus className="h-3 w-3" />
                Planifier
              </button>
            </div>

            <div className="space-y-1.5">
              {meetingsList.map((m) => (
                <div 
                  key={m.id}
                  className="p-3 bg-white/[0.02] border border-white/5 rounded-lg text-left"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-mono font-bold leading-none">{m.date}</span>
                    <span className={`text-[8.5px] px-1 rounded font-bold uppercase ${
                      m.status === "Terminé" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}>
                      {m.status}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-white mt-1.5 leading-tight line-clamp-1">{m.title}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {isFinancialMode && (
          <div>
            <div className="flex items-center justify-between mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                <Coins className="h-3.5 w-3.5 text-slate-400" />
                Cotisations & Budgets
              </h2>
              <button
                type="button"
                onClick={handleAddBudget}
                className="text-[10px] font-bold text-emerald-400 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs"
              >
                <Plus className="h-3 w-3" />
                Déclarer
              </button>
            </div>

            <div className="space-y-1.5">
              {budgetItems.map((b) => (
                <div 
                  key={b.id}
                  className="p-3 bg-white/[0.02] border border-white/5 rounded-lg text-left"
                >
                  <p className="text-xs font-bold text-white line-clamp-1">{b.title}</p>
                  <div className="flex items-center justify-between mt-1.5 font-mono text-[9px]">
                    <span className="font-semibold text-emerald-450">{b.amount}</span>
                    <span className="text-slate-500 font-semibold">{b.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {isValidationMode && (
          <div>
            <div className="flex items-center mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
                <CheckSquare className="h-3.5 w-3.5 text-slate-400" />
                Processus Légistique ISO
              </h2>
            </div>

            <div className="space-y-1.5">
              {validationSteps.map((step) => (
                <div 
                  key={step.id}
                  className="p-3 bg-white/[0.02] border border-white/5 rounded-lg text-left hover:border-emerald-500/10 transition-colors"
                >
                  <p className="text-xs font-bold text-emerald-400">{step.title}</p>
                  <p className="text-[10px] text-slate-500 leading-normal mt-0.5">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BOTTOM DYNAMIC PRESENCE / EXPERTS LIST BLOCK */}
        <div>
          <div className="mb-3 px-2 flex items-center justify-between pt-4 border-t border-white/5">
            <h2 className="text-xs font-semibold text-slate-500 tracking-wider uppercase flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-slate-400" />
              {isEditorMode && "Collaborateurs"}
              {isHistoryMode && "Éditeurs de la Norme"}
              {isExpertsMode && "Experts du CNETP"}
              {isMeetingsMode && "Validations Assemblée"}
              {isFinancialMode && "Trésoriers & Signataires"}
              {isValidationMode && "Auditeurs Légistiques"}
            </h2>

            {isEditorMode && (
              <button
                type="button"
                onClick={() => {
                  const name = prompt("Saisissez le nom de l'expert d'un autre WG à inviter sur cette norme :");
                  if (name) {
                    alert(`Invitation transmise avec succès à l'expert "${name}". Il recevra ses droits d'accès après validation.`);
                  }
                }}
                className="text-[10px] font-bold text-emerald-400 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 px-2 py-0.5 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs"
                title="Inviter un expert externe"
              >
                <Plus className="h-3 w-3" />
                Inviter
              </button>
            )}
          </div>
          
          <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed px-2 mb-2">
            {isEditorMode && "Membres du Groupe de Travail (WG) affectés :"}
            {isHistoryMode && "Auteurs des modifications enregistrées :"}
            {isExpertsMode && "Experts actifs du comité d'évaluation :"}
            {isMeetingsMode && "Présences certifiées signataires du PV :"}
            {isFinancialMode && "Responsables et directeurs financiers :"}
            {isValidationMode && "Experts constitutionnels ITP :"}
          </p>

          <div className="space-y-2">
            {isHistoryMode ? (
              historyEditors.length === 0 ? (
                <p className="text-[11px] text-slate-500 italic p-3 text-center border border-dashed border-white/5 rounded-lg">
                  Aucun éditeur historique pour cette norme.
                </p>
              ) : (
                historyEditors.map((editor) => {
                  const isSelected = selectedHistoryAuthorEmail?.toLowerCase() === editor.email.toLowerCase();
                  
                  return (
                    <button
                      key={editor.email}
                      type="button"
                      onClick={() => {
                        if (onSelectHistoryAuthorEmail) {
                          onSelectHistoryAuthorEmail(isSelected ? null : editor.email);
                        }
                      }}
                      className={`w-full text-left p-2.5 rounded-lg border flex items-center gap-3 transition-all duration-200 group relative cursor-pointer ${
                        isSelected
                          ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-xs"
                          : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                      }`}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10"
                        style={{ backgroundColor: editor.avatarColor }}
                      >
                        {editor.name.split(" ").map((n: string) => n[0]).join("")}
                        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-emerald-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <p className={`text-xs font-semibold truncate ${isSelected ? "text-emerald-400" : "text-slate-200"}`}>{editor.name}</p>
                          <span className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-tighter ${
                            isSelected 
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/30" 
                              : "bg-white/5 text-slate-400 font-medium"
                          }`}>
                            {editor.count} {editor.count > 1 ? "edits" : "edit"}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 truncate mt-0.5">{editor.role}</p>
                      </div>
                    </button>
                  );
                })
              )
            ) : isExpertsMode ? (
              experts.filter(exp => 
                exp.name.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                exp.structure.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                exp.role.toLowerCase().includes(expertSearchQuery.toLowerCase())
              ).length === 0 ? (
                <p className="text-[11px] text-slate-500 italic p-3 text-center border border-dashed border-white/5 rounded-lg">
                  Aucun expert trouvé.
                </p>
              ) : (
                experts.filter(exp => 
                  exp.name.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                  exp.structure.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                  exp.role.toLowerCase().includes(expertSearchQuery.toLowerCase())
                ).map((exp) => {
                  const isSelected = expertSelectionType === "expert" && exp.id === selectedExpertId;
                  
                  return (
                    <button
                      key={exp.id}
                      type="button"
                      onClick={() => {
                        setExpertSelectionType("expert");
                        setSelectedExpertId(exp.id);
                      }}
                      className={`w-full text-left p-2.5 rounded-lg border flex items-center gap-3 transition-all duration-200 group relative cursor-pointer ${
                        isSelected
                          ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-xs"
                          : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                      }`}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10 bg-slate-700/80"
                      >
                        {exp.name.split(" ").map((n: string) => n[0]).join("")}
                        {exp.isApproved && (
                          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-emerald-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <p className={`text-xs font-semibold truncate ${isSelected ? "text-emerald-400" : "text-slate-200"}`}>{exp.name}</p>
                          {isSelected && (
                            <span className="text-[8px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-400/30 px-1 py-0.5 rounded shrink-0 uppercase tracking-tighter">
                              SÉLEC
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500 truncate mt-0.5">{exp.role} ({exp.structure.split(" ")[0]})</p>
                      </div>
                    </button>
                  );
                })
              )
            ) : (
              collaborators.map((col) => {
                const isActiveUser = activeCollaborator?.id === col.id;
                
                // Let's formulate role descriptions based on active mode
                let displayedRole = col.role;
                if (isMeetingsMode) {
                  displayedRole = col.role.includes("Secrétaire") ? "Greffier de PV" : "Délégué de Quorum";
                } else if (isFinancialMode) {
                  displayedRole = col.role.includes("Secrétaire") ? "Auditeur Principal" : "Directeur Trésorerie";
                } else if (isValidationMode) {
                  displayedRole = col.role.includes("Secrétaire") ? "Conseiller Juridique" : "Rapporteur Légistique";
                }

                return (
                  <button
                    key={col.id}
                    id={`col-item-${col.id}`}
                    onClick={() => onSelectCollaborator(col)}
                    className={`w-full text-left p-2.5 rounded-lg border flex items-center gap-3 transition-all duration-200 group relative ${
                      isActiveUser && isEditorMode
                        ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-xs"
                        : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                    }`}
                  >
                    <div
                      className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10"
                      style={{ backgroundColor: col.avatarColor }}
                    >
                      {col.name.split(" ").map(n => n[0]).join("")}
                      {col.isActive && (
                        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-emerald-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <p className={`text-xs font-semibold truncate ${isActiveUser ? "text-emerald-400" : "text-slate-200"}`}>{col.name}</p>
                        {isActiveUser && isEditorMode && (
                          <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-400/35 px-1.5 rounded shrink-0 uppercase tracking-tighter">
                            ACTIF
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 truncate mt-0.5">{displayedRole}</p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

      </div>

      {/* Footer Statistics Bar */}
      <div 
        id="sidebar-footer-stats"
        className="p-3.5 border-t border-white/5 bg-black/90 text-slate-500 text-[10px] font-semibold flex flex-col gap-2.5 tracking-wide"
      >
        <div className="flex items-center justify-between uppercase">
          <span className="font-mono text-[9px] text-slate-500">ISO Compliance Mode</span>
          <span className="flex items-center gap-1 text-[9px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
            Sync
          </span>
        </div>
        {userRole && (
          <div className="flex items-center justify-between pt-1.5 border-t border-white/5">
            <span className="text-[9px] text-slate-400 uppercase">Poste Actif :</span>
            <span className="text-[9px] font-bold text-amber-400 bg-amber-400/10 border border-amber-400/25 px-1.5 py-0.5 rounded uppercase">
              {userRole === "ADMIN" ? "Administrateur" : 
               userRole === "RAP_CTM" ? "Rapporteur CTM" :
               userRole === "SEC_PERM" ? "Secrétaire SG" :
               userRole === "PRES_CTM" ? "Président CTM" :
               userRole === "GEST_COMP" ? "Comptable" :
               userRole === "COORD_CTC" ? "Coordonnateur CTC" : "Membre Expert"}
            </span>
          </div>
        )}
        <div className="pt-1.5">
          <button
            type="button"
            onClick={onOpenProfileModal}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/15 text-emerald-400 text-[9.5px] font-bold uppercase tracking-wider transition-all cursor-pointer shadow-sm hover:border-emerald-550 focus:outline-hidden"
            title="Ouvrir la page de configuration du profil de test"
          >
            <span>👤 Configurer Profil Test</span>
            <span className="text-white">&rarr;</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
