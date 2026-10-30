/* Micro-animations CTC : comptage KPI, barres, anneaux et apparition en douceur.
   Sans dépendance, respecte prefers-reduced-motion, ne modifie aucune valeur. */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var EASE = 'cubic-bezier(.22,.61,.36,1)';

    function forEach(list, fn) { Array.prototype.forEach.call(list, fn); }

    function isNumeric(text) { return /^-?\d+(\.\d+)?$/.test(String(text).trim()); }

    function countUp(el) {
        var raw = (el.textContent || '').trim();
        var match = raw.match(/^(\d+)/);
        if (!match) return;
        var end = parseInt(match[1], 10);
        var suffix = raw.slice(match[1].length);
        if (reduceMotion || end === 0) { el.textContent = raw; return; }
        var duration = 800;
        var start = null;
        function step(ts) {
            if (start === null) start = ts;
            var progress = Math.min(1, (ts - start) / duration);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(end * eased) + suffix;
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = raw;
        }
        requestAnimationFrame(step);
    }

    function animateBar(fill) {
        var target = fill.style.width;
        if (!target) return;
        if (reduceMotion) { fill.style.width = target; return; }
        fill.style.transition = 'width .9s ' + EASE;
        fill.style.width = '0%';
        requestAnimationFrame(function () {
            requestAnimationFrame(function () { fill.style.width = target; });
        });
    }

    function reveal(el) {
        if (reduceMotion) { el.classList.add('ctc-revealed'); return; }
        el.classList.add('ctc-reveal-pending');
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                el.classList.remove('ctc-reveal-pending');
                el.classList.add('ctc-revealed');
            });
        });
    }

    function collectTargets(root) {
        forEach(root.querySelectorAll('.premium-kpi strong, .premium-donut__value, .ctc-metric strong'), countUp);
        forEach(root.querySelectorAll('.premium-chart-fill'), animateBar);
        forEach(root.querySelectorAll('.premium-chart-card, .premium-kpi, .premium-donut, .ctc-metric, .premium-hero'), reveal);
    }

    function init() {
        var roots = [
            document.querySelector('#view-dashboard'),
            document.querySelector('#view-statistiques'),
            document.querySelector('#view-experts'),
            document.querySelector('#view-tracabilite'),
            document.querySelector('#ctm-detail'),
        ].filter(Boolean);

        if (!('IntersectionObserver' in window)) {
            roots.forEach(function (root) { collectTargets(root); });
            return;
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                var root = entry.target;
                collectTargets(root);
                observer.unobserve(root);
            });
        }, { threshold: 0.08 });

        roots.forEach(function (root) { observer.observe(root); });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
