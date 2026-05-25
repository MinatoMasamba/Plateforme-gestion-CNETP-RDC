/**
 * Application principale - Gestion de l'état et du rendu
 */

// État global de l'application
const state = {
    isLoading: true,
    isDarkMode: true,
    activeTab: 'editor',
    selectedDocId: null,
    documents: [],
    collaborators: [],
    experts: [],
    workingGroups: [],
    activeCollaborator: null,
    userProfile: {
        name: "Édouard Masamba",
        email: "edmasamba100@gmail.com",
        role: "ADMIN"
    }
};

// Initialisation Lucide Icons
function initLucide() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Setup du thème
function setupThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    btn.addEventListener('click', () => {
        state.isDarkMode = !state.isDarkMode;
        if (state.isDarkMode) {
            html.classList.add('dark');
            btn.textContent = '🌙 Thème Sombre';
        } else {
            html.classList.remove('dark');
            btn.textContent = '☀️ Thème Clair';
        }
    });
}

// Rendu des onglets
function renderTabs() {
    const tabsContainer = document.getElementById('nav-tabs');
    const tabs = [
        { id: 'editor', label: 'Éditeur', icon: 'file-text' },
        { id: 'history', label: 'Historique', icon: 'history' },
        { id: 'experts', label: 'Experts & Groupes', icon: 'users' },
        { id: 'meetings', label: 'Réunions & Votes', icon: 'vote' },
        { id: 'financial', label: 'Cotisations', icon: 'landmark' },
        { id: 'validation', label: 'Bibliothèque', icon: 'award' },
        { id: 'legistique', label: 'Bureau Légistique', icon: 'book-open' },
        { id: 'public-portal', label: '🌐 Portail Public', icon: 'book-open', isExternal: true, path: '/public-norms'}
    ];

    tabsContainer.innerHTML = tabs.map(tab => {
        if (tab.isExternal) {
            return `
                <a href="${tab.path}" target="_blank" class="h-14 px-3.5 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-2 border-b-2 border-transparent shrink-0 cursor-pointer text-slate-400 hover:text-white hover:bg-white/5">
                    <i data-lucide="${tab.icon}" class="h-4 w-4 text-teal-500 animate-pulse"></i>
                    ${tab.label}
                </a>
            `;
        }
        return `
            <button onclick="setActiveTab('${tab.id}')" id="tab-${tab.id}" 
                class="h-14 px-3 text-[10.5px] font-bold tracking-wider uppercase transition-all flex items-center gap-1.5 border-b-2 shrink-0 ${state.activeTab === tab.id ? 'border-blue-500 text-blue-400 bg-blue-500/10' : 'border-transparent text-slate-400 hover:text-white hover:bg-white/5'}">
                <i data-lucide="${tab.icon}" class="h-4 w-4"></i>
                ${tab.label}
            </button>
        `;
    }).join('');
    initLucide();
}

// Changement d'onglet
window.setActiveTab = (tabId) => {
    state.activeTab = tabId;
    renderTabs();
    renderViewport();
};

// Rendu de la barre latérale
function renderSidebar() {
    const nav = document.getElementById('sidebar-nav');
    if (!state.documents.length) {
        nav.innerHTML = '<div class="p-4 text-slate-500 text-sm">Aucun document</div>';
        return;
    }

    nav.innerHTML = `
        <div class="py-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Documents Récents</div>
        ${state.documents.map(doc => `
            <button onclick="selectDoc('${doc.id}')" 
                class="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm ${state.selectedDocId === doc.id ? 'bg-blue-500/10 text-blue-400' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}">
                <i data-lucide="file-text" class="h-4 w-4"></i>
                <span class="truncate">${doc.code || doc.title}</span>
            </button>
        `).join('')}
    `;
    initLucide();
}

// Sélection d'un document
window.selectDoc = (docId) => {
    state.selectedDocId = docId;
    renderSidebar();
    renderViewport();
};

// Rendu du viewport principal
function renderViewport(error = null) {
    const container = document.getElementById('viewport');
    
    if (state.isLoading) {
        container.innerHTML = '<div class="flex-1 flex items-center justify-center"><i data-lucide="loader" class="h-8 w-8 text-blue-500 animate-spin"></i></div>';
        initLucide();
        return;
    }

    if (error) {
        container.innerHTML = `<div class="flex-1 flex items-center justify-center text-red-400">${error}</div>`;
        return;
    }

    switch (state.activeTab) {
        case 'editor':
            renderEditor(container);
            break;
        case 'history':
            if (state.selectedDocId) {
                console.log("Selected Doc ID:", state.selectedDocId);
                console.log("Documents in state:", state.documents);
                const doc = state.documents.find(d => d.id === state.selectedDocId);
                console.log("Found document for rendering:", doc);
                HistoryArea.render(container, state.selectedDocId);
            } else {
                console.log("No document selected. Documents state:", state.documents);
                container.innerHTML = '<div class="p-8 text-slate-500">Sélectionnez un document pour voir l'historique.</div>';
            }
            break;
            case 'experts':

            ExpertsModule.render(container);
            break;
        case 'meetings':
            MeetingsModule.render(container);
            break;
        case 'financial':
            FinancialModule.render(container);
            break;
        case 'validation':
            ValidationModule.render(container);
            break;
        case 'legistique':
            LegistiqueModule.render(container);
            break;
        default:
            container.innerHTML = `<div class="p-8 text-slate-500">Module <b>${state.activeTab}</b> non disponible.</div>`;
    }
    initLucide();
}

