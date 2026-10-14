"""Cut a product out of a studio photo for the Farless product page template.

Works on photos shot on a plain, evenly lit backdrop (white or grey seamless). It models the
backdrop, finds the product, refines the edge, lifts the backdrop colour out of the edge pixels so
no light halo shows on the dark page, and saves a transparent WebP cropped to the product.
A photo that is already transparent (a maker's render or cut-out) keeps its own edge and is only
cropped. Both print where the product's foot is (shadow.x / Shadow position).

  python3 farless-work/product-page/cutout.py PHOTO HANDLE --name tap-chrome
      writes assets/HANDLE/tap-chrome.webp and assets/HANDLE/mask.png

Options:
  --mask PATH          use a hand-fixed mask (white = product) instead of finding one; the first run
                       saves mask.png, so fix that in any editor and pass it back if an edge is wrong
  --floor ROW          treat everything below this pixel row as backdrop (drops floor reflections)
  --recolour brass,copper,black
                       also write stand-in finishes recoloured from this photo, named NAME-PREFIX-<finish>
                       (tap-chrome -> tap-brass ...). Stand-ins are for previews only; real photos of
                       each finish replace them before a product goes live.

Always look at the result on the dark page before using it: every photo is different, and
manufacturer cut-outs (transparent PNGs) are better than any automatic cut when they exist.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent

# gradient maps from the photo's brightness to each finish (dark -> light)
FINISH_MAPS = {
    'brass': (0.8, [(0, '#1a1006'), (.18, '#3d2a12'), (.42, '#86642c'), (.62, '#b8924c'), (.8, '#dcbd7c'), (.93, '#f1dfab'), (1, '#fbf3d9')]),
    'copper': (0.8, [(0, '#170a06'), (.18, '#3b1c11'), (.42, '#7e4128'), (.62, '#b06c4c'), (.8, '#d69b7d'), (.93, '#ecc6b0'), (1, '#f9ebe1')]),
    'black': (3.0, [(0, '#0e0d0c'), (.3, '#181716'), (.55, '#252321'), (.75, '#3a3734'), (.9, '#615c57'), (1, '#9a948d')]),
}


def fill_small_holes(m, max_px):
    """Fill holes in the mask up to max_px pixels. Bigger holes are backdrop seen through the product,
    like the space a looped hose and spout arm close in, and stay open."""
    holes = ndi.binary_fill_holes(m) & ~m
    lbl, n = ndi.label(holes)
    if n == 0:
        return m
    sizes = ndi.sum(holes, lbl, range(1, n + 1))
    small = np.isin(lbl, 1 + np.flatnonzero(sizes <= max_px))
    return m | small


def find_mask(img_bgr, floor=None):
    """Product mask from a plain backdrop: fit the backdrop, threshold the difference, refine with GrabCut."""
    h, w = img_bgr.shape[:2]
    max_hole = 0.002 * h * w
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X, Y = xx / w, yy / h
    B = np.stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y, X ** 3, X * X * Y, X * Y * Y, Y ** 3], -1)
    sample = np.zeros((h, w), bool)
    sample[::6, ::6] = True
    keep = sample.copy()
    for _ in range(6):   # refit, dropping pixels that belong to the product
        coef = [np.linalg.lstsq(B[keep], lab[..., c][keep], rcond=None)[0] for c in range(3)]
        bg = np.stack([B @ cf for cf in coef], -1)
        d = np.sqrt(((lab - bg) ** 2).sum(-1))
        keep = sample & (d < 6)

    def blob(thr):
        m = ndi.binary_opening(d > thr, iterations=1)
        m = fill_small_holes(ndi.binary_closing(m, iterations=3), max_hole)
        lbl, n = ndi.label(m)
        if n == 0:
            raise SystemExit('no product found: is the backdrop plain and evenly lit?')
        m = lbl == (np.argmax(ndi.sum(m, lbl, range(1, n + 1))) + 1)
        return fill_small_holes(m, max_hole)

    loose, mid, strict = blob(12), blob(16), blob(20)
    gc = np.full((h, w), cv2.GC_BGD, np.uint8)
    gc[ndi.binary_dilation(loose, iterations=25)] = cv2.GC_PR_BGD
    gc[mid] = cv2.GC_PR_FGD
    gc[ndi.binary_erosion(strict, iterations=5)] = cv2.GC_FGD
    if floor is not None:
        gc[floor:, :] = cv2.GC_BGD
    cv2.grabCut(img_bgr, gc, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    m = (gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)
    m = fill_small_holes(ndi.binary_opening(m, iterations=2), max_hole)
    lbl, n = ndi.label(m)
    return lbl == (np.argmax(ndi.sum(m, lbl, range(1, n + 1))) + 1)


def hexrgb(s):
    s = s.lstrip('#')
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def recolour(F, sigma, stops):
    L = 0.2126 * F[..., 0] + 0.7152 * F[..., 1] + 0.0722 * F[..., 2]
    if sigma:   # softer reflections read as a satin or matte surface
        L = cv2.GaussianBlur(L, (0, 0), sigma) * 0.7 + L * 0.3
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.stack([hexrgb(s[1]) for s in stops])
    return np.stack([np.interp(L, xs, cs[:, c]) for c in range(3)], -1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('photo')
    ap.add_argument('handle')
    ap.add_argument('--name', required=True, help='file name for the cut-out, e.g. tap-chrome')
    ap.add_argument('--mask')
    ap.add_argument('--floor', type=int)
    ap.add_argument('--recolour', default='')
    ap.add_argument('--pad', type=int, default=18)
    args = ap.parse_args()

    src = Image.open(args.photo)
    out = HERE / 'assets' / args.handle
    out.mkdir(parents=True, exist_ok=True)
    if src.mode in ('RGBA', 'LA', 'PA') or 'transparency' in src.info:
        # already cut out: keep the maker's edge, only crop it
        rgba = np.asarray(src.convert('RGBA'), np.float32) / 255
        F, a = rgba[..., :3], rgba[..., 3].copy()
        a[a < 0.02] = 0
        M = a > 0.5
        if not M.any():
            raise SystemExit('the photo is fully transparent')
    else:
        bgr = cv2.cvtColor(np.asarray(src.convert('RGB')), cv2.COLOR_RGB2BGR)
        M = cv2.imread(args.mask, 0) > 127 if args.mask else find_mask(bgr, args.floor)
        if not args.mask:
            cv2.imwrite(str(out / 'mask.png'), (M * 255).astype(np.uint8))

        im = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        # soft edge, then take the backdrop's colour out of the edge pixels
        a = cv2.GaussianBlur(M.astype(np.float32), (0, 0), 0.75)
        a[a < 0.02] = 0
        bgm = (~ndi.binary_dilation(M, iterations=3)).astype(np.float32)
        backdrop = cv2.GaussianBlur(im * bgm[..., None], (0, 0), 7) / np.maximum(cv2.GaussianBlur(bgm, (0, 0), 7), 1e-4)[..., None]
        # along the edge, take each pixel's coverage from its colour where the product stands out from
        # the backdrop (a dark hose on white), so half-covered pixels don't keep a light rim
        band = ndi.binary_dilation(M, iterations=2) & ~ndi.binary_erosion(M, iterations=2)
        inner = ndi.binary_erosion(M, iterations=3).astype(np.float32)
        fg = cv2.GaussianBlur(im * inner[..., None], (0, 0), 4) / np.maximum(cv2.GaussianBlur(inner, (0, 0), 4), 1e-4)[..., None]
        span = fg - backdrop
        contrast = (span ** 2).sum(-1)
        cover = np.clip(((im - backdrop) * span).sum(-1) / np.maximum(contrast, 1e-4), 0, 1)
        use = band & (contrast > 0.3 ** 2) & (cv2.GaussianBlur(inner, (0, 0), 4) > 0.05)
        a = np.where(use, cover, a)
        a[a < 0.02] = 0
        A = a[..., None]
        F = np.where(A > 0.98, im, np.clip((im - (1 - A) * backdrop) / np.maximum(A, 0.08), 0, 1))

    ys, xs = np.where(a > 0.01)
    y0, y1 = max(ys.min() - args.pad, 0), min(ys.max() + args.pad, a.shape[0])
    x0, x1 = max(xs.min() - args.pad, 0), min(xs.max() + args.pad, a.shape[1])

    def save(name, rgb):
        rgba = np.dstack([np.clip(rgb, 0, 1), a])[y0:y1, x0:x1]
        Image.fromarray((rgba * 255 + .5).astype(np.uint8), 'RGBA').save(out / f'{name}.webp', quality=88, method=6)
        print('wrote', out / f'{name}.webp', f'{x1 - x0}x{y1 - y0}')

    save(args.name, F)
    # the foot: the middle of the lowest solid rows, as a % of the cut-out's width
    rows = np.flatnonzero(M.any(1))
    base = M[max(rows[-1] - max(3, (rows[-1] - rows[0]) // 60), 0):rows[-1] + 1]
    fx = np.flatnonzero(base.any(0))
    print(f'foot at {((fx[0] + fx[-1]) / 2 - x0) / (x1 - x0) * 100:.1f}% of the width (shadow.x / Shadow position)')
    prefix = args.name.rsplit('-', 1)[0] if '-' in args.name else args.name
    for fin in filter(None, args.recolour.split(',')):
        if fin not in FINISH_MAPS:
            raise SystemExit(f'no recolour map for {fin}; known: {", ".join(FINISH_MAPS)}')
        save(f'{prefix}-{fin}', recolour(F, *FINISH_MAPS[fin]))


if __name__ == '__main__':
    main()
