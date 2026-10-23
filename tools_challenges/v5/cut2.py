import numpy as np, cv2
from PIL import Image
def cutout_rgba(path, w, thr=232, close=11):
    im = Image.open(path).convert('RGB'); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    a = np.array(im); white = (a.min(2) > thr) & ((a.max(2).astype(int) - a.min(2)) < 18)
    fg0 = (~white).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    fgc = cv2.dilate(fg0, k)
    free = (1 - fgc).astype(np.uint8)
    n, lab = cv2.connectedComponents(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border)).astype(np.uint8)
    bg = cv2.dilate(bg, k) & white.astype(np.uint8)
    # also kill any remaining white blobs touching border-connected bg
    n2, lab2 = cv2.connectedComponents(white.astype(np.uint8))
    touch = set(np.unique(lab2[bg > 0])) - {0}
    bg = np.isin(lab2, list(touch)).astype(np.uint8) | bg
    alpha = np.where(bg > 0, 0, 255).astype(np.uint8)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    out = np.dstack([a, alpha]); return Image.fromarray(out, 'RGBA')
if __name__ == '__main__':
    import sys
    tiles = []
    for p in sys.argv[1:]:
        r = cutout_rgba(p, 500); bgc = Image.new('RGBA', r.size, (30, 60, 30, 255)); bgc.alpha_composite(r); tiles.append(bgc.convert('RGB').resize((400, int(400 * r.height / r.width))))
    H_ = max(t.height for t in tiles); c = Image.new('RGB', (400 * len(tiles), H_))
    for i, t in enumerate(tiles): c.paste(t, (400 * i, 0))
    c.save('/tmp/claude-0/-home-claude/095a1f67-79b6-5304-8a7c-26b575e3b942/scratchpad/cut.jpg')
