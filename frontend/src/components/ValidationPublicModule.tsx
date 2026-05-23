import React, { useState } from "react";
import { Award, Search, BookOpen, Clock, ShieldCheck, HeartPulse, Sparkles, SlidersHorizontal, Download, ArrowRight, ArrowLeft } from "lucide-react";

// Types
interface NormDraft {
  id: string;
  title: string;
  code: string;
  ctm: string;
  step: number; // 1 to 7 corresponding to the core 11 steps
  statusLabel: string;
  updatedAt: string;
}

const INITIAL_DRAFTS: NormDraft[] = [
  { id: "dr-1", title: "BTC40 - Blocs de Terre Comprimée pour murs porteurs", code: "CNETP-BTC40-2026", ctm: "CTM 8 – Sciences des Matériaux", step: 3, statusLabel: "Toilettage légistique par la CTC", updatedAt: "2026-05-18" },
  { id: "dr-2", title: "Eurocode RDC : Adaptation dynamique des calculs parasismiques", code: "CNETP-EC8-RDC", ctm: "CTM 2 – Structures et Ouvrages", step: 1, statusLabel: "Conception spécialisée WG", updatedAt: "2026-05-19" },
  { id: "dr-3", title: "Plan Directeur Numérique BIM RDC (ISO 19650)", code: "CNETP-BIM-19650", ctm: "CTM 3 – Bâtiment & BIM", step: 5, statusLabel: "Adoption souveraine Assemblée Plénière", updatedAt: "2026-05-12" },
  { id: "dr-4", title: "Standard de Qualité des Canalisations d'Adduction Urbaine", code: "CNETP-HYD-04", ctm: "CTM 6 – Ingénierie Hydraulique", step: 7, statusLabel: "Homologué & Publié au Journal Officiel", updatedAt: "2026-05-09" }
];

const WORKFLOW_STEPS = [
  { id: 1, title: "Conception spécialisée WG", desc: "Le Groupe de Travail (WG) rédige et affine le contenu initial." },
  { id: 2, title: "Validation Sectorielle CTM", desc: "Les experts du CTM concerné votent et formulent des amendements." },
  { id: 3, title: "Toilettage CTC", desc: "La Cellule de Coordination harmonise la légistique structurelle." },
  { id: 4, title: "Enquête Publique Numérique", desc: "Portail public ouvert pendant 30 jours pour recueillir les avis nationaux." },
  { id: 5, title: "Dépôt Assemblée Plénière", desc: "Les 200 experts se prononcent pour viser un consensus à au moins 75%." },
  { id: 6, title: "Sanction Ministérielle", desc: "Visé par arrêté d'homologation nominatif du Ministre ITP." },
  { id: 7, title: "Publication JO et Portail", desc: "Norme archivée, accessible au public avec filigrane officiel." }
];

