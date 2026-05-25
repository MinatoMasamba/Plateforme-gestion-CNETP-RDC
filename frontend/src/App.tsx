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
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Landing from "./components/LandingPage";
import Login from "./components/Login";
import Register from "./components/Register";
import PublicNormsPage from "./components/PublicNormsPage";
import ExpertInvitePage from "./components/ExpertInvitePage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/login/" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />
        <Route path="/auth/register/" element={<Register />} />
        <Route path="/public-norms" element={<PublicNormsPage />} />
        <Route path="/expert-invite" element={<ExpertInvitePage />} />
        <Route path="/app" element={<WorkspaceContainer />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export function WorkspaceContainer() {
  const navigate = useNavigate();
  // Navigation & Screen Tabs
  const [activeTab, setActiveTab] = useState<"editor" | "history" | "experts" | "meetings" | "financial" | "validation" | "legistique">("editor");

  // Simulated global role
  const [userRole, setUserRole] = useState<string>("ADMIN");
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [testProfile, setTestProfile] = useState({
    name: "Prof. Masamba Édouard",
    email: "edmasamba100@gmail.com",
    structure: "Université de Kinshasa (UNIKIN)",
    roleId: "ADMIN",
    dailyRate: 180,
    monthlyResearchAllowance: 800,
    payoutMethod: "Equity BCDC" as "M-Pesa" | "Orange Money" | "Airtel Money" | "Rawbank" | "Equity BCDC",
    accountDetails: "00018-9923812-71",
    presenceCount: 8
  });
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);

  const CNETP_ROLES = [
    { id: "ADMIN", name: "Administrateur technique", desc: "Supervision complète du système CNETP", badgeColor: "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20" },
    { id: "RAP_CTM", name: "Rapporteur CTM (ONIC)", desc: "Gestion des émargements, scrutins & PV", badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20" },
    { id: "SEC_PERM", name: "Secrétaire Permanent (SG)", desc: "Envoi convocations, registre administratif", badgeColor: "bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20" },
    { id: "PRES_CTM", name: "Président du CTM", desc: "Arbitrage & validations scientifiques", badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20" },
    { id: "GEST_COMP", name: "Gestionnaire Comptable (FONER)", desc: "Budget structures & jetons experts", badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/20 hover:bg-purple-500/20" },
    { id: "COORD_CTC", name: "Coordonnateur CTC", desc: "Circuit fermé, rapports & pilotage", badgeColor: "bg-pink-500/10 text-pink-400 border-pink-500/20 hover:bg-pink-500/20" },
    { id: "LEGISTE", name: "Expert Légiste (CTC)", desc: "Toilettage légistique, conformité juridique", badgeColor: "bg-teal-500/10 text-teal-400 border-teal-500/20 hover:bg-teal-500/20" },
    { id: "MEMBRE_P", name: "Membre Permanent (Expert)", desc: "Dépôt d'observations WG & vote de normes", badgeColor: "bg-slate-500/10 text-slate-300 border-slate-550/10 hover:bg-slate-500/20" }
  ];

  const currentRoleObj = CNETP_ROLES.find(r => r.id === userRole) || CNETP_ROLES[0];

  // Core Data State
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [activeCollaborator, setActiveCollaborator] = useState<Collaborator | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);

  // History Filter State
  const [selectedHistoryAuthorEmail, setSelectedHistoryAuthorEmail] = useState<string | null>(null);

  // Experts & Working Groups States for co-gouvernance tab
  const [workingGroups, setWorkingGroups] = useState([
    { id: "wg-8.1", code: "WG 8.1", title: "Matériaux de Construction Locaux (CTM 8)", tag: "Actif" },
    { id: "wg-8.2", code: "WG 8.2", title: "Métrologie & Protocoles d'Essais (CTM 8)", tag: "Évaluation" },
    { id: "wg-8.3", code: "WG 8.3", title: "Procédures de Certification (CTM 8)", tag: "Exigences" },
    { id: "wg-1.1", code: "WG 1.1", title: "Sols & Géo-mécanique (CTM 1)", tag: "Session libre" },
    { id: "wg-1.2", code: "WG 1.2", title: "Stabilité & Érosions (CTM 1)", tag: "Rédaction" },
    { id: "wg-2.3", code: "WG 2.3", title: "Calcul Structural / Eurocodes (CTM 2)", tag: "Votant" },
    { id: "wg-5.1", code: "WG 5.1", title: "Ingénierie Routière (CTM 5)", tag: "Stable" },
    { id: "wg-6.2", code: "WG 6.2", title: "Adduction Urbaine & Matériaux (CTM 6)", tag: "Rédaction" }
  ]);

  const [experts, setExperts] = useState<any[]>([
    {
      id: "exp-1",
      name: "Prof. Masamba Édouard",
      email: "edmasamba100@gmail.com",
      phone: "+243 812 345 678",
      province: "Kinshasa",
      structure: "Université de Kinshasa (UNIKIN)",
      ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
      wg: "WG 8.1 : Matériaux de Construction Locaux",
      role: "Président scientifique",
      isApproved: true
    },
    {
      id: "exp-2",
      name: "Ir. Chantal Mwamba",
      email: "chantal.mwamba@cnetp.cd",
      phone: "+243 898 765 432",
      province: "Haut-Katanga",
      structure: "Office des Voiries et Drainage (OVD)",
      ctm: "CTM 5 – Infrastructures de Transport Linéaire et Maritimes",
      wg: "WG 5.1 : Ingénierie Routière",
      role: "Secrétaire",
      isApproved: true
    },
    {
      id: "exp-3",
      name: "Arch. Sylvain Lukusa",
      email: "sylvain.l@workspace.org",
      phone: "+243 821 112 233",
      province: "Lualaba",
      structure: "Ordre National des Architectes (ONA)",
      ctm: "CTM 3 – Bâtiment, Urbanisme et Transition Numérique",
      wg: "WG 3.2 : BIM & Numérisation (ISO 19650)",
      role: "Rapporteur",
      isApproved: true
    },
    {
      id: "exp-4",
      name: "Ir. Godefroid Munongo",
      email: "g.munongo@sogert.cd",
      phone: "+243 854 998 811",
      province: "Nord-Kivu",
      structure: "Office des Routes (OR)",
      ctm: "CTM 1 – Géotechnique et Risques Naturels",
      wg: "WG 1.2 : Sols Tropicaux & Ferrallitiques",
      role: "Membre",
      isApproved: true
    }
  ]);

  const [selectedWorkingGroupId, setSelectedWorkingGroupId] = useState<string>("wg-8.1");
  const [selectedExpertId, setSelectedExpertId] = useState<string>("exp-1");
  const [expertSelectionType, setExpertSelectionType] = useState<"wg" | "expert">("expert");

  // Chat contacts mapped dynamically from collaborators and experts lists
  const chatContacts = useMemo<ChatContact[]>(() => {
    const list: ChatContact[] = [];
    
    // Add collaborators (excluding myself)
    collaborators.forEach(col => {
      if (col.email !== testProfile.email) {
        list.push({
          id: col.id,
          name: col.name,
          email: col.email,
          role: col.role,
          avatarColor: col.avatarColor,
          isOnline: col.isActive,
          structure: "Secrétariat Technique CNETP"
        });
      }
    });

    // Add experts (excluding myself)
    experts.forEach(exp => {
      if (exp.email !== testProfile.email && !list.some(l => l.email === exp.email)) {
        list.push({
          id: exp.id,
          name: exp.name,
          email: exp.email,
          role: exp.role,
          avatarColor: exp.id === "exp-2" ? "#ec4899" : exp.id === "exp-3" ? "#14b8a6" : "#eab308",
          isOnline: exp.isApproved !== false,
          structure: exp.structure,
          province: exp.province
        });
      }
    });

    return list;
  }, [collaborators, experts, testProfile]);

  // Messages log
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem("cnetp_secure_messages");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        // Fallback
      }
    }
    return [
      {
        id: "seed-1",
        senderId: "col-2",
        senderName: "Marie Laurent",
        receiverId: "me",
        text: "Bonjour Édouard, j'ai relu le dernier brouillon de la clause 4.1 de l'ISO 9001. Penses-tu que les notes de bas de page soient bien conformes pour le CTM 8 ?",
        timestamp: "10:24"
      },
      {
        id: "seed-2",
        senderId: "me",
        senderName: "Prof. Masamba Édouard",
        receiverId: "col-2",
        text: "Bonjour Marie, oui je les ai révisées pour être adaptées aux réalités RDC d'après l'analyse du Conseil.",
        timestamp: "10:28"
      },
      {
        id: "seed-3",
        senderId: "col-2",
        senderName: "Marie Laurent",
        receiverId: "me",
        text: "Parfait, je vais préparer le PV pour le Rapporteur du CTM.",
        timestamp: "10:30"
      },
      {
        id: "seed-4",
        senderId: "exp-2",
        senderName: "Ir. Chantal Mwamba",
        receiverId: "me",
        text: "Prof. Masamba, nous devons fixer la date de la prochaine réunion pour l'approbation du livrable technique sur le drainage routier.",
        timestamp: "Hier, 16:15"
      },
      {
        id: "seed-5",
        senderId: "exp-4",
        senderName: "Ir. Godefroid Munongo",
        receiverId: "me",
        text: "Des retours concernant le CBR de portance pour les sols tropicaux ? Nous aimerions clore le WG 1.2 cette semaine.",
        timestamp: "Lundi, 14:02"
      }
    ];
  });

  // Save changes to localStorage
  useEffect(() => {
    localStorage.setItem("cnetp_secure_messages", JSON.stringify(messages));
  }, [messages]);

  const [activeChatId, setActiveChatId] = useState<string>("col-2");
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);

  // Open Chat thread helper
  const openChatWith = (userId: string) => {
    setActiveChatId(userId);
    setIsChatOpen(true);
    const targetContact = chatContacts.find(c => c.id === userId);
    showToast(`Discussion cryptée ouverte avec ${targetContact?.name || "l'expert"} !`, "success");
  };

  // Clause and general text sharing helper
  const handleShareClause = (recipientId: string, clauseCode: string, excerpt: string) => {
    const timeStr = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    const shareMsg: ChatMessage = {
      id: `share-${Date.now()}`,
      senderId: "me",
      senderName: testProfile.name,
      receiverId: recipientId,
      text: `📢 J'ai partagé cette clause pour examen :\n\n"${excerpt}"`,
      timestamp: timeStr,
      isClauseShare: true,
      clauseCode,
      clauseExcerpt: excerpt
    };

    setMessages(prev => [...prev, shareMsg]);
    setActiveChatId(recipientId);
    setIsChatOpen(true);

    // Simulated reply trigger
    const matchedContact = chatContacts.find(c => c.id === recipientId);
    setTimeout(() => {
      const replyTime = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
      let responseText = `Merci pour le partage de la clause ${clauseCode}. Je l'ai de suite bien reçue.`;

      if (recipientId === "exp-2") {
        responseText = `Merci Édouard d'avoir partagé cet extrait de ${clauseCode}. À l'Office des Voiries et Drainage (OVD), nous veillons à ce que ce niveau d'exigence technique corresponde bien aux contraintes de drainage au Katanga.`;
      } else if (recipientId === "exp-3") {
        responseText = `Bonjour Prof. Masamba. J'ai examiné ce passage de ${clauseCode}. C'est très structurant réglementairement. Je valide pour le prochain rapport d'avancement de l'ONA !`;
      } else if (recipientId === "exp-4") {
        responseText = `Excellent choix de clause ! Pour ${clauseCode}, l'Office des Routes (OR) confirme que cette formulation s'accorde bien avec les portances réglementaires de nos sols tropicaux en RDC.`;
      } else if (recipientId === "col-2") {
        responseText = `Bien reçu, Édouard. Je rajoute cet extrait de ${clauseCode} en pièce jointe au registre légistique du CTM pour que l'auditeur puisse statuer ce soir.`;
      }

      const replyMsg: ChatMessage = {
        id: `reply-${Date.now()}`,
        senderId: recipientId,
        senderName: matchedContact?.name || "Ir. Expert",
        receiverId: "me",
        text: responseText,
        timestamp: replyTime
      };

      setMessages(prev => [...prev, replyMsg]);
    }, 1800);
  };

  // General text message send handler
  const handleSendMessage = (receiverId: string, text: string) => {
    const timeStr = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      senderId: "me",
      senderName: testProfile.name,
      receiverId,
      text,
      timestamp: timeStr
    };

    setMessages(prev => [...prev, userMsg]);

    // Fast simulation check: if sent to a simulated expert, let them reply after 1.5 seconds!
    const recipient = chatContacts.find(c => c.id === receiverId);
    if (recipient) {
      setTimeout(() => {
        const replyTime = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
        let responseText = "Bien reçu ! Votre message est très pertinent de la part de l'équipe technique.";

        if (receiverId === "col-2") {
          responseText = "Merci Édouard ! Je transmets les notes de bas de page révisées d'urgence.";
        } else if (receiverId === "exp-2") {
          responseText = "D'accord, je prépare le dossier de drainage et je vous reviens dès que possible.";
        } else if (receiverId === "exp-4") {
          responseText = "Compris, je vais relancer l'ingénieur de l'Office des Routes pour obtenir validation de la note géotechnique.";
        } else if (receiverId === "col-3") {
          responseText = "Message bien reçu sur mon canal chiffré. Je serai présent pour l'audition de conformité.";
        } else {
          responseText = `Parfait Édouard. Discutons-en au secrétariat permanent du CTM.`;
        }

        const replyMsg = {
          id: `chat-${Date.now()}-reply`,
          senderId: receiverId,
          senderName: recipient.name,
          receiverId: "me",
          text: responseText,
          timestamp: replyTime
        };
        setMessages(prev => [...prev, replyMsg]);
      }, 1500);
    }
  };

  // Loading & Action feedback states
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  // Auto Dismiss Toasts helper
  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  // Initial Seed Fetch
  useEffect(() => {
    async function initWorkspace() {
      try {
        // Fetch documents
        const docsRes = await fetch("/api/documents");
        const docsData = await docsRes.json();
        setDocuments(docsData);
        if (docsData.length > 0) {
          setSelectedDocId(docsData[0].id);
        }

        // Fetch collaborators list
        const colsRes = await fetch("/api/collaborators");
        const colsData = await colsRes.json();
        setCollaborators(colsData);
        // Default to first active collaborator
        const firstActive = colsData.find((c: Collaborator) => c.isActive) || colsData[0];
        setActiveCollaborator(firstActive);
      } catch (err) {
        console.error("Error initializing workspace:", err);
        showToast("Erreur lors de l'accès au serveur d'édition", "error");
      } finally {
        setIsLoading(false);
      }
    }
    initWorkspace();
  }, []);

  // Fetch Versions history whenever document selection shifts
  useEffect(() => {
    if (!selectedDocId) return;

    async function fetchDocVersions() {
      try {
        const res = await fetch(`/api/documents/${selectedDocId}/versions`);
        if (res.ok) {
          const vData = await res.json();
          setVersions(vData);
        }
      } catch (err) {
        console.error("Error fetching versions:", err);
        showToast("Impossible de synchroniser l'historique", "error");
      }
    }
    fetchDocVersions();
  }, [selectedDocId]);

  const handleUpdateDocument = (updatedDoc: Document) => {
    setDocuments((prev) => prev.map((d) => d.id === updatedDoc.id ? updatedDoc : d));
  };

  // Current selected document reference
  const activeDocument = documents.find((doc) => doc.id === selectedDocId) || null;

  // Save/Create a new version action handler
  const handleSaveVersion = async (content: string, comment: string) => {
    if (!selectedDocId || !activeCollaborator) return;
    setIsSaving(true);

    try {
      const res = await fetch(`/api/documents/${selectedDocId}/versions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content,
          author: activeCollaborator.name,
          email: activeCollaborator.email,
          comment,
        }),
      });

      if (!res.ok) {
        throw new Error("Erreur de sauvegarde de l'article");
      }

      const data = await res.json();
      
      // Update local documents list with new state
      setDocuments((prevDocs) =>
        prevDocs.map((doc) => (doc.id === selectedDocId ? data.document : doc))
      );

      // Refresh version timeline immediately
      const vRes = await fetch(`/api/documents/${selectedDocId}/versions`);
      const vData = await vRes.json();
      setVersions(vData);

      showToast(`Version v${data.version.versionNumber} sauvegardée avec succès !`);
    } catch (err: any) {
      showToast(err.message || "Échec de sauvegarde", "error");
    } finally {
      setIsSaving(false);
    }
  };

  // Rollback to previous version action handler
  const handleRollbackVersion = async (versionNumber: number) => {
    if (!selectedDocId || !activeCollaborator) return;
    
    const confirmAction = window.confirm(
      `Êtes-vous sûr de vouloir restaurer la version v${versionNumber} ? Les modifications ultérieures seront préservées sous forme d'un nouveau commit et rien ne sera perdu.`
    );
    if (!confirmAction) return;

    setIsRollingBack(true);
    try {
      const res = await fetch(`/api/documents/${selectedDocId}/rollback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          targetVersionNumber: versionNumber,
          author: activeCollaborator.name,
          email: activeCollaborator.email,
        }),
      });

      if (!res.ok) {
        const errObj = await res.json();
        throw new Error(errObj.error || "Échec de la restauration");
      }

      const data = await res.json();

      // Update local state and logs
      setDocuments((prevDocs) =>
        prevDocs.map((doc) => (doc.id === selectedDocId ? data.document : doc))
      );

      // Refresh timeline with rollback commit
      const vRes = await fetch(`/api/documents/${selectedDocId}/versions`);
      const vData = await vRes.json();
      setVersions(vData);

      showToast(`Version v${versionNumber} restaurée avec succès par ${activeCollaborator.name} !`);
      
      // Automatically redirect to the workspace editor to let users view and work on restored content
      setActiveTab("editor");
    } catch (err: any) {
      showToast(err.message || "Erreur de rollback", "error");
    } finally {
      setIsRollingBack(false);
    }
  };

  // Collaborator action handler (Initiates direct secure debate chat)
  const handleSelectCollaborator = (col: Collaborator) => {
    if (col.email !== testProfile.email) {
      openChatWith(col.id);
    } else {
      showToast(`Vous êtes connecté en tant que ${col?.name || "expert"} (${col?.role || "expert"})`, "success");
    }
  };

  const handleSaveProfile = (updatedProfile: any) => {
    setTestProfile(updatedProfile);
    setUserRole(updatedProfile.roleId);
    setIsProfileModalOpen(false);
    showToast(`Profil appliqué : ${updatedProfile.name} (${updatedProfile.roleId})`, "success");
  };

  // Initial spinner handler
  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#020204] flex flex-col items-center justify-center gap-4">
        <Loader className="h-9 w-9 text-emerald-500 animate-spin" />
        <p className="text-sm font-semibold text-slate-400 tracking-wide">Initialisation de l'espace collaboratif...</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-[#020204] font-sans text-slate-300">
      
      {/* Dynamic Toast feedback panel */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4.5 py-3.5 rounded-xl shadow-xl border animate-slideIn bg-[#020204]/90 backdrop-blur-md border-white/10">
          {toast.type === "success" && (
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]" />
          )}
          {toast.type === "error" && (
            <AlertTriangle className="h-5 w-5 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.3)]" />
          )}
          {toast.type === "info" && (
            <RefreshCw className="h-5 w-5 text-indigo-400 animate-spin" />
          )}
          <span className="text-xs font-semibold text-slate-200">{toast.message}</span>
        </div>
      )}

      {/* LEFT SIDEBAR: Doc List & Active Presence */}
      <Sidebar
        activeTab={activeTab}
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={(id) => {
          setSelectedDocId(id);
          setSelectedHistoryAuthorEmail(null); // Reset filter when selecting another document
        }}
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
        testProfile={testProfile}
      />

      {/* RIGHT SIDEBAR CONTENT: Editor/History & Nav buttons */}
      <main className="flex-1 flex flex-col h-full min-w-0 bg-[#06060c]/20 relative">
        <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-emerald-500/5 to-transparent pointer-events-none"></div>

        {/* Navigation control bar featuring Core Editor, Experts, Votes, Finances, and Public Library */}
        <nav className="h-14 border-b border-white/10 px-6 flex items-center justify-between shrink-0 bg-black/40 backdrop-blur-md z-10 overflow-x-auto whitespace-nowrap scrollbar-none">
          <div className="flex items-center gap-1 flex-row flex-nowrap shrink-0">
            <button
              id="nav-tab-editor"
              onClick={() => setActiveTab("editor")}
              className={`h-14 px-3 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-1.5 border-b-2 shrink-0 ${
                activeTab === "editor"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <FileText className="h-4 w-4" />
              Éditeur de Normes
            </button>

            <button
              id="nav-tab-history"
              onClick={() => setActiveTab("history")}
              className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                activeTab === "history"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <History className="h-4 w-4" />
              Historique (v{versions.length})
            </button>

            <button
              id="nav-tab-experts"
              onClick={() => setActiveTab("experts")}
              className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                activeTab === "experts"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Users className="h-4 w-4" />
              Experts & Groupes
            </button>

            <button
              id="nav-tab-meetings"
              onClick={() => setActiveTab("meetings")}
              className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                activeTab === "meetings"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Vote className="h-4 w-4" />
              Réunions & Votes
            </button>

            <button
              id="nav-tab-financial"
              onClick={() => setActiveTab("financial")}
              className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                activeTab === "financial"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Landmark className="h-4 w-4" />
              Cotisations & Indemnités
            </button>

            <button
              id="nav-tab-validation"
              onClick={() => setActiveTab("validation")}
              className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                activeTab === "validation"
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Award className="h-4 w-4" />
              Bibliothèque Publique
            </button>

            <button
              onClick={() => navigate("/public-norms")}
              className="h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 border-transparent text-slate-400 hover:text-white hover:bg-white/5 shrink-0 cursor-pointer"
            >
              <BookOpen className="h-4 w-4 text-teal-400 animate-pulse" />
              🌐 Portail Public (Visiteur)
            </button>
            
            {['LEGISTE', 'COORD_CTC', 'ADMIN'].includes(userRole) && (
              <button
                id="nav-tab-legistique"
                onClick={() => setActiveTab("legistique")}
                className={`h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 shrink-0 ${
                  activeTab === "legistique"
                    ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 shadow-[0_4px_15px_rgba(16,185,129,0.1)]"
                    : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <BookOpen className="h-4 w-4" />
                Bureau Légistique
              </button>
            )}
          </div>

          {/* Simulation Role & Profile Switcher Button */}
          <div className="shrink-0 flex items-center pr-3">
            <button
              id="role-switcher-btn"
              onClick={() => setIsProfileModalOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/15 text-emerald-400 hover:text-emerald-300 font-bold text-xs shadow-[0_0_15px_rgba(16,185,129,0.06)] cursor-pointer focus:outline-hidden transition-all duration-200"
              title="Modifier mon profil d'expert et choisir un rôle de test"
            >
              <Users className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span className="text-slate-300 leading-none">Modifier profil de test (</span>
              <span className="text-white hover:text-emerald-300 font-extrabold max-w-[140px] truncate">
                {testProfile.name}
              </span>
              <span className="text-slate-300 leading-none">) :</span>
              <span className="text-[10px] font-mono tracking-wide px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase leading-none">
                {currentRoleObj.name}
              </span>
            </button>
          </div>
        </nav>

        {/* Selected Area viewport */}
        <div className="flex-1 min-h-0 flex flex-col z-10">
          {activeTab === "experts" ? (
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
              testProfile={testProfile}
            />
          ) : activeTab === "meetings" ? (
            <MeetingsVotesModule
              experts={experts}
              workingGroups={workingGroups}
              userRole={userRole}
              simulatedProfile={testProfile}
            />
          ) : activeTab === "financial" ? (
            <FinancialModule
              userRole={userRole}
              experts={experts}
              simulatedProfile={testProfile}
            />
          ) : activeTab === "validation" ? (
            <ValidationPublicModule />
          ) : activeTab === "legistique" ? (
            <LegistiqueModule userRole={userRole} />
          ) : activeDocument && activeCollaborator ? (
            activeTab === "editor" ? (
              <EditorArea
                document={activeDocument}
                activeCollaborator={activeCollaborator}
                onSave={handleSaveVersion}
                onCancel={() => {
                  // Simply refresh state
                  setDocuments([...documents]);
                  showToast("L'édition en cours a été réinitialisée.", "info");
                }}
                isSaving={isSaving}
                onUpdateDocument={handleUpdateDocument}
                chatContacts={chatContacts}
                onShareClause={handleShareClause}
              />
            ) : (
              <HistoryArea
                document={activeDocument}
                versions={versions}
                onRollback={handleRollbackVersion}
                isRollingBack={isRollingBack}
                activeCollaborator={activeCollaborator}
                selectedHistoryAuthorEmail={selectedHistoryAuthorEmail}
                onClearHistoryAuthorFilter={() => setSelectedHistoryAuthorEmail(null)}
              />
            )
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500 text-sm">
              <HelpCircle className="h-10 w-10 text-slate-600 animate-pulse mb-2" />
              <p>Sélectionnez un document réglementaire dans le menu latéral pour débuter la rédaction.</p>
            </div>
          )}
        </div>
      </main>

      {/* Secured Messenger Widget */}
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

      {/* Embedded Profile Editor popup panel */}
      <ProfileSimulationModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        profile={testProfile}
        onSave={handleSaveProfile}
      />
    </div>
  );
}
