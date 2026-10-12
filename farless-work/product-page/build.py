"""The Farless product page template: every product gets a page built from this one design.

Takes the head, styles, nav and footer from farless/index.html and builds a product page around
them: the product cut out on its own on the page, sliding sideways to the chosen colour, with the
colour picker in the column beside it. The colour picker lives on product pages only; the main
page keeps its shop section as it is.

Each product is one file in products/<handle>.json (see products/faucet.json), with its cut-out
images in assets/<handle>/ (make them with cutout.py). A product with one colour gets the same
page without the picker.

Run from the repo root:
  python3 farless-work/product-page/build.py            every product
  python3 farless-work/product-page/build.py faucet     one product

Writes, per product:
  farless-work/product-page/pages/<handle>/index.html   full page, for local testing (serve it with assets/<handle> as assets/)
  farless-work/product-page/pages/<handle>/page.html    the same page without the document shell, for the artifact preview
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

CSS = '''
/* ---------- product page: the tap alone on the page, the choice beside it ---------- */
.pdp{padding:calc(118px + env(safe-area-inset-top, 0px)) var(--gutter) clamp(96px,13vh,150px)}
.crumbs{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:clamp(20px,3vh,36px)}
.crumbs a{text-decoration:none;color:var(--text-secondary);transition:color .35s var(--ease-out)}
.crumbs a:hover{color:var(--text-primary)}
.crumbs [aria-current]{color:var(--text-primary)}
.pdp-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:clamp(40px,6vw,110px);align-items:start}
.stage-col{position:sticky;top:92px;min-width:0}
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
.buy-col{min-width:0;padding-top:clamp(0px,3vh,40px)}
.buy-col h1{font:200 clamp(2.4rem,4vw,3.9rem)/1.06 var(--font);letter-spacing:-.005em;margin-top:22px}
.buy-col .lede{margin-top:14px;color:var(--text-secondary);font-size:1.12rem}
.finish{margin-top:40px;padding-top:30px;border-top:1px solid var(--hair)}
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
.buy-actions{display:grid;gap:14px;margin-top:34px}
.buy-actions form{display:grid;gap:14px;margin:0}
.buy-col .price{margin-top:18px;font:300 1.15rem/1 var(--font);letter-spacing:.06em}
.buy-col .excerpt p + p{margin-top:1em}
.buy-actions .btn{justify-content:center;cursor:pointer;font-family:var(--font)}
.buy-note{min-height:1.6em;color:var(--text-secondary);font-size:.92rem;line-height:1.6}
.buy-col .excerpt{margin-top:40px;color:var(--text-secondary);max-width:46ch}
.buy-col .f-notes{margin-top:36px}
@media (max-width:860px){
  .pdp{padding-top:calc(94px + env(safe-area-inset-top, 0px))}
  .crumbs{display:none}
  .pdp-grid{grid-template-columns:1fr;row-gap:0}
  .buy-col{display:contents}
  .buy-col > .label{order:0}
  .buy-col h1{order:1;margin-top:12px}
  .buy-col .lede{order:2;margin-top:6px}
  .stage-col{order:3;position:static;margin-top:4px}
  .stage{height:min(50vh,520px);min-height:280px}
  .finish{order:4;margin-top:20px;padding-top:0;border-top:0}
  .buy-actions{order:5;margin-top:28px}
  .buy-col .excerpt{order:6;margin-top:36px}
  .buy-col .f-notes{order:7}
}
@media (max-width:600px){
  .pdp{padding-top:calc(84px + env(safe-area-inset-top, 0px))}
  .buy-col > .label{display:none}
  .buy-col h1{margin-top:0}
  .stage{height:min(44vh,440px);min-height:260px}
  .f-rail{margin-top:12px}
  .finish-name{margin-top:12px}
  .swatches{margin-top:8px}
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
    notes = '\n'.join(f'          <li><span class="label">{e(k)}</span>{e(v)}</li>' for k, v in prod.get('notes', []))
    notes = f'        <ul class="f-notes">\n{notes}\n        </ul>\n' if notes else ''
    crumb = f'<a href="{SITE}#shop">{e(prod["collection"])}</a><span aria-hidden="true">/</span>' if prod.get('collection') else ''
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
        f'        <span class="label">{e(prod.get("kicker", "Farless"))}</span>\n'
        f'        <h1>{e(title)}</h1>\n'
        f'        <p class="lede">{e(prod.get("lede", ""))}</p>\n'
        f'{picker}'
        '        <div class="buy-actions">\n'
        f'          <button class="btn solid" type="button" data-add data-title="{e(title)}">Add to cart</button>\n'
        '          <p class="buy-note" data-buy-note aria-live="polite"></p>\n'
        '        </div>\n'
        f'        <p class="excerpt">{e(prod.get("description", ""))}</p>\n'
        f'{notes}'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
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
  if (stage) stage.addEventListener('farless:colour', () => { note.textContent = ''; });
'''

JS_PREVIEW_HEAD = '''  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const root = document;
  const nav = document.querySelector('nav.top');
  const onScroll = () => nav.classList.toggle('solid', scrollY > 8);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

'''

JS = "<script>\n(() => {\n  'use strict';\n" + JS_PREVIEW_HEAD + JS_PICKER + PREVIEW_JS + "})();\n</script>"


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
        '', nav, '', render_main(prod, w, h), '', footer, '', JS,
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
