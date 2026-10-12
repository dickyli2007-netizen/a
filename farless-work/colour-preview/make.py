"""Build a preview of the colour picker without touching the live page.

Reads farless/index.html, swaps the shop gallery for a horizontal track of finishes with a
colour picker in the info column, and writes:
  farless-work/colour-preview/index.html   full page, for local testing
  farless-work/colour-preview/page.html    the same page without the document shell, for the artifact preview

The finish photos in assets/ are recoloured from the chrome product photo, as stand-ins until real
photos of each finish exist. Run from the repo root: python3 farless-work/colour-preview/make.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
src = (ROOT / 'farless' / 'index.html').read_text(encoding='utf-8')

FINISHES = [
    ('chrome', 'Polished Chrome', 'linear-gradient(135deg,#fbfbfc 0%,#c3c6ca 38%,#eef0f2 56%,#8c9095 100%)'),
    ('brass', 'Satin Brass', 'linear-gradient(135deg,#f6e4b0 0%,#c09a52 40%,#e3c682 58%,#7a5822 100%)'),
    ('copper', 'Warm Copper', 'linear-gradient(135deg,#f4d0bb 0%,#b5714f 40%,#dca184 58%,#6c3822 100%)'),
    ('black', 'Matte Black', 'linear-gradient(135deg,#55514d 0%,#1c1a19 42%,#2c2a28 60%,#0c0b0a 100%)'),
]


def must_replace(text, old, new):
    assert text.count(old) == 1, f'expected one {old[:60]!r}, found {text.count(old)}'
    return text.replace(old, new)


CSS = '''
/* colour picker: the frame is a horizontal track of finishes, the picker sits in the info column */
.f-frame.slides{touch-action:pan-y;cursor:grab;user-select:none;-webkit-user-select:none}
.f-frame.slides.dragging{cursor:grabbing}
.f-track{position:absolute;inset:0;display:flex;transform:translate3d(calc(var(--pos,0) * -100%),0,0);will-change:transform}
.f-slide{position:relative;flex:0 0 100%;height:100%;margin:0;overflow:hidden}
.f-frame.slides img{inset:0 auto 0 -7%;width:114%;max-width:none;translate:calc(var(--d,0) * -6.14%) 0;transition:scale 1.4s var(--ease-out);-webkit-user-drag:none;pointer-events:none}
.f-frame.slides:hover img{transform:none;scale:1.025}
.f-rail{display:flex;align-items:center;gap:22px;margin-top:20px}
.f-rail .bar{position:relative;flex:1;height:1px;background:var(--hair)}
.f-rail .bar i{position:absolute;left:0;top:0;height:1px;width:calc(100% / var(--n,4));background:var(--text-primary);transform:translate3d(calc(var(--pos,0) * 100%),0,0);will-change:transform}
.f-rail .label{flex:none;font-variant-numeric:tabular-nums;letter-spacing:.2em}
.f-rail .label b{font-weight:400;color:var(--text-primary)}
.finish{margin-top:40px;padding-top:30px;border-top:1px solid var(--hair)}
.finish-h{font:400 clamp(1.3rem,1.8vw,1.65rem)/1.25 var(--font);color:var(--text-primary)}
.finish-h span{font-weight:300;color:var(--text-secondary)}
.f-info .finish-name{display:flex;align-items:baseline;gap:14px;margin-top:20px;font:400 1rem/1.4 var(--font);letter-spacing:.02em}
.f-info .finish-name .label{margin:0}
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
/* phones and tablets: name, then the photo with the picker right under it, so both stay in view */
@media (max-width:860px){
  .feature{row-gap:0}
  .f-info{display:contents}
  .f-info > .label{order:0}
  .f-info > h3{order:1;margin-bottom:30px}
  .f-media{order:2}
  .finish{order:3;margin-top:22px;padding-top:0;border-top:0}
  .f-info .excerpt{order:4;margin-top:34px}
  .f-actions{order:5}
  .f-notes{order:6}
}
@media (max-width:600px){
  .f-frame.slides{aspect-ratio:5/6}
  .f-rail{margin-top:16px}
  .finish{margin-top:18px}
  .f-info .finish-name{margin-top:12px}
  .swatches{margin-top:8px}
}
'''

slides = '\n'.join(
    f'              <figure class="f-slide"{"" if i == 0 else " aria-hidden=\"true\""}>'
    f'<img src="assets/finish-{key}.jpg" alt="The Farless 5-in-1 tap in {name.lower()}, with its arched spout and push-and-turn handles" '
    f'width="1319" height="1447" draggable="false" decoding="async"></figure>'
    for i, (key, name, _) in enumerate(FINISHES))

MEDIA = f'''        <div class="f-media part" data-finishes style="--n:{len(FINISHES)}">
          <div class="f-frame slides" aria-roledescription="carousel" aria-label="Farless in {len(FINISHES)} colours">
            <div class="f-track">
{slides}
            </div>
          </div>
          <div class="f-rail" aria-hidden="true"><span class="bar"><i></i></span><span class="label"><b data-count>01</b> / {len(FINISHES):02d}</span></div>
        </div>'''

swatches = '\n'.join(
    f'              <button type="button" role="radio" aria-checked="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" '
    f'aria-label="{name}" style="--sw:{grad}"></button>'
    for i, (_, name, grad) in enumerate(FINISHES))

PICKER = f'''          <div class="finish part" data-finish-picker>
            <p class="finish-h">Colour. <span>Pick your favourite.</span></p>
            <p class="finish-name"><span class="label">Colour</span><b data-finish-name>{FINISHES[0][1]}</b></p>
            <div class="swatches" role="radiogroup" aria-label="Colour">
{swatches}
            </div>
          </div>
'''

JS = '''  /* ---------- colour picker: the frame slides sideways to the chosen finish ---------- */
  document.querySelectorAll('[data-finishes]').forEach(media => {
    const frame = media.querySelector('.f-frame');
    const slides = [...media.querySelectorAll('.f-slide')];
    const picker = media.closest('.feature').querySelector('[data-finish-picker]');
    const radios = [...picker.querySelectorAll('[role="radio"]')];
    const nameEl = picker.querySelector('[data-finish-name]');
    const countEl = media.querySelector('[data-count]');
    const N = slides.length;
    const still = matchMedia('(prefers-reduced-motion: reduce)');
    const easeOut = t => 1 - Math.pow(1 - t, 3);
    let pos = 0, cur = 0, raf = 0, drag = null;

    const draw = () => {
      media.style.setProperty('--pos', pos.toFixed(4));
      slides.forEach((s, i) => s.style.setProperty('--d', clamp(i - pos, -1, 1).toFixed(4)));
    };
    function glide(to, ms, ease){
      cancelAnimationFrame(raf);
      const from = pos, t0 = performance.now();
      if (still.matches || Math.abs(to - from) < 1e-3){ pos = to; draw(); return; }
      const step = now => {
        const p = Math.min(1, (now - t0) / ms);
        pos = from + (to - from) * ease(p);
        draw();
        if (p < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    }
    // the finish name leaves the way the photo leaves and arrives the way the next one arrives
    function rename(i, dir){
      const text = radios[i].getAttribute('aria-label');
      countEl.textContent = String(i + 1).padStart(2, '0');
      if (still.matches || !nameEl.animate){ nameEl.textContent = text; return; }
      nameEl.getAnimations().forEach(a => a.cancel());
      nameEl.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: `translateX(${-dir * 12}px)` }],
        { duration: 180, easing: 'cubic-bezier(.55,0,1,.45)', fill: 'forwards' }).finished.then(() => {
        nameEl.textContent = text;
        nameEl.animate([{ opacity: 0, transform: `translateX(${dir * 12}px)` }, { opacity: 1, transform: 'none' }],
          { duration: 460, easing: 'cubic-bezier(.22,.61,.36,1)', fill: 'forwards' });
      }, () => {});
    }
    function select(i, opts = {}){
      const dir = Math.sign(i - cur) || Math.sign(i - pos) || 1;
      if (i !== cur) rename(i, dir);
      cur = i;
      radios.forEach((r, k) => { r.setAttribute('aria-checked', String(k === i)); r.tabIndex = k === i ? 0 : -1; });
      slides.forEach((s, k) => k === i ? s.removeAttribute('aria-hidden') : s.setAttribute('aria-hidden', 'true'));
      const dist = Math.abs(i - pos);
      if (opts.fling) glide(i, 420 + 160 * Math.min(dist, 2), easeOut);
      else glide(i, 780 + 170 * Math.min(Math.max(dist - 1, 0), 2), easeInOut);
      if (opts.focus) radios[i].focus();
    }

    radios.forEach((r, k) => {
      r.addEventListener('click', () => select(k));
      r.addEventListener('keydown', e => {
        const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (step){ e.preventDefault(); select((cur + step + N) % N, { focus: true }); }
        else if (e.key === 'Home' || e.key === 'End'){ e.preventDefault(); select(e.key === 'Home' ? 0 : N - 1, { focus: true }); }
      });
    });

    // swipe or drag the photo itself: it follows the finger, then settles on the nearest finish
    frame.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      drag = { id: e.pointerId, x: e.clientX, y: e.clientY, p: pos, on: false, v: 0, lx: e.clientX, lt: e.timeStamp };
    });
    frame.addEventListener('pointermove', e => {
      if (!drag || e.pointerId !== drag.id) return;
      if (!drag.on){
        const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)){ drag = null; return; }
        if (Math.abs(dx) < 8) return;
        cancelAnimationFrame(raf);
        Object.assign(drag, { on: true, x: e.clientX, p: pos, lx: e.clientX, lt: e.timeStamp });
        frame.setPointerCapture(e.pointerId);
        frame.classList.add('dragging');
      }
      let p = drag.p - (e.clientX - drag.x) / frame.clientWidth;
      if (p < 0) p *= 0.3;
      else if (p > N - 1) p = N - 1 + (p - (N - 1)) * 0.3;
      pos = p;
      draw();
      const dt = e.timeStamp - drag.lt;
      if (dt > 0) drag.v = 0.7 * ((e.clientX - drag.lx) / dt) + 0.3 * drag.v;
      drag.lx = e.clientX; drag.lt = e.timeStamp;
    });
    const release = e => {
      if (!drag || e.pointerId !== drag.id) return;
      const d = drag;
      drag = null;
      if (!d.on) return;
      frame.classList.remove('dragging');
      const v = e.timeStamp - d.lt > 90 ? 0 : d.v;
      // a quarter of the way is enough to commit, a flick is enough on its own
      const off = pos - cur;
      let to = Math.abs(off) > 0.22 && Math.abs(off) < 1 ? cur + Math.sign(off) : Math.round(pos);
      if (Math.abs(v) > 0.3) to = v < 0 ? Math.floor(pos) + 1 : Math.ceil(pos) - 1;
      select(clamp(to, 0, N - 1), { fling: true });
    };
    frame.addEventListener('pointerup', release);
    frame.addEventListener('pointercancel', release);

    draw();
  });

'''

page = src
page = must_replace(page, '@media (max-width:860px){.feature{grid-template-columns:1fr}}', CSS.strip() + '\n@media (max-width:860px){.feature{grid-template-columns:1fr}}')
m0 = page.index('        <div class="f-media part" data-gallery>')
m1 = page.index('        <div class="f-info">')
page = page[:m0] + MEDIA + '\n' + page[m1:]
page = must_replace(page, '          <div class="f-actions part">\n            <a class="btn" href="#buy">Add to cart</a>',
                    PICKER + '          <div class="f-actions part">\n            <a class="btn" href="#buy">Add to cart</a>')
j0 = page.index('  /* ---------- shop gallery: thumbnails swap the main image ---------- */')
j1 = page.index('  /* ---------- entrances ---------- */')
page = page[:j0] + JS + page[j1:]
assert 'data-gallery' not in page

(HERE / 'index.html').write_text(page, encoding='utf-8')

# artifact copy: the host supplies the document shell
art = page[page.index('<head>') + len('<head>'):]
art = art.replace('</head>\n<body>', '', 1).replace('</body>\n</html>', '', 1)
for tag in ('<meta charset="utf-8">\n', '<meta name="viewport" content="width=device-width, initial-scale=1">\n'):
    art = art.replace(tag, '', 1)
art = must_replace(art, '<title>Farless | Five waters. One tap.</title>', '<title>Farless Colour Preview</title>')
(HERE / 'page.html').write_text(art.lstrip(), encoding='utf-8')
print('wrote', HERE / 'index.html', 'and', HERE / 'page.html')
