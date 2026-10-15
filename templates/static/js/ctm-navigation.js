(() => {
    const content = document.getElementById('ctm-content');
    const activity = document.getElementById('ctm-activity');
    if (!content || !activity) return;

    const supervisionViews = ['statistics', 'journal', 'team', 'documents', 'dossiers'];
    const views = {
        presentation: ['presentation'],
        statistics: ['statistics'],
        journal: ['journal'],
        team: ['team'],
        documents: ['documents'],
        dossiers: ['dossiers'],
        organisation: ['presentation', 'groups', 'experts'],
        groups: ['groups'],
        experts: ['experts'],
        normes: ['progress', 'published'],
        progress: ['progress'],
        published: ['published'],
    };
    activity.querySelectorAll('.ctc-supervision-view').forEach(panel => {
        const name = panel.id.replace('ctc-view-', '');
        panel.dataset.ctmPanel = name;
        panel.classList.remove('hidden');
        panel.setAttribute('role', 'region');
        panel.setAttribute('aria-labelledby', `ctm-nav-${name}`);
    });
    const panels = [...content.querySelectorAll('[data-ctm-panel]')];
    const buttons = [...document.querySelectorAll('[data-ctm-view]')];
    const mobile = document.getElementById('ctm-mobile-view');
    const form = document.getElementById('ctc-supervision-filters');
    const tabInput = document.createElement('input');
    tabInput.type = 'hidden';
    tabInput.name = 'ctc_tab';
    form.append(tabInput);

    function requestedView() {
        const hashView = location.hash.replace(/^#ctm-/, '');
        if (Object.hasOwn(views, hashView)) return hashView;
        const params = new URLSearchParams(location.search);
        const tab = params.get('ctc_tab');
        if (supervisionViews.includes(tab)) return tab;
        if (params.has('ctc_log_page')) return 'journal';
        if (params.has('ctc_doc_page')) return 'documents';
        return 'statistics';
    }

    function selectView(name, {navigate = false, focus = false} = {}) {
        if (!Object.hasOwn(views, name)) name = 'presentation';
        activity.hidden = !supervisionViews.includes(name);
        panels.forEach(panel => {
            panel.hidden = !views[name].includes(panel.dataset.ctmPanel);
        });
        buttons.forEach(button => {
            if (button.dataset.ctmView === name) button.setAttribute('aria-current', 'page');
            else button.removeAttribute('aria-current');
        });
        mobile.value = name;
        tabInput.value = supervisionViews.includes(name) ? name : 'journal';
        const action = new URL(form.action, location.href);
        action.hash = `ctm-${name}`;
        form.action = action.href;
        // Keep refresh, reset and pagination in the corresponding sidebar view.
        activity.querySelectorAll('a[href]').forEach(link => {
            const url = new URL(link.href, location.href);
            if (url.origin !== location.origin || url.pathname !== location.pathname) return;
            const tab = url.searchParams.get('ctc_tab');
            const target = supervisionViews.includes(tab) ? tab :
                link.closest('#ctc-view-journal') ? 'journal' : name;
            url.hash = `ctm-${target}`;
            link.href = url.href;
        });
        content.scrollTop = 0;
        if (navigate) {
            const url = new URL(location.href);
            url.hash = `ctm-${name}`;
            if (url.href !== location.href) history.pushState(null, '', url);
        }
        if (focus) content.focus({preventScroll: true});
    }

    buttons.forEach(button => button.addEventListener('click', () => {
        selectView(button.dataset.ctmView, {navigate: true, focus: true});
    }));
    mobile.addEventListener('change', () => selectView(mobile.value, {navigate: true}));
    window.addEventListener('popstate', () => selectView(requestedView()));
    window.addEventListener('hashchange', () => selectView(requestedView()));
    // Contributor/document shortcuts open the filtered journal after submission.
    activity.addEventListener('click', event => {
        if (event.target.closest('[data-ctc-user], [data-ctc-document]')) {
            tabInput.value = 'journal';
            const action = new URL(form.action, location.href);
            action.hash = 'ctm-journal';
            form.action = action.href;
        }
    }, true);
    selectView(requestedView());
})();
