(() => {
  const root = document.querySelector('[data-activity-root]');
  if (!root) return;
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || window.DJANGO_CSRF_TOKEN || '';

  const activityTabs = [...document.querySelectorAll('[data-activity-tab]')];
  const activityPanels = [...document.querySelectorAll('[data-activity-panel]')];
  const showActivityTab = (name, updateUrl = true) => {
    const selected = activityTabs.find((tab) => tab.dataset.activityTab === name);
    if (!selected) return;
    activityTabs.forEach((tab) => {
      const active = tab === selected;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', String(active));
    });
    activityPanels.forEach((panel) => { panel.hidden = panel.dataset.activityPanel !== name; });
    const breadcrumb = document.getElementById('activity-current-view-name');
    if (breadcrumb) breadcrumb.textContent = selected.dataset.tabLabel;
    const filterView = document.getElementById('activity-filter-view');
    if (filterView) filterView.value = name;
    if (updateUrl) {
      const url = new URL(window.location.href);
      if (name === 'ensemble') url.searchParams.delete('vue');
      else url.searchParams.set('vue', name);
      window.history.replaceState(null, '', url);
    }
    document.querySelector('.activity-shell main')?.scrollTo({top: 0, behavior: 'smooth'});
    if (window.innerWidth < 1024 && typeof window.toggleActivitySidebar === 'function') window.toggleActivitySidebar(false);
  };
  activityTabs.forEach((tab) => tab.addEventListener('click', () => showActivityTab(tab.dataset.activityTab)));
  document.querySelectorAll('[data-activity-open-tab]').forEach((button) => button.addEventListener('click', () => showActivityTab(button.dataset.activityOpenTab)));

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

})();
