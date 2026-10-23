"""Holographic unboxing style: black stage, spotlight, floor reflection, rainbow-foil text, 3D box swing, card fan, glints."""
import sys, os, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
VO = 0.5
CFG = {
    'ygo': dict(TOTAL=15.6, T_GAME=0.88, T_PROD=2.84, T_NAME=3.14, T_F1=5.56, T_F2=6.61, T_F2b=8.35, T_PRICE=10.24, T_CTA=12.42,
                game='YU-GI-OH!', hook='تبي ألترا رير في كل باك؟', big='ULTRA RARE', label='YU-GI-OH! BOOSTER BOX', name=['MAGNIFICENT', 'MONSTERS'], n1=3, cap1='باكات في البوكس', n2=15, cap2='ULTRA RARE',
                extra='+3 SECRET RARE', price='179', seed=5),
}[KEY]
globals().update({k: v for k, v in CFG.items() if k.startswith('T')})
TOTAL = CFG['TOTAL']; rng = np.random.default_rng(CFG['seed'])
FD = '/home/claude/fonts/'
def FA(s): return ImageFont.truetype(FD + 'font_anton.ttf', s)
def FC(s, w=b'Black'):
    f = ImageFont.truetype(FD + 'font_cairo.ttf', s); f.set_variation_by_name(w); return f

def fit(spr, maxw=980):
    h, w = spr.shape[:2]
    return spr if w <= maxw else cv2.resize(spr, (maxw, int(h * maxw / w)), interpolation=cv2.INTER_AREA)

# ---------- holo text: store mask + outline, fill per frame ----------
class Holo:
    def __init__(self, s, font, stroke=6, maxw=980):
        d0 = ImageDraw.Draw(Image.new('L', (10, 10))); bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
        pad = 50; w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad; ox, oy = pad - bb[0], pad - bb[1]
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((ox, oy), s, font=font, fill=255)
        sm = Image.new('L', (w, h), 0); ImageDraw.Draw(sm).text((ox, oy), s, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
        gl = sm.filter(ImageFilter.GaussianBlur(22))
        k = min(1, maxw / w)
        if k < 1: m, sm, gl = [im.resize((int(w * k), int(h * k)), Image.LANCZOS) for im in (m, sm, gl)]
        self.m = np.asarray(m, np.float32)[..., None] / 255; self.sm = np.asarray(sm, np.float32)[..., None] / 255; self.gl = np.asarray(gl, np.float32)[..., None] / 255
        h, w = self.m.shape[:2]; ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); self.u = (xs * .8 + ys * 1.2) / (w + h)
        self.v = ys / h
    def sprite(self, t, glow=(255, 90, 200)):
        hue = (self.u * 1.6 + t * .35) % 1
        rb = np.stack([128 + 127 * np.cos(2 * np.pi * (hue + o)) for o in (.66, .33, 0)], -1)  # BGR
        chrome = 255 * (.75 + .25 * np.cos(self.v * 9 + t * 2))[..., None]
        fill = rb * .55 + chrome * .45
        band = np.exp(-((self.u - ((t * .45) % 1.6 - .3)) / .05) ** 2)[..., None]
        fill = np.clip(fill + 255 * band * .8, 0, 255)
        out = np.zeros(self.m.shape[:2] + (4,), np.float32)
        g = np.array(glow[::-1], np.float32)
        out[..., :3] = g * self.gl; a = np.clip(self.gl * 1.3, 0, 1)
        out[..., :3] = out[..., :3] * (1 - self.sm) + 20 * self.sm; a = np.maximum(a, self.sm)  # dark outline
        out[..., :3] = out[..., :3] * (1 - self.m) + fill * self.m
        out[..., 3:4] = a * 255
        return out.astype(np.uint8)

def white_text(s, font, glow=(150, 120, 255), fill=WHITE):
    return text_sprite(s, font, fill=fill, glow=glow, glow_r=20, shadow=True)

def foil_frame(im, w, r=24):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS); im = rounded(im, r)
    pad = 14; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    # rainbow foil border
    ys, xs = np.mgrid[0:c.height, 0:c.width]; hue = ((xs + ys) / (c.width + c.height) * 2) % 1
    rgb = np.stack([128 + 127 * np.cos(2 * np.pi * (hue + o)) for o in (0, .33, .66)], -1).astype(np.uint8)
    fo = Image.fromarray(rgb, 'RGB').convert('RGBA'); m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c.width - 1, c.height - 1), r + pad, fill=255); fo.putalpha(m)
    c = Image.alpha_composite(c, fo); c.alpha_composite(im, (pad, pad)); return to_bgra(c)

