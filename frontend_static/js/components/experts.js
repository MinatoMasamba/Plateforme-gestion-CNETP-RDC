/**
 * Experts Module Component
 */
const ExpertsModule = {
    render(container) {
        container.innerHTML = `
            <div class="flex-1 p-6 overflow-y-auto">
                <h2 class="text-2xl font-extrabold text-white mb-6">Experts et Groupes de Travail</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Working Groups Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Groupes de Travail (WG)</h3>
                        <ul class="space-y-3">
                            ${state.workingGroups.map(wg => `
                                <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                                    <div>
                                        <p class="font-semibold text-slate-100">${wg.code} - ${wg.title}</p>
                                        <p class="text-xs text-slate-400">Statut: ${wg.tag}</p>
                                    </div>
                                    <span class="px-2 py-0.5 text-xs font-medium rounded-full ${wg.tag === 'Actif' ? 'bg-green-500/20 text-green-300' : 'bg-slate-500/20 text-slate-300'}">
                                        ${wg.tag}
                                    </span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Experts Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Experts CNETP</h3>
                        <ul class="space-y-3">
                            ${state.experts.map(expert => `
                                <li class="flex items-center gap-3 bg-white/5 rounded-lg p-3 border border-white/10">
                                    <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm">
                                        ${expert.name.charAt(0)}
                                    </div>
                                    <div>
                                        <p class="font-semibold text-slate-100">${expert.name}</p>
                                        <p class="text-xs text-slate-400">${expert.role} (${expert.structure})</p>
                                    </div>
                                    <button onclick="Messaging.openChat('${expert.id}')" class="ml-auto p-2 bg-blue-600/20 text-blue-300 rounded-full hover:bg-blue-500/30 transition-colors">
                                        <i data-lucide="message-circle" class="h-4 w-4"></i>
                                    </button>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
        initLucide();
    }
};
