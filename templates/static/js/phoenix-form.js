(() => {
    const DEFAULT_PLACEHOLDER = 'Sélectionner…';

    function readablePlaceholder(select) {
        const empty = [...select.options].find(option => option.value === '');
        const text = empty ? empty.textContent.trim() : '';
        if (!text || /^-+$/.test(text)) return DEFAULT_PLACEHOLDER;
        return text;
    }

    function enhanceSelect(select) {
        if (select.dataset.combobox === 'on' || select.multiple || select.disabled) return;
        if (select.dataset.combobox === 'off') return;
        const options = [...select.options].filter(option => option.value !== '');
        if (options.length < 6) return;
        select.dataset.combobox = 'on';
        const placeholder = readablePlaceholder(select);

        const wrapper = document.createElement('div');
        wrapper.className = 'pf-combo';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        select.classList.add('pf-combo-native');
        select.tabIndex = -1;

        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'pf-combo-control';
        control.setAttribute('aria-haspopup', 'listbox');
        control.setAttribute('aria-expanded', 'false');
        const label = document.querySelector(`label[for="${select.id}"]`);
        if (label) control.setAttribute('aria-label', label.textContent.replace('obligatoire', '').trim());

        const value = document.createElement('span');
        value.className = 'pf-combo-value';
        const chevron = document.createElement('span');
        chevron.className = 'pf-combo-chevron';
        chevron.setAttribute('aria-hidden', 'true');
        chevron.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>';
        control.append(value, chevron);

        const pop = document.createElement('div');
        pop.className = 'pf-combo-pop';
        pop.hidden = true;
        const search = document.createElement('input');
        search.type = 'text';
        search.className = 'pf-combo-search';
        search.placeholder = 'Rechercher…';
        search.setAttribute('autocomplete', 'off');
        const list = document.createElement('ul');
        list.className = 'pf-combo-list';
        list.setAttribute('role', 'listbox');
        pop.append(search, list);
        wrapper.append(control, pop);

        function refreshValue() {
            const selected = select.selectedOptions[0];
            const hasValue = selected && selected.value !== '';
            value.textContent = hasValue ? selected.textContent.trim() : placeholder;
            value.classList.toggle('is-placeholder', !hasValue);
        }

        function buildList(filter) {
            const needle = (filter || '').toLowerCase();
            list.innerHTML = '';
            [...select.options].forEach(option => {
                if (needle && !option.textContent.toLowerCase().includes(needle)) return;
                const li = document.createElement('li');
                li.className = 'pf-combo-option';
                li.setAttribute('role', 'option');
                const isValue = option.value !== '';
                if (!isValue) li.classList.add('is-clear');
                if (option.selected) li.setAttribute('aria-selected', 'true');
                li.textContent = option.textContent.trim();
                li.addEventListener('mousedown', event => {
                    event.preventDefault();
                    choose(option.value);
                });
                list.appendChild(li);
            });
            if (!list.children.length) {
                const empty = document.createElement('li');
                empty.className = 'pf-combo-empty';
                empty.textContent = 'Aucun résultat';
                list.appendChild(empty);
            }
        }

        function choose(next) {
            select.value = next;
            select.dispatchEvent(new Event('change', { bubbles: true }));
            refreshValue();
            close();
            control.focus();
        }

        function open() {
            pop.hidden = false;
            control.setAttribute('aria-expanded', 'true');
            search.value = '';
            buildList('');
            search.focus();
        }

        function close() {
            pop.hidden = true;
            control.setAttribute('aria-expanded', 'false');
        }

        control.addEventListener('click', () => (pop.hidden ? open() : close()));
        control.addEventListener('keydown', event => {
            if (event.key === 'ArrowDown') { event.preventDefault(); open(); }
            if (event.key === 'Escape') close();
        });
        search.addEventListener('input', () => buildList(search.value));
        search.addEventListener('keydown', event => {
            if (event.key === 'Escape') { event.preventDefault(); close(); control.focus(); }
            if (event.key === 'Enter') {
                event.preventDefault();
                const first = list.querySelector('.pf-combo-option');
                if (first) first.dispatchEvent(new MouseEvent('mousedown'));
            }
        });
        document.addEventListener('click', event => {
            if (!wrapper.contains(event.target)) close();
        });
        select.addEventListener('change', refreshValue);
        refreshValue();
    }

    function trackUnsaved(form) {
        const bar = form.querySelector('[data-unsaved]');
        if (!bar) return;
        const serialize = () => [...new FormData(form).entries()]
            .filter(([key]) => key !== 'csrfmiddlewaretoken')
            .map(([key, val]) => `${key}=${val}`).sort().join('&');
        const initial = serialize();
        let dirty = false;
        const update = () => {
            const changed = dirty || serialize() !== initial;
            bar.hidden = !changed;
        };
        form.addEventListener('input', () => { dirty = true; update(); });
        form.addEventListener('change', () => { dirty = true; update(); });
        form.addEventListener('submit', () => { dirty = false; bar.hidden = true; });
        window.addEventListener('beforeunload', event => {
            if (dirty) { event.preventDefault(); event.returnValue = ''; }
        });
    }

    document.querySelectorAll('form.pf-form select.phoenix-input').forEach(enhanceSelect);
    document.querySelectorAll('form.pf-form').forEach(trackUnsaved);
})();
