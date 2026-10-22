(() => {
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const state = {norms: [], selected: null, version: null, chart: 'pie', history: false};
  const states = ['En cours', 'Terminé', 'En retard'];
  const colors = {'En cours': '#8eb3eb', 'Terminé': '#9cd5c8', 'En retard': '#ebd2a4'};
  const themeToggle = $('theme-toggle');
  function updateThemeToggle() {
    const dark = document.documentElement.classList.contains('dark');
    themeToggle.textContent = dark ? 'Thème clair' : 'Thème sombre';
    themeToggle.setAttribute('aria-pressed', String(dark));
  }
  themeToggle.addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme-preference', dark ? 'dark' : 'light');
    updateThemeToggle();
  });
  updateThemeToggle();
  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };
  function scopeUrl(id) {
    const next = new URLSearchParams();
    next.set('sc', id);
    return `${location.pathname}?${next}`;
  }
  $('scope-select').addEventListener('change', (event) => {
    location.assign(scopeUrl(event.target.value));
  });
  $('ctm-select')?.addEventListener('change', (event) => {
    const next = new URLSearchParams(location.search);
    next.set('sc', $('scope-select').value);
    next.delete('norme'); next.delete('wg');
    if (event.target.value) next.set('ctm', event.target.value); else next.delete('ctm');
    location.assign(`${location.pathname}?${next}`);
  });
  $('wg-select')?.addEventListener('change', (event) => {
    const next = new URLSearchParams(location.search);
    next.set('sc', $('scope-select').value);
    next.delete('norme');
    if (event.target.value) next.set('wg', event.target.value); else next.delete('wg');
    location.assign(`${location.pathname}?${next}`);
  });
  function selectNorm(id) {
    const norm = state.norms.find(item => item.id === Number(id));
    if (!norm) return;
    state.selected = norm;
    state.version = null;
    state.history = false;
    $('expert-filter').value = 'Tous';
    $('expert-search').value = '';
    const next = new URLSearchParams(location.search);
    next.set('norme', norm.id);
    history.replaceState(null, '', `${location.pathname}?${next}`);
    render();
  }
  function renderNorms() {
    const nav = $('norm-list');
    nav.replaceChildren();
    state.norms.forEach(norm => {
      const link = element('a', 'president-norm-link', norm.title);
      link.href = `#norme-${norm.id}`;
      link.dataset.normId = norm.id;
      link.title = `${norm.code} — ${norm.title}`;
      if (state.selected?.id === norm.id) { link.classList.add('is-selected'); link.setAttribute('aria-current', 'true'); }
      link.addEventListener('click', event => { event.preventDefault(); selectNorm(norm.id); });
      nav.append(link);
    });
    if (!state.norms.length) nav.append(element('p', 'empty', 'Aucune norme liée à ce périmètre.'));
  }
  function renderChart() {
    const norm = state.selected;
    const chart = $('chart');
    chart.replaceChildren();
    const total = norm.rows.reduce((sum, row) => sum + row.total, 0);
    const done = norm.rows.reduce((sum, row) => sum + row.done, 0);
    $('chart-summary').textContent = `${done} tâche${done > 1 ? 's' : ''} terminée${done > 1 ? 's' : ''} sur ${total} affectée${total > 1 ? 's' : ''}`;
    if (!norm.rows.length) { chart.append(element('p', 'empty', 'Aucune performance configurée pour cette norme.')); return; }
    if (state.chart === 'bar') {
      const bars = element('div', 'president-bars');
      const max = Math.max(...norm.rows.map(row => row.total), 1);
      norm.rows.forEach(row => {
        const item = element('div', 'president-bar-item');
        const bar = element('div', 'president-bar');
        bar.style.height = `${Math.max(6, row.total / max * 135)}px`;
        bar.title = `${row.name} : ${row.total} tâche(s)`;
        item.append(element('b', '', String(row.total)), bar, element('small', '', row.name));
        bars.append(item);
      });
      chart.append(bars);
      return;
    }
    const counts = Object.fromEntries(states.map(name => [name, norm.rows.filter(row => row.state === name).length]));
    let cursor = 0;
    const stops = states.map(name => {
      const start = cursor;
      cursor += counts[name] / norm.rows.length * 100;
      return `${colors[name]} ${start}% ${cursor}%`;
    });
    const donut = element('div', 'president-donut');
    donut.style.background = `conic-gradient(${stops.join(',')})`;
    const center = element('div', 'president-donut-center');
    center.append(element('strong', '', total ? `${Math.round(done / total * 100)} %` : '—'), element('small', '', total ? 'Tâches terminées' : 'Non configuré'));
    donut.append(center);
    const legend = element('div', 'president-legend');
    states.forEach(name => {
      const button = element('button', '', `${name}  ${counts[name]}`);
      button.type = 'button';
      button.style.setProperty('--legend-color', colors[name]);
      button.addEventListener('click', () => { $('expert-filter').value = $('expert-filter').value === name ? 'Tous' : name; renderRows(); });
      legend.append(button);
    });
    chart.append(donut, legend);
  }
  function renderRows() {
    const norm = state.selected;
    const query = $('expert-search').value.trim().toLocaleLowerCase('fr');
    const filter = $('expert-filter').value;
    const rows = norm.rows.filter(row => (filter === 'Tous' || row.state === filter) && row.name.toLocaleLowerCase('fr').includes(query));
    $('expert-count').textContent = norm.rows.length;
    $('visible-count').textContent = `${rows.length} expert${rows.length > 1 ? 's' : ''} affiché${rows.length > 1 ? 's' : ''}`;
    $('expert-empty').hidden = rows.length > 0;
    const body = $('expert-rows');
    body.replaceChildren();
    rows.forEach(row => {
      const tr = element('tr');
      const name = element('td');
      const person = element('div', 'person');
      person.append(element('span', 'avatar', row.name.split(/\s+/).slice(0, 2).map(word => word[0] || '').join('')));
      const personText = element('span');
      personText.append(element('b', '', row.name), element('small', '', row.state));
      person.append(personText);
      name.append(person);
      const tasks = element('td', 'time', `${row.done} / ${row.total}`);
      const performance = element('td');
      const percent = Math.round(row.done / row.total * 100);
      performance.append(element('div', 'progress-value', `${percent} %`));
      const progress = element('div', 'progress');
      const fill = element('i'); fill.style.width = `${percent}%`; progress.append(fill); performance.append(progress);
      const norms = element('td');
      const list = element('ul', 'table-norm-list');
      state.norms.filter(item => item.rows.some(expert => expert.id === row.id)).forEach(item => {
        const li = element('li');
        const link = element('a', `norm-link${item.id === norm.id ? ' is-selected' : ''}`, item.title);
        link.href = `#norme-${item.id}`;
        if (item.id === norm.id) link.setAttribute('aria-current', 'true');
        link.addEventListener('click', event => { event.preventDefault(); selectNorm(item.id); });
        li.append(link); list.append(li);
      });
      norms.append(list);
      tr.append(name, tasks, performance, norms, element('td', 'code', norm.code));
      body.append(tr);
    });
  }
  function renderReader() {
    const norm = state.selected;
    const version = state.version || norm.versions[0];
    $('reader-code').textContent = norm.code;
    $('reader-title').textContent = norm.title;
    $('dossier-link').hidden = !norm.dossier_url;
    if (norm.dossier_url) $('dossier-link').href = norm.dossier_url;
    $('reader-status').textContent = norm.status;
    $('reader-version').textContent = version ? `Version ${version.number}` : 'Aucune version enregistrée';
    $('reader-date').textContent = version?.date || '';
    $('version-count').textContent = norm.versions.length;
    $('paper-code').textContent = norm.code;
    $('paper-title').textContent = version?.title || norm.title;
    const content = $('paper-content');
    content.replaceChildren();
    const body = version?.content || norm.description;
    if (body) body.split(/\n\s*\n/).filter(Boolean).forEach(block => content.append(element('p', 'president-paragraph', block)));
    else content.append(element('p', 'president-paragraph', 'Aucun texte de document enregistré pour cette norme.'));
    if (version?.document_url) {
      const link = element('a', 'president-document-link', 'Ouvrir le document de cette version');
      link.href = version.document_url; link.target = '_blank'; link.rel = 'noopener'; content.append(link);
    }
    const historyList = $('history-list'); historyList.replaceChildren();
    norm.versions.forEach(item => {
      const button = element('button', 'version-card', `Version ${item.number} · ${item.date} · ${item.author}`);
      button.type = 'button';
      button.addEventListener('click', () => { state.version = item; state.history = false; renderReader(); });
      historyList.append(button);
    });
    if (!norm.versions.length) historyList.append(element('p', 'empty', 'Aucune version enregistrée.'));
    $('reader-experts').textContent = `${norm.rows.length} expert${norm.rows.length > 1 ? 's' : ''} avec tâches`;
    $('reader-tasks').textContent = `${norm.rows.reduce((sum, row) => sum + row.total, 0)} affectation(s) de tâche`;
    $('document-panel').hidden = state.history;
    $('history-panel').hidden = !state.history;
    $('document-tab').classList.toggle('tab-active', !state.history);
    $('history-tab').classList.toggle('tab-active', state.history);
  }
  function render() {
    if (!state.selected) return;
    $('workspace').hidden = false;
    $('performance-code').textContent = state.selected.code;
    renderNorms(); renderChart(); renderRows(); renderReader();
  }
  $('chart-pie').addEventListener('click', () => { state.chart = 'pie'; $('chart-pie').classList.add('active'); $('chart-bar').classList.remove('active'); $('chart-pie').setAttribute('aria-pressed', 'true'); $('chart-bar').setAttribute('aria-pressed', 'false'); renderChart(); });
  $('chart-bar').addEventListener('click', () => { state.chart = 'bar'; $('chart-bar').classList.add('active'); $('chart-pie').classList.remove('active'); $('chart-bar').setAttribute('aria-pressed', 'true'); $('chart-pie').setAttribute('aria-pressed', 'false'); renderChart(); });
  $('expert-search').addEventListener('input', renderRows);
  $('expert-filter').addEventListener('change', renderRows);
  $('document-tab').addEventListener('click', () => { state.history = false; renderReader(); });
  $('history-tab').addEventListener('click', () => { state.history = true; renderReader(); });
  $('method-button').addEventListener('click', () => $('method-dialog').showModal());
  fetch(`${document.body.dataset.source}${location.search}`, {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
    .then(response => { if (!response.ok) throw new Error(`Erreur ${response.status}`); return response.json(); })
    .then(data => { state.norms = data.norms; const selected = state.norms.find(item => item.id === Number(params.get('norme'))) || state.norms[0]; if (selected) selectNorm(selected.id); else renderNorms(); })
    .catch(() => { $('page-error').textContent = 'Impossible de charger les normes de ce périmètre.'; $('page-error').hidden = false; });
})();
