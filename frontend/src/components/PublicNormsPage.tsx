import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Search, ArrowLeft, Download, ShieldCheck, HelpCircle, MessageSquare, Plus, FileText, CheckCircle2, ChevronRight, Share2, Award, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface PublicNorm {
  id: string;
  code: string;
  title: string;
  category: string;
  description: string;
  statusLabel: string;
  step: number; 
  updatedAt: string;
  author: string;
  ctm: string;
  content: string;
  articles: { num: string; title: string; text: string }[];
}

const PUBLIC_NORMS_SEED: PublicNorm[] = [
  {
    id: "btc-40",
    code: "CNETP-BTC40-2026",
    title: "Blocs de Terre Comprimée (BTC) pour murs porteurs en RDC",
    category: "Matériaux locaux",
    description: "Norme nationale régissant la fabrication, les exigences mécaniques et l'intégration des briques de latérite compactées.",
    statusLabel: "Enquête Publique Ouverte",
    step: 4,
    updatedAt: "2026-05-18",
    author: "Prof. Masamba Édouard",
    ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
    content: "Cette norme définit les caractéristiques dimensionnelles et de résistance pour l'usage du bloc d'argile dans le bâtiment congolais.",
    articles: [
      { num: "Art. 1", title: "Champ d'application", text: "La présente norme s'applique aux blocs de terre comprimée stabilisés au ciment ou à la chaux, destinés à la réalisation de parois porteuses et non porteuses dans l'hinterland." },
      { num: "Art. 2", title: "Sélection des latérites", text: "Les sols argileux locaux doivent présenter une fraction sableuse comprise entre 40% et 70% et une fraction fine plastique de moins de 30% pour garantir une cohésion optimale après pressage mécanique." },
      { num: "Art. 3", title: "Résistance à la compression", text: "La résistance minimale requise après 28 jours de cure humide est fixée à 4.0 MPa pour les blocs porteurs de classe standard BTC-40, et 2.5 MPa pour les cloisons secondaires." },
      { num: "Art. 4", title: "Absorption d'eau", text: "Le taux d'absorption d'eau par capillarité ne doit en aucun cas dépasser 15% du poids sec du bloc après immersion réglementaire de 24 heures." }
    ]
  },
  {
    id: "seisme-rdc",
    code: "CNETP-EC8-RDC",
    title: "Eurocode RDC : Adaptation dynamique des calculs parasismiques",
    category: "Structures & Ouvrages",
    description: "Régulation des coefficients d'accélération sismique pour les constructions du Graben Est-Africain (Goma, Bukavu).",
    statusLabel: "En Phase de Toilettage CTC",
    step: 3,
    updatedAt: "2026-05-19",
    author: "Ir. Godefroid Munongo",
    ctm: "CTM 2 – Structures et Ouvrages d'Art",
    content: "Adaptation d'ingénierie et coefficients de comportement mécanique pour les sols volcaniques du Kivu.",
    articles: [
      { num: "Art. 1", title: "Zonage sismique national", text: "Le graben du Kivu et l'axe Albert-Tanganyika sont classés en Zone 3 (Sismicité élevée). Les modélisations doivent intégrer les spectres d'ondes de cisaillement localisés." },
      { num: "Art. 2", title: "Coefficients de comportement (q)", text: "Le facteur de comportement q pour les ossatures en béton armé à ductilité moyenne (DCM) est ramené à un maximum de 3.0 pour prévenir les ruptures fragiles sous sollicitation alternée." },
      { num: "Art. 3", title: "Dispositions constructives", text: "L'obligation d'un double chaînage continu au niveau de chaque plancher est imposée pour toutes les constructions d'utilité publique de plus de deux niveaux au Kivu." }
    ]
  },
  {
    id: "bim-rdc",
    code: "CNETP-BIM-19650",
    title: "Plan Directeur Numérique BIM RDC (Standard ISO 19650)",
    category: "Architecture & BIM",
    description: "Normalisation du Building Information Modeling pour l'obligation de la maquette numérique dans les marchés publics de l'État.",
    statusLabel: "Homologation en cours",
    step: 5,
    updatedAt: "2026-05-12",
    author: "Arch. Sylvain Lukusa",
    ctm: "CTM 3 – Bâtiment, Urbanisme et Transition Numérique",
    content: "Standardisation des formats ouverts IFC pour l'automatisation du contrôle technique par le BTC.",
    articles: [
      { num: "Art. 1", title: "Obligation de Maquette", text: "Tout projet d'infrastructure financé par le Trésor Public dont le montant estimé dépasse un million de dollars américains est assujetti à la livraison d'un modèle BIM au format ouvert IFC 4." },
      { num: "Art. 2", title: "Environnement Commun de Données (CDE)", text: "Les maîtres d'ouvrage publics doivent déployer un espace serveur souverain géré par le Ministère des ITP pour centraliser les validations de maquettes." },
      { num: "Art. 3", title: "Contrôle en bureau légistique", text: "Les visas d'approbation et l'octroi des permis de bâtir CNETP intègrent la détection automatisée des conflits géométriques par rapport aux normes d'habitabilité." }
    ]
  },
  {
    id: "hyd-04",
    code: "CNETP-HYD-04-2026",
    title: "Standard de Qualité des Canalisations d'Adduction Urbaine",
    category: "Hydraulique",
    description: "Spécifications de pression nominale, de fonte ductile et de PEHD pour la distribution d'eau potable dans les grandes agglomérations.",
    statusLabel: "Publiée au Journal Officiel",
    step: 7,
    updatedAt: "2026-05-09",
    author: "Ir. Chantal Mwamba",
    ctm: "CTM 6 – Ingénierie Hydraulique et Distribution",
    content: "Régulation des raccordements REGIDESO pour sécuriser le transport d'eau potable sans plomb.",
    articles: [
      { num: "Art. 1", title: "Matériaux certifiés", text: "Les conduites d'adduction principale d'eau potable doivent être constituées de fonte ductile avec revêtement interne en ciment de haut fourneau ou en PEHD de classe alimentaire certifié sans bisphénol." },
      { num: "Art. 2", title: "Pression nominale standard", text: "La pression de fonctionnement admissible pour les réseaux de distribution secondaires est fixée à PN 10 ou PN 16, sous réserve d'essais de charge hydrauliques après raccordement." },
      { num: "Art. 3", title: "Tolérance d'étanchéité", text: "Pour chaque tronçon de canalisation posé d'une longueur supérieure à 500 mètres, un test d'épreuve à l'eau de 2 heures sous 1.5 fois la pression nominale doit présenter une chute inférieure à 0.2 bar." }
    ]
  }
];

