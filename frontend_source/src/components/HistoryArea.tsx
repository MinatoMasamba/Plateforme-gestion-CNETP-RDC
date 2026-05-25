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
  isDarkMode?: boolean;
}

export default function HistoryArea({
  document,
  versions,
  onRollback,
  isRollingBack,
  activeCollaborator,
  selectedHistoryAuthorEmail = null,
  onClearHistoryAuthorFilter,
  isDarkMode = true,
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
    <div className={`w-full lg:w-96 flex flex-col gap-4 shrink-0 border rounded-xl p-5 shadow-lg ${
      isDarkMode ? "bg-black/45 border-white/10" : "bg-blue-50/50 border-blue-200"
    }`}>
      <div className={`flex items-center gap-2 pb-3 border-b ${isDarkMode ? "border-white/10" : "border-blue-200"}`}>
        <History className={`h-5 w-5 ${isDarkMode ? "text-blue-400" : "text-blue-600"}`} />
        <h2 className={`text-xs font-bold uppercase tracking-wider ${isDarkMode ? "text-white" : "text-slate-800"}`}>Historique des Modifications</h2>
      </div>

      {/* Filter Alert Banner if filtering by specific editor */}
      {selectedHistoryAuthorEmail && (
        <div className={`rounded-lg p-3 flex flex-col gap-1 text-left relative overflow-hidden backdrop-blur-xs border ${
          isDarkMode ? "bg-blue-500/10 border-blue-500/20" : "bg-blue-100/50 border-blue-300"
        }`}>
          <div className="absolute top-0 right-0 p-1">
            <button 
              onClick={onClearHistoryAuthorFilter}
              className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase transition-all ${
                isDarkMode 
                  ? "text-blue-400/70 hover:text-white bg-blue-500/10 hover:bg-blue-500/20" 
                  : "text-blue-700 hover:text-blue-900 bg-blue-200 hover:bg-blue-300"
              }`}
              title="Afficher l'historique de tous les collaborateurs"
            >
              Tous
            </button>
          </div>
          <span className={`text-[9px] font-extrabold uppercase tracking-widest ${isDarkMode ? "text-blue-400" : "text-blue-600"}`}>
            Filtre actif : Collaborateur
          </span>
          <p className={`text-xs font-bold truncate max-w-[180px] ${isDarkMode ? "text-white" : "text-slate-800"}`}>
            {filteredVersions[0]?.author || selectedHistoryAuthorEmail}
          </p>
          <p className={`text-[10px] ${isDarkMode ? "text-slate-400" : "text-slate-500"}`}>
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
                        ? (isDarkMode ? "bg-[#020204] border-blue-500 scale-110 shadow-[0_0_8px_rgba(59,130,246,0.5)]" : "bg-white border-blue-600 scale-110 shadow-[0_0_8px_rgba(37,99,235,0.4)]")
                        : isSelectedV2
                        ? (isDarkMode ? "bg-blue-500 border-blue-500 scale-110 shadow-[0_0_8px_rgba(59,130,246,0.7)]" : "bg-blue-600 border-blue-600 scale-110 shadow-[0_0_8px_rgba(37,99,235,0.6)]")
                        : (isDarkMode ? "bg-slate-950 border-white/20 group-hover:border-white/40" : "bg-white border-slate-300 group-hover:border-blue-400")
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
                        className={`hover:underline bg-transparent border-none cursor-pointer ${isDarkMode ? "text-blue-400" : "text-blue-600"}`}
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
      <div className={`flex-1 border rounded-xl p-5 shadow-lg flex flex-col gap-4 ${
        isDarkMode ? "bg-black/45 border-white/10" : "bg-white/80 border-slate-200"
      }`}>
        {/* Diff selection controls */}
        <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b ${
          isDarkMode ? "border-white/10" : "border-slate-200"
        }`}>
          <div className="flex items-center gap-2">
            <ArrowRightLeft className={`h-4.5 w-4.5 ${isDarkMode ? "text-slate-400" : "text-slate-500"}`} />
            <h3 className={`text-xs font-bold uppercase tracking-wider ${isDarkMode ? "text-white" : "text-slate-900"}`}>
              Analyse des différences
            </h3>
          </div>

          <div className="flex items-center gap-2 text-xs z-20">
            <div className="flex items-center gap-1.5">
              <label htmlFor="select-v1" className={`text-[11px] font-bold uppercase ${isDarkMode ? "text-slate-500" : "text-slate-600"}`}>Source :</label>
              <select
                id="select-v1"
                className={`font-mono text-xs px-2 py-1.5 rounded-lg border cursor-pointer ${
                  isDarkMode ? "border-white/10 bg-black/50 text-slate-300" : "border-slate-300 bg-white text-slate-800"
                }`}
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

            <span className={`font-mono ${isDarkMode ? "text-slate-600" : "text-slate-400"}`}>➜</span>

            <div className="flex items-center gap-1.5">
              <label htmlFor="select-v2" className={`text-[11px] font-bold uppercase ${isDarkMode ? "text-slate-500" : "text-slate-600"}`}>Cible :</label>
              <select
                id="select-v2"
                className={`font-mono text-xs px-2 py-1.5 rounded-lg border cursor-pointer ${
                  isDarkMode ? "border-white/10 bg-black/50 text-slate-300" : "border-slate-300 bg-white text-slate-800"
                }`}
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
        <div className={`p-3.5 border rounded-lg flex items-start gap-2.5 ${
          isDarkMode ? "bg-white/[0.02] border-white/5" : "bg-blue-50/50 border-blue-200"
        }`}>
          <HelpCircle className={`h-4 w-4 shrink-0 mt-0.5 ${isDarkMode ? "text-blue-400" : "text-blue-600"}`} />
          <div className={`text-[11px] leading-relaxed ${isDarkMode ? "text-slate-400" : "text-slate-600"}`}>
            <span className={`font-bold ${isDarkMode ? "text-slate-300" : "text-slate-800"}`}>Légende de comparaison :</span> Le texte inchangé reste en gris neutre. Les mots ou paragraphes supprimés apparaissent en <span className={`font-bold px-1.5 py-0.5 rounded border ${isDarkMode ? "text-red-400 bg-red-500/10 border-red-500/20" : "text-red-700 bg-red-100 border-red-200"}`}>rouge barré</span>. Les ajouts de rédaction apparaissent en <span className={`font-bold px-1.5 py-0.5 rounded border ${isDarkMode ? "text-blue-400 bg-blue-500/10 border-blue-500/20" : "text-blue-700 bg-blue-100 border-blue-200"}`}>bleu</span>.
          </div>
        </div>

        {/* Render actual computed diff elements */}
        {versions.length === 0 ? (
          <div className={`flex-1 flex flex-col items-center justify-center py-20 text-xs ${isDarkMode ? "text-slate-500" : "text-slate-400"}`}>
            <AlignLeft className="h-8 w-8 text-slate-700 mb-2 animate-pulse" />
            <p>Veuillez sauvegarder une version pour initier la comparaison.</p>
          </div>
        ) : v1Num === v2Num ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500 font-bold text-xs text-center space-y-2">
            <div className={`h-10 w-10 border rounded-full flex items-center justify-center mx-auto ${isDarkMode ? "bg-white/5 border-white/10 text-slate-400" : "bg-slate-50 border-slate-200 text-slate-500"}`}>
              v{v1Num}
            </div>
            <p className={isDarkMode ? "text-slate-300" : "text-slate-700"}>Vous comparez la version v{v1Num} avec elle-même.</p>
            <p className={`text-[10.5px] ${isDarkMode ? "text-slate-500" : "text-slate-400"}`}>Sélectionnez deux versions distinctes ci-dessus pour visualiser les modifications entre elles.</p>
          </div>
        ) : (
          <div className={`flex-1 border rounded-xl p-6 max-h-[580px] overflow-y-auto space-y-4 ${
            isDarkMode ? "border-white/10 bg-black/30" : "border-slate-200 bg-white"
          }`}>
            {diffs.map((para) => {
              if (para.type === "unchanged") {
                return (
                  <p key={para.id} className={`text-xs leading-relaxed font-sans font-medium whitespace-pre-wrap animate-fadeIn ${isDarkMode ? "text-slate-300" : "text-slate-700"}`}>
                    {para.newText}
                  </p>
                );
              }

              if (para.type === "added") {
                return (
                  <div key={para.id} className={`border-l-3 p-4 rounded-r-lg text-xs leading-relaxed whitespace-pre-wrap shadow-inner animate-fadeIn ${
                    isDarkMode ? "bg-blue-950/20 border-blue-500 text-slate-300" : "bg-blue-50/50 border-blue-500 text-slate-800"
                  }`}>
                    <span className={`font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border mr-2 uppercase ${
                      isDarkMode ? "bg-blue-500/20 text-blue-400 border-blue-500/30" : "bg-blue-100 text-blue-700 border-blue-200"
                    }`}>
                      + Ajout entier
                    </span>
                    {para.newText}
                  </div>
                );
              }

              if (para.type === "removed") {
                return (
                  <div key={para.id} className={`border-l-3 p-4 rounded-r-lg max-w-[95%] line-through leading-relaxed whitespace-pre-wrap shadow-inner animate-fadeIn ${
                    isDarkMode ? "bg-red-950/20 border-red-500 decoration-red-900/40 text-slate-400" : "bg-red-50/50 border-red-500 decoration-red-200 text-slate-600"
                  }`}>
                    <span className={`font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border mr-2 uppercase ${
                      isDarkMode ? "bg-red-500/20 text-red-400 border-red-500/30" : "bg-red-100 text-red-700 border-red-200"
                    }`}>
                      - Retrait entier
                    </span>
                    {para.oldText}
                  </div>
                );
              }

              if (para.type === "modified") {
                return (
                  <div key={para.id} className={`border-l-3 p-4 rounded-r-lg shadow-inner animate-fadeIn ${
                    isDarkMode ? "bg-[#181824]/40 border-amber-500/70" : "bg-amber-50/40 border-amber-400"
                  }`}>
                    <div className={`text-[9.5px] font-bold uppercase tracking-wider mb-2 block ${isDarkMode ? "text-amber-400" : "text-amber-600"}`}>
                      Modification dans le paragraphe (Comparaison inline) :
                    </div>
                    <p className={`text-xs leading-relaxed whitespace-pre-wrap ${isDarkMode ? "text-slate-300" : "text-slate-800"}`}>
                      {para.wordDiff?.map((word, idx) => {
                        if (word.added) {
                          return (
                            <span key={`w-add-${idx}`} className={`font-medium rounded px-1 transition-all ${isDarkMode ? "bg-blue-500/20 text-blue-400" : "bg-blue-100 text-blue-700"}`} title="Terme ajouté">
                              {word.value}
                            </span>
                          );
                        }
                        if (word.removed) {
                          return (
                            <span key={`w-rem-${idx}`} className={`font-medium rounded px-1 line-through transition-all ${isDarkMode ? "bg-red-500/20 text-red-400" : "bg-red-100 text-red-700"}`} title="Terme retiré">
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
