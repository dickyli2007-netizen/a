// Editing in the theme editor: edited content renders, editor events work, reloaded sections start again.
const { chromium, devices } = require(process.env.PLAYWRIGHT || 'playwright');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = 'http://localhost:8083';
(async () => {
  const b = await chromium.launch(); const out = {};
  const open = async (path, opts) => {
    const c = await b.newContext(opts || { viewport: { width: 1440, height: 900 } }); const p = await c.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(BASE + path, { waitUntil: 'load' });
    await p.waitForFunction(() => !document.getElementById('stage') || /video-(ready|failed)/.test(document.getElementById('stage').className), null, { timeout: 25000 }).catch(() => {});
    await sleep(1000);
    return { c, p, errs };
  };
  const point = p => p.evaluate(() => +document.getElementById('stage').dataset.point);
  { // the owner's edits show up
    const { c, p, errs } = await open('/edited/');
    out.edited = await p.evaluate(() => ({
      caption2: document.querySelectorAll('.band')[1].getAttribute('aria-label') || document.querySelectorAll('.band')[1].textContent.trim(),
      watersHeading: document.querySelector('#waters h2').textContent, rows: document.querySelectorAll('.swaps li').length,
      questions: [...document.querySelectorAll('#questions summary')].map(s => s.textContent.trim()),
      order: [...document.querySelectorAll('section[id]')].map(s => s.id),
      shopOrder: [...document.querySelector('#shop .wrap').children].map(e => e.className.split(' ')[0]),
      hotData: document.getElementById('safetyCopy').dataset.hot,
    }));
    await p.evaluate(() => document.getElementById('safety').scrollIntoView({ block: 'center' })); await sleep(1200);
    await p.click('.dial-controls [data-set="-1"]'); await sleep(2400);
    out.edited.hotWords = await p.evaluate(() => [...document.querySelectorAll('.dial-done .dw')].map(w => w.textContent));
    out.edited.errs = errs; await c.close();
  }
  { // theme editor: everything at rest, blocks selectable, sections reload cleanly
    const { c, p, errs } = await open('/design/');
    const r = {};
    r.allIn = await p.evaluate(() => [...document.querySelectorAll('[data-in],[data-strike]')].every(e => e.classList.contains('in')));
    r.seamsDrawn = await p.evaluate(() => [...document.querySelectorAll('.seam')].map(s => s.style.getPropertyValue('--d')));
    // pick the fourth film point in the sidebar
    await p.evaluate(() => { const band = document.querySelectorAll('.band')[3]; band.dispatchEvent(new CustomEvent('shopify:block:select', { bubbles: true, detail: { blockId: 'caption_4', sectionId: 'hero', load: false } })); });
    await sleep(800); r.afterSelect = await point(p);
    // pick a question: it opens; deselect closes it
    await p.evaluate(() => { const d = document.querySelectorAll('#questions details')[2]; d.dispatchEvent(new CustomEvent('shopify:block:select', { bubbles: true })); });
    r.qOpen = await p.evaluate(() => document.querySelectorAll('#questions details')[2].open);
    await p.evaluate(() => { const d = document.querySelectorAll('#questions details')[2]; d.dispatchEvent(new CustomEvent('shopify:block:deselect', { bubbles: true })); });
    r.qClosed = !(await p.evaluate(() => document.querySelectorAll('#questions details')[2].open));
    // the editor reloads the hero after an edit: unload, swap the markup, load
    await p.evaluate(() => {
      const sec = document.getElementById('stage').closest('.shopify-section');
      sec.dispatchEvent(new CustomEvent('shopify:section:unload', { bubbles: true }));
      const html = sec.innerHTML.replace('Boiling. Filtered.', 'Boiling. Filtered. Edited.');
      const fresh = document.createElement('div'); fresh.id = sec.id; fresh.className = sec.className; fresh.innerHTML = html;
      const v = fresh.querySelector('video'); v.removeAttribute('src'); v.removeAttribute('style'); fresh.querySelector('.stage').classList.remove('video-ready', 'video-failed');
      fresh.querySelectorAll('.split').forEach(el => { el.removeAttribute('data-split'); el.textContent = el.getAttribute('aria-label') || el.textContent; });
      sec.replaceWith(fresh);
      fresh.dispatchEvent(new CustomEvent('shopify:section:load', { bubbles: true }));
    });
    await p.waitForFunction(() => /video-(ready|failed)/.test(document.getElementById('stage').className), null, { timeout: 25000 }).catch(() => {});
    await sleep(800);
    await p.evaluate(() => scrollTo(0, 0)); await sleep(300);
    r.reloadStart = await point(p);
    await p.mouse.move(700, 450);
    // one wheel gesture must move exactly one point: old listeners from before the reload would move it twice
    await p.mouse.wheel(0, 100); await sleep(3000); r.reloadAfterOneWheel = await point(p);
    await p.mouse.wheel(0, 100); await sleep(3000); r.reloadAfterTwoWheels = await point(p);
    r.reloadCaption = await p.evaluate(() => document.querySelectorAll('.band')[1].querySelector('.split').getAttribute('aria-label'));
    // reload the safety section: the knob still turns
    await p.evaluate(() => {
      const sec = document.getElementById('dialWrap').closest('.shopify-section');
      sec.dispatchEvent(new CustomEvent('shopify:section:unload', { bubbles: true }));
      const fresh = document.createElement('div'); fresh.id = sec.id; fresh.className = sec.className; fresh.innerHTML = sec.innerHTML;
      sec.replaceWith(fresh);
      fresh.dispatchEvent(new CustomEvent('shopify:section:load', { bubbles: true }));
    });
    await p.evaluate(() => document.getElementById('safety').scrollIntoView({ block: 'center' })); await sleep(800);
    await p.click('.dial-controls [data-set="1"]'); await sleep(2400);
    r.knobAfterReload = await p.evaluate(() => document.getElementById('dial').getAttribute('aria-valuetext'));
    r.errs = errs; out.editor = r; await c.close();
  }
  { // menu and footer links on the home page and on a product page
    const home = await open('/');
    out.linksHome = await home.p.evaluate(() => ({ nav: [...document.querySelectorAll('nav.top a')].map(a => a.getAttribute('href')), footer: [...document.querySelectorAll('footer a, footer span.label')].map(a => a.getAttribute('href') || a.textContent) }));
    await home.c.close();
    const prod = await open('/products/faucet/');
    out.linksProduct = await prod.p.evaluate(() => ({ nav: [...document.querySelectorAll('nav.top a')].map(a => a.getAttribute('href')), title: document.title }));
    // the product page still works: colours, variant, sold out
    const sw = prod.p.locator('.swatches [role=radio]');
    await sw.nth(1).click(); await sleep(1300);
    out.product = await prod.p.evaluate(() => ({ id: document.querySelector('form.buy-form [name=id]').value, btn: document.querySelector('[data-add]').textContent, disabled: document.querySelector('[data-add]').disabled, name: document.querySelector('[data-finish-name]').textContent,
      op: [...document.querySelectorAll('.tap')].map(t => +(+getComputedStyle(t).opacity).toFixed(2)).join(' '), pdpInMain: !!document.querySelector('main#main .pdp'), mains: document.querySelectorAll('main').length }));
    await sw.nth(0).click(); await sleep(1300);
    out.product.nickel = await prod.p.evaluate(() => ({ id: document.querySelector('form.buy-form [name=id]').value, btn: document.querySelector('[data-add]').textContent }));
    out.product.errs = prod.errs;
    await prod.p.screenshot({ path: __dirname + '/shots/product-theme.png' });
    await prod.c.close();
    const phone = await open('/products/faucet/', { ...devices['iPhone 13'] });
    out.productPhone = await phone.p.evaluate(() => ({ swatchBottom: Math.round(document.querySelector('.swatches').getBoundingClientRect().bottom), vh: innerHeight, overflow: document.documentElement.scrollWidth - innerWidth }));
    out.productPhone.errs = phone.errs; await phone.c.close();
  }
  { // the side menu: picking the menu bar or a link in the editor opens it, deselecting closes it; a reloaded bar starts closed
    const { c, p, errs } = await open('/design/');
    const st = () => p.evaluate(() => ({ open: document.documentElement.classList.contains('menu-open'), expanded: document.querySelector('[data-open="menu"]').getAttribute('aria-expanded'), mainInert: !!document.querySelector('main').inert }));
    const header = () => document.querySelector('[data-open="menu"]').closest('.shopify-section');
    await p.evaluate(h => { (0, eval)('(' + h + ')')().dispatchEvent(new CustomEvent('shopify:section:select', { bubbles: true, detail: { load: false } })); }, header.toString());
    await sleep(900); const selected = await st();
    await p.evaluate(h => { (0, eval)('(' + h + ')')().dispatchEvent(new CustomEvent('shopify:section:deselect', { bubbles: true })); }, header.toString());
    await sleep(900); const deselected = await st();
    await p.evaluate(() => document.querySelector('[data-shopify-editor-block*="small_1"]').dispatchEvent(new CustomEvent('shopify:block:select', { bubbles: true })));
    await sleep(900); const blockSelected = await st();
    await p.evaluate(h => { const sec = (0, eval)('(' + h + ')')(); sec.dispatchEvent(new CustomEvent('shopify:section:unload', { bubbles: true }));
      const fresh = sec.cloneNode(true); sec.replaceWith(fresh); fresh.dispatchEvent(new CustomEvent('shopify:section:load', { bubbles: true })); }, header.toString());
    await sleep(700); const reloaded = await st();
    await p.click('[data-open="menu"]'); await sleep(900); const clickedAfterReload = await st();
    out.menu = { selected, deselected, blockSelected, reloaded, clickedAfterReload, errs }; await c.close();
  }
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
