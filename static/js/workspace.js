(function () {
    var root = document.getElementById('workspace-root');
    var token = root.dataset.token;
    var name = root.dataset.name;
    var newFlag = root.dataset.new;
    var openCategoryId = root.dataset.open;

    if (newFlag) {
        var stored = JSON.parse(localStorage.getItem('scopecreep_projects') || '[]');
        if (!stored.some(function (p) { return p.token === token; })) {
            stored.push({ name: name, token: token });
            localStorage.setItem('scopecreep_projects', JSON.stringify(stored));
        }
        history.replaceState(null, '', window.location.pathname);
    }

    function openCategory(categoryId) {
        document.querySelectorAll('.category-log').forEach(function (log) {
            log.classList.add('hidden');
        });
        document.querySelectorAll('.category-card').forEach(function (c) {
            c.classList.remove('is-selected');
        });
        var log = document.getElementById('log-' + categoryId);
        var card = document.querySelector('.category-card[data-target="log-' + categoryId + '"]');
        if (log) log.classList.remove('hidden');
        if (card) card.classList.add('is-selected');
    }

    document.querySelectorAll('.category-card').forEach(function (card) {
        card.addEventListener('click', function () {
            openCategory(card.dataset.target.replace('log-', ''));
        });
    });

    if (openCategoryId) {
        openCategory(openCategoryId);
        history.replaceState(null, '', window.location.pathname);
    }
})();
