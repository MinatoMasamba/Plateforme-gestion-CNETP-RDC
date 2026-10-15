(() => {
    const content = document.getElementById('organisation-content');
    const panels = [...document.querySelectorAll('[data-org-section]')];
    const links = [...document.querySelectorAll('[data-org-nav]')];
    const mobile = document.getElementById('organisation-mobile-section');
    if (!content || !panels.length) return;
    function selectSection() {
        const requested = location.hash.slice(1);
        const name = panels.some(panel => panel.dataset.orgSection === requested) ? requested : 'copil';
        panels.forEach(panel => { panel.hidden = panel.dataset.orgSection !== name; });
        links.forEach(link => {
            if (link.dataset.orgNav === name) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
        mobile.value = name;
        content.scrollTop = 0;
    }
    links.forEach(link => link.addEventListener('click', event => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        if (location.hash !== link.hash) history.pushState(null, '', link.hash);
        selectSection();
        content.focus({preventScroll: true});
    }));
    mobile.addEventListener('change', () => {
        history.pushState(null, '', '#' + mobile.value);
        selectSection();
    });
    window.addEventListener('hashchange', selectSection);
    window.addEventListener('popstate', selectSection);
    selectSection();
})();
