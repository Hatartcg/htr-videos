import math, subprocess, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
PURPLE = (142, 117, 255); TEAL = (46, 196, 182); GREEN = (22, 196, 119); RED = (255, 34, 69); WHITE = (255, 255, 255); LILAC = (205, 195, 255); DEEP = (12, 8, 28); DIM = (120, 112, 160)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.8): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def env(t, a, d): return max(0.0, 1 - (t - a) / d) if t >= a else 0.0
def to_bgra(im): a = np.array(im.convert('RGBA')); return a[..., [2, 1, 0, 3]].copy()
def txt(s, font, fill=WHITE, stroke=0, glow=None, gr=18):
    d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8))); bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke); p = 40
    im = Image.new('RGBA', (bb[2] - bb[0] + 2 * p, bb[3] - bb[1] + 2 * p), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).text((p - bb[0], p - bb[1]), s, font=font, fill=glow + (255,), stroke_width=stroke + 4, stroke_fill=glow + (255,)); im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(gr)))
    ImageDraw.Draw(im).text((p - bb[0], p - bb[1]), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=DEEP)
    return to_bgra(im)
def fit_txt(s, mk, size, maxw, **kw):
    while size > 20:
        t = txt(s, mk(size), **kw)
        if t.shape[1] - 80 <= maxw: return t
        size -= 4
    return t
def rrect(w, h, r, fill, outline=None, ow=0, glow=None):
    im = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((40, 40, 40 + w, 40 + h), r, fill=glow + (200,)); im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(im).rounded_rectangle((40, 40, 40 + w, 40 + h), r, fill=fill, outline=outline, width=ow); return to_bgra(im)
def pill(s, font, bg, fg=WHITE, border=None, padx=40, pady=18):
    d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8))); bb = d0.textbbox((0, 0), s, font=font); w, h = bb[2] - bb[0] + 2 * padx, bb[3] - bb[1] + 2 * pady
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg + (255,), outline=(border + (255,)) if border else None, width=4)
    d.text((20 + padx - bb[0], 20 + pady - bb[1]), s, font=font, fill=fg); return to_bgra(im)
def blit(f, spr, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.003 or s <= 0.01: return
    h0, w0 = spr.shape[:2]
    if abs(rot) > .01 or abs(s - 1) > .001:
        M = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), rot, s); cw, ch = int(w0 * s * 1.45 + 4), int(h0 * s * 1.45 + 4)
        M[0, 2] += cw / 2 - w0 / 2; M[1, 2] += ch / 2 - h0 / 2
        spr = cv2.warpAffine(spr, M, (cw, ch), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    h, w = spr.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sp = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); al = sp[..., 3:4] / 255.0 * a
    reg = f[ya:yb, xa:xb]; reg[:] = reg * (1 - al) + sp[..., :3] * al
def card_img(path, w):
    im = Image.open(path).convert('RGBA'); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), int(w * .045), fill=255)
    a = np.minimum(np.array(im.getchannel('A')), np.array(m)); im.putalpha(Image.fromarray(a)); return im
def card_spr(im, glow=None, strength=.95):
    c = Image.new('RGBA', (im.width + 120, im.height + 120), (0, 0, 0, 0))
    g = Image.new('RGBA', c.size, (0, 0, 0, 0)); gm = Image.new('L', c.size, 0); gm.paste(im.getchannel('A'), (60, 60))
    g.paste(Image.new('RGBA', c.size, (glow or (0, 0, 0)) + (255,)), (0, 0), gm.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * (strength if glow else .7))))
    c = Image.alpha_composite(c, g); c.alpha_composite(im, (60, 60)); return to_bgra(c)
def gray(im, k=.45):
    g = im.convert('L').convert('RGB'); g = Image.eval(g, lambda v: int(v * k)).convert('RGBA'); g.putalpha(im.getchannel('A')); return g
