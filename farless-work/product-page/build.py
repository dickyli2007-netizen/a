"""The Farless product page template: every product gets a page built from this one design.

Takes the head, styles, nav and footer from farless/index.html and builds a product page around
them, after Gessi's: the product cut out on its own on the page, sliding sideways to the chosen
colour, with only its name, the colour picker and the button in the column beside it, and the
details (tagline, description, notes) below. The colour picker lives on product pages only; the
main page keeps its shop section as it is.

Each product is one file in products/<handle>.json (see products/faucet.json), with its cut-out
images in assets/<handle>/ (make them with cutout.py). A product with one colour gets the same
page without the picker.

Run from the repo root:
  python3 farless-work/product-page/build.py            every product
  python3 farless-work/product-page/build.py faucet     one product

Writes, per product:
  farless-work/product-page/pages/<handle>/index.html   full page, for local testing (serve it with assets/<handle> as assets/)
  farless-work/product-page/pages/<handle>/page.html    the same page without the document shell, for the artifact preview
The bar's side menu, search and favourites come from the main page too, so their pictures (the
menu-* and search-* files in farless/assets, listed in PANEL_ASSETS) go into assets/ beside the
product's own.
"""
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
SITE = 'https://claude.ai/artifact/VUaaH6Je53dopSGLQ8Hors'   # the published site preview the nav links back to
src = (ROOT / 'farless' / 'index.html').read_text(encoding='utf-8')

# swatch fills for the finishes we have used; a product file can give its own "swatch" instead
SWATCHES = {
    'chrome': 'linear-gradient(135deg,#fbfbfc 0%,#c3c6ca 38%,#eef0f2 56%,#8c9095 100%)',
    'brass': 'linear-gradient(135deg,#f6e4b0 0%,#c09a52 40%,#e3c682 58%,#7a5822 100%)',
    'copper': 'linear-gradient(135deg,#f4d0bb 0%,#b5714f 40%,#dca184 58%,#6c3822 100%)',
    'black': 'linear-gradient(135deg,#5b5651 0%,#1c1a19 42%,#2e2b29 60%,#0c0b0a 100%)',
}


def cut(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i) + len(end)]


def link_home(html):
    # in-page anchors of the main site point back to the published site preview
    html = html.replace('href="#top"', f'href="{SITE}"')
    return re.sub(r'href="#([a-z]+)"', lambda m: f'href="{SITE}#{m.group(1)}"', html)


head = src[src.index('<head>') + len('<head>'):src.index('</head>')]
nav = link_home(cut(src, '<nav class="top"', '</nav>'))
footer = link_home(cut(src, '<footer>', '</footer>'))
# the bar's side menu, search sheet and favourites, with their script, so the bar works on the preview too;
# their pictures are the main page's (farless/assets: PANEL_ASSETS), published beside the product's
panels = link_home(src[src.index('<div class="menu-scrim"'):src.index('\n\n<header>')]).replace('"url": "#shop"', f'"url": "{SITE}#shop"')
PANEL_ASSETS = sorted(set(re.findall(r'assets/((?:menu|search)-[\w.-]+)', panels)))
JS_PANELS = src[src.index('  /* ---------- favourites:'):src.index('  initPanels(document.body);\n') + len('  initPanels(document.body);\n')]
HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.3s-7.4-4.5-9.1-9.1C1.7 7.8 3.9 4.6 7.3 4.6c2 0 3.5 1 4.7 2.7 1.2-1.7 2.7-2.7 4.7-2.7 3.4 0 5.6 3.2 4.4 6.6-1.7 4.6-9.1 9.1-9.1 9.1z"/></svg>'

