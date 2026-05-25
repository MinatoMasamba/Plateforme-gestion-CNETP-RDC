import React, { useState, useEffect } from "react";
import { 
  Save, RotateCcw, Sparkles, Loader, AlertCircle, Check, X, ShieldAlert, 
  Paperclip, Folder, FolderOpen, Video, Trash2, Calendar, FileText, ExternalLink, Plus, Info, CheckCircle,
  ChevronDown, ChevronUp, Share2, MessageSquare, Maximize2, Minimize2, ThumbsUp, ThumbsDown, Minus, Vote, Award, ShieldCheck, Eye, Users
} from "lucide-react";
import { Document, Collaborator, ChatContact } from "../types";
import CtmWorkingGroupsModal from "./CtmWorkingGroupsModal";

interface EditorAreaProps {
  document: Document;
  activeCollaborator: Collaborator;
  onSave: (content: string, comment: string) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  onUpdateDocument?: (updated: Document) => void;
  // Chat messaging integration
  chatContacts: ChatContact[];
  onShareClause: (recipientId: string, clauseCode: string, excerpt: string) => void;
  isDarkMode?: boolean;
  documentVotes?: Record<string, "pour" | "contre" | "abstention">;
  onCastVote?: (choice: "pour" | "contre" | "abstention") => void;
  experts?: any[];
}

