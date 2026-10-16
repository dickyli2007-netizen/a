# Farless

Farless sells a premium 5-in-1 kitchen tap (boiling, filtered, sparkling, hot and cold water from one tap).
The owner's direction: calm, pure luxury in the spirit of Gessi and Vipp, dark warm tones, buy online,
and no prices shown anywhere ("keep it exclusive").

## Where things are

- `farless/index.html`: the static landing page, one self-contained file, used for design previews.
  Its `<head>` styles are the theme's styles: `:root` tokens, nav, footer, buttons and labels are the
  house style for everything else. Buttons (`.btn`: Buy Farless, Add to cart, Check out) are pills, as on
  Gessi's, and the heart beside Add to cart is a circle; picture cards (collection cards, product cards)
  have soft corners (`--radius`), and small pictures in the panels a smaller one (`--radius-sm`).
- `farless-work/theme/`: the Shopify theme's own source. Every page's words, pictures, links and film
  are section settings and blocks there, so the owner edits them in Online Store > Customize:
  `sections/` (film hero, shop, five waters, safety knob, design, questions, final call, product,
  collection, menu bar with its side menu, and footer, plus the header and footer groups), `snippets/`, `templates/` (which sections each page
  shows, with today's content) and `assets/farless.src.js` (the shared script; each part starts per
  section and restarts when the editor reloads a section).
- `farless-work/build_shopify.py`: builds `shopify/` and `farless-shopify-addon.zip` from those pieces,
  the landing page's styles and the product page template. Run it after any change, then Theme Check.
- `farless-work/theme-test/`: renders the theme like Shopify does with sample data and tests it in a
  browser (against the static page, with edited content, with theme editor events, and the cart against a
  stand-in for Shopify's cart in `cart-test.js`). See render.js.
- `farless-work/design-package.md`: the brand plan (palette, type, copy decisions, confirmed facts).
- `farless-work/product-page/`: the product page template and its preview builder (below), the cut-out
  tool, and `collection_image.py`, which composes a collection's picture from its products' cut-outs.

## The menu bar

After Gessi's: the Menu button on the left, the name in the middle, and four thin outline icons on the
right: search, account, favourites and the cart (a bag with a bronze count). On phones the bar keeps search,
favourites and the cart, and Log in or sign up sits with the side menu's small links. No Buy on the bar or
in the menu: the owner does not want the buy button pushed (keep it to the hero's close, the shop section
and the final call).
- Menu slides a side menu in from the left: Home, Collections (a second layer listing each collection with its
  own picture, else its first piece's cut-out, and its piece count; every collection when none are
  picked), the links in large type (Five waters, Safety, Design, Questions), and small links with the
  store policies near the bottom.
- Search drops a sheet from the top; pieces that match appear as you type (Shopify's predictive search
  through `sections/farless-predictive.liquid`), and Enter opens the Farless search page
  (`templates/search.json`, `sections/farless-search.liquid`).
- Account goes to Shopify's log in or sign up (new customer accounts are on).
- The heart opens favourites from the right. Every piece has a heart: collection and search cards
  (`snippets/farless-card.liquid`) and beside Add to cart on product pages. Each colour is its own
  favourite (keyed by product handle and variant id, with that colour's cut-out, name and link), and the
  product page's heart follows the colour picker, so colours added later work with no change. A saved heart
  turns a quiet red (`--liked`, #C75A4E), as does the count on the bar. Favourites are kept in the
  shopper's browser (localStorage), not in their account, and pieces or colours that are gone drop out.
- The bag slides the cart in from the right. Every Add to cart (product page, the shop section) adds through
  Shopify's Ajax cart without leaving the page and opens it. Each piece has a tick, a quantity and Remove;
  Select all and "2 selected" sit on top, and Check out takes only the ticked pieces. Shopify always checks out
  a whole cart, so the unticked pieces are taken out on the way to checkout, kept in the browser
  (`farless:cart-held`), and put back into the cart, still unticked (`farless:cart-off`), on the next page
  load, whether the shopper bought or came back. Prices stay hidden unless the menu bar's "Show prices in the
  cart" is on; checkout shows them. The cart page `/cart` (`sections/farless-cart.liquid`,
  `templates/cart.json`) shows the same cart with the checkout beside it. The cart's words are the menu bar's
  Cart panel settings. The cart script is written once, in `farless/index.html` between `/* ---------- cart:`
  and `/* ---------- end of the cart ---------- */`, and `build_shopify.py` puts it into `assets/farless.js`;
  off the store (the design previews) the same script keeps a cart in the browser and checkout only says
  what would happen. While every piece is at 0 stock, Add to cart shows Sold out, so the owner needs stock
  (or "continue selling when out of stock") to try it on the store.
One panel is open at a time; Escape, Close, the shade or a link close it, focus stays inside, and the
film ignores scrolling meanwhile. Picking the menu bar in the editor opens the side menu.

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
- The layout follows Gessi's product page (the owner's reference): the product large on the left, and
  beside it only the name, the colour picker and Add to cart with its heart, so the product has the
  focus. The page is wider than the others (up to 1680px) with a wide gap (up to 300px), so the product
  stands well apart from its name. The details (the Small heading and Tagline as their heading, the
  description, the notes across) sit below the product, after a hairline.
- The trail of links (Shop / collection / product) sits just under the bar, lined up with the Menu
  button, as on Gessi's pages; collection, search, collections and cart pages place theirs the same way.
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
- Phones: name on top, then the product, then the swatches and the button, so they fit on one screen
  together; the details follow below.
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
4. The details below the product show the Tagline as their heading, then the description's first
   paragraph (the product page's Description setting in the editor can show the whole description or
   none); an opening paragraph that repeats the Tagline is skipped.
5. Put it in its collection. Collection pages (`sections/farless-collection.liquid`, used by
   `templates/collection.json`) show each product as its first colour's cut-out with the same light and
   shadow. Give the collection a picture for the home page's 3:2 card:
   `python3 farless-work/product-page/collection_image.py OUT.jpg HANDLE HANDLE ...`
A product with one colour gets the page without the picker. Other options (a size, say) get a plain
select under the swatches.

### Previewing a product before it goes live

1. Get a studio photo of each colour on a plain, evenly lit backdrop, or the maker's transparent PNGs.
2. Cut each one out:
   `python3 farless-work/product-page/cutout.py PHOTO HANDLE --name NAME-COLOUR`
   This writes `assets/HANDLE/NAME-COLOUR.webp` and `assets/HANDLE/mask.png` and prints where the foot is
   (`shadow.x`). A photo that is already transparent keeps its own edge and is only cropped. Look at the
   cut-out on the dark page. If an edge is wrong, fix `mask.png` and rerun with `--mask`; `--floor ROW`
   drops a floor reflection under the product.
3. Write `products/HANDLE.json` by copying `products/faucet.json`. Use the Shopify product handle and
   real copy from the owner: title, kicker, lede, collection, description, notes, the finishes in order,
   and `shadow.x`, which is where the product's foot is, as a % of the image width. Chrome, brass, copper and black
   have built-in swatch fills; give `"swatch"` for any other colour.
4. Build: `python3 farless-work/product-page/build.py HANDLE`. This writes `pages/HANDLE/index.html` for
   local testing (serve it with `assets/HANDLE` as `assets/`) and `pages/HANDLE/page.html` for the preview.
5. Test on desktop and a phone (click, keyboard, swipe), publish `pages/HANDLE/page.html` as an artifact
   with `assets/HANDLE/*` as `assets/*`, plus the bar's pictures (`build.PANEL_ASSETS`, the `menu-*` and
   `search-*` files in `farless/assets`) also as `assets/*`, and record its URL under `"preview"` in the
   product file. The preview's menu, search and favourites work like the store's.

