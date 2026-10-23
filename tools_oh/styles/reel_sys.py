"""Game-system HUD style: dark grid, glowing cyan UI windows with headers, typewriter text, stat bars, glitch transitions."""
import sys, os, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
VO = 0.5
BLUE = (70, 170, 255); CY = (90, 230, 255)
CFG = {
    'sl': dict(TOTAL=15.1, T_GAME=1.86, T_PROD=3.14, T_NAME=4.1, T_F1=5.82, T_F1b=6.38, T_F2=7.18, T_PRICE=9.34, T_CTA=11.62,
               game='SOLO LEVELING', name=['SWORD SET'], stats=[('خفيفة', .35), ('متينة', .92)], uses=['مثالية للعرض', 'وللكوسبلاي'],
               price='450', seed=13),
}[KEY]
globals().update({k: v for k, v in CFG.items() if k.startswith('T')})
TOTAL = CFG['TOTAL']; rng = np.random.default_rng(CFG['seed'])
FD = '/home/claude/fonts/'
def FA(s): return ImageFont.truetype(FD + 'font_anton.ttf', s)
def FC(s, w=b'Bold'):
    f = ImageFont.truetype(FD + 'font_cairo.ttf', s); f.set_variation_by_name(w); return f
def G(s, font, fill=WHITE, glow=BLUE, gr=16): return text_sprite(s, font, fill=fill, glow=glow, glow_r=gr, shadow=False)

def window(w, h, header):
    """HUD window sprite (BGRA)"""
    M = 50; im = Image.new('RGBA', (w + 2 * M, h + 2 * M), (0, 0, 0, 0))
    gl = Image.new('RGBA', im.size, BLUE + (0,)); m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rectangle((M - 4, M - 4, M + w + 4, M + h + 4), outline=255, width=8); gl.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im = Image.alpha_composite(im, gl); d = ImageDraw.Draw(im)
    d.rectangle((M, M, M + w, M + h), fill=(8, 18, 40, 205), outline=CY + (255,), width=3)
    for (x, y, sx, sy) in ((M, M, 1, 1), (M + w, M, -1, 1), (M, M + h, 1, -1), (M + w, M + h, -1, -1)):
        d.line((x, y, x + 46 * sx, y), fill=WHITE + (255,), width=7); d.line((x, y, x, y + 46 * sy), fill=WHITE + (255,), width=7)
    f = FA(44); bb = d.textbbox((0, 0), header, font=f); tw = bb[2] - bb[0]
    d.rectangle((M + w / 2 - tw / 2 - 30, M + 20, M + w / 2 + tw / 2 + 30, M + 88), fill=(20, 60, 120, 230), outline=CY + (255,), width=2)
    d.text((M + w / 2 - tw / 2 - bb[0], M + 54 - (bb[3] + bb[1]) / 2), header, font=f, fill=WHITE)
    d.line((M + 30, M + 110, M + w - 30, M + 110), fill=CY + (160,), width=2)
    return to_bgra(im)

def item_img(im, w):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    # put white-bg product on a soft light card so it reads on dark UI
    c = Image.new('RGBA', (im.width + 16, im.height + 16), CY + (255,)); c.paste(im, (8, 8)); return to_bgra(c)

logo = Image.open('/home/claude/oh/fetch/bn_ohlogo.png').convert('RGBA')
def logo_spr(w):
    l = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    g = Image.new('RGBA', (l.width + 100, l.height + 100), (0, 0, 0, 0)); gl = Image.new('RGBA', g.size, BLUE + (0,))
    m = Image.new('L', g.size, 0); m.paste(l.getchannel('A'), (50, 50)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(22)))
    g = Image.alpha_composite(g, gl); g.alpha_composite(l, (50, 50)); return to_bgra(g)
LOGO_BIG, LOGO_MID, LOGO_WM = logo_spr(540), logo_spr(430), logo_spr(140)
prod = Image.open(D + 'main.png').convert('RGB'); ITEM = item_img(prod, 640); ITEM_SM = item_img(prod, 300)
alt = Image.open(D + 'alt.png').convert('RGB'); ALT = item_img(alt, 420)

W_NOTE = window(880, 560, '[ NOTIFICATION ]'); W_ITEM = window(900, 1040, '[ ITEM ACQUIRED ]')
W_STAT = window(900, 1180, '[ STATUS ]'); W_SHOP = window(860, 1000, '[ SHOP ]')
S = dict(ya=G('حس إنك صياد من رتبة', FC(80)), game=G('S-RANK', FA(190), glow=CY, gr=28),
         name=G(CFG['name'][0], FA(110), glow=CY), gname=G(CFG['game'], FA(64), fill=(200, 235, 255)),
         stats=[G(s, FC(84)) for s, _ in CFG['stats']], uses=[G(u, FC(80)) for u in CFG['uses']],
         price=G(CFG['price'], FA(330), glow=CY, gr=30), sar=G('ريال', FC(100)),
         stock=pill('متوفر الآن', FC(52), (10, 40, 80), border=CY + (255,)),
         order=G('اطلبه الحين', FC(130, b'Black'), glow=PINK), url=pill('otakkuhaveen.com', FA(54), (20, 60, 130), border=CY + (255,)),
         lvl=G('LEVEL UP!', FA(90), fill=CY, glow=BLUE), check=G('✓', FC(80), fill=CY))
