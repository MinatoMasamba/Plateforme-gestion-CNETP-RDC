import React, { useState, useRef } from "react";
import { X, Upload, FileText, Keyboard, Loader2, Sparkles, CheckCircle } from "lucide-react";
import { Document } from "../types";

interface CreateNormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newDoc: Document) => void;
  isDarkMode: boolean;
}

export default function CreateNormModal({
  isOpen,
  onClose,
  onSuccess,
  isDarkMode
}: CreateNormModalProps) {
  const [step, setStep] = useState<"choice" | "form">("choice");
  const [importMethod, setImportMethod] = useState<"upload" | "manual">("manual");
  
  // Form fields
  const [title, setTitle] = useState("");
  const [code, setCode] = useState("");
  const [category, setCategory] = useState("Qualité");
  const [ctm, setCtm] = useState("CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [fileName, setFileName] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  // Handles drag and drop upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    setFileName(file.name);
    setLoading(true);
    setStatusMessage("Lecture du document en cours...");

    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      
      // Simulate advanced legistic structure extraction using Congo standards
      setTimeout(() => {
        setStatusMessage("Extraction des clauses réglementaires...");
        
        setTimeout(() => {
          setStatusMessage("Structuration de la nomenclature gouvernementale...");
          
          setTimeout(() => {
            // Pre-fill form fields based on filename and extracted text
            const cleanName = file.name.replace(/\.[^/.]+$/, ""); // strip extension
            const guessedTitle = "Projet de Norme RDC-ITP - " + cleanName.replace(/[_-]/g, " ");
            const guessedCode = "PR-RDC-" + cleanName.toUpperCase().replace(/[^A-Z0-9]/g, "-").slice(0, 10);
            
            setTitle(guessedTitle);
            setCode(guessedCode);
            setContent(text || "Clausier de norme extrait à compléter.");
            setDescription("Norme technique de co-gouvernance générée par import de document.");
            setImportMethod("upload");
            setStep("form");
            setLoading(false);
          }, 800);
        }, 800);
      }, 700);
    };

    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  // Submit and save on client + backend
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !code) {
      alert("Le titre et le code de la norme sont requis.");
      return;
    }

    setLoading(true);
    setStatusMessage("Enregistrement de la norme réglementaire...");

    try {
      const res = await fetch("/api/documents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          code,
          category,
          ctm,
          description,
          content: content || `// Nouveau canevas de norme ${code}\n\nClause 1 : Principes Généraux...\n`
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Erreur de création de document");
      }

      const createdDoc = await res.json();
      onSuccess(createdDoc);
      
      // Reset state
      setStep("choice");
      setTitle("");
      setCode("");
      setDescription("");
      setContent("");
      setFileName("");
      onClose();
    } catch (err: any) {
      alert(err.message || "Échec d'enregistrement");
    } finally {
      setLoading(false);
    }
  };

  const selectManualChoice = () => {
    setTitle("");
    setCode("PR-RDC-");
    setCategory("Qualité");
    setCtm("CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale");
    setDescription("");
    setContent("");
    setImportMethod("manual");
    setStep("form");
  };

  const cardTheme = isDarkMode 
    ? "bg-[#0b0c15] border-white/5 hover:border-blue-500/40 text-slate-300"
    : "bg-[#f8fafc] border-slate-250 hover:border-blue-500/40 text-slate-800 shadow-xs";

  const modalTheme = isDarkMode
    ? "bg-[#040409] border-white/10 text-white"
    : "bg-white border-slate-200 text-slate-900 shadow-xl";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
      <div className={`w-full max-w-2xl rounded-xl border p-6 flex flex-col max-h-[90vh] overflow-y-auto ${modalTheme}`}>
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 dark:border-white/5">
          <div>
            <h2 className="text-base font-bold tracking-tight flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-500" />
              Initialisation d'une Nouvelle Norme
            </h2>
            <p className="text-xs text-slate-500 font-medium">Saisissez les paramètres de co-gouvernance ISO pour la RDC</p>
          </div>
          <button 
            type="button" 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Loading Spinner Overlays */}
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center gap-4 text-center">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
            <p className="text-sm font-semibold tracking-wide text-slate-400 animate-pulse">{statusMessage}</p>
            {fileName && <span className="text-[11px] font-mono text-slate-500">Source : {fileName}</span>}
          </div>
        ) : step === "choice" ? (
          /* Choice Step */
          <div className="py-6 space-y-6">
            <p className="text-xs text-slate-500 leading-normal">
              Afin de préserver la sécurité de formulation et la cohérence de l'image de marque État, sélectionnez la méthode de création de votre avant-projet :
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Option A: Manual Edit */}
              <button
                type="button"
                onClick={selectManualChoice}
                className={`p-6 rounded-xl border text-left flex flex-col gap-3 transition-all duration-200 group cursor-pointer ${cardTheme}`}
              >
                <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-450 group-hover:scale-105 transition-transform">
                  <Keyboard className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide group-hover:text-blue-400">Rédiger un canevas vierge</h3>
                  <p className="text-[11px] leading-relaxed text-slate-500 mt-1">
                    Ouvrir un nouveau formulaire d'édition vierge pour structurer pas à pas vos clauses réglementaires RDC.
                  </p>
                </div>
              </button>

              {/* Option B: Upload file */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`p-6 rounded-xl border text-left flex flex-col gap-3 transition-all duration-200 group cursor-pointer ${cardTheme}`}
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange}
                  accept=".txt,.doc,.docx,.pdf,.md" 
                  className="hidden" 
                />
                <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-450 group-hover:scale-105 transition-transform">
                  <Upload className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide group-hover:text-blue-400">Importer & extraire un document</h3>
                  <p className="text-[11px] leading-relaxed text-slate-500 mt-1">
                    Glissez-déposez ou sélectionnez un fichier (.txt, rapport d'enquête public) pour y extraire automatiquement les clauses.
                  </p>
                </div>
              </div>

            </div>

            <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[11px] leading-normal flex items-start gap-2.5">
              <span className="text-sm">⚠️</span>
              <p className="font-semibold">
                Rappel de la Charte d'État : Tout ajout de norme doit faire l'objet d'un examen par le Secrétaire Technique du CNETP pour son homologation au Journal Officiel.
              </p>
            </div>
          </div>
        ) : (
          /* Form Step */
          <form onSubmit={handleSubmit} className="py-4 space-y-4">
            {/* Theme responsive input classes resolver */}
            {(() => {
              const isLightMode = !isDarkMode;
              const inputClass = `w-full px-3 py-2.5 rounded-lg border font-medium text-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500/60 transition-all ${
                isLightMode 
                  ? "bg-white border-slate-250 text-slate-900 placeholder-slate-400 focus:border-blue-555" 
                  : "bg-black/30 border-white/10 text-white placeholder-slate-600 focus:border-blue-500/50"
              }`;
              const labelClass = `text-[10px] font-bold uppercase tracking-wider ${isLightMode ? "text-slate-550" : "text-slate-500"}`;

              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className={labelClass}>Titre de la nouvelle norme</label>
                      <input
                        type="text"
                        required
                        placeholder="Ex: Norme sur la résistance des argiles locales de Kinshasa"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className={inputClass}
                      />
                    </div>

                    <div className="space-y-1">
                      <label className={labelClass}>Code de classification (Code)</label>
                      <input
                        type="text"
                        required
                        placeholder="Ex: PR-RDC-801-BTC"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className={`${inputClass} font-mono`}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className={labelClass}>Catégorie d'activité</label>
                      <select
                        value={category}
                        onChange={(e) => {
                          const val = e.target.value;
                          setCategory(val);
                          if (val === "Qualité") {
                            setCtm("CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale");
                          } else if (val === "Sécurité") {
                            setCtm("CTM 3 – Bâtiment, Urbanisme et Transition Numérique");
                          } else {
                            setCtm("CTM 1 – Géotechnique et Risques Naturels");
                          }
                        }}
                        className={inputClass}
                      >
                        <option value="Qualité" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>Qualité (Standardisation ISO/IEC)</option>
                        <option value="Sécurité" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>Sécurité (Infrastructures & Civil)</option>
                        <option value="Éthique" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>Éthique (Transition & Gouvernance Numérique)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className={labelClass}>Sous-commission (CTM de rattachement)</label>
                      <select
                        value={ctm}
                        onChange={(e) => setCtm(e.target.value)}
                        className={inputClass}
                      >
                        <option value="CTM 1 – Géotechnique" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 1 – Géotechnique</option>
                        <option value="CTM 2 – Ouvrages d'art" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 2 – Ouvrages d'art</option>
                        <option value="CTM 3 – Bâtiments" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 3 – Bâtiments</option>
                        <option value="CTM 4 – Aéroports" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 4 – Aéroports</option>
                        <option value="CTM 5 – Routes, Chemins de fer et Ports" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 5 – Routes, Rail & Ports</option>
                        <option value="CTM 6 – Ressources en eau & Ingénierie hydraulique" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 6 – Eau & Hydraulique</option>
                        <option value="CTM 7 – Assainissement" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 7 – Assainissement</option>
                        <option value="CTM 8 – Recherche, Simulation & Sciences des matériaux" className={isLightMode ? "text-slate-900 bg-white" : "text-white bg-black"}>CTM 8 – Sciences des Matériaux</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className={labelClass}>Description de l'ouvrage / Résumé</label>
                    <input
                      type="text"
                      placeholder="Ex: Spécifications de granulométrie et de résistance..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className={inputClass}
                    />
                  </div>

                  {/* Editable extracted contents preview */}
                  <div className="space-y-1">
                    <label className={`${labelClass} flex items-center justify-between`}>
                      <span>Contenu Rédactionnel (Texte source de la norme)</span>
                      {importMethod === "upload" && (
                        <span className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase font-bold border ${
                          isLightMode ? "bg-blue-100 text-blue-800 border-blue-200" : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        }`}>
                          Extrait avec succès
                        </span>
                      )}
                    </label>
                    <textarea
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      placeholder="Rédigez l'avant-projet de norme ici (les clauses et articles)..."
                      rows={10}
                      className={`w-full p-3.5 rounded-lg border font-mono placeholder-slate-600 focus:outline-hidden focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500/60 transition-all leading-relaxed text-xs ${
                        isLightMode 
                          ? "bg-white border-slate-250 text-slate-900 placeholder-slate-450" 
                          : "bg-black/40 border-white/10 text-white placeholder-slate-655"
                      }`}
                    />
                  </div>
                </div>
              );
            })()}

            {/* Actions */}
            <div className={`flex items-center justify-between pt-4 border-t ${
              !isDarkMode ? "border-slate-200" : "border-white/10 dark:border-white/5"
            }`}>
              <button
                type="button"
                onClick={() => setStep("choice")}
                className={`px-4 py-2 rounded-lg border text-xs cursor-pointer ${
                  !isDarkMode ? "border-slate-350 text-slate-600 hover:text-slate-950 bg-slate-100/50 hover:bg-slate-100" : "border-white/10 text-slate-400 hover:text-white"
                }`}
              >
                &larr; Retour aux options
              </button>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className={`px-4 py-2 rounded-lg text-xs cursor-pointer ${
                    !isDarkMode ? "text-slate-500 hover:text-slate-800" : "text-slate-400 hover:text-white"
                  }`}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-lg text-xs font-bold bg-blue-500 hover:bg-blue-600 text-black flex items-center gap-1.5 transition-colors shadow-md cursor-pointer"
                >
                  <CheckCircle className="h-4 w-4" />
                  Générer et Ouvrir la Norme
                </button>
              </div>
            </div>

          </form>
        )}

      </div>
    </div>
  );
}
