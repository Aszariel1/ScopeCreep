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

    var stackWrap = document.getElementById('category-stack');
    var stackCards = stackWrap ? Array.prototype.slice.call(stackWrap.querySelectorAll('.stack-card')) : [];
    var count = stackCards.length;
    var current = 0;
    var dragProgress = 0;

    if (openCategoryId) {
        var idx = stackCards.findIndex(function (c) { return c.dataset.categoryId === openCategoryId; });
        if (idx !== -1) current = idx;
        history.replaceState(null, '', window.location.pathname);
    }

    function shortestOffset(index) {
        var diff = index - current;
        if (count > 0) {
            if (diff > count / 2) diff -= count;
            if (diff < -count / 2) diff += count;
        }
        return diff - dragProgress;
    }

    function render(animated) {
        stackCards.forEach(function (card, i) {
            var offset = shortestOffset(i);
            var clamped = Math.max(-2.5, Math.min(2.5, offset));
            var width = stackWrap.offsetWidth;
            var translateX = clamped * width * 0.52;
            var scale = 1 - Math.min(Math.abs(clamped), 2) * 0.12;
            var rotate = clamped * -14;
            var opacity = Math.max(0, 1 - Math.abs(clamped) * 0.55);
            var z = Math.round(100 - Math.abs(clamped) * 10);
            var isActive = Math.abs(offset) < 0.5;

            card.style.transition = animated ? 'transform 0.35s ease, opacity 0.35s ease' : 'none';
            card.style.transform = 'translateX(' + translateX + 'px) scale(' + scale + ') rotateY(' + rotate + 'deg)';
            card.style.opacity = isActive ? '1' : String(opacity);
            card.style.zIndex = String(z);
            card.style.pointerEvents = isActive ? 'auto' : 'none';
            card.classList.toggle('is-active', isActive);
        });
    }

    function toggleCollapse(cardButton) {
        var log = cardButton.parentElement.querySelector('.category-log');
        var chevron = cardButton.querySelector('.category-chevron');
        if (!log) return;
        log.classList.toggle('is-collapsed');
        if (chevron) chevron.classList.toggle('is-collapsed');
        measureHeight();
    }

    function measureHeight() {
        if (!stackWrap) return;
        var style = getComputedStyle(stackWrap);
        var paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
        stackWrap.style.height = (stackCards[current].offsetHeight + paddingY) + 'px';
    }

    function wrap(index) {
        return ((index % count) + count) % count;
    }

    if (stackWrap && count) {
        render(false);
        measureHeight();
        window.addEventListener('resize', measureHeight);

        var dragging = false;
        var startX = 0;
        var startY = 0;
        var axisLocked = null;
        var dragStartProgress = 0;

        stackWrap.addEventListener('pointerdown', function (event) {
            if (event.target.closest('input, select, textarea, a, button:not(.category-card)')) return;
            dragging = true;
            axisLocked = null;
            startX = event.clientX;
            startY = event.clientY;
            dragStartProgress = dragProgress;
        });

        stackWrap.addEventListener('pointermove', function (event) {
            if (!dragging) return;
            var dx = event.clientX - startX;
            var dy = event.clientY - startY;
            if (axisLocked === null && (Math.abs(dx) > 6 || Math.abs(dy) > 6)) {
                axisLocked = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y';
            }
            if (axisLocked !== 'x') return;
            dragProgress = dragStartProgress - dx / (stackWrap.offsetWidth * 0.52);
            render(false);
        });

        function endDrag(event) {
            if (!dragging) return;
            dragging = false;

            if (axisLocked === 'x') {
                var steps = Math.round(dragProgress);
                if (steps !== 0) current = wrap(current + steps);
                dragProgress = 0;
                render(true);
                measureHeight();
            } else if (axisLocked === null) {
                dragProgress = 0;
                var cardButton = event && event.target.closest('.category-card');
                if (cardButton) toggleCollapse(cardButton);
            } else {
                dragProgress = 0;
                render(true);
            }
        }

        stackWrap.addEventListener('pointerup', endDrag);
        stackWrap.addEventListener('pointerleave', function (event) {
            if (dragging) endDrag(event);
        });
    }

    document.querySelectorAll('.status-toggle').forEach(function (toggle) {
        toggle.addEventListener('click', function (event) {
            event.stopPropagation();
            var form = toggle.parentElement.querySelector('.status-form');
            document.querySelectorAll('.status-form').forEach(function (f) {
                if (f !== form) f.classList.add('hidden');
            });
            form.classList.toggle('hidden');
        });
    });

    document.addEventListener('click', function () {
        document.querySelectorAll('.status-form').forEach(function (f) {
            f.classList.add('hidden');
        });
    });

    var shareToggle = document.getElementById('share-toggle');
    var shareBox = document.getElementById('share-box');
    var shareCopy = document.getElementById('share-copy');
    var shareLink = document.getElementById('share-link');

    if (shareToggle) {
        shareToggle.addEventListener('click', function (event) {
            event.stopPropagation();
            shareBox.classList.toggle('hidden');
        });
    }

    if (shareCopy) {
        shareCopy.addEventListener('click', function () {
            shareLink.select();
            navigator.clipboard.writeText(shareLink.value).then(function () {
                var original = shareCopy.textContent;
                shareCopy.textContent = 'Copiat!';
                setTimeout(function () { shareCopy.textContent = original; }, 1500);
            });
        });
    }

    var lightbox = document.getElementById('lightbox');
    var lightboxImg = document.getElementById('lightbox-img');
    var lightboxClose = document.getElementById('lightbox-close');

    function openLightbox(src) {
        lightboxImg.src = src;
        lightbox.classList.remove('hidden');
        lightbox.classList.add('flex');
    }

    function closeLightbox() {
        lightbox.classList.add('hidden');
        lightbox.classList.remove('flex');
        lightboxImg.src = '';
    }

    document.querySelectorAll('.artboard-thumb').forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            openLightbox(thumb.dataset.full);
        });
    });

    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightbox) {
        lightbox.addEventListener('click', function (event) {
            if (event.target === lightbox) closeLightbox();
        });
    }
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') closeLightbox();
    });
})();
