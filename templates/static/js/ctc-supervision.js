(() => {
    const root = document.getElementById('ctc-supervision');
    const payload = document.getElementById('ctc-chart-data');
    if (!root || !payload) return;
    const data = JSON.parse(payload.textContent);
    const svgNS = 'http://www.w3.org/2000/svg';
    const palette = ['#0095c9', '#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6', '#14b8a6', '#64748b'];
    function svgNode(tag, attributes, text) {
        const node = document.createElementNS(svgNS, tag);
        Object.entries(attributes || {}).forEach(([name, value]) => node.setAttribute(name, value));
        if (text !== undefined) node.textContent = text;
        return node;
    }
    function donut(container, values) {
        const total = values.reduce((sum, item) => sum + item.count, 0);
        const chart = svgNode('svg', {
            viewBox: '0 0 140 140', role: 'img',
            'aria-label': `${total} éléments. ${values.map(item => `${item.label} : ${item.count}`).join('. ')}`,
            class: 'w-40 h-40 mx-auto text-slate-700 dark:text-slate-200',
        });
        chart.append(svgNode('circle', {cx: 70, cy: 70, r: 52, fill: 'none', stroke: '#94a3b8', 'stroke-opacity': '.15', 'stroke-width': 15}));
        const circumference = 2 * Math.PI * 52;
        let offset = 0;
        values.forEach((item, index) => {
            if (!total || !item.count) return;
            const length = circumference * item.count / total;
            const segment = svgNode('circle', {
                cx: 70, cy: 70, r: 52, fill: 'none', stroke: palette[index % palette.length],
                'stroke-width': 15, 'stroke-dasharray': `${length} ${circumference - length}`,
                'stroke-dashoffset': -offset, transform: 'rotate(-90 70 70)',
            });
            segment.append(svgNode('title', {}, `${item.label} : ${item.count} (${(item.count / total * 100).toFixed(1)} %)`));
            chart.append(segment);
            offset += length;
        });
        chart.append(svgNode('text', {x: 70, y: 72, 'text-anchor': 'middle', fill: 'currentColor', 'font-size': 25, 'font-weight': 800}, total));
        chart.append(svgNode('text', {x: 70, y: 89, 'text-anchor': 'middle', fill: '#64748b', 'font-size': 9}, 'TOTAL'));
        container.replaceChildren(chart);
        const legend = document.createElement('ul');
        legend.className = 'mt-3 space-y-2 text-xs';
        values.forEach((item, index) => {
            const row = document.createElement('li');
            row.className = 'flex items-start justify-between gap-2';
            const label = document.createElement('span');
            label.className = 'flex items-start gap-2 min-w-0 text-slate-500';
            const marker = document.createElement('span');
            marker.className = 'w-2.5 h-2.5 rounded-full shrink-0 mt-0.5';
            marker.style.backgroundColor = palette[index % palette.length];
            label.append(marker, document.createTextNode(item.label));
            const value = document.createElement('span');
            value.className = 'font-bold whitespace-nowrap';
            value.textContent = `${item.count} · ${total ? (item.count / total * 100).toFixed(1) : '0'} %`;
            row.append(label, value);
            legend.append(row);
        });
        if (!total) {
            const empty = document.createElement('p');
            empty.className = 'text-xs text-center text-slate-400 mt-2';
            empty.textContent = 'Aucune donnée sur cette période.';
            container.append(empty);
        }
        container.append(legend);
    }
    root.querySelectorAll('[data-ctc-donut]').forEach(container => donut(container, data[container.dataset.ctcDonut] || []));

    const timeline = document.getElementById('ctc-activity-timeline');
    const days = data.timeline || [];
    const maximum = Math.max(1, ...days.map(day => day.count));
    const scaleMaximum = Math.max(3, Math.ceil(maximum / 3) * 3);
    const graph = svgNode('svg', {viewBox: '0 0 800 190', role: 'img', 'aria-label': `Activité quotidienne, maximum ${maximum} actions par jour`, class: 'w-full h-44 text-slate-500'});
    for (let step = 0; step <= 3; step++) {
        const y = 145 - step * 40;
        graph.append(svgNode('line', {x1: 30, x2: 790, y1: y, y2: y, stroke: '#94a3b8', 'stroke-opacity': '.15'}));
        graph.append(svgNode('text', {x: 23, y: y + 3, 'text-anchor': 'end', fill: 'currentColor', 'font-size': 10}, scaleMaximum * step / 3));
    }
    const width = 760 / Math.max(days.length, 1);
    const tick = Math.max(1, Math.ceil(days.length / 6));
    days.forEach((day, index) => {
        const height = day.count / scaleMaximum * 120;
        const bar = svgNode('rect', {x: 30 + index * width + 1, y: 145 - height, width: Math.max(.5, width - 2), height, rx: Math.min(3, width / 4), fill: '#0095c9'});
        bar.append(svgNode('title', {}, `${day.date} : ${day.count} actions`));
        graph.append(bar);
        if (index % tick === 0 || index === days.length - 1) graph.append(svgNode('text', {x: 30 + index * width + width / 2, y: 165, 'text-anchor': 'middle', fill: 'currentColor', 'font-size': 10}, day.label));
    });
    timeline.replaceChildren(graph);

    function selectTab(name, focus = false) {
        const target = document.getElementById(`ctc-view-${name}`);
        if (!target) return;
        root.querySelectorAll('.ctc-supervision-view').forEach(view => view.classList.toggle('hidden', view !== target));
        root.querySelectorAll('[data-ctc-tab]').forEach(button => {
            const active = button.dataset.ctcTab === name;
            button.setAttribute('aria-selected', String(active));
            button.tabIndex = active ? 0 : -1;
            ['border-[#0095c9]', 'bg-[#0095c9]/10', 'text-[#0095c9]'].forEach(style => button.classList.toggle(style, active));
            ['border-slate-200', 'dark:border-white/10'].forEach(style => button.classList.toggle(style, !active));
            if (active && focus) button.focus();
        });
    }
    const tabs = [...root.querySelectorAll('[data-ctc-tab]')];
    tabs.forEach((button, index) => {
        button.addEventListener('click', () => selectTab(button.dataset.ctcTab));
        button.addEventListener('keydown', event => {
            let next;
            if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
            if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
            if (event.key === 'Home') next = 0;
            if (event.key === 'End') next = tabs.length - 1;
            if (next !== undefined) {
                event.preventDefault();
                selectTab(tabs[next].dataset.ctcTab, true);
            }
        });
    });
    const requestedTab = new URLSearchParams(location.search).get('ctc_tab');
    if (!root.dataset.ctmSidebar) {
        selectTab(tabs.some(tab => tab.dataset.ctcTab === requestedTab) ? requestedTab : 'journal');
    }
    const form = document.getElementById('ctc-supervision-filters');
    root.querySelectorAll('[data-ctc-user]').forEach(button => button.addEventListener('click', () => {
        form.elements.ctc_user.value = button.dataset.ctcUser;
        form.requestSubmit();
    }));
    root.querySelectorAll('[data-ctc-document]').forEach(button => button.addEventListener('click', () => {
        form.elements.ctc_document.value = button.dataset.ctcDocument;
        form.requestSubmit();
    }));
})();
