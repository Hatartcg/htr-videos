"""HTR «خمّن السعر» quiz reel renderer.  usage: python3 gp.py spec.json stills t1 t2 ... | python3 gp.py spec.json a b out.mp4"""
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
SPEC = json.load(open(sys.argv[1]))
FD = '/home/claude/fonts/'
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
PURPLE = (142, 117, 255); TEAL = (46, 196, 182); GREEN = (22, 196, 119); RED = (255, 34, 69); WHITE = (255, 255, 255); LILAC = (205, 195, 255); DEEP = (12, 8, 28); DIM = (120, 112, 160)
TM = SPEC.get('timing', {})
ROUNDS = SPEC['rounds']; N = len(ROUNDS)
T_INTRO = TM.get('intro', 3.0); T_CD = 3.0; T_OUT = TM.get('outro', 4.2); T_END = TM.get('end', 3.0)
THINK = TM.get('think', [3.4] * N); RLEN = TM.get('rlen', [8.6] * N)
RSTART = [T_INTRO + sum(RLEN[:i]) for i in range(N)]
T_OUTRO = T_INTRO + sum(RLEN); TOTAL = T_OUTRO + T_OUT + T_END
def rnd_at(t):
    for i in range(N - 1, -1, -1):
        if t >= RSTART[i]: return i, t - RSTART[i]
    return 0, 0
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
def rrect(w, h, r, fill, outline=None, ow=0, glow=None):
    im = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((40, 40, 40 + w, 40 + h), r, fill=glow + (200,)); im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(im).rounded_rectangle((40, 40, 40 + w, 40 + h), r, fill=fill, outline=outline, width=ow); return im
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
# ---------- assets
def card_img(path, w):
    im = Image.open(path).convert('RGBA'); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), int(w * .045), fill=255)
    a = np.minimum(np.array(im.getchannel('A')), np.array(m)); im.putalpha(Image.fromarray(a)); return im
def card_spr(im, glow=None):
    c = Image.new('RGBA', (im.width + 120, im.height + 120), (0, 0, 0, 0))
    g = Image.new('RGBA', c.size, (0, 0, 0, 0)); gm = Image.new('L', c.size, 0); gm.paste(im.getchannel('A'), (60, 60))
    g.paste(Image.new('RGBA', c.size, (glow or (0, 0, 0)) + (255,)), (0, 0), gm.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * (.95 if glow else .7))))
    c = Image.alpha_composite(c, g); c.alpha_composite(im, (60, 60)); return to_bgra(c)
CW = 520
CARDS = []
for r in ROUNDS:
    im = card_img(r['img'], CW); dark = Image.eval(im.convert('RGB'), lambda v: int(v * .35)).convert('RGBA'); dark.putalpha(im.getchannel('A'))
    CARDS.append(dict(n=card_spr(im), g=card_spr(im, GREEN), d=card_spr(dark), small=card_spr(card_img(r['img'], 230))))
