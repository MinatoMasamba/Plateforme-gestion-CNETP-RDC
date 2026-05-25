/**
 * Meetings and Votes Module Component
 */
const MeetingsModule = {
    render(container) {
        container.innerHTML = `
            <div class="flex-1 p-6 overflow-y-auto">
                <h2 class="text-2xl font-extrabold text-white mb-6">Réunions et Votes</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Meetings Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Prochaines Réunions</h3>
                        <ul class="space-y-3">
                            <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                                <div>
                                    <p class="font-semibold text-slate-100">Réunion CTM 8</p>
                                    <p class="text-xs text-slate-400">Date: 28 Mai 2026, 10:00</p>
                                </div>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300">À venir</span>
                            </li>
                            <li class="flex items-center justify-between bg-white/5 rounded-lg p-3 border border-white/10">
                                <div>
                                    <p class="font-semibold text-slate-100">WG 1.2 - Vote Final</p>
                                    <p class="text-xs text-slate-400">Date: 30 Mai 2026, 14:00</p>
                                </div>
                                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/20 text-amber-300">Urgent</span>
                            </li>
                        </ul>
                    </div>

                    <!-- Voting Section -->
                    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
                        <h3 class="text-xl font-bold text-slate-200 mb-4">Votes en Cours</h3>
                        <ul class="space-y-3">
                            <li class="bg-white/5 rounded-lg p-3 border border-white/10">
                                <p class="font-semibold text-slate-100">Approbation Norme ISO 9001</p>
                                <p class="text-xs text-slate-400 mb-2">Date limite: 27 Mai 2026</p>
                                <div class="flex gap-2">
                                    <button class="px-3 py-1 bg-green-600/20 text-green-300 rounded-md text-xs font-semibold">Pour</button>
                                    <button class="px-3 py-1 bg-red-600/20 text-red-300 rounded-md text-xs font-semibold">Contre</button>
                                    <button class="px-3 py-1 bg-slate-600/20 text-slate-300 rounded-md text-xs font-semibold">Abstention</button>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        initLucide();
    }
};
