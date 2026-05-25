import React, { useState, useMemo } from "react";
import { 
  Vote, 
  FileSpreadsheet, 
  Calendar, 
  CheckSquare, 
  Sparkles, 
  UserCheck, 
  Percent, 
  FileText, 
  ChevronRight, 
  Check, 
  AlertCircle,
  Video,
  Share2,
  Copy,
  Users,
  Eye,
  Lock,
  Download,
  ShieldCheck,
  Plus,
  ArrowRight,
  TrendingUp,
  Clock,
  Info
} from "lucide-react";
import { Collaborator } from "../types";

// Dynamic types
interface Meeting {
  id: string;
  title: string;
  type: "WG" | "CTM" | "Comité de Pilotage" | "Assemblée plénière";
  date: string;
  time: string;
  quorumRequiredText: string;
  quorumPercentage: number;
  lawSubject: string;
  description: string;
  status: "Ébauche" | "En cours" | "Terminé";
  pvGenerated: boolean;
  meetActive: boolean;
  meetUrl: string;
  voteMode: "Synchronisé" | "Asynchrone";
  // Track attendance by expert ID
  attendance: Record<string, boolean>;
  // Track votes by expert ID ("pour" | "contre" | "abstention" | undefined)
  expertVotes: Record<string, "pour" | "contre" | "abstention">;
  observations: string;
}

interface MeetingsVotesModuleProps {
  experts?: any[];
  workingGroups?: any[];
  userRole?: string;
  simulatedProfile?: any;
  isDarkMode?: boolean;
}

