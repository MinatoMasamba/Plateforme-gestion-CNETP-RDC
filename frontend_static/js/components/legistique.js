/**
 * Legistique Module Component
 */
const LegistiqueModule = {
    render(container) {
        container.innerHTML = `
            <div class="flex-1 p-6 overflow-y-auto">
                <h2 class="text-2xl font-extrabold text-white mb-6">Bureau Légistique</h2>
                <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                    <h3 class="text-xl font-bold text-slate-200 mb-4">Dossiers en Traitement</h3>
                    <ul class="space-y-3">
                        <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                            <div>
                                <p class="font-semibold text-slate-100">Analyse Conformité Décret N°123</p>
                                <p class="text-xs text-slate-400">Statut: En Revue</p>
                            </div>
                            <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/20 text-amber-300">Urgent</span>
                        </li>
                        <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                            <div>
                                <p class="font-semibold text-slate-100">Toilettage Juridique Charte IA</p>
                                <p class="text-xs text-slate-400">Statut: Terminé</p>
                            </div>
                            <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-green-500/20 text-green-300">Validé</span>
                        </li>
                    </ul>
                </div>
            </div>
        `;
        initLucide();
    }
};
