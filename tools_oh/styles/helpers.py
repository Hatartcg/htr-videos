import sys, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
PINK = (255, 61, 154); VIOLET = (139, 92, 246); CYAN = (56, 225, 255); WHITE = (255, 255, 255); DEEP = (20, 10, 46)
rng = np.random.default_rng(7)

# ---------- helpers ----------
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def ebk(x, s=1.9): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def env(t, a, d): return max(0.0, 1 - (t - a) / d) if t >= a else 0.0

def to_bgra(im):
    a = np.array(im.convert('RGBA')); return a[..., [2, 1, 0, 3]].copy()

def text_sprite(s, font, fill=WHITE, grad=None, stroke=0, stroke_fill=(20, 10, 46), glow=None, glow_r=18, pad=40, shadow=True):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    ox, oy = pad - bb[0], pad - bb[1]
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).text((ox, oy), s, font=font, fill=255)
    smask = Image.new('L', (w, h), 0); ImageDraw.Draw(smask).text((ox, oy), s, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', (w, h), glow + (0,)); g.putalpha(smask.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.6))))
        out = Image.alpha_composite(out, g)
    if shadow:
        sh = Image.new('RGBA', (w, h), (10, 0, 30, 0)); m2 = Image.new('L', (w, h), 0); m2.paste(smask, (0, 10)); sh.putalpha(m2.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .7)))
        out = Image.alpha_composite(out, sh)
    if stroke:
        st = Image.new('RGBA', (w, h), stroke_fill + (0,)); st.putalpha(smask); out = Image.alpha_composite(out, st)
    if grad:
        y = np.linspace(0, 1, h)[:, None]; c0, c1 = np.array(grad[0], float), np.array(grad[1], float)
        col = (c0 * (1 - y) + c1 * y)[:, None, :].repeat(w, 1) if False else np.broadcast_to((c0[None, :] * (1 - y) + c1[None, :] * y)[:, None, :], (h, w, 3))
        fillim = Image.fromarray(col.astype(np.uint8), 'RGB').convert('RGBA')
    else:
        fillim = Image.new('RGBA', (w, h), fill + (255,))
    fillim.putalpha(mask); out = Image.alpha_composite(out, fillim)
    return to_bgra(out)

def pill(s, font, bg, fg=WHITE, padx=44, pady=20, border=None):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; w, h = tw + 2 * padx, th + 2 * pady
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle((20, 24, 20 + w, 24 + h), h // 2, fill=(bg[0], bg[1], bg[2], 160)); gl = gl.filter(ImageFilter.GaussianBlur(10))
    im = Image.alpha_composite(im, gl); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg + (255,), outline=border, width=4 if border else 0)
    d.text((20 + padx - bb[0], 20 + pady - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)

def rounded(im, r):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im = im.convert('RGBA'); im.putalpha(m); return im

def blit(f, spr, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.003 or s <= 0.01: return
    h0, w0 = spr.shape[:2]
    if abs(rot) > .01 or abs(s - 1) > .001:
        M = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), rot, s)
        cw, ch = int(w0 * s * 1.5 + 4), int(h0 * s * 1.5 + 4)
        M[0, 2] += cw / 2 - w0 / 2; M[1, 2] += ch / 2 - h0 / 2
        spr = cv2.warpAffine(spr, M, (cw, ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    h, w = spr.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sp = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    al = sp[..., 3:4] / 255.0 * a
    reg = f[ya:yb, xa:xb]
    reg[:] = reg * (1 - al) + sp[..., :3] * al

def persp(spr, ang, s=1.0):
    """rotate sprite around vertical axis by ang degrees (perspective) and scale"""
    h, w = spr.shape[:2]; a = math.radians(ang); f = 1400.0
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * math.cos(a), x * math.sin(a); k = f / (f + Z)
        pts.append((X * k * s, y * k * s))
    pts = np.float32(pts); mn = pts.min(0); pts -= mn - 10
    ow, oh = int(pts[:, 0].max() + 10), int(pts[:, 1].max() + 10)
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), pts)
    return cv2.warpPerspective(spr, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

