"""Dark cinematic style: letterbox, smoke, crimson/violet neon rim light, film grain, slow push-ins, lower-third text, filmstrip carousel."""
import sys, os, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
VO = 0.5
RED = (230, 30, 70)
CFG = {
    'dn': dict(TOTAL=14.4, T_GAME=0.6, T_PROD=3.14, T_NAME=3.5, T_F1=7.98, T_F1b=8.5, T_F2=4.26, T_PRICE=9.22, T_CTA=10.9,
               game=['DEATH', 'NOTE'], hook=['فريق إل؟', 'هذا لك!'], name=['DEATH NOTE PULLOVER', 'ANIME MERCH'], caps=['مقاسات لين XXXL', 'دافي للبرد'], cap2='ألوان كثيرة',
               price='200', seed=13),
    'suk': dict(TOTAL=15.1, T_GAME=0.58, T_PROD=2.5, T_NAME=2.82, T_F1=4.66, T_F1b=6.18, T_F2=8.02, T_PRICE=9.94, T_CTA=11.62,
                game=['JUJUTSU', 'KAISEN'], hook=['ملك اللعنات', 'صار هودي!'], name=['SUKUNA HOODIE', 'JUJUTSU KAISEN'], caps=['خامة عالية الجودة', 'دافي للأيام الباردة'], cap2='ألوان متعددة',
                price='200', seed=9),
    'akaza': dict(TOTAL=14.2, T_GAME=0.64, T_PROD=3.14, T_NAME=3.46, T_F2=5.14, T_C1=7.14, T_F1=7.14, T_F1b=7.6, T_PRICE=8.98, T_CTA=10.74,
                game=['DEMON', 'SLAYER'], hook=['الرتبة العليا الثالثة', 'صارت هودي!'], name=['AKAZA HOODIE', 'DEMON SLAYER'], caps=['', 'دافي للأيام الباردة'], cap2='ألوان كثيرة تختار منها',
                price='200', seed=33, hook_fs=98),
}[KEY]
globals().update({k: v for k, v in CFG.items() if k.startswith('T')})
TOTAL = CFG['TOTAL']; rng = np.random.default_rng(CFG['seed'])
FD = '/home/claude/fonts/'
def FA(s): return ImageFont.truetype(FD + 'font_anton.ttf', s)
def FC(s, w=b'Bold'):
    f = ImageFont.truetype(FD + 'font_cairo.ttf', s); f.set_variation_by_name(w); return f
def T(s, font, fill=WHITE, glow=RED, gr=26, track=0):
    if track:  # letter-spaced latin
        parts = [text_sprite(c, font, fill=fill, glow=None, shadow=False, pad=10) for c in s]
        h = max(p.shape[0] for p in parts); w = sum(p.shape[1] for p in parts) + track * (len(parts) - 1)
        out = np.zeros((h + 60, w + 60, 4), np.uint8); x = 30
        for p in parts:
            out[30 + (h - p.shape[0]):30 + h, x:x + p.shape[1]] = np.maximum(out[30 + (h - p.shape[0]):30 + h, x:x + p.shape[1]], p); x += p.shape[1] + track
        im = Image.fromarray(out[..., [2, 1, 0, 3]], 'RGBA')
        g = Image.new('RGBA', im.size, glow + (0,)); g.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(gr)))
        return to_bgra(Image.alpha_composite(g, im))
    return text_sprite(s, font, fill=fill, glow=glow, glow_r=gr, shadow=True)

def rim(im, w, col=RED):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS); im = rounded(im, 10)
    pad = 70; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    g = Image.new('RGBA', c.size, col + (0,)); m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((pad - 6, pad - 6, pad + im.width + 6, pad + im.height + 6), 14, fill=255)
    g.putalpha(m.filter(ImageFilter.GaussianBlur(30))); c = Image.alpha_composite(c, g); c.alpha_composite(im, (pad, pad)); return to_bgra(c)

