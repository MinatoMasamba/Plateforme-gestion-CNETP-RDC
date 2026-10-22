(() => {
  const sections = JSON.parse(document.getElementById('counselor-chart-data').textContent);
  const chartInstances = new Map();
  const menu = document.getElementById('counselor-menu');
  const sidebar = document.getElementById('counselor-sidebar');
  const palette = ['#087fac', '#e6a43b', '#40a88e', '#765cb5'];
  function render(section) {
    if (!window.echarts) return;
    for (const chart of section.charts) {
      if (!chart.configured || chartInstances.has(chart.key)) continue;
      const element = document.getElementById(`chart-${chart.key}`);
      if (!element) continue;
      const instance = echarts.init(element);
      chartInstances.set(chart.key, instance);
      const dark = document.documentElement.classList.contains('dark');
      instance.setOption({
        color: palette,
        textStyle: {color: dark ? '#b9cfdb' : '#425d6e'},
        tooltip: {trigger: 'axis'},
        legend: {bottom: 0, textStyle: {color: dark ? '#b9cfdb' : '#425d6e'}},
        grid: {left: 42, right: 16, top: 20, bottom: 55, containLabel: true},
        xAxis: {type: 'category', data: chart.labels, axisLabel: {rotate: chart.labels.length > 7 ? 35 : 0, color: dark ? '#b9cfdb' : '#425d6e'}},
        yAxis: {type: 'value', min: 0, axisLabel: {color: dark ? '#b9cfdb' : '#425d6e'}},
        series: chart.series.map((series, index) => ({name: series.name, type: chart.kind, smooth: chart.kind === 'line', data: series.values, barMaxWidth: 36, areaStyle: chart.kind === 'line' && index === 0 ? {opacity: .08} : undefined})),
      });
      instance.on('click', () => { const details = element.parentElement.querySelector('.chart-data'); details.open = true; details.scrollIntoView({behavior: 'smooth', block: 'nearest'}); });
    }
    requestAnimationFrame(() => chartInstances.forEach(item => item.resize()));
  }
  function show(key) {
    const match = sections.find(section => section.key === key) || sections[0];
    document.querySelectorAll('[data-section-panel]').forEach(panel => { panel.hidden = panel.dataset.sectionPanel !== match.key; });
    document.querySelectorAll('[data-section]').forEach(link => { if (link.dataset.section === match.key) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current'); });
    sidebar.classList.remove('open'); menu.setAttribute('aria-expanded', 'false');
    render(match);
    document.getElementById('counselor-main').scrollIntoView({block: 'start'});
  }
  menu.addEventListener('click', () => { const open = sidebar.classList.toggle('open'); menu.setAttribute('aria-expanded', String(open)); });
  document.querySelectorAll('[data-section]').forEach(link => link.addEventListener('click', () => show(link.dataset.section)));
  window.addEventListener('hashchange', () => show(location.hash.slice(1)));
  window.addEventListener('resize', () => chartInstances.forEach(item => item.resize()));
  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => { for (const item of chartInstances.values()) item.dispose(); chartInstances.clear(); setTimeout(() => show(location.hash.slice(1)), 20); });
  show(location.hash.slice(1));
})();