CSS = '''
/* ---------- product page, after Gessi's: the product alone with its name, colour and button beside it; the details below ---------- */
.pdp{padding:calc(118px + env(safe-area-inset-top, 0px)) var(--gutter) clamp(96px,13vh,150px)}
.crumbs{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:clamp(20px,3vh,36px)}
.crumbs a{text-decoration:none;color:var(--text-secondary);transition:color .35s var(--ease-out)}
.crumbs a:hover{color:var(--text-primary)}
.crumbs [aria-current]{color:var(--text-primary)}
.pdp-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:clamp(40px,6vw,110px);align-items:center}
.stage-col{min-width:0}
.stage{position:relative;height:min(72vh,760px);min-height:420px;touch-action:pan-y;cursor:grab;user-select:none;-webkit-user-select:none;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 9%,#000 91%,transparent);mask-image:linear-gradient(90deg,transparent,#000 9%,#000 91%,transparent)}
.stage.dragging{cursor:grabbing}
/* a soft warm light behind the tap, so dark finishes still read against the page */
.stage::before{content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(46% 42% at 50% 52%,rgba(236,227,214,.085),rgba(236,227,214,0) 72%)}
.tap{position:absolute;inset:0;margin:0;will-change:transform,opacity;backface-visibility:hidden}
.tap:not(.is-on){opacity:0}
.stage.single{cursor:auto}
.tap .obj{position:absolute;left:50%;bottom:6%;height:86%;max-width:100%;aspect-ratio:var(--ar);translate:-50% 0}
.tap img{display:block;width:100%;height:100%;max-width:none;object-fit:contain;-webkit-user-drag:none;pointer-events:none}
/* contact shadow under the product's foot; each product file says where its foot is */
.tap .obj::after{content:"";position:absolute;z-index:-1;left:var(--shadow-x,50%);top:98.4%;width:var(--shadow-w,34%);height:5%;translate:-50% -50%;background:radial-gradient(closest-side,rgba(4,3,2,.8),rgba(4,3,2,0))}
.f-rail{display:flex;align-items:center;gap:22px;margin-top:18px}
.f-rail .bar{position:relative;flex:1;height:1px;background:var(--hair)}
.f-rail .bar i{position:absolute;left:0;top:0;height:1px;width:calc(100% / var(--n,4));background:var(--text-primary);transform:translate3d(calc(var(--pos,0) * 100%),0,0);transition:transform 1.05s cubic-bezier(.45,0,.15,1)}
.f-rail.live .bar i{transition:none}
.f-rail .label{flex:none;font-variant-numeric:tabular-nums;letter-spacing:.2em}
.f-rail .label b{font-weight:400;color:var(--text-primary)}
/* beside the product only its name, the colour and the button, so the eye stays on the piece */
.buy-col{min-width:0;max-width:440px}
.buy-col h1{font:200 clamp(2.2rem,3.3vw,3.3rem)/1.08 var(--font);letter-spacing:-.005em}
.buy-col .price{margin-top:16px;font:300 1.15rem/1 var(--font);letter-spacing:.06em}
.finish{margin-top:clamp(34px,6vh,60px)}
.finish-h{font:400 clamp(1.3rem,1.8vw,1.65rem)/1.25 var(--font);color:var(--text-primary)}
.finish-h span{font-weight:300;color:var(--text-secondary)}
.finish-name{display:flex;align-items:baseline;gap:14px;margin-top:20px;font:400 1rem/1.4 var(--font);letter-spacing:.02em}
.finish-name b{display:inline-block;font-weight:400}
.swatches{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0 -7px}
.swatches button{all:unset;box-sizing:border-box;position:relative;width:48px;height:48px;border-radius:50%;cursor:pointer;-webkit-tap-highlight-color:transparent}
.swatches button::before{content:"";position:absolute;inset:7px;border-radius:50%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(255,255,255,.14),inset 0 -5px 9px rgba(0,0,0,.22);transition:transform .5s var(--ease-out)}
.swatches button::after{content:"";position:absolute;inset:2px;border-radius:50%;border:1px solid var(--text-primary);opacity:0;transform:scale(.86);transition:opacity .45s var(--ease-out),transform .55s var(--ease-out),border-color .3s var(--ease-out)}
.swatches button:hover::after{opacity:.35;transform:none}
.swatches button[aria-checked="true"]::after{opacity:1;transform:none}
.swatches button:active::before{transform:scale(.94)}
.swatches button:focus-visible{outline:none}
.swatches button:focus-visible::after{opacity:1;transform:none;border-color:var(--accent)}
.opts{display:grid;gap:14px;margin-top:30px}
.opt{display:grid;gap:10px}
.opt select{font:300 1rem/1.4 var(--font);color:var(--text-primary);background:transparent;border:1px solid var(--hair-strong);padding:12px 14px;border-radius:0}
.opt select:focus-visible{outline:1px solid var(--accent);outline-offset:3px}
.buy-actions{display:grid;gap:14px;margin-top:clamp(32px,5vh,48px)}
.buy-actions form{display:grid;gap:14px;margin:0}
.buy-actions .btn{justify-content:center;cursor:pointer;font-family:var(--font)}
.buy-note{grid-column:1 / -1;min-height:1.6em;color:var(--text-secondary);font-size:.92rem;line-height:1.6}
/* the details, below the product: the tagline large, the description beside it, the notes across */
.pdp-more{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);column-gap:clamp(40px,6vw,110px);margin-top:clamp(72px,11vh,130px);padding-top:clamp(56px,8vh,88px);border-top:1px solid var(--hair)}
.more-head{display:contents}
.more-head .label{grid-column:1 / -1}
.more-head h2{min-width:0;font:200 clamp(2rem,3.4vw,3.2rem)/1.12 var(--font);letter-spacing:-.005em;max-width:18ch}
.more-copy{grid-column:2;min-width:0;max-width:440px;color:var(--text-secondary);line-height:1.75;padding-top:6px}
.more-copy > * + *{margin-top:1em}
.more-copy ul,.more-copy ol{padding-left:1.1em}
.more-copy li + li{margin-top:.45em}
.more-copy strong,.more-copy b{font-weight:400;color:var(--text-primary)}
.more-copy a{color:var(--text-primary)}
.pdp-more .f-notes{grid-column:1 / -1;margin-top:clamp(48px,7vh,72px)}
@media (max-width:860px){
  .pdp{padding-top:calc(94px + env(safe-area-inset-top, 0px))}
  .crumbs{display:none}
  .pdp-grid{grid-template-columns:1fr;row-gap:0}
  .buy-col{display:contents}
  .buy-col h1{order:1}
  .buy-col .price{order:2;margin-top:8px}
  .stage-col{order:3;margin-top:4px}
  .stage{height:min(50vh,520px);min-height:280px}
  .finish{order:4;margin-top:20px}
  .opts{order:4}
  .buy-actions{order:5;margin-top:28px}
  .pdp-more{grid-template-columns:1fr;margin-top:72px;padding-top:48px}
  .more-copy{grid-column:auto;max-width:none;margin-top:24px;padding-top:0}
}
@media (max-width:600px){
  .pdp{padding-top:calc(84px + env(safe-area-inset-top, 0px))}
  .stage{height:min(44vh,440px);min-height:260px}
  .f-rail{margin-top:12px}
  .finish-name{margin-top:12px}
  .swatches{margin-top:8px}
  .buy-actions{margin-top:22px}
}
'''

