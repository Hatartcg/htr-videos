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
RAW = EP['segs']
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
        if k not in ('title', 'cta', 'top10') and k not in IM: IM[k] = Image.open(os.path.join(IMDIR, k)).convert('RGB')
    if g.get('blur') and g['blur'] not in IM: IM[g['blur']] = Image.open(os.path.join(IMDIR, g['blur'])).convert('RGB')
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

def fmt_price(v): return '+$' + f'{int(v):,}'
def dots(d, r, acc, cy=392):
    n = 10; sp = 58; x0 = 540 - sp * (n - 1) / 2
    for j in range(n):
        num = n - j; cx = x0 + sp * j
        on = num == r; done = r is not None and num > r
        fill = acc if on else ((70, 76, 110) if done else (34, 38, 64))
        rr = 24 if on else 19
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fill)
        f = F(24 if on else 20); w = d.textlength(str(num), font=f); d.text((cx - w / 2, cy - (15 if on else 13)), str(num), font=f, fill=WHITE if (on or done) else (120, 126, 160))
def rank_panel(t, i, img, d):
    g = RAW[i]; a = SEG[i][0]; acc = SEG[i][2]; lt = t - a; r = g.get('rank')
    hf = F(30); d.text((96, 322), EP.get('rank_header', 'TOP 10'), font=hf, fill=(216, 180, 254))
    rn = EP.get('rank_note', '')
    if rn: w = d.textlength(rn, font=hf); d.text((984 - w, 322), rn, font=hf, fill=(148, 163, 184))
    dots(d, r, acc)
    if r is None:
        f = F(170); w = d.textlength('TOP 10', font=f); k = ebk((lt - .1) / .5)
        d.text((540 - w / 2, 470 + 40 * (1 - k)), 'TOP 10', font=f, fill=TEAL)
        text_center(d, 540, 680, g['title'], 60, WHITE); text_center(d, 540, 770, g.get('sub', ''), 40, (125, 211, 252))
        return img
    ch_ = 520; c = rounded(fit(IM[g['img']], 380, ch_), 18); cw_ = c.width
    cx, cy = 300, 712 + 4 * math.sin(t * 2)
    k = ebk((lt - .05) / .45); sc = .82 + .18 * k
    # composite card + ribbon on a local canvas so they scale together
    pad = 40; L = Image.new('RGBA', (cw_ + 2 * pad, ch_ + 2 * pad), (0, 0, 0, 0)); L.alpha_composite(c, (pad, pad)); ld = ImageDraw.Draw(L)
    y0, y1 = pad + int(ch_ * .385), pad + int(ch_ * .615)
    ld.rectangle((pad - 22, y0, pad + cw_ + 22, y1), fill=acc + (255,)); ld.rectangle((pad - 22, y0, pad + cw_ + 22, y0 + 6), fill=WHITE); ld.rectangle((pad - 22, y1 - 6, pad + cw_ + 22, y1), fill=WHITE)
    kp = eo((lt - .2) / .8); v = g['price'] * kp; v = round(v / 10) * 10 if kp < 1 else g['price']
    f = F(26); tx = 'أكثر من'; w = ld.textlength(tx, font=f); ld.text((pad + cw_ / 2 - w / 2, y0 + 12), tx, font=f, fill=WHITE)
    size = 64; f = F(size); txt = fmt_price(v)
    while ld.textlength(txt, font=f) > cw_ - 10: size -= 4; f = F(size)
    w = ld.textlength(txt, font=f); ld.text((pad + cw_ / 2 - w / 2, y0 + 44), txt, font=f, fill=WHITE, stroke_width=3, stroke_fill=(60, 10, 20))
    L = L.resize((max(1, int(L.width * sc)), max(1, int(L.height * sc))), Image.LANCZOS)
    a_ = eo(lt / .25); L.putalpha(L.getchannel('A').point(lambda v_: int(v_ * a_)))
    if r == 1 and lt > .3:
        gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
        gd.rounded_rectangle((cx - cw_ / 2 - 18, cy - ch_ / 2 - 18, cx + cw_ / 2 + 18, cy + ch_ / 2 + 18), 30, fill=(250, 204, 21, 0) if False else acc + (int(220 * eo((lt - .3) / .5)),))
        img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(24)))
    img.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))
    d = ImageDraw.Draw(img)
    def ct(x, y, s_, size, fill, maxw=430):
        f = F(size); w = d.textlength(s_, font=f)
        while w > maxw and size > 20: size -= 2; f = F(size); w = d.textlength(s_, font=f)
        d.text((x - w / 2, y), s_, font=f, fill=fill)
    rx = 765; kb = ebk((lt - .15) / .4)
    if kb > 0:
        rr = int(92 * kb); by = 560; d.ellipse((rx - rr, by - rr, rx + rr, by + rr), fill=(124, 58, 237), outline=WHITE, width=5)
        f = F(int(84 * kb) + 1); txt = '#' + str(r); w = d.textlength(txt, font=f); d.text((rx - w / 2, by - 52 * kb), txt, font=f, fill=WHITE)
    ct(rx, 690, g['name'], 46, WHITE, 400)
    ct(rx, 752, g.get('var', ''), 34, (252, 165, 165), 400)
    ct(rx, 804, g.get('num', ''), 30, (148, 163, 184), 400)
    return img