export default function EditorArea({
  document,
  activeCollaborator,
  onSave,
  onCancel,
  isSaving,
  onUpdateDocument,
  chatContacts,
  onShareClause,
  isDarkMode = true,
  documentVotes = {},
  onCastVote,
  experts = []
}: EditorAreaProps) {
  // Local state for the editable content
  const [editorText, setEditorText] = useState(document.content);
  // Local state for the edit comment
  const [editComment, setEditComment] = useState("");
  const [isCtmModalOpen, setIsCtmModalOpen] = useState(false);

  // Local state for Chat/Clause Sharing
  const [selectedRecipientId, setSelectedRecipientId] = useState("");
  const [selectedExcerpt, setSelectedExcerpt] = useState("");
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  
  // Set default recipient when chatContacts load
  useEffect(() => {
    if (chatContacts && chatContacts.length > 0 && !selectedRecipientId) {
      setSelectedRecipientId(chatContacts[0].id);
    }
  }, [chatContacts]);
  
  // AI assistant simulation or generation state
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<{ suggestedText: string; explanation: string } | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [isAiExpanded, setIsAiExpanded] = useState(false);

  // Cloud integrations & Ancillary references state
  const [driveUrl, setDriveUrl] = useState(document.driveFolderUrl || "");
  const [meetUrl, setMeetUrl] = useState(document.meetMeetingUrl || "");
  const [isCloudSaving, setIsCloudSaving] = useState(false);
  const [cloudMessage, setCloudMessage] = useState<string | null>(null);

  // New ancillary file upload state
  const [newRefName, setNewRefName] = useState("");
  const [newRefType, setNewRefType] = useState("Rapport Technique");
  const [newRefDesc, setNewRefDesc] = useState("");
  const [newRefSize, setNewRefSize] = useState("1.8 MB");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  // Toggle for collapsible cloud portals and ancillary documents section
  const [isRessourcesExpanded, setIsRessourcesExpanded] = useState(false);

  // Sync editor content with document changes
  useEffect(() => {
    setEditorText(document.content);
    setEditComment("");
    setAiSuggestion(null);
    setAiError(null);
    setDriveUrl(document.driveFolderUrl || "");
    setMeetUrl(document.meetMeetingUrl || "");
    setCloudMessage(null);
    setUploadMessage(null);
    setSelectedExcerpt("");
    setShareFeedback(null);
  }, [document]);

  const handleShareSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecipientId) return;

    // Prefill excerpt with current doc overview if empty
    const textToShare = selectedExcerpt.trim() || `Projet de Norme ${document.code} - Clause en cours de modification par le comité.`;
    
    onShareClause(selectedRecipientId, document.code, textToShare);
    
    // UI Feedback
    const recipientName = chatContacts.find(c => c.id === selectedRecipientId)?.name || "l'expert";
    setShareFeedback(`🚀 Clause transmise cryptée à ${recipientName} ! Messagerie ouverte.`);
    setTimeout(() => {
      setShareFeedback(null);
    }, 4500);
  };

  // Handler to save Google Drive + Google Meet integration
  const handleSaveCloudIntegrations = async () => {
    setIsCloudSaving(true);
    setCloudMessage(null);
    try {
      const response = await fetch(`/api/documents/${document.id}/drive-meet`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ driveFolderUrl: driveUrl, meetMeetingUrl: meetUrl }),
      });
      if (!response.ok) throw new Error("Échec de mise à jour");
      const updatedDoc = await response.json();
      if (onUpdateDocument) {
        onUpdateDocument(updatedDoc);
      }
      setCloudMessage("Liens Google Drive & Meet mis à jour et classés avec succès !");
      setTimeout(() => setCloudMessage(null), 4000);
    } catch (err: any) {
      setCloudMessage("Une erreur est survenue lors de l'enregistrement de la classification.");
    } finally {
      setIsCloudSaving(false);
    }
  };

  // Handler to simulated upload helper
  const handleAddReference = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRefName) return;
    setIsUploading(true);
    setUploadMessage(null);

    try {
      const response = await fetch(`/api/documents/${document.id}/references`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newRefName,
          type: newRefType,
          description: newRefDesc,
          size: newRefSize
        }),
      });

      if (!response.ok) throw new Error("Échec d'attachement du document");
      const updatedDoc = await response.json();
      if (onUpdateDocument) {
        onUpdateDocument(updatedDoc);
      }
      
      setNewRefName("");
      setNewRefDesc("");
      setUploadMessage("Fichier de référence indexé et rattaché avec succès !");
      setTimeout(() => setUploadMessage(null), 4000);
    } catch (err: any) {
      setUploadMessage("Échec de l'indexation de la pièce jointe.");
    } finally {
      setIsUploading(false);
    }
  };

  // Handle local text changes
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditorText(e.target.value);
  };

  // Check if content is actually modified from original
  const isModified = editorText !== document.content;

  // Trigger Save Version action
  const handleSaveClick = async () => {
    if (!editorText.trim()) return;
    const commentToSubmit = editComment.trim() || "Mise à jour rapide du document";
    await onSave(editorText, commentToSubmit);
    setEditComment(""); // Reset comment
  };

  // Trigger AI advice call
  const handleAiAdvice = async () => {
    setIsAiLoading(true);
    setAiError(null);
    setAiSuggestion(null);

    try {
      const response = await fetch(`/api/documents/${document.id}/ai-review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: editorText }),
      });

      if (!response.ok) {
        throw new Error("Échec d'analyse par l'IA");
      }

      const data = await response.json();
      setAiSuggestion(data);
      setIsAiExpanded(true);
    } catch (err: any) {
      setAiError(err.message || "Impossible de contacter l'assistant réglementaire.");
    } finally {
      setIsAiLoading(false);
    }
  };

  // Apply AI's suggested rewrite
  const applyAiSuggestion = () => {
    if (aiSuggestion) {
      setEditorText(aiSuggestion.suggestedText);
      setEditComment("Réduction et corrections réglementaires appliquées par l'Assistant IA");
      setAiSuggestion(null);
    }
  };

  const displayCtm = document.ctm || (
    document.category === "Qualité" 
      ? "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale"
      : document.category === "Sécurité"
        ? "CTM 3 – Bâtiment, Urbanisme et Transition Numérique"
        : "CTM 1 – Géotechnique et Risques Naturels"
  );

  const isLightMode = !isDarkMode;

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-transparent flex flex-col gap-6">
      {/* Document Header block */}
      <div className={`border-b pb-5 ${isLightMode ? "border-slate-250" : "border-white/10"}`}>
        <div className="flex items-start justify-between gap-4 flex-col md:flex-row">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className={`font-mono text-xs px-2.5 py-0.5 rounded font-bold border ${isLightMode ? "text-blue-700 bg-blue-50 border-blue-200" : "text-blue-400 bg-blue-500/10 border-blue-500/20"}`}>
                {document.code}
              </span>
              <span className={`text-xs font-medium ${isLightMode ? "text-slate-500" : "text-slate-450"}`}>• Dernière modification le {new Date(document.updatedAt).toLocaleDateString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span>
            </div>
            <h2 className={`text-xl font-bold font-sans tracking-tight ${isLightMode ? "text-slate-900" : "text-white"}`}>
              {document.title}
            </h2>
            <p className={`${isLightMode ? "text-slate-600" : "text-slate-400"} text-xs mt-1.5 max-w-3xl leading-relaxed`}>
              {document.description}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            {/* Clickable CTM Section */}
            <button
              id="editor-ctm-button"
              type="button"
              onClick={() => setIsCtmModalOpen(true)}
              className={`border rounded-xl p-3 text-left transition-all duration-250 cursor-pointer shadow-xs group max-w-[210px] ${
                isLightMode 
                  ? "bg-blue-50 border-blue-300 hover:bg-blue-100/80 text-blue-800" 
                  : "bg-blue-500/5 border-blue-500/25 hover:bg-blue-500/15 text-blue-400"
              }`}
              title="Cliquer pour afficher tous les groupes de travail de cette commission"
            >
              <span className={`text-[9px] block font-extrabold uppercase tracking-wider ${
                isLightMode ? "text-blue-700" : "text-blue-500 group-hover:text-blue-400"
              }`}>
                Sous-Commission (CTM)
              </span>
              <span className={`text-[11px] font-extrabold block mt-0.5 truncate ${
                isLightMode ? "text-slate-900" : "text-slate-100"
              }`}>
                {displayCtm}
              </span>
              <span className={`text-[9px] block mt-1 underline decoration-dotted font-bold uppercase tracking-wider ${
                isLightMode ? "text-blue-600" : "text-slate-450 group-hover:text-slate-300"
              }`}>
                Voir Groupes (WGs) &rarr;
              </span>
            </button>

            {/* Éditeur Actif */}
            <div className={`border rounded-xl p-3 text-right hidden sm:block ${
              isLightMode ? "bg-slate-50 border-slate-200 text-slate-800" : "bg-white/[0.02] border-white/10 text-slate-200"
            }`}>
              <span className="text-[9.5px] text-slate-500 block font-bold uppercase tracking-wider">Éditeur Actif</span>
              <span className={`text-xs font-bold block mt-0.5 ${
                isLightMode ? "text-slate-900" : "text-slate-200"
              }`}>
                {activeCollaborator.name}
              </span>
              <span className="text-[9.5px] text-slate-500 block">{activeCollaborator.role}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Editor Main block */}
        <div className="lg:col-span-2 space-y-4">
          <div className={`border rounded-xl overflow-hidden transition-all shadow-md focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500/50 ${
            isLightMode 
              ? "border-slate-200 bg-white" 
              : "border-white/10 bg-black/40 shadow-[0_0_20px_rgba(0,0,0,0.3)]"
          }`}>
            {/* Editor toolbar simulation */}
            <div className={`border-b px-4 py-2.5 flex items-center justify-between text-xs ${
              isLightMode ? "bg-slate-50 border-slate-200 text-slate-505" : "bg-black/30 border-white/10 text-slate-500"
            }`}>
              <span className={`font-bold text-[10.5px] uppercase tracking-wider ${isLightMode ? "text-slate-700" : "text-slate-400"}`}>
                FORMAT : TEXTE BRUT / CLAUSES ISO
              </span>
              <span className={`font-mono text-[10px] ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>
                {editorText.length} caractères • {editorText.split(/\s+/).filter(Boolean).length} mots
              </span>
            </div>

            <textarea
              id="editor-textarea"
              value={editorText}
              onChange={handleTextChange}
              onSelect={(e) => {
                const target = e.target as HTMLTextAreaElement;
                const start = target.selectionStart;
                const end = target.selectionEnd;
                if (start !== end) {
                  const selectedText = target.value.substring(start, end);
                  setSelectedExcerpt(selectedText);
                }
              }}
              placeholder="Écrivez le standard ici..."
              className={`w-full h-96 p-5 text-sm focus:outline-hidden leading-relaxed resize-none font-sans bg-transparent ${
                isLightMode ? "text-slate-900 placeholder-slate-400" : "text-slate-200 placeholder-slate-500"
              }`}
            />
          </div>

          {/* SCRUTIN & VOTE DE CET AMENDEMENT/NORME (Expert Voting details requested) */}
          {(() => {
            const totalVotes = Object.keys(documentVotes).length;
            const pourVotes = Object.values(documentVotes).filter(v => v === "pour").length;
            const contreVotes = Object.values(documentVotes).filter(v => v === "contre").length;
            const abstentionVotes = Object.values(documentVotes).filter(v => v === "abstention").length;
            const consensusRate = totalVotes > 0 ? Math.round((pourVotes / totalVotes) * 100) : 0;
            
            const activeExpert = experts.find(e => e.email === activeCollaborator?.email) || { id: "exp-1" };
            const expertId = activeExpert.id;
            const myVote = documentVotes[expertId];

            return (
              <div className={`border rounded-xl p-5 space-y-4 shadow-sm transition-all ${
                isLightMode 
                  ? "bg-slate-50 border-slate-200 text-slate-800" 
                  : "bg-white/[0.02] border-white/10 text-white"
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg shrink-0 ${
                      isLightMode ? "bg-blue-50 text-blue-800 border border-blue-200" : "bg-blue-500/10 text-blue-400 border border-blue-500/10"
                    }`}>
                      <Vote className="h-4.5 w-4.5 animate-pulse" />
                    </div>
                    <div>
                      <h3 className={`text-xs font-bold uppercase tracking-wider ${isLightMode ? "text-slate-800" : "text-slate-200"}`}>
                        Scrutin & Évaluation Thématique
                      </h3>
                      <p className="text-[10px] text-slate-500 mt-0.5 font-medium">
                        Co-gouvernance scientifique (Consensus minimum requis : 75%)
                      </p>
                    </div>
                  </div>

                  {/* Dynamic Consensus Score */}
                  <div className="text-right">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-slate-500 block">
                      Taux de Validation
                    </span>
                    <span className={`text-sm font-black font-mono block ${
                      consensusRate >= 75 ? "text-blue-500" : "text-amber-500"
                    }`}>
                      {consensusRate}%
                    </span>
                  </div>
                </div>

                {/* Combined Progress bar indicator */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between text-[10px] font-mono font-bold text-slate-500">
                    <span className="text-blue-500">POUR ({pourVotes})</span>
                    <span className="text-rose-500">CONTRE ({contreVotes})</span>
                    <span className="text-slate-400">ABS ({abstentionVotes})</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden flex bg-slate-300/10 border border-slate-300/5">
                    {totalVotes === 0 ? (
                      <div className="w-full h-full bg-slate-400/20"></div>
                    ) : (
                      <>
                        <div style={{ width: `${(pourVotes / totalVotes) * 100}%` }} className="bg-blue-500 h-full transition-all duration-300"></div>
                        <div style={{ width: `${(contreVotes / totalVotes) * 100}%` }} className="bg-rose-500 h-full transition-all duration-300"></div>
                        <div style={{ width: `${(abstentionVotes / totalVotes) * 100}%` }} className="bg-slate-400 h-full transition-all duration-300"></div>
                      </>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between pt-0.5">
                    <span className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-slate-400" />
                      {totalVotes} {totalVotes > 1 ? "experts ont émargé" : "expert a émargé"} l'avis
                    </span>

                    {consensusRate >= 75 ? (
                      <span className="text-[10.5px] font-black text-blue-500 flex items-center gap-1 uppercase tracking-tight">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Consensus Atteint
                      </span>
                    ) : (
                      <span className="text-[10px] font-extrabold text-amber-500 flex items-center gap-1 uppercase tracking-tight animate-pulse">
                        <Info className="h-3.5 w-3.5" />
                        Avis Partiel
                      </span>
                    )}
                  </div>
                </div>

                {/* Direct Expert Ballot buttons */}
                <div className={`p-4 rounded-xl border ${
                  isLightMode ? "bg-white border-slate-205" : "bg-black/30 border-white/5"
                } space-y-3`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className={`text-[11px] font-bold uppercase tracking-wider ${isLightMode ? "text-slate-800" : "text-slate-350"}`}>
                        Exprimer votre voix d'expert permanent
                      </h4>
                      <p className="text-[10px] text-slate-500">
                        Votre identité d'élection : <strong>{activeCollaborator?.name || "Prof. Masamba Édouard"}</strong>
                      </p>
                    </div>

                    {myVote ? (
                      <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded border ${
                        myVote === "pour" 
                          ? "bg-blue-500/10 text-blue-500 border-blue-500/20" 
                          : myVote === "contre"
                            ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                            : "bg-slate-500/10 text-slate-400 border-slate-500/10"
                      }`}>
                        VOTÉ : {myVote}
                      </span>
                    ) : (
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20 animate-pulse">
                        Non voté
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-0.5">
                    <button
                      type="button"
                      id="norm-vote-pour-btn"
                      onClick={() => onCastVote?.("pour")}
                      className={`py-2 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all outline-hidden border cursor-pointer ${
                        myVote === "pour"
                          ? isLightMode
                            ? "bg-blue-600 border-blue-600 text-white font-extrabold shadow-[0_0_12px_rgba(37,99,235,0.3)]"
                            : "bg-blue-555 text-black bg-blue-500 border-blue-400 font-extrabold shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                          : isLightMode
                            ? "bg-blue-50 text-blue-800 border-blue-200 hover:bg-blue-100"
                            : "bg-blue-500/5 text-blue-400 border-blue-500/10 hover:bg-blue-500/15"
                      }`}
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                      POUR
                    </button>

                    <button
                      type="button"
                      id="norm-vote-contre-btn"
                      onClick={() => onCastVote?.("contre")}
                      className={`py-2 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all outline-hidden border cursor-pointer ${
                        myVote === "contre"
                          ? "bg-rose-555 text-white bg-rose-500 border-rose-400 font-extrabold shadow-[0_0_12px_rgba(239,68,68,0.3)]"
                          : isLightMode
                            ? "bg-rose-50 text-rose-800 border-rose-200 hover:bg-rose-100"
                            : "bg-rose-500/5 text-rose-400 border-rose-500/10 hover:bg-rose-500/15"
                      }`}
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                      CONTRE
                    </button>

                    <button
                      type="button"
                      id="norm-vote-abstention-btn"
                      onClick={() => onCastVote?.("abstention")}
                      className={`py-2 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 transition-all outline-hidden border cursor-pointer ${
                        myVote === "abstention"
                          ? "bg-slate-450 text-white bg-slate-500 border-slate-400 font-extrabold"
                          : isLightMode
                            ? "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200"
                            : "bg-white/5 text-slate-300 border-white/5 hover:bg-white/10"
                      }`}
                    >
                      <Minus className="h-3.5 w-3.5" />
                      ABS.
                    </button>
                  </div>
                </div>

                {/* Collapsible list table of voters */}
                <div className="space-y-1.5 pt-1.5">
                  <span className="text-[9.5px] uppercase font-bold tracking-wider text-slate-500 block">
                    Registre interactif d'émargement réglementaire :
                  </span>
                  <div className={`rounded-xl border divide-y overflow-hidden max-h-36 overflow-y-auto ${
                    isLightMode ? "bg-[#ffffff]/60 border-slate-200 divide-slate-150" : "bg-black/25 border-white/5 divide-white/5"
                  }`}>
                    {experts.map((exp) => {
                      const expertVote = documentVotes[exp.id];
                      return (
                        <div key={`exp-voting-${exp.id}`} className="p-2 flex items-center justify-between text-[11px] hover:bg-blue-500/[0.03]">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className={`h-5 w-5 rounded-full flex items-center justify-center font-bold text-[9px] shrink-0 ${
                              exp.id === "exp-1" ? "bg-blue-500 text-black" : "bg-slate-500/20 text-slate-400"
                            }`}>
                              {exp.name.split(" ").pop()?.substring(0, 2).toUpperCase() || "EX"}
                            </div>
                            <div className="min-w-0">
                              <p className={`font-semibold truncate max-w-[170px] ${isLightMode ? "text-slate-800" : "text-slate-200"}`}>
                                {exp.name} {exp.id === "exp-1" && <span className="text-[10px] text-slate-500 font-normal">(Vous)</span>}
                              </p>
                              <p className="text-[9px] text-slate-500 truncate text-left">{exp.structure || exp.role}</p>
                            </div>
                          </div>

                          <div className="shrink-0 font-mono text-[9.5px]">
                            {expertVote === "pour" ? (
                              <span className="text-blue-500 font-bold bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded">
                                POUR
                              </span>
                            ) : expertVote === "contre" ? (
                              <span className="text-rose-500 font-bold bg-rose-500/10 border border-rose-500/20 px-1.5 py-0.5 rounded">
                                CONTRE
                              </span>
                            ) : expertVote === "abstention" ? (
                              <span className="text-slate-400 font-bold bg-slate-500/10 border border-slate-500/15 px-1.5 py-0.5 rounded">
                                ABS.
                              </span>
                            ) : (
                              <span className="text-slate-500 font-medium italic">En attente</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Change log input required before saving */}
          <div className={`border rounded-xl p-5 space-y-3.5 ${
            isLightMode ? "bg-slate-50 border-slate-200 text-slate-800" : "bg-white/[0.02] border-white/10 text-white"
          }`}>
            <div>
              <label htmlFor="edit-comment-input" className={`block text-xs font-semibold uppercase tracking-wider ${
                isLightMode ? "text-slate-700" : "text-slate-400"
              }`}>
                Journal des versions / Commentaire d'édition <span className="text-blue-400">*</span>
              </label>
              <p className="text-[11px] text-slate-550 mt-0.5">Pour conserver un historique exploitable, détaillez brièvement votre modification.</p>
            </div>
            <input
              id="edit-comment-input"
              type="text"
              value={editComment}
              onChange={(e) => setEditComment(e.target.value)}
              placeholder="Ex: Mise en conformité de la note 2, correction des fautes d'orthographe..."
              className={`w-full text-xs px-3 py-2.5 rounded-lg border focus:outline-hidden focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500/50 transition-all font-medium ${
                isLightMode 
                  ? "bg-white border-slate-300 text-slate-900 placeholder-slate-400" 
                  : "bg-black/40 border-white/10 text-white placeholder-slate-700"
              }`}
            />

            {/* Editor Action buttons */}
            <div className="flex items-center justify-between pt-1">
              <button
                id="cancel-edit-btn"
                onClick={onCancel}
                disabled={!isModified && !editComment}
                className={`px-3.5 py-1.5 text-xs rounded-lg font-bold transition-all flex items-center gap-1.5 ${
                  isLightMode 
                    ? "hover:bg-slate-200/50 text-slate-600 disabled:opacity-30" 
                    : "text-slate-450 hover:text-white hover:bg-white/5 disabled:opacity-30"
                }`}
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Réinitialiser
              </button>

              <div className="flex items-center gap-2">
                <button
                  id="save-edit-btn"
                  onClick={handleSaveClick}
                  disabled={isSaving || !editorText.trim() || !editComment.trim()}
                  className={`px-4.5 py-2.5 text-xs font-bold rounded-lg disabled:opacity-40 transition-all flex items-center gap-1.5 shadow-sm cursor-pointer ${
                    isLightMode
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-blue-500 text-black hover:bg-blue-400"
                  }`}
                >
                  {isSaving ? (
                    <Loader className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5" />
                  )}
                  Sauvegarder la version
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* AI Compliance recommendation panel */}
        <div className="space-y-4">
          <div className={`border rounded-xl p-5 space-y-4 shadow-sm transition-all ${
            isLightMode 
              ? "bg-blue-50/50 border-blue-200 text-slate-800 animate-fadeIn" 
              : "border border-indigo-500/20 bg-indigo-950/20"
          }`}>
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${
                isLightMode ? "bg-blue-100 text-blue-800" : "bg-indigo-500/10 text-indigo-400"
              }`}>
                <Sparkles className="h-4.5 w-4.5" />
              </div>
              <div>
                <h3 className={`text-xs font-bold tracking-wider uppercase ${isLightMode ? "text-blue-950" : "text-slate-350"}`}>
                  Conseil Réglementaire IA
                </h3>
                <p className={`text-[11px] mt-1.5 leading-relaxed ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>
                  L'IA intégrée peut relire votre rédaction, l'évaluer par rapport aux exigences d'un audit de certification, corriger l'orthographe et proposer un style plus rigoureux.
                </p>
              </div>
            </div>

            <button
              id="ai-advice-btn"
              onClick={handleAiAdvice}
              disabled={isAiLoading || !editorText.trim()}
              className={`w-full text-xs font-bold py-2.5 rounded-lg disabled:opacity-50 transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer border ${
                isLightMode
                  ? "bg-blue-600 hover:bg-blue-700 text-white border-blue-700" 
                  : "bg-indigo-650 hover:bg-indigo-600 text-white border-indigo-500/30"
              }`}
            >
              {isAiLoading ? (
                <>
                  <Loader className="h-3.5 w-3.5 animate-spin" />
                  Analyse de la clause en cours...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  Analyser & optimiser le texte
                </>
              )}
            </button>

            {aiError && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg flex gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                <span>{aiError}</span>
              </div>
            )}
          </div>

          {/* AI suggestion Comparison panel */}
          {aiSuggestion && (
            <div 
              className={`border border-blue-500/20 bg-blue-950/15 rounded-xl transition-all duration-300 animate-fadeIn ${isAiExpanded ? 'p-4.5 space-y-4 shadow-sm' : 'hover:bg-blue-500/10'}`}
            >
              <div 
                className={`flex justify-between items-center cursor-pointer ${!isAiExpanded ? 'p-3' : ''}`}
                onClick={() => setIsAiExpanded(!isAiExpanded)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[9px] uppercase tracking-wider bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded font-bold border border-blue-500/20">
                    Proposition de l'IA
                  </span>
                  {!isAiExpanded && <span className="text-xs text-slate-400">Cliquez pour lire et appliquer</span>}
                </div>
                <button 
                  className="px-2 py-1 flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider hover:bg-blue-500/20 rounded-md text-blue-500 transition-colors"
                >
                  {isAiExpanded ? (
                    <>Fermer <ChevronUp className="h-3.5 w-3.5" /></>
                  ) : (
                    <>Ouvrir <ChevronDown className="h-3.5 w-3.5" /></>
                  )}
                </button>
              </div>
              
              {isAiExpanded && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="space-y-1">
                    <p className="text-xs text-slate-300 font-medium leading-relaxed mt-2.5 p-3 bg-black/30 border border-blue-500/20 rounded-lg">
                      {aiSuggestion.explanation}
                    </p>
                  </div>

                  {/* Collapsible/Scrollable rewrite preview */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase block">Texte de substitution proposé (modifiable) :</span>
                    <textarea
                      value={aiSuggestion.suggestedText}
                      onChange={(e) => setAiSuggestion({ ...aiSuggestion, suggestedText: e.target.value })}
                      className="w-full text-xs text-slate-300 bg-black/45 border border-white/10 p-4 rounded-lg leading-relaxed font-mono resize-y min-h-[160px] focus:outline-hidden focus:border-blue-500/50"
                    />
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button
                      id="apply-ai-btn"
                      onClick={() => {
                        applyAiSuggestion();
                        setIsAiExpanded(false);
                      }}
                      className="flex-1 text-xs font-bold py-2 bg-blue-500 text-black hover:bg-blue-400 rounded-lg transition-all flex items-center justify-center gap-1.5 shadow-xs cursor-pointer"
                    >
                      <Check className="h-3.5 w-3.5" />
                      Appliquer la révision
                    </button>
                    <button
                      id="dismiss-ai-btn"
                      onClick={() => {
                        setAiSuggestion(null);
                        setIsAiExpanded(false);
                      }}
                      className="px-3 text-xs font-bold py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg transition-all flex items-center justify-center gap-1 cursor-pointer"
                    >
                      <X className="h-3.5 w-3.5" />
                      Ignorer
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECURED CLAUSE CHAT SHARING PORTAL */}
          <div className={`border rounded-xl p-5 space-y-4 shadow-sm animate-fadeIn ${isLightMode ? "border-blue-200 bg-blue-50/50" : "border-blue-500/20 bg-blue-950/10"}`}>
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg shrink-0 ${isLightMode ? "bg-blue-100 text-blue-600" : "bg-blue-500/10 text-blue-400"}`}>
                <Share2 className="h-4.5 w-4.5" />
              </div>
              <div>
                <h3 className={`text-xs font-bold tracking-wider uppercase ${isLightMode ? "text-slate-800" : "text-slate-350"}`}>Partager & Débattre</h3>
                <p className={`text-[11px] mt-1.5 leading-relaxed ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>
                  Discutez d'un extrait de cette norme dans un salon de chat sécurisé.
                  Surlignez du texte à gauche pour préremplir l'extrait !
                </p>
              </div>
            </div>

            <form onSubmit={handleShareSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className={`text-[9.5px] uppercase font-bold block ${isLightMode ? "text-slate-600" : "text-slate-500"}`}>Extrait de clause sélectionné :</label>
                <textarea
                  id="share-excerpt-input"
                  value={selectedExcerpt}
                  onChange={(e) => setSelectedExcerpt(e.target.value)}
                  placeholder="Sélectionnez du texte dans l'éditeur ci-contre ou tapez un commentaire..."
                  className={`w-full h-24 p-2.5 text-xs rounded-lg focus:outline-hidden resize-none font-sans leading-normal transition-colors ${
                    isLightMode 
                      ? "bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:border-blue-500" 
                      : "bg-[#020204]/80 border border-white/10 text-slate-200 placeholder-slate-705 focus:border-blue-500/30"
                  }`}
                />
              </div>

              <div className="space-y-1">
                <label className={`text-[9.5px] uppercase font-bold block ${isLightMode ? "text-slate-600" : "text-slate-500"}`}>Expert destinataire (CNETP) :</label>
                <select
                  id="share-recipient-select"
                  value={selectedRecipientId}
                  onChange={(e) => setSelectedRecipientId(e.target.value)}
                  className={`w-full text-xs px-2.5 py-2.5 rounded-lg border font-semibold transition-colors ${
                    isLightMode
                      ? "bg-white border-slate-300 text-slate-800"
                      : "bg-black/55 border-white/10 text-slate-200"
                  }`}
                >
                  <option value="" disabled>-- Sélectionner l'expert --</option>
                  {chatContacts.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.structure ? c.structure.substring(0, 18) : c.role}...)
                    </option>
                  ))}
                </select>
              </div>

              {shareFeedback && (
                <div className={`text-[10.5px] p-2.5 rounded-lg font-semibold border-l-2 shadow-inner ${
                  isLightMode
                    ? "text-blue-700 bg-blue-100/50 border-y border-r border-y-blue-200 border-r-blue-200 border-l-blue-600"
                    : "text-blue-400 bg-blue-500/10 border-y border-r border-y-blue-500/20 border-r-blue-500/20 border-l-blue-500"
                }`}>
                  {shareFeedback}
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedRecipientId}
                className={`w-full text-xs font-bold py-2.5 rounded-lg transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-40 ${
                  isLightMode
                    ? "bg-blue-600 hover:bg-blue-700 text-white"
                    : "bg-blue-500 hover:bg-blue-400 text-black"
                }`}
              >
                <MessageSquare className="h-3.5 w-3.5" />
                Partager à l'expert & Ouvrir le Chat
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Workspace Cloud Portals & Ancillary Documents Board */}
      <div className={`border-t pt-6 mt-4 space-y-6 ${isLightMode ? "border-slate-200" : "border-white/10"}`}>
        <div className={`flex items-center justify-between border-b pb-3 ${isLightMode ? "border-slate-200" : "border-white/5"}`}>
          <div>
            <h3 className={`text-sm font-bold uppercase tracking-wider flex items-center gap-2 ${isLightMode ? "text-slate-900" : "text-white"}`}>
              <FolderOpen className={`h-4 w-4 ${isLightMode ? "text-blue-600" : "text-blue-400"}`} />
              Ressources Connexes & Espace Collaboratif Cloud
            </h3>
            <p className={`text-xs mt-1 ${isLightMode ? "text-slate-600" : "text-slate-500"}`}>
              Gérez les rapports techniques, l'archivage classifié sur Google Drive, et planifiez les réunions de standardisation via Google Meet.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-[10px] font-mono px-2.5 py-1 rounded border uppercase hidden sm:inline-block ${
              isLightMode ? "text-blue-700 bg-blue-50 border-blue-200" : "text-blue-400/80 bg-blue-500/5 border-blue-500/20"
            }`}>
              ID: {document.id} • {document.code}
            </span>
            <button
              id="toggle-ressources-btn"
              onClick={() => setIsRessourcesExpanded(!isRessourcesExpanded)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5 cursor-pointer border ${
                isRessourcesExpanded 
                  ? isLightMode
                    ? "bg-blue-50 text-blue-700 border-blue-300 shadow-[0_4px_12px_rgba(37,99,235,0.15)]"
                    : "bg-blue-500/10 text-blue-400 border-blue-500/30 shadow-[0_4px_12px_rgba(16,185,129,0.15)]" 
                  : isLightMode
                    ? "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-900"
                    : "bg-white/5 text-slate-350 border-white/10 hover:bg-white/10 hover:text-white"
              }`}
            >
              {isRessourcesExpanded ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" />
                  Masquer
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" />
                  Dérouler / Afficher
                </>
              )}
            </button>
          </div>
        </div>

        {isRessourcesExpanded ? (
          <div className={`grid grid-cols-1 xl:grid-cols-2 gap-6 items-start animate-fadeIn ${isLightMode ? "" : ""}`}>
            {/* SECTION A: Google Cloud Platform integrations (Drive Folder + Google Meet Scheduling) */}
            <div className={`rounded-xl p-5 space-y-5 border transition-colors ${isLightMode ? "bg-slate-50 border-slate-200 shadow-sm" : "bg-white/[0.02] border-white/10"}`}>
              <div className="flex items-center gap-2">
                <span className={`p-1 px-2 text-[10px] uppercase font-mono font-bold rounded-md border ${isLightMode ? "bg-blue-50 text-blue-700 border-blue-200" : "bg-blue-500/10 text-blue-400 border-blue-500/20"}`}>
                  Liaisons Cloud RDC
                </span>
                <h4 className={`text-xs font-bold uppercase tracking-widest ${isLightMode ? "text-slate-800" : "text-slate-300"}`}>
                  Portail Co-gouvernance Drive & Meet
                </h4>
              </div>

              <p className={`text-[11px] leading-relaxed ${isLightMode ? "text-slate-600" : "text-slate-400"}`}>
                Pour faciliter l'accès vu le grand volume de normes, associez un dossier d'écriture <b>Google Drive</b> unique à cette norme. Planifiez des visioconférences <b>Google Meet</b> avec les comités techniques de validation (CNETP).
              </p>

              <div className="space-y-4">
                {/* Drive link configuration */}
                <div className="space-y-2">
                  <label className={`text-[11.5px] font-bold flex items-center gap-1.5 uppercase ${isLightMode ? "text-slate-700" : "text-slate-400"}`}>
                    <Folder className="h-4 w-4 text-amber-500 fill-amber-500/10" />
                    Dossier d'archivage Google Drive Classé
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={driveUrl}
                      onChange={(e) => setDriveUrl(e.target.value)}
                      placeholder="https://drive.google.com/drive/folders/..."
                      className={`flex-1 text-xs px-3 py-2 rounded-lg border focus:outline-hidden transition-colors ${
                        isLightMode
                          ? "bg-white border-slate-300 text-slate-800 focus:border-blue-500 placeholder-slate-400"
                          : "bg-black/40 border-white/10 text-slate-200 focus:border-blue-500/50"
                      }`}
                    />
                    {driveUrl && (
                      <a
                        href={driveUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`px-3 py-2 rounded-lg flex items-center justify-center transition-all border ${
                          isLightMode
                            ? "bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100"
                            : "bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20"
                        }`}
                        title="Ouvrir le dossier Drive"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                  <p className={`text-[10px] italic ${isLightMode ? "text-slate-500" : "text-slate-500"}`}>
                    Les documents de cette norme seront rangés dans ce répertoire cloud pour une récupération accélérée.
                  </p>
                </div>

                {/* Meet link configuration */}
                <div className="space-y-2">
                  <label className={`text-[11.5px] font-bold flex items-center gap-1.5 uppercase ${isLightMode ? "text-slate-700" : "text-slate-400"}`}>
                    <Video className={`h-4 w-4 ${isLightMode ? "text-blue-500" : "text-blue-500"}`} />
                    Lien de réunion Google Meet (Groupe de Travail / WG)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={meetUrl}
                      onChange={(e) => setMeetUrl(e.target.value)}
                      placeholder="https://meet.google.com/..."
                      className={`flex-1 text-xs px-3 py-2 rounded-lg border focus:outline-hidden transition-colors ${
                        isLightMode
                          ? "bg-white border-slate-300 text-slate-800 focus:border-blue-500 placeholder-slate-400"
                          : "bg-black/40 border-white/10 text-slate-200 focus:border-blue-500/50"
                      }`}
                    />
                    {meetUrl && (
                      <a
                        href={meetUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`px-3 py-2 rounded-lg flex items-center justify-center transition-all border ${
                          isLightMode
                            ? "bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100"
                            : "bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20"
                        }`}
                        title="Rejoindre l'appel Meet"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 italic">
                    Utilisé pour convoquer instantanément le comité technique d'évaluation (CTA).
                  </p>
                </div>

                {/* Action and feedback messaging */}
                <div className="flex items-center justify-between pt-2">
                  {cloudMessage ? (
                    <span className={`text-[11px] flex items-center gap-1.5 font-medium animate-fadeIn ${
                      isLightMode ? "text-blue-700" : "text-blue-400"
                    }`}>
                      <CheckCircle className="h-3.5 w-3.5 opacity-80" />
                      {cloudMessage}
                    </span>
                  ) : (
                    <span />
                  )}

                  <button
                    type="button"
                    onClick={handleSaveCloudIntegrations}
                    disabled={isCloudSaving}
                    className="px-4 py-2 text-xs font-bold rounded-lg bg-indigo-650 hover:bg-indigo-600 border border-indigo-500/30 text-white transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-55"
                  >
                    {isCloudSaving ? (
                      <Loader className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    Enregistrer les liens Cloud
                  </button>
                </div>
              </div>
            </div>

            {/* SECTION B: Ancillary documents and references upload & list */}
            <div className="space-y-4">
              {/* List block */}
              <div className={`rounded-xl p-5 space-y-4 border transition-colors ${isLightMode ? "bg-slate-50 border-slate-200 shadow-sm" : "bg-white/[0.02] border-white/10"}`}>
                <span className={`p-1 px-2 text-[10px] uppercase font-mono font-bold rounded-md border ${
                  isLightMode ? "bg-amber-100 text-amber-700 border-amber-200" : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                }`}>
                  Pièces jointes ({document.references?.length || 0})
                </span>

                <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                  {!document.references || document.references.length === 0 ? (
                    <div className={`p-6 border border-dashed rounded-xl text-center ${isLightMode ? "border-slate-300 text-slate-500" : "border-white/10 text-slate-500"}`}>
                      <Paperclip className={`h-5 w-5 mx-auto mb-1.5 ${isLightMode ? "text-slate-400" : "text-slate-650"}`} />
                      <p className="text-xs">Aucun document connexe n'est encore associé à cette norme.</p>
                      <p className="text-[10px] text-slate-600 mt-1">Utilisez l'indexeur ci-dessous pour ajouter des rapports d'essais ou des textes de lois.</p>
                    </div>
                  ) : (
                    document.references.map((item) => (
                      <div
                        key={item.id}
                        className="p-3 bg-black/40 border border-white/5 rounded-xl flex items-start justify-between gap-4 hover:border-white/10 transition-colors"
                      >
                        <div className="flex gap-2.5">
                          <div className="p-2 rounded bg-white/5 text-slate-400 shrink-0">
                            <FileText className="h-4 w-4" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-200 leading-tight">
                                {item.name}
                              </span>
                              <span className="text-[9px] font-mono bg-white/10 text-slate-350 px-1.5 py-0.5 rounded uppercase">
                                {item.type}
                              </span>
                            </div>
                            {item.description && (
                              <p className="text-[10.5px] text-slate-400 mt-0.5">
                                {item.description}
                              </p>
                            )}
                            <span className="text-[9.5px] text-slate-500 block mt-1">
                              Taille estimée : {item.size}
                            </span>
                          </div>
                        </div>

                        <a
                          href="#download"
                          onClick={(e) => {
                            e.preventDefault();
                            alert(`Téléchargement de "${item.name}" initié depuis le serveur cloud.`);
                          }}
                          className="text-[10px] text-indigo-400 hover:text-white hover:underline shrink-0 flex items-center gap-1 font-bold pt-1"
                        >
                          Télécharger
                        </a>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Simulated file upload form */}
              <form onSubmit={handleAddReference} className="bg-white/[0.02] border border-white/10 rounded-xl p-5 space-y-4">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1.5">
                  <Plus className="h-3.5 w-3.5 text-blue-400" />
                  Indexation d'une nouvelle pièce réglementaire
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Titre du document</label>
                    <input
                      type="text"
                      required
                      value={newRefName}
                      onChange={(e) => setNewRefName(e.target.value)}
                      placeholder="Ex: Rapport_Essais_Mechaniques_V2.pdf"
                      className="w-full text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/40 text-slate-200 placeholder-slate-700"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Typologie ou nature</label>
                    <select
                      value={newRefType}
                      onChange={(e) => setNewRefType(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/45 text-slate-200"
                    >
                      <option value="Rapport Technique">Rapport Technique / Contrôle</option>
                      <option value="Étude / Papier Scientifique">Étude / Papier Scientifique</option>
                      <option value="Réglementation Nationale">Réglementation Nationale</option>
                      <option value="Fiche Technique">Fiche Technique / Spécifications</option>
                      <option value="Autre Annexe">Autre Pièce Annexe</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Description / Commentaires</label>
                    <input
                      type="text"
                      value={newRefDesc}
                      onChange={(e) => setNewRefDesc(e.target.value)}
                      placeholder="Commentaires ou notes pour le comité d'évaluation..."
                      className="w-full text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/40 text-slate-200 placeholder-slate-700"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Taille du fichier simulée</label>
                    <select
                      value={newRefSize}
                      onChange={(e) => setNewRefSize(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/45 text-slate-200"
                    >
                      <option value="1.2 MB">1.2 MB</option>
                      <option value="2.4 MB">2.4 MB</option>
                      <option value="5.8 MB">5.8 MB</option>
                      <option value="12.4 MB">12.4 MB</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  {uploadMessage ? (
                    <span className="text-[11px] text-blue-400 flex items-center gap-1 font-medium">
                      <CheckCircle className="h-3.5 w-3.5" />
                      {uploadMessage}
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-550 flex items-center gap-1 font-medium">
                      <Info className="h-3 w-3" />
                      Formulaire d'enregistrement avec contrôle à la source
                    </span>
                  )}

                  <button
                    type="submit"
                    disabled={isUploading || !newRefName}
                    className="px-4 py-2 text-xs font-bold rounded-lg bg-blue-500 hover:bg-blue-400 text-black transition-all flex items-center gap-1 cursor-pointer disabled:opacity-50"
                  >
                    {isUploading ? (
                      <Loader className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Paperclip className="h-3.5 w-3.5" />
                    )}
                    Lier cette pièce adjointe
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          <div className="p-5 border border-dashed border-white/5 rounded-2xl bg-white/[0.01] text-center">
            <p className="text-xs text-slate-500">
              Le dossier d'archivage Google Drive, les réunions Google Meet, et les pieces jointes de cette norme ({document.references?.length || 0}) sont masqués.
            </p>
            <button
              onClick={() => setIsRessourcesExpanded(true)}
              className="mt-2 text-xs font-bold text-blue-400 hover:text-white transition-colors bg-blue-500/5 px-3 py-1.5 rounded-lg border border-blue-500/10 cursor-pointer"
            >
              Afficher/Dérouler le gestionnaire cloud
            </button>
          </div>
        )}
      </div>

      {/* CTM Working Groups Detailed Modal */}
      <CtmWorkingGroupsModal
        isOpen={isCtmModalOpen}
        onClose={() => setIsCtmModalOpen(false)}
        ctmName={displayCtm}
        isDarkMode={!isLightMode}
      />
    </div>
  );
}
