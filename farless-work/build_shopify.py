"""Build the Shopify theme add-on from farless/index.html.

Splits the static site into a Shopify layout (head, styles, page chrome) and a section
(the page itself, with a product picker for the buy buttons), rewrites asset paths to
Liquid asset_url, and copies the media into the theme's assets folder with a farless- prefix.

Run from the repo root: python3 farless-work/build_shopify.py
"""
import importlib.util
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'farless' / 'index.html'
OUT = ROOT / 'shopify'

ASSETS = {
    'hero-scrub.mp4': 'farless-hero.mp4',
    'hero-scrub.webm': 'farless-hero.webm',
    'hero-poster.jpg': 'farless-hero-poster.jpg',
    'hero-ending.jpg': 'farless-hero-ending.jpg',
    'design-faucet.jpg': 'farless-design.jpg',
}


def asset(name):
    return "{{ '%s' | asset_url }}" % ASSETS[name]


def must_replace(text, old, new, count=1):
    found = text.count(old)
    assert found == count, f'expected {count} of {old[:60]!r}, found {found}'
    return text.replace(old, new)


src = SRC.read_text(encoding='utf-8')

# the approved product page template: its styles, its slide and picker script, its swatch fills
_spec = importlib.util.spec_from_file_location('product_page', ROOT / 'farless-work' / 'product-page' / 'build.py')
product_page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(product_page)
assert '{{' not in src and '{%' not in src, 'source contains Liquid delimiters'

head = src[src.index('<head>') + len('<head>'):src.index('</head>')]
body = src[src.index('<body>') + len('<body>'):src.index('</body>')]

# ---------- layout: head, styles, page chrome ----------
head = must_replace(head, '<title>Farless | Five waters. One tap.</title>',
                    "{%- if template.name == 'product' -%}\n<title>{{ product.title | escape }} | Farless</title>\n"
                    "{%- else -%}\n<title>Farless | Five waters. One tap.</title>\n{%- endif %}\n"
                    '<link rel="canonical" href="{{ canonical_url }}">')
head = must_replace(head, '<meta name="description" content="Farless is one quiet kitchen tap for boiling, filtered, sparkling, hot and cold water. Far less on your counter.">',
                    "{%- if template.name == 'product' -%}\n"
                    '<meta name="description" content="{{ product.description | strip_html | strip | truncate: 160 | escape }}">\n'
                    "{%- else -%}\n"
                    '<meta name="description" content="Farless is one quiet kitchen tap for boiling, filtered, sparkling, hot and cold water. Far less on your counter.">\n'
                    '{%- endif %}')
head = must_replace(head, '<meta property="og:title" content="Farless | Five waters. One tap.">\n'
                    '<meta property="og:description" content="Boiling, filtered, sparkling, hot and cold water from one quiet tap.">\n'
                    '<meta property="og:type" content="website">',
                    "{%- if template.name == 'product' -%}\n"
                    '<meta property="og:title" content="{{ product.title | escape }} | Farless">\n'
                    '<meta property="og:description" content="{{ product.description | strip_html | strip | truncate: 160 | escape }}">\n'
                    '<meta property="og:type" content="product">\n'
                    "{%- else -%}\n"
                    '<meta property="og:title" content="Farless | Five waters. One tap.">\n'
                    '<meta property="og:description" content="Boiling, filtered, sparkling, hot and cold water from one quiet tap.">\n'
                    '<meta property="og:type" content="website">\n'
                    '{%- endif %}')
head = must_replace(head, '<!-- DEPLOY STEP: patch og:url and og:image with the live absolute URL before zipping -->\n', '')
head = must_replace(head, '<meta property="og:url" content="https://example.com/">',
                    '<meta property="og:url" content="{{ canonical_url }}">')
head = must_replace(head, '<meta property="og:image" content="https://example.com/assets/hero-ending.jpg">',
                    "{%- if template.name == 'product' and product.featured_media -%}\n"
                    '<meta property="og:image" content="https:{{ product.featured_media.preview_image | image_url: width: 1200 }}">\n'
                    "{%- else -%}\n"
                    '<meta property="og:image" content="https:HERO_IMAGE">\n'
                    '{%- endif %}'.replace('HERO_IMAGE', asset('hero-ending.jpg')))
head = must_replace(head, "url('assets/hero-ending.jpg')", "url('%s')" % asset('hero-ending.jpg'))
head = head.rstrip() + '\n{{ content_for_header }}\n'

chrome_end = body.index('<nav class="top"')
chrome = body[:chrome_end].strip()
page = body[chrome_end:]

layout = (
    '<!doctype html>\n<html lang="{{ request.locale.iso_code }}">\n<head>' + head + '</head>\n<body>\n'
    + chrome + '\n{{ content_for_layout }}\n</body>\n</html>\n'
)

