import React, { useState, useEffect } from "react";
import { User, Mail, Phone, MapPin, Briefcase, FileText, CreditCard, Award, Save, Loader, AlertCircle, CheckCircle2 } from "lucide-react";

interface ProfileData {
  id: string;
  user: {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string;
    province: string;
  };
  structure: {
    name: string;
    acronym: string;
    category: string;
  };
  status: string;
  specialties: string;
  appointment_decree_number: string;
  appointment_date: string;
  bank_account: string;
  bank_name: string;
  mobile_money_number: string;
  affectations: any[];
}

export default function ProfileModule() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const [formData, setFormData] = useState<Partial<ProfileData>>({});

  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await fetch("/api/v1/experts/my_profile/");
        if (!res.ok) throw new Error("Impossible de charger le profil");
        const data = await res.json();
        setProfile(data);
        setFormData(data);
      } catch (err: any) {
        setToast({ message: err.message, type: "error" });
      } finally {
        setIsLoading(false);
      }
    }
    fetchProfile();
  }, []);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch(`/api/v1/experts/${profile?.id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error("Erreur lors de la sauvegarde");
      const updated = await res.json();
      setProfile(updated);
      setIsEditing(false);
      setToast({ message: "Profil mis à jour avec succès !", type: "success" });
    } catch (err: any) {
      setToast({ message: err.message, type: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center gap-4 text-slate-400">
        <Loader className="h-8 w-8 animate-spin text-emerald-500" />
        <p className="text-sm font-medium">Chargement de votre profil expert...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center gap-4 text-slate-400">
        <AlertCircle className="h-10 w-10 text-red-400" />
        <p className="text-sm font-medium">Aucun profil d'expert trouvé pour cet utilisateur.</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-auto p-8 bg-[#06060c]/20">
      {toast && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border animate-slideIn backdrop-blur-md ${
          toast.type === "success" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-red-500/10 border-red-500/20 text-red-400"
        }`}>
          {toast.type === "success" ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
          <span className="text-xs font-semibold">{toast.message}</span>
        </div>
      )}

      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row items-center gap-6 p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm">
          <div className="h-24 w-24 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-emerald-500/20">
            {profile.user.first_name[0]}{profile.user.last_name[0]}
          </div>
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-2xl font-bold text-white mb-1">
              {profile.user.first_name} {profile.user.last_name}
            </h1>
            <div className="flex flex-wrap justify-center md:justify-start gap-3">
              <span className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
                <Award className="h-3 w-3" /> Expert Certifié
              </span>
              <span className={`flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider ${
                profile.status === 'ACTIVE' ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }`}>
                Statut : {profile.status}
              </span>
            </div>
          </div>
          <button
            onClick={() => isEditing ? (setIsEditing(false)) : (setIsEditing(true))}
            className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
              isEditing 
                ? "bg-slate-700 text-white hover:bg-slate-600" 
                : "bg-emerald-500 text-black hover:bg-emerald-400 shadow-lg shadow-emerald-500/20"
            }`}
          >
            {isEditing ? "Annuler" : "Modifier le profil"}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Basic & Prof Info */}
          <div className="lg:col-span-2 space-y-8">
            {/* Personal Information */}
            <section className="p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-2 text-emerald-400 mb-4">
                <User className="h-5 w-5" />
                <h2 className="text-sm font-bold uppercase tracking-widest">Informations Personnelles</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <Mail className="h-3 w-3" /> Email
                  </label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={profile.user.email}
                      disabled
                      title="L'email ne peut pas être modifié"
                    />
                  ) : (
                    <p className="text-sm text-slate-300">{profile.user.email}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <Phone className="h-3 w-3" /> Téléphone
                  </label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={formData.user?.phone || profile.user.phone}
                      onChange={(e) => handleInputChange('user_phone', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300">{profile.user.phone || "Non renseigné"}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> Province
                  </label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={formData.user?.province || profile.user.province}
                      onChange={(e) => handleInputChange('user_province', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300">{profile.user.province || "Non renseigné"}</p>
                  )}
                </div>
              </div>
            </section>

            {/* Professional Information */}
            <section className="p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-2 text-emerald-400 mb-4">
                <Briefcase className="h-5 w-5" />
                <h2 className="text-sm font-bold uppercase tracking-widest">Parcours Professionnel</h2>
              </div>
              <div className="space-y-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <Award className="h-3 w-3" /> Spécialités & Compétences
                  </label>
                  {isEditing ? (
                    <textarea 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all h-24"
                      value={formData.specialties || profile.specialties}
                      onChange={(e) => handleInputChange('specialties', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300 leading-relaxed">{profile.specialties || "Aucune spécialité renseignée."}</p>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <FileText className="h-3 w-3" /> N° Arrêté de Nomination
                    </label>
                    {isEditing ? (
                      <input 
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                        value={formData.appointment_decree_number || profile.appointment_decree_number}
                        onChange={(e) => handleInputChange('appointment_decree_number', e.target.value)}
                      />
                    ) : (
                      <p className="text-sm text-slate-300">{profile.appointment_decree_number || "Non renseigné"}</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" /> Date de Nomination
                    </label>
                    {isEditing ? (
                      <input 
                        type="date"
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                        value={formData.appointment_date || profile.appointment_date}
                        onChange={(e) => handleInputChange('appointment_date', e.target.value)}
                      />
                    ) : (
                      <p className="text-sm text-slate-300">{profile.appointment_date || "Non renseignée"}</p>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* Right Column: Structure & Finance */}
          <div className="space-y-8">
            {/* Structure Section */}
            <section className="p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-2 text-emerald-400 mb-4">
                <Landmark className="h-5 w-5" />
                <h2 className="text-sm font-bold uppercase tracking-widest">Structure</h2>
              </div>
              <div className="text-center p-4 rounded-xl bg-white/5 border border-white/5">
                <p className="text-lg font-bold text-white">{profile.structure.name}</p>
                <p className="text-xs text-slate-500 font-mono uppercase tracking-tighter">{profile.structure.acronym}</p>
                <p className="text-[10px] text-emerald-500/70 mt-2 font-semibold">{profile.structure.category}</p>
              </div>
            </section>

            {/* Financial Details */}
            <section className="p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-2 text-emerald-400 mb-4">
                <CreditCard className="h-5 w-5" />
                <h2 className="text-sm font-bold uppercase tracking-widest">Infos Bancaires</h2>
              </div>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Banque</label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={formData.bank_name || profile.bank_name}
                      onChange={(e) => handleInputChange('bank_name', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300">{profile.bank_name || "Non renseigné"}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Numéro de Compte</label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={formData.bank_account || profile.bank_account}
                      onChange={(e) => handleInputChange('bank_account', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300 font-mono">{profile.bank_account || "Non renseigné"}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Mobile Money</label>
                  {isEditing ? (
                    <input 
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-emerald-500 outline-none transition-all"
                      value={formData.mobile_money_number || profile.mobile_money_number}
                      onChange={(e) => handleInputChange('mobile_money_number', e.target.value)}
                    />
                  ) : (
                    <p className="text-sm text-slate-300 font-mono">{profile.mobile_money_number || "Non renseigné"}</p>
                  )}
                </div>
              </div>
            </section>

            {/* Save Button (Visible only when editing) */}
            {isEditing && (
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500 text-black font-bold text-sm transition-all hover:bg-emerald-400 disabled:opacity-50 shadow-lg shadow-emerald-500/20"
              >
                {isSaving ? <Loader className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Enregistrer les modifications
              </button>
            )}
          </div>
        </div>

        {/* Affectations Section */}
        <section className="p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-sm space-y-6">
          <div className="flex items-center gap-2 text-emerald-400 mb-4">
            <Award className="h-5 w-5" />
            <h2 className="text-sm font-bold uppercase tracking-widest">Affectations Gouvernance</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profile.affectations && profile.affectations.length > 0 ? (
              profile.affectations.map((aff, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-emerald-500/30 transition-all">
                  <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Comité / Groupe</p>
                  <p className="text-sm font-bold text-white mb-2">{aff.ctm_name || aff.wg_name || "Non spécifié"}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-medium text-slate-400 uppercase">Rôle : {aff.role_type}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">Aucune affectation active pour le moment.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