logo = Image.open('/home/claude/oh/fetch/bn_ohlogo.png').convert('RGBA')
def logo_spr(w):
    l = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    g = Image.new('RGBA', (l.width + 100, l.height + 100), (0, 0, 0, 0)); gl = Image.new('RGBA', g.size, RED + (0,))
    m = Image.new('L', g.size, 0); m.paste(l.getchannel('A'), (50, 50)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(24)))
    g = Image.alpha_composite(g, gl); g.alpha_composite(l, (50, 50)); return to_bgra(g)
LOGO_BIG, LOGO_MID, LOGO_WM = logo_spr(520), logo_spr(420), logo_spr(140)
prod = Image.open(D + 'main.png').convert('RGB')
PROD_BIG = rim(prod, 900); PROD = rim(prod, 760); PROD_SM = rim(prod, 330)
STRIP = [rim(Image.open(D + f'c{i}.png').convert('RGB'), 400, col=(c if c else RED)) for i, c in zip((8, 4, 3, 1, 5, 7), (RED, RED, VIOLET, VIOLET, PINK, (60, 110, 255)))]
T_C1 = CFG.get('T_C1', 5.82)
S = dict(
    size=T('المقاسات', FC(92)), sizes=T('S · M · L · XL · XXL · XXXL', FA(62), fill=WHITE, glow=VIOLET, gr=16),
    ya=np.zeros((4, 4, 4), np.uint8),
    game=[T(g, FC(CFG.get('hook_fs', 160), b'Black')) for g in CFG['hook']],
    name0=(lambda sp: cv2.resize(sp, (960, int(sp.shape[0] * 960 / sp.shape[1])), interpolation=cv2.INTER_AREA) if sp.shape[1] > 960 else sp)(T(CFG['name'][0], FA(130), track=6)), name1=T(CFG['name'][1], FA(70), fill=(240, 220, 230), glow=VIOLET, track=26),
    caps=[T(c or ' ', FC(92)) for c in CFG['caps']], cap2=T(CFG['cap2'], FC(96)),
    price=T(CFG['price'], FA(380), track=10), sar=T('ريال', FC(110), glow=VIOLET),
    stock=T('متوفر الآن', FC(60, b'SemiBold'), fill=(220, 210, 230), glow=VIOLET, gr=12),
    order=T('اطلبه الحين', FC(130, b'Black')), url=T('otakkuhaveen.com', FA(66), fill=WHITE, glow=VIOLET, track=4),
    game_sm=T(CFG.get('game_sm', ' '.join(CFG['game'])), FA(64), fill=(230, 220, 235), glow=RED, gr=12, track=8),
)