logo = Image.open('/home/claude/oh/fetch/bn_ohlogo.png').convert('RGBA')
def logo_spr(w):
    l = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    g = Image.new('RGBA', (l.width + 100, l.height + 100), (0, 0, 0, 0)); gl = Image.new('RGBA', g.size, VIOLET + (0,))
    m = Image.new('L', g.size, 0); m.paste(l.getchannel('A'), (50, 50)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(20)))
    g = Image.alpha_composite(g, gl); g.alpha_composite(l, (50, 50)); return to_bgra(g)
LOGO_BIG, LOGO_MID, LOGO_WM = logo_spr(560), logo_spr(440), logo_spr(150)

prod = Image.open(D + 'main.png').convert('RGB')
BOX = foil_frame(prod, 640); BOX_SM = foil_frame(prod, 300, r=16)
alt = Image.open(D + 'alt.png').convert('RGB')
CARD = foil_frame(alt.crop((60, 0, alt.width - 60, int(alt.height * .64))).resize((300, 420)), 300, r=16)  # card-shaped crop of the product art
# generic foil pack silhouettes (no branding)
def pack_spr(hshift):
    w, h = 230, 380; ys, xs = np.mgrid[0:h, 0:w]; hue = ((xs * .6 + ys) / (w + h) * 1.5 + hshift) % 1
    rgb = np.stack([110 + 100 * np.cos(2 * np.pi * (hue + o)) for o in (0, .33, .66)], -1)
    rgb = rgb * (.55 + .45 * (np.cos(xs / w * 3.1 - 1.2)[..., None]))
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB').convert('RGBA'); d = ImageDraw.Draw(im)
    for y0 in (0, h - 26):  # crimped seals
        for x in range(0, w, 12): d.polygon([(x, y0), (x + 6, y0 + 26), (x + 12, y0)], fill=(230, 230, 245, 255))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rectangle((0, 0, w, h), fill=255); im.putalpha(m)
    return to_bgra(im)
PACKS = [pack_spr(i * .23) for i in range(3)]

H_GAME = Holo(CFG['big'], FA(230), stroke=8)
H_N1 = Holo(str(CFG['n1']), FA(520), stroke=10); H_N2 = {n: Holo(str(n), FA(400), stroke=10) for n in range(1, CFG['n2'] + 1)}
H_PRICE = Holo(CFG['price'], FA(420), stroke=10)
H_NAME = [Holo(CFG['name'][0], FA(150), stroke=6), Holo(CFG['name'][1], FA(170), stroke=6)]
S = dict(
    ya=white_text(CFG['hook'], FC(86)), label=pill(CFG['label'], FA(52), (40, 30, 80), border=(180, 160, 255, 255)),
    cap1=white_text(CFG['cap1'], FC(96)), cap2=pill(CFG['cap2'], FA(66), (30, 20, 60), border=(255, 120, 220, 255)),
    extra=pill(CFG['extra'], FA(60), (255, 61, 154)), sar=white_text('ريال', FC(120)),
    stock=pill('متوفر الآن', FC(54, b'Bold'), (20, 16, 40), border=(56, 225, 255, 255)),
    order=white_text('اطلبه الحين', FC(140)), url=pill('otakkuhaveen.com', FA(54), (139, 92, 246)),
)
H_SM = Holo(CFG['game'], FA(80), stroke=4)

# ---------- stage background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def radial(cx, cy, rx, ry): return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))[..., None]
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (22, 8, 10)  # BGR deep navy-black
SPOTL = radial(W / 2, H * .38, 520, 900) * np.array((120, 50, 70), np.float32)
FLOOR = (yy > H * .66)[..., None] * radial(W / 2, H * .70, 600, 120) * np.array((180, 90, 120), np.float32)
CONE = np.clip(1 - np.abs(xx - W / 2) / (120 + (yy / H) * 520), 0, 1)[..., None] * (yy < H * .7)[..., None] * np.array((60, 30, 40), np.float32)
DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4), rng.uniform(0, 6.28), rng.uniform(8, 30)) for _ in range(90)]
def background(t, glow=0):
    hue = ((xx + yy) / (W + H) * .8 + t * .05) % 1
    f = BASE + SPOTL * (1 + .3 * glow) + CONE * (1 + glow) + FLOOR
    sweep = np.exp(-(((xx * .7 + yy * .3) - ((t * 500) % 2600 - 600)) / 160) ** 2)[..., None]
    f += sweep * np.stack([40 + 30 * np.cos(2 * np.pi * (hue + o)) for o in (.66, .33, 0)], -1) * .5
    f = np.clip(f, 0, 255).astype(np.uint8)
    for x, y, r, ph, vy in DUST:
        a = .35 + .35 * math.sin(t * 2 + ph); cv2.circle(f, (int(x + 10 * math.sin(t + ph)), int((y - vy * t) % H)), int(r), (230, 200, 220), -1, cv2.LINE_AA) if a > .5 else None
    return f.astype(np.float32)