def hook_panel(t, i, img, d):
    g = RAW[i]; a = SEG[i][0]; acc = SEG[i][2]; lt = t - a
    chip(img, SEG[i][3], acc, 370); d = ImageDraw.Draw(img)
    text_center(d, 540, 420, SEG[i][4], 62, WHITE)
    c = fit(IM[g['blur']], 330, 460).filter(ImageFilter.GaussianBlur(22)); c = rounded(c, 16)
    s = .85 + .15 * ebk((lt - .1) / .45); c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    img.alpha_composite(c, (int(540 - c.width / 2), int(760 - c.height / 2)))
    pulse = 1 + .06 * math.sin(lt * 6); f = F(int(120 * pulse)); txt = '$???'; w = d.textlength(txt, font=f)
    d.text((540 - w / 2, 760 - 75 * pulse), txt, font=f, fill=WHITE, stroke_width=6, stroke_fill=(30, 10, 40))
    return img
def panel(t, i):
    a, b, acc, ch, title, sub, key = SEG[i]; lt = t - a
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((PX0, PY0, PX1, PY1), 40, fill=NAVY + (255,), outline=acc, width=8)
    # new badge
    if True:
        d.rounded_rectangle((828, 262, 968, 314), 26, fill=(14, 16, 32)); d.text((858, 266), 'جديد', font=F(32), fill=WHITE)
    k1 = eo(lt / .35)
    if 'rank' in RAW[i] or RAW[i].get('img') == 'top10': return rank_panel(t, i, img, d)
    if RAW[i].get('blur'): return hook_panel(t, i, img, d)
    if key == 'title':
        text_center(d, 540, 400, title, 84, WHITE)
        f = F(230); w = d.textlength('TCG', font=f); d.text((540 - w / 2, 500), 'TCG', font=f, fill=TEAL)
        if lt > .5: text_center(d, 540, 800, EP['date_label'], 56, (125, 211, 252))
        return img
    if key == 'cta':
        text_center(d, 540, 470, title, 64, WHITE); text_center(d, 540, 610, sub, 70, (125, 211, 252)); text_center(d, 540, 760, EP.get('cta_end', 'ونشوفكم بكرة!'), 54, (216, 180, 254))
        return img
    chip(img, ch, acc, 370); d = ImageDraw.Draw(img)
    if RAW[i].get('hook'):  # hook: big number + card visible from frame 0
        text_center(d, 540, 410, title, RAW[i].get('tsize', 120), WHITE); text_center(d, 540, 545, sub, 44, acc)
        c = card_img(key, 860, 365); s = 1 + .03 * math.sin(lt * 3)
        c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
        img.alpha_composite(c, (int(540 - c.width / 2), int(805 - c.height / 2))); return img
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
    lt = t - a; k = 1.0 if RAW[i].get('hook') else eo(lt / .3)
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
