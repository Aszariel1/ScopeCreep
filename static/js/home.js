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
        var link = document.createElement('a');
        link.href = '/artist/' + p.token + '/';
        link.className = 'btn block rounded-lg px-3 py-2 text-gray-200';
        link.textContent = p.name;
        list.appendChild(link);
    });

    toggle.addEventListener('click', function () {
        list.classList.toggle('hidden');
        toggle.querySelector('.chevron').classList.toggle('rotate-180');
    });

    container.appendChild(list);
})();
