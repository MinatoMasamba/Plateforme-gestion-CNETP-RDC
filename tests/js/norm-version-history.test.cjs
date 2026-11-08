const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync('templates/static/js/norm-version-history.js', 'utf8'), sandbox);
const History = sandbox.window.NormVersionHistory;
const deferred = () => {let resolve; const promise = new Promise(done => {resolve = done;}); return {promise, resolve};};

test('allège le rendu des longs textes sans modifier le texte ou les changements', () => {
  const source = [{type: 'equal', text: 'Un '}, {type: 'equal', text: 'texte\n'},
    {type: 'delete', text: 'ancien'}, {type: 'insert', text: 'corrigé'}];
  const compact = History.compactSegments(source);
  assert.equal(compact.length, 3);
  assert.equal(compact[0].text, 'Un texte\n');
  assert.equal(compact.map(item => item.text).join(''), source.map(item => item.text).join(''));
  assert.equal(compact[1].type, 'delete');
  assert.equal(compact[2].type, 'insert');
});

test('charge toutes les pages au-delà des dix premières versions', async () => {
  const pages = [];
  const versions = Array.from({length: 123}, (_, i) => ({id: 123 - i, version_number: 123 - i}));
  const loaded = await History.loadAll(7, async url => {
    const page = Number(new URL(url, 'http://localhost').searchParams.get('page'));
    pages.push(page);
    return versions.slice((page - 1) * 100, page * 100);
  });
  assert.equal(loaded.length, 123);
  assert.equal(loaded[122].version_number, 1);
  assert.deepEqual(pages, [1, 2]);
});

test('ne présente pas un chargement partiel comme un historique complet', async () => {
  await assert.rejects(History.loadAll(7, async url => {
    if (url.includes('page=2')) throw new Error('Lecture refusée');
    return Array.from({length: 100}, (_, id) => ({id}));
  }), /Lecture refusée/);
});

function viewer(loadVersions) {
  const result = Object.create(History.prototype);
  Object.assign(result, {request: 0, comparison: 0, rows: [], options: {loadVersions}, render() {}, async compare() {}});
  return result;
}

test('une réponse lente du document précédent ne remplace pas les versions sélectionnées', async () => {
  const first = deferred(), second = deferred();
  const history = viewer(key => key === 'a' ? first.promise : second.promise);
  const oldRequest = history.open('a'), newRequest = history.open('b');
  second.resolve([{id: 20, version_number: 2}, {id: 19, version_number: 1}]);
  await newRequest;
  first.resolve([{id: 7, version_number: 5}]);
  await oldRequest;
  assert.equal(history.key, 'b');
  assert.equal(history.right, 20);
  assert.equal(history.left, 19);
});

test('réinitialise source et cible quand le document change', async () => {
  const history = viewer(async key => key === 'a' ? [{id: 10, version_number: 15}, {id: 9, version_number: 14}] : [{id: 30, version_number: 1}]);
  await history.open('a');
  await history.open('b');
  assert.equal(history.rows.length, 1);
  assert.equal(history.left, 30);
  assert.equal(history.right, 30);
});

test('compare la version à traiter à sa précédente même si une rédaction plus récente existe', async () => {
  const history = viewer(async () => [
    {id: 90, version_number: 4}, {id: 80, version_number: 3}, {id: 70, version_number: 2}
  ]);
  await history.open('controle', 'Dossier en attente', {versionNumber: 3});
  assert.equal(history.right, 80);
  assert.equal(history.left, 70);
});

test('affiche le texte de la version unique sans demander une comparaison impossible', async () => {
  sandbox.document = {createElement: () => ({})};
  const note = {textContent: ''}, contents = [];
  const box = {replaceChildren: node => contents.push(node)};
  const history = Object.create(History.prototype);
  Object.assign(history, {key: 'unique', comparison: 0, left: 8, right: 8,
    rows: [{id: 8, version_number: 1, content: 'Texte initial conservé.'}],
    root: {querySelector: selector => selector === '[data-nvh-note]' ? note : box},
    options: {compare() {assert.fail('Une seule version ne se compare pas.');}}});
  await history.compare();
  assert.match(note.textContent, /Une seule version enregistrée/);
  assert.equal(contents[0].textContent, 'Texte initial conservé.');
});

test('une ancienne comparaison ne remplace pas la nouvelle sélection', async () => {
  const old = deferred(), recent = deferred(), note = {textContent: ''};
  const box = {replaceChildren() {}, setAttribute() {}, removeAttribute() {}};
  const history = Object.create(History.prototype);
  Object.assign(history, {key: 'a', comparison: 0, left: 1, right: 2,
    rows: [1, 2, 3].map(id => ({id, version_number: id})),
    root: {querySelector: selector => selector === '[data-nvh-note]' ? note : box},
    options: {compare: (_left, right) => right.id === 2 ? old.promise : recent.promise},
    message() {}});
  const older = history.compare();
  history.right = 3;
  const newer = history.compare();
  recent.resolve({segments: [], note: 'Comparaison récente'});
  await newer;
  old.resolve({segments: [], note: 'Ancienne comparaison'});
  await older;
  assert.match(note.textContent, /Comparaison récente/);
  assert.doesNotMatch(note.textContent, /Ancienne comparaison/);
});
