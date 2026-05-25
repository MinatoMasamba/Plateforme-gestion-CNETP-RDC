/**
 * Financial Module Component
 */
const FinancialModule = {
    render(container) {
        container.innerHTML = `
            <div class="flex-1 p-6 overflow-y-auto">
                <h2 class="text-2xl font-extrabold text-white mb-6">Cotisations & Indemnités</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Contributions Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Vos Cotisations</h3>
                        <ul class="space-y-3">
                            <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                                <div>
                                    <p class="font-semibold text-slate-100">Cotisation CTM 8 (Mai)</p>
                                    <p class="text-xs text-slate-400">Statut: Payé</p>
                                </div>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-green-500/20 text-green-300">Validé</span>
                            </li>
                            <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                                <div>
                                    <p class="font-semibold text-slate-100">Cotisation WG 1.2 (Juin)</p>
                                    <p class="text-xs text-slate-400">Statut: En attente</p>
                                </div>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/20 text-amber-300">En Cours</span>
                            </li>
                        </ul>
                    </div>

                    <!-- Allowances Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Vos Indemnités</h3>
                        <ul class="space-y-3">
                            <li class="bg-white/5 rounded-lg p-3 border border-white/10">
                                <p class="font-semibold text-slate-100">Indemnité Réunion CTM 8</p>
                                <p class="text-xs text-slate-400 mb-2">Montant: 180 USD</p>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300">Payé</span>
                            </li>
                            <li class="bg-white/5 rounded-lg p-3 border border-white/10">
                                <p class="font-semibold text-slate-100">Indemnité Recherche Mensuelle</p>
                                <p class="text-xs text-slate-400 mb-2">Montant: 800 USD</p>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-500/20 text-purple-300">En Attente</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        initLucide();
    }
};