BACK = Image.new('RGBA', (300, 418), (0, 0, 0, 0)); bd = ImageDraw.Draw(BACK)
bd.rounded_rectangle((0, 0, 299, 417), 22, fill=(40, 30, 80, 255), outline=PURPLE + (255,), width=6)
for i in range(0, 600, 34): bd.line((i - 300, 0, i, 417), fill=(60, 48, 110, 255), width=10)
q = FL(240); bb = bd.textbbox((0, 0), '؟', font=q); bd.text((150 - (bb[2] - bb[0]) / 2 - bb[0], 209 - (bb[3] - bb[1]) / 2 - bb[1]), '؟', font=q, fill=WHITE, stroke_width=8, stroke_fill=PURPLE)
BACK_S = card_spr(BACK, PURPLE)
def logo_spr(w, glow=True):
    l = Image.open('/home/claude/gp/htr_logo.png').convert('RGBA'); l = l.resize((w, int(l.height * w / l.width)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    c = Image.new('RGBA', (l.width + 120, l.height + 120), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', c.size, (0, 0, 0, 0)); m = Image.new('L', c.size, 0); m.paste(l.getchannel('A'), (60, 60)); g.paste(Image.new('RGBA', c.size, (150, 200, 255, 255)), (0, 0), m.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 1.0))); c = Image.alpha_composite(c, g)
    c.alpha_composite(l, (60, 60)); return to_bgra(c)
LOGO_BIG = logo_spr(560); LOGO_WM = logo_spr(150, False)
S = dict(
    t1=txt(SPEC['title1'], FL(118), WHITE), t2=txt(SPEC['title2'], FL(140), PURPLE, glow=PURPLE),
    sub=to_bgra(rrect(560, 84, 42, (24, 18, 50, 255), TEAL + (255,), 4)), subt=txt(SPEC['subtitle'], FL(50), LILAC),
    lock=txt('ثبّت إجابتك!', FL(64), WHITE, glow=RED), how1=txt('كم جبت صح؟', FL(130), WHITE, glow=PURPLE),
    cmt=to_bgra(rrect(640, 100, 50, PURPLE + (255,), glow=PURPLE)), cmtt=txt('اكتب نتيجتك بالتعليقات', FL(56), WHITE),
    src=txt(SPEC['source'], FL(36), DIM),
    htr=LOGO_BIG, tcg=np.zeros((2, 2, 4), np.uint8),
    e3=txt('كل أسبوع تحدي جديد', FL(66), WHITE), ig=to_bgra(rrect(420, 86, 43, (28, 22, 50, 255), TEAL + (255,), 4)), igt=txt('@hatar_tcg', FB(46), (160, 240, 230)),
    loc=txt('معرضنا – أبحر الجنوبية، العليا سكوير، جدة', FL(42), LILAC), wm=LOGO_WM,
)
SCORES = [txt(s, FB(54), WHITE) for s in ('0/3', '1/3', '2/3', '3/3')]
CHIP = to_bgra(rrect(170, 100, 26, (30, 24, 60, 255), PURPLE + (255,), 4)); CHIP_ON = to_bgra(rrect(170, 100, 26, GREEN + (255,), glow=GREEN))
LET = 'ABC'
def opt_bar(state, w=760, h=104):
    fill = {'n': (26, 20, 54, 255), 'ok': GREEN + (255,), 'off': (20, 16, 40, 255)}[state]
    return to_bgra(rrect(w, h, 22, fill, (PURPLE + (255,)) if state == 'n' else None, 3, GREEN if state == 'ok' else None))
BARS = {k: opt_bar(k) for k in ('n', 'ok', 'off')}
def badge(L, col): im = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle((0, 0, 89, 89), 20, fill=col + (255,)); f = FB(50); bb = d.textbbox((0, 0), L, font=f); d.text((45 - (bb[2] - bb[0]) / 2 - bb[0], 45 - (bb[3] - bb[1]) / 2 - bb[1]), L, font=f, fill=WHITE); return to_bgra(im)
BADGE = {(L, k): badge(L, c) for L in LET for k, c in (('n', PURPLE), ('ok', (10, 120, 70)), ('off', (50, 44, 80)))}
PRICE = {}
for r in ROUNDS:
    for o in r['options']:
        PRICE[(o, 'n')] = txt(o, FB(62), WHITE); PRICE[(o, 'ok')] = txt(o, FB(62), WHITE); PRICE[(o, 'off')] = txt(o, FB(62), (80, 74, 110))
    PRICE[('big', r['answer'])] = txt(r['options'][r['answer']], FB(150), WHITE, stroke=10, glow=GREEN, gr=26)
NAMES = [(txt(r['name'], FB(58), WHITE), txt(r['set'], FL(40), LILAC)) for r in ROUNDS]
RND = [txt(f'الجولة {i + 1} من {N}', FL(54), LILAC) for i in range(N)]
NUM = {n: txt(str(n), FB(220), WHITE, stroke=10, glow=PURPLE, gr=30) for n in (1, 2, 3)}
RING = Image.new('RGBA', (320, 320), (0, 0, 0, 0)); ImageDraw.Draw(RING).ellipse((10, 10, 310, 310), fill=(14, 10, 32, 220), outline=PURPLE + (255,), width=12); RING = to_bgra(RING)
CHECK = Image.new('RGBA', (70, 70), (0, 0, 0, 0)); cd = ImageDraw.Draw(CHECK); cd.ellipse((0, 0, 69, 69), fill=WHITE); cd.line((18, 36, 30, 49, 52, 22), fill=GREEN + (255,), width=9, joint='curve'); CHECK = to_bgra(CHECK)
# ---------- background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
ANG = np.arctan2(yy - 760, xx - W / 2); RAD = np.sqrt((xx - W / 2) ** 2 + (yy - 760) ** 2)
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = np.array(DEEP[::-1], np.float32)
GLOWP = np.exp(-(RAD / 760) ** 2)[..., None] * np.array(PURPLE[::-1], np.float32)
GLOWG = np.exp(-(RAD / 620) ** 2)[..., None] * np.array(GREEN[::-1], np.float32)
rng = np.random.default_rng(5); SPK = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 5), rng.uniform(0, 6.3), rng.uniform(20, 60)) for _ in range(60)]
def background(t, win=0.0):
    rays = (.5 + .5 * np.cos((ANG + t * .18) * 16))[..., None] * np.exp(-(RAD / 1100) ** 2)[..., None]
    f = BASE + GLOWP * .30 + rays * 20 + win * (GLOWG * .35 + rays * 40 * np.array([.6, 1, .7], np.float32))
    f = np.clip(f, 0, 255).astype(np.uint8)
    for x, y, r, ph, v in SPK:
        a = .35 + .35 * math.sin(t * 2 + ph); cv2.circle(f, (int(x), int((y - v * t) % H)), int(r), (255, 230, 240), -1, cv2.LINE_AA) if a > .5 else None
    return f.astype(np.float32)
