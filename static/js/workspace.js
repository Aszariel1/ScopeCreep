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
    var logPanels = Array.prototype.slice.call(document.querySelectorAll('.category-log-panel'));
    var count = stackCards.length;
    var current = 0;
    var dragProgress = 0;
    var logCollapsed = false;

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

    function peekFactor() {
        if (!stackWrap || !stackCards.length) return 0.19;
        var width = stackWrap.offsetWidth;
        var cardWidth = stackCards[0].offsetWidth;
        return width > 0 ? Math.max(0, (width - cardWidth) / 2) / width : 0.19;
    }

    function render(animated) {
        var factor = peekFactor();
        stackCards.forEach(function (card, i) {
            var offset = shortestOffset(i);
            var clamped = Math.max(-1, Math.min(1, offset));
            var width = stackWrap.offsetWidth;
            var translateX = clamped * width * factor;
            var isActive = Math.abs(offset) < 0.5;
            var proximity = Math.max(0, 1 - Math.max(0, Math.abs(offset) - 1));
            var opacity = isActive ? 1 : 0.88 * proximity;
            var z = Math.round(100 - Math.abs(clamped) * 10);

            card.style.transition = animated ? 'transform 0.35s ease, opacity 0.35s ease' : 'none';
            card.style.transform = 'translateX(calc(-50% + ' + translateX + 'px))';
            card.style.opacity = isActive ? '1' : String(opacity);
            card.style.zIndex = String(z);
            card.style.pointerEvents = isActive ? 'auto' : 'none';
            card.classList.toggle('is-active', isActive);
        });

        logPanels.forEach(function (panel, i) {
            panel.classList.toggle('hidden', !(i === current && !logCollapsed));
        });

        var activeChevron = stackCards[current] && stackCards[current].querySelector('.category-chevron');
        if (activeChevron) activeChevron.classList.toggle('is-collapsed', logCollapsed);
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

    var briefPanel = document.getElementById('brief-panel');
    var briefTab = document.getElementById('brief-tab');
    var detailsPanel = document.getElementById('details-panel');
    var detailsTab = document.getElementById('details-tab');
    var briefOpen = false;

    function showAccordionPanel(which) {
        briefOpen = which === 'brief';
        if (briefPanel) briefPanel.classList.toggle('hidden', !briefOpen);
        if (detailsPanel) detailsPanel.classList.toggle('hidden', briefOpen);
        if (!briefOpen) logCollapsed = false;
        if (!stackWrap || !count) return;
        render(false);
        measureHeight();
    }

    if (briefTab) briefTab.addEventListener('click', function () { showAccordionPanel('brief'); });
    if (detailsTab) detailsTab.addEventListener('click', function () { showAccordionPanel('details'); });

    if (stackWrap && count) {
        render(false);
        measureHeight();
        window.addEventListener('resize', function () {
            render(false);
            measureHeight();
        });

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
            dragProgress = dragStartProgress - dx / (stackWrap.offsetWidth * peekFactor());
            render(false);
        });

        function endDrag(event) {
            if (!dragging) return;
            dragging = false;

            if (axisLocked === 'x') {
                var steps = Math.round(dragProgress);
                if (steps !== 0) {
                    current = wrap(current + steps);
                    logCollapsed = false;
                }
                dragProgress = 0;
                render(true);
                measureHeight();
            } else if (axisLocked === null) {
                dragProgress = 0;
                var cardButton = event && event.target.closest('.category-card');
                if (cardButton) {
                    var tappedIndex = stackCards.indexOf(cardButton);
                    if (tappedIndex !== -1) {
                        if (tappedIndex === current) {
                            if (briefOpen) {
                                showAccordionPanel('details');
                            } else {
                                logCollapsed = !logCollapsed;
                            }
                        } else {
                            current = tappedIndex;
                            logCollapsed = false;
                            if (briefOpen) showAccordionPanel('details');
                        }
                        render(true);
                        measureHeight();
                    }
                }
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

    document.querySelectorAll('.category-rename-toggle').forEach(function (toggle) {
        toggle.addEventListener('click', function (event) {
            event.stopPropagation();
            var form = toggle.parentElement.querySelector('.category-rename-form');
            document.querySelectorAll('.category-rename-form').forEach(function (f) {
                if (f !== form) f.classList.add('hidden');
            });
            form.classList.toggle('hidden');
        });
    });

    document.addEventListener('click', function (event) {
        document.querySelectorAll('.status-form, .category-rename-form, #add-category-form, #notif-panel, #calendar-panel').forEach(function (f) {
            if (!f.contains(event.target)) f.classList.add('hidden');
        });
    });

    var notifToggle = document.getElementById('notif-toggle');
    var notifPanel = document.getElementById('notif-panel');
    var calendarToggle = document.getElementById('calendar-toggle');
    var calendarPanel = document.getElementById('calendar-panel');

    if (notifToggle) {
        notifToggle.addEventListener('click', function (event) {
            event.stopPropagation();
            if (calendarPanel) calendarPanel.classList.add('hidden');
            notifPanel.classList.toggle('hidden');
        });
    }

    if (calendarToggle) {
        calendarToggle.addEventListener('click', function (event) {
            event.stopPropagation();
            if (notifPanel) notifPanel.classList.add('hidden');
            calendarPanel.classList.toggle('hidden');
        });
    }

    var addCategoryToggle = document.getElementById('add-category-toggle');
    var addCategoryForm = document.getElementById('add-category-form');

    if (addCategoryToggle) {
        addCategoryToggle.addEventListener('click', function (event) {
            event.stopPropagation();
            addCategoryForm.classList.toggle('hidden');
        });
    }

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
        var shareCopyIcon = shareCopy.innerHTML;
        var checkIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="w-3.5 h-3.5 shrink-0"><path d="M20 6 9 17l-5-5"/></svg>';
        shareCopy.addEventListener('click', function () {
            shareLink.select();
            navigator.clipboard.writeText(shareLink.value).then(function () {
                shareCopy.title = 'Copied!';
                shareCopy.innerHTML = checkIcon;
                setTimeout(function () {
                    shareCopy.title = 'Copy link';
                    shareCopy.innerHTML = shareCopyIcon;
                }, 1500);
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
