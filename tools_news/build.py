import sys, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
import json, os
EP = json.load(open(os.environ.get('EP', 'episode.json')))
TOTAL = EP['total']
def C(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
PK = (239, 68, 68); POCKET = (56, 189, 248); TEAL = (45, 212, 191); PURPLE = (168, 85, 247); WHITE = (255, 255, 255)
NAVY = (13, 17, 38)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def F(s): return ImageFont.truetype(FB, s)
SEG = [(g['s'], g['e'], C(g['accent']), g.get('chip'), g['title'], g.get('sub', ''), g['img']) for g in EP['segs']]
PX0, PY0, PX1, PY1 = 58, 300, 1022, 992
def rounded(im, r):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255); im = im.convert('RGBA'); im.putalpha(m); return im
def fit(im, w, h):
    s = min(w / im.width, h / im.height); return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
IMDIR = EP.get('imgdir', 'img')
IM = {}
for g in EP['segs']:
    for k in (g['img'] if isinstance(g['img'], list) else [g['img']]):
        if k not in ('title', 'cta') and k not in IM: IM[k] = Image.open(os.path.join(IMDIR, k)).convert('RGB')
CROPS = {}
def card_img(k, maxw, maxh):
    if k == 'three':
        cw = int(maxh * 733 / 1024); c = Image.new('RGBA', (cw * 2 + 40, maxh), (0, 0, 0, 0))
        for i, (kk, dx, rot) in enumerate([('gastly', 0, 8), ('golett', cw + 40 - int(cw * .0), -8), ('heatran', None, 0)]):
            pass
        return None
    return rounded(fit(IM[k], maxw, maxh), 16)
def text_center(d, cx, y, s, size, fill):
    f = F(size); w = d.textlength(s, font=f)
    while w > 900 and size > 30: size -= 4; f = F(size); w = d.textlength(s, font=f)
    d.text((cx - w / 2, y), s, font=f, fill=fill)
def chip(img, s, acc, cy):
    d = ImageDraw.Draw(img); f = F(40); w = d.textlength(s, font=f) + 60
    d.rounded_rectangle((540 - w / 2, cy - 32, 540 + w / 2, cy + 32), 32, fill=acc); d.text((540 - (w - 60) / 2, cy - 26), s, font=f, fill=WHITE)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def panel(t, i):
    a, b, acc, ch, title, sub, key = SEG[i]; lt = t - a
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((PX0, PY0, PX1, PY1), 40, fill=NAVY + (255,), outline=acc, width=8)
    # new badge
    if True:
        d.rounded_rectangle((828, 262, 968, 314), 26, fill=(14, 16, 32)); d.text((858, 266), 'جديد', font=F(32), fill=WHITE)
    k1 = eo(lt / .35)
    if key == 'title':
        text_center(d, 540, 400, title, 84, WHITE)
        f = F(230); w = d.textlength('TCG', font=f); d.text((540 - w / 2, 500), 'TCG', font=f, fill=TEAL)
        if lt > .5: text_center(d, 540, 800, EP['date_label'], 56, (125, 211, 252))
        return img
    if key == 'cta':
        text_center(d, 540, 470, title, 64, WHITE); text_center(d, 540, 610, sub, 70, (125, 211, 252)); text_center(d, 540, 760, EP.get('cta_end', 'ونشوفكم بكرة!'), 54, (216, 180, 254))
        return img
    chip(img, ch, acc, 370); d = ImageDraw.Draw(img)
    text_center(d, 540, 420, title, 66, WHITE); text_center(d, 540, 510, sub, 40, acc)
    # image zone y 580..960
    zx, zy, zw, zh = 540, 775, 860, 370
    if isinstance(key, list):
        n = len(key); ch_ = 360 if n <= 3 else 300; cw = int(ch_ * .716); xs = [(-1 + 2 * j / max(1, n - 1)) * (270 if n > 1 else 0) for j in range(n)]
        order = sorted(range(n), key=lambda j: -abs(xs[j]))
        for j in order:
            kk = key[j]; rot = -xs[j] / 30; dl = .1 + .12 * abs(xs[j]) / 270
            c = rounded(fit(IM[kk], cw, ch_), 14); kk_ = ebk((lt - dl) / .45)
            if kk_ <= 0: continue
            c = c.rotate(rot * kk_, expand=True, resample=Image.BICUBIC); s_ = max(.01, kk_)
            c = c.resize((max(1, int(c.width * s_)), max(1, int(c.height * s_))), Image.LANCZOS)
            img.alpha_composite(c, (int(zx + xs[j] * kk_ - c.width / 2), int(zy - c.height / 2)))
        return img
    c = card_img(key, zw, zh)
    s = .85 + .15 * ebk((lt - .2) / .45); c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
    a_ = eo((lt - .15) / .3); c.putalpha(c.getchannel('A').point(lambda v: int(v * a_)))
    img.alpha_composite(c, (int(zx - c.width / 2), int(zy - c.height / 2 + 6 * math.sin(t * 2))))
    return img
cap = cv2.VideoCapture(os.environ.get('PLATE', 'plate.mp4')); PN = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); PF = cap.get(cv2.CAP_PROP_FPS)
NP = PN
_last = [-9]
def plate(t):
    n = int(t * PF) % (2 * NP - 2); n = n if n < NP else 2 * NP - 2 - n
    if _last[0] + 1 != n: cap.set(cv2.CAP_PROP_POS_FRAMES, n)
    ok, fr = cap.read(); _last[0] = n
    return fr
_b = Image.new('RGBA', (W, H), (0, 0, 0, 0)); _d = ImageDraw.Draw(_b)
_d.rounded_rectangle((PX0 - 6, PY0 - 6, PX1 + 6, PY1 + 6), 44, fill=NAVY + (255,)); _d.rounded_rectangle((828, 262, 968, 314), 26, fill=(14, 16, 32)); _d.text((858, 266), 'جديد', font=F(32), fill=WHITE)
BASE = np.array(_b); BA = BASE[..., 3:4] / 255.0; BRGB = BASE[..., :3][..., ::-1].astype(np.float32)
def render(t):
    i = next(k for k, s in enumerate(SEG) if s[0] <= t < s[1]) if t < TOTAL else len(SEG) - 1
    f = (plate(t) * (1 - BA) + BRGB * BA).astype(np.uint8)
    p = panel(t, i); a, b = SEG[i][0], SEG[i][1]
    # transition: panel slides/fades in
    lt = t - a; k = eo(lt / .3)
    arr = np.array(p); al = arr[..., 3:4] / 255.0 * k
    if k < 1: arr = np.roll(arr, int((1 - k) * 60), axis=0); al = np.roll(al, int((1 - k) * 60), axis=0)
    rgb = arr[..., :3][..., ::-1].astype(np.float32)
    f = (f * (1 - al) + rgb * al).astype(np.uint8)
    # cover old panel when fading: draw navy base always
    # progress bar
    f[0:12] = (40, 20, 30); f[0:12, :int(W * t / TOTAL)] = (252, 211, 125)
    if t > TOTAL - .4: f = (f * max(0, (TOTAL - t) / .4)).astype(np.uint8)
    return f
if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite('st.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))): p.stdin.write(render(i / FPS).tobytes())
        p.stdin.close(); p.wait()