def render_main(prod, w, h):
    """The page body for one product. Text from the product file is escaped; the layout is fixed."""
    e = lambda t: html.escape(t, quote=True)
    fins = prod['finishes']
    n = len(fins)
    title = prod['title']
    shadow = prod.get('shadow', {})
    stage_vars = f'--ar:{w}/{h};--shadow-x:{shadow.get("x", 50)}%;--shadow-w:{shadow.get("width", 34)}%'
    taps = '\n'.join(
        f'          <figure class="tap{" is-on" if i == 0 else ""}"{"" if i == 0 else " aria-hidden=\"true\""}><div class="obj">'
        f'<img src="assets/{e(f["image"])}" alt="The {e(title)} in {e(f["name"].lower())}" width="{w}" height="{h}" draggable="false"></div></figure>'
        for i, f in enumerate(fins))
    swatches = '\n'.join(
        f'            <button type="button" role="radio" aria-checked="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" '
        f'aria-label="{e(f["name"])}" style="--sw:{f.get("swatch") or SWATCHES[f["key"]]}"></button>'
        for i, f in enumerate(fins))
    picker = (
        '        <div class="finish">\n'
        '          <p class="finish-h">Colour. <span>Pick your favourite.</span></p>\n'
        f'          <p class="finish-name"><span class="label">Colour</span><b data-finish-name>{e(fins[0]["name"])}</b></p>\n'
        '          <div class="swatches" role="radiogroup" aria-label="Colour">\n'
        f'{swatches}\n'
        '          </div>\n'
        '        </div>\n'
    ) if n > 1 else ''
    rail = (f'        <div class="f-rail" aria-hidden="true"><span class="bar"><i></i></span>'
            f'<span class="label"><b data-count>01</b> / {n:02d}</span></div>\n') if n > 1 else ''
    stage_attrs = f'aria-roledescription="carousel" aria-label="{e(title)} in {n} colours"' if n > 1 else f'aria-label="{e(title)}"'
    notes = '\n'.join(f'        <li><span class="label">{e(k)}</span>{e(v)}</li>' for k, v in prod.get('notes', []))
    notes = f'      <ul class="f-notes">\n{notes}\n      </ul>\n' if notes else ''
    crumb = f'<a href="{SITE}#shop">{e(prod["collection"])}</a><span aria-hidden="true">/</span>' if prod.get('collection') else ''
    # the details sit below the product: the small heading and tagline, the description, the notes
    lede = prod.get('lede', '')
    more_head = (
        '      <div class="more-head">\n'
        f'        <span class="label kicker">{e(prod.get("kicker", "Farless"))}</span>\n'
        + (f'        <h2>{e(lede)}</h2>\n' if lede else '')
        + '      </div>\n')
    more_copy = f'      <div class="more-copy"><p>{e(prod["description"])}</p></div>\n' if prod.get('description') else ''
    # each colour is its own favourite, as in the store; the heart follows the picker
    slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    f0 = fins[0]
    heart = (f'          <button type="button" class="fav big" data-fav="{e(prod["handle"])}:{slug(f0["name"])}" data-fav-handle="{e(prod["handle"])}" '
             f'data-fav-variant="{slug(f0["name"])}" data-fav-title="{e(title)}" data-fav-url="{e(prod.get("preview", {}).get("url", "#"))}" '
             f'data-fav-image="assets/{e(f0["image"])}" data-fav-sub="{e(f0["name"])}" aria-pressed="false" '
             f'aria-label="Save to favourites: {e(title)}, {e(f0["name"])}">{HEART}</button>\n')
    colours = json.dumps([{'key': slug(f['name']), 'name': f['name'], 'image': f'assets/{f["image"]}'} for f in fins])
    more = (
        f'    <section class="pdp-more" aria-label="{e(title)}: details">\n'
        f'{more_head}{more_copy}{notes}'
        '    </section>\n'
    ) if lede or more_copy or notes else ''
    return (
        '<main id="main" class="pdp" tabindex="-1">\n'
        '  <div class="wrap">\n'
        f'    <nav class="crumbs label" aria-label="Breadcrumb"><a href="{SITE}#shop">Shop</a><span aria-hidden="true">/</span>{crumb}<span aria-current="page">{e(title)}</span></nav>\n'
        '    <div class="pdp-grid">\n'
        f'      <div class="stage-col" style="--n:{n}">\n'
        f'        <div class="stage{"" if n > 1 else " single"}" data-stage style="{stage_vars}" {stage_attrs}>\n'
        f'{taps}\n'
        '        </div>\n'
        f'{rail}'
        '      </div>\n'
        '      <div class="buy-col">\n'
        f'        <h1>{e(title)}</h1>\n'
        f'{picker}'
        '        <div class="buy-actions has-fav">\n'
        f'          <button class="btn solid" type="button" data-add data-title="{e(title)}">Add to cart</button>\n'
        f'{heart}'
        '          <p class="buy-note" data-buy-note aria-live="polite"></p>\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>\n'
        f'{more}'
        '  </div>\n'
        f'  <script type="application/json" data-colours>{colours.replace("<", "\\u003c")}</script>\n'
        '</main>'
    )