def logo_spr(w, glow=True):
    l = Image.open('/home/claude/v5/htr_logo.png').convert('RGBA'); l = l.resize((w, int(l.height * w / l.width)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    c = Image.new('RGBA', (l.width + 120, l.height + 120), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', c.size, (0, 0, 0, 0)); m = Image.new('L', c.size, 0); m.paste(l.getchannel('A'), (60, 60)); g.paste(Image.new('RGBA', c.size, (150, 200, 255, 255)), (0, 0), m.filter(ImageFilter.GaussianBlur(30))); c = Image.alpha_composite(c, g)
    c.alpha_composite(l, (60, 60)); return to_bgra(c)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def make_bg(cy=760, base=DEEP, glowc=PURPLE):
    ANG = np.arctan2(yy - cy, xx - W / 2); RAD = np.sqrt((xx - W / 2) ** 2 + (yy - cy) ** 2)
    B = np.zeros((H, W, 3), np.float32); B[:] = np.array(base[::-1], np.float32)
    GP = np.exp(-(RAD / 760) ** 2)[..., None] * np.array(glowc[::-1], np.float32)
    GG = np.exp(-(RAD / 620) ** 2)[..., None] * np.array(GREEN[::-1], np.float32)
    FALL = np.exp(-(RAD / 1100) ** 2)[..., None]
    rng = np.random.default_rng(5); SPK = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 5), rng.uniform(0, 6.3), rng.uniform(20, 60)) for _ in range(60)]
    def bg(t, win=0.0, rays_n=16):
        rays = (.5 + .5 * np.cos((ANG + t * .18) * rays_n))[..., None] * FALL
        f = B + GP * .30 + rays * 20 + win * (GG * .35 + rays * 40 * np.array([.6, 1, .7], np.float32))
        f = np.clip(f, 0, 255).astype(np.uint8)
        for x, y, r, ph, v in SPK:
            if .35 + .35 * math.sin(t * 2 + ph) > .5: cv2.circle(f, (int(x), int((y - v * t) % H)), int(r), (255, 230, 240), -1, cv2.LINE_AA)
        return f.astype(np.float32)
    return bg
def end_card(f, k, S):
    blit(f, S['logo'], W / 2, 660, ebk(k / .4), 1)
    blit(f, S['e3'], W / 2, 900, ebk((k - .3) / .35), 1 if k > .3 else 0); blit(f, S['ig'], W / 2, 1020, ebk((k - .45) / .35), 1 if k > .45 else 0)
    blit(f, S['loc'], W / 2, 1140, ebk((k - .6) / .35), 1 if k > .6 else 0)
def end_assets(line='تابعنا لتحديات أكثر'):
    return dict(logo=logo_spr(560), e3=txt(line, FL(66), WHITE), ig=pill('@hatar_tcg', FB(46), (28, 22, 50), fg=(160, 240, 230), border=TEAL),
                loc=txt('معرضنا – أبحر الجنوبية، العليا سكوير، جدة', FL(42), LILAC), wm=logo_spr(150, False))
def encode(render, a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(int(round(a * FPS)), int(round(b * FPS))): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait()
def stills(render, ts, out='st.jpg'):
    ims = [cv2.resize(render(t), (270, 480)) for t in ts]
    rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
    cv2.imwrite(out, np.vstack(rows))
def split_voice(path, lines_ranges, SR=48000):
    v = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
    return [v[int(a * SR):int((b if b else len(v) / SR) * SR)] for a, b in lines_ranges]
def silences(path, db=-38, d=.35):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', f'silencedetect=n={db}dB:d={d}', '-f', 'null', '-'], capture_output=True, text=True).stderr
    import re
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', o)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', o)]
    return list(zip(st, en))
def lines_from_silences(path, n):
    """split voice into n lines using the n-1 longest silences"""
    s = silences(path); s = sorted(sorted(s, key=lambda x: -(x[1] - x[0]))[:n - 1])
    b = [0.0] + [e for _, e in s]; e = [st for st, _ in s] + [None]
    return list(zip(b, e))
