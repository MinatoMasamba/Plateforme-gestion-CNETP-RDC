/*
 * Markdown CNE-ITP ↔ Delta Quill, et pont entre l'éditeur Quill et le
 * <textarea> source de /app/. Miroir de apps/norms/rich_text.py et de
 * flutter_app/lib/core/rich_text/cnetp_markdown.dart : toute évolution du
 * dialecte doit être répercutée dans les trois implémentations.
 */
(function (root) {
    'use strict';

    var FORMAT_PLAIN = 'plain';
    var FORMAT_MD = 'md';
    var COLORS = { bleu: '#0095c9', rouge: '#db3832', nuit: '#0a2540' };
    var SIZES = { petit: 'small', grand: 'large', 'tres-grand': 'huge' };
    var HIGHLIGHT = '#fff24b';

    var RAW_HTML = /(?<!\\)<\s*\/?\s*[a-zA-Z!]/;
    var STYLED = /\[((?:\\.|[^\[\]\\\n])+)\]\{([^{}\n]+)\}/y;
    var HEADING = /^(#{1,3})\s+(.+)$/;
    var LIST = /^(?:(-)|(\d+)\.)\s+(.+)$/;
    var QUOTE = /^>\s?(.*)$/;
    var BLOCK_LIKE = /^(?:#|>|-\s|\d+\.\s)/;

    function RichTextError(message) {
        this.name = 'RichTextError';
        this.message = message;
    }
    RichTextError.prototype = Object.create(Error.prototype);

    function fail(message) { throw new RichTextError(message); }

    function splitLines(value) {
        if (!value) return [];
        var lines = value.split(/\r\n|\r|\n/);
        if (lines.length && lines[lines.length - 1] === '') lines.pop();
        return lines;
    }

    function safeUrl(value) {
        var url = String(value || '').trim();
        for (var i = 0; i < url.length; i++) {
            var code = url.charCodeAt(i);
            if (code < 33 || code === 127) fail('Lien contenant des espaces ou caractères interdits');
        }
        var match = /^([a-zA-Z][a-zA-Z0-9+.-]*):(.*)$/.exec(url);
        if (!match) fail('Lien interdit : seuls http, https et mailto sont acceptés');
        var scheme = match[1].toLowerCase();
        if (['http', 'https', 'mailto'].indexOf(scheme) < 0) {
            fail('Lien interdit : seuls http, https et mailto sont acceptés');
        }
        if (scheme !== 'mailto' && !/^\/\/[^\/?#]+/.test(match[2])) fail('Lien absolu incomplet');
        if (scheme === 'mailto' && !match[2]) fail('Adresse mailto vide');
        return url;
    }

    function isSafeUrl(url) {
        try { safeUrl(url); return true; } catch (e) { return false; }
    }

    function styleAttrs(attributes) {
        var result = {};
        attributes.split('|').forEach(function (item) {
            var separator = item.indexOf('=');
            if (separator < 0) fail('Attribut de style invalide');
            var key = item.slice(0, separator).trim();
            var value = item.slice(separator + 1).trim();
            if (key === 'taille') {
                if (!SIZES[value]) fail('Taille de texte inconnue : ' + value);
                result.size = SIZES[value];
            } else if (key === 'couleur') {
                if (!COLORS[value]) fail('Couleur de texte inconnue : ' + value);
                result.color = COLORS[value];
            } else if (key === 'surlignage') {
                if (value !== 'jaune') fail('Surlignage inconnu : ' + value);
                result.background = HIGHLIGHT;
            } else {
                fail('Attribut non autorisé : ' + key);
            }
        });
        return result;
    }

    function findClosing(text, marker, position) {
        var escaped = false;
        for (var index = position; index < text.length; index++) {
            var char = text[index];
            if (escaped) escaped = false;
            else if (char === '\\') escaped = true;
            else if (text.startsWith(marker, index)) return index;
        }
        return -1;
    }

    function findLinkEnd(text, position) {
        var depth = 0;
        for (var index = position; index < text.length; index++) {
            var char = text[index];
            if (char === '\n') break;
            if (char === '(') depth++;
            else if (char === ')') {
                if (depth === 0) return index;
                depth--;
            }
        }
        return -1;
    }

    function apply(runs, attrs) {
        return runs.map(function (run) {
            return { text: run.text, attrs: Object.assign({}, attrs, run.attrs) };
        });
    }

    var MARKERS = [['**', 'bold'], ['++', 'underline'], ['*', 'italic']];

    function inline(text, start, closing, depth) {
        start = start || 0;
        depth = depth || 0;
        if (depth > 30) fail('Mise en forme trop profondément imbriquée');
        var runs = [];
        var index = start;
        while (index < text.length) {
            if (closing && text.startsWith(closing, index)) return { runs: runs, end: index + closing.length };
            var char = text[index];
            if (char === '\\') {
                if (index + 1 >= text.length) fail("Caractère d'échappement sans valeur");
                runs.push({ text: text[index + 1], attrs: {} });
                index += 2;
                continue;
            }
            if (char === '[') {
                STYLED.lastIndex = index;
                var styled = STYLED.exec(text);
                if (styled) {
                    var inner = inline(styled[1]);
                    if (inner.end < styled[1].length) fail('Libellé de style invalide');
                    runs = runs.concat(apply(inner.runs, styleAttrs(styled[2])));
                    index = STYLED.lastIndex;
                    continue;
                }
                var labelEnd = text.indexOf('](', index + 1);
                if (labelEnd > -1) {
                    var label = text.slice(index + 1, labelEnd);
                    var urlStart = labelEnd + 2;
                    var urlEnd = findLinkEnd(text, urlStart);
                    if (urlEnd === -1) fail('Lien non fermé');
                    var linkInner = inline(label);
                    if (linkInner.end < label.length) fail('Libellé de lien invalide');
                    var url = safeUrl(text.slice(urlStart, urlEnd));
                    runs = runs.concat(apply(linkInner.runs, { link: url }));
                    index = urlEnd + 1;
                    continue;
                }
            }
            var matched = false;
            for (var m = 0; m < MARKERS.length; m++) {
                var marker = MARKERS[m][0];
                if (text.startsWith(marker, index)) {
                    if (findClosing(text, marker, index + marker.length) < 0) {
                        fail('Marqueur « ' + marker + ' » non fermé');
                    }
                    var wrapped = inline(text, index + marker.length, marker, depth + 1);
                    var attr = {};
                    attr[MARKERS[m][1]] = true;
                    runs = runs.concat(apply(wrapped.runs, attr));
                    index = wrapped.end;
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                runs.push({ text: char, attrs: {} });
                index++;
            }
        }
        if (closing) fail('Marqueur « ' + closing + ' » non fermé');
        return { runs: runs, end: index };
    }

    function inlineLine(line, number) {
        try {
            var result = inline(line);
            if (result.end !== line.length) fail('Contenu riche incomplet');
            return result.runs;
        } catch (error) {
            fail(error.message + ' (ligne ' + number + ')');
        }
    }

    function plainOf(runs) {
        return runs.map(function (run) { return run.text; }).join('');
    }

    function parseLines(source, format) {
        var lines = splitLines(source || '');
        if (format === FORMAT_PLAIN) {
            return lines.map(function (line) {
                return line ? { kind: 'paragraph', runs: [{ text: line, attrs: {} }] } : { kind: 'empty', runs: [] };
            });
        }
        if (format !== FORMAT_MD) fail('Format de contenu inconnu : ' + format);
        if (RAW_HTML.test(source || '')) fail('Le HTML brut n’est pas autorisé');
        return lines.map(function (raw, index) {
            var stripped = raw.trim();
            var number = index + 1;
            if (!stripped) return { kind: 'empty', runs: [] };
            var heading = HEADING.exec(stripped);
            if (heading) return { kind: 'heading', level: heading[1].length, runs: inlineLine(heading[2], number) };
            var item = LIST.exec(stripped);
            if (item) {
                var ordered = item[2] !== undefined;
                return {
                    kind: ordered ? 'ordered' : 'bullet',
                    marker: ordered ? item[2] + '.' : '-',
                    runs: inlineLine(item[3], number),
                };
            }
            var quote = QUOTE.exec(stripped);
            if (quote) return { kind: 'quote', runs: inlineLine(quote[1], number) };
            return { kind: 'paragraph', runs: inlineLine(stripped, number) };
        });
    }

    function validate(source, format) {
        parseLines(source, format || FORMAT_MD);
    }

    function toPlain(source, format) {
        format = format || FORMAT_MD;
        if (format === FORMAT_PLAIN) return source || '';
        var lines = parseLines(source, format);
        var blocks = [];
        var index = 0;
        while (index < lines.length) {
            var line = lines[index];
            if (line.kind === 'empty') { index++; continue; }
            if (line.kind === 'heading') { blocks.push(plainOf(line.runs)); index++; continue; }
            var group = [];
            var kind = line.kind;
            while (index < lines.length && lines[index].kind === kind) {
                var current = lines[index];
                group.push(kind === 'bullet' || kind === 'ordered'
                    ? current.marker + ' ' + plainOf(current.runs)
                    : plainOf(current.runs));
                index++;
            }
            blocks.push(group.join('\n'));
        }
        return blocks.join('\n\n');
    }

    function sameAttrs(a, b) {
        a = a || {};
        b = b || {};
        var keys = Object.keys(a);
        if (keys.length !== Object.keys(b).length) return false;
        return keys.every(function (key) { return a[key] === b[key]; });
    }

    function toDelta(source, format) {
        format = format || FORMAT_MD;
        var lines;
        try {
            lines = parseLines(source, format);
        } catch (error) {
            // Un contenu invalide est affiché tel quel plutôt que perdu.
            lines = parseLines(source, FORMAT_PLAIN);
        }
        var ops = [];
        lines.forEach(function (line) {
            line.runs.forEach(function (run) {
                if (!run.text) return;
                var op = { insert: run.text };
                if (Object.keys(run.attrs).length) op.attributes = Object.assign({}, run.attrs);
                ops.push(op);
            });
            var block = null;
            if (line.kind === 'heading') block = { header: line.level };
            else if (line.kind === 'bullet') block = { list: 'bullet' };
            else if (line.kind === 'ordered') block = { list: 'ordered' };
            else if (line.kind === 'quote') block = { blockquote: true };
            ops.push(block ? { insert: '\n', attributes: block } : { insert: '\n' });
        });
        if (!ops.length) ops.push({ insert: '\n' });
        var merged = [];
        ops.forEach(function (op) {
            var previous = merged[merged.length - 1];
            if (previous && op.insert !== '\n' && typeof previous.insert === 'string'
                && !previous.insert.endsWith('\n') && sameAttrs(previous.attributes, op.attributes)) {
                previous.insert += op.insert;
            } else {
                merged.push(Object.assign({}, op));
            }
        });
        return merged;
    }

    function escape(text) {
        return text.replace(/[\\*+\[\]<]/g, '\\$&');
    }

    function normalizeColor(value) {
        if (typeof value !== 'string') return null;
        var rgb = /^rgba?\((\d+),\s*(\d+),\s*(\d+)/i.exec(value.trim());
        if (rgb) {
            return '#' + rgb.slice(1, 4).map(function (part) {
                return ('0' + Number(part).toString(16)).slice(-2);
            }).join('');
        }
        return value.trim().toLowerCase();
    }

    function keyOf(map, value) {
        var normalized = normalizeColor(value);
        for (var key in map) {
            if (map[key] === normalized) return key;
        }
        return null;
    }

    function serializeRun(text, attrs) {
        var value = escape(text);
        if (attrs.underline === true) value = '++' + value + '++';
        if (attrs.italic === true) value = '*' + value + '*';
        if (attrs.bold === true) value = '**' + value + '**';
        var styles = [];
        var size = keyOf(SIZES, attrs.size);
        var color = keyOf(COLORS, attrs.color);
        if (size) styles.push('taille=' + size);
        if (color) styles.push('couleur=' + color);
        if (normalizeColor(attrs.background) === HIGHLIGHT) styles.push('surlignage=jaune');
        if (styles.length) value = '[' + value + ']{' + styles.join('|') + '}';
        if (typeof attrs.link === 'string' && isSafeUrl(attrs.link)) {
            var url = attrs.link.trim();
            var depth = 0;
            for (var i = 0; i < url.length; i++) {
                if (url[i] === '(') depth++;
                if (url[i] === ')' && --depth < 0) break;
            }
            if (depth !== 0) url = url.replace(/\(/g, '%28').replace(/\)/g, '%29');
            value = '[' + value + '](' + url + ')';
        }
        return value;
    }

    function fromDelta(ops) {
        var output = [];
        var runs = [];
        var ordered = 0;

        function closeLine(attrs) {
            var merged = [];
            runs.forEach(function (run) {
                if (!run.text) return;
                var last = merged[merged.length - 1];
                if (last && sameAttrs(last.attrs, run.attrs)) last.text += run.text;
                else merged.push({ text: run.text, attrs: run.attrs });
            });
            var plain = plainOf(merged);
            var line = merged.map(function (run) { return serializeRun(run.text, run.attrs); }).join('');
            var header = attrs.header;
            var list = attrs.list;
            ordered = list === 'ordered' ? ordered + 1 : 0;
            if (!plain.trim()) {
                output.push('');
            } else if (typeof header === 'number' && header > 0) {
                output.push('#'.repeat(Math.min(Math.max(header, 1), 3)) + ' ' + line);
            } else if (list === 'bullet' || list === 'checked' || list === 'unchecked') {
                output.push('- ' + line);
            } else if (list === 'ordered') {
                output.push(ordered + '. ' + line);
            } else if (attrs.blockquote === true) {
                output.push('> ' + line);
            } else {
                line = line.trim();
                var match = BLOCK_LIKE.exec(line);
                if (match) {
                    var dot = match[0].indexOf('.');
                    line = dot > 0 ? line.slice(0, dot) + '\\' + line.slice(dot) : '\\' + line;
                }
                output.push(line);
            }
            runs = [];
        }

        (ops || []).forEach(function (op) {
            if (!op || typeof op.insert !== 'string') return;
            var attrs = op.attributes || {};
            var parts = op.insert.split('\n');
            parts.forEach(function (part, index) {
                if (part) runs.push({ text: part, attrs: Object.assign({}, attrs) });
                if (index < parts.length - 1) closeLine(attrs);
            });
        });
        if (runs.length) closeLine({});
        while (output.length && output[output.length - 1] === '') output.pop();
        return output.join('\n');
    }

    /** Markdown normalisé d'un contenu stocké (texte brut converti une fois). */
    function normalize(source, format) {
        return fromDelta(toDelta(source || '', format || FORMAT_MD));
    }

    var api = {
        FORMAT_PLAIN: FORMAT_PLAIN,
        FORMAT_MD: FORMAT_MD,
        COLORS: COLORS,
        SIZES: SIZES,
        HIGHLIGHT: HIGHLIGHT,
        RichTextError: RichTextError,
        isSafeUrl: isSafeUrl,
        validate: validate,
        toPlain: toPlain,
        toDelta: toDelta,
        fromDelta: fromDelta,
        normalize: normalize,
    };

    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (typeof window === 'undefined') return;
    root.CnetpRichText = api;

    // ==========================================================
    // Pont éditeur Quill ↔ <textarea> source (PC uniquement)
    // ==========================================================
    var nativeValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');

    function el(tag, className, html) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (html !== undefined) node.innerHTML = html;
        return node;
    }

    var BUTTON = 'cnetp-rt-btn';
    var TOOLBAR_HTML = ''
        + '<select data-rt="block" title="Style de paragraphe" class="cnetp-rt-select">'
        + '<option value="p">Paragraphe</option><option value="1">Titre 1</option>'
        + '<option value="2">Titre 2</option><option value="3">Titre 3</option>'
        + '<option value="quote">Citation</option></select>'
        + '<select data-rt="size" title="Taille du texte" class="cnetp-rt-select">'
        + '<option value="">Normal</option><option value="small">Petit</option>'
        + '<option value="large">Grand</option><option value="huge">Très grand</option></select>'
        + '<span class="cnetp-rt-sep"></span>'
        + '<button type="button" data-rt="bold" title="Gras (Ctrl+B)" class="' + BUTTON + '"><b>G</b></button>'
        + '<button type="button" data-rt="italic" title="Italique (Ctrl+I)" class="' + BUTTON + '"><i>I</i></button>'
        + '<button type="button" data-rt="underline" title="Souligné (Ctrl+U)" class="' + BUTTON + '"><u>S</u></button>'
        + '<select data-rt="color" title="Couleur du texte" class="cnetp-rt-select">'
        + '<option value="">Couleur auto</option><option value="#0095c9">Bleu CNE-ITP</option>'
        + '<option value="#db3832">Rouge</option><option value="#0a2540">Bleu nuit</option></select>'
        + '<button type="button" data-rt="background" title="Surligner en jaune" class="' + BUTTON + '">'
        + '<span class="cnetp-rt-mark">ab</span></button>'
        + '<span class="cnetp-rt-sep"></span>'
        + '<button type="button" data-rt="bullet" title="Liste à puces" class="' + BUTTON + '">• ≡</button>'
        + '<button type="button" data-rt="ordered" title="Liste numérotée" class="' + BUTTON + '">1. ≡</button>'
        + '<button type="button" data-rt="blockquote" title="Citation" class="' + BUTTON + '">❝</button>'
        + '<button type="button" data-rt="link" title="Lien (Ctrl+K)" class="' + BUTTON + '">🔗</button>'
        + '<span class="cnetp-rt-sep"></span>'
        + '<button type="button" data-rt="clean" title="Effacer la mise en forme" class="' + BUTTON + '">⌫ Effacer</button>';

    var MINI_HTML = ''
        + '<button type="button" data-rt="bold" title="Gras" class="' + BUTTON + '"><b>G</b></button>'
        + '<button type="button" data-rt="italic" title="Italique" class="' + BUTTON + '"><i>I</i></button>'
        + '<button type="button" data-rt="underline" title="Souligné" class="' + BUTTON + '"><u>S</u></button>'
        + '<button type="button" data-rt="background" title="Surligner" class="' + BUTTON + '"><span class="cnetp-rt-mark">ab</span></button>'
        + '<button type="button" data-rt="link" title="Lien" class="' + BUTTON + '">🔗</button>'
        + '<button type="button" data-rt="share" title="Partager l’extrait" class="' + BUTTON + '">Partager</button>';

    /**
     * Monte Quill à la place de [textarea], qui reste la source Markdown
     * (lue/écrite par le reste de /app/ via `.value`).
     * options: { formatFor(value) → 'md'|'plain', onChange(md), onSelect(plain),
     *            onFocus(), onShare(plain) }
     */
    function mount(textarea, options) {
        if (!root.Quill || !textarea || textarea.__cnetpRich) return null;
        options = options || {};
        var wrapper = el('div', 'cnetp-rt');
        var toolbar = el('div', 'cnetp-rt-toolbar', TOOLBAR_HTML);
        var host = el('div', 'cnetp-rt-editor');
        var mini = el('div', 'cnetp-rt-mini hidden', MINI_HTML);
        var linkBox = el('form', 'cnetp-rt-link hidden',
            '<label>Adresse du lien<input type="url" name="url" placeholder="https://…" autocomplete="off"></label>'
            + '<p class="cnetp-rt-error hidden">Adresse invalide : utilisez http://, https:// ou mailto:.</p>'
            + '<div class="cnetp-rt-link-actions">'
            + '<button type="button" data-link="remove" class="' + BUTTON + '">Retirer</button>'
            + '<button type="button" data-link="cancel" class="' + BUTTON + '">Annuler</button>'
            + '<button type="submit" class="' + BUTTON + ' cnetp-rt-primary">Appliquer</button></div>');
        wrapper.appendChild(toolbar);
        wrapper.appendChild(host);
        wrapper.appendChild(mini);
        wrapper.appendChild(linkBox);
        textarea.parentNode.insertBefore(wrapper, textarea);
        textarea.style.display = 'none';
        textarea.__cnetpRich = true;

        var quill = new root.Quill(host, {
            placeholder: textarea.getAttribute('placeholder') || '',
            formats: ['header', 'bold', 'italic', 'underline', 'list', 'blockquote',
                'link', 'size', 'color', 'background'],
            modules: {
                keyboard: {
                    bindings: {
                        cnetpLink: { key: 'K', shortKey: true, handler: function () { openLink(); return false; } },
                    },
                },
            },
        });
        var loading = false;
        var savedRange = null;

        function source() { return fromDelta(quill.getContents().ops); }
        function plainText() { return quill.getText().replace(/\n$/, ''); }

        function load(value, format) {
            loading = true;
            try {
                quill.setContents(toDelta(value || '', format || FORMAT_MD), 'silent');
                quill.history.clear();
            } finally {
                loading = false;
            }
            nativeValue.set.call(textarea, source());
        }

        // Toute écriture de `.value` par le code existant recharge l'éditeur.
        Object.defineProperty(textarea, 'value', {
            configurable: true,
            get: function () { return nativeValue.get.call(textarea); },
            set: function (value) {
                var format = options.formatFor ? options.formatFor(value) : FORMAT_MD;
                load(value, format);
                refreshToolbar();
            },
        });

        quill.on('text-change', function () {
            if (loading) return;
            nativeValue.set.call(textarea, source());
            if (options.onChange) options.onChange(textarea.value);
        });

        function refreshToolbar() {
            var range = quill.getSelection();
            var format = range ? quill.getFormat(range) : {};
            toolbar.querySelectorAll('button[data-rt]').forEach(function (button) {
                var name = button.dataset.rt;
                var active = name === 'bullet' ? format.list === 'bullet'
                    : name === 'ordered' ? format.list === 'ordered'
                    : name === 'background' ? normalizeColor(format.background) === HIGHLIGHT
                    : name === 'link' ? !!format.link
                    : !!format[name];
                button.classList.toggle('is-active', active);
                button.setAttribute('aria-pressed', active ? 'true' : 'false');
            });
            toolbar.querySelector('[data-rt="block"]').value = format.header
                ? String(format.header) : (format.blockquote ? 'quote' : 'p');
            toolbar.querySelector('[data-rt="size"]').value = format.size || '';
            var color = normalizeColor(format.color);
            toolbar.querySelector('[data-rt="color"]').value = keyOf(COLORS, color) ? color : '';
        }

        function positionMini(range) {
            if (!range || !range.length || !quill.isEnabled()) {
                mini.classList.add('hidden');
                return;
            }
            var bounds = quill.getBounds(range.index, range.length);
            var top = host.offsetTop + bounds.top - 44;
            mini.style.top = Math.max(top, host.offsetTop) + 'px';
            mini.style.left = Math.max(8, host.offsetLeft + bounds.left) + 'px';
            mini.classList.remove('hidden');
        }

        quill.on('selection-change', function (range, oldRange) {
            if (range) {
                savedRange = range;
                if (!oldRange && options.onFocus) options.onFocus();
                if (range.length && options.onSelect) {
                    var text = quill.getText(range.index, range.length).trim();
                    if (text) options.onSelect(text);
                }
            }
            refreshToolbar();
            positionMini(range);
        });
        quill.on('editor-change', function (type) {
            if (type === 'text-change') refreshToolbar();
        });

        function currentRange() {
            return quill.getSelection(true) || savedRange || { index: quill.getLength(), length: 0 };
        }

        function toggle(name, value) {
            var range = currentRange();
            var format = quill.getFormat(range);
            quill.format(name, format[name] === value ? false : value, 'user');
        }

        function setBlock(value) {
            currentRange();
            quill.format('header', false, 'user');
            quill.format('blockquote', false, 'user');
            if (value === 'quote') {
                quill.format('list', false, 'user');
                quill.format('blockquote', true, 'user');
            } else if (value !== 'p') {
                quill.format('header', Number(value), 'user');
            }
        }

        function openLink() {
            var range = currentRange();
            savedRange = range;
            var current = quill.getFormat(range).link;
            linkBox.url.value = current || 'https://';
            linkBox.querySelector('[data-link="remove"]').classList.toggle('hidden', !current);
            linkBox.querySelector('.cnetp-rt-error').classList.add('hidden');
            linkBox.classList.remove('hidden');
            linkBox.url.focus();
            linkBox.url.select();
        }

        function closeLink() {
            linkBox.classList.add('hidden');
            quill.setSelection(savedRange, 'silent');
        }

        linkBox.addEventListener('submit', function (event) {
            event.preventDefault();
            var url = linkBox.url.value.trim();
            if (!isSafeUrl(url)) {
                linkBox.querySelector('.cnetp-rt-error').classList.remove('hidden');
                return;
            }
            closeLink();
            if (savedRange && savedRange.length) quill.formatText(savedRange, 'link', url, 'user');
            else if (savedRange) {
                quill.insertText(savedRange.index, url, { link: url }, 'user');
            }
        });
        linkBox.addEventListener('click', function (event) {
            var action = event.target.closest('[data-link]');
            if (!action) return;
            closeLink();
            if (action.dataset.link === 'remove' && savedRange) {
                var length = savedRange.length;
                if (!length) {
                    // Sélection vide : retirer le lien du mot sous le curseur.
                    var leaf = quill.getLeaf(savedRange.index);
                    if (leaf && leaf[0]) {
                        var blot = leaf[0];
                        quill.formatText(quill.getIndex(blot), blot.length(), 'link', false, 'user');
                    }
                    return;
                }
                quill.formatText(savedRange, 'link', false, 'user');
            }
        });
        linkBox.url.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') closeLink();
        });

        function handle(event) {
            var target = event.target.closest('[data-rt]');
            if (!target || target.tagName === 'SELECT') return;
            event.preventDefault();
            var name = target.dataset.rt;
            if (name === 'bullet' || name === 'ordered') {
                currentRange();
                if (quill.getFormat().list !== name) quill.format('blockquote', false, 'user');
                toggle('list', name);
            } else if (name === 'blockquote') {
                setBlock(quill.getFormat(currentRange()).blockquote ? 'p' : 'quote');
            } else if (name === 'background') {
                var format = quill.getFormat(currentRange());
                quill.format('background', normalizeColor(format.background) === HIGHLIGHT ? false : HIGHLIGHT, 'user');
            } else if (name === 'link') {
                openLink();
            } else if (name === 'clean') {
                var range = currentRange();
                ['bold', 'italic', 'underline', 'size', 'color', 'background', 'link'].forEach(function (key) {
                    quill.formatText(range, key, false, 'user');
                });
            } else if (name === 'share') {
                var selection = savedRange;
                if (selection && selection.length && options.onShare) {
                    options.onShare(quill.getText(selection.index, selection.length).trim());
                }
            } else {
                toggle(name, true);
            }
            refreshToolbar();
        }
        // mousedown évite de perdre la sélection avant l'action.
        toolbar.addEventListener('mousedown', function (event) {
            if (event.target.closest('button[data-rt]')) event.preventDefault();
        });
        mini.addEventListener('mousedown', function (event) { event.preventDefault(); });
        toolbar.addEventListener('click', handle);
        mini.addEventListener('click', handle);
        toolbar.addEventListener('change', function (event) {
            var name = event.target.dataset.rt;
            currentRange();
            if (name === 'block') setBlock(event.target.value);
            else if (name === 'size') quill.format('size', event.target.value || false, 'user');
            else if (name === 'color') quill.format('color', event.target.value || false, 'user');
            refreshToolbar();
        });

        // Les liens s'ouvrent dans un nouvel onglet, après confirmation.
        host.addEventListener('click', function (event) {
            var anchor = event.target.closest('a[href]');
            if (!anchor || !(event.ctrlKey || event.metaKey)) return;
            event.preventDefault();
            var href = anchor.getAttribute('href');
            if (isSafeUrl(href) && root.confirm('Ouvrir ce lien dans un nouvel onglet ?\n' + href)) {
                root.open(href, '_blank', 'noopener');
            }
        });

        load(nativeValue.get.call(textarea), options.formatFor ? options.formatFor(nativeValue.get.call(textarea)) : FORMAT_MD);
        refreshToolbar();

        var editor = {
            quill: quill,
            source: source,
            plainText: plainText,
            load: load,
            setReadOnly: function (readOnly) {
                quill.enable(!readOnly);
                wrapper.classList.toggle('is-readonly', !!readOnly);
            },
        };
        textarea.__cnetpEditor = editor;
        return editor;
    }

    api.mount = mount;
})(typeof window !== 'undefined' ? window : globalThis);