def reflect(f, spr, cx, cy_bottom, s=1.0, a=.28):
    """mirror sprite below floor line"""
    if s != 1: spr = cv2.resize(spr, (int(spr.shape[1] * s), int(spr.shape[0] * s)))
    r = spr[::-1].copy(); h = r.shape[0]; fade = np.linspace(1, 0, h)[:, None] ** 1.5
    r[..., 3] = (r[..., 3] * fade).astype(np.uint8)
    blit(f, r, cx, cy_bottom + h / 2, 1, a)

def glint(f, x, y, size, a):
    if a <= .02: return
    fx = np.clip(f, 0, 255).astype(np.uint8); ov = fx.copy()
    for ang, L in ((0, size), (90, size), (45, size * .45), (135, size * .45)):
        dx, dy = math.cos(math.radians(ang)) * L, math.sin(math.radians(ang)) * L
        cv2.line(ov, (int(x - dx), int(y - dy)), (int(x + dx), int(y + dy)), (255, 255, 255), 3, cv2.LINE_AA)
    cv2.circle(ov, (int(x), int(y)), int(size * .12), (255, 255, 255), -1, cv2.LINE_AA)
    cv2.addWeighted(ov, a, fx, 1 - a, 0, fx); f[:] = fx

def holo_sweep(spr, p):
    h, w = spr.shape[:2]; ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); u = (xs + ys * .6) / (w + h * .6)
    band = np.exp(-((u - p) / .07) ** 2)[..., None]; hue = (u * 3 + p) % 1
    rb = np.stack([128 + 127 * np.cos(2 * np.pi * (hue + o)) for o in (0, .33, .66)], -1)
    out = spr.copy(); m = (spr[..., 3:4] > 0)
    out[..., :3] = np.clip(spr[..., :3] * (1 - .35 * band) + (rb * .5 + 140) * band * m, 0, 255).astype(np.uint8); return out

def flash(t):
    return sum(env(t, tc, .16) * a for tc, a in ((0.05, .8), (T_GAME, .6), (T_PROD, .35), (T_F1, .3), (T_F2, .3), (T_PRICE + .02, .7), (T_CTA, .35)))