# The slide and the picker, shared by the preview and the Shopify theme (assets/farless.js wraps it
# in a function per product section). It needs clamp() and a root element to look inside, and fires
# a 'farless:colour' event on the stage at each change of colour for the page-specific part.
JS_PICKER = '''  /* ---------- colour picker: the tap slides sideways to the chosen colour ---------- */
  const stage = root.querySelector('[data-stage]');
  const taps = stage ? [...stage.querySelectorAll('.tap')] : [];
  const radios = [...root.querySelectorAll('.swatches [role="radio"]')];
  const nameEl = root.querySelector('[data-finish-name]');
  const countEl = root.querySelector('[data-count]');
  const rail = root.querySelector('.f-rail');
  const N = taps.length;
  const SHIFT = 55;                                   // how far a tap travels, in % of the stage width
  const MOVE = 'cubic-bezier(.45,0,.15,1)';            // eases off the mark, long soft landing
  const SETTLE = 'cubic-bezier(.22,.61,.36,1)';       // after a swipe the tap is already moving
  const still = matchMedia('(prefers-reduced-motion: reduce)');
  let cur = stage ? clamp(+stage.dataset.start || 0, 0, Math.max(N - 1, 0)) : 0, drag = null;

  if (N > 1){   // one colour: no picker, nothing to slide

  // only transform and opacity change, so the browser slides the taps on the compositor
  function place(el, d, opacity){
    const dc = clamp(d, -1, 1);
    el.style.transform = `translate3d(${(dc * SHIFT).toFixed(3)}%,0,0) scale(${(1 - 0.05 * Math.abs(dc)).toFixed(4)})`;
    el.style.opacity = opacity.toFixed(3);
  }
  function rename(i, dir){
    const text = radios[i].getAttribute('aria-label');
    countEl.textContent = String(i + 1).padStart(2, '0');
    if (still.matches || !nameEl.animate){ nameEl.textContent = text; return; }
    nameEl.getAnimations().forEach(a => a.cancel());
    nameEl.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: `translateX(${-dir * 12}px)` }],
      { duration: 200, easing: 'cubic-bezier(.55,0,1,.45)', fill: 'forwards' }).finished.then(() => {
      nameEl.textContent = text;
      nameEl.animate([{ opacity: 0, transform: `translateX(${dir * 12}px)` }, { opacity: 1, transform: 'none' }],
        { duration: 520, easing: 'cubic-bezier(.22,.61,.36,1)', fill: 'forwards' });
    }, () => {});
  }
  function show(i, opts = {}){
    const dir = Math.sign(i - cur) || 1;
    if (i !== cur) rename(i, dir);
    cur = i;
    const fling = !!opts.fling;
    taps.forEach((el, k) => {
      if (still.matches) el.style.transition = 'none';
      else if (k === i) el.style.transition = fling
        ? `transform .75s ${SETTLE}, opacity .55s ${SETTLE}`
        : `transform 1.05s ${MOVE}, opacity .75s cubic-bezier(.25,.1,.25,1) .15s`;
      else el.style.transition = fling
        ? `transform .75s ${SETTLE}, opacity .4s ${SETTLE}`
        : `transform 1.05s ${MOVE}, opacity .45s cubic-bezier(.5,0,.9,.6)`;
      place(el, k - i, k === i ? 1 : 0);
      if (k === i) el.removeAttribute('aria-hidden'); else el.setAttribute('aria-hidden', 'true');
    });
    rail.classList.toggle('live', still.matches);
    rail.style.setProperty('--pos', String(i));
    radios.forEach((r, k) => { r.setAttribute('aria-checked', String(k === i)); r.tabIndex = k === i ? 0 : -1; });
    if (opts.focus) radios[i].focus();
    stage.dispatchEvent(new CustomEvent('farless:colour', { detail: { index: i } }));
  }

  radios.forEach((r, k) => {
    r.addEventListener('click', () => show(k));
    r.addEventListener('keydown', e => {
      const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (step){ e.preventDefault(); show((cur + step + N) % N, { focus: true }); }
      else if (e.key === 'Home' || e.key === 'End'){ e.preventDefault(); show(e.key === 'Home' ? 0 : N - 1, { focus: true }); }
    });
  });

  // swipe or drag the tap itself: it follows the finger, then settles on the nearest colour
  stage.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, p: cur, on: false, v: 0, lx: e.clientX, lt: e.timeStamp };
  });
  stage.addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id) return;
    if (!drag.on){
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)){ drag = null; return; }
      if (Math.abs(dx) < 8) return;
      Object.assign(drag, { on: true, x: e.clientX, lx: e.clientX, lt: e.timeStamp });
      stage.setPointerCapture(e.pointerId);
      stage.classList.add('dragging');
      rail.classList.add('live');
      taps.forEach(el => { el.style.transition = 'none'; });
    }
    let p = cur - (e.clientX - drag.x) / (stage.clientWidth * SHIFT / 100);
    if (p < 0) p *= 0.3;
    else if (p > N - 1) p = N - 1 + (p - (N - 1)) * 0.3;
    drag.p = p;
    taps.forEach((el, k) => place(el, k - p, clamp(1 - Math.abs(k - p) * 1.4, 0, 1)));
    rail.style.setProperty('--pos', p.toFixed(4));
    const dt = e.timeStamp - drag.lt;
    if (dt > 0) drag.v = 0.7 * ((e.clientX - drag.lx) / dt) + 0.3 * drag.v;
    drag.lx = e.clientX; drag.lt = e.timeStamp;
  });
  const release = e => {
    if (!drag || e.pointerId !== drag.id) return;
    const d = drag;
    drag = null;
    if (!d.on) return;
    stage.classList.remove('dragging');
    const v = e.timeStamp - d.lt > 90 ? 0 : d.v;
    const off = d.p - cur;
    // a quarter of the way is enough to commit, a flick is enough on its own
    let to = Math.abs(off) > 0.22 && Math.abs(off) < 1 ? cur + Math.sign(off) : Math.round(d.p);
    if (Math.abs(v) > 0.3) to = v < 0 ? Math.floor(d.p) + 1 : Math.ceil(d.p) - 1;
    show(clamp(to, 0, N - 1), { fling: true });
  };
  stage.addEventListener('pointerup', release);
  stage.addEventListener('pointercancel', release);

  taps.forEach((el, k) => { el.style.transition = 'none'; place(el, k - cur, k === cur ? 1 : 0); });
  }
'''

