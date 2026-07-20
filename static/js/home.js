(function () {
    var stored = JSON.parse(localStorage.getItem('scopecreep_projects') || '[]');
    if (!stored.length) return;

    var container = document.getElementById('active-projects');
    container.className += ' card rounded-xl';

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'w-full flex items-center justify-between px-4 py-3 font-medium text-gray-100';
    toggle.innerHTML = '<span>Active projects</span><span class="chevron transition-transform text-gray-400">'
        + '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="m6 9 6 6 6-6"/></svg>'
        + '</span>';
    container.appendChild(toggle);

    var list = document.createElement('div');
    list.className = 'space-y-2 hidden px-4 pb-4';

    stored.forEach(function (p) {
        var row = document.createElement('div');
        row.className = 'flex items-center gap-2';

        var link = document.createElement('a');
        link.href = '/artist/' + p.token + '/';
        link.className = 'btn flex-1 min-w-0 truncate rounded-lg px-3 py-2 text-gray-200';
        link.textContent = p.name;
        row.appendChild(link);

        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn w-9 h-9 rounded-lg flex items-center justify-center text-red-400 shrink-0';
        removeBtn.title = 'Remove from this list';
        removeBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4 shrink-0">'
            + '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>';
        removeBtn.addEventListener('click', function () {
            if (!confirm('Remove "' + p.name + '" from this list? The project itself stays intact, you just lose the shortcut.')) return;
            var updated = JSON.parse(localStorage.getItem('scopecreep_projects') || '[]').filter(function (item) { return item.token !== p.token; });
            localStorage.setItem('scopecreep_projects', JSON.stringify(updated));
            row.remove();
        });
        row.appendChild(removeBtn);

        list.appendChild(row);
    });

    toggle.addEventListener('click', function () {
        list.classList.toggle('hidden');
        toggle.querySelector('.chevron').classList.toggle('rotate-180');
    });

    container.appendChild(list);
})();