# ---------- section: the page, wired to a Shopify product ----------
# the static shop preview is swapped for live Liquid: real product media, stock state and collections
shop_start, shop_end = page.index('  <!-- SHOP:START -->'), page.index('<!-- SHOP:END -->') + len('<!-- SHOP:END -->')
page = page[:shop_start] + (ROOT / 'farless-work' / 'shopify-shop.liquid').read_text(encoding='utf-8').rstrip() + page[shop_end:]
page = must_replace(page, '<img src="assets/design-faucet.jpg"', '<img src="%s"' % asset('design-faucet.jpg'))
page = must_replace(page, '<li class="keep"><a class="buy" href="#buy">Buy</a></li>',
                    '<li class="keep"><a class="buy" href="{{ buy_url }}">Buy</a></li>')
page = must_replace(page, '<a class="btn" href="#buy">Buy Farless</a>', '<a class="btn" href="{{ buy_url }}">Buy Farless</a>', 2)
page = must_replace(page, '      <!-- SHOP LINK: replace href with the Farless online shop URL -->\n', '')
page = must_replace(page, '<a class="btn solid part" href="#buy" data-shop>Buy Farless</a>',
                    '<a class="btn solid part" href="{{ buy_url }}">Buy Farless</a>')
# store policies in the footer (refunds, privacy, terms), as every Shopify storefront should link them
page = must_replace(page, '      <li><span class="label">© Farless</span></li>',
                    '      {%- for policy in shop.policies -%}\n      <li><a class="label" href="{{ policy.url }}">{{ policy.title }}</a></li>\n      {%- endfor -%}\n'
                    '      <li><span class="label">© {{ "now" | date: "%Y" }} Farless</span></li>')

script_start = page.index('<script>')
markup, script = page[:script_start], page[script_start:]
script = must_replace(script, "url: 'assets/hero-scrub.webm'", 'url: FARLESS.webm')
script = must_replace(script, "url: 'assets/hero-scrub.mp4'", 'url: FARLESS.mp4')
script = must_replace(script, "\"url('assets/hero-poster.jpg')\"", '"url(\'" + FARLESS.poster + "\')"')
script = must_replace(script, "img.src = 'assets/hero-poster.jpg';", 'img.src = FARLESS.poster;')
script = must_replace(script, "\"url('assets/hero-ending.jpg')\"", '"url(\'" + FARLESS.ending + "\')"')
assert 'assets/' not in markup + script, 'unrewritten asset path left in the section'

section = (
    "{%- liquid\n"
    "  assign p = section.settings.product\n"
    "  if p == blank\n"
    "    assign buy_url = routes.all_products_collection_url\n"
    "  elsif section.settings.straight_to_checkout\n"
    "    assign buy_url = routes.cart_url | append: '/' | append: p.selected_or_first_available_variant.id | append: ':1'\n"
    "  else\n"
    "    assign buy_url = p.url\n"
    "  endif\n"
    "-%}\n"
    + markup
    + '<script>\n  window.FARLESS = {\n'
    + '    webm: %s,\n' % "{{ 'farless-hero.webm' | asset_url | json }}"
    + '    mp4: %s,\n' % "{{ 'farless-hero.mp4' | asset_url | json }}"
    + '    poster: %s,\n' % "{{ 'farless-hero-poster.jpg' | asset_url | json }}"
    + '    ending: %s\n' % "{{ 'farless-hero-ending.jpg' | asset_url | json }}"
    + '  };\n</script>\n'
    + '{% raw %}\n' + script.strip() + '\n{% endraw %}\n\n'
    + '{% schema %}\n' + json.dumps({
        'name': 'Farless landing',
        'tag': 'div',
        'class': 'farless-landing',
        'settings': [
            {'type': 'product', 'id': 'product', 'label': 'Farless product',
             'info': 'Every Buy Farless button links to this product.'},
            {'type': 'checkbox', 'id': 'straight_to_checkout', 'default': False,
             'label': 'Skip the product page',
             'info': 'Buy buttons put one Farless in the cart and open checkout directly.'},
            {'type': 'header', 'content': 'Shop section'},
            {'type': 'product_list', 'id': 'shop_products', 'label': 'Products to show', 'limit': 8,
             'info': 'Leave empty to feature the Farless product above. Two or more show as a grid.'},
            {'type': 'checkbox', 'id': 'show_prices', 'default': False, 'label': 'Show prices'},
            {'type': 'collection_list', 'id': 'collections', 'label': 'Collections to show', 'limit': 6},
        ],
        'presets': [{'name': 'Farless landing'}],
    }, indent=2) + '\n{% endschema %}\n'
)

template = {'layout': 'farless', 'sections': {'main': {'type': 'farless-landing', 'settings': {}}}, 'order': ['main']}

# ---------- product section: the approved product page, for every product ----------
def home_links(html):
    """The main page's in-page links, pointed at the home page from any other page."""
    html = html.replace('href="#top"', 'href="{{ routes.root_url }}"')
    html = html.replace('href="#buy"', 'href="#buy"')
    return re.sub(r'href="#(?!buy")([a-z]+)"', lambda m: 'href="{{ routes.root_url }}#%s"' % m.group(1), html)


def cut(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i) + len(end)]


