/**
 * Utilitaires réseau partagés (site-wide).
 * Toute action déclenchée par un clic qui attend une réponse serveur doit :
 *  1. utiliser fetchWithTimeout() au lieu de fetch() pour ne jamais bloquer indéfiniment
 *     sur une connexion mobile instable (Lie-Fi),
 *  2. envelopper le bouton déclencheur avec withButtonLoading() pour désactiver le bouton,
 *     afficher un état de chargement, et restaurer/afficher une erreur claire en cas d'échec.
 */
(function () {
    const DEFAULT_TIMEOUT_MS = 15000;

    async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
            return await fetch(url, { ...options, signal: controller.signal });
        } catch (err) {
            if (err.name === 'AbortError') {
                throw new Error('TIMEOUT');
            }
            throw err;
        } finally {
            clearTimeout(timer);
        }
    }

    if (typeof window.showAppToast !== 'function') {
        window.showAppToast = function (message, type = 'info') {
            let host = document.getElementById('global-toast-host');
            if (!host) {
                host = document.createElement('div');
                host.id = 'global-toast-host';
                host.className = 'fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 items-end pointer-events-none';
                document.body.appendChild(host);
            }
            const colors = {
                success: 'bg-emerald-600',
                error: 'bg-red-600',
                warning: 'bg-amber-600',
                info: 'bg-slate-800',
            };
            const toast = document.createElement('div');
            toast.className = `${colors[type] || colors.info} text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg opacity-0 translate-y-2 transition-all duration-200 max-w-xs pointer-events-auto`;
            toast.textContent = message;
            host.appendChild(toast);
            requestAnimationFrame(() => toast.classList.remove('opacity-0', 'translate-y-2'));
            setTimeout(() => {
                toast.classList.add('opacity-0');
                setTimeout(() => toast.remove(), 200);
            }, 4000);
        };
    }

    function networkErrorMessage(err) {
        if (err && err.message === 'TIMEOUT') {
            return 'Connexion instable. Veuillez réessayer.';
        }
        if (err instanceof TypeError) {
            return 'Impossible de contacter le serveur. Vérifiez votre connexion.';
        }
        return (err && err.message) || 'Une erreur est survenue.';
    }

    /**
     * Enveloppe une action async déclenchée par un bouton : désactive le bouton et
     * affiche un état de chargement pendant l'exécution, restaure son état initial
     * ensuite, et affiche un toast d'erreur (timeout compris) en cas d'échec.
     * @param {HTMLElement} btn - le bouton qui a déclenché l'action (peut être null)
     * @param {() => Promise<any>} asyncFn - l'action à exécuter (doit utiliser fetchWithTimeout)
     * @param {{loadingHtml?: string, errorMessage?: string}} [options]
     */
    async function withButtonLoading(btn, asyncFn, options = {}) {
        if (!btn) {
            try {
                return await asyncFn();
            } catch (err) {
                window.showAppToast(options.errorMessage || networkErrorMessage(err), 'error');
                throw err;
            }
        }

        const originalHtml = btn.innerHTML;
        const originalDisabled = btn.disabled;
        btn.disabled = true;
        if (options.loadingHtml) {
            btn.innerHTML = options.loadingHtml;
        } else {
            btn.classList.add('opacity-60', 'cursor-wait');
        }

        try {
            return await asyncFn();
        } catch (err) {
            window.showAppToast(options.errorMessage || networkErrorMessage(err), 'error');
            throw err;
        } finally {
            btn.disabled = originalDisabled;
            btn.innerHTML = originalHtml;
            btn.classList.remove('opacity-60', 'cursor-wait');
            if (window.lucide && typeof window.lucide.createIcons === 'function') {
                window.lucide.createIcons();
            }
        }
    }

    window.fetchWithTimeout = fetchWithTimeout;
    window.withButtonLoading = withButtonLoading;
    window.networkErrorMessage = networkErrorMessage;
})();
