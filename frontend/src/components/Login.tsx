import React, { useState } from 'react';
import { apiPost } from '../utils/api/client';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Lock, User, ArrowRight, AlertCircle, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await apiPost('/api/v1/auth/login/', { username, password });
      if (res && res.status === 200) {
        navigate('/app');
      } else {
        setError(res?.message || 'Identifiants invalides ou erreur serveur.');
      }
    } catch (err: any) {
      setError(err?.message || 'Erreur de connexion');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020204] font-sans text-slate-300 relative overflow-hidden flex items-center justify-center p-4">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/10 via-black to-slate-900/20 pointer-events-none" />
      
      {/* Decorative blobs */}
      <div className="absolute top-1/4 -left-1/4 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-1/4 w-[500px] h-[500px] bg-teal-500/5 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-md relative z-10"
      >
        {/* LOGO AREA */}
        <div className="flex flex-col items-center mb-8">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-5 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
          >
            <FileText className="w-8 h-8 text-emerald-400" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white tracking-widest uppercase text-center mb-2">CNETP</h1>
          <p className="text-emerald-500/80 text-[11px] font-bold uppercase tracking-[0.2em] text-center">Portail d'Accès</p>
        </div>

        {/* LOGIN CARD */}
        <div className="bg-[#06060c]/80 border border-white/5 rounded-3xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500/20 via-emerald-400/80 to-teal-500/20" />
          
          <h2 className="text-xl font-bold text-white mb-2">Connexion</h2>
          <p className="text-slate-500 text-xs mb-8">Accès sécurisé pour experts et public.</p>
          
          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0, marginTop: 0 }}
                animate={{ opacity: 1, height: 'auto', marginTop: 16 }}
                exit={{ opacity: 0, height: 0, marginTop: 0 }}
                className="mb-6 overflow-hidden"
              >
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-[11px] font-medium p-3 rounded-lg flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-px text-red-500" />
                  <span>{error}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Nom d'utilisateur</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                  <User className="h-4 w-4" />
                </div>
                <input 
                  type="text"
                  value={username} 
                  onChange={e => setUsername(e.target.value)} 
                  className="block w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                  placeholder="ex: jean_dupont"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-1.5">
              <div className="flex justify-between items-center pl-1 pr-1">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Mot de passe</label>
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input 
                  type="password" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)} 
                  className="block w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium tracking-widest"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div className="flex items-center gap-2 mb-8 pt-2">
              <div className="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
                <Shield className="w-3 h-3 text-emerald-500" />
              </div>
              <span className="text-[11px] text-slate-500 leading-tight">Authentification unifiée (Expert et Public).</span>
            </div>

            <motion.button 
              type="submit" 
              disabled={isLoading || !username || !password}
              className="w-full py-3.5 bg-emerald-500 text-black rounded-xl font-bold uppercase tracking-widest text-xs hover:bg-emerald-400 shadow-[0_4px_20px_rgba(16,185,129,0.2)] hover:shadow-[0_4px_25px_rgba(16,185,129,0.35)] transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 disabled:hover:bg-emerald-500 disabled:shadow-none disabled:cursor-not-allowed"
              whileHover={{ scale: (isLoading || !username || !password) ? 1 : 1.01 }}
              whileTap={{ scale: (isLoading || !username || !password) ? 1 : 0.98 }}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  <span>Connexion...</span>
                </>
              ) : (
                <>
                  S'identifier <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </form>
          
          <div className="mt-8 text-center bg-white/5 -mx-8 -mb-8 p-5 border-t border-white/5">
            <p className="text-[11px] text-slate-400">
              Vous n'avez pas de compte ?{' '}
              <Link to="/auth/register/" className="text-emerald-400 hover:text-emerald-300 font-bold transition-colors uppercase tracking-wider ml-1">
                Créer un profil
              </Link>
            </p>
          </div>
        </div>
        
        <div className="mt-10 text-center opacity-60">
            <p className="text-[9px] text-slate-500 uppercase tracking-widest leading-relaxed">
              République Démocratique du Congo<br/>Ministère des ITPR © 2026
            </p>
        </div>
      </motion.div>
    </div>
  );
}
