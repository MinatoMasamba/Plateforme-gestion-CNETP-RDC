import { useState, useMemo } from "react";
import { History, RotateCcw, ArrowRightLeft, Calendar, User, AlignLeft, Info, HelpCircle } from "lucide-react";
import { Document, DocumentVersion, Collaborator } from "../types";
import { diffDocuments } from "../utils/diff";

interface HistoryAreaProps {
  document: Document;
  versions: DocumentVersion[];
  onRollback: (versionNumber: number) => Promise<void>;
  isRollingBack: boolean;
  activeCollaborator: Collaborator;
  selectedHistoryAuthorEmail?: string | null;
  onClearHistoryAuthorFilter?: () => void;
}

export default function HistoryArea({
  document,
  versions,
  onRollback,
  isRollingBack,
  activeCollaborator,
  selectedHistoryAuthorEmail = null,
  onClearHistoryAuthorFilter,
}: HistoryAreaProps) {
  // Checkboxes/Dropdowns for custom version selection diff comparisons
  const [v1Num, setV1Num] = useState<number | null>(null);
  const [v2Num, setV2Num] = useState<number | null>(null);

  // Filter versions by author if requested
  const filteredVersions = useMemo(() => {
    if (!selectedHistoryAuthorEmail) return versions;
    return versions.filter((v) => v.email.toLowerCase() === selectedHistoryAuthorEmail.toLowerCase());
  }, [versions, selectedHistoryAuthorEmail]);

  // Initialize comparison when versions load or document changes
  useMemo(() => {
    if (versions.length >= 2) {
      setV1Num(versions[1].versionNumber); // older
      setV2Num(versions[0].versionNumber); // newer
    } else if (versions.length === 1) {
      setV1Num(versions[0].versionNumber);
      setV2Num(versions[0].versionNumber);
    } else {
      setV1Num(null);
      setV2Num(null);
    }
  }, [versions]);

  // Retrieve texts for both selected comparison entities
  const comparisonText_1 = useMemo(() => {
    if (!v1Num) return "";
    const ver = versions.find((v) => v.versionNumber === v1Num);
    return ver ? ver.content : "";
  }, [v1Num, versions]);

  const comparisonText_2 = useMemo(() => {
    if (!v2Num) return "";
    const ver = versions.find((v) => v.versionNumber === v2Num);
    return ver ? ver.content : "";
  }, [v2Num, versions]);

  // Compute paragraph and word-level diffs
  const diffs = useMemo(() => {
    if (!comparisonText_1 && !comparisonText_2) return [];
    return diffDocuments(comparisonText_1, comparisonText_2);
  }, [comparisonText_1, comparisonText_2]);

  // Quick comparison triggers from timeline
  const handleQuickCompare = (tgtVerNum: number) => {
    // Set selected target as base (v1/older)
    setV1Num(tgtVerNum);
    
    // Choose comparison (v2/newer): either the newest version on top, or current active
    if (versions.length > 0) {
      const topNum = versions[0].versionNumber;
      if (topNum !== tgtVerNum) {
        setV2Num(topNum);
      } else {
        setV2Num(tgtVerNum);
      }
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-transparent flex flex-col lg:flex-row gap-6">
      {/* LEFT COLUMN: History log / Timeline */}
      <div className="w-full lg:w-96 flex flex-col gap-4 shrink-0 bg-black/45 border border-white/10 rounded-xl p-5 shadow-lg">
        <div className="flex items-center gap-2 pb-3 border-b border-white/10">
          <History className="h-5 w-5 text-emerald-400" />
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">Historique des Modifications</h2>
        </div>

        {/* Filter Alert Banner if filtering by specific editor */}
        {selectedHistoryAuthorEmail && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 flex flex-col gap-1 text-left relative overflow-hidden backdrop-blur-xs">
            <div className="absolute top-0 right-0 p-1">
              <button 
                onClick={onClearHistoryAuthorFilter}
                className="text-[10px] text-emerald-400/70 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 px-2 py-0.5 rounded font-bold uppercase transition-all"
                title="Afficher l'historique de tous les collaborateurs"
              >
                Tous
              </button>
            </div>
            <span className="text-[9px] font-extrabold text-emerald-400 uppercase tracking-widest">
              Filtre actif : Collaborateur
            </span>
            <p className="text-xs font-bold text-white truncate max-w-[180px]">
              {filteredVersions[0]?.author || selectedHistoryAuthorEmail}
            </p>
            <p className="text-[10px] text-slate-400">
              {filteredVersions.length} {filteredVersions.length > 1 ? "modifications répertoriées" : "modification répertoriée"}
            </p>
          </div>
        )}

        {filteredVersions.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs font-medium space-y-1">
            <Info className="h-6 w-6 mx-auto mb-2 text-slate-600" />
            <p>Aucun historique d'édition enregistré.</p>
            {selectedHistoryAuthorEmail && (
              <p className="text-[11px] text-slate-600 pt-1">Aucune modification par cet auteur.</p>
            )}
          </div>
        ) : (
          <div className="overflow-y-auto max-h-[600px] pr-1 space-y-4 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/5">
            {filteredVersions.map((ver, idx) => {
              const isSelectedV1 = v1Num === ver.versionNumber;
              const isSelectedV2 = v2Num === ver.versionNumber;

              return (
                <div key={ver.id} className="relative pl-8 group">
                  {/* Timeline bubble icon */}
                  <div
                    className={`absolute left-1.5 top-1.5 h-4 w-4 rounded-full border-2 flex items-center justify-center transition-all ${
                      isSelectedV1
                        ? "bg-[#020204] border-emerald-500 scale-110 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                        : isSelectedV2
                        ? "bg-emerald-500 border-emerald-500 scale-110 shadow-[0_0_8px_rgba(16,185,129,0.7)]"
                        : "bg-slate-950 border-white/20 group-hover:border-white/40"
                    }`}
                  >
                    <span className="h-1 w-1 rounded-full bg-white"></span>
                  </div>

                  {/* Version card */}
                  <div className="bg-white/[0.02] border border-white/5 rounded-lg p-3.5 space-y-2.5 hover:bg-white/5 transition-all">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[9.5px] font-bold bg-white/10 text-slate-200 px-1.5 py-0.5 rounded shadow-xs">
                          v{ver.versionNumber}
                        </span>
                        {ver.isRollback && (
                          <span className="text-[9px] font-bold bg-amber-500/10 text-amber-405 border border-amber-500/20 px-1.5 py-0.5 rounded uppercase tracking-tighter">
                            Restauré
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-550 font-mono">
                        {new Date(ver.timestamp).toLocaleDateString("fr-FR", {
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-300 line-clamp-3 leading-relaxed">
                      "{ver.comment}"
                    </p>

                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-semibold">
                      <User className="h-3 w-3 text-slate-650" />
                      <span className="truncate max-w-[120px]" title={ver.email}>
                        {ver.author}
                      </span>
                    </div>

                    {/* Timeline operations */}
                    <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[10.5px] font-bold">
                      <button
                        id={`timeline-compare-${ver.versionNumber}`}
                        onClick={() => handleQuickCompare(ver.versionNumber)}
                        className="text-emerald-400 hover:underline bg-transparent border-none cursor-pointer"
                      >
                        Comparer
                      </button>

                      <button
                        id={`timeline-restore-${ver.versionNumber}`}
                        onClick={() => onRollback(ver.versionNumber)}
                        disabled={isRollingBack}
                        className="text-amber-400 hover:underline flex items-center gap-0.5 disabled:opacity-50 cursor-pointer"
                      >
                        <RotateCcw className="h-2.5 w-2.5" />
                        Restaurer
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* RIGHT COLUMN: Custom Differences Workspace (Diff Viewer) */}
      <div className="flex-1 bg-black/45 border border-white/10 rounded-xl p-5 shadow-lg flex flex-col gap-4">
        {/* Diff selection controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="h-4.5 w-4.5 text-slate-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Analyse des différences
            </h3>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-450 z-20">
            <div className="flex items-center gap-1.5">
              <label htmlFor="select-v1" className="text-[11px] font-bold text-slate-500 uppercase">Source :</label>
              <select
                id="select-v1"
                className="font-mono text-xs px-2 py-1.5 rounded-lg border border-white/10 bg-black/50 text-slate-300 cursor-pointer"
                value={v1Num || ""}
                onChange={(e) => setV1Num(Number(e.target.value))}
              >
                {versions.map((v) => (
                  <option key={`opt-v1-${v.versionNumber}`} value={v.versionNumber}>
                    v{v.versionNumber} ({v.author.split(" ")[0]})
                  </option>
                ))}
              </select>
            </div>

            <span className="text-slate-600 font-mono">➜</span>

            <div className="flex items-center gap-1.5">
              <label htmlFor="select-v2" className="text-[11px] font-bold text-slate-500 uppercase">Cible :</label>
              <select
                id="select-v2"
                className="font-mono text-xs px-2 py-1.5 rounded-lg border border-white/10 bg-black/50 text-slate-300 cursor-pointer"
                value={v2Num || ""}
                onChange={(e) => setV2Num(Number(e.target.value))}
              >
                {versions.map((v) => (
                  <option key={`opt-v2-${v.versionNumber}`} value={v.versionNumber}>
                    v{v.versionNumber} ({v.author.split(" ")[0]})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Informative advice banner explaining diff colors */}
        <div className="p-3.5 bg-white/[0.02] border border-white/5 rounded-lg flex items-start gap-2.5">
          <HelpCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-400 leading-relaxed">
            <span className="font-bold text-slate-300">Légende de comparaison :</span> Le texte inchangé reste en gris neutre. Les mots ou paragraphes supprimés apparaissent en <span className="text-red-400 bg-red-500/10 border border-red-500/20 font-bold px-1.5 py-0.5 rounded">rouge barré</span>. Les ajouts de rédaction apparaissent en <span className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 font-bold px-1.5 py-0.5 rounded">vert</span>.
          </div>
        </div>

        {/* Render actual computed diff elements */}
        {versions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500 text-xs">
            <AlignLeft className="h-8 w-8 text-slate-700 mb-2 animate-pulse" />
            <p>Veuillez sauvegarder une version pour initier la comparaison.</p>
          </div>
        ) : v1Num === v2Num ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500 font-bold text-xs text-center space-y-2">
            <div className="h-10 w-10 bg-white/5 border border-white/10 rounded-full flex items-center justify-center text-slate-400 mx-auto">
              v{v1Num}
            </div>
            <p className="text-slate-300">Vous comparez la version v{v1Num} avec elle-même.</p>
            <p className="text-slate-500 text-[10.5px]">Sélectionnez deux versions distinctes ci-dessus pour visualiser les modifications entre elles.</p>
          </div>
        ) : (
          <div className="flex-1 border border-white/10 rounded-xl p-6 bg-black/30 max-h-[580px] overflow-y-auto space-y-4">
            {diffs.map((para) => {
              if (para.type === "unchanged") {
                return (
                  <p key={para.id} className="text-slate-300 text-xs leading-relaxed font-sans font-medium whitespace-pre-wrap animate-fadeIn">
                    {para.newText}
                  </p>
                );
              }

              if (para.type === "added") {
                return (
                  <div key={para.id} className="bg-emerald-950/20 border-l-3 border-emerald-500 p-4 rounded-r-lg text-slate-300 text-xs leading-relaxed whitespace-pre-wrap shadow-inner animate-fadeIn">
                    <span className="font-mono text-[9px] font-bold bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30 mr-2 uppercase">
                      + Ajout entier
                    </span>
                    {para.newText}
                  </div>
                );
              }

              if (para.type === "removed") {
                return (
                  <div key={para.id} className="bg-red-950/20 border-l-3 border-red-500 p-4 rounded-r-lg text-slate-400 line-through leading-relaxed whitespace-pre-wrap decoration-red-900/40 shadow-inner animate-fadeIn">
                    <span className="font-mono text-[9px] font-bold bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded border border-red-500/30 mr-2 uppercase">
                      - Retrait entier
                    </span>
                    {para.oldText}
                  </div>
                );
              }

              if (para.type === "modified") {
                return (
                  <div key={para.id} className="bg-[#181824]/40 border-l-3 border-amber-500/70 p-4 rounded-r-lg shadow-inner animate-fadeIn">
                    <div className="text-[9.5px] font-bold uppercase tracking-wider text-amber-400 mb-2 block">
                      Modification dans le paragraphe (Comparaison inline) :
                    </div>
                    <p className="text-slate-300 text-xs leading-relaxed whitespace-pre-wrap">
                      {para.wordDiff?.map((word, idx) => {
                        if (word.added) {
                          return (
                            <span key={`w-add-${idx}`} className="diff-added" title="Terme ajouté">
                              {word.value}
                            </span>
                          );
                        }
                        if (word.removed) {
                          return (
                            <span key={`w-rem-${idx}`} className="diff-removed" title="Terme retiré">
                              {word.value}
                            </span>
                          );
                        }
                        return <span key={`w-neutral-${idx}`}>{word.value}</span>;
                      })}
                    </p>
                  </div>
                );
              }

              return null;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
