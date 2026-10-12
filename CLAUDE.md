# Farless

Farless sells a premium 5-in-1 kitchen tap (boiling, filtered, sparkling, hot and cold water from one tap).
The owner's direction: calm, pure luxury in the spirit of Gessi and Vipp, dark warm tones, buy online,
and no prices shown anywhere ("keep it exclusive").

## Where things are

- `farless/index.html`: the main landing page, one self-contained file. Its `:root` tokens, nav, footer,
  buttons and labels are the house style for everything else.
- `farless-work/design-package.md`: the brand plan (palette, type, copy decisions, confirmed facts).
- `farless-work/build_shopify.py`: builds the Shopify theme add-on from the landing page into `shopify/`
  and `farless-shopify-addon.zip`.
- `farless-work/product-page/`: the product page template (below).

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

### Adding a product

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
copper and black are stand-ins: in Shopify it has one variant and no colour option yet.

## Store

- Shopify, reached through the Shopify connector. Product "Farless 5-in-1 Tap" (handle `faucet`, one
  variant), collection "Multi Function Faucets". Prices stay hidden on the site.
- The landing page runs as a theme add-on (`layout/farless.liquid`, `sections/farless-landing.liquid`).
  The connector cannot write to the live theme, so uploads go to an unpublished theme copy and the owner
  previews and publishes it.
- The product page template is not in Shopify yet. Taking it live means a Farless product template
  (a section that renders any product, with each colour as a variant option and that variant's cut-out
  as its image). Do that only when the owner asks.
