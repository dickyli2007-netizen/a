// The editable theme against today's static page: same words, same look, same behaviour.
const { chromium, devices } = require(process.env.PLAYWRIGHT || 'playwright');
const { PNG } = (() => { try { return require('pngjs'); } catch { return {}; } })();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const SHOTS = __dirname + '/shots';
require('fs').mkdirSync(SHOTS, { recursive: true });
const STATIC = 'http://localhost:8090/', THEME = 'http://localhost:8083/';

const textOf = p => p.evaluate(() => {
  const t = sel => [...document.querySelectorAll(sel)].map(e => (e.getAttribute('aria-label') || e.textContent).replace(/\s+/g, ' ').trim());
  return {
    nav: t('nav.top a'), bands: t('.band'), dots: t('.dots button'), still: t('.static-hero .sh-copy'), note: t('.hero-note'),
    waters: t('#waters .head, #waters .swap'), safety: t('#safety #safetyCopy, #safety .dial-controls'), knob: t('#dial'),
    design: t('#design'), faq: t('#questions'), final: t('#buy'), seams: document.querySelectorAll('.seam').length,
    ids: [...document.querySelectorAll('section[id]')].map(s => s.id),
  };
});
const heroState = p => p.evaluate(() => ({ point: +document.getElementById('stage').dataset.point, on: [...document.querySelectorAll('.band')].findIndex(b => b.classList.contains('on')),
  ready: document.getElementById('stage').classList.contains('video-ready'), t: +document.getElementById('hero').currentTime.toFixed(1), y: Math.round(scrollY),
  panx: getComputedStyle(document.querySelector('.pan')).getPropertyValue('--panx').trim() }));
(async () => {
  const b = await chromium.launch(); const out = {};
  const open = async (url, opts) => {
    const c = await b.newContext(opts || { viewport: { width: 1440, height: 900 } }); const p = await c.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'load' });
    await p.waitForFunction(() => /video-(ready|failed)/.test(document.getElementById('stage')?.className || ''), null, { timeout: 25000 }).catch(() => {});
    await sleep(1200);
    return { c, p, errs };
  };
  // 1. same words in every section except the shop (real product data there) and the footer (policies, year)
  {
    const s = await open(STATIC), t = await open(THEME);
    const a = await textOf(s.p), z = await textOf(t.p);
    out.textDiff = Object.keys(a).filter(k => JSON.stringify(a[k]) !== JSON.stringify(z[k])).map(k => ({ k, static: a[k], theme: z[k] }));
    // 2. the hero steps the same way, wheel by wheel
    const steps = async p => { await p.mouse.move(700, 450); const r = [await heroState(p)]; for (let i = 0; i < 4; i++){ await p.mouse.wheel(0, 100); await sleep(3000); r.push(await heroState(p)); } return r; };
    out.heroStatic = await steps(s.p); out.heroTheme = await steps(t.p);
    // 3. same look, section by section, after the film
    out.pixels = {};
    for (const [name, sel] of [['waters', '#waters'], ['safety', '#safety'], ['design', '#design'], ['faq', '#questions'], ['final', '#buy']]) {
      for (const [pp, tag] of [[s.p, 'static'], [t.p, 'theme']]) {
        await pp.evaluate(q => { document.querySelector(q).scrollIntoView({ block: 'start' }); }, sel); await sleep(2200);
        await pp.locator(sel).screenshot({ path: `${SHOTS}/${name}-${tag}.png` });
      }
    }
    out.errsStatic = s.errs; out.errsTheme = t.errs;
    await s.c.close(); await t.c.close();
  }
  // 4. the knob works in the theme
  {
    const t = await open(THEME);
    await t.p.evaluate(() => document.getElementById('safety').scrollIntoView({ block: 'center' })); await sleep(1500);
    await t.p.click('.dial-controls [data-set="-1"]'); await sleep(2200);
    const hot = await t.p.evaluate(() => ({ cls: document.getElementById('dialWrap').className, val: document.getElementById('dial').getAttribute('aria-valuetext'), words: document.querySelector('.dial-done').textContent, ang: document.getElementById('dialWrap').style.getPropertyValue('--ang') }));
    await t.p.click('.dial-controls [data-set="1"]'); await sleep(3000);
    const spark = await t.p.evaluate(() => ({ cls: document.getElementById('dialWrap').className, val: document.getElementById('dial').getAttribute('aria-valuetext'), words: document.querySelector('.dial-done').textContent, ang: document.getElementById('dialWrap').style.getPropertyValue('--ang') }));
    await t.p.click('.dial-controls .reset'); await sleep(2200);
    const reset = await t.p.evaluate(() => ({ val: document.getElementById('dial').getAttribute('aria-valuetext'), ang: document.getElementById('dialWrap').style.getPropertyValue('--ang') }));
    out.knob = { hot, spark, reset, errs: t.errs };
    await t.c.close();
  }
  // 5. phones: the film pans and steps on swipes
  {
    const t = await open(THEME, { ...devices['iPhone 13'] });
    const cdp = await t.c.newCDPSession(t.p);
    const swipe = async dy => { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 190, y: 600 }] }); for (let i = 1; i <= 8; i++){ await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 190, y: 600 - dy * i / 8 }] }); await sleep(16); } await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); };
    const r = [await heroState(t.p)];
    for (let i = 0; i < 4; i++){ await swipe(160); await sleep(3000); r.push(await heroState(t.p)); }
    out.phone = { steps: r, errs: t.errs, overflow: await t.p.evaluate(() => document.documentElement.scrollWidth - innerWidth) };
    await t.c.close();
  }
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