export default function ValidationPublicModule() {
  const [drafts, setDrafts] = useState<NormDraft[]>(INITIAL_DRAFTS);
  const [activeDraftId, setActiveDraftId] = useState<string>("dr-1");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCtm, setSelectedCtm] = useState("Tous");
  
  const activeDraft = drafts.find(d => d.id === activeDraftId) || drafts[0];

  const advanceStep = (id: string) => {
    setDrafts(prev => prev.map(d => {
      if (d.id === id && d.step < 7) {
        const nextStep = d.step + 1;
        return {
          ...d,
          step: nextStep,
          statusLabel: WORKFLOW_STEPS[nextStep - 1].title,
          updatedAt: new Date().toISOString().split("T")[0]
        };
      }
      return d;
    }));
  };

  const retreatStep = (id: string) => {
    setDrafts(prev => prev.map(d => {
      if (d.id === id && d.step > 1) {
        const prevStep = d.step - 1;
        return {
          ...d,
          step: prevStep,
          statusLabel: WORKFLOW_STEPS[prevStep - 1].title,
          updatedAt: new Date().toISOString().split("T")[0]
        };
      }
      return d;
    }));
  };

  const filteredDrafts = drafts.filter(d => {
    const matchesSearch = d.title.toLowerCase().includes(searchQuery.toLowerCase()) || d.code.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCtm = selectedCtm === "Tous" || d.ctm.includes(selectedCtm);
    return matchesSearch && matchesCtm;
  });

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full text-slate-300">
      
      {/* Header section */}
      <div className="border-b border-white/10 pb-5">
        <div className="flex items-center gap-3 mb-1">
          <BookOpen className="h-6 w-6 text-emerald-400" />
          <h2 className="text-xl font-extrabold text-white tracking-tight uppercase">Modules 6 & 7 : Bureau Légistique & Bibliothèque Publique</h2>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
          Suivez le cycle de vie légistique en boucle fermée (11 étapes structurelles d'après l'Arrêté) et visitez le guichet public de consultation réglementaire nationale.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* Step tracker layout (Module 6) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-black/45 border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
            
            <div className="flex justify-between items-center pb-3 border-b border-white/5">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="h-4.5 w-4.5 text-emerald-400" />
                Bibliothèque Publique & Enquête
              </h3>
              <span className="text-[9.5px] bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded-full border border-emerald-500/20">
                Portail Public
              </span>
            </div>

            {/* Selector draft */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 mb-1.5 font-semibold uppercase tracking-wider text-[9.5px]">Projet Réglementaire :</label>
                <select
                  value={activeDraftId}
                  onChange={e => setActiveDraftId(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-white/10 bg-black/60 text-xs text-slate-300 focus:outline-hidden"
                >
                  {drafts.map(d => (
                    <option key={d.id} value={d.id}>{d.title} ({d.code})</option>
                  ))}
                </select>
              </div>

              <div className="p-3.5 bg-white/[0.02] border border-white/5 rounded-xl text-xs space-y-1">
                <p className="font-bold text-slate-300">{activeDraft.title}</p>
                <p className="text-[10px] text-slate-500 font-mono">Code : {activeDraft.code} • CTM associé: {activeDraft.ctm}</p>
              </div>
            </div>

            {/* Render Horizontal/Vertical interactive step progression */}
            <div className="space-y-4">
              <p className="text-[10.5px] uppercase tracking-wider text-slate-400 font-bold block">Suivi des phases réglementaires :</p>
              
              <div className="space-y-3 relative">
                {/* Timeline center line */}
                <div className="absolute left-3.5 top-4 bottom-4 w-0.5 bg-white/5 pointer-events-none" />

                {WORKFLOW_STEPS.map(step => {
                  const isPast = step.id < activeDraft.step;
                  const isCurrent = step.id === activeDraft.step;
                  const isFuture = step.id > activeDraft.step;

                  return (
                    <div
                      key={step.id}
                      className={`flex gap-4 p-3 rounded-lg border transition-all duration-200 text-xs select-none ${
                        isCurrent
                          ? "bg-emerald-500/10 border-emerald-500/35 text-white shadow-sm scale-[1.01]"
                          : isPast
                          ? "bg-white/[0.01] border-white/5 text-slate-400 opacity-60"
                          : "bg-transparent border-transparent text-slate-600 opacity-30"
                      }`}
                    >
                      {/* Check status circle indicator */}
                      <span className={`h-7 w-7 rounded-full flex items-center justify-center font-bold text-[10.5px] font-mono shrink-0 transition-colors ${
                        isCurrent
                          ? "bg-emerald-500 text-black shadow-[0_0_8px_rgba(16,185,129,0.4)]"
                          : isPast
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-black/40 border border-white/10 text-slate-600"
                      }`}>
                        {step.id}
                      </span>

                      <div>
                        <p className={`font-bold ${isCurrent ? "text-emerald-400" : ""}`}>{step.title}</p>
                        {isCurrent && <p className="text-[10.5px] text-slate-400 mt-1 leading-normal">{step.desc}</p>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Workflow command controls */}
            <div className="flex gap-3 pt-4 border-t border-white/5 font-sans">
              <button
                disabled={activeDraft.step === 1}
                onClick={() => retreatStep(activeDraft.id)}
                className="px-3.5 py-2 rounded-lg bg-white/5 text-white hover:bg-white/10 font-bold text-xs disabled:opacity-30 disabled:hover:bg-transparent flex items-center gap-1 transition-all cursor-pointer"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Renvoyer au niveau précédent
              </button>

              <button
                disabled={activeDraft.step === 7}
                onClick={() => advanceStep(activeDraft.id)}
                className="px-4 py-2 rounded-lg bg-emerald-500 text-black hover:bg-emerald-400 font-extrabold text-xs disabled:opacity-35 disabled:hover:bg-transparent flex items-center gap-1 ml-auto transition-all cursor-pointer"
              >
                Promouvoir au niveau supérieur
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

          </div>
        </div>

        {/* Public library guichet (Module 7) */}
        <div className="bg-black/45 border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex justify-between items-center pb-3 border-b border-white/5">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Award className="h-4.5 w-4.5 text-emerald-400" />
              Portail Public des Normes
            </h3>
            <span className="text-[9.5px] bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded-full border border-emerald-500/20">
              Module 7
            </span>
          </div>

          <p className="text-[11px] text-slate-400 leading-normal">
            Guichet libre de relecture citoyenne. Les ingénieurs ou le public peuvent télécharger les versions intermédiaires ou définitives homologuées par le Ministère.
          </p>

          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Ex: Eurocode, Canalisations, BTC..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-lg border border-white/10 bg-black/55 text-xs text-white focus:outline-hidden"
              />
            </div>

            <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
              {filteredDrafts.map(d => (
                <div key={d.id} className="p-3.5 bg-white/[0.02] border border-white/5 rounded-xl space-y-2 relative overflow-hidden group">
                  
                  {/* Diagonal "JOURNAL OFFICIEL" watermark for draft index 7 */}
                  {d.step === 7 && (
                    <div className="absolute right-[-24px] top-6 rotate-[35deg] bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-5 py-0.5 text-[8px] font-bold uppercase tracking-wider opacity-60 pointer-events-none uppercase">
                      JO Officiel
                    </div>
                  )}

                  <div className="space-y-0.5">
                    <span className="font-mono text-[9px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">
                      {d.code}
                    </span>
                    <h4 className="font-bold text-white text-xs mt-1.5 pr-10">{d.title}</h4>
                    <p className="text-[10px] text-slate-500 italic mt-0.5">{d.ctm}</p>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400 font-semibold font-sans">
                    <span>Statut: {d.step === 7 ? "Homologué" : "En cours"}</span>
                    
                    <button
                      onClick={() => alert(`Préparation du PDF de la norme ${d.code} filigrané en cours...`)}
                      className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-white rounded font-bold cursor-pointer transition-colors flex items-center gap-1.5"
                    >
                      <Download className="h-3 w-3" />
                      Télécharger
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