PREVIEW_JS = '''
  // preview only: there is no store behind this page
  const add = document.querySelector('[data-add]'), note = document.querySelector('[data-buy-note]');
  add.addEventListener('click', () => {
    const chosen = document.querySelector('.swatches [aria-checked="true"]');
    note.textContent = `Preview only. In the shop this adds the ${add.dataset.title}${chosen ? ` in ${chosen.getAttribute('aria-label')}` : ''} to the cart.`;
  });
  const heart = document.querySelector('.buy-actions [data-fav]');
  const colours = JSON.parse(document.querySelector('[data-colours]').textContent);
  if (stage) stage.addEventListener('farless:colour', e => {
    note.textContent = '';
    const c = colours[e.detail.index];
    Object.assign(heart.dataset, { fav: `${heart.dataset.favHandle}:${c.key}`, favVariant: c.key, favImage: c.image, favSub: c.name });
    heart.setAttribute('aria-label', `Save to favourites: ${heart.dataset.favTitle}, ${c.name}`);
    syncFavs();
  });
'''

JS_PREVIEW_HEAD = '''  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const root = document;
  const nav = document.querySelector('nav.top');
  const onScroll = () => nav.classList.toggle('solid', scrollY > 8);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

'''

JS = "<script>\n(() => {\n  'use strict';\n" + JS_PREVIEW_HEAD + JS_PANELS + '\n' + JS_PICKER + PREVIEW_JS + "})();\n</script>"


