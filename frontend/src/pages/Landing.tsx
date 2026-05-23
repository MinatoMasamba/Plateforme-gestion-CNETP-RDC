import React, { useState } from 'react';
import { FileText, Users, BarChart3, Shield, Zap, ArrowRight, Globe, Lock, Briefcase, GraduationCap, Building2, Landmark, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';

/**
 * PAGE D'ACCUEIL - CNETP PLATEFORME
 */
export const Landing: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogin = () => navigate('/auth/login/');
  const handleAppAccess = () => navigate('/app/');

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 50, damping: 15 } }
  };

  const features = [
    {
      icon: <FileText className="w-8 h-8" />,
      title: "Édition Collaborative",
      description: "Travaillez ensemble sur les textes normatifs avec un support d'Intelligence Artificielle et un suivi rigoureux des versions.",
      color: "bg-teal-500/10 text-teal-400 border border-teal-500/20",
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: "Gouvernance Structurée",
      description: "Organisation claire autour de 8 Comités Techniques (CTM) et 24 Groupes de Travail (WG) pour une élaboration démocratique.",
      color: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    },
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: "Transparence & Suivi",
      description: "Vote électronique, émargement numérique et génération automatique de procès-verbaux pour chaque réunion.",
      color: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "Validation & Sécurité",
      description: "Un parcours de validation strict (toilettage, enquête publique, ministère) garantissant la souveraineté et l'intégrité.",
      color: "bg-pink-500/10 text-pink-400 border border-pink-500/20",
    },
  ];

  const modules = [
    { icon: <Globe className="w-8 h-8" />, name: "Bibliothèque Publique", desc: "Accédez aux normes officielles publiées, participez aux enquêtes publiques ou téléchargez les textes homologués.", color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
    { icon: <FileText className="w-8 h-8" />, name: "Éditeur de Normes", desc: "L'atelier de rédaction où les experts débattent, amendent et finalisent le corps technique des normes.", color: "text-teal-400 bg-teal-500/10 border-teal-500/20" },
    { icon: <Users className="w-8 h-8" />, name: "Réseau d'Experts", desc: "Un annuaire exclusif regroupant les plus grands ingénieurs, chercheurs et légistes de la nation.", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    { icon: <BarChart3 className="w-8 h-8" />, name: "Réunions & Scrutins", desc: "Gérez les convocations, les quorums, et lancez des scrutins officiels à majorité qualifiée en un clic.", color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
    { icon: <Lock className="w-8 h-8" />, name: "Bureau Légistique", desc: "Espace réservé à la vérification juridique pour garantir que chaque terme respecte la législation en vigueur.", color: "text-pink-400 bg-pink-500/10 border-pink-500/20" },
    { icon: <Zap className="w-8 h-8" />, name: "Gestion & Allocations", desc: "Suivi des cotisations institutionnelles et automatisation du paiement des jetons de présence pour les experts.", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  ];

  const profiles = [
    {
      icon: <Briefcase className="w-10 h-10 mb-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-xl border border-emerald-500/20" />,
      title: "Experts & Ingénieurs",
      reason: "Pour co-rédiger les standards, influencer la réglementation technique et valoriser votre expertise au sein de comités prestigieux de niveau national."
    },
    {
      icon: <GraduationCap className="w-10 h-10 mb-4 text-purple-400 bg-purple-500/10 p-2 rounded-xl border border-purple-500/20" />,
      title: "Universités & Chercheurs",
      reason: "Pour connecter la recherche académique au monde industriel, et s'assurer que les normes nationales reflètent l'état de l'art scientifique."
    },
    {
      icon: <Building2 className="w-10 h-10 mb-4 text-indigo-400 bg-indigo-500/10 p-2 rounded-xl border border-indigo-500/20" />,
      title: "Industries & Entreprises",
      reason: "Pour anticiper les nouvelles réglementations, participer aux enquêtes publiques, et garantir la pleine conformité légale de vos réalisations."
    },
    {
      icon: <Landmark className="w-10 h-10 mb-4 text-pink-400 bg-pink-500/10 p-2 rounded-xl border border-pink-500/20" />,
      title: "Institutions Publiques",
      reason: "Pour superviser l'élaboration des textes de loi, valider leur homologation et piloter la stratégie normative pour le développement du pays."
    }
  ];

  const stats = [
    { number: "25+", label: "Normes Éditées", icon: "📚" },
    { number: "200", label: "Experts Actifs", icon: "👥" },
    { number: "8", label: "Comités (CTM)", icon: "📊" },
    { number: "24", label: "Groupes (WG)", icon: "🎯" },
  ];

  return (
    <div className="w-full min-h-screen bg-[#06060c] text-slate-300 relative z-0 overflow-hidden font-sans">
      <div className="absolute inset-0 bg-gradient-to-br from-teal-900/10 via-black to-slate-900/20 pointer-events-none" />

      {/* NAVBAR */}
      <motion.nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? 'bg-black/60 backdrop-blur-xl border-b border-white/5 py-2' : 'bg-transparent py-4'
        }`}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 50, damping: 15 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-12">
            <motion.div className="flex items-center gap-3 cursor-pointer" whileHover={{ scale: 1.05 }} onClick={handleAppAccess}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-teal-500/20 border border-teal-500/30">
                <FileText className="w-4 h-4 text-teal-400" />
              </div>
              <span className="text-xl font-bold text-white tracking-widest">CNETP</span>
            </motion.div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-xs font-bold tracking-wider uppercase text-slate-400 hover:text-white transition-colors">
                La Plateforme
              </a>
              <a href="#modules" className="text-xs font-bold tracking-wider uppercase text-slate-400 hover:text-white transition-colors">
                Modules
              </a>
              <a href="#audience" className="text-xs font-bold tracking-wider uppercase text-slate-400 hover:text-white transition-colors">
                Pour Qui ?
              </a>
            </div>
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleLogin}
                className="px-4 py-2 text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-teal-400 transition-colors pointer-cursor"
              >
                Se Connecter
              </button>
              <motion.button
                type="button"
                onClick={handleAppAccess}
                className="px-5 py-2.5 bg-teal-500 text-black rounded font-bold uppercase tracking-wider text-xs hover:bg-teal-400 flex items-center gap-2 shadow-[0_0_15px_rgba(20,184,166,0.3)] pointer-cursor"
                whileHover={{ scale: 1.05, boxShadow: "0 0 25px rgba(20,184,166,0.5)" }}
                whileTap={{ scale: 0.95 }}
              >
                Accès <ArrowRight className="w-3.5 h-3.5" />
              </motion.button>
            </div>
          </div>
        </div>
      </motion.nav>

      {/* HERO SECTION */}
      <section className="pt-40 pb-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center"
            initial={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <motion.div 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[10px] font-bold uppercase tracking-widest mb-8"
            >
              <Zap className="w-3.5 h-3.5" />
              Plateforme Ouverte • officielle
            </motion.div>
            
            <h1 className="text-5xl sm:text-7xl font-bold text-white mb-8 leading-[1.1] tracking-tight">
              Centraliser la Création des <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-300">Normes Nationales</span>
            </h1>
            
            <p className="text-lg sm:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
              Une plateforme souveraine pour orchestrer la rédaction, la validation et la publication de normes techniques, en réunissant l'élite scientifique et industrielle du pays.
            </p>
            
            <motion.div
              className="flex gap-4 justify-center flex-wrap"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <motion.button
                type="button"
                onClick={handleAppAccess}
                className="px-8 py-4 bg-teal-500 text-black rounded font-bold uppercase tracking-widest text-xs hover:bg-teal-400 shadow-[0_0_20px_rgba(20,184,166,0.4)] flex items-center gap-2"
                whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(20,184,166,0.6)" }}
                whileTap={{ scale: 0.95 }}
              >
                Accéder à l'Espace de Travail <ArrowRight className="w-4 h-4" />
              </motion.button>
              <motion.button
                type="button"
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="px-8 py-4 bg-white/5 text-white border border-white/10 rounded font-bold uppercase tracking-widest text-xs hover:bg-white/10"
                whileHover={{ scale: 1.05, backgroundColor: "rgba(255,255,255,0.1)" }}
                whileTap={{ scale: 0.95 }}
              >
                Découvrir le Fonctionnement
              </motion.button>
            </motion.div>
          </motion.div>

          {/* STATS */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {stats.map((stat, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                className="bg-black/40 rounded-2xl p-6 border border-white/5 backdrop-blur-md text-center hover:border-teal-500/30 transition-colors duration-300"
              >
                <div className="text-3xl mb-3 opacity-90">{stat.icon}</div>
                <div className="text-4xl font-black text-white">{stat.number}</div>
                <div className="text-teal-500 text-[10px] uppercase tracking-wider font-bold mt-2">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* POURQUOI / FONCTIONNALITES (FEATURES) */}
      <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 relative z-10 border-t border-white/5 bg-black/20">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-white tracking-wider mb-4">
              L'AVENIR DE LA NORMALISATION
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-sm">
              Fini les documents perdus, les échanges par e-mail interminables et les procédures opaques. 
              La plateforme centralise et certifie chaque étape de création d'une norme.
            </p>
          </motion.div>

          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                className={`rounded-2xl p-8 bg-black/50 border border-white/5 shadow-2xl backdrop-blur-sm group`}
                whileHover={{ y: -5, borderColor: 'rgba(20,184,166,0.2)' }}
              >
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110 ${feature.color}`}>
                  {feature.icon}
                </div>
                <h3 className="text-sm font-bold mb-3 text-white">{feature.title}</h3>
                <p className="text-slate-500 text-xs leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* MODULES (FONCTIONNEMENT) */}
      <section id="modules" className="py-24 px-4 sm:px-6 lg:px-8 relative z-10 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-white tracking-wider mb-4">
              DES OUTILS SUR-MESURE
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-sm">
              Six modules interconnectés couvrant l'ensemble des besoins administratifs, 
              financiers, légaux et collaboratifs de votre gouvernance.
            </p>
          </motion.div>

          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {modules.map((mod, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                className="group bg-black/40 rounded-2xl p-8 border border-white/5 hover:bg-white/5 transition-all backdrop-blur-sm cursor-pointer"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 border transition-all duration-300 group-hover:shadow-[0_0_15px_currentColor] ${mod.color}`}>
                  {mod.icon}
                </div>
                <h3 className="text-sm font-bold text-white mb-2 group-hover:text-teal-400 transition-colors">{mod.name}</h3>
                <p className="text-slate-500 text-xs leading-relaxed">{mod.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* AUDIENCE : QUI PEUT S'INSCRIRE ET POURQUOI */}
      <section id="audience" className="py-32 px-4 sm:px-6 lg:px-8 relative z-10 border-t border-white/5 bg-gradient-to-t from-teal-950/20 to-black/20">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
            className="text-center mb-20"
          >
            <h2 className="text-3xl font-bold text-white tracking-wider mb-4 uppercase">
              Qui Devrait S'Inscrire ?
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto text-sm">
              La plateforme est un espace professionnel sécurisé nécessitant une accréditation. 
              Elle rassemble les acteurs majeurs du développement technique national.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <AnimatePresence>
              {profiles.map((profile, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-100px" }}
                  transition={{ delay: i * 0.1, type: "spring", stiffness: 60 }}
                  className="flex flex-col sm:flex-row gap-6 bg-black/60 border border-white/5 p-8 rounded-2xl hover:border-teal-500/20 transition-colors"
                >
                  <div className="shrink-0">
                    {profile.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white mb-3">{profile.title}</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      {profile.reason}
                    </p>
                    <div className="mt-4 flex items-center gap-2 text-[10px] uppercase tracking-widest text-teal-500 font-bold">
                      <CheckCircle2 className="w-3 h-3" /> Accès sur accréditation
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 relative z-10 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 40 }}
          >
            <h2 className="text-4xl sm:text-5xl font-bold mb-6 text-white tracking-tight">
              Intégrez le Cercle d'Excellence
            </h2>
            <p className="text-slate-400 mb-10 text-lg">
              Devenez acteur de la standardisation nationale. Publiez des textes qui façonneront l'avenir technique de nos infrastructures et industries.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <motion.button
                type="button"
                onClick={handleLogin}
                className="px-8 py-4 bg-teal-500 text-black rounded font-bold uppercase tracking-widest text-xs hover:bg-teal-400 shadow-[0_0_20px_rgba(20,184,166,0.3)] flex items-center gap-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Se Connecter <ArrowRight className="w-4 h-4" />
              </motion.button>
              <motion.button
                type="button"
                onClick={handleAppAccess}
                className="px-8 py-4 bg-white/5 text-white border border-white/10 rounded font-bold uppercase tracking-widest text-xs hover:bg-white/10"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Naviguer sur la Plateforme
              </motion.button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-black/90 border-t border-white/5 py-12 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Plateforme</h3>
              <ul className="space-y-3 text-xs text-slate-400">
                <li><a href="#" className="hover:text-teal-400 transition-colors">Fonctionnalités de l'Éditeur</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Bibliothèque des Normes</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Portail Enquête Publique</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Ressources</h3>
              <ul className="space-y-3 text-xs text-slate-400">
                <li><a href="#" className="hover:text-teal-400 transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Manuel Opérationnel</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Assistance Technique</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Légal</h3>
              <ul className="space-y-3 text-xs text-slate-400">
                <li><a href="#" className="hover:text-teal-400 transition-colors">Mentions Légales</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Politique de Confidentialité</a></li>
                <li><a href="#" className="hover:text-teal-400 transition-colors">Conditions d'Accréditation</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Contact</h3>
              <ul className="space-y-3 text-xs text-slate-400">
                <li className="flex items-center gap-2">support@cnetp.cd</li>
                <li className="flex items-center gap-2">+243 81 234 56 78</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/5 pt-8 flex justify-between items-center flex-wrap gap-4">
            <p className="text-xs text-slate-500">&copy; 2026 CNETP. Tous droits réservés.</p>
            <div className="flex items-center gap-6 text-xs text-slate-500">
              <a href="#" className="hover:text-teal-400 transition-colors">Twitter</a>
              <a href="#" className="hover:text-teal-400 transition-colors">LinkedIn</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