def render(t):
    gl = env(t, T_GAME, .6) + env(t, T_PRICE, .8)
    f = background(t, gl)
    zoom = 1 + .06 * env(t, T_GAME, .4) + .08 * env(t, T_PRICE + .02, .5)
    # intro: logo scan reveal
    if t < VO + .2:
        p = eo(t / .35); out = eo((t - VO) / .2)
        spr = LOGO_BIG.copy(); h = spr.shape[0]; cut = int(h * p); spr[cut:, :, 3] = 0
        blit(f, spr, W / 2, H * .42, 1 + .2 * (1 - p), 1 - out)
        if p < 1: f[int(H * .42 - h / 2 + cut) - 2:int(H * .42 - h / 2 + cut) + 2] = 255
    if VO <= t < T_CTA: blit(f, LOGO_WM, 120, 110, 1, min(1, (t - VO) / .2) * .9)
    if VO <= t < T_PROD:
        lt = t - VO
        blit(f, S['ya'], W / 2, H * .30 + 40 * (1 - eo(lt / .3)), 1, eo(lt / .25))
        if t > T_GAME:
            k = t - T_GAME; spr = H_GAME.sprite(t)
            blit(f, spr, W / 2, H * .42, 1 + .9 * (1 - eo(k / .2)), min(1, k / .06))
            reflect(f, spr, W / 2, H * .42 + spr.shape[0] / 2 - 30, 1, .22)
            glint(f, W / 2 + 330, H * .38, 90 * env(t, T_GAME + .25, .5) * 2, env(t, T_GAME + .25, .5))
    if T_PROD <= t < T_F1:
        lt = t - T_PROD
        ang = 80 * (1 - eo(lt / .7)) + 18 * math.sin(lt * 1.6) * eo(lt / .7)
        spr = persp(BOX, ang, .7 + .3 * ebk(lt / .6))
        if .6 < lt < 1.6: spr = holo_sweep(spr, (lt - .6) / 1.0 * 1.4 - .2)
        cy = H * .40 + 10 * math.sin(t * 2) - 300 * (1 - eo(lt / .4))
        blit(f, spr, W / 2, cy, 1, eo(lt / .2)); reflect(f, spr, W / 2, cy + spr.shape[0] / 2 - 4, 1, .25)
        if lt > .3: blit(f, S['label'], W / 2, H * .10, ebk((lt - .3) / .3), 1)
        if t > T_NAME:
            for i, hn in enumerate(H_NAME):
                k = t - T_NAME - i * .15
                if k > 0: blit(f, hn.sprite(t + i), W / 2, H * (.76 + .085 * i), 1 + .3 * (1 - eo(k / .2)), min(1, k / .1))
    if T_F1 <= t < T_F2:
        lt = t - T_F1
        blit(f, H_N1.sprite(t), W / 2, H * .27, 1 + .8 * (1 - eo(lt / .18)), min(1, lt / .06))
        for i, pk in enumerate(PACKS):
            k = lt - .12 - i * .1; x = W / 2 + (i - 1) * 270
            if k > 0:
                y = H * .60 - 500 * (1 - eo(k / .35)); spr = persp(pk, 25 * math.sin(t * 2 + i), 1)
                blit(f, spr, x, y + 10 * math.sin(t * 3 + i), 1, min(1, k / .1), (i - 1) * 8)
                glint(f, x + 60, y - 120, 60, env(t, T_F1 + .5 + i * .1, .4))
        if lt > .35: blit(f, S['cap1'], W / 2, H * .82, ebk((lt - .35) / .3), 1)
    if T_F2 <= t < T_PRICE:
        lt = t - T_F2; n = max(1, min(CFG['n2'], int(1 + (CFG['n2'] - 1) * eo(lt / .55))))
        blit(f, H_N2[n].sprite(t), W / 2, H * .20, 1 + .15 * env(t, T_F2 + .55, .25), 1)
        if lt > .4: blit(f, S['cap2'], W / 2, H * .33, ebk((lt - .4) / .3), 1)
        for j in [0, 4, 1, 3, 2]:
            i = j - 2; k = ebk((lt - .15 - abs(i) * .06) / .5)
            spr = holo_sweep(CARD, ((t * .5 + j * .15) % 1.4) - .2)
            blit(f, spr, W / 2 + i * 170 * k, H * .58 + abs(i) ** 1.5 * 30 * k + 700 * (1 - eo((lt - abs(i) * .06) / .4)), .95 + (.1 if j == 2 else 0), 1, -i * 10 * k)
        if t > T_F2b:
            k = t - T_F2b; blit(f, S['extra'], W / 2, H * .82, ebk(k / .3), 1)
            for i in range(3): glint(f, W / 2 + (i - 1) * 260, H * .76 - 40 * i % 2, 70, env(t, T_F2b + .1 + i * .12, .45))
    if T_PRICE <= t < T_CTA:
        lt = t - T_PRICE
        blit(f, BOX_SM, W / 2, H * .22 + 8 * math.sin(t * 2), ebk(lt / .4), 1, 3 * math.sin(t * 1.4))
        spr = H_PRICE.sprite(t * 1.5)
        blit(f, spr, W / 2, H * .50, 1 + 1.2 * (1 - eo(lt / .16)), min(1, lt / .05))
        reflect(f, spr, W / 2, H * .50 + spr.shape[0] / 2 - 40, 1, .2)
        if lt > .45: blit(f, S['sar'], W / 2, H * .70, ebk((lt - .45) / .3), 1)
        if lt > 1.0: blit(f, S['stock'], W / 2, H * .79, ebk((lt - 1.0) / .3), 1)
        for i in range(5): glint(f, W / 2 + math.cos(i * 1.3) * 380, H * .5 + math.sin(i * 2.1) * 200, 70, env(t, T_PRICE + .1 + i * .13, .4))
    if t >= T_CTA:
        lt = t - T_CTA
        blit(f, LOGO_MID, W / 2, H * .27, ebk(lt / .4), 1)
        if lt > .2: blit(f, S['order'], W / 2, H * .47, ebk((lt - .2) / .3), 1)
        if lt > .45: blit(f, S['url'], W / 2, H * .58, ebk((lt - .45) / .3) * (1 + .03 * math.sin(t * 6)), 1)
        if lt > .65: blit(f, H_SM.sprite(t), W / 2, H * .67, ebk((lt - .65) / .3), 1)
        if lt > .65:
            cy = H * .80 + 20 * (1 - eo((lt - .65) / .4)); blit(f, BOX_SM, W / 2, cy, .8 * ebk((lt - .65) / .4), 1)
    f = np.clip(f, 0, 255)
    fl = flash(t)
    if fl > .01: f = f + (255 - f) * min(1, fl)
    f = f.astype(np.uint8)
    if zoom > 1.001:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, zoom); f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    if t > TOTAL - .4: f = (f * max(0, (TOTAL - t) / .4)).astype(np.uint8)
    return f

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite(D + 'sth.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            fa = render(i / FPS).astype(np.uint16); fb = render(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