def build(prod):
    handle = prod['handle']
    assets = HERE / 'assets' / handle
    with Image.open(assets / prod['finishes'][0]['image']) as im:
        w, h = im.size
    for f in prod['finishes']:
        assert (assets / f['image']).is_file(), f'missing {assets / f["image"]}'
        assert f.get('swatch') or f['key'] in SWATCHES, f'no swatch for {f["key"]}: add "swatch" to the product file'
    body = '\n'.join([
        '<a class="skip" href="#main">Skip to content</a>',
        '<div class="env" aria-hidden="true"></div>',
        '<div class="grain" aria-hidden="true"></div>',
        '', nav, panels, '', render_main(prod, w, h), '', footer, '', JS,
    ])
    title = f'{prod["title"]} | Farless'
    style_end = head.rindex('</style>')
    page_head = head[:style_end] + CSS.lstrip('\n') + head[style_end:]
    page_head = page_head.replace('<title>Farless | Five waters. One tap.</title>', f'<title>{html.escape(title)}</title>', 1)
    assert f'<title>{html.escape(title)}</title>' in page_head
    out = HERE / 'pages' / handle
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text('<!doctype html>\n<html lang="en">\n<head>' + page_head + '</head>\n<body>\n' + body + '\n</body>\n</html>\n', encoding='utf-8')
    # artifact copy: the host supplies the document shell
    art = page_head
    for tag in ('<meta charset="utf-8">\n', '<meta name="viewport" content="width=device-width, initial-scale=1">\n'):
        art = art.replace(tag, '', 1)
    preview_title = prod.get('preview', {}).get('title', prod['title'])
    art = art.replace(f'<title>{html.escape(title)}</title>', f'<title>{html.escape(preview_title)}</title>', 1)
    (out / 'page.html').write_text(art.lstrip() + '\n' + body + '\n', encoding='utf-8')
    print('built', out)


if __name__ == '__main__':
    wanted = sys.argv[1:]
    files = [HERE / 'products' / f'{h}.json' for h in wanted] if wanted else sorted((HERE / 'products').glob('*.json'))
    for path in files:
        build(json.loads(path.read_text(encoding='utf-8')))
