"""Build the Farless Shopify theme files into shopify/ and farless-shopify-addon.zip.

Everything the owner edits lives in sections with settings and blocks, so the theme editor can
change it. The pieces come from:
  farless/index.html                   the styles (layout head) and the page chrome
  farless-work/theme/sections/         the editable sections, header and footer groups
  farless-work/theme/snippets/         small shared pieces (the arc line, the water icons)
  farless-work/theme/templates/        which sections each page shows, with today's content
  farless-work/theme/assets/farless.src.js   the shared script; the product picker comes from
                                       the product page template (farless-work/product-page/build.py)

Run from the repo root: python3 farless-work/build_shopify.py, then run Theme Check.
"""
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'farless' / 'index.html'
THEME = ROOT / 'farless-work' / 'theme'
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

# the approved product page template: its styles, its slide and picker script, its swatch fills
_spec = importlib.util.spec_from_file_location('product_page', ROOT / 'farless-work' / 'product-page' / 'build.py')
product_page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(product_page)

# ---------- layout: head and styles from the landing page; header, page and footer from the editor ----------
head = src[src.index('<head>') + len('<head>'):src.index('</head>')]
body = src[src.index('<body>') + len('<body>'):src.index('</body>')]

# titles and descriptions come from Shopify: each product's search listing, and the home page title and
# description in Online Store > Preferences, with today's wording when those are left at the defaults
TITLE = ("{%- liquid\n"
         "  if template.name == 'product'\n"
         "    assign farless_title = product.title | append: ' | ' | append: shop.name\n"
         "  elsif template.name == 'index' and page_title != shop.name\n"
         "    assign farless_title = page_title\n"
         "  elsif template.name == 'index'\n"
         "    assign farless_title = 'Farless | Five waters. One tap.'\n"
         "  else\n"
         "    assign farless_title = page_title | append: ' | ' | append: shop.name\n"
         "  endif\n"
         "  assign farless_description = page_description | default: 'Farless is one quiet kitchen tap for boiling, filtered, sparkling, hot and cold water. Far less on your counter.'\n"
         "-%}\n"
         "<title>{{ farless_title | escape }}</title>\n"
         '<link rel="canonical" href="{{ canonical_url }}">')
head = must_replace(head, '<title>Farless | Five waters. One tap.</title>', TITLE)
head = must_replace(head, '<meta name="description" content="Farless is one quiet kitchen tap for boiling, filtered, sparkling, hot and cold water. Far less on your counter.">',
                    '<meta name="description" content="{{ farless_description | escape }}">')
head = must_replace(head, '<meta property="og:title" content="Farless | Five waters. One tap.">\n'
                    '<meta property="og:description" content="Boiling, filtered, sparkling, hot and cold water from one quiet tap.">\n'
                    '<meta property="og:type" content="website">',
                    '<meta property="og:title" content="{{ farless_title | escape }}">\n'
                    '<meta property="og:description" content="{{ farless_description | escape }}">\n'
                    "<meta property=\"og:type\" content=\"{% if template.name == 'product' %}product{% else %}website{% endif %}\">")
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

chrome = body[:body.index('<nav class="top"')].strip()
layout = (
    '<!doctype html>\n<html lang="{{ request.locale.iso_code }}">\n<head>' + head + '</head>\n<body>\n'
    + chrome + '\n'
    + "{% sections 'farless-header-group' %}\n"
    + '<main id="main" tabindex="-1">\n{{ content_for_layout }}\n</main>\n'
    + "{% sections 'farless-footer-group' %}\n"
    + "<script src=\"{{ 'farless.js' | asset_url }}\" defer></script>\n"
    + '</body>\n</html>\n'
)

# ---------- sections: copied as written, the product section gets the template's styles and swatches ----------
SWATCH_EXTRA = {
    'white': 'linear-gradient(135deg,#ffffff 0%,#e7e3dd 45%,#f6f3ee 60%,#bdb7ae 100%)',
    'neutral': 'linear-gradient(135deg,#d8d1c7 0%,#8f877c 50%,#5e574f 100%)',
}
files = {}
for path in sorted((THEME / 'sections').iterdir()):
    files[f'sections/{path.name}'] = path.read_text(encoding='utf-8')
for path in sorted((THEME / 'snippets').iterdir()):
    files[f'snippets/{path.name}'] = path.read_text(encoding='utf-8')
for path in sorted((THEME / 'templates').iterdir()):
    files[f'templates/{path.name}'] = path.read_text(encoding='utf-8')

product = files['sections/farless-product.liquid']
assert '{{' not in product_page.CSS and '{%' not in product_page.CSS
product = must_replace(product, '/*FARLESS_PRODUCT_CSS*/', product_page.CSS)
for key, fill in {**product_page.SWATCHES, **SWATCH_EXTRA}.items():
    product = product.replace('%%%%SW_%s%%%%' % key.upper(), fill)
assert '%%SW_' not in product, 'a swatch placeholder has no fill'
files['sections/farless-product.liquid'] = product

# ---------- the shared script, with the product picker from the template ----------
script = (THEME / 'assets' / 'farless.src.js').read_text(encoding='utf-8')
script = must_replace(script, '/*FARLESS_PICKER*/', product_page.JS_PICKER.rstrip())
files['assets/farless.js'] = script
files['layout/farless.liquid'] = layout

# ---------- write ----------
if OUT.exists():
    shutil.rmtree(OUT)
for name, text in files.items():
    (OUT / name).parent.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(text, encoding='utf-8')
for src_name, dst_name in ASSETS.items():
    shutil.copy2(ROOT / 'farless' / 'assets' / src_name, OUT / 'assets' / dst_name)

zip_path = ROOT / 'farless-shopify-addon.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file():
            z.write(f, f.relative_to(OUT))
print('built', OUT, 'and', zip_path)
for name in sorted(files):
    print('  ', name)
