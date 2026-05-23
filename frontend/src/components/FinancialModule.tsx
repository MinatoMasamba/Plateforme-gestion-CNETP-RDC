import React, { useState, useMemo } from "react";
import { 
  HandCoins, 
  Building2, 
  Landmark, 
  RefreshCw, 
  FileText, 
  CheckCircle2, 
  DollarSign, 
  Wallet2, 
  CalendarRange, 
  Code, 
  AlertTriangle,
  Users,
  Download,
  BellRing,
  Award,
  ArrowRight,
  TrendingUp,
  Coins,
  ShieldCheck,
  Plus,
  Search,
  ExternalLink
} from "lucide-react";

interface StructureFee {
  id: string;
  name: string;
  category: "Administration" | "Établissements / Offices" | "Ordres" | "Académiques" | "Société Civile / Privé";
  annualFee: number;
  paidAmount: number;
  status: "Payé" | "Partiellement payé" | "Non payé";
  lastPaymentDate?: string;
   expertsQuota: number;
}

interface SelectedExpertPayroll {
  id: string;
  name: string;
  role: string;
  structure: string;
  presenceCount: number;
  dailyRate: number; // Jeton de présence rate
  monthlyResearchAllowance: number; // Allocations de recherche
  payoutMethod: "M-Pesa" | "Orange Money" | "Airtel Money" | "Rawbank" | "Equity BCDC";
  accountDetails: string;
  status: "En attente" | "Traité";
}

const INITIAL_FEES: StructureFee[] = [
  { id: "fee-1", name: "Office des Routes (OR)", category: "Établissements / Offices", annualFee: 25000, paidAmount: 25000, status: "Payé", lastPaymentDate: "2026-03-12", expertsQuota: 18 },
  { id: "fee-2", name: "Bureau Technique de Contrôle (BTC)", category: "Établissements / Offices", annualFee: 15000, paidAmount: 5000, status: "Partiellement payé", lastPaymentDate: "2026-04-01", expertsQuota: 10 },
  { id: "fee-3", name: "Ordre National des Ingénieurs Civils (ONIC)", category: "Ordres", annualFee: 10000, paidAmount: 0, status: "Non payé", expertsQuota: 8 },
  { id: "fee-4", name: "Fédération des Entreprises du Congo (FEC)", category: "Société Civile / Privé", annualFee: 30000, paidAmount: 30000, status: "Payé", lastPaymentDate: "2026-05-02", expertsQuota: 15 },
  { id: "fee-5", name: "Office des Voiries et Drainage (OVD)", category: "Établissements / Offices", annualFee: 25000, paidAmount: 12500, status: "Partiellement payé", lastPaymentDate: "2026-05-10", expertsQuota: 14 },
  { id: "fee-6", name: "Secrétariat Général des ITP (SG-ITP)", category: "Administration", annualFee: 40000, paidAmount: 40000, status: "Payé", lastPaymentDate: "2026-02-15", expertsQuota: 30 },
  { id: "fee-7", name: "Cabinet du Ministre ITP", category: "Administration", annualFee: 20000, paidAmount: 20000, status: "Payé", lastPaymentDate: "2026-01-20", expertsQuota: 12 },
  { id: "fee-8", name: "Agence Congolaise des Grands Travaux (ACGT)", category: "Établissements / Offices", annualFee: 30000, paidAmount: 15000, status: "Partiellement payé", lastPaymentDate: "2026-04-20", expertsQuota: 16 },
  { id: "fee-9", name: "Fonds National d'Entretien Routier (FONER)", category: "Établissements / Offices", annualFee: 35000, paidAmount: 35000, status: "Payé", lastPaymentDate: "2026-05-01", expertsQuota: 12 },
  { id: "fee-10", name: "Cellule d'Infrastructures (CI)", category: "Administration", annualFee: 15000, paidAmount: 7500, status: "Partiellement payé", lastPaymentDate: "2026-04-18", expertsQuota: 8 },
  { id: "fee-11", name: "Bureau d'Études d'Aménagement (BEAU)", category: "Établissements / Offices", annualFee: 15000, paidAmount: 0, status: "Non payé", expertsQuota: 9 },
  { id: "fee-12", name: "Ministère de l'Urbanisme & Habitat", category: "Administration", annualFee: 10000, paidAmount: 5000, status: "Partiellement payé", lastPaymentDate: "2026-03-30", expertsQuota: 7 },
  { id: "fee-13", name: "Ordre National des Architectes (ONA)", category: "Ordres", annualFee: 10000, paidAmount: 10000, status: "Payé", lastPaymentDate: "2026-05-05", expertsQuota: 6 },
  { id: "fee-14", name: "Société Civile & OCC (Contrôle)", category: "Société Civile / Privé", annualFee: 12000, paidAmount: 6000, status: "Partiellement payé", lastPaymentDate: "2026-04-12", expertsQuota: 8 },
  { id: "fee-15", name: "Cellule Reconstruction Nationale", category: "Administration", annualFee: 15500, paidAmount: 0, status: "Non payé", expertsQuota: 10 },
  { id: "fee-16", name: "Collège Experts Académiques / Juristes", category: "Académiques", annualFee: 12000, paidAmount: 12000, status: "Payé", lastPaymentDate: "2026-03-22", expertsQuota: 15 }
];