# ---------- render
CARD_Y = 640; OPT_Y = [1290, 1415, 1540]
def render(t):
    win = 0.0
    if T_INTRO <= t < T_OUTRO:
        i, lt = rnd_at(t); rv = THINK[i] + T_CD; R_LEN = RLEN[i]
        if lt >= rv: win = min(1, (lt - rv) / .25) * (1 - max(0, (lt - R_LEN + .3) / .3))
    f = background(t, win)
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        blit(f, S['t1'], W / 2, 420 - 300 * out, ebk(k / .4), 1 - out); blit(f, S['t2'], W / 2, 560 - 300 * out, ebk((k - .2) / .4), (1 if k > .2 else 0) * (1 - out))
        for j, (dx, rot) in enumerate(((-250, -12), (0, 0), (250, 12))):
            kk = ebk((k - .4 - j * .12) / .45); blit(f, BACK_S, W / 2 + dx * kk, 1000 + 25 * abs(j - 1) + 700 * (1 - kk) + 900 * out, .9 + .1 * (j == 1) + .03 * math.sin(t * 4 + j), 1 if kk > 0 else 0, rot * kk)
        blit(f, S['sub'], W / 2, 1420 + 400 * out, ebk((k - .8) / .3), 1 if k > .8 else 0); blit(f, S['subt'], W / 2, 1420 + 400 * out, ebk((k - .8) / .3), 1 if k > .8 else 0)
    elif t < T_OUTRO:
        i, lt = rnd_at(t); r = ROUNDS[i]; C = CARDS[i]; R_LEN = RLEN[i]; T_THINK = THINK[i]
        out = eo((lt - R_LEN + .3) / .3); inn = eo(lt / .35)
        cd0 = T_THINK; rv = T_THINK + T_CD
        if not (cd0 - .2 <= lt < rv): blit(f, RND[i], W / 2, 130, 1, inn * (1 - out))
        for j in range(N):
            col = GREEN if j < i else (PURPLE if j == i else (60, 52, 100)); cv2.circle(f, (int(W / 2 + (j - (N - 1) / 2) * 46), 200), 13 if j == i else 10, col[::-1], -1, cv2.LINE_AA)
        if cd0 - .2 <= lt < rv: blit(f, S['lock'], W / 2, 125, ebk((lt - cd0 + .2) / .3), 1)
        cx = W / 2 - 1300 * out + 1300 * (1 - inn); s = 1 + .05 * env(lt, rv, .4)
        spr = C['g'] if lt >= rv else (C['d'] if cd0 <= lt < rv else C['n'])
        blit(f, spr, cx, CARD_Y + 8 * math.sin(t * 2.2), s, 1, 2 * math.sin(t * 1.3) * (lt < rv))
        if cd0 <= lt < rv:
            n = 3 - int(lt - cd0); kk = (lt - cd0) % 1
            blit(f, RING, cx, CARD_Y, 1, 1); blit(f, NUM[n], cx, CARD_Y + 8, 1.4 - .4 * eo(kk / .25), 1 - max(0, (kk - .8) / .2))
            ang = int(360 * kk); cv2.ellipse(f, (int(cx), CARD_Y), (150, 150), -90, 0, ang, (140, 230, 190), 12, cv2.LINE_AA)
        if lt >= rv: blit(f, PRICE[('big', r['answer'])], cx, CARD_Y + 120, ebk((lt - rv) / .35) * (1 + .03 * math.sin(t * 7)), 1, -6)
        nm, st = NAMES[i]; blit(f, nm, W / 2, 1060, 1, inn * (1 - out)); blit(f, st, W / 2, 1135, 1, inn * (1 - out))
        for j, o in enumerate(r['options']):
            state = 'n' if lt < rv else ('ok' if j == r['answer'] else 'off')
            k2 = eo((lt - .25 - j * .1) / .35); y = OPT_Y[j]; x = W / 2 + 900 * (1 - k2) + 900 * out * (1 if j % 2 else -1)
            sc = 1 + .06 * env(lt, rv, .3) * (state == 'ok')
            blit(f, BARS[state], x, y, sc, k2); blit(f, BADGE[(LET[j], state)], x + 320 * sc, y, sc, k2); blit(f, PRICE[(o, state)], x - 40, y, sc, k2)
            if state == 'ok': blit(f, CHECK, x - 320 * sc, y, ebk((lt - rv) / .3), 1)
        blit(f, S['src'], W / 2, 1680, 1, inn * (1 - out))
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO; out = eo((k - T_OUT + .3) / .3)
        blit(f, S['how1'], W / 2, 330 - 400 * out, ebk(k / .4), 1)
        for j in range(N):
            kk = ebk((k - .3 - j * .15) / .4); x = W / 2 + (j - 1) * 300
            blit(f, CARDS[j]['small'], x, 760 + 600 * (1 - kk) + 900 * out, 1, 1 if kk > 0 else 0, (j - 1) * 6)
            p = PRICE[(ROUNDS[j]['options'][ROUNDS[j]['answer']], 'n')]; blit(f, p, x, 1010 + 900 * out, .8 * kk, 1 if kk > 0 else 0)
        for j in range(4):
            kk = ebk((k - 1.0 - j * .1) / .3); x = W / 2 + (j - 1.5) * 200; on = j == 3 and k > 2.0
            blit(f, CHIP_ON if on else CHIP, x, 1260 + 900 * out, kk, 1 if kk > 0 else 0); blit(f, SCORES[j], x, 1260 + 900 * out, kk, 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1450 + 900 * out, ebk((k - 1.4) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.4 else 0); blit(f, S['cmtt'], W / 2, 1450 + 900 * out, ebk((k - 1.4) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.4 else 0)
    else:
        k = t - T_OUTRO - T_OUT
        blit(f, S['htr'], W / 2, 660, ebk(k / .4), 1); blit(f, S['tcg'], W / 2, 800, ebk((k - .15) / .35), 1 if k > .15 else 0)
        blit(f, S['e3'], W / 2, 980, ebk((k - .3) / .35), 1 if k > .3 else 0); blit(f, S['ig'], W / 2, 1110, ebk((k - .45) / .35), 1 if k > .45 else 0); blit(f, S['igt'], W / 2, 1110, ebk((k - .45) / .35), 1 if k > .45 else 0)
        blit(f, S['loc'], W / 2, 1230, ebk((k - .6) / .35), 1 if k > .6 else 0)
    if t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 130, 80, 1, .9)
    fl = 0.0
    for i in range(N): fl += env(t, RSTART[i] + THINK[i] + T_CD, .15) * .5
    fl += env(t, T_OUTRO + T_OUT, .15) * .5
    f = np.clip(f + (255 - f) * fl, 0, 255)
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return f.astype(np.uint8)
def cues():
    c = dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, rounds=[])
    for i in range(N):
        a = RSTART[i]; c['rounds'].append(dict(start=a, cd=a + THINK[i], reveal=a + THINK[i] + T_CD, end=a + RLEN[i]))
    return c
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills':
        ts = [float(x) for x in sys.argv[3:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite('st.jpg', np.vstack(rows)); print(TOTAL)
    else:
        a, b, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))): p.stdin.write(render(i / FPS).tobytes())
        p.stdin.close(); p.wait()
