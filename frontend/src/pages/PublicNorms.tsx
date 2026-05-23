import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Search, 
  Filter, 
  BookOpen, 
  ChevronRight, 
  Loader,
  AlertCircle,
  CheckCircle2,
  Eye
} from "lucide-react";

interface Norme {
  id: number;
  reference_number: string;
  title: string;
  description: string;
  ctm_id: number;
  wg_id: number;
  status: string;
  updated_at: string;
  version_number?: number;
}

export default function PublicNorms() {
  const [norms, setNorms] = useState<Norme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCTM, setFilterCTM] = useState<number | null>(null);

  useEffect(() => {
    fetchPublishedNorms();
  }, []);

  const fetchPublishedNorms = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try multiple endpoints
      let data = [];
      
      // First try the published endpoint
      try {
        const response = await fetch("/api/v1/norms/?status=PUBLISHED", {
          headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
          const result = await response.json();
          data = Array.isArray(result) ? result : result.results || [];
        }
      } catch (e) {
        console.warn("Failed to fetch from /api/v1/norms/", e);
      }

      // Fallback to mobile endpoint
      if (data.length === 0) {
        const response = await fetch("/api/v1/mobile/published_norms/", {
          headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
          data = await response.json();
        }
      }

      // Filter only published
      data = data.filter((n: any) => n.status === 'PUBLISHED');
      setNorms(data || []);
      
      if (data.length === 0) {
        setError("Aucune norme publiée pour le moment");
      }
    } catch (err) {
      console.error("Error fetching norms:", err);
      setError("Impossible de charger les normes");
    } finally {
      setLoading(false);
    }
  };

  // Filter norms
  const filteredNorms = norms.filter(norm => {
    const matchesSearch = 
      norm.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      norm.reference_number.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCTM = filterCTM === null || norm.ctm_id === filterCTM;
    
    return matchesSearch && matchesCTM;
  });

  const ctmOptions = Array.from(new Set(norms.map(n => n.ctm_id))).sort();

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader className="h-8 w-8 text-emerald-500 animate-spin" />
          <p className="text-slate-300">Chargement des normes publiées...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-slate-50 mb-2">Normes Publiées</h1>
              <p className="text-slate-400">Consultez les normes officielles de la CNETP</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
              <Eye className="h-5 w-5 text-emerald-400" />
              <span className="text-sm font-medium text-emerald-300">{filteredNorms.length} normes</span>
            </div>
          </div>

          {/* Search & Filter */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Chercher une norme..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
              />
            </div>

            {/* Filter CTM */}
            {ctmOptions.length > 0 && (
              <select
                value={filterCTM || ""}
                onChange={(e) => setFilterCTM(e.target.value ? parseInt(e.target.value) : null)}
                className="px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
              >
                <option value="">Tous les CTM</option>
                {ctmOptions.map(ctm => (
                  <option key={ctm} value={ctm}>CTM {ctm}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0" />
            <p className="text-sm text-amber-200">{error}</p>
          </div>
        )}

        {filteredNorms.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="h-12 w-12 text-slate-600 mx-auto mb-4" />
            <p className="text-lg font-medium text-slate-300">Aucune norme trouvée</p>
            <p className="text-sm text-slate-400">Essayez une autre recherche</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredNorms.map((norm) => (
              <Link
                key={norm.id}
                to={`/public/norms/${norm.id}/`}
                className="group relative p-6 bg-slate-800/40 border border-slate-700/50 rounded-lg hover:border-emerald-500/50 hover:bg-slate-800/60 transition-all duration-300 cursor-pointer"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <p className="text-xs font-mono text-slate-500 mb-1">{norm.reference_number}</p>
                    <h3 className="text-lg font-semibold text-slate-50 group-hover:text-emerald-400 transition-colors line-clamp-2">
                      {norm.title}
                    </h3>
                  </div>
                  <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0 ml-2" />
                </div>

                {/* Description */}
                {norm.description && (
                  <p className="text-sm text-slate-300 line-clamp-2 mb-4">
                    {norm.description}
                  </p>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-700/30">
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span className="px-2 py-1 bg-slate-700/30 rounded">v{norm.version_number || 1}</span>
                    <span>{formatDate(norm.updated_at)}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-slate-700/30 text-center text-sm text-slate-400">
        <p>Plateforme de Normalisation CNETP - République Démocratique du Congo</p>
      </footer>
    </div>
  );
}
