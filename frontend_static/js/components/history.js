/**
 * History Area Component
 */
const HistoryArea = {
    async render(container, docId) {
        container.innerHTML = '<div class="flex-1 flex items-center justify-center"><i data-lucide="loader" class="h-8 w-8 text-blue-500 animate-spin"></i></div>';
        initLucide();

        try {
            const versions = await API.fetchDocVersions(docId);
            if (versions.length === 0) {
                container.innerHTML = '<div class="p-8 text-slate-500">Aucun historique de version pour ce document.</div>';
                return;
            }

            container.innerHTML = `
                <div class="flex-1 p-6 overflow-y-auto">
                    <h2 class="text-2xl font-extrabold text-white mb-6">Historique des Versions</h2>
                    <div class="space-y-4">
                        ${versions.map(v => `
                            <div class="bg-white/5 border border-white/10 p-4 rounded-lg flex items-center justify-between">
                                <div>
                                    <p class="font-bold text-slate-200">Version ${v.versionNumber} par ${v.author}</p>
                                    <p class="text-slate-400 text-sm">${new Date(v.timestamp).toLocaleString()}</p>
                                    ${v.comment ? `<p class="text-slate-500 text-xs mt-1 italic">"${v.comment}"</p>` : ''}
                                </div>
                                <button onclick="HistoryArea.rollback('${docId}', ${v.versionNumber})" 
                                    class="px-3 py-1 bg-amber-600/20 text-amber-300 rounded-md text-xs font-semibold hover:bg-amber-500/30 transition-colors">
                                    Restaurer
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            initLucide();
        } catch (err) {
            console.error("Error rendering history:", err);
            container.innerHTML = '<div class="p-8 text-red-400">Erreur de chargement de l\'historique.</div>';
        }
    },

    async rollback(docId, versionNumber) {
        if (!confirm(`Êtes-vous sûr de vouloir restaurer la version v${versionNumber} ?`)) return;
        
        const userData = {
            author: state.userProfile.name,
            email: state.userProfile.email
        };

        try {
            const result = await API.rollbackVersion(docId, versionNumber, userData);
            if (result.document) {
                state.documents = state.documents.map(d => d.id === result.document.id ? result.document : d);
                state.selectedDocId = result.document.id;
                state.activeTab = 'editor';
                renderSidebar();
                renderTabs();
                renderViewport();
                alert(`Version v${versionNumber} restaurée avec succès !`);
            } else if (result.error) {
                alert(`Erreur de restauration: ${result.error}`);
            } else {
                alert("Erreur inconnue lors de la restauration.");
            }
        } catch (err) {
            console.error("Rollback failed:", err);
            alert("Échec de la restauration de la version.");
        }
    }
};