// Rendu de l'éditeur
function renderEditor(container) {
    const doc = state.documents.find(d => d.id === state.selectedDocId);
    if (!doc) {
        container.innerHTML = '<div class="p-8 text-slate-500">Aucun document sélectionné.</div>';
        return;
    }

    container.innerHTML = `
        <div class="flex-1 flex flex-col p-6 overflow-hidden">
            <div class="mb-6">
                <h2 class="text-3xl font-bold text-white mb-2">${doc.title}</h2>
                <p class="text-slate-500 text-sm">${doc.code} • Dernière modification par ${doc.lastAuthor || 'Système'}</p>
            </div>
            <div class="flex-1 bg-white/5 border border-white/10 rounded-lg p-6 overflow-y-auto mb-4">
                <div id="editor-content" class="prose prose-invert max-w-none text-slate-300 leading-relaxed">
                    ${doc.content || '<em class="text-slate-500">Contenu du document...</em>'}
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button id="save-doc-btn" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition-all shadow-lg shadow-blue-600/20">
                    Sauvegarder
                </button>
            </div>
        </div>
    `;
    
    document.getElementById('save-doc-btn').addEventListener('click', handleSaveVersion);
}

// Sauvegarde de version
async function handleSaveVersion() {
    const doc = state.documents.find(d => d.id === state.selectedDocId);
    if (!doc || !state.activeCollaborator) return;

    const content = document.getElementById('editor-content').innerHTML;
    const comment = prompt("Entrez un commentaire pour cette version:");

    if (comment === null) return;

    try {
        const data = {
            content,
            author: state.activeCollaborator.name || state.userProfile.name,
            email: state.activeCollaborator.email || state.userProfile.email,
            comment,
        };
        const result = await API.saveVersion(state.selectedDocId, data);
        
        if (result.document) {
            state.documents = state.documents.map((d) => d.id === state.selectedDocId ? result.document : d);
            renderSidebar();
            alert(`Version v${result.version.versionNumber} sauvegardée avec succès !`);
        } else {
            alert(result.error || "Échec de la sauvegarde.");
        }
    } catch (err) {
        console.error("Save failed:", err);
        alert("Erreur lors de la sauvegarde du document.");
    }
}

// Chargement des données initiales
async function loadInitialData() {
    state.isLoading = true;
    renderViewport();

    try {
        const [docs, collabs] = await Promise.all([
            API.fetchDocs(),
            API.fetchCollaborators()
        ]);

        state.documents = docs || [];
        state.collaborators = collabs || [];
        state.activeCollaborator = state.collaborators[0] || state.userProfile;

        console.log("Loaded Documents:", state.documents);
        console.log("Selected Doc ID initially:", state.selectedDocId);

        // Données de démonstration si API ne retourne rien
        if (state.documents.length === 0) {
            state.documents = [
                {
                    id: 'doc-1',
                    code: 'CTM-8-001',
                    title: 'Matériaux de Construction Locaux - Spécifications',
                    content: '<h3>Contenu du document CTM 8</h3><p>Spécifications techniques pour les matériaux de construction locaux...</p>',
                    lastAuthor: 'Système',
                    versionNumber: 1
                }
            ];
            console.log("Using mock documents as API returned empty:", state.documents);
        }

        state.selectedDocId = state.documents[0]?.id || null;
        console.log("Final selectedDocId after loading:", state.selectedDocId);

        // Données des experts et groupes de travail
        state.workingGroups = [
            { id: "wg-8.1", code: "WG 8.1", title: "Matériaux de Construction Locaux", tag: "Actif" },
            { id: "wg-1.1", code: "WG 1.1", title: "Sols & Géo-mécanique", tag: "Session libre" }
        ];

        state.experts = [
            { id: "exp-1", name: "Dr. Jean Kaseba", role: "Expert Senior", structure: "INBTP" },
            { id: "exp-2", name: "Ing. Marie Mbala", role: "Coordinatrice", structure: "CNETP" }
        ];

        state.isLoading = false;
        state.selectedDocId = state.documents[0]?.id || null;
        
        renderSidebar();
        renderTabs();
        renderViewport();
        
        document.getElementById('user-name').textContent = state.userProfile.name;
    } catch (err) {
        console.error("Failed to load initial data:", err);
        state.isLoading = false;
        renderViewport("Erreur de chargement des données");
    }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    renderTabs();
    loadInitialData();
    
    // Rendre le widget de messagerie
    Messaging.render(document.body);
});
Messaging.render(document.body);
});
