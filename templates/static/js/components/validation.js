/**
 * Validation Public Module Component
 */
const ValidationModule = {
    render(container) {
        container.innerHTML = `
            <div class="flex-1 p-6 overflow-y-auto">
                <h2 class="text-2xl font-extrabold text-white mb-6">Bibliothèque Publique</h2>
                <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                    <h3 class="text-xl font-bold text-slate-200 mb-4">Normes Publiées</h3>
                    <ul class="space-y-3">
                        <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                            <div>
                                <p class="font-semibold text-slate-100">ISO 9001:2015 - Qualité</p>
                                <p class="text-xs text-slate-400">Publiée le: 12 Mars 2026</p>
                            </div>
                            <button class="px-3 py-1 bg-blue-600/20 text-blue-300 rounded-md text-xs font-semibold hover:bg-blue-500/30 transition-colors">
                                Consulter
                            </button>
                        </li>
                        <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                            <div>
                                <p class="font-semibold text-slate-100">ISO 27001:2022 - Sécurité</p>
                                <p class="text-xs text-slate-400">Publiée le: 01 Février 2026</p>
                            </div>
                            <button class="px-3 py-1 bg-blue-600/20 text-blue-300 rounded-md text-xs font-semibold hover:bg-blue-500/30 transition-colors">
                                Consulter
                            </button>
                        </li>
                        <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                            <div>
                                <p class="font-semibold text-slate-100">Charte Nationale de l'IA</p>
                                <p class="text-xs text-slate-400">Publiée le: 20 Janvier 2026</p>
                            </div>
                            <button class="px-3 py-1 bg-blue-600/20 text-blue-300 rounded-md text-xs font-semibold hover:bg-blue-500/30 transition-colors">
                                Consulter
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
        `;
        initLucide();
    }
};
