import React, { useState, useEffect } from "react";
import { 
  Save, RotateCcw, Sparkles, Loader, AlertCircle, Check, X, ShieldAlert, 
  Paperclip, Folder, FolderOpen, Video, Trash2, Calendar, FileText, ExternalLink, Plus, Info, CheckCircle,
  ChevronDown, ChevronUp, Share2, MessageSquare, Maximize2, Minimize2
} from "lucide-react";
import { Document, Collaborator, ChatContact } from "../types";

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
}: EditorAreaProps) {
  // Local state for the editable content
  const [editorText, setEditorText] = useState(document.content);
  // Local state for the edit comment
  const [editComment, setEditComment] = useState("");

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

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-transparent flex flex-col gap-6">
      {/* Document Header block */}
      <div className="border-b border-white/10 pb-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-mono text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded font-bold border border-emerald-500/20">
                {document.code}
              </span>
              <span className="text-xs text-slate-400 font-medium">• Dernière modification le {new Date(document.updatedAt).toLocaleDateString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span>
            </div>
            <h2 className="text-xl font-bold text-white font-sans tracking-tight">
              {document.title}
            </h2>
            <p className="text-slate-400 text-xs mt-1.5 max-w-3xl leading-relaxed">
              {document.description}
            </p>
          </div>

          <div className="bg-white/[0.02] border border-white/10 rounded-xl p-3 text-right shrink-0">
            <span className="text-[9.5px] text-slate-500 block font-bold uppercase tracking-wider">Éditeur Actif</span>
            <span className="text-xs font-bold text-slate-200 block mt-0.5">{activeCollaborator.name}</span>
            <span className="text-[9.5px] text-slate-500 block">{activeCollaborator.role}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Editor Main block */}
        <div className="lg:col-span-2 space-y-4">
          <div className="border border-white/10 bg-black/40 rounded-xl overflow-hidden shadow-[0_0_20px_rgba(0,0,0,0.3)] focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-500/50 transition-colors">
            {/* Editor toolbar simulation */}
            <div className="bg-black/30 border-b border-white/10 px-4 py-2.5 flex items-center justify-between text-xs text-slate-500">
              <span className="font-bold text-[10.5px] text-slate-400 uppercase tracking-wider">FORMAT : TEXTE BRUT / CLAUSES ISO</span>
              <span className="font-mono text-[10px] text-slate-400">
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
              className="w-full h-96 p-5 text-slate-200 bg-transparent text-sm focus:outline-hidden leading-relaxed resize-none font-sans"
            />
          </div>

          {/* Change log input required before saving */}
          <div className="bg-white/[0.02] border border-white/10 rounded-xl p-5 space-y-3.5">
            <div>
              <label htmlFor="edit-comment-input" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Journal des versions / Commentaire d'édition <span className="text-emerald-400">*</span>
              </label>
              <p className="text-[11px] text-slate-500 mt-0.5">Pour conserver un historique exploitable, détaillez brièvement votre modification.</p>
            </div>
            <input
              id="edit-comment-input"
              type="text"
              value={editComment}
              onChange={(e) => setEditComment(e.target.value)}
              placeholder="Ex: Mise en conformité de la note 2, correction des fautes d'orthographe..."
              className="w-full text-xs px-3 py-2.5 rounded-lg border border-white/10 bg-black/40 focus:outline-hidden focus:ring-2 focus:ring-emerald-500/10 focus:border-emerald-500/50 transition-all text-white font-medium placeholder-slate-700"
            />

            {/* Editor Action buttons */}
            <div className="flex items-center justify-between pt-1">
              <button
                id="cancel-edit-btn"
                onClick={onCancel}
                disabled={!isModified && !editComment}
                className="px-3.5 py-1.5 text-xs text-slate-450 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent rounded-lg font-bold transition-all flex items-center gap-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Réinitialiser
              </button>

              <div className="flex items-center gap-2">
                <button
                  id="save-edit-btn"
                  onClick={handleSaveClick}
                  disabled={isSaving || !editorText.trim() || !editComment.trim()}
                  className="px-4.5 py-2.5 text-xs font-bold rounded-lg bg-emerald-500 text-black hover:bg-emerald-400 disabled:opacity-40 transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
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
          <div className="border border-indigo-500/20 bg-indigo-950/20 rounded-xl p-5 space-y-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0">
                <Sparkles className="h-4.5 w-4.5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-350 tracking-wider uppercase">Conseil Réglementaire IA</h3>
                <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                  L'IA intégrée peut relire votre rédaction, l'évaluer par rapport aux exigences d'un audit de certification, corriger l'orthographe et proposer un style plus rigoureux.
                </p>
              </div>
            </div>

            <button
              id="ai-advice-btn"
              onClick={handleAiAdvice}
              disabled={isAiLoading || !editorText.trim()}
              className="w-full text-xs font-bold py-2.5 bg-indigo-650 hover:bg-indigo-600 text-white rounded-lg disabled:opacity-50 transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer border border-indigo-500/30"
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
              className={`border border-emerald-500/20 bg-emerald-950/15 rounded-xl transition-all duration-300 animate-fadeIn ${isAiExpanded ? 'p-4.5 space-y-4 shadow-sm' : 'hover:bg-emerald-500/10'}`}
            >
              <div 
                className={`flex justify-between items-center cursor-pointer ${!isAiExpanded ? 'p-3' : ''}`}
                onClick={() => setIsAiExpanded(!isAiExpanded)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[9px] uppercase tracking-wider bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded font-bold border border-emerald-500/20">
                    Proposition de l'IA
                  </span>
                  {!isAiExpanded && <span className="text-xs text-slate-400">Cliquez pour lire et appliquer</span>}
                </div>
                <button 
                  className="px-2 py-1 flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider hover:bg-emerald-500/20 rounded-md text-emerald-500 transition-colors"
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
                    <p className="text-xs text-slate-300 font-medium leading-relaxed mt-2.5 p-3 bg-black/30 border border-emerald-500/20 rounded-lg">
                      {aiSuggestion.explanation}
                    </p>
                  </div>

                  {/* Collapsible/Scrollable rewrite preview */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase block">Texte de substitution proposé (modifiable) :</span>
                    <textarea
                      value={aiSuggestion.suggestedText}
                      onChange={(e) => setAiSuggestion({ ...aiSuggestion, suggestedText: e.target.value })}
                      className="w-full text-xs text-slate-300 bg-black/45 border border-white/10 p-4 rounded-lg leading-relaxed font-mono resize-y min-h-[160px] focus:outline-hidden focus:border-emerald-500/50"
                    />
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button
                      id="apply-ai-btn"
                      onClick={() => {
                        applyAiSuggestion();
                        setIsAiExpanded(false);
                      }}
                      className="flex-1 text-xs font-bold py-2 bg-emerald-500 text-black hover:bg-emerald-400 rounded-lg transition-all flex items-center justify-center gap-1.5 shadow-xs cursor-pointer"
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
          <div className="border border-emerald-500/20 bg-emerald-950/10 rounded-xl p-5 space-y-4 shadow-sm animate-fadeIn">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 shrink-0">
                <Share2 className="h-4.5 w-4.5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-350 tracking-wider uppercase">Partager & Débattre</h3>
                <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                  Discutez d'un extrait de cette norme dans un salon de chat sécurisé.
                  Surlignez du texte à gauche pour préremplir l'extrait !
                </p>
              </div>
            </div>

            <form onSubmit={handleShareSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-[9.5px] uppercase font-bold text-slate-500 block">Extrait de clause sélectionné :</label>
                <textarea
                  id="share-excerpt-input"
                  value={selectedExcerpt}
                  onChange={(e) => setSelectedExcerpt(e.target.value)}
                  placeholder="Sélectionnez du texte dans l'éditeur ci-contre ou tapez un commentaire..."
                  className="w-full h-24 p-2.5 text-xs text-slate-200 bg-[#020204]/80 border border-white/10 rounded-lg focus:outline-hidden focus:border-emerald-500/30 resize-none font-sans placeholder-slate-705 leading-normal"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[9.5px] uppercase font-bold text-slate-500 block">Expert destinataire (CNETP) :</label>
                <select
                  id="share-recipient-select"
                  value={selectedRecipientId}
                  onChange={(e) => setSelectedRecipientId(e.target.value)}
                  className="w-full text-xs px-2.5 py-2.5 rounded-lg border border-white/10 bg-black/55 text-slate-200 font-semibold"
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
                <div className="text-[10.5px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-lg font-semibold border-l-2 border-l-emerald-500 shadow-inner">
                  {shareFeedback}
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedRecipientId}
                className="w-full text-xs font-bold py-2.5 bg-emerald-500 hover:bg-emerald-400 text-black rounded-lg transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-40"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                Partager à l'expert & Ouvrir le Chat
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Workspace Cloud Portals & Ancillary Documents Board */}
      <div className="border-t border-white/10 pt-6 mt-4 space-y-6">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FolderOpen className="h-4 w-4 text-emerald-400" />
              Ressources Connexes & Espace Collaboratif Cloud
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Gérez les rapports techniques, l'archivage classifié sur Google Drive, et planifiez les réunions de standardisation via Google Meet.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-emerald-400/80 bg-emerald-500/5 px-2.5 py-1 rounded border border-emerald-500/20 uppercase hidden sm:inline-block">
              ID: {document.id} • {document.code}
            </span>
            <button
              id="toggle-ressources-btn"
              onClick={() => setIsRessourcesExpanded(!isRessourcesExpanded)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5 cursor-pointer border ${
                isRessourcesExpanded 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_4px_12px_rgba(16,185,129,0.15)]" 
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
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start animate-fadeIn">
            {/* SECTION A: Google Cloud Platform integrations (Drive Folder + Google Meet Scheduling) */}
            <div className="bg-white/[0.02] border border-white/10 rounded-xl p-5 space-y-5">
              <div className="flex items-center gap-2">
                <span className="p-1 px-2 text-[10px] uppercase font-mono font-bold bg-blue-500/10 text-blue-400 rounded-md border border-blue-500/20">
                  Liaisons Cloud RDC
                </span>
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">
                  Portail Co-gouvernance Drive & Meet
                </h4>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">
                Pour faciliter l'accès vu le grand volume de normes, associez un dossier d'écriture <b>Google Drive</b> unique à cette norme. Planifiez des visioconférences <b>Google Meet</b> avec les comités techniques de validation (CNETP).
              </p>

              <div className="space-y-4">
                {/* Drive link configuration */}
                <div className="space-y-2">
                  <label className="text-[11.5px] font-bold text-slate-400 flex items-center gap-1.5 uppercase">
                    <Folder className="h-4 w-4 text-amber-500 fill-amber-500/10" />
                    Dossier d'archivage Google Drive Classé
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={driveUrl}
                      onChange={(e) => setDriveUrl(e.target.value)}
                      placeholder="https://drive.google.com/drive/folders/..."
                      className="flex-1 text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/40 focus:outline-hidden focus:border-blue-500/50 text-slate-200"
                    />
                    {driveUrl && (
                      <a
                        href={driveUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 rounded-lg flex items-center justify-center transition-all"
                        title="Ouvrir le dossier Drive"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 italic">
                    Les documents de cette norme seront rangés dans ce répertoire cloud pour une récupération accélérée.
                  </p>
                </div>

                {/* Meet link configuration */}
                <div className="space-y-2">
                  <label className="text-[11.5px] font-bold text-slate-400 flex items-center gap-1.5 uppercase">
                    <Video className="h-4 w-4 text-emerald-500" />
                    Lien de réunion Google Meet (Groupe de Travail / WG)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={meetUrl}
                      onChange={(e) => setMeetUrl(e.target.value)}
                      placeholder="https://meet.google.com/..."
                      className="flex-1 text-xs px-3 py-2 rounded-lg border border-white/10 bg-black/40 focus:outline-hidden focus:border-emerald-500/50 text-slate-200"
                    />
                    {meetUrl && (
                      <a
                        href={meetUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 rounded-lg flex items-center justify-center transition-all"
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
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1.5 font-medium animate-fadeIn">
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
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
              <div className="bg-white/[0.02] border border-white/10 rounded-xl p-5 space-y-4">
                <span className="p-1 px-2 text-[10px] uppercase font-mono font-bold bg-amber-500/10 text-amber-400 rounded-md border border-amber-500/20">
                  Pièces jointes ({document.references?.length || 0})
                </span>

                <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                  {!document.references || document.references.length === 0 ? (
                    <div className="p-6 border border-dashed border-white/10 rounded-xl text-center text-slate-500">
                      <Paperclip className="h-5 w-5 mx-auto mb-1.5 text-slate-650" />
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
                  <Plus className="h-3.5 w-3.5 text-emerald-400" />
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
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
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
                    className="px-4 py-2 text-xs font-bold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black transition-all flex items-center gap-1 cursor-pointer disabled:opacity-50"
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
              className="mt-2 text-xs font-bold text-emerald-400 hover:text-white transition-colors bg-emerald-500/5 px-3 py-1.5 rounded-lg border border-emerald-500/10 cursor-pointer"
            >
              Afficher/Dérouler le gestionnaire cloud
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