Stand-in colours: `cutout.py --recolour brass,copper,black` makes recoloured stand-ins from one photo,
for previews only. Mark them `"stand_in": true` and tell the owner. The Farless 5-in-1 Tap's brass,
copper and black are stand-ins until real photos exist.

## Store

- Shopify (farless.store), reached through the Shopify connector. Product "Farless 5-in-1 Tap" (handle
  `faucet`) has a Colour option with four variants at the same price: Polished Chrome, Satin Brass,
  Warm Copper, Matte Black. Brass, copper and black use the recoloured stand-in cut-outs until real
  photos exist; all four have 0 stock, so they show Sold out. Collection "Multi Function Faucets".
  Prices stay hidden on the site.
- Collection "Filtered Faucets" (manual order, picture composed from the cut-outs) holds five filtered
  taps from the maker's photos, one colour each: Farless Flex Duo Filter Tap (Polished Gold), Flex Square
  (Brushed Gold), Flex Angle (Rose Gold), Arc Duo (Brushed Steel) and Arc (Brushed Steel); handles
  `flex-duo-filter-tap` and so on, files in `farless-work/product-page/products/`. Their names and copy
  are working choices from the photos (visible features only) and their price is a 0.00 placeholder until
  the owner gives real ones; all have 0 stock, so they show Sold out, and they are on the Online Store
  only, not Shop or Point of Sale.
- The Farless fields on products are metafields in the `farless` namespace with definitions:
  `kicker`, `lede`, `notes`, `foot_x`.
- Theme files: `layout/farless.liquid` (loads `farless-header-group`, the page, `farless-footer-group`
  and `assets/farless.js`), the `farless-*` sections and snippets, `templates/index.json` and
  `templates/page.farless.json` (home page), `templates/product.json` (every product page),
  `templates/collection.json` (every collection page), `templates/cart.json` (the cart page,
  `sections/farless-cart.liquid`), `templates/list-collections.json` (the page listing
  every collection, `sections/farless-collections.liquid`, the home page's collection cards without
  Shopify's own "Home page" and "all" collections), `templates/search.json` (search results). The theme's
  original product, collection, collections list, cart and search pages are kept as the alternate templates
  `templates/product.atelier.json`, `collection.atelier.json`, `list-collections.atelier.json`,
  `cart.atelier.json` and `search.atelier.json`. Every Buy Farless button (the film's close, the still hero, the final call) goes
  to `/collections`, the owner's choice; they can repoint them in the editor.
- The connector cannot write to the live theme, publish one or delete theme files, so uploads go to an
  unpublished copy (duplicate the newest theme, upload with `themeFilesUpsert` from raw GitHub URLs
  pinned to a commit, check the checksums) and the owner previews and publishes it. Before copying, read
  the live theme's `templates/*.json` and group files: the owner's own editor changes live there and must
  not be overwritten. Upload sections and snippets before the templates and groups that use them; a
  URL upload runs as a background job, so check the checksums after it finishes. The retired
  `sections/farless-landing.liquid` is an empty stub with no preset; the owner can delete it.
- The landing shop section skips variant images, so colour cut-outs never show as photos there.
- Shopify's `collection.featured_image` falls back to the first product's photo; use `collection.image`
  for the collection's own picture.
- Shopify refuses a section whose text setting has `"default": ""` (Theme Check passes it); leave the
  default out for a setting that starts empty.
- `farless/index.html` must not contain Liquid braces (the build checks), so its script avoids writing a
  double opening brace even in strings.