# ---------- background: smoke + neon + grain ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def smoke_tex(seed, sc):
    r = np.random.default_rng(seed); acc = np.zeros((H // 4 + 200, W // 4 + 100), np.float32)
    for o in range(5):
        n = r.standard_normal((acc.shape[0] // (2 ** (4 - o)) + 2, acc.shape[1] // (2 ** (4 - o)) + 2)).astype(np.float32)
        acc += cv2.resize(n, (acc.shape[1], acc.shape[0]), interpolation=cv2.INTER_CUBIC) * (.55 ** o)
    acc = (acc - acc.min()) / (acc.max() - acc.min()); return np.clip((acc - .45) * 2.2, 0, 1)
SM1 = smoke_tex(1, 1); SM2 = smoke_tex(2, 1)
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
VIG = (1 - .75 * np.clip(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2, 0, 1))[..., None]
NEON_R = radial(W * 1.0, H * .25, 700) * np.array(RED[::-1], np.float32)
NEON_V = radial(0, H * .75, 750) * np.array(VIOLET[::-1], np.float32)
BAR = 150
def background(t, hit=0):
    o1 = int(t * 22) % 200; o2 = int(t * 14) % 100
    s1 = cv2.resize(SM1[o1:o1 + H // 4, :W // 4], (W, H)); s2 = cv2.resize(SM2[200 - o1 // 2 - 1:200 - o1 // 2 - 1 + H // 4, o2:o2 + W // 4] if False else SM2[:H // 4, o2:o2 + W // 4], (W, H))
    f = np.zeros((H, W, 3), np.float32) + (10, 6, 8)
    f += NEON_R * (.35 + .1 * math.sin(t * 1.7) + .4 * hit) * (.4 + s1[..., None])
    f += NEON_V * (.30 + .08 * math.sin(t * 1.1 + 1)) * (.4 + s2[..., None])
    f += (s1 * .5 + s2 * .5)[..., None] * 26
    return f

def grain_vig_bars(f, t, ca=0):
    if ca > .5:
        sh = int(ca); f[..., 2] = np.roll(f[..., 2], sh, 1); f[..., 0] = np.roll(f[..., 0], -sh, 1)
    f *= VIG
    g = np.random.default_rng(int(t * 30)).standard_normal((H // 2, W // 2)).astype(np.float32)
    f += cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 7
    f[:BAR] = 0; f[H - BAR:] = 0
    return f

def reveal(spr, p, rtl=False):  # wipe reveal (rtl for Arabic)
    if p >= 1: return spr
    out = spr.copy(); w = spr.shape[1]; c = int(w * max(0, p))
    if rtl: out[:, :w - c, 3] = 0; out[:, w - c:min(w, w - c + 6), :3] = 255
    else: out[:, c:, 3] = 0; out[:, max(0, c - 6):c, :3] = 255
    return out

def line(f, x0, x1, y, a, col=RED):
    if a <= .01: return
    fx = np.clip(f, 0, 255).astype(np.uint8); ov = fx.copy(); cv2.line(ov, (int(x0), int(y)), (int(x1), int(y)), col[::-1], 4, cv2.LINE_AA)
    cv2.addWeighted(ov, a, fx, 1 - a, 0, fx); f[:] = fx

def fade_cut(t):  # dip to black around cuts
    return max([env(t, tc - .12, .12) * 0 + (1 - min(1, abs(t - tc) / .12)) for tc in (T_PROD, T_F2, T_C1, T_F1, T_CTA)] + [0])

def render(t):
    hit = env(t, T_GAME, .7) + env(t, T_PRICE, .8)
    f = background(t, hit)
    if t < VO + .3:
        p = eio(t / .6); out = eio((t - VO) / .3)
        blit(f, LOGO_BIG, W / 2, H * .46, .92 + .08 * p, p * (1 - out))
    if VO <= t < T_CTA: blit(f, LOGO_WM, 120, BAR + 70, 1, min(1, (t - VO) / .4) * .85)
    if VO <= t < T_PROD:
        lt = t - VO
        blit(f, S['ya'], W / 2, H * .36, 1, eo(lt / .4) * (1 - eo((t - T_PROD + .25) / .25)))
        if t > T_GAME:
            k = t - T_GAME; push = 1 + .05 * (k / 1.4)
            for i, g in enumerate(S['game']):
                kk = k - i * .18
                if kk > 0: blit(f, reveal(g, eo(kk / .35), True), W / 2, H * (.42 + .1 * i), push, 1 - eo((t - T_PROD + .2) / .2))
            line(f, W / 2 - 330 * eo(k / .5), W / 2 + 330 * eo(k / .5), H * .62, 1)
    if T_PROD <= t < T_F2:
        lt = t - T_PROD; s = .86 + .08 * (lt / (T_F1 - T_PROD))
        blit(f, PROD_BIG, W / 2 + 40 * (1 - eo(lt / .6)), H * .42, s, eo(lt / .35))
        if t > T_NAME:
            k = t - T_NAME
            blit(f, reveal(S['name0'], eo(k / .35)), W / 2, H * .74, 1, 1)
            blit(f, S['name1'], W / 2, H * .80, 1, eo((k - .3) / .3))
            line(f, W / 2 - 260 * eo((k - .2) / .4), W / 2 + 260 * eo((k - .2) / .4), H * .775, 1)
    if T_C1 <= t < T_F1:
        lt = t - T_C1
        blit(f, PROD, W / 2 + 30 * (lt / 3), H * .36, .9 + .03 * lt / 3, eo(lt / .3))
        blit(f, reveal(S['size'], eo(lt / .4), True), W / 2, H * .68, 1, 1)
        blit(f, S['sizes'], W / 2, H * .76, 1, eo((lt - .35) / .3))
        line(f, W * .2, W * .2 + W * .6 * eo(lt / .5), H * .645, .9)
    if T_F1 <= t < T_PRICE:
        lt = t - T_F1
        blit(f, PROD, W / 2 - 30 * (lt / 3), H * .36, .9 + .03 * lt / 3, eo(lt / .3))
        for i, (tc, spr) in enumerate(zip([T_F1 + .05], S['caps'][1:])):
            if t > tc:
                k = t - tc; y = H * (.68 + .075 * i)
                blit(f, reveal(spr, eo(k / .4), True), W / 2, y, 1, 1)
        line(f, W * .2, W * .2 + W * .6 * eo(lt / .5), H * .645, .9)
    if T_F2 <= t < T_C1:
        lt = t - T_F2; off = -lt * 260 + 700 * (1 - eo(lt / .6))
        for i, sp in enumerate(STRIP):
            x = W / 2 + (i - 1) * 460 + off; blit(f, sp, x, H * .44 + (i % 2) * 40 - 20, .95, eo((lt - i * .05) / .3))
        if lt > .4: blit(f, reveal(S['cap2'], eo((lt - .4) / .4), True), W / 2, H * .74, 1, 1)
    if T_PRICE <= t < T_CTA:
        lt = t - T_PRICE
        blit(f, PROD_SM, W / 2, H * .26, 1, eo(lt / .3))
        blit(f, S['price'], W / 2, H * .50, 1.25 - .25 * eo(lt / .3), min(1, lt / .08))
        if lt > .45: blit(f, S['sar'], W / 2, H * .64, 1, eo((lt - .45) / .3))
        if lt > 1.0: blit(f, S['stock'], W / 2, H * .72, 1, eo((lt - 1.0) / .3))
        line(f, W / 2 - 300 * eo(lt / .4), W / 2 + 300 * eo(lt / .4), H * .585, 1)
    if t >= T_CTA:
        lt = t - T_CTA
        blit(f, LOGO_MID, W / 2, H * .30, .95 + .05 * eo(lt / .5), eo(lt / .4))
        if lt > .2: blit(f, reveal(S['order'], eo((lt - .2) / .4), True), W / 2, H * .48, 1, 1)
        if lt > .5: blit(f, S['url'], W / 2, H * .57, 1, eo((lt - .5) / .3))
        if lt > .7: blit(f, S['game_sm'], W / 2, H * .64, 1, eo((lt - .7) / .3))
        if lt > .7: blit(f, PROD_SM, W / 2, H * .76, .8, eo((lt - .7) / .4))
    fc = fade_cut(t)
    if fc > 0: f *= (1 - .85 * fc)
    fl = env(t, T_GAME, .12) * .7 + env(t, T_PRICE, .12) * .6
    if fl > .01: f = f + (np.array(RED[::-1], np.float32) * 1.1 - f) * fl
    ca = env(t, T_GAME, .4) * 10 + env(t, T_PRICE, .4) * 10
    f = grain_vig_bars(np.clip(f, 0, 255), t, ca)
    f = np.clip(f, 0, 255).astype(np.uint8)
    if t > TOTAL - .6: f = (f * max(0, (TOTAL - t) / .6)).astype(np.uint8)
    return f

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite(D + 'stc.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            fa = render(i / FPS).astype(np.uint16); fb = render(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
