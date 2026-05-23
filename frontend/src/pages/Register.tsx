import React, { useState } from 'react';
import { apiPost } from '../utils/api/client';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Lock, ArrowRight, AlertCircle, FileText, Type, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (password !== password2) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await apiPost('/api/v1/auth/register/', { 
        username, 
        email, 
        first_name: firstName, 
        last_name: lastName, 
        password, 
        password2, 
        phone 
      });
      
      if (res && res.status === 201) {
        navigate('/auth/login/');
      } else {
        setError(res?.message || JSON.stringify(res?.error) || 'Erreur lors de l\'inscription');
      }
    } catch (err: any) {
      setError(err?.message || 'Erreur lors de la création du compte.');
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
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-lg relative z-10 my-8"
      >
        {/* LOGO AREA */}
        <div className="flex flex-col items-center mb-6">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
          >
            <FileText className="w-6 h-6 text-emerald-400" />
          </motion.div>
          <h1 className="text-2xl font-bold text-white tracking-widest uppercase text-center mb-1">CNETP</h1>
          <p className="text-emerald-500/80 text-[10px] font-bold uppercase tracking-[0.2em] text-center">Bureau d'Accès Public</p>
        </div>

        {/* REGISTER CARD */}
        <div className="bg-[#06060c]/80 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500/20 via-emerald-400/80 to-teal-500/20" />
          
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-1">Créer un compte</h2>
            <p className="text-slate-500 text-xs">Rejoignez le portail de consultation publique des normes.</p>
          </div>
          
          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                animate={{ opacity: 1, height: 'auto', marginBottom: 20 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                className="overflow-hidden"
              >
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-[11px] font-medium p-3 rounded-lg flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-px text-red-500" />
                  <span>{error}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* ROW 1: Username & Email */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Utilisateur</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <User className="h-4 w-4" />
                  </div>
                  <input 
                    type="text"
                    value={username} 
                    onChange={e => setUsername(e.target.value)} 
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                    placeholder="Pseudo"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Email</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input 
                    type="email"
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                    placeholder="nom@exemple.cd"
                    required
                  />
                </div>
              </div>
            </div>

            {/* ROW 2: First Name & Last Name */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Prénom</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <Type className="h-4 w-4" />
                  </div>
                  <input 
                    type="text"
                    value={firstName} 
                    onChange={e => setFirstName(e.target.value)} 
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                    placeholder="Prénom"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Nom</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <Type className="h-4 w-4" />
                  </div>
                  <input 
                    type="text"
                    value={lastName} 
                    onChange={e => setLastName(e.target.value)} 
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                    placeholder="Nom"
                  />
                </div>
              </div>
            </div>

            {/* ROW 3: Phone */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Téléphone</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                  <Phone className="h-4 w-4" />
                </div>
                <input 
                  type="tel"
                  value={phone} 
                  onChange={e => setPhone(e.target.value)} 
                  className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium"
                  placeholder="+243 ..."
                />
              </div>
            </div>

            {/* ROW 4: Passwords */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Mot de passe</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input 
                    type="password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/40 transition-all text-sm font-medium tracking-widest"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400 pl-1">Confirmer mot de passe</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors group-focus-within:text-emerald-400 text-slate-500">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <input 
                    type="password" 
                    value={password2} 
                    onChange={e => setPassword2(e.target.value)} 
                    className={`block w-full pl-10 pr-3 py-2.5 bg-white/5 border rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 transition-all text-sm font-medium tracking-widest ${password && password2 && password !== password2 ? 'border-red-500/50 focus:ring-red-500/40 focus:border-red-500/40' : 'border-white/10 focus:ring-emerald-500/40 focus:border-emerald-500/40'}`}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="pt-4">
              <motion.button 
                type="submit" 
                disabled={isLoading || !username || !email || !password || !password2}
                className="w-full py-3.5 bg-emerald-500 text-black rounded-xl font-bold uppercase tracking-widest text-xs hover:bg-emerald-400 shadow-[0_4px_20px_rgba(16,185,129,0.2)] hover:shadow-[0_4px_25px_rgba(16,185,129,0.35)] transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 disabled:hover:bg-emerald-500 disabled:shadow-none disabled:cursor-not-allowed"
                whileHover={{ scale: (isLoading || !username || !email || !password || !password2) ? 1 : 1.01 }}
                whileTap={{ scale: (isLoading || !username || !email || !password || !password2) ? 1 : 0.98 }}
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    <span>Création...</span>
                  </>
                ) : (
                  <>
                    S'inscrire <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </motion.button>
            </div>
          </form>
          
          <div className="mt-8 text-center bg-white/5 -mx-6 sm:-mx-8 -mb-6 sm:-mb-8 p-5 border-t border-white/5">
            <p className="text-[11px] text-slate-400">
              Déjà un compte ?{' '}
              <Link to="/auth/login/" className="text-emerald-400 hover:text-emerald-300 font-bold transition-colors uppercase tracking-wider ml-1">
                Se Connecter
              </Link>
            </p>
          </div>
        </div>
        
        <div className="mt-8 text-center opacity-60">
            <p className="text-[9px] text-slate-500 uppercase tracking-widest leading-relaxed">
              * Ce formulaire est réservé aux consultations publiques.<br/>Pour une accréditation en tant qu'Expert, contactez l'administration.
            </p>
        </div>
      </motion.div>
    </div>
  );
}
