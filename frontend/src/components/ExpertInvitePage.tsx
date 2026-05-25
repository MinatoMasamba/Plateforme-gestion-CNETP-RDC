import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Mail, Shield, User, Lock, Award, ArrowRight, AlertCircle, CheckCircle2, ChevronRight, Landmark, Building2, Phone, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Invitee {
  email: string;
  name: string;
  ctm: string;
  wg: string;
  structure: string;
  province: string;
}

const INVITEES_SEED: Invitee[] = [
  {
    email: "edmasamba100@gmail.com",
    name: "Prof. Masamba Édouard",
    ctm: "CTM 8 – Sciences des Matériaux, Métrologie et Valorisation Locale",
    wg: "WG 8.1 : Matériaux de Construction Locaux",
    structure: "Université de Kinshasa (UNIKIN)",
    province: "Kinshasa"
  },
  {
    email: "chantal.mwamba@cnetp.cd",
    name: "Ir. Chantal Mwamba",
    ctm: "CTM 5 – Infrastructures de Transport Linéaire et Maritimes",
    wg: "WG 5.1 : Ingénierie Routière",
    structure: "Office des Voiries et Drainage (OVD)",
    province: "Haut-Katanga"
  },
  {
    email: "sylvain.l@workspace.org",
    name: "Arch. Sylvain Lukusa",
    ctm: "CTM 3 – Bâtiment, Urbanisme et Transition Numérique",
    wg: "WG 3.2 : BIM & Numérisation (ISO 19650)",
    structure: "Ordre National des Architectes (ONA)",
    province: "Lualaba"
  },
  {
    email: "g.munongo@sogert.cd",
    name: "Ir. Godefroid Munongo",
    ctm: "CTM 1 – Géotechnique et Risques Naturels",
    wg: "WG 1.2 : Sols Tropicaux & Ferrallitiques",
    structure: "Office des Routes (OR)",
    province: "Nord-Kivu"
  }
];

