"""Build the Shopify theme add-on from farless/index.html.

Splits the static site into a Shopify layout (head, styles, page chrome) and a section
(the page itself, with a product picker for the buy buttons), rewrites asset paths to
Liquid asset_url, and copies the media into the theme's assets folder with a farless- prefix.

Run from the repo root: python3 farless-work/build_shopify.py
"""
import json
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
assert '{{' not in src and '{%' not in src, 'source contains Liquid delimiters'

head = src[src.index('<head>') + len('<head>'):src.index('</head>')]
body = src[src.index('<body>') + len('<body>'):src.index('</body>')]

# ---------- layout: head, styles, page chrome ----------
head = must_replace(head, '<title>Farless | Five waters. One tap.</title>',
                    '<title>Farless | Five waters. One tap.</title>\n<link rel="canonical" href="{{ canonical_url }}">')
head = must_replace(head, '<!-- DEPLOY STEP: patch og:url and og:image with the live absolute URL before zipping -->\n', '')
head = must_replace(head, '<meta property="og:url" content="https://example.com/">',
                    '<meta property="og:url" content="{{ canonical_url }}">')
head = must_replace(head, '<meta property="og:image" content="https://example.com/assets/hero-ending.jpg">',
                    '<meta property="og:image" content="https:%s">' % asset('hero-ending.jpg'))
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
script = must_replace(script, "const VIDEO_URL = canWebm ? 'assets/hero-scrub.webm' : 'assets/hero-scrub.mp4';",
                      'const VIDEO_URL = canWebm ? FARLESS.webm : FARLESS.mp4;')
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
        ],
        'presets': [{'name': 'Farless landing'}],
    }, indent=2) + '\n{% endschema %}\n'
)

template = {'layout': 'farless', 'sections': {'main': {'type': 'farless-landing', 'settings': {}}}, 'order': ['main']}

# ---------- write ----------
if OUT.exists():
    shutil.rmtree(OUT)
for d in ('layout', 'sections', 'templates', 'assets', 'optional-homepage/templates'):
    (OUT / d).mkdir(parents=True, exist_ok=True)
(OUT / 'layout' / 'farless.liquid').write_text(layout, encoding='utf-8')
(OUT / 'sections' / 'farless-landing.liquid').write_text(section, encoding='utf-8')
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