product_nav = home_links(cut(src, '<nav class="top"', '</nav>'))
product_footer = home_links(cut(src, '<footer>', '</footer>'))
product_footer = must_replace(product_footer, '      <li><span class="label">© Farless</span></li>',
                              '      {%- for policy in shop.policies -%}\n      <li><a class="label" href="{{ policy.url }}">{{ policy.title }}</a></li>\n      {%- endfor -%}\n'
                              '      <li><span class="label">© {{ "now" | date: "%Y" }} Farless</span></li>')

SWATCH_EXTRA = {
    'white': 'linear-gradient(135deg,#ffffff 0%,#e7e3dd 45%,#f6f3ee 60%,#bdb7ae 100%)',
    'neutral': 'linear-gradient(135deg,#d8d1c7 0%,#8f877c 50%,#5e574f 100%)',
}
product_markup = (ROOT / 'farless-work' / 'shopify-product.liquid').read_text(encoding='utf-8')
for key, fill in {**product_page.SWATCHES, **SWATCH_EXTRA}.items():
    product_markup = product_markup.replace('%%%%SW_%s%%%%' % key.upper(), fill)
assert '%%SW_' not in product_markup, 'a swatch placeholder has no fill'

SHOP_JS = """
  // the chosen colour (and any other option) decides which variant goes in the cart
  const data = document.querySelector('[data-variants]');
  const form = document.querySelector('form.buy-form');
  if (data && form){
    const variants = JSON.parse(data.textContent);
    const colourPos = +data.dataset.colourPos;
    const input = form.querySelector('[name="id"]');
    const btn = form.querySelector('[data-add]');
    const price = document.querySelector('[data-price]');
    const selects = [...document.querySelectorAll('select[data-option]')];
    const update = () => {
      const want = [];
      const chosen = document.querySelector('.swatches [aria-checked="true"]');
      if (colourPos >= 0 && chosen) want[colourPos] = chosen.getAttribute('aria-label');
      selects.forEach(s => { want[+s.dataset.option] = s.value; });
      const v = variants.find(x => x.options.every((o, k) => want[k] === undefined || want[k] === o));
      if (!v){ btn.disabled = true; btn.textContent = 'Unavailable'; return; }
      input.value = v.id;
      btn.disabled = !v.available;
      btn.textContent = v.available ? 'Add to cart' : 'Sold out';
      if (price) price.innerHTML = v.price;
      history.replaceState(history.state, '', `${location.pathname}?variant=${v.id}`);
    };
    if (stage) stage.addEventListener('farless:colour', update);
    selects.forEach(s => s.addEventListener('change', update));
  }
"""
product_script = "(() => {\n  'use strict';\n" + product_page.JS_CORE + SHOP_JS + "})();"
for chunk in (product_page.CSS, product_script):
    assert '{{' not in chunk and '{%' not in chunk, 'Liquid delimiters in a raw chunk'

product_section = (
    '{%- comment -%} Generated by farless-work/build_shopify.py from the product page template. {%- endcomment -%}\n'
    '<style>' + product_page.CSS + '</style>\n'
    + product_nav + '\n\n'
    + product_markup.strip() + '\n\n'
    + product_footer + '\n\n'
    + '<script>\n{% raw %}\n' + product_script + '\n{% endraw %}\n</script>\n\n'
    + '{% schema %}\n' + json.dumps({
        'name': 'Farless product',
        'tag': 'div',
        'class': 'farless-product',
        'settings': [
            {'type': 'text', 'id': 'kicker', 'label': 'Small heading', 'default': 'Farless',
             'info': 'Shown above the product name when the product has no "Small heading" field of its own.'},
            {'type': 'checkbox', 'id': 'show_prices', 'default': False, 'label': 'Show prices'},
        ],
    }, indent=2) + '\n{% endschema %}\n'
)
product_template = {'layout': 'farless', 'sections': {'main': {'type': 'farless-product', 'settings': {}}}, 'order': ['main']}

# ---------- write ----------
if OUT.exists():
    shutil.rmtree(OUT)
for d in ('layout', 'sections', 'templates', 'assets', 'optional-homepage/templates'):
    (OUT / d).mkdir(parents=True, exist_ok=True)
(OUT / 'layout' / 'farless.liquid').write_text(layout, encoding='utf-8')
(OUT / 'sections' / 'farless-landing.liquid').write_text(section, encoding='utf-8')
(OUT / 'sections' / 'farless-product.liquid').write_text(product_section, encoding='utf-8')
(OUT / 'templates' / 'product.json').write_text(json.dumps(product_template, indent=2) + '\n', encoding='utf-8')
(OUT / 'templates' / 'page.farless.json').write_text(json.dumps(template, indent=2) + '\n', encoding='utf-8')
(OUT / 'optional-homepage' / 'templates' / 'index.json').write_text(json.dumps(template, indent=2) + '\n', encoding='utf-8')
for src_name, dst_name in ASSETS.items():
    shutil.copy2(ROOT / 'farless' / 'assets' / src_name, OUT / 'assets' / dst_name)

zip_path = ROOT / 'farless-shopify-addon.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file():
            z.write(f, f.relative_to(OUT))
print('built', OUT, 'and', zip_path)
