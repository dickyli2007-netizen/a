// The theme's cart against a stand-in for Shopify's Ajax cart API (cart.js, cart/add.js, change.js, update.js):
// Add to cart opens the cart, quantities change, an unticked piece stays out of checkout and comes back into the
// cart afterwards (when the shopper returns without buying, and after the order), a sold-out piece says so, the
// home page's shop section adds too, the cart page draws, and the panel fits a phone.
//   node render.js, serve site/ on 8083 (see render.js), then: node cart-test.js
const { chromium, devices } = require('playwright');
const BASE = 'http://localhost:8083';
// the page's sample shows Matte Black as sold out; here it can be added, and 109 stands for a sold-out piece
const VARIANTS = { 101: ['Brushed Nickel', true], 102: ['Matte Black', true], 109: ['Brushed Nickel', false] };
let cart = [];   // [{ key, variant_id, quantity, properties }]
const line = l => ({ key: l.key, variant_id: l.variant_id, quantity: l.quantity, properties: l.properties || {}, product_title: 'Farless 5-in-1 Tap',
  variant_title: VARIANTS[l.variant_id][0], image: `${BASE}/img/tap-${VARIANTS[l.variant_id][0].split(' ')[1].toLowerCase()}.webp`, url: `/products/faucet?variant=${l.variant_id}`, final_line_price: 89999 * l.quantity });