export default function MeetingsVotesModule({
  experts = [],
  workingGroups = [],
  userRole = "ADMIN",
  simulatedProfile = null,
  isDarkMode = true
}: MeetingsVotesModuleProps) {
  // Let's establish robust default experts if empty or undefined for maximum offline experience
  const fallbackExperts = [
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
      isPermanent: true,
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
      role: "Secrétaire du CTM",
      isPermanent: true,
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
      isPermanent: true,
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
      isPermanent: true,
      isApproved: true
    },
    {
      id: "exp-5",
      name: "Ir. Blaise Nkansu",
      email: "nkansu.blaise@gmail.com",
      phone: "+243 812 990 011",
      province: "Kongo-Central",
      structure: "Bureau de Contrôle Technique (BCT)",
      ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
      wg: "WG 8.1 : Matériaux de Construction Locaux",
      role: "Observateur Représentant",
      isPermanent: false,
      isApproved: true
    },
    {
       id: "exp-6",
       name: "Ir. Albertine Mpaka",
       email: "albertine.mpaka@itp.gouv.cd",
       phone: "+243 890 223 344",
       province: "Kinshasa",
       structure: "Ministère des ITP RDC - Secrétariat Général",
       ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
       wg: "WG 8.1 : Matériaux de Construction Locaux",
       role: "Membre Permanent",
       isPermanent: true,
       isApproved: true
    }
  ];

  // Merge the passed experts or use fallback, ensuring they have an `isPermanent` property
  const allExperts = useMemo(() => {
    let list = experts.length > 0 ? [...experts] : [...fallbackExperts];
    
    // Inject or update simulated profile expert at the top
    if (simulatedProfile) {
      const existsIdx = list.findIndex(e => e.id === "sim-user" || e.email === simulatedProfile.email);
      const simulatedExpert = {
        id: "sim-user",
        name: simulatedProfile.name,
        email: simulatedProfile.email,
        phone: "+243 811 000 111",
        province: "Kinshasa",
        structure: simulatedProfile.structure,
        ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
        wg: "WG 8.1 : Matériaux de Construction Locaux",
        role: userRole === "ADMIN" ? "Administrateur technique" : 
              userRole === "RAP_CTM" ? "Rapporteur CTM" :
              userRole === "SEC_PERM" ? "Secrétaire Permanent" :
              userRole === "PRES_CTM" ? "Président du CTM" :
              userRole === "GEST_COMP" ? "Comptable Principal" :
              userRole === "COORD_CTC" ? "Coordonnateur CTC" : "Membre Permanent (Expert)",
        isPermanent: userRole !== "GEST_COMP" && userRole !== "COORD_CTC" && userRole !== "ADMIN",
        isApproved: true
      };
      
      if (existsIdx >= 0) {
        list[existsIdx] = simulatedExpert;
      } else {
        list.unshift(simulatedExpert);
      }
    }

    return list.map(e => ({
      ...e,
      // If not defined, mark as permanent unless they possess "Observateur" in role or structure
      isPermanent: e.isPermanent !== undefined 
        ? e.isPermanent 
        : !(e.role || "").toLowerCase().includes("observateur")
    }));
  }, [experts, simulatedProfile, userRole]);

  // Dynamic Meetings database
  const [meetings, setMeetings] = useState<Meeting[]>([
    {
      id: "meet-1",
      title: "Session CTM 8 - Homologation d'Argiles Locales RDC",
      type: "CTM",
      date: "2026-05-19",
      time: "10:30",
      quorumRequiredText: "Majorité qualifiée requise (2/3 des Membres P)",
      quorumPercentage: 66.6,
      lawSubject: "Norme BTC40 - Blocs de Terre Comprimée pour murs porteurs",
      description: "Validation de la norme technique sur la consolidation des mortiers d'argile à base de chaux locale et d'additifs pouzzolanes.",
      status: "Terminé",
      pvGenerated: true,
      meetActive: true,
      meetUrl: "https://meet.google.com/xyz-bcte-arg",
      voteMode: "Synchronisé",
      attendance: {
        "exp-1": true,
        "exp-2": true,
        "exp-3": true,
        "exp-4": true,
        "exp-5": true,
        "exp-6": true
      },
      expertVotes: {
        "exp-1": "pour",
        "exp-2": "pour",
        "exp-3": "pour",
        "exp-4": "contre",
        "exp-6": "pour"
      },
      observations: "Le consensus scientifique a été obtenu vigoureusement après amendement de l'article 4.3 concernant le coefficient d'absorption d'eau."
    },
    {
      id: "meet-2",
      title: "Commission d'Étude Plénière - Ligne Directrice ITP",
      type: "Assemblée plénière",
      date: "2026-05-24",
      time: "14:00",
      quorumRequiredText: "Consensus souverain renforcé (75% minimum)",
      quorumPercentage: 75.0,
      lawSubject: "Directives Générales pour Dimensionnement des Routes en RDC",
      description: "Adoption finale de la réglementation nationale de calcul d'épaisseur sous climat équatorial humide de la CEEAC.",
      status: "En cours",
      pvGenerated: false,
      meetActive: true,
      meetUrl: "https://meet.google.com/pqr-itpr-rtes",
      voteMode: "Asynchrone",
      attendance: {
        "exp-1": true,
        "exp-2": true,
        "exp-3": false,
        "exp-4": true,
        "exp-5": true,
        "exp-6": true
      },
      expertVotes: {
        "exp-1": "pour",
        "exp-2": "pour",
        "exp-4": "abstention"
      },
      observations: "Session ouverte en visioconférence pour amendement général par les experts des provinces."
    },
    {
      id: "meet-3",
      title: "Groupe de Travail 1.1 - Sols & Géo-mécanique",
      type: "WG",
      date: "2026-05-29",
      time: "09:00",
      quorumRequiredText: "Simple majorité des présents requis (50%)",
      quorumPercentage: 50.0,
      lawSubject: "Classification géotechnique des sols latéritiques",
      description: "Travail technique préliminaire et établissement des bornes Proctor modifiées pour chantiers civils.",
      status: "Ébauche",
      pvGenerated: false,
      meetActive: false,
      meetUrl: "https://meet.google.com/abc-wg11-sol",
      voteMode: "Asynchrone",
      attendance: {},
      expertVotes: {},
      observations: ""
    }
  ]);

  const [activeMeetingId, setActiveMeetingId] = useState<string>("meet-2");
  
  // Dashboard Sub-tabs
  const [activeSubTab, setActiveSubTab] = useState<"meet" | "attendance" | "vote" | "pv">("meet");

  // Local notification feedbacks
  const [notification, setNotification] = useState<{ message: string; type: "success" | "info" } | null>(null);
  const triggerNotification = (message: string, type: "success" | "info" = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Copy Google Meet link with user feedback
  const [copiedMeetId, setCopiedMeetId] = useState<string | null>(null);
  const handleCopyMeetUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedMeetId(url);
    triggerNotification("Lien Google Meet copié dans le presse-papier !", "success");
    setTimeout(() => setCopiedMeetId(null), 2500);
  };

  // Simulate sending invitations over emails / notifications
  const handleInviteExperts = (meeting: Meeting) => {
    const participantCount = allExperts.filter(e => e.isPermanent).length;
    triggerNotification(
      `Invitation transmise aux ${participantCount} experts permanents et partenaires via courriers sécurisés CNETP !`,
      "info"
    );
  };

  // Form states for creating a new meeting
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState<"WG" | "CTM" | "Comité de Pilotage" | "Assemblée plénière">("WG");
  const [newLaw, setNewLaw] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newTime, setNewTime] = useState("10:00");
  const [newDate, setNewDate] = useState("");
  const [activateMeetImmediately, setActivateMeetImmediately] = useState(true);

  // Computed fields for active meeting
  const activeMeetingIndex = meetings.findIndex(m => m.id === activeMeetingId);
  const activeMeeting = meetings[activeMeetingIndex] || meetings[0];

  // Handling submission of a new official meeting
  const handleCreateMeetingSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newLaw.trim()) return;

    let quorumText = "Simple majorité requise (50%)";
    let quorumPct = 50.0;
    if (newType === "CTM") {
      quorumText = "Majorité qualifiée requise des 20 membres permanents (2/3 favorable)";
      quorumPct = 66.6;
    } else if (newType === "Comité de Pilotage") {
      quorumText = "Majorité qualifiée consultative (2/3)";
      quorumPct = 66.6;
    } else if (newType === "Assemblée plénière") {
      quorumText = "Adoption par Consensus des 200 experts (0 opposition)";
      quorumPct = 100.0;
    }

    const randomHash = Math.random().toString(36).substring(2, 5) + "-" + Math.random().toString(36).substring(2, 6) + "-" + Math.random().toString(36).substring(2, 5);
    const generateMeetUrl = `https://meet.google.com/${randomHash}`;

    // Auto mark all fallback experts as present for instant usability
    const initialAttendance: Record<string, boolean> = {};
    allExperts.forEach(exp => {
      initialAttendance[exp.id] = true; // markers default to true
    });

    const added: Meeting = {
      id: `meet-${Date.now()}`,
      title: newTitle,
      type: newType,
      date: newDate || new Date().toISOString().split("T")[0],
      time: newTime || "10:00",
      quorumRequiredText: quorumText,
      quorumPercentage: quorumPct,
      lawSubject: newLaw,
      description: newDescription || "Discussion législative autour de la codification nationale.",
      status: "En cours",
      pvGenerated: false,
      meetActive: activateMeetImmediately,
      meetUrl: generateMeetUrl,
      voteMode: "Synchronisé",
      attendance: initialAttendance,
      expertVotes: {},
      observations: ""
    };

    setMeetings([...meetings, added]);
    setActiveMeetingId(added.id);
    setActiveSubTab("meet"); // instantly switch to meet configuration review

    // Reset controls
    setNewTitle("");
    setNewLaw("");
    setNewDescription("");
    triggerNotification(`La session nationale "${added.title}" a été initialisée !`, "success");
  };

  // Toggle expert presence on feuille d'émargement
  const toggleAttendance = (expertId: string) => {
    if (userRole !== "ADMIN" && userRole !== "RAP_CTM" && userRole !== "SEC_PERM") {
      triggerNotification("Habilitation insuffisante : Seul le Rapporteur CTM (ONIC) ou le Secrétariat Permanent est en droit de modifier l'émargement.", "info");
      return;
    }
    if (activeMeeting.status === "Terminé") {
      triggerNotification("Impossible de modifier les présences d'une réunion archivée.", "info");
      return;
    }

    setMeetings(prev => prev.map(m => {
      if (m.id === activeMeetingId) {
        const nextAttendance = { ...m.attendance };
        nextAttendance[expertId] = !nextAttendance[expertId];
        
        // If they became absent, remove their vote too as they can't vote offline
        const nextVotes = { ...m.expertVotes };
        if (!nextAttendance[expertId]) {
          delete nextVotes[expertId];
        }

        return {
          ...m,
          attendance: nextAttendance,
          expertVotes: nextVotes
        };
      }
      return m;
    }));
  };

  // Cast electronic vote for a specific expert
  const handleCastExpertVote = (expertId: string, choice: "pour" | "contre" | "abstention" | "non-voté") => {
    if (activeMeeting.status === "Terminé") {
      triggerNotification("Cette session de vote est close et scellée.", "info");
      return;
    }

    // Verify presence first
    if (!activeMeeting.attendance[expertId]) {
      triggerNotification("Cet expert doit être marqué 'Présent' au Quorum pour pouvoir voter.", "info");
      return;
    }

    // Verify they are a permanent member (Membres P) with voting rights
    const exp = allExperts.find(e => e.id === expertId);
    if (exp && !exp.isPermanent) {
      triggerNotification("Rôle Observateur (Membre O) : Droit de vote indisponible selon l'Article 7.", "info");
      return;
    }

    setMeetings(prev => prev.map(m => {
      if (m.id === activeMeetingId) {
        const nextVotes = { ...m.expertVotes };
        if (choice === "non-voté") {
          delete nextVotes[expertId];
        } else {
          nextVotes[expertId] = choice;
        }

        return {
          ...m,
          expertVotes: nextVotes,
          status: "En cours" // Dynamically stay in-progress
        };
      }
      return m;
    }));
  };

  // End meeting, lock votes, and approve PV
  const handleCloseScrutinAndGeneratePv = () => {
    if (userRole !== "ADMIN" && userRole !== "RAP_CTM") {
      triggerNotification("Habilitation insuffisante : Seul le Rapporteur CTM (ONIC) est en droit de clore le scrutin et certifier le procès-verbal.", "info");
      return;
    }
    if (activeMeeting.status === "Terminé") return;

    setMeetings(prev => prev.map(m => {
      if (m.id === activeMeetingId) {
        return {
          ...m,
          status: "Terminé",
          pvGenerated: true,
          observations: m.observations || "Les débats clos ont permis l'homologation selon le circuit réglementaire fermé du CNETP."
        };
      }
      return m;
    }));
    setActiveSubTab("pv"); // directly jump to PV overview
    triggerNotification("Le scrutin est clos souverainement et le PV officiel a été généré !", "success");
  };

  // Quorum Calculations
  const quorumStats = useMemo(() => {
    // Permanent members list
    const permanentMembers = allExperts.filter(e => e.isPermanent);
    const totalPCount = permanentMembers.length;
    
    // Present permanent members count
    let presentPCount = 0;
    permanentMembers.forEach(m => {
      if (activeMeeting.attendance[m.id]) {
        presentPCount++;
      }
    });

    const activePresencePercentage = totalPCount > 0 ? (presentPCount / totalPCount) * 100 : 0;
    const isQuorumReached = activePresencePercentage >= activeMeeting.quorumPercentage;

    return {
      totalPCount,
      presentPCount,
      activePresencePercentage: Math.round(activePresencePercentage),
      isQuorumReached
    };
  }, [allExperts, activeMeeting]);

  // Votes Calculations
  const votesStats = useMemo(() => {
    const votingMembers = allExperts.filter(e => e.isPermanent && activeMeeting.attendance[e.id]);
    const totalVotersPossible = votingMembers.length;
    
    let pourCount = 0;
    let contreCount = 0;
    let abstentionCount = 0;

    votingMembers.forEach(m => {
      const vote = activeMeeting.expertVotes[m.id];
      if (vote === "pour") pourCount++;
      else if (vote === "contre") contreCount++;
      else if (vote === "abstention") abstentionCount++;
    });

    const totalVotesCast = pourCount + contreCount + abstentionCount;
    const pourPct = totalVotesCast > 0 ? Math.round((pourCount / totalVotesCast) * 100) : 0;
    const contrePct = totalVotesCast > 0 ? Math.round((contreCount / totalVotesCast) * 100) : 0;
    const abstentionPct = totalVotesCast > 0 ? Math.round((abstentionCount / totalVotesCast) * 100) : 0;

    // Vote & Approval Logic according to the official Manuel Organisationnel of CNETP:
    // 1. CTM (Vote Sectoriel): Qualified majority of 2/3 (66.6% minimum) of the 20 permanent members
    // 2. Assemblée Plénière (Adoption Souveraine): Absolute Consensus (0 votes 'contre' / opposition allowed)
    // 3. Others: Simple Majority (>= 50.0%)
    let isApproved = false;
    let thresholdRuleText = "Simple majorité (>= 50% favorable)";
    let verdictText = "";

    if (activeMeeting.type === "Assemblée plénière") {
      thresholdRuleText = "Consensus de l'Assemblée Plénière (Aucune opposition / 0 Contre)";
      isApproved = totalVotesCast > 0 && contreCount === 0;
      verdictText = isApproved 
        ? "✓ CONSENSUS REJOINT : AUCUNE OPPOSITION (Adoption Souveraine)" 
        : totalVotesCast === 0 
          ? "Aucun suffrage exprimé"
          : "❌ CONSENSUS NON ATTEINT (Droit de veto exercé / Opposition active)";
    } else if (activeMeeting.type === "CTM") {
      thresholdRuleText = "Majorité qualifiée de la sous-commission CTM (>= 66.6% favorables)";
      const approvalRateVal = totalVotesCast > 0 ? (pourCount / totalVotesCast) * 100 : 0;
      isApproved = approvalRateVal >= 66.6;
      verdictText = isApproved 
        ? "✓ MAJORITÉ QUALIFIÉE DE 2/3 REJOINTE ET VALIDÉE (Vote Sectoriel)" 
        : "⚠️ PROJET REJETÉ : MAJORITÉ QUALIFIÉE D'APPROBATION DE 2/3 NON ATTEINTE";
    } else {
      const approvalRateVal = totalVotesCast > 0 ? (pourCount / totalVotesCast) * 100 : 0;
      isApproved = approvalRateVal >= 50.0;
      verdictText = isApproved 
        ? "✓ PROJET DE NORME SCIENTIFIQUE VALIDÉ À LA MAJORITÉ SIMPLE" 
        : "❌ PROJET REJETÉ (Simple majorité d'approbations de 50% non atteinte)";
    }

    const approvalRate = totalVotesCast > 0 ? (pourCount / totalVotesCast) * 100 : 0;

    return {
      totalVotersPossible,
      totalVotesCast,
      nonVotedCount: totalVotersPossible - totalVotesCast,
      pourCount,
      contreCount,
      abstentionCount,
      pourPct,
      contrePct,
      abstentionPct,
      approvalRate: Math.round(approvalRate),
      isApproved,
      thresholdRuleText,
      verdictText
    };
  }, [allExperts, activeMeeting]);

  const [isPvModalOpen, setIsPvModalOpen] = useState(false);

  const isLightMode = !isDarkMode;

  return (
    <div className={`p-6 space-y-8 overflow-y-auto h-full transition-colors duration-250 ${isLightMode ? "bg-white text-slate-850" : "text-slate-300 bg-[#06060c]"}`}>
      
      {/* Module Banner Header */}
      <div className={`border-b pb-5 ${isLightMode ? "border-slate-250" : "border-white/10"}`}>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Vote className="h-6 w-6 text-blue-500" />
            <h2 className={`text-xl font-extrabold tracking-tight uppercase ${isLightMode ? "text-slate-900" : "text-white"}`}>
              Réunions techniques & Scrutin électronique
            </h2>
          </div>
          <div className={`flex items-center gap-1 border rounded-lg p-1 text-[11px] font-mono ${isLightMode ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-black/40 border-white/10 text-slate-400"}`}>
            <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span>Blockchain Nationale CNETP RDC Actived</span>
          </div>
        </div>
        <p className={`text-xs leading-relaxed mt-2 ${isLightMode ? "text-slate-600 font-medium" : "text-slate-400"}`}>
          Convoquez en direct les Comités Techniques Miroirs (CTM) ou l'Assemblée plénière. Établissez la visioconférence Google Meet intégrée, vérifiez l'atteinte du quorum souverain en République Démocratique du Congo, attribuez les suffrages certifiés des Experts permanents, et validez le Procès-Verbal (PV).
        </p>
      </div>

      {/* Floating Notification Pop-up */}
      {notification && (
        <div className={`fixed bottom-6 right-6 z-50 p-4 rounded-xl border shadow-2xl flex items-center gap-3 animate-slideIn backdrop-blur-md max-w-md ${
          notification.type === "success" 
            ? "bg-blue-500/10 border-blue-500/30 text-blue-400"
            : "bg-blue-500/15 border-blue-500/30 text-blue-300"
        }`}>
          <div className="h-6 w-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
            ✓
          </div>
          <p className="text-xs font-semibold leading-relaxed">{notification.message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* LEFT COLUMN: Create session & active categories list */}
        <div className="space-y-6">
          
          {/* Create meeting form box */}
          <div className={`border rounded-2xl p-5 space-y-4 relative overflow-hidden ${isLightMode ? "bg-slate-50 border-slate-205" : "bg-gradient-to-b from-black/50 to-black/35 border-white/10"}`}>
            {userRole !== "ADMIN" && userRole !== "SEC_PERM" && userRole !== "RAP_CTM" ? (
              <div className={`absolute inset-0 backdrop-blur-xs flex flex-col items-center justify-center p-6 text-center z-25 ${isLightMode ? "bg-slate-100/95" : "bg-[#06060c]/95"}`}>
                <Lock className="h-7 w-7 text-slate-500 mb-2 animate-pulse" />
                <h4 className={`font-bold text-xs uppercase tracking-wider ${isLightMode ? "text-slate-800" : "text-white"}`}>Planification verrouillée</h4>
                <p className={`text-[10px] mt-2 max-w-[220px] leading-relaxed ${isLightMode ? "text-slate-550" : "text-slate-400"}`}>
                  Selon le manuel d'organisation, seul le <strong className="text-blue-500">Secrétaire Permanent (SG-ITP)</strong> ou le <strong className="text-amber-600">Rapporteur</strong> est habilité à initier des convocations officielles.
                </p>
                <div className={`mt-3 text-[8.5px] font-mono px-2 py-0.5 rounded ${isLightMode ? "bg-slate-200 text-slate-600 border border-slate-300" : "bg-white/5 text-slate-500"}`}>
                  RÔLE REQUIS : COMPTABLE / ADMIN / SEC_PERM
                </div>
              </div>
            ) : null}

            <h3 className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${isLightMode ? "text-slate-800" : "text-white"}`}>
              <Calendar className="h-4.5 w-4.5 text-blue-500" />
              Planifier une session de vote
            </h3>
            <form onSubmit={handleCreateMeetingSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className={`block mb-1 font-semibold uppercase tracking-wider text-[9px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>Intitulé officiel :</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder="Ex: Concile CTM 8 - Homologation BTC"
                  className={`w-full p-2.5 rounded-lg border font-semibold focus:outline-hidden ${isLightMode ? "bg-white border-slate-300 text-slate-800 focus:border-blue-500" : "bg-black/60 border-white/10 text-white focus:border-blue-500/50"}`}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`block mb-1 font-semibold uppercase tracking-wider text-[9px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>Organe :</label>
                  <select
                    value={newType}
                    onChange={e => setNewType(e.target.value as any)}
                    className={`w-full p-2.5 rounded-lg border font-semibold focus:outline-hidden ${isLightMode ? "bg-white border-slate-300 text-slate-800" : "bg-black/65 border-white/10 text-slate-300"}`}
                  >
                    <option value="WG">Comité WG (Étude)</option>
                    <option value="CTM">Comité CTM (Décision)</option>
                    <option value="Comité de Pilotage">Pilotage (24 exp)</option>
                    <option value="Assemblée plénière">Plénière (200 exp)</option>
                  </select>
                </div>
                <div>
                  <label className={`block mb-1 font-semibold uppercase tracking-wider text-[9px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>Heure d'ouverture :</label>
                  <input
                    type="time"
                    value={newTime}
                    onChange={e => setNewTime(e.target.value)}
                    className={`w-full p-2 rounded-lg border focus:outline-hidden font-mono ${isLightMode ? "bg-white border-slate-300 text-slate-800" : "bg-black/65 border-white/10 text-slate-300"}`}
                  />
                </div>
              </div>

              <div>
                <label className={`block mb-1 font-semibold uppercase tracking-wider text-[9px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>Document réglementaire concerné :</label>
                <input
                  type="text"
                  required
                  value={newLaw}
                  onChange={e => setNewLaw(e.target.value)}
                  placeholder="Ex: Standard de composition du béton C30"
                  className={`w-full p-2.5 rounded-lg border font-semibold focus:outline-hidden ${isLightMode ? "bg-white border-slate-300 text-slate-800 focus:border-blue-500" : "bg-black/60 border-white/10 text-white focus:border-blue-500/50"}`}
                />
              </div>

              <div>
                <label className={`block mb-1 font-semibold uppercase tracking-wider text-[9px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>Raison ou ordre du jour :</label>
                <textarea
                  value={newDescription}
                  onChange={e => setNewDescription(e.target.value)}
                  placeholder="Entrez brièvement la teneur des résolutions prévues..."
                  rows={2}
                  className={`w-full p-2.5 rounded-lg border font-semibold focus:outline-hidden resize-none ${isLightMode ? "bg-white border-slate-300 text-slate-800 focus:border-blue-500" : "bg-black/60 border-white/10 text-slate-300 focus:border-blue-500/50"}`}
                />
              </div>

              <div className={`flex items-center justify-between p-2.5 border rounded-lg ${isLightMode ? "bg-white border-slate-200" : "bg-black/45 border-white/5"}`}>
                <div className="flex items-center gap-2">
                  <Video className="h-4 w-4 text-blue-400" />
                  <div>
                    <span className={`block font-bold text-[10px] ${isLightMode ? "text-slate-800" : "text-white"}`}>Activer Google Meet</span>
                    <span className="text-[8.5px] text-slate-500">Générer visioconférence</span>
                  </div>
                </div>
                <input 
                  type="checkbox"
                  checked={activateMeetImmediately}
                  onChange={(e) => setActivateMeetImmediately(e.target.checked)}
                  className="h-4 w-4 rounded accent-blue-500 text-black cursor-pointer"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-blue-500 text-black font-extrabold hover:bg-blue-400 rounded-lg transition-all cursor-pointer font-sans shadow-[0_4px_12px_rgba(16,185,129,0.15)] flex items-center justify-center gap-1.5"
              >
                <Plus className="h-4 w-4" />
                Convoquer & Ouvrir Scrutin
              </button>
            </form>
          </div>

          {/* List of dynamic sessions */}
          <div className={`border rounded-2xl p-5 space-y-3 ${isLightMode ? "bg-slate-50 border-slate-205" : "bg-black/35 border-white/10"}`}>
            <h3 className={`text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>
              <Clock className="h-3.5 w-3.5" />
              Séquences de Réunions Actives & Archivées
            </h3>
            
            <div className="space-y-2">
              {meetings.map(m => {
                const isSelected = m.id === activeMeetingId;
                
                let typeColor = isLightMode ? "bg-slate-200 text-slate-700" : "bg-white/5 text-slate-400";
                if (m.type === "CTM") typeColor = "bg-blue-500/10 text-blue-600 border border-blue-500/20";
                else if (m.type === "Assemblée plénière") typeColor = "bg-purple-500/10 text-purple-600 border border-purple-500/20";
                else if (m.type === "WG") typeColor = "bg-blue-500/10 text-blue-600 border border-blue-500/20";

                return (
                  <button
                    key={m.id}
                    onClick={() => {
                      setActiveMeetingId(m.id);
                      setActiveSubTab("meet");
                    }}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col gap-2 relative cursor-pointer ${
                      isSelected
                        ? isLightMode
                          ? "bg-slate-200/50 border-blue-500 shadow-sm"
                          : "bg-white/[0.07] border-blue-500/50 shadow-xs"
                        : isLightMode
                          ? "bg-transparent border-slate-200/60 hover:bg-slate-100"
                          : "bg-transparent border-white/5 hover:bg-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 w-full">
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-bold ${typeColor}`}>
                        {m.type}
                      </span>
                      <span className={`text-[9.5px] font-bold px-2 py-0.5 rounded ${
                        m.status === "Terminé"
                          ? "bg-blue-500/15 text-blue-600"
                          : "bg-amber-500/15 text-amber-500 border border-amber-500/30 animate-pulse"
                      }`}>
                        {m.status}
                      </span>
                    </div>

                    <div className="min-w-0">
                      <p className={`text-xs font-bold leading-snug ${isSelected ? (isLightMode ? "text-slate-900" : "text-white") : (isLightMode ? "text-slate-700" : "text-slate-300")}`}>
                        {m.title}
                      </p>
                      <p className="text-[10px] text-slate-500 font-semibold font-mono mt-1">
                        Heure : {m.time} • Date : {m.date}
                      </p>
                    </div>

                    {m.meetActive && (
                      <div className="flex items-center gap-1 mt-1 text-[9px] text-blue-600 font-bold font-mono">
                        <Video className="h-3 w-3 animate-pulse" />
                        <span>Google Meet disponible</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* CENTER & RIGHT COLUMN - MEETING WORKSPACE */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className={`border rounded-2xl shadow-2xl p-6 space-y-6 relative overflow-hidden ${isLightMode ? "bg-white border-slate-205 text-slate-800" : "bg-[#0b0c14]/90 border-white/10 text-slate-105"}`}>
            
            {/* Header / Active metadata box */}
            <div className={`flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-5 ${isLightMode ? "border-slate-250" : "border-white/10"}`}>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[9.5px] uppercase tracking-widest bg-blue-500/15 border border-blue-500/30 text-blue-600 px-2 py-0.5 rounded font-bold">
                    Scrutin national souverain
                  </span>
                  {activeMeeting.meetActive && (
                    <span className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />
                  )}
                </div>
                
                <h3 className={`text-md font-extrabold mt-1.5 ${isLightMode ? "text-slate-900" : "text-white"}`}>{activeMeeting.title}</h3>
                <p className="text-xs text-slate-500 mt-1 flex items-start sm:items-center gap-1">
                  <span className="font-bold text-slate-500">Sujet soumis :</span> 
                  <span className={`font-mono text-[11px] truncate ${isLightMode ? "text-slate-700" : "text-slate-200"}`}>{activeMeeting.lawSubject}</span>
                </p>
              </div>

              <div className={`text-left md:text-right shrink-0 p-3 rounded-xl border space-y-1 ${isLightMode ? "bg-slate-50 border-slate-250" : "bg-black/30 border-white/5"}`}>
                <span className="text-[9.5px] text-slate-500 font-bold uppercase tracking-wider block">Calcul Quorum</span>
                <span className={`text-xs font-mono font-bold block ${isLightMode ? "text-blue-700" : "text-blue-400"}`}>
                  {quorumStats.presentPCount} / {quorumStats.totalPCount} Membres Votants
                </span>
                <span className={`text-[9.1px] font-bold px-1.5 py-0.5 rounded inline-block ${
                  quorumStats.isQuorumReached 
                    ? "bg-blue-500/10 text-blue-650" 
                    : "bg-amber-500/15 text-amber-600"
                }`}>
                  {quorumStats.isQuorumReached ? "✓ Quorum Atteint" : "⚠️ Séance Consultative"}
                </span>
              </div>
            </div>

            {/* PROROGATIVES & MISSIONS ASSOCIEES AU ROLE ACTIF */}
            {(() => {
              let title = "";
              let description = "";
              let postes = "";
              let colorClasses = "";
              let missions: string[] = [];

              if (userRole === "RAP_CTM") {
                title = "Rapporteur du CTM";
                postes = "Ingénieurs ONIC (Postes 138 à 143)";
                description = "Pilote souverain de la feuille d'émargement, de la présence et du Procès-Verbal.";
                colorClasses = "border-amber-500/25 bg-amber-500/5 text-amber-400";
                missions = [
                  "Responsable de la feuille d'émargement officielle de la séance (ajouts/retraits).",
                  "Vérifie et atteste l'atteinte du quorum (la présence conditionne le quorum).",
                  "Seul habilité à clore le scrutin de vote technique et certifier le PV d'homologation."
                ];
              } else if (userRole === "SEC_PERM") {
                title = "Secrétaire Permanent du CTM";
                postes = "Cadres Secrétariat Général ITP (Postes 16 à 23)";
                description = "Gestionnaire administratif de la commission nationale.";
                colorClasses = "border-blue-500/25 bg-blue-500/5 text-blue-400";
                missions = [
                  "Pouvoir d'initialiser les convocations officielles et planifier les réunions.",
                  "Habilité à confirmer les présences et assister le rapporteur dans l'émargement.",
                  "Gère l'aspect administratif, confirme les participations et tient le registre central."
                ];
              } else if (userRole === "PRES_CTM") {
                title = "Président du CTM";
                postes = "Expertise Universitaire / Arbitre Scientifique";
                description = "Décision scientifique, arbitrage technique et garant de la conformité.";
                colorClasses = "border-blue-500/25 bg-blue-500/5 text-blue-400";
                missions = [
                  "Arbitrage supérieur et présidence technique des concertations réglementaires.",
                  "Rôle de décision scientifique et dépôt d'observations de blocage de l'avant-projet.",
                  "Consulte les scrutins et s'exprime scientifiquement dans l'annexe du PV."
                ];
              } else if (userRole === "GEST_COMP") {
                title = "Gestionnaire Comptable de la CTC";
                postes = "Direction Financière / Organe FONER (Poste 110)";
                description = "Régulateur comptable des indemnités scientifiques sous double énumération.";
                colorClasses = "border-purple-500/25 bg-purple-500/5 text-purple-400";
                missions = [
                  "Calcule en temps réel les enveloppes de liquidation des jetons selon la feuille d'émargement.",
                  "Supervise les structures de financement afférentes et génère les ordres de virement.",
                  "Contrôle l'adéquation présence-calculatrice d'indemnités d'experts."
                ];
              } else if (userRole === "COORD_CTC") {
                title = "Coordonnateur de la CTC";
                postes = "Directeur Général (Poste 15, SG-ITP / Relations Extérieures)";
                description = "Pilotage général et rapporteur de synthèse logistique inter-institutionnel.";
                colorClasses = "border-pink-500/25 bg-pink-500/5 text-pink-400";
                missions = [
                  "Supervision logistique globale pour les grandes réunions d'assemblée plénière.",
                  "Validation de la conformité du circuit de co-gouvernance numérique.",
                  "Audit des indicateurs techniques et financier de la commission nationale."
                ];
              } else if (userRole === "ADMIN") {
                title = "Administrateur technique";
                postes = "BTC – Bureau d'Appui Technique Numérique (Postes 98-100)";
                description = "Support technique et administration souveraine de l'émargement QR-Code.";
                colorClasses = "border-red-500/25 bg-red-500/5 text-red-400";
                missions = [
                  "Support technique pour le système d'émargement numérique (QR Code, plateforme).",
                  "Détenteur de pleins pouvoirs d'édition à des fins d'assistance aux utilisateurs.",
                  "Audit complet de la sécurité de la blockchain nationale de co-gouvernance."
                ];
              } else {
                title = "Membre Permanent (Expert)";
                postes = "Expert Thématique d'Affiliation (Ex: OVD, OR, ONA, CNPR...)";
                description = "Expert technique d'un organe co-financeur participant aux débats et aux votes.";
                colorClasses = "border-slate-500/20 bg-slate-500/5 text-slate-300";
                missions = [
                  "Exprime ses suffrages de vote personnel pour valider ou rejeter l'avant-projet de norme.",
                  "Soumet des remarques et amendements scientifiques via le canal d'études.",
                  "Doit être marqué émargé pour disposer de jetons de présence et de droits de vote."
                ];
              }

              return (
                <div className={`p-4 rounded-xl border flex flex-col gap-3 justify-between text-xs transition-colors duration-200 ${isLightMode ? "bg-slate-50 border-slate-250 text-slate-850" : colorClasses}`}>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-extrabold uppercase tracking-wide text-xs ${isLightMode ? "text-slate-900" : "text-white"}`}>⚙️ Mission active : {title}</span>
                      <span className={`text-[9.5px] font-mono font-bold px-2 py-0.5 rounded-sm uppercase tracking-wider ${isLightMode ? "bg-slate-200/80 border border-slate-300/60 text-slate-705" : "bg-[#050609] border border-white/5"}`}>{postes}</span>
                    </div>
                    <p className={`font-medium text-[11px] leading-relaxed mt-1 ${isLightMode ? "text-slate-650" : "text-slate-300"}`}>
                      {description}
                    </p>
                    <div className={`pt-2 text-[10.5px] space-y-1 p-3 rounded-lg border mt-2 ${isLightMode ? "bg-white border-slate-200 text-slate-600" : "bg-black/40 text-slate-400 border-white/5"}`}>
                      <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">📋 Missions Légales attribuées :</span>
                      {missions.map((m, i) => (
                        <div key={i} className="flex gap-1.5 items-start">
                          <span className="text-blue-500 font-bold shrink-0">•</span>
                          <span className="leading-relaxed">{m}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* SEGMENTED TAB ACTIONS BAR */}
            <div className={`grid grid-cols-4 gap-1.5 p-1 rounded-xl border text-xs font-semibold ${
              isLightMode 
                ? "bg-slate-100 border-slate-250" 
                : "bg-black/45 border-white/5"
            }`}>
              <button
                onClick={() => setActiveSubTab("meet")}
                className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  activeSubTab === "meet"
                    ? isLightMode
                      ? "bg-white text-slate-900 border border-slate-250 font-black shadow-xs"
                      : "bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold"
                    : isLightMode
                      ? "text-slate-600 hover:text-slate-900"
                      : "text-slate-400 hover:text-white"
                }`}
              >
                <Video className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Meet</span>
              </button>
              
              <button
                onClick={() => setActiveSubTab("attendance")}
                className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  activeSubTab === "attendance"
                    ? isLightMode
                      ? "bg-white text-slate-900 border border-slate-250 font-black shadow-xs"
                      : "bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold"
                    : isLightMode
                      ? "text-slate-600 hover:text-slate-900"
                      : "text-slate-400 hover:text-white"
                }`}
              >
                <Users className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Émargement</span>
              </button>

              <button
                onClick={() => setActiveSubTab("vote")}
                className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  activeSubTab === "vote"
                    ? isLightMode
                      ? "bg-white text-slate-900 border border-slate-250 font-black shadow-xs"
                      : "bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold"
                    : isLightMode
                      ? "text-slate-600 hover:text-slate-900"
                      : "text-slate-400 hover:text-white"
                }`}
              >
                <Vote className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Urne Virtuelle (Votes)</span>
              </button>

              <button
                onClick={() => setActiveSubTab("pv")}
                className={`py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  activeSubTab === "pv"
                    ? isLightMode
                      ? "bg-white text-slate-900 border border-slate-250 font-black shadow-xs"
                      : "bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold"
                    : isLightMode
                      ? "text-slate-600 hover:text-slate-900"
                      : "text-slate-400 hover:text-white"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Procès-Verbal</span>
              </button>
            </div>

            {/* TAB CONTENTS */}

            {/* TAB 1: VISIOCONFERENCE DETAILS */}
            {activeSubTab === "meet" && (
              <div className="space-y-6 animate-fadeIn">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Conformément au manuel d'orientation légistique (Article 12), les votes et concertations s'accomplissent aussi de manière numérique par visioconférence sécurisée pour intégrer les experts affiliés en dehors de Kinshasa (Goma, Lubumbashi, Kolwezi).
                </p>

                {activeMeeting.meetActive ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Google Meet virtual frame mockup */}
                    <div className="md:col-span-2 bg-[#05060a] border border-white/10 rounded-2xl overflow-hidden relative group">
                      <div className="aspect-video bg-[#12131a] flex flex-col items-center justify-center text-center p-6 relative">
                        {/* Little absolute bar */}
                        <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 px-3 py-1 rounded-full border border-white/10">
                          <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse"></span>
                          <span className="font-mono text-[9px] font-bold text-white uppercase tracking-wider">Visioconférence LIVE</span>
                        </div>

                        {/* Connected representatives grid */}
                        <div className="grid grid-cols-3 gap-3.5 max-w-sm w-full">
                          {allExperts.slice(0, 5).map((exp, x) => {
                            const isPresent = activeMeeting.attendance[exp.id];
                            return (
                              <div 
                                key={exp.id}
                                className={`p-2.5 rounded-xl border flex flex-col items-center text-center justify-center transition-all ${
                                  isPresent 
                                    ? "bg-white/[0.04] border-blue-500/30 text-white" 
                                    : "bg-black/30 border-white/5 opacity-40 text-slate-500"
                                }`}
                              >
                                <div className={`h-8 w-8 rounded-full flex items-center justify-center font-extrabold text-[10.5px] mb-1.5 ${
                                  isPresent ? "bg-blue-500/20 text-blue-400 border border-blue-500/30" : "bg-slate-800 text-slate-500"
                                }`}>
                                  {exp.name.split(" ").map((n: string) => n[0]).join("")}
                                </div>
                                <span className="text-[9.5px] font-bold truncate max-w-[70px] block">{exp.name.split(" ")[1] || exp.name}</span>
                                <span className="text-[8px] text-slate-500 font-mono mt-0.5">{isPresent ? "ONLINE" : "OFFLINE"}</span>
                              </div>
                            );
                          })}
                          <div className="p-2.5 rounded-xl border border-dashed border-white/5 bg-transparent flex flex-col items-center justify-center text-center text-slate-500">
                            <span className="text-[12px] font-bold">+ {allExperts.length > 5 ? allExperts.length - 5 : 0}</span>
                            <span className="text-[8px] uppercase tracking-tighter">Observateurs</span>
                          </div>
                        </div>

                        <div className="mt-6 text-center">
                          <a
                            href={activeMeeting.meetUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="px-5 py-2.5 bg-blue-500 hover:bg-blue-400 text-black font-extrabold text-xs rounded-xl shadow-[0_4px_15px_rgba(16,185,129,0.3)] inline-flex items-center gap-2 transition-all cursor-pointer uppercase tracking-wider font-sans"
                          >
                            <Video className="h-4.5 w-4.5" />
                            Lancer l'Appel Virtuel (Meet)
                          </a>
                        </div>
                      </div>

                      {/* Video control simulated footer */}
                      <div className="bg-black/80 px-4 py-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
                        <span className="font-semibold text-[10px] text-blue-400 tracking-wide">{activeMeeting.meetUrl}</span>
                        <span className="text-[9.5px]">Cryptage SSL de bout en bout</span>
                      </div>
                    </div>

                    {/* Meet action sidebar controls */}
                    <div className="bg-black/25 border border-white/5 rounded-2xl p-4 space-y-4">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
                        <Share2 className="h-4 w-4 text-blue-400" />
                        Partage d'Accès
                      </h4>
                      <p className="text-[11px] text-slate-400 leading-normal">
                        Transmettez instantanément le lien d'accès crypté Google Meet aux bureaux ministériels et membres permanents du comité CNETP.
                      </p>

                      <div className="space-y-2.5 text-xs pt-2">
                        <button
                          type="button"
                          onClick={() => handleCopyMeetUrl(activeMeeting.meetUrl)}
                          className="w-full py-2 px-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
                        >
                          {copiedMeetId === activeMeeting.meetUrl ? (
                            <>
                              <Check className="h-4 w-4 text-blue-400" />
                              <span className="text-blue-400">Copié !</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-4 w-4 text-slate-400" />
                              <span>Copier l'URL Meet</span>
                            </>
                          )}
                        </button>

                        <button
                          type="button"
                          onClick={() => handleInviteExperts(activeMeeting)}
                          className="w-full py-2 px-3 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 rounded-lg text-blue-400 font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
                        >
                          <Share2 className="h-4 w-4 text-blue-400" />
                          <span>Notifier les Experts</span>
                        </button>
                      </div>

                      <div className="pt-3 border-t border-white/5 font-mono text-[9px] text-slate-500 space-y-1">
                        <p>• URL : {activeMeeting.meetUrl}</p>
                        <p>• Code : {activeMeeting.meetUrl.split("/").pop()}</p>
                        <p>• Statut : Scénario d'enregistrement ouvert</p>
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="bg-black/40 border border-dashed border-white/10 rounded-2xl p-8 text-center space-y-3">
                    <Video className="h-8 w-8 text-slate-500 mx-auto" />
                    <div>
                      <p className="text-xs font-bold text-slate-300">Visioconférence Google Meet déconnectée</p>
                      <p className="text-[11px] text-slate-500 mt-1 max-w-md mx-auto">
                        Cette session d'études est planifiée d'office en présentiel ou n'a pas été configurée avec de liaison Meet numérique.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setMeetings(prev => prev.map(m => m.id === activeMeetingId ? { ...m, meetActive: true } : m));
                        triggerNotification("Un salon Google Meet sécurisé a été généré !", "success");
                      }}
                      className="px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-bold transition-all cursor-pointer inline-block"
                    >
                      Activer visioconférence Meet
                    </button>
                  </div>
                )}

                {/* CTA Redirect to Vote/Emargement */}
                {activeMeeting.status !== "Terminé" && (
                  <div className="mt-8 bg-blue-500/10 border border-blue-500/25 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-1">
                      <span className="text-[11px] text-blue-400 font-extrabold uppercase tracking-widest flex items-center gap-1.5">
                        <Vote className="h-4 w-4" />
                        Session de vote disponible
                      </span>
                      <p className="text-[11px] text-slate-300">
                        Pour attribuer votre suffrage et statuer sur la norme technique, rendez-vous dans l'Urne Virtuelle. (Assurez-vous d'avoir émargé)
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveSubTab("vote")}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-black font-extrabold text-[10.5px] rounded-lg transition-all shadow-md uppercase tracking-wider shrink-0 cursor-pointer"
                    >
                      Ouvrir l'Urne
                    </button>
                  </div>
                )}

              </div>
            )}

            {/* TAB 2: FEUILLE D'EMARGEMENT / ATTENDANCE & QUORUM */}
            {activeSubTab === "attendance" && (
              <div className="space-y-6 animate-fadeIn">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-black/35 p-4 rounded-xl border border-white/5 text-xs">
                  <div>
                    <h4 className="font-bold text-white uppercase text-[11px] flex items-center gap-1">
                      <CheckSquare className="h-4 w-4 text-blue-400" />
                      Règle de quorum sur émargement
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1 max-w-xl">
                      {activeMeeting.type === "Assemblée plénière" 
                        ? "L'adoption finale par l'Assemblée Plénière des 200 experts se fait obligatoirement par consensus. Le quorum exige la présence d'au moins 75% des experts scientifiques de la CNETP (soit 150 experts)."
                        : activeMeeting.type === "CTM"
                          ? "Au niveau de la Sous-Commission Technique (Comité Miroir de 20 membres permanents), le vote sectoriel exige un quorum strict de 2/3 des membres émargés (soit 14 experts)."
                          : `Le quorum exige la présence d'au moins ${activeMeeting.quorumPercentage}% des intervenants pour statuer.`}
                    </p>
                  </div>

                  <div className="bg-[#05060a] p-3 rounded-lg border border-white/10 shrink-0 font-mono text-center">
                    <span className="text-[10px] text-slate-500 block">Présence Votante</span>
                    <span className="text-sm font-extrabold text-white">{quorumStats.activePresencePercentage}%</span>
                    <span className="text-[8.5px] text-slate-500 block uppercase font-sans font-bold mt-1">Requis : {activeMeeting.quorumPercentage}%</span>
                  </div>
                </div>

                {/* ROLE-SPECIFIC SPECIAL WIDGET FOR EMARGEMENT */}
                {userRole === "GEST_COMP" && (
                  <div className="bg-purple-950/20 border border-purple-500/25 rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-fadeIn">
                    <div>
                      <span className="text-[10px] text-purple-400 font-bold uppercase tracking-wide">💰 Diagnostic Comptable (Jetons de Présence)</span>
                      <p className="text-xs text-slate-300 mt-1 max-w-xl">
                        En tant que <strong>Gestionnaire Comptable</strong>, l'outil évalue le montant des jetons d'études liquidés d'après les présences émargées :
                      </p>
                    </div>
                    <div className="bg-[#0c0512] border border-purple-550/10 p-3 rounded-lg text-center font-mono shrink-0">
                      <span className="text-[9px] text-slate-500 block">ENVELOPPE ÉVALUÉE</span>
                      <span className="text-md font-bold text-purple-400">{(allExperts.filter(e => activeMeeting.attendance[e.id]).length) * 180} USD</span>
                      <span className="text-[8px] text-slate-500 block mt-0.5">({allExperts.filter(e => activeMeeting.attendance[e.id]).length} experts × 180$)</span>
                    </div>
                  </div>
                )}

                {/* QR CODE DIGITAL ENTRY SIMULATION FOR EXPERT OR OTHER ROLES */}
                {(userRole !== "ADMIN" && userRole !== "RAP_CTM" && userRole !== "SEC_PERM") && (
                  <div className="bg-blue-950/20 border border-blue-550/20 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 animate-fadeIn">
                    <div className="space-y-1">
                      <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wide">📱 Émargement Autonome Numérique</span>
                      <p className="text-xs text-slate-300">
                        Vous incarnez <strong>{simulatedProfile?.name || "Expert Thématique"}</strong> ({simulatedProfile?.structure}). Signalez votre présence directement par QR Code d'assistance.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setMeetings(prev => prev.map(m => {
                          if (m.id === activeMeetingId) {
                            const nextAt = { ...m.attendance };
                            nextAt["sim-user"] = true;
                            return { ...m, attendance: nextAt };
                          }
                          return m;
                        }));
                        triggerNotification(`Émargement QR-Code simulé avec succès pour ${simulatedProfile?.name || "vous-même"} !`, "success");
                      }}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-black font-extrabold text-[10.5px] rounded-lg transition-all shadow-md flex items-center gap-1.5 uppercase tracking-wider font-sans shrink-0 cursor-pointer"
                    >
                      <span>Simuler Scan Badge QR-Code</span>
                    </button>
                  </div>
                )}

                {/* Checklist list */}
                <div className="space-y-2.5">
                  <h4 className="text-[10.5px] font-bold text-slate-400 uppercase tracking-wider px-1">Feuille d'émargement officielle (Experts)</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {allExperts.map((exp) => {
                      const isPresent = activeMeeting.attendance[exp.id] || false;
                      return (
                        <div
                          key={exp.id}
                          className={`p-3 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                            isPresent 
                              ? "bg-blue-500/5 border-blue-500/25" 
                              : "bg-black/25 border-white/5 opacity-80"
                          }`}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="h-8.5 w-8.5 rounded-lg bg-black/40 border border-white/10 flex items-center justify-center font-bold text-xs shrink-0">
                              {exp.name.split(" ").map((n: string) => n[0]).join("")}
                            </div>
                            <div className="min-w-0">
                              <p className="text-xs font-bold text-white truncate">{exp.name}</p>
                              <div className="flex items-center gap-1 my-0.5 text-[9.5px]">
                                <span className={`font-mono text-[9px] font-bold px-1 rounded-sm uppercase ${
                                  exp.isPermanent ? "bg-purple-500/15 text-purple-400" : "bg-slate-500/10 text-slate-500"
                                }`}>
                                  {exp.isPermanent ? "Membre P (Votant)" : "Observateur (Non V)"}
                                </span>
                                <span className="text-slate-600">•</span>
                                <span className="text-slate-400 truncate max-w-[120px]">{exp.structure.split(" ")[0]}</span>
                              </div>
                            </div>
                          </div>

                          <button
                            type="button"
                            disabled={userRole !== "ADMIN" && userRole !== "RAP_CTM" && userRole !== "SEC_PERM"}
                            onClick={() => toggleAttendance(exp.id)}
                            className={`px-3 py-1.5 rounded-md text-[10.5px] font-bold tracking-tight transition-all cursor-pointer ${
                              isPresent 
                                ? "bg-blue-500 text-black shadow-[0_0_10px_rgba(16,185,129,0.25)]" 
                                : "bg-white/5 hover:bg-white/10 text-slate-300"
                            } ${(userRole !== "ADMIN" && userRole !== "RAP_CTM" && userRole !== "SEC_PERM") ? "opacity-50 cursor-not-allowed" : ""}`}
                          >
                            {isPresent ? "✓ Présent" : "✗ Absent"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Verdict Quorum callout */}
                <div className={`p-4 rounded-xl border flex items-start gap-3 ${
                  quorumStats.isQuorumReached 
                    ? "bg-blue-500/5 border-blue-500/20 text-blue-400" 
                    : "bg-amber-500/5 border-amber-500/25 text-amber-500"
                }`}>
                  <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                  <div className="text-xs">
                    <p className="font-extrabold uppercase">
                      {quorumStats.isQuorumReached ? "SÉANCE SOUPERÉ LÉGITIME" : "SEUIL DE QUORUM NON ATTEINT"}
                    </p>
                    <p className="text-slate-400 mt-1 leading-normal text-[11px]">
                      {quorumStats.isQuorumReached 
                        ? "Le nombre requis de membres techniques permanents habilités est réuni. Les résolutions et votes souverains qui suivent disposeront d'une pleine valeur légale de co-gouvernance."
                        : `Le quorum requis de ${activeMeeting.quorumPercentage}% de Membres P n'est pas encore atteint pour cette séance. Le scrutin ne pourra pas valider formellement la norme technique RDC dans le circuit d'homologation administrative.`}
                    </p>
                  </div>
                </div>

              </div>
            )}

            {/* TAB 3: BALLOTBOX / LIVE ELECTORAL VOTING */}
            {activeSubTab === "vote" && (
              <div className="space-y-6 animate-fadeIn">
                
                {/* Voting stats widgets */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-black/30 border border-white/5 p-3 rounded-xl font-mono text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Votants possibles</span>
                    <span className="text-lg font-extrabold text-white">{votesStats.totalVotersPossible}</span>
                  </div>
                  <div className="bg-black/30 border border-white/5 p-3 rounded-xl font-mono text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Suffrages exprimés</span>
                    <span className="text-lg font-extrabold text-white">{votesStats.totalVotesCast}</span>
                  </div>
                  <div className="bg-black/30 border border-white/5 p-3 rounded-xl font-mono text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Abstentions</span>
                    <span className="text-lg font-extrabold text-white">{votesStats.abstentionCount}</span>
                  </div>
                  <div className="bg-black/30 border border-white/5 p-3 rounded-xl font-mono text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Taux d'approbation</span>
                    <span className={`text-lg font-extrabold ${votesStats.isApproved ? "text-blue-400" : "text-amber-500"}`}>
                      {votesStats.approvalRate}%
                    </span>
                  </div>
                </div>

                {/* Progress Visual bars */}
                <div className="bg-black/35 border border-white/5 p-4.5 rounded-xl space-y-4">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                    <span className="uppercase">Régularité des suffrages</span>
                    <span>Consensus requis : {activeMeeting.quorumPercentage}%</span>
                  </div>

                  <div className="space-y-3.5 text-xs font-semibold">
                    {/* POUR */}
                    <div className="space-y-1 block">
                      <div className="flex justify-between font-bold text-[11.5px]">
                        <span className="text-blue-400">Pour / Approbations (OUI)</span>
                        <span className="font-mono text-slate-300">{votesStats.pourCount} voix ({votesStats.pourPct}%)</span>
                      </div>
                      <div className="w-full h-2.5 bg-white/5 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full transition-all duration-300"
                          style={{ width: `${votesStats.pourPct}%` }}
                        />
                      </div>
                    </div>

                    {/* CONTRE */}
                    <div className="space-y-1 block">
                      <div className="flex justify-between font-bold text-[11.5px]">
                        <span className="text-red-400">Contre / Opposition (NON)</span>
                        <span className="font-mono text-slate-300">{votesStats.contreCount} voix ({votesStats.contrePct}%)</span>
                      </div>
                      <div className="w-full h-2.5 bg-white/5 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-red-500 rounded-full transition-all duration-300"
                          style={{ width: `${votesStats.contrePct}%` }}
                        />
                      </div>
                    </div>

                    {/* ABSTENTION */}
                    <div className="space-y-1 block">
                      <div className="flex justify-between font-bold text-[11.5px]">
                        <span className="text-slate-400">Abstentions / Neutres</span>
                        <span className="font-mono text-slate-300">{votesStats.abstentionCount} voix ({votesStats.abstentionPct}%)</span>
                      </div>
                      <div className="w-full h-2.5 bg-white/5 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-slate-500 rounded-full transition-all duration-300"
                          style={{ width: `${votesStats.abstentionPct}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className={`p-3 rounded-lg text-[11px] font-mono text-center font-bold ${
                    votesStats.isApproved ? "bg-blue-550/20 text-blue-400 border border-blue-500/30" : "bg-red-950/20 text-red-400 border border-red-500/30"
                  }`}>
                    {votesStats.verdictText}
                    <div className="text-[9px] text-slate-400 mt-1 font-sans">
                      Règle : {votesStats.thresholdRuleText}
                    </div>
                  </div>
                </div>

                {/* INTERACTIVE CONTROLS CORRESPONDING TO ACTIVE ROLE */}
                {activeMeeting.status !== "Terminé" && (
                  <div className="space-y-4 animate-fadeIn">
                    
                    {/* 1) INDIVIDUAL VOTE BALLOT FOR USERS (EXPERTS OR SPECIAL ROLES THAT CAN VOTE) */}
                    {allExperts.some(e => e.id === "sim-user") && (
                      <div className="bg-blue-950/10 border border-blue-500/20 rounded-xl p-4 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-2">
                          <span className="text-[11px] text-blue-400 font-bold uppercase tracking-wider flex items-center gap-1.5 font-sans">
                            <Vote className="h-4 w-4 text-blue-400" />
                            Votre Bulletin de Vote Personnel ({simulatedProfile?.name || "Vous-même"})
                          </span>
                          <span className="text-[9px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded border border-white/5">
                            Rôle : {
                              userRole === "ADMIN" ? "Administrateur technique" : 
                              userRole === "RAP_CTM" ? "Rapporteur CTM" :
                              userRole === "SEC_PERM" ? "Secrétaire Permanent" :
                              userRole === "PRES_CTM" ? "Président du CTM" :
                              userRole === "GEST_COMP" ? "Comptable Principal" :
                              userRole === "COORD_CTC" ? "Coordonnateur CTC" : "Membre Permanent (Expert)"
                            } {(!userRole.startsWith("GEST_COMP") && !userRole.startsWith("COORD_CTC") && !userRole.startsWith("ADMIN")) ? "• Permanent Votant" : "• Observateur (Mode Démo)"}
                          </span>
                        </div>

                        {!activeMeeting.attendance["sim-user"] ? (
                          <div className="bg-amber-500/5 border border-amber-500/25 p-3.5 rounded-lg space-y-2.5">
                            <div className="flex items-start gap-2 text-xs">
                              <span className="text-amber-500 font-bold shrink-0">⚠️</span>
                              <div className="space-y-0.5">
                                <p className="font-bold text-amber-500 uppercase text-[10.5px] font-sans">Statut : Non Émargé à la Séance</p>
                                <p className="text-slate-300 text-[11px] leading-relaxed font-sans">
                                  Conformément au manuel de co-gouvernance CNETP, l'émargement de présence est obligatoire pour pouvoir exprimer son vote légal et être éligible aux jetons de présence.
                                </p>
                              </div>
                            </div>
                            <div className="flex justify-start">
                              <button
                                type="button"
                                onClick={() => {
                                  setMeetings(prev => prev.map(m => {
                                    if (m.id === activeMeetingId) {
                                      const nextAt = { ...m.attendance };
                                      nextAt["sim-user"] = true;
                                      return { ...m, attendance: nextAt };
                                    }
                                    return m;
                                  }));
                                  triggerNotification(`Émargement QR-Code simulé avec succès pour ${simulatedProfile?.name || "vous-même"} ! Votre bulletin de vote est maintenant débloqué.`, "success");
                                }}
                                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-extrabold text-[10.5px] rounded-lg transition-all shadow-md uppercase tracking-wider flex items-center gap-1.5 cursor-pointer font-sans"
                              >
                                📱 S'émarger maintenant par QR-Code
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <p className="text-xs text-slate-300 leading-relaxed font-sans">
                              Exprimez ci-dessous votre suffrage pour ou contre l'adoption définitive du texte réglementaire :
                              <br />
                              <strong className="text-white font-mono">"{activeMeeting.lawSubject}"</strong>.
                            </p>
                            
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => {
                                  handleCastExpertVote("sim-user", "pour");
                                  triggerNotification("Votre suffrage favorable (POUR) a été enregistré !", "success");
                                }}
                                className={`flex-1 py-2.5 rounded-lg text-xs font-semibold hover:opacity-95 transition-all cursor-pointer flex items-center justify-center gap-1 font-sans ${
                                  activeMeeting.expertVotes["sim-user"] === "pour"
                                    ? "bg-blue-500 text-black font-extrabold shadow-lg"
                                    : "bg-white/5 text-slate-300 hover:bg-white/10"
                                }`}
                              >
                                {activeMeeting.expertVotes["sim-user"] === "pour" && "✓ "}
                                OUI – Voter Pour
                              </button>
                              
                              <button
                                type="button"
                                onClick={() => {
                                  handleCastExpertVote("sim-user", "contre");
                                  triggerNotification("Votre suffrage d'opposition (CONTRE) a été enregistré !", "success");
                                }}
                                className={`flex-1 py-2.5 rounded-lg text-xs font-semibold hover:opacity-95 transition-all cursor-pointer flex items-center justify-center gap-1 font-sans ${
                                  activeMeeting.expertVotes["sim-user"] === "contre"
                                    ? "bg-red-500 text-black font-extrabold shadow-lg"
                                    : "bg-white/5 text-slate-300 hover:bg-white/10"
                                }`}
                              >
                                {activeMeeting.expertVotes["sim-user"] === "contre" && "✓ "}
                                NON – Voter Contre
                              </button>
                              
                              <button
                                type="button"
                                onClick={() => {
                                  handleCastExpertVote("sim-user", "abstention");
                                  triggerNotification("Votre abstention a été enregistrée.", "info");
                                }}
                                className={`flex-1 py-2.5 rounded-lg text-xs font-semibold hover:opacity-95 transition-all cursor-pointer flex items-center justify-center gap-1 font-sans ${
                                  activeMeeting.expertVotes["sim-user"] === "abstention"
                                    ? "bg-slate-300 text-black font-extrabold shadow-lg"
                                    : "bg-white/5 text-slate-300 hover:bg-white/10"
                                }`}
                              >
                                {activeMeeting.expertVotes["sim-user"] === "abstention" && "✓ "}
                                Abstention
                              </button>
                            </div>

                            {activeMeeting.expertVotes["sim-user"] && (
                              <p className="text-[10px] text-blue-400 font-mono text-right font-semibold">
                                ✓ Votre choix enregistré : {activeMeeting.expertVotes["sim-user"]?.toUpperCase()}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 2) PRESIDENTIAL OBSERVATIONS & SCIENTIFIC ARBITRATION VIEW */}
                    {userRole === "PRES_CTM" && (
                      <div className="bg-blue-950/15 border border-blue-500/20 rounded-xl p-4 space-y-3">
                        <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider block">
                          ⚖️ Consigner les Délibérations & Avis d'Arbitrage (Président du CTM)
                        </span>
                        <p className="text-xs text-slate-300">
                          En tant que <strong>Président Scientifique du CTM</strong>, formulez souverainement vos remarques d'arbitrage de conformité technique. Elles seront instantanément intégrées au Procès-Verbal réglementaire national.
                        </p>
                        <textarea
                          value={activeMeeting.observations}
                          onChange={(e) => {
                            const val = e.target.value;
                            setMeetings(prev => prev.map(m => m.id === activeMeetingId ? { ...m, observations: val } : m));
                          }}
                          placeholder="Entrez vos réserves techniques, amendements ou observations de blocage de haut niveau..."
                          rows={3}
                          className="w-full p-2.5 rounded-lg border border-white/10 bg-black/60 font-semibold text-slate-200 text-xs focus:outline-hidden focus:border-blue-500/50 resize-none"
                        />
                        <div className="flex justify-end">
                          <span className="text-[10px] text-slate-500 font-mono">✓ Consigné automatiquement de plein droit</span>
                        </div>
                      </div>
                    )}

                    {/* 3) SECRETARY ADMINISTRATIVE REMINDER TRIGGERS */}
                    {userRole === "SEC_PERM" && (
                      <div className="bg-blue-950/15 border border-blue-500/20 rounded-xl p-4 space-y-2">
                        <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider block">
                          📢 Rappels des Suffrages (Secrétaire Permanent)
                        </span>
                        <p className="text-xs text-slate-300">
                          Certains experts ayant émargé n'ont pas achevé de saisir leur bulletin technique. Relancez instantanément les retardataires via alertes sécurisées.
                        </p>
                        <button
                          type="button"
                          onClick={() => {
                            triggerNotification("Ordre de rappel expédié ! Notifications transmises de plein droit aux experts techniques.", "success");
                          }}
                          className="py-2 px-4 bg-blue-500 hover:bg-blue-400 text-black font-extrabold text-[10.5px] rounded-lg transition-all shadow-md inline-flex items-center gap-1.5 uppercase tracking-wide font-sans cursor-pointer"
                        >
                          Relancer les votants retardataires
                        </button>
                      </div>
                    )}
                    
                  </div>
                )}

                {/* BALLOT CAST SECTOR - EXPERTS (VISIBLE TO ALL FOR DEMONSTRATION & REVIEWS) */}
                {activeMeeting.status !== "Terminé" ? (
                  <div className="bg-black/25 border border-white/10 rounded-xl p-5 space-y-4 animate-fadeIn">
                    <h4 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                      <span className="flex items-center gap-1.5">
                        <CheckSquare className="h-4 w-4 text-blue-400" />
                        {(userRole === "ADMIN" || userRole === "RAP_CTM" || userRole === "SEC_PERM") 
                          ? "Saisie des Suffrages réglementaires (Contrôle Autorisé)" 
                          : "Simulateur de scrutin d'experts (Démonstration & Revue)"}
                      </span>
                      <span className="font-mono text-[9.5px] text-slate-500">Uniquement membres permanents présents émargés</span>
                    </h4>

                    {!(userRole === "ADMIN" || userRole === "RAP_CTM" || userRole === "SEC_PERM") && (
                      <p className="text-[11px] text-slate-400 bg-white/[0.01] border border-white/5 p-3 rounded-lg leading-relaxed font-sans">
                        💡 <strong>Mode Démonstration :</strong> En tant que <em>{
                          userRole === "ADMIN" ? "Administrateur technique" : 
                          userRole === "RAP_CTM" ? "Rapporteur CTM" :
                          userRole === "SEC_PERM" ? "Secrétaire Permanent" :
                          userRole === "PRES_CTM" ? "Président du CTM" :
                          userRole === "GEST_COMP" ? "Comptable Principal" :
                          userRole === "COORD_CTC" ? "Coordonnateur CTC" : "Membre Permanent (Expert)"
                        }</em>, l'urne virtuelle vous est présentée de manière transparente. Vous pouvez simuler à votre guise le vote de chaque expert émargé en cliquant sur <strong>Oui</strong> / <strong>Non</strong> / <strong>Abs.</strong> pour observer la mise à jour instantanée du taux de consensus national !
                      </p>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {allExperts.filter(e => e.isPermanent && activeMeeting.attendance[e.id]).map((exp) => {
                        const currentVote = activeMeeting.expertVotes[exp.id];
                        return (
                          <div 
                            key={exp.id}
                            className="p-3 bg-black/40 border border-white/5 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                          >
                            <div className="min-w-0">
                              <p className="text-xs font-bold text-white truncate">{exp.name}</p>
                              <p className="text-[9px] text-slate-500 truncate mt-0.5">{exp.role} ({exp.structure.split(" ")[0]})</p>
                            </div>

                            {/* Vote selection tags */}
                            <div className="flex gap-1">
                              <button
                                type="button"
                                onClick={() => handleCastExpertVote(exp.id, "pour")}
                                className={`px-2 py-1 rounded text-[10px] font-bold transition-all cursor-pointer ${
                                  currentVote === "pour"
                                    ? "bg-blue-500 text-black font-extrabold"
                                    : "bg-white/5 hover:bg-white/10 text-slate-400"
                                }`}
                              >
                                Oui
                              </button>
                              <button
                                type="button"
                                onClick={() => handleCastExpertVote(exp.id, "contre")}
                                className={`px-2 py-1 rounded text-[10px] font-bold transition-all cursor-pointer ${
                                  currentVote === "contre"
                                    ? "bg-red-500 text-black font-extrabold"
                                    : "bg-white/5 hover:bg-white/10 text-slate-400"
                                }`}
                              >
                                Non
                              </button>
                              <button
                                type="button"
                                onClick={() => handleCastExpertVote(exp.id, "abstention")}
                                className={`px-2 py-1 rounded text-[10px] font-bold transition-all cursor-pointer ${
                                  currentVote === "abstention"
                                    ? "bg-slate-300 text-black"
                                    : "bg-white/5 hover:bg-white/10 text-slate-400"
                                }`}
                              >
                                Abs.
                              </button>
                              <button
                                type="button"
                                onClick={() => handleCastExpertVote(exp.id, "non-voté")}
                                className={`px-2 py-1 rounded text-[10px] transition-all cursor-pointer bg-transparent text-slate-600 hover:text-slate-400`}
                                title="Effacer le vote"
                              >
                                ✗
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {allExperts.filter(e => e.isPermanent && activeMeeting.attendance[e.id]).length === 0 && (
                      <p className="text-center text-xs text-slate-500 italic py-4">
                        Aucun membre permanent marqué présent sur la feuille d'émargement.
                      </p>
                    )}
                  </div>
                ) : null}

                {/* CLOSING THE ACTION (RAPPORTUER & ADMIN ONLY) */}
                {activeMeeting.status !== "Terminé" && (userRole === "RAP_CTM" || userRole === "ADMIN") ? (
                    <div className="pt-4 border-t border-white/5 flex justify-end animate-fadeIn">
                      <button
                        type="button"
                        onClick={handleCloseScrutinAndGeneratePv}
                        className="px-5 py-2.5 bg-blue-500 text-black font-extrabold hover:bg-blue-400 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 shadow-md"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        Clore le Scrutin & Valider le PV
                      </button>
                    </div>
                ) : activeMeeting.status === "Terminé" ? (
                  <div className="bg-blue-500/5 border border-blue-500/10 p-5 rounded-2xl flex items-start gap-3">
                    <CheckSquare className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <p className="font-extrabold text-blue-400 uppercase">SCRUTIN ARCHIVÉ ET VISÉ</p>
                      <p className="text-slate-400 mt-1 leading-relaxed">
                        Cette session de concertation est verrouillée souverainement. Les résultats officiels ont été authentifiés de manière asymétrique sur l'enregistrement CNETP crypté. Le rapport de procès-verbal est disponible en téléchargement officiel.
                      </p>
                    </div>
                  </div>
                ) : null}

              </div>
            )}

            {/* TAB 4: PROCÈS-VERBAL GENERATOR / REPORT DESIGN */}
            {activeSubTab === "pv" && (
              <div className="space-y-6 animate-fadeIn">
                
                <p className="text-xs text-slate-400 leading-relaxed">
                  Conformément aux attributions de co-gouvernance, le <strong>Rapporteur (ONIC)</strong> pilote l'ordre du jour et certifie la feuille d'émargement. Le PV ci-dessous résume souverainement l'issue des concertations techniques.
                </p>

                {activeMeeting.pvGenerated ? (
                  <div className="bg-black/35 border border-white/10 rounded-xl p-5 space-y-4">
                    <div className="flex items-center justify-between border-b border-white/5 pb-3">
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 uppercase font-bold block">Document Authentique</span>
                        <h4 className="text-xs font-bold text-white uppercase tracking-wider mt-0.5">PV d'Homologation n°{activeMeeting.id.toUpperCase()}</h4>
                      </div>
                      <span className="text-[9px] font-bold px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded-md select-all uppercase font-mono">
                        CNETP-{activeMeeting.id}
                      </span>
                    </div>

                    <div className="p-4 bg-white/[0.02] border border-white/5 rounded-lg space-y-3.5 text-xs text-slate-300 leading-relaxed">
                      <p>
                        L'an deux mille vingt-six, le <span className="font-bold text-white">{activeMeeting.date}</span> s'est tenue la séance de vote pour la validation légistique du texte normatif :
                        <br />
                        <strong className="text-blue-400 font-mono">"{activeMeeting.lawSubject}"</strong>.
                      </p>

                      <div className="space-y-1 block">
                        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tight block">1. Participants & Émargement</span>
                        <p>
                          Nombre total d'experts permanents convoqués au quorum : <strong className="text-slate-100">{quorumStats.totalPCount}</strong>.
                          <br />
                          Nombre de présences valides émargées avant la séance : <strong className="text-slate-100">{quorumStats.presentPCount}</strong>.
                          <br />
                          Verdict du Quorum requis : <strong className="text-blue-400">{quorumStats.isQuorumReached ? "Atteint" : "Insuffisant d'office, séance d'auditions d'avis consultatif"}</strong>.
                        </p>
                      </div>

                      <div className="space-y-1 block">
                        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tight block">2. Teneur Légistique & Suffrages</span>
                        <ul className="list-disc list-inside space-y-0.5 pl-1">
                          <li>Votes Favorables (Pour) : <strong>{votesStats.pourCount}</strong> ({votesStats.pourPct}%)</li>
                          <li>Votes Défavorables (Contre) : <strong>{votesStats.contreCount}</strong> ({votesStats.contrePct}%)</li>
                          <li>Abstentions certifiées : <strong>{votesStats.abstentionCount}</strong> ({votesStats.abstentionPct}%)</li>
                        </ul>
                        <p className="mt-1 font-mono text-[11px]">
                          Taux d'approbation d'experts : <strong className="text-white">{votesStats.approvalRate}%</strong> (<strong>{votesStats.isApproved ? "CONDUIT À L'HOMOLOGATION (HOMOLOGATION VALIDÉE)" : "HOMOLOGATION REFUSÉE / BLOCAGE"}</strong>).
                        </p>
                        <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                          Mode de scrutin : <span className="text-slate-300 font-bold">{votesStats.thresholdRuleText}</span> | Verdict : <span className={votesStats.isApproved ? "text-blue-400 font-bold" : "text-amber-500 font-bold"}>{votesStats.verdictText}</span>
                        </p>
                      </div>

                      <div className="space-y-1 block">
                        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tight block">3. Remarques du Secrétariat Général Technique (RDC)</span>
                        <p className="italic text-slate-400">
                          {activeMeeting.observations || "Aucun amendement subsidiaire n'a été inséré au dossier des débats de co-gouvernance."}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setIsPvModalOpen(true)}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-black font-extrabold text-xs rounded-lg transition-all flex items-center gap-1.5 cursor-pointer shadow-md uppercase tracking-wider font-sans"
                      >
                        <Eye className="h-4 w-4" />
                        Imprimer le PV Officiel
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          const pvText = `RÉPUBLIQUE DÉMOCRATIQUE DU CONGO\nCNETP RDC - PROCÈS-VERBAL\n\nID: CNETP-${activeMeeting.id}\nSujet: ${activeMeeting.lawSubject}\nPrésences: ${quorumStats.presentPCount} / ${quorumStats.totalPCount}\nVotes favorables: ${votesStats.pourCount} (${votesStats.pourPct}%)\nVotes défavorables: ${votesStats.contreCount}\nAbstentions: ${votesStats.abstentionCount}\nObservations: ${activeMeeting.observations || 'N/A'}`;
                          navigator.clipboard.writeText(pvText);
                          triggerNotification("Le procès-verbal textuel a été copié dans votre presse-papier !", "success");
                        }}
                        className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold text-xs rounded-lg transition-all flex items-center gap-1.5 cursor-pointer"
                      >
                        <Copy className="h-4 w-4" />
                        Copier les métadonnées
                      </button>
                    </div>

                  </div>
                ) : (
                  <div className="bg-black/40 border border-dashed border-white/10 rounded-2xl p-8 text-center space-y-4">
                    <FileSpreadsheet className="h-8 w-8 text-slate-500 mx-auto" />
                    <div>
                      <p className="text-xs font-bold text-slate-200 uppercase">Le scrutin n'est pas clos</p>
                      <p className="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto">
                        Afin de pouvoir générer le procès-verbal d'homologation légale sous seing de RDC, vous devez d'abord clore l'enregistrement des suffrages actifs.
                      </p>
                    </div>
                    
                    <button
                      type="button"
                      onClick={() => setActiveSubTab("vote")}
                      className="px-4 py-2 bg-blue-500 text-black font-semibold rounded-lg text-xs transition-all cursor-pointer inline-flex items-center gap-1 hover:bg-blue-400"
                    >
                      <span>Aller au Scrutin</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}

              </div>
            )}

          </div>

        </div>

      </div>

      {/* FOOTER STATS INFORMATIONS ACCONTING FOR LAWS IN RDC */}
      <div className="bg-black/25 border border-white/10 rounded-xl p-5">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 pb-2 border-b border-white/5 flex items-center gap-1.5">
          <TrendingUp className="h-4 w-4 text-blue-400" />
          État de Validation Législative des Textes (Session 2026)
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-semibold">
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Réglementations Adoptées</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">17 Standards</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-blue-500 h-1 rounded-full" style={{ width: "85%" }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Quorum Consensuel Moyen</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">91.4 %</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-blue-500 h-1 rounded-full" style={{ width: "91.4%" }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Enquêtes Publiques Ouvertes</span>
            <span className="text-xl font-mono font-extrabold text-blue-400 mt-1 block">4 Dossiers</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-blue-400 h-1 rounded-full" style={{ width: "40%" }}></div>
            </div>
          </div>
          <div className="bg-black/30 border border-white/5 p-4 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase tracking-tight block">Sceaux de certification Visés</span>
            <span className="text-xl font-mono font-extrabold text-white mt-1 block">22 Arrêtés</span>
            <div className="w-full bg-white/5 h-1 rounded-full mt-2">
              <div className="bg-blue-500 h-1 rounded-full" style={{ width: "100%" }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* OVERLAY PROCÈS-VERBAL PRINTABLE TEMPLATE MODAL */}
      {isPvModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/15 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-scaleUp">
            
            {/* Stamp header banner */}
            <div className="bg-[#050609] p-6 border-b border-white/10 relative text-center flex flex-col items-center">
              <span className="absolute left-6 top-6 text-slate-500 font-serif text-[9px] uppercase font-bold text-left hidden sm:block leading-snug">
                Ministère des Infrastructures<br />et Travaux Publics
              </span>
              
              <div className="h-10 w-10 bg-blue-500 text-black font-black flex items-center justify-center rounded-xl shadow-[0_0_12px_rgba(16,185,129,0.4)] text-xs">
                CNETP
              </div>
              <h3 className="font-serif font-extrabold text-white text-md tracking-wider mt-3 uppercase">RÉPUBLIQUE DÉMOCRATIQUE DU CONGO</h3>
              <p className="text-[9.5px] text-slate-400 tracking-wider uppercase font-semibold mt-1">CNETP - COMMISSION NATIONALE POUR L'ÉLABORATION DES NORMES</p>
            </div>

            {/* Content body with classic stamp aesthetics */}
            <div className="p-8 space-y-6 bg-[#0a0a0f] font-serif text-slate-200 text-xs leading-relaxed max-h-[420px] overflow-y-auto">
              
              <div className="border-b border-dashed border-white/10 pb-4 text-center">
                <p className="font-sans font-extrabold text-blue-400 text-sm tracking-wide uppercase">PROCÈS-VERBAL DE CONCERTATION TECHNIQUE ET D'ADOPTION n°{activeMeeting.id.toUpperCase()}</p>
                <p className="text-[10.5px] text-slate-500 font-mono italic">Fait le {activeMeeting.date} à Kinshasa, Secrétariat permanent Gombe, RDC</p>
              </div>

              <div>
                <p className="font-bold underline text-slate-300 uppercase tracking-tight text-[11px]">Préambule :</p>
                <p className="mt-1">
                  En vertu de la co-gouvernance scientifique et technique attribuée par ordonnance ministérielle, s'est réunie l'assemblée extraordinaire pour délibérer de l'avant-projet réglementaire national intitulé :
                  <br />
                  <strong className="text-white font-sans text-xs italic bg-white/[0.02] border border-white/5 py-1 px-2.5 rounded block mt-1.5">"{activeMeeting.lawSubject}"</strong>.
                </p>
              </div>

              <div>
                <p className="font-bold underline text-slate-300 uppercase tracking-tight text-[11px]">1. Feuille de Présence & Quorum :</p>
                <p className="mt-1">
                  Membres permanents d'organes convoqués : <strong className="text-slate-100">{quorumStats.totalPCount}</strong>.
                  <br />
                  Représentants de métiers émargés présents au Quorum : <strong className="text-slate-100">{quorumStats.presentPCount}</strong>.
                  <br />
                  Le quorum légal de validation fixé à <strong className="text-slate-100">{activeMeeting.quorumPercentage}%</strong> étant certifié par le Secrétariat permanent, les délibérations rattachées possèdent force exécutoire légistique.
                </p>
              </div>

              <div>
                <p className="font-bold underline text-slate-300 uppercase tracking-tight text-[11px]">2. Résultats Certifiés de Scrutin :</p>
                <ul className="list-disc list-inside mt-1 pl-1 space-y-1">
                  <li>Pourcentage d'approbation d'experts favorables (POUR) : <strong className="text-blue-400">{votesStats.pourPct}%</strong> ({votesStats.pourCount} votes)</li>
                  <li>Pourcentage de désaccords (CONTRE) : <strong className="text-red-400">{votesStats.contrePct}%</strong> ({votesStats.contreCount} votes)</li>
                  <li>Abstentions neutres (SANS APPRÉCIATION) : <strong className="text-slate-400">{votesStats.abstentionPct}%</strong> ({votesStats.abstentionCount} votes)</li>
                </ul>
                <p className="mt-2 text-blue-400 font-bold font-sans text-[10.5px]">
                  Consensus d'homologation : {votesStats.isApproved ? "✓ CONSTATÉ CONFORME" : "✗ REJETÉ - RECOURS EXPÉDIÉ EN COMMISSION"}
                </p>
              </div>

              {activeMeeting.observations && (
                <div>
                  <p className="font-bold underline text-slate-300 uppercase tracking-tight text-[11px]">3. Observations consignées :</p>
                  <p className="italic text-slate-400 mt-1 whitespace-pre-wrap">
                    "{activeMeeting.observations}"
                  </p>
                </div>
              )}

              <div className="border-t border-dashed border-white/10 pt-5 mt-6 flex justify-between gap-6">
                <div className="text-center font-sans shrink-0">
                  <p className="text-[9px] text-slate-500 font-extrabold uppercase tracking-wider">Le Secrétaire Légistique</p>
                  <p className="text-xs font-bold text-slate-300 mt-5 font-serif">M. Bakolo Jean</p>
                  <div className="inline-block mt-2 px-2 py-0.5 bg-blue-500/10 border border-blue-500/30 rounded text-[8px] text-blue-400 uppercase font-mono font-bold">
                    Visé permanent
                  </div>
                </div>

                <div className="text-center font-sans shrink-0">
                  <p className="text-[9px] text-slate-500 font-extrabold uppercase tracking-wider">Le Rapporteur CTM du scrutin</p>
                  <p className="text-xs font-bold text-slate-300 mt-5 font-serif">Ir. Sylvain Lukusa</p>
                  <div className="inline-block mt-2 px-2 py-0.5 bg-blue-500/10 border border-blue-500/30 rounded text-[8px] text-blue-400 uppercase font-mono font-bold">
                    Ordre ONIC Certifié
                  </div>
                </div>

                <div className="text-center font-sans shrink-0">
                  <p className="text-[9px] text-slate-500 font-extrabold uppercase tracking-wider">Le Président de Séance scientifique</p>
                  <p className="text-xs font-bold text-slate-300 mt-5 font-serif">Prof. Masamba Édouard</p>
                  <div className="inline-block mt-2 px-2 py-0.5 bg-purple-500/10 border border-purple-500/30 rounded text-[8px] text-purple-400 uppercase font-mono font-bold">
                    Signature Électronique
                  </div>
                </div>
              </div>

            </div>

            {/* Footer buttons actions with PDF mockup download simulation */}
            <div className="bg-[#050609] p-4.5 border-t border-white/10 flex justify-between gap-3 text-xs">
              <button
                type="button"
                onClick={() => {
                  triggerNotification("Téléchargement du PDF de Procès-Verbal entamé pour signature physique !", "success");
                  setTimeout(() => {
                    alert(`Téléchargement simulé réussi !\nFichier: PV_CNETP_${activeMeeting.id.toUpperCase()}_AUTHENTIFIE.pdf\nTaille: 142 KB\nSignature MD5: b58e390c29f4b9340986`);
                  }, 600);
                }}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-black font-extrabold rounded-lg flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <Download className="h-4 w-4" />
                Télécharger PDF Signé
              </button>

              <button
                onClick={() => setIsPvModalOpen(false)}
                className="px-4 py-2 bg-white/10 hover:bg-white/15 text-white font-bold rounded-lg transition-colors cursor-pointer"
              >
                Fermer l'Aperçu Officiel
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
