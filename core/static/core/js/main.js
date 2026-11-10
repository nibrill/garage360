/* Garage360 · interacciones de interfaz (sin dependencias) */
(function () {
    'use strict';
    var root = document.documentElement;

    // --- Tema claro / oscuro --------------------------------------------------
    function setTheme(t) {
        root.setAttribute('data-bs-theme', t);
        try { localStorage.setItem('g360-theme', t); } catch (e) {}
        document.querySelectorAll('[data-theme-toggle] i').forEach(function (i) {
            i.className = t === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        });
    }
    document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-theme-toggle]');
        if (b) setTheme(root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark');
    });
    setTheme(root.getAttribute('data-bs-theme') || 'dark');

    // --- Navbar: sombra al hacer scroll --------------------------------------
    var nav = document.querySelector('.site-nav');
    function onScroll() { if (nav) nav.classList.toggle('scrolled', window.scrollY > 12); }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // --- Aparición al hacer scroll ---------------------------------------------
    var items = document.querySelectorAll('.reveal');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
            });
        }, { threshold: 0.12 });
        items.forEach(function (el) { io.observe(el); });
    } else {
        items.forEach(function (el) { el.classList.add('in'); });
    }

    // --- Contadores animados ---------------------------------------------------
    var counters = document.querySelectorAll('[data-count]');
    function runCounter(el) {
        var target = parseFloat(el.dataset.count), suffix = el.dataset.suffix || '', t0 = null;
        function step(ts) {
            if (!t0) t0 = ts;
            var p = Math.min((ts - t0) / 1200, 1), v = target * (1 - Math.pow(1 - p, 3));
            el.textContent = Math.round(v) + suffix;
            if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }
    if ('IntersectionObserver' in window) {
        var co = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) { if (en.isIntersecting) { runCounter(en.target); co.unobserve(en.target); } });
        }, { threshold: 0.6 });
        counters.forEach(function (el) { co.observe(el); });
    }

    // --- Brillo que sigue al cursor en las tarjetas -----------------------------
    document.addEventListener('pointermove', function (e) {
        var t = e.target.closest && e.target.closest('.tile');
        if (!t) return;
        var r = t.getBoundingClientRect();
        t.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        t.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });

    // --- Confirmación antes de enviar formularios con data-confirm ---------------
    document.addEventListener('submit', function (e) {
        var f = e.target;
        if (!f.dataset || !f.dataset.confirm || f.dataset.confirmed) return;
        e.preventDefault();
        var go = function () { f.dataset.confirmed = '1'; f.submit(); };
        if (window.Swal) {
            Swal.fire({ title: f.dataset.confirm, icon: 'warning', showCancelButton: true,
                confirmButtonColor: '#7c5cff', cancelButtonColor: '#6b7280',
                confirmButtonText: 'Sí, continuar', cancelButtonText: 'Cancelar' })
                .then(function (r) { if (r.isConfirmed) go(); });
        } else if (window.confirm(f.dataset.confirm)) { go(); }
    });
})();
