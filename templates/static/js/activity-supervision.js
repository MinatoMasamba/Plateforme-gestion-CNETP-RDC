(() => {
  const root = document.querySelector('[data-activity-root]');
  if (!root) return;
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.DJANGO_CSRF_TOKEN || '';

  // Les deux jeux d'onglets gardent tout le contenu dans le DOM pour les lecteurs d'écran.
  document.querySelectorAll('[data-view-tab]').forEach((button) => button.addEventListener('click', () => {
    const name = button.dataset.viewTab;
    document.querySelectorAll('[data-view-tab]').forEach((item) => {
      const active = item === button; item.setAttribute('aria-selected', String(active));
      item.classList.toggle('bg-white', active); item.classList.toggle('shadow-sm', active);
    });
    document.querySelectorAll('[data-view-panel]').forEach((panel) => panel.classList.toggle('hidden', panel.dataset.viewPanel !== name));
  }));
  document.querySelectorAll('[data-detail-tab]').forEach((button) => button.addEventListener('click', () => {
    const name = button.dataset.detailTab;
    document.querySelectorAll('[data-detail-tab]').forEach((item) => {
      const active = item === button; item.setAttribute('aria-selected', String(active));
      item.classList.toggle('border-sky-700', active); item.classList.toggle('text-sky-800', active);
      item.classList.toggle('border-transparent', !active); item.classList.toggle('text-slate-500', !active);
    });
    document.querySelectorAll('[data-detail-panel]').forEach((panel) => panel.classList.toggle('hidden', panel.dataset.detailPanel !== name));
  }));

  const postTransition = async (card, status) => {
    if (!status || !card?.dataset.transitionUrl) return false;
    if (!window.confirm(`Déplacer « ${card.dataset.taskTitle} » vers la nouvelle étape ?`)) return false;
    const form = new FormData(); form.append('status', status);
    const response = await fetch(card.dataset.transitionUrl, {method:'POST', credentials:'same-origin', headers:{'X-CSRFToken':csrf}, body:form});
    const data = await response.json();
    if (!response.ok) { window.alert(data.error || 'Transition refusée.'); return false; }
    return true;
  };
  let dragged = null;
  document.querySelectorAll('[draggable="true"][data-task-id]').forEach((card) => {
    card.addEventListener('dragstart', () => { dragged = card; card.classList.add('opacity-50'); });
    card.addEventListener('dragend', () => { card.classList.remove('opacity-50'); dragged = null; });
    const select = document.createElement('select');
    select.className = 'mt-3 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-xs dark:bg-slate-950';
    select.setAttribute('aria-label', `Changer l’étape de ${card.dataset.taskTitle}`);
    select.innerHTML = '<option value="">Déplacer au clavier…</option><option value="PLANNED">Planifiée</option><option value="IN_PROGRESS">En cours</option><option value="BLOCKED">Bloquée</option><option value="ON_HOLD">En attente</option><option value="COMPLETED">Terminée</option>';
    select.addEventListener('change', async () => {
      const target = document.querySelector(`[data-kanban-column="${select.value}"] [data-dropzone]`);
      if (await postTransition(card, select.value)) target?.appendChild(card);
      select.value = '';
    });
    card.appendChild(select);
  });
  document.querySelectorAll('[data-kanban-column]').forEach((column) => {
    column.addEventListener('dragover', (event) => { if (dragged) event.preventDefault(); });
    column.addEventListener('drop', async (event) => {
      event.preventDefault(); if (!dragged) return;
      const status = column.dataset.kanbanColumn;
      if (await postTransition(dragged, status)) column.querySelector('[data-dropzone]')?.appendChild(dragged);
    });
  });

  const drawer = document.getElementById('activity-drawer');
  const overlay = document.getElementById('activity-drawer-overlay');
  const drawerTitle = document.getElementById('activity-drawer-title');
  const drawerContent = document.getElementById('activity-drawer-content');
  const closeDrawer = () => {
    drawer?.classList.remove('is-open'); overlay?.classList.remove('is-open');
    drawer?.setAttribute('aria-hidden','true'); if (overlay) setTimeout(() => { overlay.hidden = true; }, 210);
  };
  document.querySelectorAll('[data-close-drawer]').forEach((item) => item.addEventListener('click', closeDrawer));
  overlay?.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeDrawer(); });
  document.querySelectorAll('[data-metric]').forEach((card) => card.addEventListener('click', async () => {
    if (!drawer || !overlay || !drawerContent) return;
    overlay.hidden = false; requestAnimationFrame(() => overlay.classList.add('is-open'));
    drawer.classList.add('is-open'); drawer.setAttribute('aria-hidden','false');
    drawerTitle.textContent = `${card.dataset.label} · ${card.dataset.value}`;
    drawerContent.innerHTML = '<p class="rounded-lg bg-slate-50 p-4">Chargement des événements sources…</p>';
    const params = new URLSearchParams({metric:card.dataset.metric, debut:new URLSearchParams(location.search).get('debut') || '', fin:new URLSearchParams(location.search).get('fin') || ''});
    [['ctm','ctmId'],['wg','wgId'],['target_group','targetGroupId'],['norme','normeId']].forEach(([key,data]) => { if (root.dataset[data]) params.set(key, root.dataset[data]); });
    try {
      const response = await fetch(`${root.dataset.sourceUrl}?${params}`, {credentials:'same-origin'});
      const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Accès refusé');
      drawerContent.innerHTML = data.items.length ? data.items.map((item) => `<article class="rounded-xl border border-slate-200 p-4 dark:border-slate-700"><div class="flex items-start justify-between gap-3"><strong>${escapeHtml(item.title)}</strong><span class="status-badge status-gray">${escapeHtml(item.status || '')}</span></div><p class="mt-2 text-xs text-slate-500">${escapeHtml(item.detail || '')}</p>${item.value ? `<p class="mt-2 text-sm font-bold">${escapeHtml(item.value)}</p>` : ''}</article>`).join('') : '<p class="rounded-lg bg-slate-50 p-5 text-center text-slate-500">Aucune source disponible pour ce filtre.</p>';
    } catch (error) { drawerContent.innerHTML = `<p class="rounded-lg bg-red-50 p-4 text-red-800">${escapeHtml(error.message)}</p>`; }
    drawer.querySelector('[data-close-drawer]')?.focus();
  }));
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

  const chartDataNode = document.getElementById('activity-chart-data');
  if (!chartDataNode || root.dataset.lightMode === 'true') return;
  const loadCharts = () => new Promise((resolve, reject) => {
    if (window.echarts) return resolve(window.echarts);
    const script = document.createElement('script'); script.src = '/static/vendor/echarts.min.js'; script.defer = true;
    script.onload = () => resolve(window.echarts); script.onerror = () => reject(new Error('Bibliothèque graphique indisponible'));
    document.head.appendChild(script);
  });
  const renderCharts = async () => {
    try {
      const echarts = await loadCharts(); const data = JSON.parse(chartDataNode.textContent);
      const heat = document.getElementById('activity-heatmap');
      if (heat) {
        const points = []; data.heatmap.rows.forEach((row,y) => row.values.forEach((value,x) => points.push([x,y,value == null ? -1 : value])));
        const chart = echarts.init(heat); chart.setOption({animation:true,tooltip:{formatter:(p)=>`${data.heatmap.rows[p.value[1]].label}<br>${data.heatmap.weeks[p.value[0]]} : ${p.value[2] < 0 ? 'Données insuffisantes' : `${p.value[2]} %`}`},grid:{left:72,right:20,top:20,bottom:42},xAxis:{type:'category',data:data.heatmap.weeks},yAxis:{type:'category',data:data.heatmap.rows.map(r=>r.label)},visualMap:{min:0,max:100,calculable:false,orient:'horizontal',left:'center',bottom:0,inRange:{color:['#fed7aa','#7dd3fc','#0369a1']},outOfRange:{color:'#e2e8f0'}},series:[{type:'heatmap',data:points,label:{show:true,formatter:(p)=>p.value[2] < 0 ? '—' : `${Math.round(p.value[2])}%`},emphasis:{itemStyle:{shadowBlur:8,shadowColor:'rgba(0,0,0,.2)'}}}]});
        window.addEventListener('resize',()=>chart.resize(),{passive:true});
      }
      const load = document.getElementById('activity-load-chart');
      if (load) {
        const chart = echarts.init(load); chart.setOption({animation:true,tooltip:{trigger:'axis'},grid:{left:70,right:30,top:18,bottom:35},xAxis:{type:'value',name:'Tâches'},yAxis:{type:'category',data:data.load.map(r=>r.label)},series:[{type:'bar',data:data.load.map(r=>r.tasks),itemStyle:{color:'#0284c7',borderRadius:[0,5,5,0]},label:{show:true,position:'right'}}]});
        window.addEventListener('resize',()=>chart.resize(),{passive:true});
      }
    } catch (error) {
      document.querySelectorAll('.chart-box').forEach((box) => { box.innerHTML = `<p class="rounded-lg bg-slate-50 p-5 text-center text-sm text-slate-500">${escapeHtml(error.message)}. Le tableau accessible reste disponible.</p>`; });
    }
  };
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => { if (entries.some(e=>e.isIntersecting)) { observer.disconnect(); renderCharts(); } }, {rootMargin:'200px'});
    observer.observe(chartDataNode.parentElement);
  } else renderCharts();
})();
