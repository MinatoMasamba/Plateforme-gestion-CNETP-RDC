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

export function StateArmoirie({ size = 44, dark = true }) {
  return (
    <div className="flex items-center gap-2 shrink-0 select-none">
      {/* 1. Bloc-Armoirie Circle */}
      <svg 
        width={size} 
        height={size} 
        viewBox="0 0 100 100" 
        className="shrink-0 drop-shadow-[0_1.5px_3px_rgba(0,0,0,0.2)]"
      >
        <circle cx="50" cy="50" r="46" fill={dark ? "#171717" : "#ffffff"} stroke="#d4af37" strokeWidth="1.5" />
        <circle cx="50" cy="50" r="41" fill="none" stroke="#d4af37" strokeWidth="0.5" strokeDasharray="3 2" />
        
        <path id="textPathTop" d="M 12 52 A 38 38 0 0 1 88 52" fill="none" />
        <text className="font-sans font-extrabold" fontSize="5.2" fill={dark ? "#e2e8f0" : "#334155"} letterSpacing="0.2">
          <textPath href="#textPathTop" startOffset="50%" textAnchor="middle">
            REP. DEM. DU CONGO
          </textPath>
        </text>
        
        <path id="textPathBottom" d="M 88 48 A 38 38 0 0 1 12 48" fill="none" />
        <text className="font-sans font-black" fontSize="5.5" fill={dark ? "#ffd700" : "#0095c9"} letterSpacing="0.3">
          <textPath href="#textPathBottom" startOffset="50%" textAnchor="middle">
            LE GOUVERNEMENT
          </textPath>
        </text>

        <g transform="translate(18, 22) scale(0.65)">
          <line x1="20" y1="65" x2="70" y2="15" stroke="#78350f" strokeWidth="3" strokeLinecap="round" />
          <polygon points="70,15 74,10 75,18 70,15" fill="#94a3b8" stroke="#334155" strokeWidth="0.5" />
          
          <path d="M 23 72 C 15 50 25 30 35 22 C 30 35 25 55 25 72 Z" fill="#fdfae6" stroke="#cbb281" strokeWidth="1" />
          
          <ellipse cx="48" cy="55" rx="14" ry="7" fill="#dc2626" stroke="#991b1b" strokeWidth="1" />
          
          <ellipse cx="48" cy="46" rx="15" ry="12" fill="#ffea00" stroke="#000" strokeWidth="1" />
          <path d="M 36 38 Q 30 30 38 34" fill="#ffea00" stroke="#000" strokeWidth="1" />
          <path d="M 60 38 Q 66 30 58 34" fill="#ffea00" stroke="#000" strokeWidth="1" />
          <circle cx="40" cy="42" r="1.5" fill="#000" />
          <circle cx="56" cy="42" r="1.5" fill="#000" />
          <circle cx="48" cy="38" r="1" fill="#000" />
          <path d="M 43 47 Q 48 50 53 47" stroke="#000" strokeWidth="1" fill="none" />
          <ellipse cx="43" cy="43" rx="2" ry="1.2" fill="#ffea00" stroke="#000" />
          <ellipse cx="53" cy="43" rx="2" ry="1.2" fill="#ffea00" stroke="#000" />
          <circle cx="43" cy="43" r="0.8" fill="#000" />
          <circle cx="53" cy="43" r="0.8" fill="#000" />
        </g>
        
        <path d="M 22 74 Q 50 83 78 74 L 75 79 Q 50 87 25 79 Z" fill="#db3832" stroke="#991b1b" strokeWidth="0.5" />
        <text x="50" y="78.5" fontSize="3.8" fill="#ffffff" fontWeight="bold" textAnchor="middle" letterSpacing="0.4">
          PAIX - JUSTICE - TRAVAIL
        </text>
      </svg>

      {/* 2. Ligne d’État (Congo Flag blue, yellow, red strip) */}
      <div className="w-[4px] h-[34px] flex flex-col rounded-sm overflow-hidden shrink-0">
        <div className="flex-1 bg-[#0095c9]" title="Bleu : Paix / Souveraineté" />
        <div className="h-[25%] bg-[#fff24b]" title="Jaune : Richesses du Pays" />
        <div className="flex-1 bg-[#db3832]" title="Rouge : Sang des Martyrs" />
      </div>
    </div>
  );
}

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
  testProfile?: any;
  isDarkMode?: boolean;
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
  onOpenProfileModal = () => {},
  testProfile,
  isDarkMode = true
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

  const sidebarBg = isDarkMode 
    ? "bg-[#06060c]/90 border-r border-white/10 text-slate-300" 
    : "bg-slate-50 border-r border-slate-250 text-slate-850 shadow-sm";

  const borderClass = isDarkMode ? "border-white/10" : "border-slate-200";
  const softBorderClass = isDarkMode ? "border-white/5" : "border-slate-150";
  const textTitleClass = isDarkMode ? "text-white font-bold" : "text-slate-900 font-extrabold";
  const subTextClass = isDarkMode ? "text-slate-400" : "text-slate-500 font-semibold";
  const buttonActiveBg = isDarkMode 
    ? "bg-blue-600/15 border-blue-500/30 text-blue-300 shadow-xs" 
    : "bg-blue-50 border-blue-200 text-blue-800 font-bold shadow-xs";
  const buttonInactiveBg = isDarkMode
    ? "bg-transparent border-transparent hover:bg-white/5 hover:border-white/5 text-slate-400 hover:text-white"
    : "bg-transparent border-transparent hover:bg-slate-100 hover:border-slate-100 text-slate-600 hover:text-slate-900";

  return (
    <aside className={`w-80 flex flex-col h-full shrink-0 backdrop-blur-md transition-colors duration-250 ${sidebarBg}`}>
      {/* App Header Branding Banner featuring official logo as per PDF guidelines */}
      <div className={`p-4 flex items-center gap-3 ${isDarkMode ? "border-b border-white/10 bg-black/15" : "border-b border-slate-200 bg-white"}`}>
        <StateArmoirie size={46} dark={isDarkMode} />
        <div className="min-w-0">
          <h1 className={`text-xs uppercase tracking-wider leading-none text-slate-450 ${isDarkMode ? "text-slate-400" : "text-slate-500 font-bold"}`}>
            SÉCRÉTARIAT TECHNIQUE
          </h1>
          <h2 className={`text-[12px] font-black tracking-tight leading-tight mt-1 uppercase ${isDarkMode ? "text-blue-500" : "text-blue-600"}`}>
            Portail CNETP RDC
          </h2>
          <p className="text-[10px] text-slate-500 font-mono font-semibold uppercase tracking-tight leading-none mt-0.5">
            M.I.T.P. & NUMÉRIQUE
          </p>
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
                className={`text-[10px] font-bold px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs border ${
                  isDarkMode
                    ? "text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20"
                    : "text-blue-600 hover:bg-blue-100 bg-blue-50 border-blue-200"
                }`}
                title="Créer une nouvelle rédaction de norme (Avant-projet)"
              >
                <Plus className="h-3 w-3" />
                Nouveau
              </button>
            </div>

            <div className="space-y-1">
              {documents.length === 0 ? (
                <p className={`text-[11px] italic p-3 text-center border border-dashed rounded-lg ${isDarkMode ? "text-slate-500 border-white/5" : "text-slate-450 border-slate-200"}`}>
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
                        isSelected ? buttonActiveBg : buttonInactiveBg
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 Q-full">
                        <span className={`font-semibold text-xs truncate max-w-[150px] ${isSelected ? (isDarkMode ? "text-white" : "text-blue-950") : (isDarkMode ? "text-slate-300" : "text-slate-700")}`}>
                          {doc.title}
                        </span>
                        <span className={`text-[9.5px] px-1.5 py-0.5 rounded-full font-bold border shrink-0 ${categoryColor}`}>
                          {doc.category}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className={`font-mono px-1.5 rounded font-semibold border ${isDarkMode ? "bg-white/5 border-white/5 text-slate-400" : "bg-slate-100 border-slate-200 text-slate-600"}`}>
                          {doc.code}
                        </span>
                        <span className="truncate max-w-[100px] text-[10px]">Par {doc.updatedBy.split(" ")[0]}</span>
                      </div>

                      {/* Interactive Scrutin indicator (Addressed "y'a pas de lien pour voter") */}
                      <div className={`mt-2 pt-2 border-t border-dashed flex items-center justify-between ${isDarkMode ? "border-white/5" : "border-slate-200"}`}>
                        <span className={`text-[10px] font-bold flex items-center gap-1 ${isDarkMode ? "text-slate-400" : "text-slate-600"}`}>
                          <span className={`inline-block w-1.5 h-1.5 rounded-full animate-pulse ${isDarkMode ? "bg-blue-500" : "bg-blue-500"}`}></span>
                          Avis officiel
                        </span>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border flex items-center gap-1 shrink-0 transition-all uppercase tracking-tight ${
                          isSelected
                            ? isDarkMode
                                ? "text-white border-blue-400 shadow-[0_0_8px_rgba(16,185,129,0.2)] bg-blue-500"
                                : "bg-blue-600 border-blue-500 text-white shadow-[0_0_8px_rgba(37,99,235,0.2)]"
                            : isDarkMode
                                ? "bg-blue-500/10 text-blue-500 border-blue-500/20 hover:bg-blue-500/20"
                                : "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
                        }`}>
                          🗳️ Voter
                        </span>
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
                        isSelected ? buttonActiveBg : buttonInactiveBg
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
                  (() => {
                    const getCmtNumber = (ctmStr: string) => {
                      if (!ctmStr) return null;
                      const match = ctmStr.match(/CTM\s*(\d+)/i);
                      return match ? match[1] : null;
                    };

                    const getWgCmtNumber = (wgCodeStr: string) => {
                      if (!wgCodeStr) return null;
                      const match = wgCodeStr.match(/(?:WG|wg)\s*(\d+)\.?/i);
                      return match ? match[1] : null;
                    };

                    const currentExpert = testProfile 
                      ? experts.find(e => e.email.toLowerCase() === testProfile.email.toLowerCase()) 
                      : experts.find(e => e.id === "exp-1");

                    return workingGroups.filter(wg => 
                      wg.code.toLowerCase().includes(expertSearchQuery.toLowerCase()) ||
                      wg.title.toLowerCase().includes(expertSearchQuery.toLowerCase())
                    ).map((wg) => {
                      const isSelected = expertSelectionType === "wg" && wg.id === selectedWorkingGroupId;
                      
                      const currentExpertCmtNum = currentExpert ? getCmtNumber(currentExpert.ctm) : null;
                      const wgCmtNum = getWgCmtNumber(wg.code);

                      const isSameCmt = currentExpertCmtNum && wgCmtNum ? currentExpertCmtNum === wgCmtNum : false;
                      const isMyWg = currentExpert?.wg && wg.code ? currentExpert.wg.toLowerCase().includes(wg.code.toLowerCase()) : false;

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
                              ? "bg-blue-500/10 border-blue-500/35 text-blue-400 shadow-[0_4px_12px_rgba(16,185,129,0.05)]"
                              : "bg-white/[0.02] hover:bg-white/[0.05] border-white/5 hover:border-white/10 text-slate-300"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-1.5">
                            <div className="flex items-center gap-1.5">
                              <span className={`font-mono text-[9.5px] font-bold px-1.5 rounded ${
                                isSelected 
                                  ? "bg-blue-500/20 text-blue-300 border border-blue-500/30" 
                                  : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              }`}>
                                {wg.code}
                              </span>
                              
                              {/* Relations badges */}
                              {isMyWg ? (
                                <span className="text-[8.5px] px-1 bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded font-extrabold uppercase scale-90 origin-left">
                                  Mon WG
                                </span>
                              ) : isSameCmt ? (
                                <span className="text-[8.5px] px-1 bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded font-extrabold uppercase scale-90 origin-left" title="Même Comité technique (Lecture Seule)">
                                  Même CTM
                                </span>
                              ) : (
                                <span className="text-[8.5px] px-1 bg-white/5 text-slate-500 border border-white/5 rounded font-bold uppercase scale-90 origin-left" title="Autre Comité (Accès restreint)">
                                  Hors CTM
                                </span>
                              )}
                            </div>
                            <span className="text-[9px] font-bold text-slate-500 bg-white/5 px-1.5 py-0.5 rounded-full uppercase tracking-tight">
                              {wg.tag}
                            </span>
                          </div>
                          <p className={`text-xs font-semibold mt-1.5 line-clamp-1 ${isSelected ? "text-white" : "text-slate-200"}`}>{wg.title}</p>
                          
                          {/* Parallel Norms Indicators */}
                          {(() => {
                            const getParallelNormsForWg = (wgCode: string) => {
                              switch (wgCode) {
                                case "WG 8.1":
                                  return ["Pr-RDC 801 (BTC)", "Pr-RDC 802 (Eco-Briques)", "Pr-RDC 803 (Recyclage)"];
                                case "WG 8.2":
                                  return ["Pr-RDC 812 (Ultrasons)", "Pr-RDC 813 (Mécanique)"];
                                case "WG 8.3":
                                  return ["Pr-RDC 821 (Label Vert)"];
                                case "WG 1.1":
                                  return ["Pr-RDC 101 (Argiles)", "Pr-RDC 102 (CBR Route)"];
                                case "WG 1.2":
                                  return ["Pr-RDC 112 (Anti-Érosion)"];
                                case "WG 2.3":
                                  return ["Pr-RDC 231 (Sismique)"];
                                case "WG 5.1":
                                  return ["Pr-RDC 501 (Enrobés Latérite)"];
                                case "WG 6.2":
                                  return ["Pr-RDC 611 (Assainissement)"];
                                default:
                                  return [];
                              }
                            };
                            const norms = getParallelNormsForWg(wg.code);
                            if (norms.length === 0) return null;
                            return (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {norms.map((norm, idx) => (
                                  <span 
                                    key={idx} 
                                    title={norm}
                                    className={`text-[8.5px] px-1 rounded font-mono font-bold tracking-tight border ${
                                      isSelected
                                        ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                                        : "bg-white/5 text-slate-400 border-white/5"
                                    }`}
                                  >
                                    {norm.split(" ")[0]}
                                  </span>
                                ))}
                              </div>
                            );
                          })()}
                        </button>
                      );
                    });
                  })()
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
                className={`text-[10px] font-bold px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs border ${
                  isDarkMode
                    ? "text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20"
                    : "text-blue-600 hover:bg-blue-100 bg-blue-50 border-blue-200"
                }`}
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
                      m.status === "Terminé" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
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
                className={`text-[10px] font-bold px-2 py-1 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs border ${
                  isDarkMode
                    ? "text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20"
                    : "text-blue-600 hover:bg-blue-100 bg-blue-50 border-blue-200"
                }`}
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
                    <span className="font-semibold text-blue-450">{b.amount}</span>
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
                  className="p-3 bg-white/[0.02] border border-white/5 rounded-lg text-left hover:border-blue-500/10 transition-colors"
                >
                  <p className="text-xs font-bold text-blue-400">{step.title}</p>
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
                className={`text-[10px] font-bold px-2 py-0.5 rounded transition-all flex items-center gap-1 cursor-pointer shadow-xs border ${
                  isDarkMode
                    ? "text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20"
                    : "text-blue-600 hover:bg-blue-100 bg-blue-50 border-blue-200"
                }`}
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
                          ? "bg-blue-500/15 border-blue-500/30 text-blue-400 shadow-xs"
                          : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                      }`}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10"
                        style={{ backgroundColor: editor.avatarColor }}
                      >
                        {editor.name.split(" ").map((n: string) => n[0]).join("")}
                        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-blue-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <p className={`text-xs font-semibold truncate ${isSelected ? "text-blue-400" : "text-slate-200"}`}>{editor.name}</p>
                          <span className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-tighter ${
                            isSelected 
                              ? "bg-blue-500/20 text-blue-300 border border-blue-400/30" 
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
                          ? "bg-blue-500/15 border-blue-500/30 text-blue-400 shadow-xs"
                          : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                      }`}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10 bg-slate-700/80"
                      >
                        {exp.name.split(" ").map((n: string) => n[0]).join("")}
                        {exp.isApproved && (
                          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-blue-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <p className={`text-xs font-semibold truncate ${isSelected ? "text-blue-400" : "text-slate-200"}`}>{exp.name}</p>
                          {isSelected && (
                            <span className="text-[8px] font-bold text-blue-400 bg-blue-500/10 border border-blue-400/30 px-1 py-0.5 rounded shrink-0 uppercase tracking-tighter">
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
                        ? "bg-blue-500/15 border-blue-500/30 text-blue-400 shadow-xs"
                        : "bg-black/10 border-white/5 hover:border-white/10 text-slate-300"
                    }`}
                  >
                    <div
                      className="h-8 w-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs relative ring-1 ring-white/10"
                      style={{ backgroundColor: col.avatarColor }}
                    >
                      {col.name.split(" ").map(n => n[0]).join("")}
                      {col.isActive && (
                        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-blue-500 border-2 border-slate-950 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <p className={`text-xs font-semibold truncate ${isActiveUser ? "text-blue-400" : "text-slate-200"}`}>{col.name}</p>
                        {isActiveUser && isEditorMode && (
                          <span className="text-[9px] font-bold text-blue-400 bg-blue-500/10 border border-blue-400/35 px-1.5 rounded shrink-0 uppercase tracking-tighter">
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
        className={`p-3.5 border-t text-[10px] font-semibold flex flex-col gap-2.5 tracking-wide transition-colors ${
          isDarkMode
            ? "border-white/5 bg-black/95 text-slate-500"
            : "border-slate-200 bg-slate-100 text-slate-600"
        }`}
      >
        <div className="flex items-center justify-between uppercase">
          <span className="font-mono text-[9px] text-slate-500">ISO Compliance Mode</span>
          <span className={`flex items-center gap-1 text-[9px] ${isDarkMode ? "text-slate-400" : "text-slate-600"}`}>
            <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${
              isDarkMode 
                ? "bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]" 
                : "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"
            }`}></span>
            Sync
          </span>
        </div>
        {userRole && (
          <div className={`flex items-center justify-between pt-1.5 border-t ${isDarkMode ? "border-white/5" : "border-slate-200"}`}>
            <span className={`text-[9px] uppercase ${isDarkMode ? "text-slate-400" : "text-slate-500"}`}>Poste Actif :</span>
            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
              isDarkMode 
                ? "text-amber-400 bg-amber-400/10 border border-amber-400/25" 
                : "text-blue-600 bg-blue-50 border border-blue-200"
            }`}>
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
            className={`w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg border text-[9.5px] font-bold uppercase tracking-wider transition-all cursor-pointer shadow-sm focus:outline-hidden ${
              isDarkMode
                ? "border-amber-500/20 bg-amber-500/5 hover:bg-amber-500/15 text-amber-400 hover:border-amber-400"
                : "border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-600 hover:border-blue-400"
            }`}
            title="Ouvrir la page de configuration du profil de test"
          >
            <span>👤 Configurer Profil Test</span>
            <span className={isDarkMode ? "text-amber-300" : "text-blue-500"}>&rarr;</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
