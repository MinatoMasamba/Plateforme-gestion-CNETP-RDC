(() => {
  const root = document.querySelector('[data-activity-root]') || document.body;
  if (!window.fetch) return;
  const deviceKey = 'cne-itp-activity-device';
  const tabKey = 'cne-itp-activity-tab';
  const randomId = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);
  let deviceId = localStorage.getItem(deviceKey);
  if (!deviceId) { deviceId = randomId(); localStorage.setItem(deviceKey, deviceId); }
  let tabId = sessionStorage.getItem(tabKey);
  if (!tabId) { tabId = randomId(); sessionStorage.setItem(tabKey, tabId); }
  let interacted = false;
  ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach((name) => window.addEventListener(name, () => { interacted = true; }, {passive:true}));
  const cookieToken = () => {
    const match = document.cookie.split(';').map((item) => item.trim())
      .find((item) => item.startsWith('csrftoken='));
    return match ? decodeURIComponent(match.slice('csrftoken='.length)) : '';
  };
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content
    || window.DJANGO_CSRF_TOKEN
    || cookieToken();
  const payload = () => ({
    device_id: deviceId,
    tab_id: tabId,
    visible: document.visibilityState === 'visible',
    interacted,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
    path: location.pathname,
    ctm_id: root.dataset.ctmId || null,
    working_group_id: root.dataset.wgId || null,
    target_group_id: root.dataset.targetGroupId || null,
    norme_id: root.dataset.normeId || null,
  });
  const send = () => {
    if (document.visibilityState !== 'visible') return;
    const body = JSON.stringify(payload());
    interacted = false;
    fetch('/api/activite/presence/', {
      method:'POST', credentials:'same-origin', keepalive:true,
      headers:{'Content-Type':'application/json','X-CSRFToken':csrf}, body,
    }).catch(() => { interacted = true; });
  };
  setTimeout(send, 1200);
  setInterval(send, 60000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') send(); });
})();
