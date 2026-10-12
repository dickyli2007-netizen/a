# Farless

Farless sells a premium 5-in-1 kitchen tap (boiling, filtered, sparkling, hot and cold water from one tap).
The owner's direction: calm, pure luxury in the spirit of Gessi and Vipp, dark warm tones, buy online,
and no prices shown anywhere ("keep it exclusive").

## Where things are

- `farless/index.html`: the static landing page, one self-contained file, used for design previews.
  Its `<head>` styles are the theme's styles: `:root` tokens, nav, footer, buttons and labels are the
  house style for everything else.
- `farless-work/theme/`: the Shopify theme's own source. Every page's words, pictures, links and film
  are section settings and blocks there, so the owner edits them in Online Store > Customize:
  `sections/` (film hero, shop, five waters, safety knob, design, questions, final call, product, menu bar
  and footer, plus the header and footer groups), `snippets/`, `templates/` (which sections each page
  shows, with today's content) and `assets/farless.src.js` (the shared script; each part starts per
  section and restarts when the editor reloads a section).
- `farless-work/build_shopify.py`: builds `shopify/` and `farless-shopify-addon.zip` from those pieces,
  the landing page's styles and the product page template. Run it after any change, then Theme Check.
- `farless-work/theme-test/`: renders the theme like Shopify does with sample data and tests it in a
  browser (against the static page, with edited content, with theme editor events). See render.js.
- `farless-work/design-package.md`: the brand plan (palette, type, copy decisions, confirmed facts).
- `farless-work/product-page/`: the product page template and its preview builder (below).

## Changing the site

The owner edits content in the theme editor, so content changes belong in the store, not in code.
A design change goes in two places: the static page `farless/index.html` (styles and markup) and the
matching section in `farless-work/theme/sections/`; the styles reach the theme through the build.
Anything new the owner might want to change gets a setting or a block, never fixed text.

## Product pages: always use the approved template

The owner approved the product page in `farless-work/product-page/` as the template for every product
they add. Build each new product's page from it instead of designing a new one.
Approved example: https://claude.ai/artifact/CbtjXLSyknvk6Hb2CFsAa7 (Farless 5-in-1 Tap).

Keep these, they are what the owner approved:
- The product alone on the page: a transparent cut-out on the dark page, with a soft warm light behind
  it and a contact shadow under its foot. Never a photo backdrop.
- The colour picker sits in the column beside the product: "Colour. Pick your favourite.", then the
  colour name, then round swatches with a thin ivory ring on the chosen one.
- Choosing a colour slides the current product out to the left and fades it while the next glides in
  from the right and settles (1.05s, `cubic-bezier(.45,0,.15,1)`); the colour name slides with it; a
  hairline with an "01 / 04" counter sits under the product. Swiping or dragging the product changes
  colour too. Only transform and opacity animate.
- The colour picker belongs on product pages only, never on the main page. The main page's shop
  section stays as it is.
- Phones: name on top, then the product, then the swatches, so the product and the swatches fit on one
  screen together.
- A product with one colour gets the same page without the picker.

### Adding a product to the store

The Shopify product page (`sections/farless-product.liquid`, used by `templates/product.json` for every
product) builds itself from the product, so a new product needs no new code:
1. Cut out a photo of each colour with `cutout.py` (below) and upload them to the product.
2. Give the product an option named Colour (Color or Finish also work), one variant per colour, and set
   each variant's image to its cut-out. The swatch fill comes from the colour's name (chrome, steel,
   nickel, brass, gold, copper, rose, bronze, black, graphite, white), or from Shopify's own swatch colour
   when one is set.
3. Fill in the product's Farless fields in the admin: Small heading, Tagline, Notes (one per line,
   "Label | text") and Shadow position (where the foot is, % from the left of the cut-out).
4. The first paragraph of the description shows under the button, so open the description with it.
A product with one colour gets the page without the picker. Other options (a size, say) get a plain
select under the swatches.

### Previewing a product before it goes live

1. Get a studio photo of each colour on a plain, evenly lit backdrop, or the maker's transparent PNGs.
2. Cut each one out:
   `python3 farless-work/product-page/cutout.py PHOTO HANDLE --name NAME-COLOUR`
   This writes `assets/HANDLE/NAME-COLOUR.webp` and `assets/HANDLE/mask.png`. Look at the cut-out on the
   dark page. If an edge is wrong, fix `mask.png` and rerun with `--mask`; `--floor ROW` drops a floor
   reflection under the product.
3. Write `products/HANDLE.json` by copying `products/faucet.json`. Use the Shopify product handle and
   real copy from the owner: title, kicker, lede, collection, description, notes, the finishes in order,
   and `shadow.x`, which is where the product's foot is, as a % of the image width. Chrome, brass, copper and black
   have built-in swatch fills; give `"swatch"` for any other colour.
4. Build: `python3 farless-work/product-page/build.py HANDLE`. This writes `pages/HANDLE/index.html` for
   local testing (serve it with `assets/HANDLE` as `assets/`) and `pages/HANDLE/page.html` for the preview.
5. Test on desktop and a phone (click, keyboard, swipe), publish `pages/HANDLE/page.html` as an artifact
   with `assets/HANDLE/*` as `assets/*`, and record its URL under `"preview"` in the product file.

Stand-in colours: `cutout.py --recolour brass,copper,black` makes recoloured stand-ins from one photo,
for previews only. Mark them `"stand_in": true` and tell the owner. The Farless 5-in-1 Tap's brass,
copper and black are stand-ins until real photos exist.

## Store

- Shopify (farless.store), reached through the Shopify connector. Product "Farless 5-in-1 Tap" (handle
  `faucet`) has a Colour option with four variants at the same price: Polished Chrome, Satin Brass,
  Warm Copper, Matte Black. Brass, copper and black use the recoloured stand-in cut-outs until real
  photos exist; all four have 0 stock, so they show Sold out. Collection "Multi Function Faucets".
  Prices stay hidden on the site.
- The Farless fields on products are metafields in the `farless` namespace with definitions:
  `kicker`, `lede`, `notes`, `foot_x`.
- Theme files: `layout/farless.liquid` (loads `farless-header-group`, the page, `farless-footer-group`
  and `assets/farless.js`), the `farless-*` sections and snippets, `templates/index.json` and
  `templates/page.farless.json` (home page), `templates/product.json` (every product page). The theme's
  original product page is kept as the alternate template `templates/product.atelier.json`. Buttons that
  buy link to `shopify://products/faucet` in the templates; the owner can repoint them in the editor.
- The connector cannot write to the live theme or publish one, so uploads go to an unpublished copy
  (duplicate the live theme, upload with `themeFilesUpsert` from raw GitHub URLs pinned to a commit,
  check the checksums) and the owner previews and publishes it. The landing shop section skips variant
  images, so colour cut-outs never show as photos there.
