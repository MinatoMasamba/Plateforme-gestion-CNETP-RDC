import { useState, useEffect, useMemo } from "react";
import { FileText, History, HelpCircle, Loader, CheckCircle2, AlertTriangle, RefreshCw, Users, Vote, Landmark, BookOpen, ChevronDown, Shield, Award } from "lucide-react";
import Sidebar from "./components/Sidebar";
import EditorArea from "./components/EditorArea";
import HistoryArea from "./components/HistoryArea";
import ExpertsModule from "./components/ExpertsModule";
import MeetingsVotesModule from "./components/MeetingsVotesModule";
import FinancialModule from "./components/FinancialModule";
import ValidationPublicModule from "./components/ValidationPublicModule";
import LegistiqueModule from "./components/LegistiqueModule";
import ProfileSimulationModal from "./components/ProfileSimulationModal";
import MessagingWidget, { ChatContact, ChatMessage } from "./components/MessagingWidget";
import { Document, DocumentVersion, Collaborator } from "./types";

// Données mockées par défaut (pour que l’app fonctionne sans API)
const DEFAULT_DOCUMENTS: Document[] = [
  {
    id: "doc-1",
    title: "Eurocode 8 - Conception parasismique",
    code: "CNETP-EC8-1",
    description: "Règles générales pour la conception parasismique en RDC.",
    content: "Article 1.\nLa présente norme définit...\n\nArticle 2.\nSpécifications liées...",
    category: "Sécurité",
    updatedAt: new Date().toISOString(),
    updatedBy: "Prof. Masamba",
    updatedByEmail: "edmasamba100@gmail.com",
    references: [],
    driveFolderUrl: "",
    meetMeetingUrl: ""
  }
];

