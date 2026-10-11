(function () {
    const root = document.documentElement;
    const metaTheme = document.querySelector('meta[name="theme-color"]');

    function readTheme() {
        try {
            const stored = localStorage.getItem('theme-preference');
            if (stored === 'dark' || stored === 'light') return stored;
        } catch (error) {}

        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }

    function updateControls(theme) {
        const isDark = theme === 'dark';
        document.querySelectorAll('[data-theme-toggle]').forEach((toggle) => {
            toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            toggle.setAttribute('aria-label', isDark ? 'Activer le thème clair' : 'Activer le thème sombre');
            toggle.setAttribute('title', isDark ? 'Activer le thème clair' : 'Activer le thème sombre');
        });
    }

    function applyTheme(theme, persist) {
        const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
        root.classList.toggle('dark', normalizedTheme === 'dark');
        root.dataset.theme = normalizedTheme;
        if (metaTheme) metaTheme.setAttribute('content', normalizedTheme === 'dark' ? '#020617' : '#0095c9');
        if (persist) {
            try {
                localStorage.setItem('theme-preference', normalizedTheme);
            } catch (error) {}
        }
        updateControls(normalizedTheme);
    }

    function toggleTheme() {
        applyTheme(root.classList.contains('dark') ? 'light' : 'dark', true);
    }

    window.CNETPTheme = { apply: applyTheme, toggle: toggleTheme };
    window.toggleCnetpTheme = toggleTheme;
    applyTheme(readTheme(), false);

    document.addEventListener('click', (event) => {
        const target = event.target instanceof Element
            ? event.target.closest('[data-theme-toggle]')
            : null;
        if (!target) return;
        event.preventDefault();
        event.stopPropagation();
        toggleTheme();
    }, true);

    document.addEventListener('DOMContentLoaded', () => updateControls(root.classList.contains('dark') ? 'dark' : 'light'));
})();