const WORKFLOW_STEPS = [
  { id: 1, title: "Conception spécialisée WG", desc: "Le Groupe de Travail (WG) rédige et affine le contenu initial." },
  { id: 2, title: "Validation Sectorielle CTM", desc: "Les experts du CTM concerné votent et formulent des amendements." },
  { id: 3, title: "Toilettage CTC", desc: "La Cellule de Coordination harmonise la légistique structurelle." },
  { id: 4, title: "Enquête Publique Numérique", desc: "Portail public ouvert pendant 30 jours pour recueillir les avis nationaux." },
  { id: 5, title: "Dépôt Assemblée Plénière", desc: "Les 200 experts se prononcent pour viser un consensus à au moins 75%." },
  { id: 6, title: "Sanction Ministérielle", desc: "Visé par arrêté d'homologation nominatif du Ministre ITP." },
  { id: 7, title: "Publication JO et Portail", desc: "Norme homologuée finale intégrée de plein droit au Journal Officiel de la RDC." }
];

export default function PublicNormsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Tous");
  
  // Selected detail norm
  const [selectedNorm, setSelectedNorm] = useState<PublicNorm | null>(null);

  // In-memory public reviews list
  const [publicReviews, setPublicReviews] = useState<Record<string, { author: string; profession: string; date: string; comment: string }[]>>({
    "btc-40": [
      { author: "Ir. Gabriel Kasongo", profession: "Ingénieur Structure, OVD Goma", date: "2026-05-12", comment: "Excellente initiative d'aborder les briques en terre comprimées. Je suggère toutefois d'imposer un essai d'absorption d'eau plus régulier pour faire face à la saison des pluies du Kwilu." },
      { author: "Prof. Thérèse Nzuzi", profession: "Laboratoire Génie Civil, UNILU", date: "2026-05-15", comment: "L'art. 3 sur les 4.0 MPa me paraît très réaliste si la stabilisation au ciment Portland CEM II dose à au moins 8%. Les ateliers locaux devront être équipés de presses homologuées." }
    ],
    "seisme-rdc": [
      { author: "Marc Tshilombo", profession: "Promoteur Immobilier, Bukavu", date: "2026-05-20", comment: "Le double chaînage continu à l'article 3 va augmenter le coût du gros œuvre d'environ 12%, mais au vu des derniers séismes de Goma, c'est indispensable pour sauver des vies." }
    ]
  });

  // Review form states
  const [newAuthor, setNewAuthor] = useState("");
  const [newProfession, setNewProfession] = useState("");
  const [newComment, setNewComment] = useState("");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const categories = ["Tous", ...Array.from(new Set(PUBLIC_NORMS_SEED.map(n => n.category)))];

  const filteredNorms = PUBLIC_NORMS_SEED.filter(n => {
    const matchesSearch = n.title.toLowerCase().includes(search.toLowerCase()) || n.code.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === "Tous" || n.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleAddReview = (e: React.FormEvent, normId: string) => {
    e.preventDefault();
    if (!newAuthor || !newComment) return;

    const newRecord = {
      author: newAuthor,
      profession: newProfession || "Citoyen",
      date: new Date().toISOString().split("T")[0],
      comment: newComment
    };

    setPublicReviews(prev => ({
      ...prev,
      [normId]: [newRecord, ...(prev[normId] || [])]
    }));

    setNewAuthor("");
    setNewProfession("");
    setNewComment("");
    
    setToastMessage("Opinion d'enquête publique soumise avec succès ! Elle sera auditée par le Secrétaire du CTM.");
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleDownloadNorm = (normCode: string) => {
    setToastMessage(`Téléchargement de la norme ${normCode} officiel en cours (Filigrane public CNETP).`);
    setTimeout(() => setToastMessage(null), 4500);
  };

  return (
    <div className="min-h-screen bg-[#020204] font-sans text-slate-300 relative overflow-hidden flex flex-col">
      {/* Background patterns */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/10 via-black to-slate-900/15 pointer-events-none" />
      <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-teal-500/5 to-transparent pointer-events-none"></div>

      {/* HEADER BAR */}
      <header className="h-16 border-b border-white/10 px-6 bg-black/60 backdrop-blur-xl shrink-0 flex items-center justify-between z-10 relative">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-teal-500/20 border border-teal-500/30">
            <BookOpen className="w-4 h-4 text-teal-400" />
          </div>
          <div>
            <span className="text-sm font-bold text-white tracking-widest uppercase">CNETP</span>
            <span className="text-[9px] text-slate-500 block font-mono font-bold uppercase tracking-wider">Bibliothèque Publique</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/auth/login/")}
            className="text-xs font-bold text-slate-400 hover:text-white uppercase tracking-wider bg-white/5 border border-white/10 px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Espace Experts
          </button>
          <button
            onClick={() => navigate("/")}
            className="text-xs font-bold text-slate-300 hover:text-teal-400 flex items-center gap-1.5 transition-colors"
          >
            Retour Accueil
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </header>

      {/* SYSTEM TOAST NOTIFICATIONS */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div 
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl border bg-[#040c06] border-emerald-500/30 max-w-md"
          >
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 shadow-[0_0_15px_rgba(16,185,129,0.3)]" />
            <span className="text-xs font-semibold text-slate-200">{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 overflow-y-auto p-6 sm:p-8 z-10 relative">
        <div className="max-w-6xl mx-auto space-y-8">
          
          <AnimatePresence mode="wait">
            {!selectedNorm ? (
              // MAIN DIRECTORY LIST WITH SEARCH & FILTER
              <motion.div
                key="list"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8"
              >
                {/* Intro Section */}
                <div className="space-y-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[10px] font-bold uppercase tracking-widest">
                    <Award className="h-3 w-3" />
                    Enquête publique & Bibliothèque nationale
                  </span>
                  <h1 className="text-3xl font-extrabold text-white tracking-tight">Référentiel Public des Normes ITP</h1>
                  <p className="text-sm text-slate-400 max-w-3xl leading-relaxed">
                    Bienvenue sur le portail ouvert de la commission CNETP. Vous pouvez ici consulter en toute transparence l'évolution des avant-projets règlementations de la RDC et formuler vos avis techniques pour l'enquête publique.
                  </p>
                </div>

                {/* Filter and search bar */}
                <div className="flex flex-col sm:flex-row gap-4 bg-black/45 border border-white/10 p-4 rounded-2xl">
                  {/* Search Bar */}
                  <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Rechercher par mot clé, code..."
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-teal-500/30 transition-all font-medium"
                    />
                  </div>

                  {/* Categories picker */}
                  <div className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-none shrink-0">
                    {categories.map(cat => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-3.5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg border transition-all cursor-pointer ${
                          selectedCategory === cat
                            ? "bg-teal-500/15 border-teal-500/30 text-teal-400 shadow-sm"
                            : "border-white/5 bg-transparent text-slate-400 hover:text-white"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Grid list of normas */}
                {filteredNorms.length === 0 ? (
                  <div className="border border-dashed border-white/10 rounded-2xl p-16 text-center space-y-3">
                    <HelpCircle className="h-10 w-10 text-slate-600 mx-auto animate-pulse" />
                    <p className="text-sm text-slate-500">Aucun projet de norme ne correspond à vos critères de recherche.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {filteredNorms.map(norm => (
                      <div 
                        key={norm.id} 
                        className="bg-[#06060c]/60 border border-white/5 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-teal-500/20 hover:bg-black flex flex-col justify-between h-72 group shadow-[0_10px_35px_rgba(0,0,0,0.4)]"
                      >
                        {/* Status tag */}
                        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-teal-500/30 via-emerald-400/80 to-teal-500/20" />
                        
                        <div>
                          <div className="flex items-center justify-between gap-2 mb-3">
                            <span className="font-mono text-[9px] text-teal-400 font-bold bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
                              {norm.code}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              norm.step === 7 
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}>
                              {norm.statusLabel}
                            </span>
                          </div>

                          <h3 className="text-sm font-bold text-white mb-2 line-clamp-2 leading-snug group-hover:text-teal-400 transition-colors">
                            {norm.title}
                          </h3>

                          <p className="text-xs text-slate-500 leading-normal line-clamp-3 mb-4">
                            {norm.description}
                          </p>
                        </div>

                        <div className="pt-4 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 mt-auto font-sans font-semibold">
                          <span>Catégorie: <strong className="text-slate-300">{norm.category}</strong></span>
                          
                          <button
                            type="button"
                            onClick={() => setSelectedNorm(norm)}
                            className="px-3 py-1.5 bg-teal-500 text-black hover:bg-teal-400 font-extrabold rounded-lg flex items-center gap-1.5 transition-all cursor-pointer shadow-sm text-[10px] uppercase tracking-wider"
                          >
                            Consulter la Norme
                            <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            ) : (
              // DETAILLNORME : IN-DEPTH DETAIL VIEW FOR INDIVIDUAL STANDARD
              <motion.div
                key="detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                {/* Back Link */}
                <button
                  type="button"
                  onClick={() => setSelectedNorm(null)}
                  className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  <ArrowLeft className="h-4 w-4 text-emerald-400" />
                  Retourner au catalogue des normes publiques
                </button>

                {/* Norm Detail Header Card */}
                <div className="bg-black/60 border border-white/10 rounded-3xl p-6 sm:p-8 relative overflow-hidden backdrop-blur-md space-y-6 shadow-2xl">
                  <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-teal-500/30 via-emerald-400 to-teal-500/30" />
                  
                  <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-teal-400 font-bold bg-teal-500/10 px-2.5 py-0.5 rounded border border-teal-500/30">
                          {selectedNorm.code}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          Mis à jour : {selectedNorm.updatedAt}
                        </span>
                      </div>
                      <h1 className="text-xl sm:text-2xl font-extrabold text-white leading-snug tracking-tight">
                        {selectedNorm.title}
                      </h1>
                      <p className="text-xs text-slate-400 font-semibold font-mono">
                        CTM Responsable : {selectedNorm.ctm}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleDownloadNorm(selectedNorm.code)}
                        className="px-4 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 font-bold text-xs flex items-center gap-2 cursor-pointer transition-all duration-200"
                        title="Télécharger l'acte légal et le texte complet (PDF)"
                      >
                        <Download className="h-4 w-4" />
                        Télécharger Acte Officiel
                      </button>
                    </div>
                  </div>

                  <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-teal-500/40 pl-4 py-1 italic">
                    "{selectedNorm.description}"
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                  
                  {/* LEFT SIDE: Chapter Index and text readers */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="bg-black/45 border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
                      <div className="flex items-center justify-between pb-3 border-b border-white/5">
                        <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                          <FileText className="h-4.5 w-4.5 text-teal-400" />
                          Contenu de l'Avant-Projet de Norme Actif
                        </h2>
                        <span className="text-[9.5px] bg-slate-500/15 text-slate-300 font-mono px-2 py-0.5 rounded">
                          {selectedNorm.articles.length} Clauses Rédigées
                        </span>
                      </div>

                      {/* Displaying actual articles */}
                      <div className="space-y-6">
                        {selectedNorm.articles.map(art => (
                          <div key={art.num} className="bg-white/[0.01] border border-white/5 rounded-xl p-5 hover:bg-white/[0.02] transition-colors relative group">
                            <div className="flex justify-between items-start mb-3">
                              <span className="font-mono text-xs font-bold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
                                {art.num}
                              </span>
                              <span className="text-xs font-bold text-slate-300">{art.title}</span>
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed font-sans pl-1">
                              {art.text}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* RIGHT SIDE: Validation track & Public inquiry reviews */}
                  <div className="space-y-6">
                    
                    {/* Validation Step widget */}
                    <div className="bg-black/45 border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
                      <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        <ShieldCheck className="h-4.5 w-4.5 text-teal-400" />
                        Niveau d'Avancement
                      </h3>
                      
                      <div className="p-3.5 rounded-xl bg-teal-500/5 border border-teal-500/15 text-xs">
                        <p className="font-bold text-teal-400 flex items-center gap-1.5 mb-1 text-[11px] uppercase tracking-wider">
                          Étape active : {selectedNorm.step} / 7
                        </p>
                        <p className="text-slate-300 font-bold">{WORKFLOW_STEPS[selectedNorm.step - 1].title}</p>
                        <p className="text-[10px] text-slate-500 leading-normal mt-2.5">
                          {WORKFLOW_STEPS[selectedNorm.step - 1].desc}
                        </p>
                      </div>

                      {/* Step Progress visual bar */}
                      <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
                        <div 
                          className="h-full bg-teal-500 rounded-full transition-all duration-500"
                          style={{ width: `${(selectedNorm.step / 7) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Public opinion / Review section */}
                    <div className="bg-black/45 border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
                      <div className="flex items-center justify-between pb-3 border-b border-white/5">
                        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                          <MessageSquare className="h-4.5 w-4.5 text-teal-400" />
                          Enquête Publique : Opinions
                        </h3>
                        <span className="text-[10px] font-bold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded-full">
                          {(publicReviews[selectedNorm.id] || []).length} Avis
                        </span>
                      </div>

                      {/* Form panel */}
                      {selectedNorm.step === 4 ? (
                        <form onSubmit={(e) => handleAddReview(e, selectedNorm.id)} className="space-y-3 p-3 bg-white/[0.01] border border-white/5 rounded-xl">
                          <p className="text-[9.5px] text-slate-500 uppercase font-mono tracking-wider mb-2">📢 Déposez votre avis technique :</p>
                          <div className="grid grid-cols-2 gap-2">
                            <input 
                              type="text" 
                              required 
                              placeholder="Votre Nom"
                              value={newAuthor}
                              onChange={e => setNewAuthor(e.target.value)}
                              className="p-2 text-xs bg-black/50 border border-white/5 rounded-lg text-white placeholder-slate-600 focus:outline-none"
                            />
                            <input 
                              type="text" 
                              placeholder="Profession"
                              value={newProfession}
                              onChange={e => setNewProfession(e.target.value)}
                              className="p-2 text-xs bg-black/50 border border-white/5 rounded-lg text-white placeholder-slate-600 focus:outline-none"
                            />
                          </div>
                          <textarea 
                            required 
                            rows={3}
                            placeholder="Vos commentaires, critiques, propositions d'amendements..."
                            value={newComment}
                            onChange={e => setNewComment(e.target.value)}
                            className="w-full p-2 text-xs bg-black/50 border border-white/5 rounded-lg text-white placeholder-slate-600 focus:outline-none resize-none"
                          />
                          <button 
                            type="submit"
                            className="w-full py-1.5 bg-teal-500 text-black rounded font-extrabold text-[10px] uppercase tracking-wider hover:bg-teal-400 cursor-pointer"
                          >
                            Soumettre mon observations
                          </button>
                        </form>
                      ) : (
                        <div className="p-3 bg-white/5 border border-white/5 rounded-xl text-center text-[11px] text-slate-500">
                          L'enquête publique pour ce projet est fermée ou en attente d'ouverture réglementaire.
                        </div>
                      )}

                      {/* List reviews */}
                      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                        {(publicReviews[selectedNorm.id] || []).length === 0 ? (
                          <p className="text-[11px] text-slate-600 italic text-center py-4">Aucune observation citoyenne n'a été soumise pour le moment.</p>
                        ) : (
                          (publicReviews[selectedNorm.id] || []).map((rev, idx) => (
                            <div key={idx} className="p-3 bg-black/30 border border-white/5 rounded-lg text-[11px] space-y-1">
                              <div className="flex justify-between items-center flex-wrap gap-1">
                                <span className="font-bold text-slate-300">{rev.author}</span>
                                <span className="text-[9px] text-slate-500 font-mono">{rev.date}</span>
                              </div>
                              <p className="text-[9.5px] text-teal-400 font-semibold">{rev.profession}</p>
                              <p className="text-slate-400 leading-normal italic mt-1 font-sans">
                                "{rev.comment}"
                              </p>
                            </div>
                          ))
                        )}
                      </div>

                    </div>
                  </div>

                </div>

              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </main>

      {/* FOOTER */}
      <footer className="bg-black/90 border-t border-white/5 py-8 px-6 text-center shrink-0">
        <p className="text-[10px] text-slate-500 uppercase tracking-widest leading-relaxed">
          Commission Nationale pour l'Élaboration des Normes (CNETP) • RDC © 2026<br/>
          Portail Public de transparence technique conforme au Manuel d'Organisation et de Co-gouvernance
        </p>
      </footer>
    </div>
  );
}
