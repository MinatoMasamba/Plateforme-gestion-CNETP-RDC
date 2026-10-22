(function () {
    const body = document.body;
    const toggle = document.querySelector('[data-space-menu-toggle]');
    const backdrop = document.querySelector('.space-nav-backdrop');
    if (!toggle) return;

    function setOpen(open) {
        body.classList.toggle('space-menu-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
        if (backdrop) backdrop.hidden = !open;
    }

    toggle.addEventListener('click', () => {
        setOpen(!body.classList.contains('space-menu-open'));
    });

    document.querySelectorAll('[data-space-menu-close]').forEach((element) => {
        element.addEventListener('click', () => setOpen(false));
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') setOpen(false);
    });
})();
