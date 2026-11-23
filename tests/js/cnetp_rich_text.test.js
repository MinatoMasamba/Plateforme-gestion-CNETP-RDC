// Parité du convertisseur web avec Python et Dart :
// `node --test tests/js/cnetp_rich_text.test.js`.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const rich = require('../../templates/static/js/components/cnetp-rich-text.js');

const cases = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'rich_text_cases.json'), 'utf8'),
);

for (const item of cases) {
    test(`fixture ${item.name}`, () => {
        if (item.error) {
            assert.throws(() => rich.validate(item.source, item.content_format), rich.RichTextError);
            return;
        }
        assert.equal(rich.toPlain(item.source, item.content_format), item.plain);
        const delta = rich.toDelta(item.source, item.content_format);
        const markdown = rich.fromDelta(delta);
        assert.deepEqual(rich.toDelta(markdown), delta);
        assert.equal(rich.toPlain(markdown), item.plain);
    });
}

test('styles hors palette et liens dangereux ignorés, rgb() normalisé', () => {
    const markdown = rich.fromDelta([
        { insert: 'Rose', attributes: { color: '#ff00ff', bold: true } },
        { insert: ' lien', attributes: { link: 'javascript:alert(1)' } },
        { insert: ' bleu', attributes: { color: 'rgb(0, 149, 201)' } },
        { insert: '\n' },
    ]);
    assert.equal(markdown, '**Rose** lien[ bleu]{couleur=bleu}');
});
