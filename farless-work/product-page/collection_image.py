"""Compose a collection's picture from its products' cut-outs: the pieces standing in a row on the dark
panel, in the soft light and with the contact shadows of the product pages. Shopify shows it on the
home page's collection card (3:2), so the card never crops a single cut-out.

  python3 farless-work/product-page/collection_image.py OUT.jpg HANDLE [HANDLE ...]

Each HANDLE needs products/HANDLE.json (its first finish's image and shadow.x) and its cut-out in
assets/HANDLE/. HANDLE@FINISH picks another finish by its key (faucet@black), so one product can stand
in two finishes side by side.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
W, H = 2400, 1600
PANEL = (34, 27, 22)        # --panel
LIGHT = (236, 227, 214)     # the ivory of the product pages' light


def main():
    out, handles = sys.argv[1], sys.argv[2:]
    if not handles:
        raise SystemExit(__doc__)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .46)) ** 2 + ((yy - H * .52) / (H * .42)) ** 2)
    glow = np.clip(1 - r / .72, 0, 1)[..., None] * .085
    base = np.array(PANEL, np.float32) * (1 - glow) + np.array(LIGHT, np.float32) * glow
    canvas = Image.fromarray(base.astype(np.uint8), 'RGB').convert('RGBA')

    pieces = []
    for spec in handles:
        h, _, key = spec.partition('@')
        p = json.loads((HERE / 'products' / f'{h}.json').read_text())
        fin = next(f for f in p['finishes'] if f['key'] == key) if key else p['finishes'][0]
        im = Image.open(HERE / 'assets' / h / fin['image']).convert('RGBA')
        pieces.append((im, p['shadow']['x'] / 100))
    tall = int(H * .5)
    floor = int(H * .77)
    step = W * .94 / len(pieces)
    scaled = [(im.resize((round(im.width * tall / im.height), tall), Image.LANCZOS), fx) for im, fx in pieces]
    # spread the feet evenly, then centre the whole row on the picture
    feet = [step * (i + .5) for i in range(len(scaled))]
    left = min(f - im.width * fx for (im, fx), f in zip(scaled, feet))
    right = max(f + im.width * (1 - fx) for (im, fx), f in zip(scaled, feet))
    shift = (W - (right - left)) / 2 - left
    for (im, fx), f in zip(scaled, feet):
        x = round(f + shift - im.width * fx)
        y = floor - im.height
        # contact shadow under the foot
        sw, sh = int(im.width * .34 * 1.6), int(tall * .05)
        sm = Image.new('L', (sw * 2, sh * 2), 0)
        a = np.asarray(sm, np.float32)
        gy, gx = np.mgrid[0:sh * 2, 0:sw * 2].astype(np.float32)
        d = np.sqrt(((gx - sw) / sw) ** 2 + ((gy - sh) / sh) ** 2)
        shadow_a = (np.clip(1 - d, 0, 1) ** 1.2 * 205).astype(np.uint8)
        shadow = Image.new('RGBA', (sw * 2, sh * 2), (4, 3, 2, 0))
        shadow.putalpha(Image.fromarray(shadow_a, 'L').filter(ImageFilter.GaussianBlur(3)))
        canvas.alpha_composite(shadow, (round(f + shift - sw), round(floor - tall * .016 - sh)))
        canvas.alpha_composite(im, (x, y))
    canvas.convert('RGB').save(out, quality=90, optimize=True, progressive=True)
    print('wrote', out, f'{W}x{H}')


if __name__ == '__main__':
    main()