const INITIAL_PAYROLL: SelectedExpertPayroll[] = [
  { id: "exp-1", name: "Prof. Masamba Édouard", role: "Président scientifique", structure: "UNIKIN/Académiques", presenceCount: 8, dailyRate: 180, monthlyResearchAllowance: 800, payoutMethod: "Equity BCDC", accountDetails: "00018-9923812-71", status: "En attente" },
  { id: "exp-2", name: "Ir. Chantal Mwamba", role: "Secrétaire du CTM", structure: "OVD", presenceCount: 11, dailyRate: 150, monthlyResearchAllowance: 500, payoutMethod: "M-Pesa", accountDetails: "+243 812 345 678", status: "En attente" },
  { id: "exp-3", name: "Arch. Sylvain Lukusa", role: "Rapporteur CTM", structure: "ONA", presenceCount: 10, dailyRate: 150, monthlyResearchAllowance: 600, payoutMethod: "Orange Money", accountDetails: "+243 898 765 432", status: "Traité" },
  { id: "exp-4", name: "Ir. Godefroid Munongo", role: "Membre Permanent", structure: "OR", presenceCount: 7, dailyRate: 120, monthlyResearchAllowance: 300, payoutMethod: "Airtel Money", accountDetails: "+243 821 112 233", status: "En attente" },
  { id: "exp-5", name: "Ir. Blaise Nkansu", role: "Observateur Représentant", structure: "BCT", presenceCount: 6, dailyRate: 100, monthlyResearchAllowance: 150, payoutMethod: "Rawbank", accountDetails: "00238-1122394-02", status: "Traité" },
  { id: "exp-6", name: "Ir. Albertine Mpaka", role: "Membre Permanent", structure: "SG-ITP", presenceCount: 9, dailyRate: 120, monthlyResearchAllowance: 300, payoutMethod: "Equity BCDC", accountDetails: "00019-2233441-15", status: "En attente" }
];

interface FinancialModuleProps {
  userRole?: string;
  experts?: any[];
  simulatedProfile?: any;
}

