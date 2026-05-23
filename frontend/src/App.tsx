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
import { useNorms, useExperts } from "./hooks/useNormsAndExperts";

// Données mockées par défaut (fallback si API n'est pas disponible)
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

  // ✅ Charger les normes et experts depuis l'API
  const { norms: apiNorms, isLoading: normsLoading } = useNorms();
  const { experts: apiExperts, isLoading: expertsLoading } = useExperts();

  // Données principales (API ou fallback)
  const [documents, setDocuments] = useState<Document[]>(DEFAULT_DOCUMENTS);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [collaborators, setCollaborators] = useState<Collaborator[]>(DEFAULT_COLLABORATORS);
  const [activeCollaborator, setActiveCollaborator] = useState<Collaborator | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [selectedHistoryAuthorEmail, setSelectedHistoryAuthorEmail] = useState<string | null>(null);

  // Utiliser les données API si disponibles
  useEffect(() => {
    if (apiNorms && apiNorms.length > 0) {
      setDocuments(apiNorms);
      setSelectedDocId(apiNorms[0].id);
    }
  }, [apiNorms]);

  useEffect(() => {
    if (apiExperts && apiExperts.length > 0) {
      setCollaborators(apiExperts as any[]);
      setActiveCollaborator((apiExperts[0] as any) || null);
    }
  }, [apiExperts]);

  const [workingGroups, setWorkingGroups] = useState([
    { id: "wg-8.1", code: "WG 8.1", title: "Matériaux de Construction Locaux", tag: "Actif" },
    { id: "wg-1.1", code: "WG 1.1", title: "Sols & Géo-mécanique", tag: "Session libre" }
  ]);

  const [experts, setExperts] = useState<any[]>([
    { id: "exp-1", name: "Prof. Masamba Édouard", email: "edmasamba100@gmail.com", structure: "UNIKIN", role: "Président", isApproved: true },
    { id: "exp-2", name: "Ir. Chantal Mwamba", email: "chantal@cnetp.cd", structure: "OVD", role: "Secrétaire", isApproved: true }
  ]);

  useEffect(() => {
    if (apiExperts && apiExperts.length > 0) {
      setExperts(apiExperts);
    }
  }, [apiExperts]);

  const selectedDoc = useMemo(() => documents.find(doc => doc.id === selectedDocId) || documents[0], [documents, selectedDocId]);

  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "msg-1", sender: "Prof. Masamba", text: "Normes de sécurité mises à jour", timestamp: new Date(Date.now() - 3600000).toISOString(), isUser: false }
  ]);

  const chatContacts: ChatContact[] = [
    { id: "contact-1", name: "Prof. Masamba", lastMessage: "Normes de sécurité mises à jour", avatar: "👨‍🏫" }
  ];

  const handleSendMessage = (text: string) => {
    const newMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "Vous",
      text,
      timestamp: new Date().toISOString(),
      isUser: true
    };
    setMessages([...messages, newMessage]);
  };

  const [isLoading] = useState(false);

  return (
    <div className="flex h-screen bg-[#020204] text-slate-300 font-sans overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[#06060c] border border-white/5 rounded-2xl p-8">
              <Loader className="w-8 h-8 animate-spin text-emerald-400 mb-4" />
              <p className="text-sm">Chargement...</p>
            </div>
          </div>
        )}

        {activeTab === "editor" && (
          <EditorArea
            selectedDoc={selectedDoc}
            documents={documents}
            selectedDocId={selectedDocId}
            setSelectedDocId={setSelectedDocId}
            setDocuments={setDocuments}
            activeCollaborator={activeCollaborator}
            setActiveCollaborator={setActiveCollaborator}
            collaborators={collaborators}
            versions={versions}
            onVersionSelect={(versionId: string) => {
              const version = versions.find(v => v.id === versionId);
              if (version && selectedDocId) {
                setDocuments(docs => docs.map(doc => 
                  doc.id === selectedDocId ? { ...doc, content: version.content } : doc
                ));
              }
            }}
            selectedHistoryAuthorEmail={selectedHistoryAuthorEmail}
            setSelectedHistoryAuthorEmail={setSelectedHistoryAuthorEmail}
          />
        )}

        {activeTab === "history" && <HistoryArea versions={versions} />}

        {activeTab === "experts" && (
          <ExpertsModule
            experts={experts}
            setExperts={setExperts}
            workingGroups={workingGroups}
            setWorkingGroups={setWorkingGroups}
            isLoading={expertsLoading}
          />
        )}

        {activeTab === "meetings" && <MeetingsVotesModule experts={experts} />}

        {activeTab === "financial" && (
          <FinancialModule
            userRole={userRole}
            testProfile={testProfile}
            setTestProfile={setTestProfile}
          />
        )}

        {activeTab === "validation" && <ValidationPublicModule documents={documents} />}

        {activeTab === "legistique" && <LegistiqueModule />}
      </main>

      <ProfileSimulationModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        userRole={userRole}
        setUserRole={setUserRole}
        CNETP_ROLES={CNETP_ROLES}
        currentRoleObj={currentRoleObj}
        testProfile={testProfile}
        setTestProfile={setTestProfile}
      />

      <MessagingWidget
        contacts={chatContacts}
        messages={messages}
        onSendMessage={handleSendMessage}
        profileBadge={currentRoleObj.name}
      />
    </div>
  );
}
