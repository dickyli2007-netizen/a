/* Farless theme script: the film hero, the menu bar's panels (side menu, search, favourites), the
   safety knob, the shop gallery, the product picker, the entrances and the arcs. Every part starts per section and can be stopped again, so when the theme
   editor reloads a section after an edit, that section starts afresh.
   build_shopify.py copies this to assets/farless.js and fills in the product picker from the
   product page template (farless-work/product-page/build.py, JS_PICKER). */
(() => {
  'use strict';
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const smoothstep = (p, e0, e1) => { const t = clamp((p - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); };
  const easeInOut = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  function rng(seed){ let s = seed >>> 0; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  // in the theme editor everything shows at rest, so nothing being edited is hidden behind an entrance
  const designMode = !!(window.Shopify && window.Shopify.designMode);
  // the film leaves scrolling and keys alone while the side menu is open
  const menuOpen = () => document.documentElement.classList.contains('menu-open');

  /* ---------- split words once ---------- */
  function splitWords(root){
    const r = rng(7);
    root.querySelectorAll('.split').forEach(el => {
      if (el.dataset.split) return;
      el.dataset.split = '1';
      const text = el.textContent.trim();
      el.setAttribute('aria-label', text);
      el.textContent = '';
      const words = text.split(' ');
      words.forEach((w, i) => {
        const s = document.createElement('span');
        s.className = 'w'; s.setAttribute('aria-hidden', 'true');
        s.textContent = w;
        s.style.setProperty('--th', (i / words.length * 0.5 + r() * 0.04).toFixed(3));
        el.appendChild(s);
        if (i < words.length - 1) el.appendChild(document.createTextNode(' '));
      });
    });
  }

  /* ---------- hero: point to point ---------- */
  function initHero(root){
    const stage = root.querySelector('#stage');
    if (!stage) return null;
    const off = [];   // everything to undo when the section goes away
    const on = (target, type, fn, opts) => { target.addEventListener(type, fn, opts); off.push(() => target.removeEventListener(type, fn, opts)); };

    // VP9 WebM is half the size; Apple devices and browsers without it get the H.264 MP4 first,
    // and whichever loads first falls back to the other if it cannot play
    const ua = navigator.userAgent;
    const apple = /iPad|iPhone|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) || (/Safari\//.test(ua) && !/Chrome|Chromium|CriOS|FxiOS|Edg|Android/.test(ua));
    const canWebm = document.createElement('video').canPlayType('video/webm; codecs="vp9"') === 'probably';
    const ds = stage.dataset;
    const WEBM = ds.webm ? { url: ds.webm, type: 'video/webm', bytes: +ds.webmBytes || 0 } : null;
    const MP4 = ds.mp4 ? { url: ds.mp4, type: 'video/mp4', bytes: +ds.mp4Bytes || 0 } : null;
    const SOURCES = (canWebm && !apple ? [WEBM, MP4] : [MP4, WEBM]).filter(Boolean);

    const video = stage.querySelector('#hero');
    const loadLine = stage.querySelector('.hero-note .line');
    const posterLayer = stage.querySelector('.poster');
    const posterEnd = stage.querySelector('.poster-end');
    const bands = [...stage.querySelectorAll('.band')].map(el => ({ el, t: el.dataset.t, raf: null }));
    const dots = [...stage.querySelectorAll('.dots button')];
    const LAST = Math.max(0, bands.length - 1);
    let point = 0, videoReady = false, videoFailed = false, anim = null, ctrl = null, blobUrl = null, gone = false;

    const timeOf = i => {
      const d = video.duration || 8;
      const t = bands[i] ? bands[i].t : '0';
      return Math.min(t === 'end' ? d : (parseFloat(t) || 0), d - 0.04);
    };

    // captions assemble on a time-based --k, the same entrance language as the rest of the page
    function assemble(band){
      cancelAnimationFrame(band.raf);
      band.el.style.setProperty('--k', '0');
      const t0 = performance.now() + 220;
      const step = now => {
        const k = smoothstep(Math.max(0, now - t0) / 1100, 0, 1);
        band.el.style.setProperty('--k', k.toFixed(3));
        if (k < 1) band.raf = requestAnimationFrame(step);
      };
      band.raf = requestAnimationFrame(step);
    }

    function render(prev){
      stage.dataset.point = point;
      bands.forEach((b, i) => {
        const isOn = i === point;
        b.el.classList.toggle('on', isOn);
        if (b.el.classList.contains('settle')) b.el.inert = !isOn;
        if (isOn && i !== prev) assemble(b);
      });
      dots.forEach((d, i) => {
        if (i === point) d.setAttribute('aria-current', 'step'); else d.removeAttribute('aria-current');
      });
      if (videoFailed) stage.style.setProperty('--pe', (point / (LAST || 1)).toFixed(3));
    }

    let seekBusy = false, pendingTime = null;
    function requestSeek(t){
      if (!video.duration || videoFailed) return;
      if (seekBusy){ pendingTime = t; return; }
      seekBusy = true;
      video.currentTime = t;
    }
    on(video, 'seeked', () => {
      seekBusy = false;
      if (pendingTime !== null){ const t = pendingTime; pendingTime = null; requestSeek(t); }
    });
    // a format that downloads but cannot decode here gets one retry with the other format
    on(video, 'error', () => { if (gone) return; seekBusy = false; pendingTime = null; if (srcIndex >= 0 && srcIndex + 1 < SOURCES.length && !videoReady) tryLoad(srcIndex + 1); else failVideo(); });

    function stopAnim(){
      if (anim){ cancelAnimationFrame(anim.raf); anim = null; }
      if (!video.paused) video.pause();
    }
    // forward: real playback, eased in and out with the playback rate; backward: eased seeks
    function playTo(target){
      stopAnim();
      if (!videoReady) return;
      const from = video.currentTime;
      if (target <= from + 0.05){ seekTween(from, target); return; }
      const a = anim = { raf: 0 };
      let lastRate = 0;
      const watch = () => {
        if (anim !== a) return;
        const ct = video.currentTime;
        if (ct >= target - 0.03 || video.ended){
          video.pause();
          if (Math.abs(ct - target) > 0.06) requestSeek(target);
          anim = null; return;
        }
        const p = clamp((ct - from) / (target - from), 0, 1);
        const rate = clamp(0.55 + 1.25 * Math.sin(Math.PI * p), 0.5, 1.8);
        if (Math.abs(rate - lastRate) > 0.05){ lastRate = rate; video.playbackRate = rate; }
        a.raf = requestAnimationFrame(watch);
      };
      video.playbackRate = 0.6;
      video.play().then(() => { if (anim === a) a.raf = requestAnimationFrame(watch); })
        .catch(() => { if (anim === a){ anim = null; seekTween(from, target); } });
    }
    function seekTween(from, target){
      const dur = clamp(Math.abs(target - from) / 2.4, 0.45, 1.6) * 1000;
      const a = anim = { raf: 0 };
      const t0 = performance.now();
      const step = now => {
        if (anim !== a) return;
        const t = Math.min(1, (now - t0) / dur);
        requestSeek(from + (target - from) * easeInOut(t));
        if (t < 1) a.raf = requestAnimationFrame(step); else anim = null;
      };
      a.raf = requestAnimationFrame(step);
    }

    /* portrait screens: slide the wide film so the point's subject stays in view */
    const pan = stage.querySelector('.pan');
    const portrait = matchMedia('(orientation: portrait)');
    function panTo(i, ms){
      if (!portrait.matches){ pan.style.removeProperty('--panx'); return; }
      const h = pan.offsetHeight, w = stage.offsetWidth;
      if (!h || !bands[i]) return;
      const sc = h / 1080, cx = +bands[i].el.dataset.cx || 960;
      const x = clamp(cx * sc - w / 2, 0, Math.max(0, 1920 * sc - w));
      if (ms === 0) pan.classList.add('snap');
      else pan.style.transitionDuration = (ms / 1000).toFixed(2) + 's';
      pan.style.setProperty('--panx', x.toFixed(1) + 'px');
      if (ms === 0){ void pan.offsetWidth; pan.classList.remove('snap'); }
    }
    on(window, 'resize', () => panTo(point, 0));
    on(portrait, 'change', () => panTo(point, 0));

    function goTo(i, instant){
      i = clamp(i, 0, LAST);
      if (i === point) return;
      const prev = point;
      point = i;
      render(prev);
      const dt = Math.abs(timeOf(i) - timeOf(prev));
      panTo(i, instant ? 0 : Math.round(clamp(i > prev ? dt / 1.25 : dt / 2.4, 0.6, 2.2) * 1000));
      if (instant){ stopAnim(); requestSeek(timeOf(i)); }
      else playTo(timeOf(i));
    }

    /* one scroll gesture moves one point; momentum in the same gesture never moves another */
    const atTop = () => scrollY <= 1;
    const canMove = dir => dir > 0 ? point < LAST : point > 0;
    let lastWheel = 0, gTop = false, gUsed = false, acc = 0;
    function onWheel(e){
      if (e.ctrlKey || menuOpen()) return;
      const now = performance.now();
      if (now - lastWheel > 220){ gTop = atTop(); gUsed = false; acc = 0; }
      lastWheel = now;
      if (!atTop()) return;
      if (gUsed){ e.preventDefault(); return; }
      const dy = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
      const dir = Math.sign(dy);
      if (!dir || !canMove(dir)) return;
      e.preventDefault();
      if (!gTop) return;
      acc += dy;
      if (Math.abs(acc) >= 18){ gUsed = true; goTo(point + dir); }
    }
    let ty = 0, tTop = false, tUsed = false;
    function onTouchStart(e){ ty = e.touches[0].clientY; tTop = atTop(); tUsed = false; }
    function onTouchMove(e){
      if (!tTop || !atTop() || menuOpen()) return;
      if (tUsed){ e.preventDefault(); return; }
      const dy = ty - e.touches[0].clientY;
      const dir = Math.sign(dy);
      if (!dir || !canMove(dir)) return;
      e.preventDefault();
      if (Math.abs(dy) > 36){ tUsed = true; goTo(point + dir); }
    }
    function onKey(e){
      if (!atTop() || e.altKey || e.ctrlKey || e.metaKey || menuOpen()) return;
      const el = e.target;
      if (el.closest && el.closest('input,textarea,select,[contenteditable]')) return;
      if (e.key === ' ' && el.closest && el.closest('button,a,summary')) return;
      let dir = 0;
      if (e.key === 'ArrowDown' || e.key === 'PageDown' || (e.key === ' ' && !e.shiftKey)) dir = 1;
      else if (e.key === 'ArrowUp' || e.key === 'PageUp' || (e.key === ' ' && e.shiftKey)) dir = -1;
      if (!dir || !canMove(dir)) return;
      e.preventDefault();
      if (!e.repeat) goTo(point + dir);
    }
    // anyone who leaves the hero comes back to its resting point
    function onScrollAway(){ if (scrollY > innerHeight * 0.6 && point !== LAST) goTo(LAST, true); }
    dots.forEach((d, i) => on(d, 'click', () => goTo(i)));

    let heroInit = false;
    function initHeroOnce(){
      if (heroInit) return; heroInit = true;
      posterLayer.style.backgroundImage = `url('${ds.poster}')`;
      let started = false;
      const startBlobFetch = () => { if (started || gone) return; started = true; tryLoad(0); };
      const img = new Image();
      img.onload = startBlobFetch; img.onerror = startBlobFetch;
      img.src = ds.poster;
      setTimeout(startBlobFetch, 4000);
    }
    let srcIndex = -1;
    function tryLoad(i){
      if (gone) return;
      if (i >= SOURCES.length){ failVideo(); return; }
      srcIndex = i;
      loadHeroBlob(SOURCES[i]).catch(() => tryLoad(i + 1));
    }
    async function loadHeroBlob(src){
      ctrl = new AbortController();
      const c = ctrl;
      let watchdog = setTimeout(() => c.abort(), 20000);
      const res = await fetch(src.url, { priority: 'low', signal: c.signal });
      if (!res.ok) throw new Error('video ' + res.status);
      const total = Number(res.headers.get('Content-Length')) || src.bytes || 4e6;
      const reader = res.body.getReader();
      const chunks = []; let got = 0, lastRing = 0;
      for (;;){
        const { done, value } = await reader.read();
        if (done) break;
        clearTimeout(watchdog); watchdog = setTimeout(() => c.abort(), 20000);
        chunks.push(value); got += value.length;
        const frac = Math.min(1, got / total), now = performance.now();
        if (now - lastRing > 100 || frac === 1){ lastRing = now; loadLine.style.setProperty('--lp', frac.toFixed(3)); }
      }
      clearTimeout(watchdog);
      if (gone) return;
      loadLine.style.setProperty('--lp', '1');
      blobUrl = URL.createObjectURL(new Blob(chunks, { type: src.type }));
      video.src = blobUrl;
      video.load();
      video.addEventListener('canplay', () => {
        videoReady = true;
        requestSeek(timeOf(point));
        stage.classList.add('video-ready');
      }, { once: true });
    }
    function failVideo(){
      if (videoFailed) return;
      videoFailed = true;
      stopAnim();
      stage.classList.add('video-failed');
      video.style.display = 'none';
      posterEnd.style.backgroundImage = `url('${ds.ending}')`;
      render(point);
    }

    /* the static-hero gates, live (kept identical to the CSS query) */
    const GATES = [
      '(orientation: landscape) and (pointer: coarse) and (max-height: 560px)',
      '(prefers-reduced-motion: reduce)'
    ];
    let stepperOn = false;
    const winOpts = [['wheel', onWheel, { passive: false }], ['touchstart', onTouchStart, { passive: true }], ['touchmove', onTouchMove, { passive: false }], ['keydown', onKey, undefined], ['scroll', onScrollAway, { passive: true }]];
    function enableStepper(){
      if (stepperOn) return; stepperOn = true;
      initHeroOnce();
      winOpts.forEach(([t, f, o]) => addEventListener(t, f, o));
      if (scrollY > innerHeight * 0.6) point = LAST;
      render(-1);
      panTo(point, 0);
      if (videoReady) requestSeek(timeOf(point));
    }
    function disableStepper(){
      if (!stepperOn) return; stepperOn = false;
      winOpts.forEach(([t, f, o]) => removeEventListener(t, f, o));
      stopAnim();
    }
    function applyHeroMode(){ GATES.some(q => matchMedia(q).matches) ? disableStepper() : enableStepper(); }
    GATES.map(q => matchMedia(q)).forEach(m => on(m, 'change', applyHeroMode));
    applyHeroMode();

    return {
      goTo,
      indexOf: el => bands.findIndex(b => b.el === el),
      reapply: applyHeroMode,
      destroy(){
        gone = true;
        disableStepper();
        off.forEach(f => f());
        bands.forEach(b => cancelAnimationFrame(b.raf));
        if (ctrl) ctrl.abort();
        if (blobUrl) URL.revokeObjectURL(blobUrl);
      },
    };
  }

  /* ---------- header: transparent over the film, solid once anything scrolls under it ---------- */
  function updateNav(){
    const nav = document.querySelector('nav.top');
    if (nav) nav.classList.toggle('solid', scrollY > 8);
  }
  addEventListener('scroll', updateNav, { passive: true });
  addEventListener('resize', updateNav);

  /* ---------- favourites: kept in this browser; every heart and the bar's count follow them ---------- */
  const FAV_KEY = 'farless:favourites';
  let favMem = null;
  function favList(){
    if (favMem) return favMem;
    // each colour is its own favourite, keyed by product and variant; older entries are keyed by product alone
    try { const v = JSON.parse(localStorage.getItem(FAV_KEY) || '[]'); favMem = Array.isArray(v) ? v.filter(x => x && x.handle).map(x => ({ ...x, key: x.key || x.handle })) : []; }
    catch (err){ favMem = []; }
    return favMem;
  }
  function favWrite(list){
    favMem = list;
    try { localStorage.setItem(FAV_KEY, JSON.stringify(list)); } catch (err){}
    syncFavs();
  }
  const X_ICON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true"><path d="M2 2l12 12M14 2L2 14"/></svg>';
  function renderFavList(ul){
    const list = favList();
    const panel = ul.closest('[data-panel]');
    const empty = panel && panel.querySelector('[data-fav-empty]');
    if (empty) empty.hidden = list.length > 0;
    ul.hidden = !list.length;
    const removeLabel = ul.dataset.removeLabel || 'Remove';
    ul.replaceChildren(...list.map(item => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.className = 'fp-item'; a.href = item.url || '#';
      const thumb = document.createElement('span'); thumb.className = 'fp-thumb';
      if (item.image){ const img = document.createElement('img'); img.src = item.image; img.alt = ''; img.loading = 'lazy'; thumb.append(img); }
      const text = document.createElement('span');
      const h = document.createElement('h3'); h.textContent = item.title; text.append(h);
      if (item.sub){ const sub = document.createElement('span'); sub.className = 'fp-sub'; sub.textContent = item.sub; text.append(sub); }
      a.append(thumb, text);
      const rm = document.createElement('button');
      rm.type = 'button'; rm.className = 'fp-remove'; rm.dataset.favRemove = item.key;
      rm.setAttribute('aria-label', `${removeLabel}: ${item.title}${item.sub ? ', ' + item.sub : ''}`); rm.innerHTML = X_ICON;
      li.append(a, rm);
      return li;
    }));
  }
  function syncFavs(){
    const list = favList();
    const saved = new Set(list.map(x => x.key));
    document.querySelectorAll('[data-fav]').forEach(b => b.setAttribute('aria-pressed', saved.has(b.dataset.fav) ? 'true' : 'false'));
    document.querySelectorAll('[data-fav-count]').forEach(c => { c.textContent = list.length; c.hidden = !list.length; });
    document.querySelectorAll('[data-fav-list]').forEach(renderFavList);
  }
  document.addEventListener('click', e => {
    const heart = e.target.closest('[data-fav]');
    if (heart){
      e.preventDefault();
      const d = heart.dataset, list = favList();
      favWrite(list.some(x => x.key === d.fav) ? list.filter(x => x.key !== d.fav)
        : [{ key: d.fav, handle: d.favHandle || d.fav, variant: d.favVariant || '', title: d.favTitle || '', url: d.favUrl || '', image: d.favImage || '', sub: d.favSub || '' }, ...list]);
      heart.classList.remove('beat'); void heart.offsetWidth; heart.classList.add('beat');
      return;
    }
    const rm = e.target.closest('[data-fav-remove]');
    if (rm){
      const ul = rm.closest('[data-fav-list]');
      const items = [...ul.querySelectorAll('[data-fav-remove]')];
      const at = items.indexOf(rm);
      favWrite(favList().filter(x => x.key !== rm.dataset.favRemove));
      // keep focus in the list: the next piece's remove button, or the panel's close button once it is empty
      const left = [...ul.querySelectorAll('[data-fav-remove]')];
      (left[Math.min(at, left.length - 1)] || ul.closest('[data-panel]').querySelector('[data-close]'))?.focus({ preventScroll: true });
    }
  });
  addEventListener('storage', e => { if (e.key === FAV_KEY){ favMem = null; syncFavs(); } });
  // on the store, drop saved pieces and colours that are gone and pick up renamed ones
  let favChecked = false;
  async function refreshFavs(){
    if (favChecked || !(window.Shopify && window.Shopify.routes)) return;
    favChecked = true;
    const root = window.Shopify.routes.root || '/';
    const list = favList().slice();
    let changed = false;
    const gone = new Set();
    await Promise.all([...new Set(list.map(x => x.handle))].map(async handle => {
      try {
        const r = await fetch(`${root}products/${encodeURIComponent(handle)}.js`);
        if (r.status === 404){ list.forEach(x => { if (x.handle === handle) gone.add(x.key); }); changed = true; return; }
        if (!r.ok) return;
        const p = await r.json();
        list.filter(x => x.handle === handle).forEach(item => {
          if (item.variant && !(p.variants || []).some(v => String(v.id) === String(item.variant))){ gone.add(item.key); changed = true; return; }
          if (p.title && p.title !== item.title){ item.title = p.title; changed = true; }
        });
      } catch (err){}
    }));
    if (changed) favWrite(list.filter(x => !gone.has(x.key)));
  }

/*FARLESS_CART*/
  // Add to cart opens the cart panel of the menu bar
  function openPanel(name){ menus.forEach(m => m.open(name)); }

  /* ---------- panels: the side menu (left), search (top), favourites and the cart (right), one open at a time;
     Close, the shade, Escape or a link close them, focus stays inside, the page behind is out of reach ---------- */
  const HEART_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.3s-7.4-4.5-9.1-9.1C1.7 7.8 3.9 4.6 7.3 4.6c2 0 3.5 1 4.7 2.7 1.2-1.7 2.7-2.7 4.7-2.7 3.4 0 5.6 3.2 4.4 6.6-1.7 4.6-9.1 9.1-9.1 9.1z"/></svg>';
  function initPanels(root){
    const panels = [...root.querySelectorAll('[data-panel]')];
    if (!panels.length) return null;
    const html = document.documentElement;
    let current = null, opener = null, shut = [];
    const menu = root.querySelector('[data-panel="menu"]');
    const main = menu && menu.querySelector('.sm-main'), sub = menu && menu.querySelector('.sm-sub'), subOpener = menu && menu.querySelector('[data-sub-open]');
    const focusables = () => [...current.querySelectorAll('a[href],button,input,select,textarea')].filter(el => !el.disabled && !el.closest('[inert]') && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
    function setSub(on, focus){
      if (!sub) return;
      menu.classList.toggle('sub', on);
      if (subOpener) subOpener.setAttribute('aria-expanded', on ? 'true' : 'false');
      main.inert = on;
      sub.inert = !on;
      if (focus) (on ? sub.querySelector('[data-sub-close]') : subOpener)?.focus({ preventScroll: true });
    }
    // quiet: opened by the theme editor, so focus stays with the editor and the page stays reachable
    function open(name, from, quiet){
      const panel = panels.find(p => p.dataset.panel === name);
      if (!panel || panel === current) return;
      if (current) close(false);
      current = panel;
      opener = from || root.querySelector(`[data-open="${name}"]`);
      if (panel === menu) setSub(false);
      panel.classList.add('open');
      html.classList.add('menu-open');
      root.querySelectorAll(`[data-open="${name}"]`).forEach(b => b.setAttribute('aria-expanded', 'true'));
      if (name === 'favourites') refreshFavs();
      if (name === 'cart') refreshCart();
      if (quiet === true) return;
      shut = [...document.body.children].filter(el => !el.contains(panel) && !el.inert && !el.matches('.menu-scrim'));
      const bar = root.querySelector('nav.top');
      if (bar && !bar.contains(panel)) shut.push(bar);
      shut.forEach(el => { el.inert = true; });
      const first = panel.querySelector('[data-autofocus]') || panel.querySelector('.sm-close');
      setTimeout(() => first && first.focus({ preventScroll: true }), 60);
    }
    function close(returnFocus){
      if (!current) return;
      const name = current.dataset.panel, back = opener;
      current.classList.remove('open');
      html.classList.remove('menu-open');
      root.querySelectorAll(`[data-open="${name}"]`).forEach(b => b.setAttribute('aria-expanded', 'false'));
      shut.forEach(el => { el.inert = false; });
      shut = []; current = null; opener = null;
      if (returnFocus !== false && back) back.focus({ preventScroll: true });
    }
    function onClick(e){
      const t = e.target.closest('[data-open],[data-close],[data-sub-open],[data-sub-close],[data-panel] a[href]');
      if (!t || !root.contains(t)) return;
      if (t.matches('[data-open]')){ e.preventDefault(); if (current && current.dataset.panel === t.dataset.open) close(); else open(t.dataset.open, t); }
      else if (t.matches('[data-close]')) close();
      else if (t.matches('[data-sub-open]')) setSub(true, true);
      else if (t.matches('[data-sub-close]')) setSub(false, true);
      else close(false);   // a link: the panel closes and the page follows it
    }
    function onKeyDown(e){
      if (!current) return;
      if (e.key === 'Escape'){
        e.preventDefault();
        if (current === menu && menu.classList.contains('sub')) setSub(false, true); else close();
      } else if (e.key === 'Tab'){
        const f = focusables();
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && (document.activeElement === first || !current.contains(document.activeElement))){ e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && (document.activeElement === last || !current.contains(document.activeElement))){ e.preventDefault(); first.focus(); }
      }
    }
    if (sub) sub.inert = true;
    const stopSearch = initSearch(root.querySelector('[data-panel="search"]'));
    root.addEventListener('click', onClick);
    document.addEventListener('keydown', onKeyDown);
    syncFavs();
    return { open, close, destroy(){ close(false); stopSearch(); root.removeEventListener('click', onClick); document.removeEventListener('keydown', onKeyDown); } };
  }

  /* ---------- search: the pieces that match appear as you type; Enter opens the full results page ---------- */
  function initSearch(panel){
    if (!panel) return () => {};
    const form = panel.querySelector('[data-search-form]'), input = form.querySelector('input[name="q"]');
    const out = panel.querySelector('[data-search-results]'), idle = panel.querySelector('[data-search-idle]');
    const local = panel.querySelector('[data-search-local]');
    const items = local ? JSON.parse(local.textContent) : null;
    const L = panel.dataset;
    let timer = 0, ctrl = null, last = null;
    const heading = text => { const p = document.createElement('p'); p.className = 'label'; p.textContent = text; return p; };
    function card(it){
      const li = document.createElement('li'); li.className = 'cl-card';
      const a = document.createElement('a'); a.href = it.url;
      const pic = document.createElement('div'); pic.className = 'cl-pic';
      const obj = document.createElement('div'); obj.className = 'cl-obj';
      obj.style.cssText = `--ar:${it.ar};--shadow-x:${it.foot}%;--shadow-w:34%`;
      const img = document.createElement('img'); img.src = it.image; img.alt = ''; img.loading = 'lazy';
      obj.append(img); pic.append(obj);
      const meta = document.createElement('div'); meta.className = 'cl-meta';
      const h = document.createElement('h2'); h.textContent = it.title; meta.append(h);
      const lab = document.createElement('span'); lab.className = 'label';
      lab.textContent = it.colours > 1 ? `${it.colours} ${L.labelColours || 'colours'}` : (L.labelSold || 'Sold out');
      meta.append(lab);
      a.append(pic, meta);
      const fav = document.createElement('button');
      fav.type = 'button'; fav.className = 'fav';
      Object.assign(fav.dataset, { fav: `${it.handle}:${it.colourKey || ''}`, favHandle: it.handle, favTitle: it.title, favUrl: it.url, favImage: it.image, favSub: it.colour || '' });
      fav.setAttribute('aria-label', `${L.labelSave || 'Save to favourites'}: ${it.title}${it.colour ? ', ' + it.colour : ''}`);
      fav.innerHTML = HEART_ICON;
      li.append(a, fav);
      return li;
    }
    function show(nodes, q){
      idle.hidden = true;
      out.replaceChildren(...nodes);
      if (!nodes.length){ const p = document.createElement('p'); p.className = 'sp-none'; p.textContent = L.labelNone || 'Nothing matches that yet.'; out.append(p); }
      if (L.searchPage){
        const all = document.createElement('a'); all.className = 'link sp-all';
        all.href = `${L.searchPage}?q=${encodeURIComponent(q)}&type=product`; all.textContent = L.labelAll || 'See all results';
        out.append(all);
      }
      // the words on fetched cards follow the menu bar's settings
      if (L.labelSave) out.querySelectorAll('[data-fav]').forEach(f => f.setAttribute('aria-label', `${L.labelSave}: ${f.dataset.favTitle}${f.dataset.favSub ? ', ' + f.dataset.favSub : ''}`));
      if (L.labelSold) out.querySelectorAll('[data-sold]').forEach(x => { x.textContent = L.labelSold; });
      syncFavs();
    }
    async function run(){
      const q = input.value.trim();
      if (q === last) return;
      last = q;
      if (ctrl) ctrl.abort();
      if (!q){ out.replaceChildren(); idle.hidden = false; return; }
      if (items){
        const words = q.toLowerCase().split(/\s+/);
        const hits = items.filter(it => words.every(w => `${it.title} ${it.sub || ''} ${it.colour || ''}`.toLowerCase().includes(w)));
        const nodes = [];
        if (hits.length){ const ul = document.createElement('ul'); ul.className = 'sp-grid'; ul.append(...hits.map(card)); nodes.push(heading(L.labelProducts || 'Pieces'), ul); }
        show(nodes, q);
        return;
      }
      ctrl = new AbortController();
      try {
        const r = await fetch(`${L.suggestUrl}?q=${encodeURIComponent(q)}&resources[type]=product,collection&resources[limit]=8&resources[options][unavailable_products]=last&section_id=farless-predictive`, { signal: ctrl.signal });
        const doc = new DOMParser().parseFromString(await r.text(), 'text/html');
        const nodes = [];
        const products = doc.querySelector('[data-results="products"]'), cols = doc.querySelector('[data-results="collections"]');
        if (products){ nodes.push(heading(L.labelProducts || 'Pieces'), products); }
        if (cols){ nodes.push(heading(L.labelCollections || 'Collections'), cols); }
        show(nodes, q);
      } catch (err){ if (err.name !== 'AbortError') show([], q); }
    }
    const onInput = () => { clearTimeout(timer); timer = setTimeout(run, 180); };
    const onSubmit = e => {
      if (!L.searchPage || !input.value.trim()){ e.preventDefault(); clearTimeout(timer); last = null; run(); }
    };
    input.addEventListener('input', onInput);
    form.addEventListener('submit', onSubmit);
    return () => { clearTimeout(timer); if (ctrl) ctrl.abort(); input.removeEventListener('input', onInput); form.removeEventListener('submit', onSubmit); };
  }

  /* ---------- shop gallery: thumbnails swap the main image ---------- */
  function initGallery(root){
    root.querySelectorAll('[data-gallery]').forEach(g => {
      const main = g.querySelector('.f-main');
      const thumbs = [...g.querySelectorAll('.f-thumbs button')];
      if (!main) return;
      thumbs.forEach(t => t.addEventListener('click', () => {
        if (t.hasAttribute('aria-current')) return;
        thumbs.forEach(x => x.removeAttribute('aria-current'));
        t.setAttribute('aria-current', 'true');
        main.classList.add('swap');
        setTimeout(() => {
          const show = () => main.classList.remove('swap');
          main.onload = show;
          main.srcset = t.dataset.srcset || '';
          main.src = t.dataset.src;
          main.alt = t.dataset.alt || '';
          if (main.complete) show();
        }, reduce.matches ? 0 : 280);
      }));
    });
  }

  /* ---------- entrances ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in');
    io.unobserve(e.target);
    setTimeout(() => e.target.classList.add('settled'), 1400);
  }), { rootMargin: '0px 0px -12% 0px' });
  function observeEntrances(root){
    root.querySelectorAll('[data-in],[data-strike]').forEach(el => {
      if (designMode || reduce.matches) el.classList.add('in', 'settled');
      else io.observe(el);
    });
  }

  /* ---------- pause loops off-screen and on hidden tabs ---------- */
  const loopIO = new IntersectionObserver(es => es.forEach(e => e.target.classList.toggle('loop-off', !e.isIntersecting)));
  function watchLoops(root){ root.querySelectorAll('section.sec').forEach(el => loopIO.observe(el)); }
  document.addEventListener('visibilitychange', () => document.body.classList.toggle('paused', document.hidden));

  /* ---------- the arc seams, drawn by scroll ---------- */
  let seams = [];
  const seamIO = new IntersectionObserver(es => es.forEach(e => { const s = seams.find(x => x.el === e.target); if (s) s.on = e.isIntersecting; }), { rootMargin: '10% 0px' });
  function addSeams(root){
    root.querySelectorAll('.seam').forEach(el => {
      if (seams.some(s => s.el === el)) return;
      const s = { el, d: -1, on: false };
      seams.push(s);
      seamIO.observe(el);
      if (designMode || reduce.matches){ s.d = 1; el.style.setProperty('--d', '1'); }
    });
    drawSeams();
  }
  function removeSeams(root){
    seams = seams.filter(s => { const keep = !root.contains(s.el); if (!keep) seamIO.unobserve(s.el); return keep; });
  }
  let seamRaf = null;
  function drawSeams(){
    seamRaf = null;
    if (reduce.matches || designMode) return;
    const vh = innerHeight;
    seams.forEach(s => {
      if (!s.on) return;
      const rect = s.el.getBoundingClientRect();
      const d = clamp((vh - rect.top) / (vh * 0.6 + rect.height), 0, 1);
      if (Math.abs(d - s.d) > 0.004 || (d === 1 && s.d !== 1)){ s.d = d; s.el.style.setProperty('--d', d.toFixed(3)); }
    });
  }
  addEventListener('scroll', () => { if (seamRaf === null) seamRaf = requestAnimationFrame(drawSeams); }, { passive: true });

  /* ---------- the one interactive moment: press the pin, then turn ----------
     Back (counter-clockwise) for hot, forward (clockwise) for sparkling. Drag the knob, tap the
     settings underneath, or use the arrow keys; Reset turns it home and lets the pin spring up.
     Button turns are eased tweens; a drag follows the finger smoothly and springs into its detent. */
  function initKnob(root){
    const dialWrap = root.querySelector('#dialWrap');
    const dial = root.querySelector('#dial');
    const safetyCopy = root.querySelector('#safetyCopy');
    if (!dialWrap || !dial || !safetyCopy) return;
    const doneLine = safetyCopy.querySelector('.dial-done');
    const hint = safetyCopy.querySelector('.hint');
    const ctrlBtns = [...root.querySelectorAll('.dial-controls .dc')];
    const resetBtn = root.querySelector('.dial-controls .reset');
    const btnFor = v => ctrlBtns.find(b => b.dataset.set === String(v));
    const inds = { '-1': dialWrap.querySelector('.ind-hot'), '1': dialWrap.querySelector('.ind-spark') };
    // each sentence of the result line appears in turn
    const words = s => (s || '').split(/(?<=\.)\s+/).filter(Boolean);
    const LINES = { '-1': words(safetyCopy.dataset.hot), '1': words(safetyCopy.dataset.spark) };
    const NAMES = { '-1': btnFor(-1)?.textContent.trim() || 'Hot', '0': safetyCopy.dataset.off || 'Off', '1': btnFor(1)?.textContent.trim() || 'Sparkling' };
    const K = { ang: 0, pin: 0 };
    let setting = 0, run = 0, drag = null;

    function drawKnob(){
      const m = Math.min(1, Math.abs(K.ang) / 90), st = dialWrap.style;
      st.setProperty('--ang', K.ang.toFixed(2));
      st.setProperty('--pin', K.pin.toFixed(3));
      st.setProperty('--m', m.toFixed(3));
      st.setProperty('--mh', (K.ang < 0 ? m : 0).toFixed(3));
      st.setProperty('--ms', (K.ang > 0 ? m : 0).toFixed(3));
      st.setProperty('--dir', K.ang < 0 ? '-1' : '1');
    }
    // cubic-bezier easing, solved numerically, for a soft start and a long glide into the detent
    function bezier(x1, y1, x2, y2){
      const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
      const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
      const X = t => ((ax * t + bx) * t + cx) * t, Y = t => ((ay * t + by) * t + cy) * t, dX = t => (3 * ax * t + 2 * bx) * t + cx;
      return x => {
        let t = x;
        for (let i = 0; i < 6; i++){ const d = dX(t); if (Math.abs(d) < 1e-6) break; t -= (X(t) - x) / d; }
        return Y(clamp(t, 0, 1));
      };
    }
    const EASE_TURN = bezier(0.62, 0.02, 0.3, 1);
    const EASE_PRESS = t => 1 - Math.pow(1 - t, 3);
    const EASE_RISE = t => { const c = 1.35; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };

    // one tween per property, so the pin and the turn can overlap
    const tw = {};
    function stopKey(key){ const a = tw[key]; if (!a) return; tw[key] = null; cancelAnimationFrame(a.raf); a.settle(false); }
    function animateKey(key, to, ms, ease, delay){
      stopKey(key);
      return new Promise(settle => {
        if (reduce.matches || ms <= 0){ K[key] = to; drawKnob(); settle(true); return; }
        const from = K[key], t0 = performance.now() + (delay || 0);
        const a = tw[key] = { raf: 0, settle };
        const step = now => {
          if (tw[key] !== a) return;
          const t = clamp((now - t0) / ms, 0, 1);
          K[key] = from + (to - from) * ease(t);
          drawKnob();
          if (t < 1) a.raf = requestAnimationFrame(step); else { tw[key] = null; settle(true); }
        };
        a.raf = requestAnimationFrame(step);
      });
    }
    // a gently under-damped spring for the angle, carrying the velocity of a flick
    let springId = 0;
    function springAngle(target, v0){
      stopKey('ang');
      const id = ++springId;
      return new Promise(settle => {
        if (reduce.matches){ K.ang = target; drawKnob(); settle(true); return; }
        let x = K.ang, v = v0 || 0, last = performance.now();
        const w = 14, z = 0.82;
        const step = now => {
          if (id !== springId) return settle(false);
          const dt = Math.min(32, now - last) / 1000; last = now;
          v += (-2 * z * w * v - w * w * (x - target)) * dt;
          x += v * dt;
          K.ang = clamp(x, -96, 96);
          drawKnob();
          if (Math.abs(x - target) < 0.05 && Math.abs(v) < 1.5){ K.ang = target; drawKnob(); settle(true); }
          else requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }
    function stopAll(){ springId++; stopKey('ang'); }

    function showSetting(next){
      setting = next;
      dialWrap.classList.toggle('is-hot', next === -1);
      dialWrap.classList.toggle('is-spark', next === 1);
      dial.setAttribute('aria-valuenow', String(next));
      dial.setAttribute('aria-valuetext', NAMES[next]);
      ctrlBtns.forEach(b => b.classList.toggle('on', next !== 0 && +b.dataset.set === next));
      resetBtn.setAttribute('aria-disabled', next === 0 ? 'true' : 'false');
      safetyCopy.classList.remove('done');
      if (next !== 0){
        doneLine.textContent = '';
        LINES[next].forEach(w => { const s = document.createElement('span'); s.className = 'dw'; s.textContent = w; doneLine.appendChild(s); });
        safetyCopy.classList.toggle('res-hot', next === -1);
        safetyCopy.classList.toggle('res-spark', next === 1);
        void doneLine.offsetWidth;   // restart the staged entrance
        safetyCopy.classList.add('done');
        const ind = inds[next];
        ind.classList.remove('pulse'); void ind.offsetWidth; ind.classList.add('pulse');
      }
    }
    // the full sequence: the pin presses, and the turn begins as it bottoms out
    async function goSetting(next){
      const id = ++run;
      stopAll();
      if (next === 0){
        showSetting(0);
        if (!(await animateKey('ang', 0, 420 + Math.abs(K.ang) * 6, EASE_TURN)) || id !== run) return;
        await animateKey('pin', 0, 520, EASE_RISE);
        return;
      }
      if (setting === next && Math.abs(K.ang - 90 * next) < 1) return;
      if (setting !== 0 || Math.abs(K.ang) > 1){
        showSetting(0);
        if (!(await animateKey('ang', 0, 380 + Math.abs(K.ang) * 5, EASE_TURN)) || id !== run) return;
      }
      const wasDown = K.pin > 0.98;
      if (!wasDown) animateKey('pin', 1, 340, EASE_PRESS);
      if (!(await animateKey('ang', 90 * next, 1200, EASE_TURN, wasDown ? 0 : 210)) || id !== run) return;
      showSetting(next);
    }

    const angleAt = (x, y) => {
      const r = dial.getBoundingClientRect();
      return Math.atan2(y - (r.top + r.height / 2), x - (r.left + r.width / 2)) * 180 / Math.PI;
    };
    // while dragging, the knob eases after the finger instead of jumping to it
    function follow(){
      let last = performance.now();
      const step = now => {
        if (!drag) return;
        const dt = Math.min(50, now - last); last = now;
        const prev = K.ang;
        K.ang += (drag.target - K.ang) * (1 - Math.exp(-dt / 55));
        drag.v = drag.v * 0.6 + ((K.ang - prev) / Math.max(1, dt)) * 1000 * 0.4;
        drawKnob();
        requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }
    dial.addEventListener('pointerdown', e => {
      e.preventDefault();
      dial.setPointerCapture?.(e.pointerId);
      run++; stopAll();
      drag = { a0: angleAt(e.clientX, e.clientY), start: K.ang, target: K.ang, v: 0, x: e.clientX, y: e.clientY, moved: false };
      dialWrap.classList.add('grabbing');
      animateKey('pin', 1, 260, EASE_PRESS);
      follow();
    });
    dial.addEventListener('pointermove', e => {
      if (!drag) return;
      if (!drag.moved && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) > 4) drag.moved = true;
      if (!drag.moved) return;
      const d = ((angleAt(e.clientX, e.clientY) - drag.a0 + 540) % 360) - 180;
      drag.target = clamp(drag.start + d, -90, 90);
    });
    function endDrag(){
      if (!drag) return;
      const { moved, v } = drag;
      drag = null;
      dialWrap.classList.remove('grabbing');
      const id = ++run;
      if (!moved){
        // a tap: the pin presses and springs back up, the knob stays where it is
        if (setting === 0){
          hint.classList.remove('nudge'); void hint.offsetWidth; hint.classList.add('nudge');
          animateKey('pin', 1, 140, EASE_PRESS).then(ok => { if (ok && id === run) animateKey('pin', 0, 520, EASE_RISE); });
        } else animateKey('pin', 1, 140, EASE_PRESS);
        return;
      }
      // where the knob would coast to decides the detent, so a quick flick counts
      const coast = K.ang + v * 0.12;
      const next = coast >= 50 ? 1 : coast <= -50 ? -1 : 0;
      if (next === 0){
        showSetting(0);
        springAngle(0, v).then(ok => { if (ok && id === run) animateKey('pin', 0, 520, EASE_RISE); });
      } else {
        springAngle(90 * next, v).then(ok => { if (ok && id === run) showSetting(next); });
      }
    }
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => dial.addEventListener(t, endDrag));
    dial.addEventListener('contextmenu', e => e.preventDefault());
    dial.addEventListener('keydown', e => {
      let next = null;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') next = Math.max(-1, setting - 1);
      else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') next = Math.min(1, setting + 1);
      else if (e.key === 'Escape' || e.key === 'Home') next = 0;
      if (next === null) return;
      e.preventDefault();
      goSetting(next);
    });
    ctrlBtns.forEach(b => b.addEventListener('click', () => {
      if (b.getAttribute('aria-disabled') === 'true') return;
      goSetting(+b.dataset.set);
    }));
    drawKnob();
  }

  /* ---------- product page: the colour slide and picker, then the variant that goes in the cart ---------- */
  function initPicker(root){
    if (!root.querySelector('[data-stage]')) return;
/*FARLESS_PICKER*/
    // the chosen colour (and any other option) decides which variant goes in the cart
    const data = root.querySelector('[data-variants]');
    const form = root.querySelector('form.buy-form');
    if (!data || !form) return;
    const variants = JSON.parse(data.textContent);
    const colourPos = +data.dataset.colourPos;
    const input = form.querySelector('[name="id"]');
    const btn = form.querySelector('[data-add]');
    const price = root.querySelector('[data-price]');
    const selects = [...root.querySelectorAll('select[data-option]')];
    const update = () => {
      const want = [];
      const chosen = root.querySelector('.swatches [aria-checked="true"]');
      if (colourPos >= 0 && chosen) want[colourPos] = chosen.getAttribute('aria-label');
      selects.forEach(s => { want[+s.dataset.option] = s.value; });
      const v = variants.find(x => x.options.every((o, k) => want[k] === undefined || want[k] === o));
      if (!v){ btn.disabled = true; btn.textContent = btn.dataset.labelNone || 'Unavailable'; return; }
      input.value = v.id;
      btn.disabled = !v.available;
      btn.textContent = v.available ? (btn.dataset.labelAdd || 'Add to cart') : (btn.dataset.labelSold || 'Sold out');
      if (price) price.innerHTML = v.price;
      if (!designMode) history.replaceState(history.state, '', `${location.pathname}?variant=${v.id}`);
      // each colour is its own favourite: the heart now saves this one
      const heart = root.querySelector('.buy-actions [data-fav]');
      if (heart){
        const colour = colourPos >= 0 ? v.options[colourPos] : '';
        Object.assign(heart.dataset, { fav: `${heart.dataset.favHandle}:${v.id}`, favVariant: v.id, favUrl: `${heart.dataset.favBase}?variant=${v.id}`, favSub: colour || '' });
        if (v.image) heart.dataset.favImage = v.image;
        heart.setAttribute('aria-label', `${heart.dataset.labelSave || 'Save to favourites'}: ${heart.dataset.favTitle}${colour ? ', ' + colour : ''}`);
        syncFavs();
      }
    };
    if (stage) stage.addEventListener('farless:colour', update);
    selects.forEach(s => s.addEventListener('change', update));
  }

  /* ---------- sections start, and start again when the theme editor reloads them ---------- */
  const running = new Map();
  const heroes = new Map();
  const menus = new Map();
  function start(root){
    stop(root);
    splitWords(root);
    const cleanups = [];
    const hero = initHero(root);
    if (hero){ cleanups.push(hero.destroy); heroes.set(root, hero); }
    const panels = initPanels(root);
    if (panels){ cleanups.push(panels.destroy); menus.set(root, panels); }
    initKnob(root);
    initGallery(root);
    initPicker(root);
    observeEntrances(root);
    syncFavs();
    paintCart();
    addSeams(root);
    watchLoops(root);
    running.set(root, cleanups);
  }
  function stop(root){
    (running.get(root) || []).forEach(f => f());
    running.delete(root);
    heroes.delete(root);
    menus.delete(root);
    removeSeams(root);
  }
  const sectionOf = el => el.closest('.shopify-section') || document.body;
  const sections = [...document.querySelectorAll('.shopify-section')];
  (sections.length ? sections : [document.body]).forEach(start);
  updateNav();

  document.addEventListener('shopify:section:load', e => { start(e.target); updateNav(); });
  document.addEventListener('shopify:section:unload', e => stop(e.target));
  // picking a film point or a question in the editor shows it
  // picking the menu bar, or one of its links, in the editor opens the side menu
  document.addEventListener('shopify:section:select', e => { const m = menus.get(e.target); if (m) m.open('menu', null, true); });
  document.addEventListener('shopify:section:deselect', e => { const m = menus.get(e.target); if (m) m.close(false); });
  document.addEventListener('shopify:block:select', e => {
    const block = e.target;
    const menu = menus.get(sectionOf(block));
    if (menu) menu.open('menu', null, true);
    const hero = heroes.get(sectionOf(block));
    if (hero && block.classList.contains('band')) hero.goTo(hero.indexOf(block), true);
    if (block.tagName === 'DETAILS') block.open = true;
  });
  document.addEventListener('shopify:block:deselect', e => { if (e.target.tagName === 'DETAILS') e.target.open = false; });

  /* ---------- reduced motion, live in both directions ---------- */
  reduce.addEventListener('change', e => {
    if (e.matches){
      seams.forEach(s => { s.d = 1; s.el.style.setProperty('--d', '1'); });
      document.querySelectorAll('[data-in],[data-strike]').forEach(el => el.classList.add('in', 'settled'));
    } else drawSeams();
    heroes.forEach(h => h.reapply());
  });
})();
