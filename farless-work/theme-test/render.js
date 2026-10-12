// Renders the Farless theme the way Shopify does: JSON templates, section groups, schema defaults,
// block markers and section wrappers, with sample store data, into site/ for the tests.
//   cd farless-work/theme-test && npm install && node render.js
//   npx http-server site -p 8083     (and, for parity.js, npx http-server ../../farless -p 8090)
//   node parity.js       the theme against the static page: words, look, film, knob, phone
//   node editor-test.js  edited content, theme editor events, section reloads, links, product page
const fs = require('fs');
const path = require('path');
const { Liquid, Tag } = require('liquidjs');
const REPO = path.resolve(__dirname, '../..');
const THEME = path.join(REPO, 'shopify');
const OUT = path.join(__dirname, 'site');

const engine = new Liquid({ root: [path.join(THEME, 'snippets')], extname: '.liquid', strictFilters: true, dynamicPartials: true });
const kw = args => { const o = {}; for (const a of args) if (Array.isArray(a) && a.length === 2 && typeof a[0] === 'string') o[a[0]] = a[1]; return o; };
class Img { constructor(img, width){ this.img = img; this.width = width; } toString(){ return `${this.img.src}?width=${this.width}`; } }
engine.registerFilter('image_url', (img, ...args) => new Img(img, kw(args).width || img.width));
engine.registerFilter('image_tag', (u, ...args) => {
  const o = kw(args); const extra = Object.entries(o).filter(([k]) => !['widths', 'sizes'].includes(k)).map(([k, v]) => ` ${k}="${String(v).replace(/"/g, '&quot;')}"`).join('');
  const srcset = o.widths ? ` srcset="${String(o.widths).split(',').map(w => `${u.img.src}?width=${w.trim()} ${w.trim()}w`).join(', ')}"` : '';
  return `<img src="${u}"${srcset}${o.sizes ? ` sizes="${o.sizes}"` : ''} width="${u.img.width}" height="${u.img.height}"${extra}>`;
});
engine.registerFilter('money', c => `$${(c / 100).toFixed(2)}`);
engine.registerFilter('json', v => JSON.stringify(v));
engine.registerFilter('asset_url', n => `/cdn/${n}`);
engine.registerFilter('handleize', s => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
class FormTag extends Tag {
  constructor(token, remain, liquid){
    super(token, remain, liquid); this.args = token.args; this.tpls = [];
    while (remain.length){ const t = remain.shift(); if (t.name === 'endform') return; this.tpls.push(liquid.parser.parseToken(t, remain)); }
    throw new Error('form not closed');
  }
  * render(ctx, emitter){
    const cls = (this.args.match(/class:\s*'([^']*)'/) || [])[1] || '';
    emitter.write(`<form method="post" action="/cart/add" accept-charset="UTF-8"${cls ? ` class="${cls}"` : ''} enctype="multipart/form-data"><input type="hidden" name="form_type" value="product">`);
    yield this.liquid.renderer.renderTemplates(this.tpls, ctx, emitter);
    emitter.write('</form>');
  }
}
engine.registerTag('form', FormTag);
class SchemaTag extends Tag {
  constructor(token, remain, liquid){ super(token, remain, liquid); while (remain.length){ if (remain.shift().name === 'endschema') break; } }
  * render(){}
}
engine.registerTag('schema', SchemaTag);

// ---------- sample store ----------
const img = (name, w, h, alt) => ({ src: `/img/${name}`, width: w, height: h, aspect_ratio: +(w / h).toFixed(4), alt });
const media = (id, image) => ({ id, alt: image.alt, preview_image: image });
const photo = media(1, img('photo.jpg', 1200, 1608, 'The Farless 5-in-1 tap in polished chrome'));
const design = media(2, img('design.jpg', 880, 1080, 'A hand pushing and turning the Farless handle'));
const ending = media(3, img('ending.jpg', 1920, 1080, 'Sparkling water pouring'));
const desc = fs.readFileSync(path.join(__dirname, 'description.html'), 'utf8');
const COLOURS = [['Polished Chrome', 'chrome', true], ['Satin Brass', 'brass', false], ['Warm Copper', 'copper', true], ['Matte Black', 'black', true]];
const variants = COLOURS.map(([n, key, av], i) => ({ id: 101 + i, title: n, options: [n], available: av, price: 89999, featured_media: media(11 + i, img(`tap-${key}.webp`, 924, 1416, '')) }));
const sel = variants[0];
const faucet = {
  id: 9, title: 'Farless 5-in-1 Tap', handle: 'faucet', url: '/products/faucet', description: desc, featured_media: photo,
  media: [photo, design, ending, ...variants.map(v => v.featured_media)], variants, available: true, price: 89999,
  options_with_values: [{ name: 'Colour', position: 1, values: COLOURS.map(([n]) => ({ name: n, selected: n === sel.options[0], swatch: null })) }],
  has_only_default_variant: false, selected_or_first_available_variant: sel,
  collections: [{ handle: 'frontpage', title: 'Home page', url: '/collections/frontpage' }, { handle: 'multi-function-faucets', title: 'Multi Function Faucets', url: '/collections/multi-function-faucets' }],
  metafields: { farless: { kicker: { value: 'The tap' }, lede: { value: 'Five waters. One tap.' }, foot_x: { value: 33.3 },
    notes: { value: 'Five waters | Boiling, filtered, sparkling, hot and cold.\r\nPush and turn | Boiling only when you mean it.\r\n5-year warranty | On every Farless.' } } },
};
const COLLECTIONS = {
  'multi-function-faucets': { title: 'Multi Function Faucets', url: '/collections/multi-function-faucets', products_count: 1, featured_image: null, products: [faucet] },
  'filtered-faucets': { title: 'Filtered Faucets', url: '/collections/filtered-faucets', products_count: 0, featured_image: null, products: [] },
};
const PRODUCTS = { faucet };

const globals = { routes: { root_url: '/', cart_url: '/cart', all_products_collection_url: '/collections/all', collections_url: '/collections' },
  shop: { name: 'Farless', policies: [{ title: 'Refund policy', url: '/policies/refund-policy' }] }, request: { locale: { iso_code: 'en' } }, content_for_header: '' };
// Shopify's global objects are visible inside rendered snippets too
engine.options.globals = { routes: globals.routes, shop: globals.shop, request: globals.request };

// ---------- sections the Shopify way ----------
const schemaOf = file => JSON.parse(file.match(/{% schema %}([\s\S]*?){% endschema %}/)[1]);
function resolve(def, value){
  if (value === undefined) value = def.default;
  if (value === undefined || value === '') return def.type === 'checkbox' ? false : null;
  switch (def.type){
    case 'product': return PRODUCTS[value] || null;
    case 'product_list': return (value || []).map(h => PRODUCTS[h]).filter(Boolean);
    case 'collection_list': return (value || []).map(h => COLLECTIONS[h]).filter(Boolean);
    case 'url': return String(value).replace(/^shopify:\/\/products\//, '/products/').replace(/^shopify:\/\/collections\//, '/collections/');
    default: return value;
  }
}
const settingsFrom = (defs, saved) => { const o = {}; (defs || []).forEach(d => { if (d.id) o[d.id] = resolve(d, (saved || {})[d.id]); }); return o; };
async function renderSection(type, id, data, scope, groupId){
  const file = fs.readFileSync(path.join(THEME, 'sections', `${type}.liquid`), 'utf8');
  const schema = schemaOf(file);
  const blocks = (data.block_order || []).map(bid => {
    const b = data.blocks[bid];
    const def = schema.blocks.find(x => x.type === b.type);
    return { id: bid, type: b.type, settings: settingsFrom(def.settings, b.settings), shopify_attributes: `data-shopify-editor-block='${JSON.stringify({ id: bid, type: b.type })}'` };
  });
  const section = { id, settings: settingsFrom(schema.settings, data.settings), blocks };
  const html = await engine.parseAndRender(file, { ...globals, ...scope, section });
  const tag = schema.tag || 'div';
  return `<${tag} id="shopify-section-${groupId}__${id}" class="shopify-section ${schema.class || ''}">${html}</${tag}>`;
}
async function renderJson(file, scope, groupId){
  const json = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\/\*[\s\S]*?\*\//, ''));
  let out = '';
  for (const id of json.order) out += await renderSection(json.sections[id].type, id, json.sections[id], scope, groupId);
  return out;
}
class SectionsTag extends Tag {
  constructor(token, remain, liquid){ super(token, remain, liquid); this.name = token.args.trim().replace(/['"]/g, ''); }
  async render(ctx, emitter){
    emitter.write(await renderJson(path.join(THEME, 'sections', `${this.name}.json`), ctx.getAll(), `sections--${this.name}`));
  }
}
engine.registerTag('sections', SectionsTag);

async function page(file, templateFile, template, scope, designMode){
  const body = await renderJson(templateFile, { ...scope, template }, 'template--1');
  const layout = fs.readFileSync(path.join(THEME, 'layout', 'farless.liquid'), 'utf8');
  let html = await engine.parseAndRender(layout, { ...globals, ...scope, template, canonical_url: 'https://farless.example/', page_title: scope.page_title || 'Farless', page_description: scope.page_description, content_for_layout: body });
  if (designMode) html = html.replace('<head>', '<head><script>window.Shopify={designMode:true}</script>');
  fs.mkdirSync(path.dirname(path.join(OUT, file)), { recursive: true });
  fs.writeFileSync(path.join(OUT, file), html);
}
(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(path.join(OUT, 'img'), { recursive: true });
  fs.mkdirSync(path.join(OUT, 'cdn'), { recursive: true });
  for (const k of ['chrome', 'brass', 'copper', 'black']) fs.copyFileSync(`${REPO}/farless-work/product-page/assets/faucet/tap-${k}.webp`, `${OUT}/img/tap-${k}.webp`);
  fs.copyFileSync(`${REPO}/farless/assets/product-1.jpg`, `${OUT}/img/photo.jpg`);
  fs.copyFileSync(`${REPO}/farless/assets/design-faucet.jpg`, `${OUT}/img/design.jpg`);
  fs.copyFileSync(`${REPO}/farless/assets/hero-ending.jpg`, `${OUT}/img/ending.jpg`);
  for (const f of fs.readdirSync(`${THEME}/assets`)) fs.copyFileSync(`${THEME}/assets/${f}`, `${OUT}/cdn/${f}`);
  const T = n => path.join(THEME, 'templates', n);
  await page('index.html', T('index.json'), { name: 'index', suffix: null }, {});
  await page('design/index.html', T('index.json'), { name: 'index', suffix: null }, {}, true);
  await page('products/faucet/index.html', T('product.json'), { name: 'product', suffix: null }, { product: faucet, page_title: 'Farless 5-in-1 Tap', page_description: 'Five waters. One tap.' });
  // the owner's edits: new words, a question added, a water row removed, sections reordered, a picture link
  const edited = JSON.parse(fs.readFileSync(T('index.json'), 'utf8'));
  edited.sections.hero.blocks.caption_2.settings.line = 'Boiling. Filtered. Edited.';
  edited.sections.waters.settings.heading = 'Edited heading.';
  delete edited.sections.waters.blocks.row_3; edited.sections.waters.block_order = edited.sections.waters.block_order.filter(b => b !== 'row_3');
  edited.sections.questions.blocks.question_5 = { type: 'question', settings: { question: 'Can I add my own question?', answer: '<p>Yes, from the theme editor.</p>' } };
  edited.sections.questions.block_order.push('question_5');
  edited.sections.safety.settings.result_hot = 'Push. Twist back. Hot water.';
  edited.order = ['hero', 'waters', 'shop', 'safety', 'design', 'questions', 'final'];
  fs.writeFileSync(path.join(__dirname, 'edited.json'), JSON.stringify(edited));
  await page('edited/index.html', path.join(__dirname, 'edited.json'), { name: 'index', suffix: null }, {});
  console.log('rendered home, design mode, product, edited home');
})().catch(e => { console.error(e); process.exit(1); });
