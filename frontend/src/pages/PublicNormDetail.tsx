import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  Download, 
  ChevronLeft, 
  Clock, 
  User, 
  FileText, 
  AlertCircle,
  CheckCircle2,
  Loader,
  Share2,
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
  created_at: string;
  version_number?: number;
  content?: string;
  jo_reference?: string;
  publication_date?: string;
}

export default function PublicNormDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [norme, setNorme] = useState<Norme | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);

  useEffect(() => {
    fetchNorme();
  }, [id]);

  const fetchNorme = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try API v1
      const response = await fetch(`/api/v1/norms/${id}/`, {
        headers: {
          'Accept': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Check if published
      if (data.status !== 'PUBLISHED') {
        setError('Cette norme n\'est pas encore publiée');
        return;
      }
      
      setNorme(data);
    } catch (err) {
      console.error("Error fetching norme:", err);
      setError("Impossible de charger la norme");
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const handleDownloadPDF = () => {
    // Future: Generate PDF
    alert("Téléchargement PDF: Fonctionnalité en développement");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader className="h-8 w-8 text-emerald-500 animate-spin" />
          <p className="text-slate-300">Chargement de la norme...</p>
        </div>
      </div>
    );
  }

  if (error || !norme) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <h2 className="text-lg font-semibold text-red-400">Erreur</h2>
                <p className="text-sm text-red-300">{error || "Norme non trouvée"}</p>
              </div>
            </div>
            <button
              onClick={() => navigate("/")}
              className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium text-slate-100 transition-colors"
            >
              Retour à l'accueil
            </button>
          </div>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header Navigation */}
      <nav className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-300 hover:text-emerald-400 hover:bg-slate-800/50 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            Retour
          </button>
          <h1 className="text-lg font-semibold text-slate-100">Norme Publiée</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="p-2 text-slate-300 hover:text-emerald-400 hover:bg-slate-800/50 rounded-lg transition-colors"
              title="Partager le lien"
            >
              <Share2 className="h-5 w-5" />
            </button>
            {copiedUrl && <span className="text-xs text-emerald-400">Copié!</span>}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Status Badge */}
        <div className="mb-6">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-300">Norme publiée</span>
          </div>
        </div>

        {/* Title & Reference */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-slate-50 mb-2">{norme.title}</h1>
              <p className="text-lg text-slate-400 font-mono">{norme.reference_number}</p>
            </div>
            <button
              onClick={handleDownloadPDF}
              className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
            >
              <Download className="h-5 w-5" />
              PDF
            </button>
          </div>
        </div>

        {/* Description */}
        {norme.description && (
          <div className="mb-8 p-6 bg-slate-800/50 border border-slate-700/50 rounded-lg">
            <h2 className="text-sm font-semibold text-slate-400 uppercase mb-3">Description</h2>
            <p className="text-slate-200 leading-relaxed">{norme.description}</p>
          </div>
        )}

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Version */}
          <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase">Version</span>
            </div>
            <p className="text-lg font-bold text-slate-100">{norme.version_number || 1}</p>
          </div>

          {/* Created */}
          <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase">Créée</span>
            </div>
            <p className="text-sm font-mono text-slate-300">{formatDate(norme.created_at)}</p>
          </div>

          {/* Updated */}
          <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Eye className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase">Mise à jour</span>
            </div>
            <p className="text-sm font-mono text-slate-300">{formatDate(norme.updated_at)}</p>
          </div>

          {/* CTM/WG */}
          <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <User className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase">CTM/WG</span>
            </div>
            <p className="text-sm font-mono text-slate-300">
              CTM {norme.ctm_id} / WG {norme.wg_id}
            </p>
          </div>
        </div>

        {/* Content */}
        {norme.content && (
          <div className="mb-8 p-8 bg-slate-800/20 border border-slate-700/30 rounded-lg">
            <h2 className="text-lg font-semibold text-slate-100 mb-6">Contenu de la norme</h2>
            <div className="prose prose-invert max-w-none">
              <div className="text-slate-200 whitespace-pre-wrap leading-relaxed">
                {norme.content}
              </div>
            </div>
          </div>
        )}

        {/* Journal Officiel Info */}
        {norme.jo_reference && (
          <div className="p-6 bg-blue-500/10 border border-blue-500/30 rounded-lg mb-8">
            <h3 className="text-sm font-semibold text-blue-400 uppercase mb-2">Publication Officielle</h3>
            <p className="text-sm text-blue-200">
              <strong>Référence JO:</strong> {norme.jo_reference}
            </p>
            {norme.publication_date && (
              <p className="text-sm text-blue-200 mt-1">
                <strong>Date de publication:</strong> {formatDate(norme.publication_date)}
              </p>
            )}
          </div>
        )}

        {/* Footer Info */}
        <div className="mt-12 pt-8 border-t border-slate-700/30 text-center">
          <p className="text-sm text-slate-400">
            Cette norme est publiquement accessible et consultable.
            <br />
            Pour plus d'informations, contactez la <span className="font-semibold text-slate-300">CNETP - RDC</span>
          </p>
        </div>
      </main>
    </div>
  );
}