const DEFAULT_COLLABORATORS: Collaborator[] = [
  {
    id: "col-1",
    name: "Prof. Masamba Édouard",
    email: "edmasamba100@gmail.com",
    role: "Président scientifique",
    avatarColor: "#10b981",
    isActive: true
  },
  {
    id: "col-2",
    name: "Marie Laurent",
    email: "marie.laurent@cnetp.cd",
    role: "Secrétaire technique",
    avatarColor: "#3b82f6",
    isActive: true
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<"editor" | "history" | "experts" | "meetings" | "financial" | "validation" | "legistique">("editor");

  // États pour la simulation de profil
  const [userRole, setUserRole] = useState<string>("ADMIN");
  const [authUser, setAuthUser] = useState<{ email: string } | null>({ email: "edmasamba100@gmail.com" });
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [testProfile, setTestProfile] = useState({
    name: "Prof. Masamba Édouard",
    email: "edmasamba100@gmail.com",
    structure: "Université de Kinshasa (UNIKIN)",
    roleId: "ADMIN",
    dailyRate: 180,
    monthlyResearchAllowance: 800,
    payoutMethod: "Equity BCDC" as const,
    accountDetails: "00018-9923812-71",
    presenceCount: 8
  });

  const CNETP_ROLES = [
    { id: "ADMIN", name: "Administrateur technique", badgeColor: "bg-red-500/10 text-red-400" },
    { id: "RAP_CTM", name: "Rapporteur CTM", badgeColor: "bg-amber-500/10 text-amber-400" },
    { id: "SEC_PERM", name: "Secrétaire Permanent", badgeColor: "bg-blue-500/10 text-blue-400" },
    { id: "PRES_CTM", name: "Président CTM", badgeColor: "bg-emerald-500/10 text-emerald-400" },
    { id: "GEST_COMP", name: "Comptable", badgeColor: "bg-purple-500/10 text-purple-400" },
    { id: "COORD_CTC", name: "Coordonnateur CTC", badgeColor: "bg-pink-500/10 text-pink-400" },
    { id: "LEGISTE", name: "Expert Légiste", badgeColor: "bg-teal-500/10 text-teal-400" },
    { id: "MEMBRE_P", name: "Membre Permanent", badgeColor: "bg-slate-500/10 text-slate-300" }
  ];
  const currentRoleObj = CNETP_ROLES.find(r => r.id === userRole) || CNETP_ROLES[0];

  // Données principales (chargées depuis API ou valeurs par défaut)
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [activeCollaborator, setActiveCollaborator] = useState<Collaborator | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [selectedHistoryAuthorEmail, setSelectedHistoryAuthorEmail] = useState<string | null>(null);

  const [workingGroups, setWorkingGroups] = useState([
    { id: "wg-8.1", code: "WG 8.1", title: "Matériaux de Construction Locaux", tag: "Actif" },
    { id: "wg-1.1", code: "WG 1.1", title: "Sols & Géo-mécanique", tag: "Session libre" }
  ]);

  const [experts, setExperts] = useState<any[]>([
    { id: "exp-1", name: "Prof. Masamba Édouard", email: "edmasamba100@gmail.com", structure: "UNIKIN", role: "Président", isApproved: true },
    { id: "exp-2", name: "Ir. Chantal Mwamba", email: "chantal@cnetp.cd", structure: "OVD", role: "Secrétaire", isApproved: true }
  ]);

  const [selectedWorkingGroupId, setSelectedWorkingGroupId] = useState<string>("wg-8.1");
  const [selectedExpertId, setSelectedExpertId] = useState<string>("exp-1");
  const [expertSelectionType, setExpertSelectionType] = useState<"wg" | "expert">("expert");

  // Chat
  const chatContacts = useMemo<ChatContact[]>(() => {
    const list: ChatContact[] = [];
    collaborators.forEach(col => {
      if (col.email !== testProfile.email) {
        list.push({ ...col, isOnline: col.isActive, structure: "Secrétariat CNETP" });
      }
    });
    experts.forEach(exp => {
      if (exp.email !== testProfile.email && !list.some(l => l.email === exp.email)) {
        list.push({
          id: exp.id,
          name: exp.name,
          email: exp.email,
          role: exp.role,
          avatarColor: "#eab308",
          isOnline: exp.isApproved,
          structure: exp.structure
        });
      }
    });
    return list;
  }, [collaborators, experts, testProfile]);

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem("cnetp_secure_messages");
    return saved ? JSON.parse(saved) : [];
  });
  const [activeChatId, setActiveChatId] = useState<string>("col-1");
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  };

  // Chargement initial : on utilise les données mockées par défaut, pas d’appel API bloquant
  useEffect(() => {
    const timer = setTimeout(() => {
      setDocuments(DEFAULT_DOCUMENTS);
      setCollaborators(DEFAULT_COLLABORATORS);
      setActiveCollaborator(DEFAULT_COLLABORATORS[0]);
      if (DEFAULT_DOCUMENTS.length) setSelectedDocId(DEFAULT_DOCUMENTS[0].id);
      setIsLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  // Ici vous pourrez plus tard remplacer par de vrais appels API
  // sans casser l’affichage.

  const handleUpdateDocument = (updatedDoc: Document) => {
    setDocuments(prev => prev.map(d => d.id === updatedDoc.id ? updatedDoc : d));
  };

  const handleSaveVersion = async (content: string, comment: string) => {
    showToast("Fonctionnalité sauvegarde bientôt connectée à l’API", "info");
  };

  const handleRollbackVersion = async (versionNumber: number) => {
    showToast("Restauration désactivée en mode démo", "info");
  };

  const handleSelectCollaborator = (col: Collaborator) => {
    if (col.email !== testProfile.email) {
      setActiveChatId(col.id);
      setIsChatOpen(true);
      showToast(`Discussion ouverte avec ${col.name}`, "success");
    }
  };

  const handleSaveProfile = (updatedProfile: any) => {
    setTestProfile(updatedProfile);
    setUserRole(updatedProfile.roleId);
    setAuthUser({ email: updatedProfile.email });
    setIsProfileModalOpen(false);
    showToast(`Profil changé : ${updatedProfile.name} (${updatedProfile.roleId})`, "success");
  };

  const openChatWith = (userId: string) => {
    setActiveChatId(userId);
    setIsChatOpen(true);
  };

  const handleShareClause = (recipientId: string, clauseCode: string, excerpt: string) => {
    showToast(`Clause partagée avec ${recipientId}`, "info");
  };

  const handleSendMessage = (receiverId: string, text: string) => {
    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      senderId: "me",
      senderName: testProfile.name,
      receiverId,
      text,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, newMsg]);
    localStorage.setItem("cnetp_secure_messages", JSON.stringify([...messages, newMsg]));
  };

  const activeDocument = documents.find(doc => doc.id === selectedDocId) || null;

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#020204] flex flex-col items-center justify-center gap-4">
        <Loader className="h-9 w-9 text-emerald-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-400">Chargement de l’application...</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-[#020204] font-sans text-slate-300">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl bg-black/90 border border-white/10">
          {toast.type === "success" && <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
          {toast.type === "error" && <AlertTriangle className="h-5 w-5 text-red-400" />}
          <span className="text-xs">{toast.message}</span>
        </div>
      )}

      <Sidebar
        activeTab={activeTab}
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={setSelectedDocId}
        collaborators={collaborators}
        activeCollaborator={activeCollaborator}
        onSelectCollaborator={handleSelectCollaborator}
        onAddNewDoc={() => {}}
        workingGroups={workingGroups}
        experts={experts}
        selectedWorkingGroupId={selectedWorkingGroupId}
        setSelectedWorkingGroupId={setSelectedWorkingGroupId}
        selectedExpertId={selectedExpertId}
        setSelectedExpertId={setSelectedExpertId}
        expertSelectionType={expertSelectionType}
        setExpertSelectionType={setExpertSelectionType}
        versions={versions}
        selectedHistoryAuthorEmail={selectedHistoryAuthorEmail}
        onSelectHistoryAuthorEmail={setSelectedHistoryAuthorEmail}
        userRole={userRole}
        onChangeRole={setUserRole}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
      />

      <main className="flex-1 flex flex-col h-full min-w-0 bg-[#06060c]/20 relative">
        <nav className="h-14 border-b border-white/10 px-6 flex items-center justify-between bg-black/40 backdrop-blur-md">
          <div className="flex gap-1">
            {(["editor","history","experts","meetings","financial","validation"] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-2 text-[10.5px] font-bold uppercase border-b-2 ${
                  activeTab === tab ? "border-emerald-500 text-emerald-400" : "border-transparent text-slate-400"
                }`}
              >
                {tab === "editor" && "Éditeur"}
                {tab === "history" && "Historique"}
                {tab === "experts" && "Experts"}
                {tab === "meetings" && "Réunions"}
                {tab === "financial" && "Finances"}
                {tab === "validation" && "Bibliothèque"}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">
              Connecté : <span className="text-white font-bold">{authUser?.email || testProfile.email}</span>
            </span>
            <button
              onClick={() => setIsProfileModalOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/5 text-emerald-400 text-xs font-bold"
            >
              {currentRoleObj.name}
            </button>
          </div>
        </nav>

        <div className="flex-1 overflow-auto">
          {activeTab === "experts" && (
            <ExpertsModule
              experts={experts}
              setExperts={setExperts}
              workingGroups={workingGroups}
              selectedWorkingGroupId={selectedWorkingGroupId}
              setSelectedWorkingGroupId={setSelectedWorkingGroupId}
              selectedExpertId={selectedExpertId}
              setSelectedExpertId={setSelectedExpertId}
              expertSelectionType={expertSelectionType}
              setExpertSelectionType={setExpertSelectionType}
              onOpenChat={openChatWith}
            />
          )}
          {activeTab === "meetings" && (
            <MeetingsVotesModule experts={experts} workingGroups={workingGroups} userRole={userRole} simulatedProfile={testProfile} />
          )}
          {activeTab === "financial" && (
            <FinancialModule userRole={userRole} experts={experts} simulatedProfile={testProfile} />
          )}
          {activeTab === "validation" && <ValidationPublicModule />}
          {activeTab === "legistique" && <LegistiqueModule userRole={userRole} />}
          {activeTab === "editor" && activeDocument && activeCollaborator && (
            <EditorArea
              document={activeDocument}
              activeCollaborator={activeCollaborator}
              onSave={handleSaveVersion}
              onCancel={() => {}}
              isSaving={isSaving}
              onUpdateDocument={handleUpdateDocument}
              chatContacts={chatContacts}
              onShareClause={handleShareClause}
            />
          )}
          {activeTab === "history" && activeDocument && (
            <HistoryArea
              document={activeDocument}
              versions={versions}
              onRollback={handleRollbackVersion}
              isRollingBack={isRollingBack}
              activeCollaborator={activeCollaborator!}
              selectedHistoryAuthorEmail={selectedHistoryAuthorEmail}
              onClearHistoryAuthorFilter={() => setSelectedHistoryAuthorEmail(null)}
            />
          )}
        </div>
      </main>

      <MessagingWidget
        contacts={chatContacts}
        currentProfile={testProfile}
        messages={messages}
        onSendMessage={handleSendMessage}
        activeChatId={activeChatId}
        setActiveChatId={setActiveChatId}
        isOpen={isChatOpen}
        setIsOpen={setIsChatOpen}
      />

      <ProfileSimulationModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        profile={testProfile}
        onSave={handleSaveProfile}
      />
    </div>
  );
}