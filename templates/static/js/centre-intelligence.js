(() => {
  const launch = document.getElementById('ai-launch');
  const panel = document.getElementById('ai-panel');
  const close = document.getElementById('ai-close');
  const form = document.getElementById('ai-form');
  const output = document.getElementById('ai-answer');
  const question = document.getElementById('ai-question');
  function toggle(open) { panel.hidden = !open; launch.setAttribute('aria-expanded', String(open)); if (open) question.focus(); else launch.focus(); }
  launch.addEventListener('click', () => toggle(panel.hidden));
  close.addEventListener('click', () => toggle(false));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && !panel.hidden) toggle(false); });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    output.textContent = 'Recherche en cours…';
    const button = form.querySelector('button[type=submit]'); button.disabled = true;
    try {
      const response = await fetch(form.action, {method:'POST', body:new FormData(form), credentials:'same-origin'});
      if (!response.ok) throw new Error('Réponse indisponible.');
      const data = await response.json();
      output.replaceChildren();
      const answer = document.createElement('p'); answer.textContent = data.answer; output.append(answer);
      if (data.chart && data.chart.type === 'bar') {
        const figure = document.createElement('figure'); figure.className = 'ai-chart';
        const title = document.createElement('figcaption'); title.textContent = data.chart.title; figure.append(title);
        const maximum = Math.max(1, ...data.chart.values);
        data.chart.labels.forEach((label, index) => {
          const line = document.createElement('div'); line.className = 'ai-chart-row';
          const name = document.createElement('span'); name.textContent = label;
          const track = document.createElement('div'); track.className = 'ai-chart-track';
          const bar = document.createElement('span'); bar.style.width = `${100 * data.chart.values[index] / maximum}%`; track.append(bar);
          const value = document.createElement('strong'); value.textContent = data.chart.values[index];
          line.append(name, track, value); figure.append(line);
        });
        output.append(figure);
      }
      if (data.table && data.table.length) {
        const keys = Object.keys(data.table[0]); const table = document.createElement('table');
        const head = table.createTHead().insertRow(); keys.forEach(key => { const cell = document.createElement('th'); cell.textContent = key.replaceAll('_',' '); head.append(cell); });
        const body = table.createTBody(); data.table.forEach(row => { const tr = body.insertRow(); keys.forEach(key => { const cell = tr.insertCell(); cell.textContent = row[key]; }); });
        output.append(table);
      }
      (data.sources || []).forEach(source => { const link = document.createElement('a'); link.href = source.url; link.textContent = source.label; output.append(link); });
    } catch (error) { output.textContent = error.message; }
    finally { button.disabled = false; }
  });
})();