export default function FinancialModule({
  userRole = "ADMIN",
  experts = [],
  simulatedProfile = null
}: FinancialModuleProps) {
  const [fees, setFees] = useState<StructureFee[]>(INITIAL_FEES);
  const [payroll, setPayroll] = useState<SelectedExpertPayroll[]>(INITIAL_PAYROLL);
  
  const [searchFeeText, setSearchFeeText] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("TOUS");
  const [searchExpertText, setSearchExpertText] = useState("");
  
  const [xmlData, setXmlData] = useState<string | null>(null);
  const [invoiceView, setInvoiceView] = useState<StructureFee | null>(null);
  const [payoutReceiptView, setPayoutReceiptView] = useState<SelectedExpertPayroll | null>(null);
  
  const [adminTab, setAdminTab] = useState<"structure" | "perdiem" | "kpis">("structure");
  const [notification, setNotification] = useState<{ msg: string; type: "success" | "info" } | null>(null);

  const triggerNotify = (msg: string, type: "success" | "info" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Calculations for total tracking
  const totals = useMemo(() => {
    const totalDues = fees.reduce((acc, f) => acc + f.annualFee, 0);
    const totalPaid = fees.reduce((acc, f) => acc + f.paidAmount, 0);
    
    // Auto calculated payroll sums
    const pendingJetons = payroll
      .filter(p => p.status === "En attente")
      .reduce((acc, p) => acc + (p.presenceCount * p.dailyRate), 0);
      
    const pendingResearch = payroll
      .filter(p => p.status === "En attente")
      .reduce((acc, p) => acc + p.monthlyResearchAllowance, 0);
      
    const totalPayrollPending = pendingJetons + pendingResearch;

    return {
      totalDues,
      totalPaid,
      totalOwed: totalDues - totalPaid,
      pendingJetons,
      pendingResearch,
      totalPayrollPending
    };
  }, [fees, payroll]);

  // Handle recorded structure cotisation payment
  const handlePayFee = (id: string, amount: number) => {
    setFees(prev => prev.map(f => {
      if (f.id === id) {
        const newPaid = f.paidAmount + amount;
        let newStatus: "Payé" | "Partiellement payé" | "Non payé" = "Non payé";
        if (newPaid >= f.annualFee) newStatus = "Payé";
        else if (newPaid > 0) newStatus = "Partiellement payé";

        return {
          ...f,
          paidAmount: Math.min(newPaid, f.annualFee),
          status: newStatus,
          lastPaymentDate: new Date().toISOString().split("T")[0]
        };
      }
      return f;
    }));
    triggerNotify(`La contribution administrative a été enregistrée avec succès !`, "success");
  };

  // Simulate reminder alert transmit
  const handleTriggerRelance = (fee: StructureFee) => {
    triggerNotify(`Rappel réglementaire et facture proforma transmis automatiquement au secrétariat de "${fee.name}" !`, "info");
  };

  // Process liquidation payout per expert
  const processExpertPayment = (id: string) => {
    setPayroll(prev => prev.map(p => p.id === id ? { ...p, status: "Traité" } : p));
    const target = payroll.find(p => p.id === id);
    if (target) {
      triggerNotify(`Ordre d'indemnité liquidé avec succès pour ${target.name} !`, "success");
    }
  };

  // Automated ISO-20022 wire file layout generator
  const generateIsoXml = () => {
    const pendingList = payroll.filter(p => p.status === "En attente");
    if (pendingList.length === 0) {
      triggerNotify("Aucun ordre d'indemnité en attente à compiler.", "info");
      return;
    }

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<!-- CNETP RDC - SYSTEME DE MANDATEMENT NATIONAL -->
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>CNETP-RDC-PAY-GEN-${Date.now()}</MsgId>
      <CreDtTm>${new Date().toISOString()}</CreDtTm>
      <NbOfTxs>${pendingList.length}</NbOfTxs>
      <CtrlSum>${totals.totalPayrollPending}</CtrlSum>
      <InitgPty>
        <Nm>COMMISSION NATIONALE NORMES EQUIPEMENTS ET TRAVAUX PUBLICS (RDC)</Nm>
        <PstlAdr>
          <TwnNm>Kinshasa-Gombe</TwnNm>
          <Ctry>CD</Ctry>
        </PstlAdr>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMT-INFO-CNETP-${new Date().getFullYear()}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>${new Date().toISOString().split("T")[0]}</ReqdExctnDt>
      <Dbtr>
        <Nm>FONER COMPTE EXCLUSIF DIRECTION GENERALE</Nm>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <Othr>
            <Id>CD24-30110-00100-98831201103-91</Id>
            <Issr>BANQUE CENTRALE DU CONGO (BCC)</Issr>
          </Othr>
        </Id>
      </DbtrAcct>
      ${pendingList.map(p => {
        const totalPayout = (p.presenceCount * p.dailyRate) + p.monthlyResearchAllowance;
        return `
      <CdtTrfTxInf>
        <PmtId>
          <EndToEndId>PAY-ID-${p.id.toUpperCase()}-${new Date().getMonth() + 1}</EndToEndId>
        </PmtId>
        <Amt>
          <InstdHrg Ccy="USD">${totalPayout}</InstdHrg>
        </Amt>
        <Cdtr>
          <Nm>${p.name}</Nm>
          <Role>${p.role}</Role>
        </Cdtr>
        <CdtrAcct>
          <Id>
            <Othr>
              <Id>${p.accountDetails}</Id>
              <Issr>${p.payoutMethod}</Issr>
            </Othr>
          </Id>
        </CdtrAcct>
        <RmtInf>
          <Ustrd>Indemnites CNETP: ${p.presenceCount} jetons (${p.presenceCount * p.dailyRate} USD) plus allocation ${p.monthlyResearchAllowance} USD</Ustrd>
        </RmtInf>
      </CdtTrfTxInf>`;
      }).join("")}
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>`;
    setXmlData(xml);
    triggerNotify("Fichier de mandatement ISO-20022 de virement bancaire généré !", "success");
  };

  // Filtered lists
  const filteredFees = useMemo(() => {
    return fees.filter(f => {
      const matchSearch = f.name.toLowerCase().includes(searchFeeText.toLowerCase());
      const matchCat = filterCategory === "TOUS" || f.category === filterCategory;
      return matchSearch && matchCat;
    });
  }, [fees, searchFeeText, filterCategory]);

  const filteredPayroll = useMemo(() => {
    return payroll.filter(p => {
      return p.name.toLowerCase().includes(searchExpertText.toLowerCase()) || 
             p.structure.toLowerCase().includes(searchExpertText.toLowerCase());
    });
  }, [payroll, searchExpertText]);


  // Determine the active simulated expert based on simulated userRole
  // If user is a simple expert, we map them to a mock card to show customized view!
  const isFinancialAdmin = userRole === "ADMIN" || userRole === "GEST_COMP" || userRole === "COORD_CTC";
  
  const simulatedExpertObj = useMemo(() => {
    if (simulatedProfile) {
      return {
        id: "simulated-user",
        name: simulatedProfile.name,
        role: userRole === "ADMIN" ? "Administrateur technique" : 
              userRole === "RAP_CTM" ? "Rapporteur CTM" :
              userRole === "SEC_PERM" ? "Secrétaire Permanent" :
              userRole === "PRES_CTM" ? "Président du CTM" :
              userRole === "GEST_COMP" ? "Comptable Principal" :
              userRole === "COORD_CTC" ? "Coordonnateur CTC" : "Membre Permanent",
        structure: simulatedProfile.structure,
        presenceCount: simulatedProfile.presenceCount || 8,
        dailyRate: simulatedProfile.dailyRate || 150,
        monthlyResearchAllowance: simulatedProfile.monthlyResearchAllowance || 500,
        payoutMethod: simulatedProfile.payoutMethod || "Equity BCDC",
        accountDetails: simulatedProfile.accountDetails || "00018-9923812-70",
        status: "En attente"
      };
    }
    if (userRole === "PRES_CTM") {
      return payroll.find(p => p.id === "exp-1"); // Prof. Masamba
    } else if (userRole === "SEC_PERM") {
      return payroll.find(p => p.id === "exp-2"); // Ir. Chantal Mwamba
    } else if (userRole === "RAP_CTM") {
      return payroll.find(p => p.id === "exp-3"); // Sylvain Lukusa
    } else {
      // Default fallback simple expert
      return payroll.find(p => p.id === "exp-4"); // Ir. Godefroid Munongo
    }
  }, [userRole, payroll, simulatedProfile]);

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full text-slate-300">
      
      {/* Banner */}
      <div className="border-b border-white/10 pb-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <HandCoins className="h-6 w-6 text-emerald-400" />
            <h2 className="text-xl font-extrabold text-white tracking-tight uppercase">Portail de Gestion Financière CNETP</h2>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
            Module de perception des cotisations des 16 structures et liquidation automatisée des jetons de présence et d'allocations de recherche des experts techniques (RDC, Mai 2026).
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-3.5 py-2 rounded-xl text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-400">Poste Connecté :</span>
          <strong className="text-white bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded font-mono uppercase text-[10px]">
            {userRole}
          </strong>
        </div>
      </div>

      {/* Internal notifications */}
      {notification && (
        <div className={`p-4 rounded-xl border flex items-center gap-3 transition-all animate-fadeIn ${
          notification.type === "success" 
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            : "bg-blue-500/15 border-blue-500/30 text-blue-300"
        }`}>
          <div className="h-5.5 w-5.5 rounded-full bg-black/40 text-center font-bold text-xs flex items-center justify-center">
            ℹ
          </div>
          <p className="text-xs font-semibold">{notification.msg}</p>
        </div>
      )}

      {/* IF CURRENT RECRUITED ROLE IS LOGISTIQUE / ADMIN / COMPTABLE */}
      {isFinancialAdmin ? (
        <div className="space-y-6">
          
          {/* KPI Dashboard Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <div className="bg-black/45 border border-white/10 rounded-xl p-4.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase block tracking-wider">Trésor perçu (16 structures)</span>
              <span className="text-xl font-mono text-white font-extrabold block mt-1">${totals.totalPaid.toLocaleString()} USD</span>
              <span className="text-[10px] text-emerald-400 font-medium block mt-1">Cumulé sur ${totals.totalDues.toLocaleString()} USD attendus</span>
            </div>

            <div className="bg-black/45 border border-white/10 rounded-xl p-4.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase block tracking-wider">Quote-part Restante</span>
              <span className="text-xl font-mono text-amber-500 font-extrabold block mt-1">${totals.totalOwed.toLocaleString()} USD</span>
              <span className="text-[10px] text-slate-400 font-medium block mt-1">Sera couverte par rappels</span>
            </div>

            <div className="bg-black/45 border border-white/10 rounded-xl p-4.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase block tracking-wider">Jetons de présence en cours</span>
              <span className="text-xl font-mono text-indigo-400 font-extrabold block mt-1">${totals.pendingJetons.toLocaleString()} USD</span>
              <span className="text-[10px] text-slate-400 font-medium block mt-1">Estimés à partir des émargements</span>
            </div>

            <div className="bg-black/45 border border-white/10 rounded-xl p-4.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase block tracking-wider">Liquidations en attente</span>
              <span className="text-xl font-mono text-red-400 font-extrabold block mt-1">${totals.totalPayrollPending.toLocaleString()} USD</span>
              <span className="text-[10px] text-slate-400 font-medium block mt-1">A régler via virement ISO-20022</span>
            </div>
          </div>

          {/* Tab Submenu */}
          <div className="flex border-b border-white/5 pb-2 gap-4">
            <button
              onClick={() => setAdminTab("structure")}
              className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${
                adminTab === "structure"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              Cotisations Structures (CNETP-16)
            </button>
            <button
              onClick={() => setAdminTab("perdiem")}
              className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${
                adminTab === "perdiem"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              Double Taux Experts (Jetons / Recherche)
            </button>
            <button
              onClick={() => setAdminTab("kpis")}
              className={`pb-2 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer ${
                adminTab === "kpis"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              États de Synthèse & Pilotage
            </button>
          </div>

          {/* TAB 1: STRUCTURE CONTRACT FEES (COTISE) */}
          {adminTab === "structure" && (
            <div className="space-y-4 animate-fadeIn">
              
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs">
                <div className="relative w-full max-w-sm">
                  <span className="absolute left-3 top-3.5 flex items-center text-slate-550">
                    <Search className="h-4 w-4" />
                  </span>
                  <input
                    type="text"
                    value={searchFeeText}
                    onChange={e => setSearchFeeText(e.target.value)}
                    placeholder="Filtrer parmi les 16 structures (OR, OVD, FEC, SG-ITP...)"
                    className="w-full pl-9 p-2.5 rounded-lg border border-white/10 bg-black/45 text-white placeholder-slate-500 font-semibold focus:outline-hidden focus:border-emerald-500/50"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-slate-500 font-semibold font-mono">Domaine :</span>
                  <div className="flex gap-1 bg-black/40 p-1 rounded-lg border border-white/5">
                    {["TOUS", "Administration", "Établissements / Offices", "Ordres", "Société Civile / Privé"].map(cat => (
                      <button
                        key={cat}
                        onClick={() => setFilterCategory(cat)}
                        className={`px-2.5 py-1 rounded text-[10.5px] font-bold ${
                          filterCategory === cat
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/15"
                            : "text-slate-500 hover:text-slate-300"
                        }`}
                      >
                        {cat === "TOUS" ? "Tous" : cat.split(" / ")[0]}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Grid of structures */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredFees.map(fee => {
                  const rest = fee.annualFee - fee.paidAmount;
                  return (
                    <div key={fee.id} className="p-4 bg-black/35 hover:bg-black/45 border border-white/10 rounded-2xl flex flex-col justify-between gap-3 text-xs transition-colors relative overflow-hidden">
                      <div className="space-y-2">
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase tracking-tighter font-mono bg-white/5 px-2 py-0.5 rounded border border-white/5">{fee.category}</span>
                            <h4 className="font-bold text-slate-100 text-xs mt-1.5">{fee.name}</h4>
                          </div>

                          <span className={`text-[8.5px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                            fee.status === "Payé"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : fee.status === "Partiellement payé"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}>
                            {fee.status}
                          </span>
                        </div>

                        <div className="flex items-center justify-between font-mono text-[11px] pt-1.5">
                          <span className="text-slate-400">Quota d'Experts : <strong>{fee.expertsQuota}</strong></span>
                          <span>Reçu : <strong className="text-white">${fee.paidAmount.toLocaleString()} USD</strong> <span className="text-slate-500">/ ${fee.annualFee.toLocaleString()}</span></span>
                        </div>

                        <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden mt-1">
                          <div 
                            className={`h-full rounded-full ${fee.status === 'Payé' ? 'bg-emerald-500' : fee.status === 'Partiellement payé' ? 'bg-amber-400' : 'bg-red-500'}`}
                            style={{ width: `${(fee.paidAmount / fee.annualFee) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-white/5 text-[10.5px]">
                        {rest > 0 ? (
                          <>
                            <button
                              onClick={() => handlePayFee(fee.id, rest / 2)}
                              className="px-2.5 py-1 bg-white/5 hover:bg-white/10 font-bold text-white rounded cursor-pointer"
                            >
                              Enregistrer 50%
                            </button>
                            <button
                              onClick={() => handlePayFee(fee.id, rest)}
                              className="px-2.5 py-1 bg-emerald-500/15 hover:bg-emerald-500/25 font-bold text-emerald-400 rounded cursor-pointer"
                            >
                              Apurer solde
                            </button>
                            <button
                              onClick={() => handleTriggerRelance(fee)}
                              className="px-2 py-1 ml-auto text-slate-400 hover:text-white"
                              title="Déclencher une relance numérique"
                            >
                              <BellRing className="h-3.5 w-3.5" />
                            </button>
                          </>
                        ) : (
                          <div className="flex items-center gap-1.5 text-emerald-400 font-medium font-sans">
                            <CheckCircle2 className="h-4 w-4" />
                            <span>Trésor apuré sur l'exercice 2026</span>
                          </div>
                        )}
                        <button
                          onClick={() => setInvoiceView(fee)}
                          className="px-2 py-1 bg-white/5 hover:bg-white/10 text-white rounded ml-auto text-[10px]"
                        >
                          Facture Pro
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {filteredFees.length === 0 && (
                <div className="p-8 text-center bg-black/25 rounded-2xl border border-white/5">
                  <p className="text-sm text-slate-500 italic">Aucune structure ne correspond à votre recherche.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DOUBLE-TIER PER DIEMS AND RESEARCH ALLOWANCE GENERATOR */}
          {adminTab === "perdiem" && (
            <div className="space-y-5 animate-fadeIn">
              
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs pb-2 border-b border-white/5">
                <div>
                  <h4 className="font-bold text-white uppercase text-[11.5px] flex items-center gap-1">
                    <Coins className="h-4.5 w-4.5 text-emerald-400" />
                    Grille Administrative de Double Rémunération
                  </h4>
                  <p className="text-slate-400 mt-0.5 text-[10.5px]">
                    Selon l'Article 10, chaque expert émerge au budget de la commission par cumul de **Jetons de présence** et d'**Allocations de recherche** mensuelles.
                  </p>
                </div>

                <div className="relative w-full max-w-xs shrink-0">
                  <span className="absolute left-2.5 top-2.5 flex items-center text-slate-550">
                    <Search className="h-3.5 w-3.5" />
                  </span>
                  <input
                    type="text"
                    value={searchExpertText}
                    onChange={e => setSearchExpertText(e.target.value)}
                    placeholder="Filtrer par expert ou structure..."
                    className="w-full pl-8 p-2 rounded-lg border border-white/10 bg-black/45 text-white text-[11px] placeholder-slate-550 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Expert payroll list */}
              <div className="space-y-3">
                {filteredPayroll.map(p => {
                  const jetonTotal = p.presenceCount * p.dailyRate;
                  const totalDue = jetonTotal + p.monthlyResearchAllowance;
                  return (
                    <div key={p.id} className="p-4 bg-black/35 border border-white/10 rounded-2xl flex flex-col md:flex-row justify-between md:items-center gap-4 text-xs hover:bg-[#090b14] transition-all">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-white text-xs">{p.name}</p>
                          <span className="text-[9px] font-mono bg-indigo-505/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.2 rounded-sm">{p.role}</span>
                        </div>
                        <p className="text-[10.5px] text-slate-500 leading-normal">
                          Affiliation: <strong className="text-slate-400">{p.structure}</strong> • Compte: <span className="text-slate-300 font-mono">{p.payoutMethod} ({p.accountDetails})</span>
                        </p>
                        
                        {/* Two-Tier Breakdowns */}
                        <div className="grid grid-cols-2 gap-3 max-w-sm text-[10.5px] font-mono pt-1">
                          <div className="p-2 bg-white/[0.02] border border-white/5 rounded-lg">
                            <span className="text-[9px] text-slate-500 block uppercase">1. Jetons de présence :</span>
                            <span className="text-white block font-extrabold mt-0.5">${jetonTotal} USD</span>
                            <span className="text-[8.5px] text-slate-500 block mt-0.5">{p.presenceCount} scrutins émargés @ ${p.dailyRate}</span>
                          </div>
                          <div className="p-2 bg-white/[0.02] border border-white/5 rounded-lg">
                            <span className="text-[9px] text-slate-500 block uppercase">2. Rapport d'Allocation :</span>
                            <span className="text-white block font-extrabold mt-0.5">${p.monthlyResearchAllowance} USD</span>
                            <span className="text-[8.5px] text-slate-500 block mt-0.5">Stipend académique fixe / mois</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right shrink-0 flex flex-col justify-center items-end gap-2 border-t md:border-t-0 pt-3 md:pt-0 border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 block font-semibold uppercase font-mono">Total Net calculé</span>
                          <span className="font-mono text-emerald-400 font-black text-base">${totalDue} USD</span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          {p.status === "Traité" ? (
                            <span className="text-[9px] font-bold px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded uppercase">
                              Liquidé (OK)
                            </span>
                          ) : (
                            <button
                              onClick={() => processExpertPayment(p.id)}
                              className="px-2.5 py-1 bg-emerald-500 text-black font-extrabold text-[10.5px] hover:bg-emerald-400 rounded-md uppercase"
                            >
                              Liquider
                            </button>
                          )}
                          <button
                            onClick={() => setPayoutReceiptView(p)}
                            className="px-2 py-1 bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white rounded text-[10px]"
                          >
                            Détail
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Wire output XML button */}
              <div className="p-4 bg-indigo-500/5 rounded-2xl border border-indigo-500/10 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs mt-4">
                <div className="space-y-1">
                  <h4 className="font-extrabold text-white flex items-center gap-1.5">
                    <ShieldCheck className="h-4.5 w-4.5 text-indigo-400" />
                    Mandatement Bancaire Centralisé (XML ISO)
                  </h4>
                  <p className="text-slate-400 text-[10.5px]">
                    Générez le fichier d'ordre de transfert bancaire à destination de la Banque Centrale du Congo pour liquider les indemnités en attente.
                  </p>
                </div>

                <button
                  onClick={generateIsoXml}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-550 text-white font-extrabold tracking-wide uppercase rounded-lg flex items-center gap-1.5 cursor-pointer shrink-0 shadow-md"
                >
                  <Code className="h-4 w-4" />
                  Générer fichier pain.001
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: KEY SUMMARY CHARTS AND FORECASTS */}
          {adminTab === "kpis" && (
            <div className="space-y-6 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Structure contributions charts simulation summary */}
                <div className="bg-black/35 border border-white/10 rounded-2xl p-5 space-y-4">
                  <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider flex items-center gap-1">
                    <Building2 className="h-4.5 w-4.5 text-emerald-400" />
                    Ratio de Paiement des Cotisations CNETP-16
                  </h4>
                  <div className="space-y-3.5 text-xs text-slate-400">
                    <p className="leading-relaxed text-[11px]">
                      Conformément à l'Article 15 de la Charte Administrative CNETP, au moins **70% des cotisations collectées** doivent abonder le fonds avant le calcul trimestriel des stipends.
                    </p>

                    <div className="space-y-2 pt-2">
                      <div className="flex justify-between font-mono text-[10.5px]">
                        <span>Taux Global de Collecte (Réalisé)</span>
                        <span className="text-emerald-400 font-bold">
                          {((totals.totalPaid / totals.totalDues) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-emerald-500 h-full rounded-full" 
                          style={{ width: `${(totals.totalPaid / totals.totalDues) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 font-mono text-[10.5px] pt-2">
                      <div className="bg-[#05060b] p-2.5 rounded-xl border border-white/5">
                        <span className="text-slate-500 block font-sans">1. Objectif Global :</span>
                        <strong className="text-white block mt-0.5">${totals.totalDues.toLocaleString()} USD</strong>
                      </div>
                      <div className="bg-[#05060b] p-2.5 rounded-xl border border-white/5">
                        <span className="text-slate-500 block font-sans">2. Collecté Trésor :</span>
                        <strong className="text-emerald-400 block mt-0.5">${totals.totalPaid.toLocaleString()} USD</strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Logistics expenditure report simulation */}
                <div className="bg-black/35 border border-white/10 rounded-2xl p-5 space-y-4">
                  <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider flex items-center gap-1">
                    <Users className="h-4.5 w-4.5 text-emerald-400" />
                    Flux d'Indemnisation d'Experts
                  </h4>
                  <div className="space-y-3.5 text-xs text-slate-400">
                    <p className="leading-relaxed text-[11px]">
                      La masse salariale prévisionnelle est financée à part égale entre la contribution d'offices routières de RDC (OVD, OR, BTC, ACGT, FONER) et stipulée au budget de fonctionnement.
                    </p>

                    <div className="grid grid-cols-2 gap-4 pt-1 font-mono text-[10.5px]">
                      <div className="p-3 bg-indigo-500/5 rounded-xl border border-indigo-550/10">
                        <span className="text-[9px] uppercase text-slate-500 font-sans block">Total Indemnités Jetons :</span>
                        <strong className="text-indigo-400 text-sm mt-1 block">${totals.pendingJetons.toLocaleString()} USD</strong>
                        <span className="text-[8px] text-slate-500 block mt-1">Calculé au pro-rata d'émargements</span>
                      </div>
                      <div className="p-3 bg-purple-500/5 rounded-xl border border-purple-550/10">
                        <span className="text-[9px] uppercase text-slate-500 font-sans block">Total Allocations Recherche :</span>
                        <strong className="text-purple-400 text-sm mt-1 block">${totals.pendingResearch.toLocaleString()} USD</strong>
                        <span className="text-[8px] text-slate-500 block mt-1">Estimations par grades académiques</span>
                      </div>
                    </div>

                    <div className="p-2.5 bg-white/5 rounded-xl text-[10.5px]">
                      <p className="flex justify-between text-slate-300">
                        <span>Solde de trésor résiduel disponible :</span>
                        <strong className="text-emerald-400">${(totals.totalPaid - totals.totalPayrollPending).toLocaleString()} USD</strong>
                      </p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

        </div>
      ) : (
        /* IF LOGGED IN USER IS A SIMPLE EXPERT / SCIENTIFIC PRESIDENT */
        <div className="space-y-6 animate-fadeIn">
          
          <div className="p-5 bg-[#05060b] border border-emerald-500/20 rounded-2xl space-y-4">
            <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-2">
              <Award className="h-5 w-5 text-emerald-400" />
              Espace Personnel d'Indemnisation du Membre CNETP
            </h3>
            
            <p className="text-xs text-slate-400 leading-relaxed">
              Bienvenue sur votre espace d'accès réservé. Conformément à l'arrêté du Ministre des ITP, vous pouvez consulter vos données d'émargement de présence, vos allocations dues, et réclamer vos certificats de paiement.
            </p>

            {simulatedExpertObj ? (
              <div className="space-y-4">
                
                {/* Profile card details */}
                <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl flex flex-col sm:flex-row justify-between sm:items-center gap-3 text-xs">
                  <div>
                    <h4 className="font-bold text-white text-sm">{simulatedExpertObj.name}</h4>
                    <p className="text-slate-400 mt-0.5 text-[10.5px]">{simulatedExpertObj.role} • {simulatedExpertObj.structure}</p>
                  </div>

                  <div className="text-right">
                    <span className="text-[9.5px] text-slate-500 block uppercase">Province de Travail</span>
                    <strong className="text-slate-300">Kinshasa (RDC)</strong>
                  </div>
                </div>

                {/* Personal allowance overview card */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-2">
                  <div className="bg-black/40 border border-white/5 rounded-xl p-4">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold leading-none">Scrutins convoqués émargés</span>
                    <span className="text-xl font-mono text-white font-extrabold block mt-2">{simulatedExpertObj.presenceCount} Séances</span>
                    <span className="text-[9px] text-slate-400 block mt-1 font-mono">Chaque jeton réglé à ${simulatedExpertObj.dailyRate} USD</span>
                  </div>

                  <div className="bg-black/40 border border-white/5 rounded-xl p-4">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold leading-none">Allocation mensuelle fixe</span>
                    <span className="text-xl font-mono text-indigo-400 font-extrabold block mt-2">${simulatedExpertObj.monthlyResearchAllowance} USD</span>
                    <span className="text-[9px] text-slate-400 block mt-1">Directement abondé au grade scientifique</span>
                  </div>

                  <div className="bg-black/40 border border-white/5 rounded-xl p-4">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold leading-none">Montant Net d'indemnité</span>
                    <span className="text-xl font-mono text-emerald-400 font-extrabold block mt-2">
                      ${(simulatedExpertObj.presenceCount * simulatedExpertObj.dailyRate) + simulatedExpertObj.monthlyResearchAllowance} USD
                    </span>
                    <div className="mt-1 flex items-center gap-1">
                      <span className={`w-1.5 h-1.5 rounded-full ${simulatedExpertObj.status === 'Traité' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
                      <span className="text-[9px] text-slate-450 uppercase font-bold">{simulatedExpertObj.status === "Traité" ? "Transféré (OK)" : "En attente de liquidation"}</span>
                    </div>
                  </div>
                </div>

                {/* Bank Account review */}
                <div className="p-4 bg-[#0d0d15] border border-white/5 rounded-xl space-y-2 text-xs">
                  <h4 className="font-bold text-slate-200 text-xs">Coordonnées de virement enregistrées :</h4>
                  <div className="flex items-center gap-2 py-1 text-slate-350">
                    <Wallet2 className="h-4 w-4 text-emerald-400" />
                    <span>Mode de Règlement : <strong>{simulatedExpertObj.payoutMethod}</strong> • Compte : <strong className="font-mono text-white">{simulatedExpertObj.accountDetails}</strong></span>
                  </div>
                  <p className="text-[9.5px] text-slate-500 leading-normal">
                    Pour éditer ou modifier votre méthode de règlement (Rawbank, BCDC ou Mobile Money M-Pesa/Orange), vous devez soumettre un justificatif d'identité certifié par le Secrétariat permanent.
                  </p>
                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-3 pt-2">
                  <button
                    onClick={() => {
                      setPayoutReceiptView(simulatedExpertObj);
                      triggerNotify("Fiche de paie consolidée ouverte !", "success");
                    }}
                    className="flex-1 py-2.5 bg-emerald-500 text-black font-extrabold text-xs uppercase hover:bg-emerald-400 rounded-lg flex items-center justify-center gap-2 cursor-pointer shadow-md"
                  >
                    <Download className="h-4 w-4" />
                    Télécharger Reçu de Paiement PDF
                  </button>

                  <button
                    onClick={() => triggerNotify("Requête de re-calcul de jetons soumise aux services comptables.", "info")}
                    className="px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white font-bold text-xs uppercase rounded-lg cursor-pointer"
                  >
                    Contester un émargement
                  </button>
                </div>

              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">Identité de l'expert introuvable dans le répertoire.</p>
            )}

          </div>

        </div>
      )}

      {/* ISO XML VIEW SECTION */}
      {xmlData && (
        <div id="xml-modal" className="p-6 bg-[#04050a] border border-indigo-500/20 rounded-2xl space-y-3 font-mono text-[10.5px] leading-relaxed relative animate-fadeIn">
          <div className="flex justify-between items-center text-slate-400 border-b border-white/5 pb-2">
            <span className="text-indigo-400 font-bold uppercase tracking-wider flex items-center gap-1">
              <Code className="h-4 w-4" />
              Transfert de fonds XML pain.001.001.03 (RDC-CNETP-STANDARD)
            </span>
            <button
              onClick={() => setXmlData(null)}
              className="text-slate-500 hover:text-white px-2 py-1 bg-white/5 rounded-md cursor-pointer"
            >
              Fermer
            </button>
          </div>
          <pre className="overflow-x-auto text-slate-350 bg-black/60 p-4 rounded-xl max-h-72">{xmlData}</pre>
          <div className="text-[9.5px] text-slate-500 text-right uppercase">
            Signature Électronique Certifiée BCC (RDC)
          </div>
        </div>
      )}

      {/* Structured proforma invoice */}
      {invoiceView && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0b0c14] border border-white/10 rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl animate-slideIn text-slate-300">
            <div className="text-center font-serif pb-3 border-b border-white/10">
              <h3 className="font-bold text-white text-md tracking-wider">REPUBLIQUE DEMOCRATIQUE DU CONGO</h3>
              <p className="text-[9px] text-slate-500 mt-1 uppercase leading-none">Commission Nationale des Normes (CNETP)</p>
              <p className="text-[9px] text-slate-500 mt-1 leading-none">Secrétariat Général des ITP</p>
            </div>

            <div className="space-y-3 text-xs text-slate-300 leading-normal">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] text-slate-500 block">DÉBITEUR CO-FINANCEUR :</span>
                  <strong className="text-white text-xs">{invoiceView.name}</strong>
                  <span className="text-[10px] text-slate-400 block mt-1">Représentation experts CNETP : {invoiceView.expertsQuota} experts</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block">N° Facture :</span>
                  <strong className="text-slate-200 mt-0.5 block">CNETP-INV-2026-{invoiceView.id.toUpperCase()}</strong>
                </div>
              </div>

              <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl space-y-1.5 text-xs font-mono">
                <p className="flex justify-between"><span>Cotisation de base :</span> <span className="font-mono text-white">${invoiceView.annualFee.toLocaleString()} USD</span></p>
                <p className="flex justify-between text-slate-450 border-t border-white/5 pt-1.5 mt-1"><span>Acompte enregistré :</span> <span className="text-white">-${invoiceView.paidAmount.toLocaleString()} USD</span></p>
                <p className="flex justify-between border-t border-white/10 pt-1.5 mt-1 font-bold text-slate-100">
                  <span>Solde net restant dû :</span>
                  <span className="text-amber-400">${(invoiceView.annualFee - invoiceView.paidAmount).toLocaleString()} USD</span>
                </p>
              </div>

              <div className="p-3 bg-amber-500/5 border border-amber-550/10 rounded-lg text-[10.5px] text-amber-400 flex items-start gap-2.5 leading-relaxed">
                <AlertTriangle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
                <span>Rappel réglementaire : En conformité avec les directives CNETP, les redevances instituées sont destinées à financer l'indemnisation double taux des commissions techniques.</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 text-xs pt-4 border-t border-white/10 font-sans">
              <button
                onClick={() => setInvoiceView(null)}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white font-bold rounded-lg cursor-pointer"
              >
                Fermer l'ébauche
              </button>
              <button
                onClick={() => {
                  alert("Relance et facture officielle transmises par courriel sécurisé !");
                  setInvoiceView(null);
                }}
                className="px-4 py-2 bg-emerald-500 text-black font-extrabold rounded-lg hover:bg-emerald-400 cursor-pointer"
              >
                Transmettre facture
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Personal payroll receipt detail layout */}
      {payoutReceiptView && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0b0c14] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-5 shadow-2xl animate-slideIn text-slate-300 font-sans">
            <div className="text-center pb-3 border-b border-white/10">
              <p className="text-[10px] text-emerald-400 uppercase tracking-widest font-mono font-bold">REÇU D'EFFETS D'INDEMNITÉ</p>
              <h4 className="font-bold text-white text-md tracking-wider uppercase mt-1">CNETP - MASSE SALARIALE RDC</h4>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="flex justify-between items-start text-xs border-b border-white/5 pb-2">
                <div>
                  <span className="text-[9px] text-slate-500 block uppercase">Nom de l'expert</span>
                  <strong className="text-white text-xs">{payoutReceiptView.name}</strong>
                  <span className="text-[9px] text-slate-400 block mt-0.5">{payoutReceiptView.role}</span>
                </div>
                <div className="text-right">
                  <span className="text-[9px] text-slate-500 block">ID Paiement</span>
                  <strong className="text-slate-300 font-mono">REC-{payoutReceiptView.id.toUpperCase()}</strong>
                </div>
              </div>

              <div className="space-y-2 bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <p className="flex justify-between items-center text-[10px] uppercase font-bold text-slate-450">Decompositions des droits :</p>
                <div className="space-y-1 font-mono text-[10.5px]">
                  <p className="flex justify-between text-slate-400">
                    <span>Jetons de présence ({payoutReceiptView.presenceCount} sessions) :</span>
                    <span className="text-white font-bold">${payoutReceiptView.presenceCount * payoutReceiptView.dailyRate} USD</span>
                  </p>
                  <p className="flex justify-between text-slate-400">
                    <span>Allocation recherche CTM :</span>
                    <span className="text-white font-bold">${payoutReceiptView.monthlyResearchAllowance} USD</span>
                  </p>
                  <p className="flex justify-between text-indigo-400 font-bold border-t border-white/5 pt-1.5 mt-1.5 font-sans">
                    <span>Montant total perçu :</span>
                    <span className="text-emerald-400 font-mono text-xs">
                      ${(payoutReceiptView.presenceCount * payoutReceiptView.dailyRate) + payoutReceiptView.monthlyResearchAllowance} USD
                    </span>
                  </p>
                </div>
              </div>

              <div className="p-3 bg-black/40 rounded-lg text-[10px] text-slate-400 border border-white/5 space-y-1">
                <p><strong>Bénéficiaire :</strong> {payoutReceiptView.structure}</p>
                <p><strong>Banque / Compte :</strong> {payoutReceiptView.payoutMethod} - {payoutReceiptView.accountDetails}</p>
                <p><strong>Statut :</strong> <span className="text-emerald-400 font-bold">{payoutReceiptView.status === 'Traité' ? 'Liquidé via pain.001' : 'En attente de virement'}</span></p>
              </div>
            </div>

            <div className="flex justify-end gap-2 text-xs pt-4 border-t border-white/10 font-sans">
              <button
                onClick={() => setPayoutReceiptView(null)}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white font-bold rounded-lg cursor-pointer"
              >
                Fermer
              </button>
              <button
                onClick={() => {
                  alert("Téléchargement du reçu PDF simulé avec succès !");
                  setPayoutReceiptView(null);
                }}
                className="px-4 py-2 bg-emerald-500 text-black font-extrabold rounded-lg hover:bg-emerald-400 cursor-pointer"
              >
                Télécharger PDF
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
