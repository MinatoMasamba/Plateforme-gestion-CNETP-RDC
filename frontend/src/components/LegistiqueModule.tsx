import React, { useState } from "react";
import { BookOpen, Check, Search, FileText, Send, Clock, User, FileSignature } from "lucide-react";

interface DocumentForReview {
  id: string;
  title: string;
  code: string;
  ctm: string;
  status: "En attente" | "En cours" | "Validé";
  assignedTo?: string;
  lastUpdated: string;
  content: string;
}

const INITIAL_DOCS: DocumentForReview[] = [
  { 
    id: "doc-rev-1", 
    title: "Eurocode RDC : Adaptation dynamique des calculs parasismiques", 
    code: "CNETP-EC8-RDC", 
    ctm: "CTM 2 – Structures et Ouvrages", 
    status: "En attente", 
    lastUpdated: "2026-05-19",
    content: "Article 1.\nLa présente norme définit... (Contenu à toiletter)"
  },
  { 
    id: "doc-rev-2", 
    title: "BTC40 - Blocs de Terre Comprimée", 
    code: "CNETP-BTC40-2026", 
    ctm: "CTM 8 – Sciences des Matériaux", 
    status: "En cours", 
    assignedTo: "Expert Légiste 1",
    lastUpdated: "2026-05-18",
    content: "Article 2.\nSpécifications techniques des blocs..."
  }
];

export default function LegistiqueModule({ userRole }: { userRole: string }) {
  const [docs, setDocs] = useState<DocumentForReview[]>(INITIAL_DOCS);
  const [activeDoc, setActiveDoc] = useState<DocumentForReview | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [editedContent, setEditedContent] = useState("");

  const isLegiste = userRole === "LEGISTE";
  const isCoordCtc = userRole === "COORD_CTC" || userRole === "ADMIN";

  const handleAssign = (docId: string) => {
    setDocs(docs.map(d => d.id === docId ? { ...d, status: "En cours", assignedTo: "Moi (Légiste)" } : d));
  };

  const handleValidate = (docId: string) => {
    setDocs(docs.map(d => d.id === docId ? { ...d, status: "Validé" } : d));
    setActiveDoc(null);
  };

  const filteredDocs = docs.filter(d => 
    d.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    d.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#06060c] text-slate-300 relative z-0 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-teal-900/10 via-black to-slate-900/20 pointer-events-none" />
      
      <div className="flex-1 flex h-full relative z-10 overflow-hidden px-6 py-6 gap-6">
        
        {/* Left List */}
        <div className="w-1/3 flex flex-col border border-white/10 bg-black/40 rounded-xl overflow-hidden shadow-2xl backdrop-blur-xl">
          <div className="p-4 border-b border-white/10 bg-white/5">
            <h2 className="text-sm font-bold text-teal-400 flex items-center gap-2">
              <FileSignature className="h-4.5 w-4.5" />
              Toilettage Légistique
            </h2>
            <p className="text-[11px] text-slate-400 mt-1">Normes en attente de conformité juridique (CTC)</p>
            
            <div className="mt-4 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Rechercher une norme..."
                className="w-full bg-black/40 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-xs font-medium text-slate-300 placeholder:text-slate-600 focus:outline-hidden focus:border-teal-500/50"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin scrollbar-thumb-white/10">
            {filteredDocs.map(doc => (
              <div
                key={doc.id}
                onClick={() => {
                  setActiveDoc(doc);
                  setEditedContent(doc.content);
                }}
                className={`p-3 rounded-lg cursor-pointer transition-all border ${
                  activeDoc?.id === doc.id
                    ? "bg-teal-500/10 border-teal-500/30 shadow-[0_4px_15px_rgba(20,184,166,0.1)]"
                    : "bg-white/5 border-transparent hover:bg-white/10"
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-[10px] font-bold text-teal-500 bg-teal-500/10 px-1.5 py-0.5 rounded uppercase tracking-wider">{doc.code}</span>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                    doc.status === "Validé" ? "bg-emerald-500/10 text-emerald-400" :
                    doc.status === "En cours" ? "bg-amber-500/10 text-amber-400" :
                    "bg-slate-500/10 text-slate-400"
                  }`}>{doc.status}</span>
                </div>
                <h3 className="text-xs font-medium text-slate-200 line-clamp-2 leading-relaxed">{doc.title}</h3>
                <div className="flex items-center gap-3 mt-3 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {doc.lastUpdated}</span>
                  {doc.assignedTo && <span className="flex items-center gap-1"><User className="h-3 w-3" /> {doc.assignedTo}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Editor Work Area */}
        <div className="w-2/3 flex flex-col border border-white/10 bg-black/40 rounded-xl overflow-hidden shadow-2xl backdrop-blur-xl">
          {activeDoc ? (
            <>
              <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">{activeDoc.title}</h3>
                  <p className="text-xs text-slate-400 mt-1">{activeDoc.code} - {activeDoc.ctm}</p>
                </div>
                <div className="flex items-center gap-2">
                  {activeDoc.status === "En attente" && (isLegiste || isCoordCtc) && (
                    <button
                      onClick={() => handleAssign(activeDoc.id)}
                      className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-medium transition-all"
                    >
                      M'assigner la relecture
                    </button>
                  )}
                  {activeDoc.status === "En cours" && (isLegiste || isCoordCtc) && (
                    <button
                      onClick={() => handleValidate(activeDoc.id)}
                      className="px-3 py-1.5 bg-teal-500 text-black hover:bg-teal-400 rounded-lg text-xs font-bold transition-all shadow-[0_0_15px_rgba(20,184,166,0.3)] flex items-center gap-1.5"
                    >
                      <Check className="h-3.5 w-3.5" />
                      Prêt pour l'enquête publique
                    </button>
                  )}
                </div>
              </div>

              <div className="flex-1 p-6 overflow-y-auto">
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-slate-300">Édition restreinte (forme juridique)</span>
                    <span className="text-[10px] text-teal-400 font-mono bg-teal-500/10 px-2 py-0.5 rounded">RÉVISION ACTIVE</span>
                  </div>
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    disabled={activeDoc.status === "Validé" || (!isLegiste && !isCoordCtc)}
                    className="w-full h-96 bg-black/50 border border-white/10 rounded-lg p-4 text-sm font-mono text-slate-300 leading-relaxed focus:outline-hidden focus:border-teal-500/50 resize-none disabled:opacity-70"
                  />
                  <p className="text-[11px] text-slate-500 mt-2">
                    Les modifications apportées ici ne doivent concerner que la structure légistique et la numérotation (sans altérer le fond technique).
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <BookOpen className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Sélectionnez une norme pour le toilettage légistique</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