MAXSTAT = [G(f'{int(v * 100)}', FA(70), fill=CY) for _, v in CFG['stats']]

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (24, 10, 4)
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
GLOW = radial(W / 2, H * .45, 700) * np.array(BLUE[::-1], np.float32) * .35 + radial(W, 0, 600) * np.array(VIOLET[::-1], np.float32) * .3
SCAN = (1 - .12 * ((yy.astype(np.int32) // 3) % 2))[..., None]
HEX = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(6, 18), rng.uniform(0, 6.28), rng.uniform(15, 50)) for _ in range(40)]
def background(t):
    f = BASE + GLOW * (1 + .15 * math.sin(t * 3))
    off = (t * 60) % 90
    gx = np.abs(((xx + 0) % 90) - 45) > 43.5; gy = np.abs(((yy + off) % 90) - 45) > 43.5
    f += (gx | gy)[..., None] * np.array((90, 50, 10), np.float32) * (.35 + .65 * (yy / H))[..., None]
    f = np.clip(f, 0, 255).astype(np.uint8)
    for x, y, r, ph, vy in HEX:
        yy_ = (y - vy * t) % H; pts = [(x + r * math.cos(ph + t + k * math.pi / 3), yy_ + r * math.sin(ph + t + k * math.pi / 3)) for k in range(6)]
        cv2.polylines(f, [np.int32(pts)], True, (255, 200, 90), 1, cv2.LINE_AA)
    return f.astype(np.float32)

def typed(spr, p):  # typewriter: reveal right->left for Arabic, left->right for latin handled by caller
    if p >= 1: return spr
    out = spr.copy(); w = spr.shape[1]; c = int(w * max(0, p)); out[:, :w - c, 3] = 0; return out
def typed_ltr(spr, p):
    if p >= 1: return spr
    out = spr.copy(); w = spr.shape[1]; c = int(w * max(0, p)); out[:, c:, 3] = 0; return out
def win_open(spr, p):  # window opens vertically from center line
    if p >= 1: return spr
    h = spr.shape[0]; k = max(.02, eo(p)); out = spr.copy(); cut = int(h * (1 - k) / 2)
    out[:cut, :, 3] = 0; out[h - cut:, :, 3] = 0; return out

def bar(f, x, y, w, h, p, a=1):
    fx = np.clip(f, 0, 255).astype(np.uint8); ov = fx.copy()
    cv2.rectangle(ov, (int(x), int(y)), (int(x + w), int(y + h)), (120, 60, 20), -1)
    cv2.rectangle(ov, (int(x), int(y)), (int(x + w * p), int(y + h)), CY[::-1], -1)
    cv2.rectangle(ov, (int(x), int(y)), (int(x + w), int(y + h)), (255, 230, 150), 2, cv2.LINE_AA)
    cv2.addWeighted(ov, a, fx, 1 - a, 0, fx); f[:] = fx

def glitch(f, amt, t):
    if amt <= .02: return f
    r = np.random.default_rng(int(t * 60)); out = f.copy()
    for _ in range(int(8 * amt) + 2):
        y0 = int(r.uniform(0, H - 80)); hh = int(r.uniform(10, 90)); dx = int(r.uniform(-80, 80) * amt)
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], dx, axis=1)
    sh = int(14 * amt); out[..., 2] = np.roll(out[..., 2], sh, 1); out[..., 0] = np.roll(out[..., 0], -sh, 1)
    return out

