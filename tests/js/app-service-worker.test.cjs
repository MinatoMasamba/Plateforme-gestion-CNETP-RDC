const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function worker(fetch, path = 'web/static/dist/app-sw.js') {
  const handlers = {}, deleted = [];
  const cached = new Response('Ancien écran');
  const context = {
    URL, Response, fetch,
    self: {location: {origin: 'http://localhost'}, addEventListener: (type, fn) => {handlers[type] = fn;}, clients: {claim() {} }},
    caches: {match: async () => cached,
      open: async () => ({put: async () => {}}),
      keys: async () => ['cnetp-shell-v1', 'cnetp-shell-v2', 'ctc-global-cache'],
      delete: async key => {deleted.push(key);}},
  };
  vm.runInNewContext(fs.readFileSync(path, 'utf8'), context);
  return {handlers, deleted};
}

test('une navigation reçoit le HTML courant même si un ancien écran est en cache', async () => {
  const {handlers} = worker(async () => new Response('Historique corrigé'));
  let result;
  const writes = [];
  handlers.fetch({request: {method: 'GET', url: 'http://localhost/app/', mode: 'navigate'},
    respondWith: value => {result = value;}, waitUntil: value => writes.push(value)});
  assert.equal(await (await result).text(), 'Historique corrigé');
  await Promise.all(writes);
});

test('le HTML en cache reste disponible hors ligne', async () => {
  const {handlers} = worker(async () => {throw new Error('Hors ligne');});
  let result;
  handlers.fetch({request: {method: 'GET', url: 'http://localhost/app/', mode: 'navigate'},
    respondWith: value => {result = value;}, waitUntil() {}});
  assert.equal(await (await result).text(), 'Ancien écran');
});

test('la mise à jour conserve les caches des autres applications', async () => {
  const {handlers, deleted} = worker(async () => new Response('OK'));
  let done;
  handlers.activate({waitUntil: value => {done = value;}});
  await done;
  assert.deepEqual(deleted, ['cnetp-shell-v1']);
});

for (const path of ['web/static/dist/app-sw.js', 'web/static/dist/sw.js']) {
  test('la navigation revalide le cache HTTP : ' + path, async () => {
    let mode;
    const {handlers} = worker(async (_request, options) => {mode = options?.cache; return new Response('Page courante');}, path);
    let result;
    handlers.fetch({request: {method: 'GET', url: 'http://localhost/ctc/', mode: 'navigate'},
      respondWith: value => {result = value;}, waitUntil() {}});
    assert.equal(await (await result).text(), 'Page courante');
    assert.equal(mode, 'no-cache');
  });
}
