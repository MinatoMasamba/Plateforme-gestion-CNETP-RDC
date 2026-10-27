(function () {
    'use strict';

    var charts = [];

    function refreshIcons() {
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
        }
    }

    function initSidebar() {
        var sidebar = document.getElementById('console-sidebar');
        var toggle = document.querySelector('[data-console-sidebar-toggle]');
        var overlay = document.querySelector('[data-console-sidebar-close]');
        var dismiss = document.querySelector('[data-console-sidebar-dismiss]');
        var mobile = window.matchMedia('(max-width: 760px)');
        if (!sidebar || !toggle) {
            return;
        }

        function setOpen(open) {
            var wasOpen = sidebar.classList.contains('is-open');
            sidebar.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            sidebar.inert = mobile.matches && !open;
            document.body.classList.toggle('console-mobile-nav-open', mobile.matches && open);
            if (overlay) {
                overlay.hidden = !open;
            }
            if (open) {
                (dismiss || sidebar.querySelector('a')).focus();
            } else if (wasOpen) {
                toggle.focus();
            }
        }

        toggle.addEventListener('click', function () {
            setOpen(!sidebar.classList.contains('is-open'));
        });
        if (overlay) {
            overlay.addEventListener('click', function () {
                setOpen(false);
            });
        }
        if (dismiss) dismiss.addEventListener('click', function () { setOpen(false); });
        sidebar.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.matchMedia('(max-width: 760px)').matches) {
                    setOpen(false);
                }
            });
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                setOpen(false);
            }
            if (event.key === 'Tab' && mobile.matches && sidebar.classList.contains('is-open')) {
                var focusable = Array.from(sidebar.querySelectorAll('a[href], button:not([disabled])'));
                var first = focusable[0];
                var last = focusable[focusable.length - 1];
                if (event.shiftKey && document.activeElement === first) {
                    event.preventDefault(); last.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                    event.preventDefault(); first.focus();
                }
            }
        });
        function syncMode() { setOpen(false); }
        if (mobile.addEventListener) mobile.addEventListener('change', syncMode);
        syncMode();
    }

    function initListFilters() {
        document.querySelectorAll('[data-console-filter-select]').forEach(function (select) {
            select.addEventListener('change', function () {
                window.location.assign(select.value);
            });
        });
    }

    function initDirectory() {
        var directory = document.querySelector('[data-expert-directory]');
        if (!directory) return;
        var form = directory.querySelector('[data-directory-filters]');
        var structures = directory.querySelector('[data-structure-filter]');
        var search = structures.querySelector('[data-structure-search]');
        var options = Array.from(structures.querySelectorAll('[data-structure-option]'));
        var count = structures.querySelector('[data-structure-count]');
        var empty = structures.querySelector('[data-structure-empty]');
        function updateCount() {
            var total = structures.querySelectorAll('input[type="checkbox"]:checked').length;
            count.textContent = total;
            count.hidden = total === 0;
        }
        function fold(text) { return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr'); }
        search.addEventListener('input', function () {
            var needle = fold(search.value.trim());
            var visible = 0;
            options.forEach(function (option) {
                option.hidden = !fold(option.textContent).includes(needle);
                if (!option.hidden) visible++;
            });
            empty.hidden = visible > 0;
        });
        structures.addEventListener('change', updateCount);
        structures.querySelector('[data-structure-clear]').addEventListener('click', function () {
            structures.querySelectorAll('input[type="checkbox"]').forEach(function (input) { input.checked = false; });
            updateCount();
        });
        directory.querySelectorAll('[data-popover-close]').forEach(function (button) {
            button.addEventListener('click', function () {
                var details = button.closest('details'); details.open = false; details.querySelector('summary').focus();
            });
        });
        directory.querySelectorAll('.console-popover').forEach(function (details) {
            details.addEventListener('toggle', function () {
                if (!details.open) return;
                directory.querySelectorAll('.console-popover').forEach(function (other) { if (other !== details) other.open = false; });
                var panel = details.querySelector('.console-popover-panel');
                var rect = panel.getBoundingClientRect();
                if (rect.right > window.innerWidth - 16) { panel.style.left = 'auto'; panel.style.right = '0'; }
                if (rect.left < 16) { panel.style.right = 'auto'; panel.style.left = '0'; }
            });
        });
        document.addEventListener('click', function (event) {
            directory.querySelectorAll('details[open]').forEach(function (details) {
                if (!details.contains(event.target) && !(details.consolePanel && details.consolePanel.contains(event.target))) details.open = false;
            });
        });
        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') return;
            directory.querySelectorAll('details[open]').forEach(function (details) {
                details.open = false; details.querySelector('summary').focus();
            });
        });
        directory.querySelectorAll('[data-console-row-menu]').forEach(function (details) {
            var panel = details.querySelector('.console-row-menu-panel');
            details.consolePanel = panel;
            panel.addEventListener('keydown', function (event) {
                var links = Array.from(panel.querySelectorAll('a[href]'));
                var index = links.indexOf(document.activeElement);
                if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    links[(index + (event.key === 'ArrowDown' ? 1 : links.length - 1)) % links.length].focus();
                } else if (event.key === 'Tab' && ((!event.shiftKey && index === links.length - 1) || (event.shiftKey && index === 0))) {
                    event.preventDefault(); details.open = false; details.querySelector('summary').focus();
                }
            });
            details.addEventListener('toggle', function () {
                if (!details.open) { details.appendChild(panel); return; }
                directory.querySelectorAll('[data-console-row-menu]').forEach(function (other) { if (other !== details) other.open = false; });
                var rect = details.querySelector('summary').getBoundingClientRect();
                // Les surfaces floutées et le tableau défilable ne doivent pas rogner le menu.
                document.body.appendChild(panel);
                panel.style.position = 'fixed';
                panel.style.right = 'auto';
                panel.style.left = Math.max(12, Math.min(rect.right - panel.offsetWidth, window.innerWidth - panel.offsetWidth - 12)) + 'px';
                panel.style.top = (rect.bottom + panel.offsetHeight + 8 > window.innerHeight ? Math.max(12, rect.top - panel.offsetHeight - 8) : rect.bottom + 8) + 'px';
                panel.querySelector('a').focus();
            });
        });
        var scroll = directory.querySelector('.expert-table-scroll');
        if (scroll) scroll.addEventListener('scroll', function () {
            directory.querySelectorAll('[data-console-row-menu][open]').forEach(function (details) { details.open = false; });
        });
        function closeMenus() { directory.querySelectorAll('details[open]').forEach(function (details) { details.open = false; }); }
        window.addEventListener('resize', closeMenus);
        var start = directory.querySelector('#expert-date-from');
        var end = directory.querySelector('#expert-date-to');
        function validateDates() {
            end.setCustomValidity(start.value && end.value && start.value > end.value ? 'La date de fin doit être postérieure ou égale à la date de début.' : '');
        }
        start.addEventListener('change', validateDates);
        end.addEventListener('change', validateDates);
        form.addEventListener('submit', function () {
            form.setAttribute('aria-busy', 'true');
            var submit = form.querySelector('button[type="submit"]');
            submit.disabled = true;
            submit.querySelector('span').textContent = 'Chargement…';
        });
        window.addEventListener('pageshow', function () {
            form.removeAttribute('aria-busy');
            var submit = form.querySelector('button[type="submit"]'); submit.disabled = false; submit.querySelector('span').textContent = 'Appliquer';
        });
    }

    function chartTheme() {
        var dark = document.documentElement.classList.contains('dark');
        return {
            text: dark ? '#cbd5e1' : '#42526b',
            muted: dark ? '#8fa3ba' : '#6b7c93',
            grid: dark ? 'rgba(148,163,184,.14)' : 'rgba(100,116,139,.14)',
            tooltipBg: dark ? '#122239' : '#ffffff',
            tooltipText: dark ? '#e5edf7' : '#102033',
            palette: ['#087fac', '#e6a43b', '#40a88e', '#765cb5', '#d4af37', '#c65b52']
        };
    }

    function disposeCharts() {
        charts.forEach(function (chart) {
            try {
                chart.dispose();
            } catch (error) {
                // ignore
            }
        });
        charts = [];
    }

    function initCharts() {
        var dataElement = document.getElementById('console-chart-data');
        if (!dataElement || !window.echarts) {
            return;
        }
        var data;
        try {
            data = JSON.parse(dataElement.textContent);
        } catch (error) {
            return;
        }
        disposeCharts();
        var theme = chartTheme();
        var base = {
            backgroundColor: 'transparent',
            textStyle: { fontFamily: 'Inter, system-ui, sans-serif', color: theme.text },
            tooltip: {
                backgroundColor: theme.tooltipBg,
                borderColor: theme.grid,
                textStyle: { color: theme.tooltipText, fontSize: 11 },
                confine: true
            }
        };

        var activityElement = document.getElementById('console-chart-activity');
        if (activityElement && data.activity) {
            var activity = window.echarts.init(activityElement);
            activity.setOption(Object.assign({}, base, {
                grid: { left: 34, right: 16, top: 32, bottom: 30 },
                legend: {
                    top: 0,
                    right: 0,
                    textStyle: { color: theme.muted, fontSize: 10 },
                    itemWidth: 10,
                    itemHeight: 8
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: data.activity.labels,
                    axisLine: { lineStyle: { color: theme.grid } },
                    axisLabel: { color: theme.muted, fontSize: 9 },
                    axisTick: { show: false }
                },
                yAxis: {
                    type: 'value',
                    splitLine: { lineStyle: { color: theme.grid } },
                    axisLabel: { color: theme.muted, fontSize: 9 }
                },
                series: [
                    {
                        name: 'Administration',
                        type: 'line',
                        smooth: true,
                        symbol: 'circle',
                        symbolSize: 5,
                        data: data.activity.admin,
                        lineStyle: { width: 2.5, color: '#087fac' },
                        itemStyle: { color: '#087fac' },
                        areaStyle: { color: 'rgba(8,127,172,.12)' }
                    },
                    {
                        name: 'Métier',
                        type: 'line',
                        smooth: true,
                        symbol: 'circle',
                        symbolSize: 5,
                        data: data.activity.business,
                        lineStyle: { width: 2.5, color: '#e6a43b' },
                        itemStyle: { color: '#e6a43b' },
                        areaStyle: { color: 'rgba(230,164,59,.10)' }
                    }
                ]
            }));
            charts.push(activity);
        }

        var appsElement = document.getElementById('console-chart-apps');
        if (appsElement && data.apps) {
            var apps = window.echarts.init(appsElement);
            apps.setOption(Object.assign({}, base, {
                grid: { left: 92, right: 22, top: 10, bottom: 22 },
                xAxis: {
                    type: 'value',
                    splitLine: { lineStyle: { color: theme.grid } },
                    axisLabel: { color: theme.muted, fontSize: 9 }
                },
                yAxis: {
                    type: 'category',
                    data: data.apps.labels,
                    axisLine: { show: false },
                    axisTick: { show: false },
                    axisLabel: { color: theme.muted, fontSize: 9, width: 80, overflow: 'truncate' }
                },
                series: [{
                    type: 'bar',
                    data: data.apps.values,
                    barMaxWidth: 15,
                    itemStyle: {
                        borderRadius: [0, 5, 5, 0],
                        color: new window.echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: '#087fac' },
                            { offset: 1, color: '#40a88e' }
                        ])
                    }
                }]
            }));
            charts.push(apps);
        }

        var normsElement = document.getElementById('console-chart-norms');
        if (normsElement && data.norms) {
            var norms = window.echarts.init(normsElement);
            norms.setOption(Object.assign({}, base, {
                color: theme.palette,
                tooltip: Object.assign({}, base.tooltip, { trigger: 'item' }),
                legend: {
                    orient: 'vertical',
                    right: 0,
                    top: 'middle',
                    textStyle: { color: theme.muted, fontSize: 9 },
                    itemWidth: 9,
                    itemHeight: 9
                },
                series: [{
                    type: 'pie',
                    radius: ['48%', '72%'],
                    center: ['34%', '52%'],
                    avoidLabelOverlap: true,
                    itemStyle: { borderColor: 'transparent', borderWidth: 2 },
                    label: { show: false },
                    emphasis: { label: { show: true, fontSize: 11, fontWeight: 700 } },
                    data: data.norms.labels.map(function (label, index) {
                        return { name: label, value: data.norms.values[index] };
                    })
                }]
            }));
            charts.push(norms);
        }
    }

    function initConfirmations() {
        document.querySelectorAll('form[data-confirm]').forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!window.confirm(form.dataset.confirm)) {
                    event.preventDefault();
                }
            });
        });
    }

    function initThemeWatcher() {
        var root = document.documentElement;
        var observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === 'class') {
                    initCharts();
                }
            });
        });
        observer.observe(root, { attributes: true, attributeFilter: ['class'] });
        window.addEventListener('resize', function () {
            charts.forEach(function (chart) {
                chart.resize();
            });
        });
    }

    function init() {
        refreshIcons();
        initSidebar();
        initListFilters();
        initDirectory();
        initConfirmations();
        initCharts();
        initThemeWatcher();
    }

    window.ConsoleAdmin = {
        initCharts: initCharts,
        refreshIcons: refreshIcons
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