export default function ExpertInvitePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Use email from query string if present, otherwise default to first seed
  const initialEmail = searchParams.get("email") || "";
  
  const [activeStep, setActiveStep] = useState<"mailbox" | "form" | "success">(() => {
    return initialEmail ? "form" : "mailbox";
  });
  
  const [selectedEmail, setSelectedEmail] = useState(initialEmail || INVITEES_SEED[0].email);
  const [customEmail, setCustomEmail] = useState("");
  const [useCustom, setUseCustom] = useState(false);

  // Form Fields
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [structure, setStructure] = useState("");
  const [ctm, setCtm] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Find selected active invitee details
  const currentInvitee = useCustom 
    ? {
        email: customEmail || "expert@custom.cd",
        name: name || "Expert Invité",
        ctm: ctm || "CTM 8 - Valorisation Locale",
        wg: "WG Spécialisé",
        structure: structure || "Institution Extérieure",
        province: "Kinshasa"
      }
    : INVITEES_SEED.find(i => i.email === selectedEmail) || INVITEES_SEED[0];

  // Initialize form on step change or email change
  React.useEffect(() => {
    if (currentInvitee) {
      setName(currentInvitee.name);
      setStructure(currentInvitee.structure);
      setCtm(currentInvitee.ctm);
    }
  }, [selectedEmail, useCustom, activeStep]);

  const handleStartForm = (invitee: Invitee) => {
    setSelectedEmail(invitee.email);
    setUseCustom(false);
    setActiveStep("form");
  };

  const handleStartCustomForm = () => {
    if (!customEmail) {
      setGeneralError("Veuillez entrer une adresse e-mail valide pour simuler.");
      return;
    }
    setUseCustom(true);
    setGeneralError(null);
    setActiveStep("form");
  };

  const handleActivateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);
    setPasswordError("");

    if (!username) {
      setGeneralError("Veuillez choisir un nom d'utilisateur unique.");
      return;
    }

    if (password !== passwordConfirm) {
      setPasswordError("Les mots de passe ne correspondent pas.");
      return;
    }

    if (password.length < 6) {
      setPasswordError("Le mot de passe doit comporter au moins 6 caractères.");
      return;
    }

    setIsLoading(true);

    try {
      // Simulate API call delay to simulate database register integration
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Store in local storage to preserve this newly activated expert so they can log in
      const activatedExperts = JSON.parse(localStorage.getItem("cnetp_active_experts") || "[]");
      activatedExperts.push({
        username,
        password,
        email: currentInvitee.email,
        name: name,
        structure: structure,
        ctm: ctm,
        role: "Membre Permanent (Expert)"
      });
      localStorage.setItem("cnetp_active_experts", JSON.stringify(activatedExperts));

      setActiveStep("success");
    } catch (err: any) {
      setGeneralError("Une erreur s'est produite lors de l'enregistrement de vos accès.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020204] font-sans text-slate-300 relative overflow-hidden flex items-center justify-center p-4 sm:p-6">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-950/15 via-black to-slate-900/15 pointer-events-none" />
      
      {/* Dynamic blobs */}
      <div className="absolute top-1/4 -left-1/4 w-[500px] h-[500px] bg-indigo-500/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-1/4 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-2xl relative z-10 my-8">
        
        {/* LOGO AREA */}
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4 shadow-[0_0_30px_rgba(99,102,241,0.15)]">
            <Mail className="w-7 h-7 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-widest uppercase text-center mb-1">CNETP</h1>
          <p className="text-indigo-400 text-[10px] font-bold uppercase tracking-[0.2em] text-center">Portail d'Activation d'Accréditation</p>
        </div>

        {/* CONTAINER SHELL */}
        <div className="bg-[#06060c]/80 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500/20 via-indigo-400 to-emerald-500/20" />

          <AnimatePresence mode="wait">
            
            {/* STEP 1: MAILBOX / EMAIL SIMULATION */}
            {activeStep === "mailbox" && (
              <motion.div
                key="mailbox"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div>
                  <h2 className="text-lg font-bold text-white mb-1">Activation pour Expert CNETP</h2>
                  <p className="text-xs text-slate-400 leading-normal">
                    Conformément au Manuel d'Organisation, les experts ne créent pas leur compte publiquement. Ils reçoivent une notification gouvernementale par courriel avec un jeton d'invitation nominatif verrouillé.
                  </p>
                </div>

                {/* Email Interface Simulation Card */}
                <div className="bg-black/60 border border-white/10 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center gap-2 text-xs text-slate-500 border-b border-white/5 pb-2">
                    <span className="h-2 w-2 rounded-full bg-red-400 inline-block"></span>
                    <span className="h-2 w-2 rounded-full bg-yellow-400 inline-block"></span>
                    <span className="h-2 w-2 rounded-full bg-green-400 inline-block"></span>
                    <span className="font-mono text-[10px] ml-2 text-slate-400 uppercase tracking-widest">Générateur d'emails d'invitation :</span>
                  </div>

                  <p className="text-[11px] text-slate-400 block font-bold leading-normal">
                    Sélectionnez un email ci-dessous pour simuler l'ouverture du lien recu par e-mail :
                  </p>

                  {/* Seed invitations list */}
                  <div className="space-y-2.5">
                    {INVITEES_SEED.map(inv => (
                      <button
                        key={inv.email}
                        type="button"
                        onClick={() => handleStartForm(inv)}
                        className="w-full text-left p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] transition-all text-xs flex justify-between items-center group cursor-pointer"
                      >
                        <div className="space-y-1">
                          <p className="text-[10px] text-indigo-400 font-mono font-bold uppercase">{inv.structure}</p>
                          <p className="font-bold text-white group-hover:text-indigo-300 transition-colors">{inv.name}</p>
                          <p className="text-slate-500 text-[11px]">{inv.email}</p>
                        </div>
                        <div className="h-7 w-7 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500 group-hover:text-black transition-all">
                          <ChevronRight className="h-4 w-4" />
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Custom email Simulation input */}
                  <div className="pt-4 border-t border-white/5 space-y-2.5">
                    <p className="text-[11px] font-bold text-slate-400">Ou simuler avec votre adresse e-mail personnalisée :</p>
                    {generalError && <p className="text-xs text-red-400 font-bold mb-2 flex items-center gap-1"><AlertCircle className="h-3.5 w-3.5" />{generalError}</p>}
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Mail className="h-4 w-4 text-slate-500 absolute left-3 top-2.5" />
                        <input
                          type="email"
                          placeholder="votre-adresse-email@domaine.cd"
                          value={customEmail}
                          onChange={e => setCustomEmail(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-3 py-2.5 text-xs text-white focus:outline-none"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleStartCustomForm}
                        className="px-4 py-2.5 bg-indigo-500 text-black rounded-xl font-bold uppercase tracking-wider text-xs hover:bg-indigo-400 shrink-0 cursor-pointer"
                      >
                        Simuler
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* STEP 2: EXPERT PROFILE ACTIVATION & PASSWORD FORM */}
            {activeStep === "form" && (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center pb-3 border-b border-white/10">
                  <div>
                    <h2 className="text-lg font-bold text-white mb-0.5">Compléter votre Profil d'Expert</h2>
                    <p className="text-xs text-slate-500">
                      Veuillez inscrire vos accréditations fédérales et choisir vos identifiants d'accès.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setGeneralError(null);
                      setActiveStep("mailbox");
                    }}
                    className="text-xs text-slate-500 hover:text-white"
                  >
                    Changer l'adresse d'invitation
                  </button>
                </div>

                <div className="p-4 bg-indigo-500/5 border border-indigo-500/15 rounded-2xl text-xs space-y-2 relative">
                  <div className="absolute top-3 right-3 text-indigo-400 font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-[9px] uppercase tracking-wider font-mono border border-indigo-500/20">
                    JETON D'ACTIVATION VALIDE
                  </div>
                  <p className="font-bold text-slate-300">Invitation ITPR associée :</p>
                  <p className="text-[11px] text-indigo-400 font-mono">{currentInvitee.email}</p>
                  <p className="text-[10px] text-slate-500 leading-relaxed block pt-1 border-t border-white/5">
                    <strong>CTM visé:</strong> {currentInvitee.ctm} • <strong>Groupe:</strong> {currentInvitee.wg}
                  </p>
                </div>

                {generalError && (
                  <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-px text-red-500" />
                    <span>{generalError}</span>
                  </div>
                )}

                <form onSubmit={handleActivateProfile} className="space-y-4">
                  {/* IDENTIFIANTS PERSONNEL */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Nom Complet d'Expert</label>
                      <input
                        type="text"
                        required
                        value={name}
                        onChange={e => setName(e.target.value)}
                        className="w-full p-2.5 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                        placeholder="Dr. Jean Dupont"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Téléphone Mobile</label>
                      <div className="relative">
                        <Phone className="h-3.5 w-3.5 text-slate-500 absolute left-3.5 top-3.5" />
                        <input
                          type="tel"
                          required
                          value={phone}
                          onChange={e => setPhone(e.target.value)}
                          className="w-full p-2.5 pl-9 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none"
                          placeholder="+243 ..."
                        />
                      </div>
                    </div>
                  </div>

                  {/* STRUCTURES DE PROVENANCE */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Structure d'Origine (Giron)</label>
                      <div className="relative">
                        <Building2 className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-3.5" />
                        <input
                          type="text"
                          required
                          value={structure}
                          onChange={e => setStructure(e.target.value)}
                          className="w-full p-2.5 pl-8 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none"
                          placeholder="ex: Office des Routes"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Décret de Nomination (Optionnel)</label>
                      <input
                        type="text"
                        className="w-full p-2.5 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none"
                        placeholder="N° 2026/ITPR/04"
                      />
                    </div>
                  </div>

                  {/* IDENTIFIANTS COMPTE SECURISE */}
                  <div className="pt-4 border-t border-white/5 space-y-4">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Shield className="h-4 w-4 text-indigo-400" />
                      Créer vos accès utilisateur sécurisés
                    </h3>

                    {/* Username Choice */}
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Nom d'Utilisateur (Username)</label>
                      <div className="relative">
                        <User className="h-4 w-4 text-slate-500 absolute left-3 top-3" />
                        <input
                          type="text"
                          required
                          value={username}
                          onChange={e => setUsername(e.target.value.toLowerCase().trim())}
                          className="w-full p-2.5 pl-9 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 font-semibold"
                          placeholder="Nom d'utilisateur d'expert (ex: j_dupont)"
                        />
                      </div>
                    </div>

                    {/* Passwords Input */}
                    {passwordError && <p className="text-xs text-red-400 font-bold flex items-center gap-1"><AlertCircle className="h-3.5 w-3.5" />{passwordError}</p>}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Créer Mot de passe</label>
                        <div className="relative">
                          <Lock className="h-4 w-4 text-slate-500 absolute left-3 top-3" />
                          <input
                            type="password"
                            required
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="w-full p-2.5 pl-9 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 tracking-widest"
                            placeholder="••••••••"
                          />
                        </div>
                      </div>

                      <div className="space-y-1">
                        <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Confirmer Mot de passe</label>
                        <div className="relative">
                          <Lock className="h-4 w-4 text-slate-500 absolute left-3 top-3" />
                          <input
                            type="password"
                            required
                            value={passwordConfirm}
                            onChange={e => setPasswordConfirm(e.target.value)}
                            className="w-full p-2.5 pl-9 text-xs bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 tracking-widest"
                            placeholder="••••••••"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 flex items-center gap-2 text-[10px] text-slate-500 uppercase tracking-wider font-mono">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
                    Ce profil sera validé dans l'organigramme fédéral (200 postes CNETP).
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      disabled={isLoading || !username || !password || !passwordConfirm}
                      className="w-full py-3.5 bg-indigo-500 text-black hover:bg-indigo-400 font-extrabold uppercase tracking-widest text-xs rounded-xl shadow-[0_4px_25px_rgba(99,102,241,0.25)] flex items-center justify-center gap-2 transform active:scale-98 disabled:opacity-50 cursor-pointer"
                    >
                      {isLoading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                          Enregistrement...
                        </>
                      ) : (
                        <>
                          Activer mon Profil d'Expert <ArrowRight className="h-4 w-4" />
                        </>
                      )}
                    </button>
                  </div>

                </form>
              </motion.div>
            )}

            {/* STEP 3: CONGRATS / ACTIVATION SUCCESS */}
            {activeStep === "success" && (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="text-center py-6 space-y-6"
              >
                <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto shadow-[0_0_40px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 animate-bounce" />
                </div>

                <div className="space-y-2">
                  <h2 className="text-xl font-extrabold text-white">Félicitations Expert !</h2>
                  <p className="text-emerald-400 text-xs font-bold font-mono uppercase tracking-widest">
                    Compte et profil d'expert activés avec succès
                  </p>
                  <p className="text-slate-400 text-xs max-w-md mx-auto leading-relaxed">
                    Votre nomination technique a été validée dans la base de données CNETP. Vous pouvez désormais vous connecter en utilisant le nom d'utilisateur et le mot de passe que vous venez de créer.
                  </p>
                </div>

                <div className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl max-w-sm mx-auto text-xs text-slate-400 space-y-1 text-left">
                  <p><strong>Expert accrédité :</strong> {name}</p>
                  <p><strong>Identifiant :</strong> <code className="text-indigo-400 font-mono font-bold">{username}</code></p>
                  <p><strong>E-mail :</strong> {currentInvitee.email}</p>
                  <p><strong>Structure rattachée :</strong> {structure}</p>
                  <p><strong>Comité Technique :</strong> {ctm}</p>
                </div>

                <div className="pt-4 max-w-sm mx-auto">
                  <button
                    type="button"
                    onClick={() => {
                      // Navigate to login and pass the username so it's pre-filled
                      navigate("/auth/login/", { state: { prefilledUsername: username } });
                    }}
                    className="w-full py-3.5 bg-emerald-500 text-black hover:bg-emerald-400 font-extrabold uppercase tracking-widest text-xs rounded-xl flex items-center justify-center gap-2 cursor-pointer shadow-lg"
                  >
                    Aller s'identifier <ArrowRight className="h-4 w-4" />
                  </button>
                </div>

              </motion.div>
            )}

          </AnimatePresence>

        </div>

        <div className="mt-8 text-center opacity-60">
            <p className="text-[9px] text-slate-500 uppercase tracking-widest leading-relaxed">
              Ministère des Infrastructures et Travaux Publics • RDC © 2026<br/>
              Procédure d'accréditation nominative sécurisée en concertation avec la CTC.
            </p>
        </div>

      </div>
    </div>
  );
}
