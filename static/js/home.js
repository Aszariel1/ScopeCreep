(function () {
    var stored = JSON.parse(localStorage.getItem('scopecreep_projects') || '[]');
    if (!stored.length) return;

    var container = document.getElementById('active-projects');
    container.className += ' glass-card rounded-2xl';

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'w-full flex items-center justify-between px-4 py-3 font-semibold text-gray-100';
    toggle.innerHTML = '<span>Active projects</span><span class="chevron transition-transform text-gray-400">&#9662;</span>';
    container.appendChild(toggle);

    var list = document.createElement('div');
    list.className = 'space-y-2 hidden px-4 pb-4';

    stored.forEach(function (p) {
        var link = document.createElement('a');
        link.href = '/artist/' + p.token + '/';
        link.className = 'neu-btn block rounded-xl px-3 py-2 text-gray-200';
        link.textContent = p.name;
        list.appendChild(link);
    });

    toggle.addEventListener('click', function () {
        list.classList.toggle('hidden');
        toggle.querySelector('.chevron').classList.toggle('rotate-180');
    });

    container.appendChild(list);
})();