def render(t):
    f = background(t)
    if t < VO + .2:
        p = eo(t / .3); out = eo((t - VO) / .2)
        blit(f, LOGO_BIG, W / 2, H * .45, .9 + .1 * p, p * (1 - out))
    if VO <= t < T_CTA: blit(f, LOGO_WM, 115, 100, 1, .9)
    if VO <= t < T_PROD:
        lt = t - VO
        blit(f, win_open(W_NOTE, lt / .3), W / 2, H * .42, 1, 1)
        if lt > .2: blit(f, typed(S['ya'], (lt - .2) / .3), W / 2, H * .42 - 90, 1, 1)
        if t > T_GAME:
            k = t - T_GAME
            blit(f, typed_ltr(S['game'], k / .45), W / 2, H * .42 + 80, 1 + .25 * env(t, T_GAME + .45, .25), 1)
    if T_PROD <= t < T_F1:
        lt = t - T_PROD
        blit(f, win_open(W_ITEM, lt / .3), W / 2, H * .47, 1, 1)
        if lt > .2:
            sp = ITEM.copy()
            if .5 < lt < 1.3:  # scan line over the item
                y = int(sp.shape[0] * (lt - .5) / .8); sp[max(0, y - 4):y + 4, :, :3] = (255, 240, 160)
            blit(f, sp, W / 2, H * .45, .2 + .8 * eo((lt - .2) / .3), 1)
        if t > T_NAME:
            k = t - T_NAME
            blit(f, typed_ltr(S['gname'], k / .3), W / 2, H * .69, 1, 1)
            blit(f, typed_ltr(S['name'], (k - .2) / .3), W / 2, H * .745, 1, 1)
        if lt > .3: blit(f, S['lvl'], W / 2, H * .17 - 30 * eo((lt - .3) / .4), 1, env(t, T_PROD + .3, 1.2) * 1.2 if lt < 1.5 else 0)
    if T_F1 <= t < T_PRICE:
        lt = t - T_F1
        blit(f, win_open(W_STAT, lt / .3), W / 2, H * .47, 1, 1)
        blit(f, ALT, W / 2 + 250, H * .70, .42, eo((lt - .1) / .3), -12)
        for i, (tc, (sname, val)) in enumerate(zip([T_F1, T_F1b], CFG['stats'])):
            if t > tc:
                k = t - tc; y = H * (.30 + .08 * i)
                blit(f, typed(S['stats'][i], k / .25), W / 2 + 270, y, 1, 1)
        for i, (tc, (sname, val)) in enumerate(zip([T_F1, T_F1b], CFG['stats'])):
            pass
        # bars for each stat (lightness shown as weight bar = low, durability = high)
        if t > T_F1: bar(f, 140, H * .30 - 11, 480, 22, 1.0 * eo((t - T_F1 - .15) / .5))
        if t > T_F1b: bar(f, 140, H * .38 - 11, 480, 22, 1.0 * eo((t - T_F1b - .15) / .5))
        if t > T_F2:
            for i, u in enumerate(S['uses']):
                k = t - T_F2 - i * .55
                if k > 0:
                    y = H * (.50 + .075 * i)
                    blit(f, typed(u, k / .3), W / 2 + 40, y, 1, 1)
                    if k > .2:
                        q = eo((k - .2) / .25); fx = np.clip(f, 0, 255).astype(np.uint8); cx_, cy_ = int(W / 2 - 300), int(y)
                        cv2.line(fx, (cx_ - 26, cy_), (cx_ - 8, cy_ + 20), CY[::-1], 9, cv2.LINE_AA)
                        if q > .4: cv2.line(fx, (cx_ - 8, cy_ + 20), (int(cx_ - 8 + 40 * q), int(cy_ + 20 - 44 * q)), CY[::-1], 9, cv2.LINE_AA)
                        f[:] = fx
    if T_PRICE <= t < T_CTA:
        lt = t - T_PRICE
        blit(f, win_open(W_SHOP, lt / .25), W / 2, H * .50, 1, 1)
        blit(f, ITEM_SM, W / 2, H * .385, .8 * ebk((lt - .1) / .35), 1)
        if lt > .05: blit(f, S['price'], W / 2, H * .535, 1 + 1.0 * (1 - eo((lt - .05) / .16)), min(1, (lt - .05) / .05))
        if lt > .45: blit(f, S['sar'], W / 2, H * .645, ebk((lt - .45) / .3), 1)
        if lt > 1.0: blit(f, S['stock'], W / 2, H * .705, ebk((lt - 1.0) / .3), 1)
    if t >= T_CTA:
        lt = t - T_CTA
        blit(f, LOGO_MID, W / 2, H * .27, ebk(lt / .4), 1)
        if lt > .2: blit(f, typed(S['order'], (lt - .2) / .35), W / 2, H * .46, 1, 1)
        if lt > .5: blit(f, S['url'], W / 2, H * .56, ebk((lt - .5) / .3), 1)
        if lt > .7: blit(f, S['gname'], W / 2, H * .64, ebk((lt - .7) / .3), 1)
        if lt > .7: blit(f, ITEM_SM, W / 2, H * .77, .8 * ebk((lt - .7) / .4), 1)
    f = np.clip(f * SCAN, 0, 255)
    g = max([env(t, tc - .06, .22) for tc in (T_GAME, T_PROD, T_F1, T_PRICE, T_CTA)] + [0])
    f = glitch(f, g, t)
    fl = env(t, T_PRICE, .15) * .5 + env(t, T_GAME, .12) * .4
    if fl > .01: f = f + (np.array((255, 240, 200), np.float32) - f) * fl
    f = np.clip(f, 0, 255).astype(np.uint8)
    if t > TOTAL - .4: f = (f * max(0, (TOTAL - t) / .4)).astype(np.uint8)
    return f

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite(D + 'sts.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            fa = render(i / FPS).astype(np.uint16); fb = render(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