const json = () => ({ item_count: cart.reduce((s, l) => s + l.quantity, 0), items: cart.map(line) });
function add(id, q){
  if (!VARIANTS[id] || !VARIANTS[id][1]) return null;
  let l = cart.find(x => x.variant_id === +id);
  if (l) l.quantity += q; else { l = { key: `${id}:k`, variant_id: +id, quantity: q }; cart.unshift(l); }
  return line(l);
}
async function mock(ctx){
  await ctx.addInitScript(() => { window.Shopify = { routes: { root: '/' } }; });
  await ctx.route('**/cart.js', r => r.fulfill({ json: json() }));
  await ctx.route('**/cart/add.js', r => {
    const req = r.request(), body = req.postData() || '';
    if ((req.headers()['content-type'] || '').includes('json')){
      const items = JSON.parse(body).items, out = [];
      for (const it of items){ if (!VARIANTS[it.id][1]) return r.fulfill({ status: 422, json: { status: 422, description: 'Sold out' } }); }
      for (const it of items) out.push(add(it.id, it.quantity));
      return r.fulfill({ json: { items: out } });
    }
    const id = (body.match(/name="id"\r\n\r\n(\d+)/) || [])[1];
    const added = add(id, 1);
    return added ? r.fulfill({ json: added }) : r.fulfill({ status: 422, json: { status: 422, description: 'This tap is sold out.' } });
  });
  await ctx.route('**/cart/change.js', r => { const { id, quantity } = JSON.parse(r.request().postData()); const l = cart.find(x => x.key === id); if (l) l.quantity = quantity; cart = cart.filter(x => x.quantity > 0); r.fulfill({ json: json() }); });
  await ctx.route('**/cart/update.js', r => { const { updates } = JSON.parse(r.request().postData()); for (const [k, q] of Object.entries(updates)){ const l = cart.find(x => x.key === k); if (l) l.quantity = q; } cart = cart.filter(x => x.quantity > 0); r.fulfill({ json: json() }); });
  await ctx.route('**/checkout', r => r.fulfill({ contentType: 'text/html', body: `<title>checkout</title><p id="co">${cart.map(l => VARIANTS[l.variant_id][0] + ' x' + l.quantity).join(', ')}</p>` }));
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await mock(ctx);
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error' && !/422|Failed to load resource/.test(m.text())) errs.push(m.text()); });
  const st = () => p.evaluate(() => ({ open: !!document.querySelector('.cart-panel.open'), count: document.querySelector('[data-cart-count]').hidden ? 0 : +document.querySelector('[data-cart-count]').textContent,
    lines: [...document.querySelectorAll('.cart-panel .ct-line')].map(l => `${l.querySelector('.ct-sub').textContent} x${l.querySelector('.ct-n').textContent}${l.querySelector('[data-ct-pick]').checked ? '' : ' (unticked)'}`),
    msg: document.querySelector('.cart-panel [data-ct-msg]')?.textContent || '', url: location.pathname }));
  const out = {};
  await p.goto(BASE + '/products/faucet/', { waitUntil: 'networkidle' });
  await p.evaluate(() => localStorage.clear());
  out.start = await st();
  await p.click('form.buy-form [data-add]'); await sleep(1200);
  out.addedNickel = await st();
  await p.screenshot({ path: __dirname + '/shots/cart-1.png' });
  await p.keyboard.press('Escape'); await sleep(900);
  await p.locator('.swatches [role=radio]').nth(1).click(); await sleep(1300);
  await p.evaluate(() => { document.querySelector('form.buy-form [data-add]').disabled = false; });
  await p.click('form.buy-form [data-add]'); await sleep(1200);
  out.addedBlack = await st();
  await p.click('.cart-panel .ct-line:nth-child(1) [data-step="1"]'); await sleep(500);
  out.blackPlus = await st();
  // untick the nickel, check out the black only
  await p.click('.cart-panel .ct-line:nth-child(2) .ct-pick'); await sleep(300);
  out.untickedNickel = await st();
  await Promise.all([p.waitForURL('**/checkout'), p.click('.cart-panel [data-ct-go]')]);
  out.checkoutPage = await p.textContent('#co');
  out.held = await p.evaluate(() => localStorage.getItem('farless:cart-held'));
  // the shopper comes back without buying: everything is in the cart again, the nickel still unticked
  await p.goto(BASE + '/products/faucet/', { waitUntil: 'networkidle' }); await sleep(800);
  await p.click('[data-open="cart"]'); await sleep(1000);
  out.backWithoutBuying = await st();
  out.heldAfter = await p.evaluate(() => localStorage.getItem('farless:cart-held'));
  // check out the black again, and this time the order goes through: Shopify empties the cart
  await Promise.all([p.waitForURL('**/checkout'), p.click('.cart-panel [data-ct-go]')]);
  out.checkoutAgain = await p.textContent('#co');
  cart = [];
  await p.goto(BASE + '/products/faucet/', { waitUntil: 'networkidle' }); await sleep(800);
  await p.click('[data-open="cart"]'); await sleep(1000);
  out.afterOrder = await st();
  await p.screenshot({ path: __dirname + '/shots/cart-2.png' });
  // a sold-out colour says so in the cart
  await p.keyboard.press('Escape'); await sleep(900);
  await p.evaluate(() => { const f = document.querySelector('form.buy-form'); f.querySelector('[name=id]').value = '109'; f.querySelector('[data-add]').disabled = false; });
  await p.click('form.buy-form [data-add]'); await sleep(1200);
  out.soldOut = await st();
  // the home page's shop section adds without leaving the page too
  await p.goto(BASE + '/', { waitUntil: 'networkidle' }); await sleep(600);
  const shopBtn = p.locator('#shop form button[type=submit]').first();
  out.shopForm = await shopBtn.count();
  if (out.shopForm){ await shopBtn.scrollIntoViewIfNeeded(); await shopBtn.click(); await sleep(1200); out.shopAdd = await st(); }
  // the cart page
  await p.goto(BASE + '/cart/', { waitUntil: 'networkidle' }); await sleep(800);
  out.cartPage = await p.evaluate(() => ({ lines: [...document.querySelectorAll('.cart-page .ct-line')].map(l => l.querySelector('.ct-sub').textContent + ' ' + (l.querySelector('[data-ct-pick]')?.checked)), go: document.querySelector('.cart-page [data-ct-go]')?.textContent }));
  await p.screenshot({ path: __dirname + '/shots/cart-cart-page.png', fullPage: true });
  out.errs = errs;
  // phone: the panel fits, nothing spills sideways
  const ph = await b.newContext({ ...devices['iPhone 13'] }); await mock(ph);
  const q = await ph.newPage(); await q.goto(BASE + '/products/faucet/', { waitUntil: 'networkidle' });
  await q.click('[data-open="cart"]'); await sleep(1000);
  out.phone = await q.evaluate(() => { const go = document.querySelector('.cart-panel [data-ct-go]').getBoundingClientRect(); return { goBottom: Math.round(go.bottom), vh: innerHeight, overflow: document.documentElement.scrollWidth - innerWidth }; });
  await q.screenshot({ path: __dirname + '/shots/cart-phone.png' });
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
