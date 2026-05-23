import React, { useState, useEffect } from "react";
import { 
  X, 
  Shield, 
  User, 
  Mail, 
  Building2, 
  Coins, 
  TrendingUp, 
  Wallet2, 
  Check, 
  Info,
  Award,
  CalendarRange
} from "lucide-react";

interface ProfileSimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: {
    name: string;
    email: string;
    structure: string;
    roleId: string;
    dailyRate: number;
    monthlyResearchAllowance: number;
    payoutMethod: "M-Pesa" | "Orange Money" | "Airtel Money" | "Rawbank" | "Equity BCDC";
    accountDetails: string;
    presenceCount: number;
  };
  onSave: (updatedProfile: any) => void;
}

export default function ProfileSimulationModal({
  isOpen,
  onClose,
  profile,
  onSave
}: ProfileSimulationModalProps) {
  // Local transient state for editing form
  const [name, setName] = useState(profile.name);
  const [email, setEmail] = useState(profile.email);
  const [structure, setStructure] = useState(profile.structure);
  const [roleId, setRoleId] = useState(profile.roleId);
  const [dailyRate, setDailyRate] = useState(profile.dailyRate);
  const [monthlyResearchAllowance, setMonthlyResearchAllowance] = useState(profile.monthlyResearchAllowance);
  const [payoutMethod, setPayoutMethod] = useState(profile.payoutMethod);
  const [accountDetails, setAccountDetails] = useState(profile.accountDetails);
  const [presenceCount, setPresenceCount] = useState(profile.presenceCount);

  // Sync edits when input modal opens/changes profile
  useEffect(() => {
    if (isOpen) {
      setName(profile.name);
      setEmail(profile.email);
      setStructure(profile.structure);
      setRoleId(profile.roleId);
      setDailyRate(profile.dailyRate);
      setMonthlyResearchAllowance(profile.monthlyResearchAllowance);
      setPayoutMethod(profile.payoutMethod);
      setAccountDetails(profile.accountDetails);
      setPresenceCount(profile.presenceCount);
    }
  }, [isOpen, profile]);

  if (!isOpen) return null;

  const CNETP_ROLES_DETAILED = [
    { 
      id: "ADMIN", 
      name: "Administrateur technique", 
      desc: "Supervision complète du système CNETP", 
      power: "Accès à tous les outils et configuration générale",
      colorClass: "border-red-500/30 bg-red-500/5 text-red-400"
    },
    { 
      id: "RAP_CTM", 
      name: "Rapporteur CTM (ONIC)", 
      desc: "Gestion de l'émargement et certification du procès-verbal", 
      power: "Habilité à modifier les présences, clore les scrutins de vote et valider le PV",
      colorClass: "border-amber-500/30 bg-amber-500/5 text-amber-400"
    },
    { 
      id: "SEC_PERM", 
      name: "Secrétaire Permanent (SG)", 
      desc: "Lancement des convocations officielles et ordonnancement", 
      power: "Habilité à initier de nouvelles sessions de vote et éditer l'émargement",
      colorClass: "border-blue-500/30 bg-blue-500/5 text-blue-400"
    },
    { 
      id: "PRES_CTM", 
      name: "Président du CTM", 
      desc: "Arbitrage technique de haut niveau et validations de conformité", 
      power: "Rôle de décision scientifique et dépôt d'observations de blocage",
      colorClass: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400"
    },
    { 
      id: "GEST_COMP", 
      name: "Comptable Principal (FONER)", 
      desc: "Liquidation des indemnités d'experts et collecte des structures co-financeurs", 
      power: "Accès total au portail financier, génération des virements ISO-20022",
      colorClass: "border-purple-500/30 bg-purple-500/5 text-purple-400"
    },
    { 
      id: "COORD_CTC", 
      name: "Coordonnateur CTC", 
      desc: "Pilotage général et rapporteur de synthèse", 
      power: "Consultation et supervision globale des indicateurs financiers",
      colorClass: "border-pink-500/30 bg-pink-500/5 text-pink-400"
    },
    { 
      id: "MEMBRE_P", 
      name: "Membre Permanent (Expert)", 
      desc: "Expert thématique en charge d'amender et voter les projets de normes", 
      power: "Visualisation de son propre espace d'indemnités personnelles de test",
      colorClass: "border-slate-500/30 bg-slate-500/5 text-slate-300"
    }
  ];

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      name,
      email,
      structure,
      roleId,
      dailyRate: Number(dailyRate),
      monthlyResearchAllowance: Number(monthlyResearchAllowance),
      payoutMethod,
      accountDetails,
      presenceCount: Number(presenceCount)
    });
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 overflow-y-auto bg-black/90 backdrop-blur-md">
      <div 
        className="w-full max-w-4xl bg-[#090a10] border border-white/10 rounded-2xl shadow-3xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header Modal */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-black/40">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-400/20 flex items-center justify-center text-emerald-400">
              <User className="h-4.5 w-4.5" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-white tracking-wide uppercase">Configurateur de Profil de Simulation</h3>
              <p className="text-[10.5px] text-slate-400">Modifiez instantanément votre identité de test pour expérimenter les différentes vues applicatives.</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 hover:bg-white/5 rounded-lg text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-4.5 w-4.5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleApply} className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* COLUMN 1: IDENTIFICATION FORM */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest border-b border-white/5 pb-1">
                ❶ Fiche d'Identité de Test
              </h4>

              <div className="space-y-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Nom complet de l'expert :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <User className="h-4 w-4" />
                    </span>
                    <input
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      required
                      placeholder="Ex: Ir. Jean-Pierre Kabange"
                      className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-semibold focus:outline-hidden focus:border-emerald-500/50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Adresse courriel :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <Mail className="h-4 w-4" />
                    </span>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                      placeholder="Ex: jp.kabange@cnetp.cd"
                      className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-hidden focus:border-emerald-500/50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Structure d'affiliation (CNETP-16) :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <Building2 className="h-4 w-4" />
                    </span>
                    <input
                      type="text"
                      value={structure}
                      onChange={e => setStructure(e.target.value)}
                      required
                      placeholder="Ex: Office des Routes (OR)"
                      className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-semibold focus:outline-hidden focus:border-emerald-500/50"
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 mt-1 block">Renseignez l'une des 16 entités co-financeurs (ex: OVD, OR, BTC, ONIC, ONA, FEC...)</span>
                </div>
              </div>

              {/* BARÈME DE DOUBLE ENUMERATION */}
              <h4 className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest border-b border-white/5 pb-1 pt-2">
                ❷ Barème & Coordonnées Financières
              </h4>

              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Taux jeton ($ USD) :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <Coins className="h-4 w-4" />
                    </span>
                    <input
                      type="number"
                      value={dailyRate}
                      onChange={e => setDailyRate(Number(e.target.value))}
                      min="0"
                      className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-hidden"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Recherche Mensuelle ($) :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <TrendingUp className="h-4 w-4" />
                    </span>
                    <input
                      type="number"
                      value={monthlyResearchAllowance}
                      onChange={e => setMonthlyResearchAllowance(Number(e.target.value))}
                      min="0"
                      className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-hidden"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3.5 pt-1">
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Mode de règlement :</label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-2.5 text-slate-500">
                      <Wallet2 className="h-4 w-4" />
                    </span>
                    <select
                      value={payoutMethod}
                      onChange={e => setPayoutMethod(e.target.value as any)}
                      className="w-full pl-8.5 p-2 bg-black text-white border border-white/10 rounded-lg focus:outline-hidden"
                    >
                      <option value="Equity BCDC">Equity BCDC</option>
                      <option value="Rawbank">Rawbank</option>
                      <option value="M-Pesa">Airtel Money / M-Pesa</option>
                      <option value="Orange Money">Orange Money</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">N° Compte / Coordonnées :</label>
                  <input
                    type="text"
                    value={accountDetails}
                    onChange={e => setAccountDetails(e.target.value)}
                    required
                    placeholder="Ex: 00019-992381..."
                    className="w-full p-2 bg-black/40 border border-white/10 rounded-lg text-white text-[11px] font-mono focus:outline-hidden"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold uppercase tracking-wider text-[9px]">Scrutins émargés (Présence) :</label>
                <div className="relative">
                  <span className="absolute left-2.5 top-2.5 text-slate-500">
                    <CalendarRange className="h-4 w-4" />
                  </span>
                  <input
                    type="number"
                    value={presenceCount}
                    onChange={e => setPresenceCount(Number(e.target.value))}
                    min="0"
                    max="50"
                    className="w-full pl-8.5 p-2 bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-hidden"
                  />
                </div>
                <span className="text-[9px] text-slate-500 mt-1 block">Sert à simuler l'indemnisation cumulée dans l'espace personnel.</span>
              </div>

            </div>

            {/* COLUMN 2: ROLE SELECTOR PANEL */}
            <div className="flex flex-col h-full">
              <h4 className="text-[10px] font-bold text-amber-400 uppercase tracking-widest border-b border-white/5 pb-1 mb-3">
                ❸ Sélectionner le Rôle Réglementaire
              </h4>

              <div className="flex-1 overflow-y-auto space-y-2 pr-1 select-none">
                {CNETP_ROLES_DETAILED.map(role => {
                  const isSelected = role.id === roleId;
                  return (
                    <div 
                      key={role.id}
                      onClick={() => setRoleId(role.id)}
                      className={`p-3 border rounded-xl transition-all cursor-pointer flex gap-3 items-start ${
                        isSelected 
                          ? `${role.colorClass} scale-[1.01] ring-1 ring-emerald-500/20` 
                          : "border-white/5 bg-white/[0.01] hover:bg-white/[0.03] text-slate-400"
                      }`}
                    >
                      <div className="mt-0.5 shrink-0">
                        <div className={`h-4.5 w-4.5 rounded-full border flex items-center justify-center ${
                          isSelected ? "border-emerald-400 text-emerald-400" : "border-slate-700"
                        }`}>
                          {isSelected && <Check className="h-3 w-3" />}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-extrabold text-white text-xs leading-none">{role.name}</span>
                          <span className="text-[8.5px] font-mono opacity-80 uppercase px-1.5 py-0.2 rounded bg-black/40">
                            {role.id}
                          </span>
                        </div>
                        <p className="text-[10.5px] text-slate-400 leading-normal">{role.desc}</p>
                        <p className="text-[9.5px] text-slate-500 italic flex items-center gap-1">
                          <Info className="h-3.5 w-3.5 shrink-0" />
                          <span>Pouvoirs : {role.power}</span>
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

          {/* Action Footer */}
          <div className="pt-4 border-t border-white/10 flex justify-end gap-3 bg-black/20 p-4 -mx-6 -mb-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white font-bold rounded-lg transition-colors cursor-pointer"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-black font-extrabold rounded-lg tracking-wide uppercase transition-all cursor-pointer flex items-center gap-1.5 shadow-md"
            >
              <Award className="h-4 w-4" />
              Appliquer & Tester Rôle Actif
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
