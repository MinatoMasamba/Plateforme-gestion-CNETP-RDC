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
        if (!sidebar || !toggle) {
            return;
        }

        function setOpen(open) {
            sidebar.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            if (overlay) {
                overlay.hidden = !open;
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
