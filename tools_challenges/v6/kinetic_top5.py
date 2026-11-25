"""kinetic_top5.py — HTR «أكبر قفزات الأسعار (توب ٥)» countdown reel, kinetic-typography template. New 25 Nov 2026.
Looks unlike the ticker/stock-app, split-flip, VHS and 3D templates: flat colour fields that flip light ↔ violet on every
rank (brightness change = visible cut), giant rank numerals sliding in, words that slam in on the voice, rolling prices,
tangerine «+$» stamps, moving diagonal stripes. HTR logo pill always on. No yellow in our graphics.
python3 kinetic_top5.py spec.json out.mp4 [--subs]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
D = spec['dur']; NF = int(round(D * FPS))
def F(n, s): return ImageFont.truetype(FD + n, s)
AR = lambda s: F('font_lalezar.ttf', s)
NUM = lambda s: F('font_anton.ttf', s)
TXT = lambda s: F('font_cairo.ttf', s)
LIGHT, VIOL, INK, MUT, TANG, WHITE, MINT = (243, 240, 255), (88, 40, 220), (22, 14, 50), (120, 110, 160), (255, 104, 60), (255, 255, 255), (0, 205, 160)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.9): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def timg(s, f, fill=INK, stroke=0, sfill=None, pad=10):
    fill = tuple(fill) if isinstance(fill, list) else fill
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    im = Image.new('RGBA', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill); return im
def paste(base, im, cx, cy, s=1.0, a=1.0, rot=0):
    if a <= 0 or s <= 0.01: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def boxed(s, f, fill, bg, r=30, px=34, py=14):
    t = timg(s, f, fill); im = Image.new('RGBA', (t.width + 2 * px, t.height + 2 * py), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=bg); im.alpha_composite(t, (px, py)); return im
def cardimg(path, w, blur=0):
    im = Image.open(path).convert('RGB'); h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
    if Image.open(path).width < 500: im = im.filter(ImageFilter.UnsharpMask(2, 90, 2))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.convert('RGBA'); m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=255); im.putalpha(m)
    sh = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + w, 54 + h), 26, fill=(10, 0, 40, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh
LOGO = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA').resize((220, 82), Image.LANCZOS)
PILL = Image.new('RGBA', (262, 112), (0, 0, 0, 0)); ImageDraw.Draw(PILL).rounded_rectangle((0, 0, 261, 111), 30, fill=(255, 255, 255, 245)); PILL.alpha_composite(LOGO, (21, 15))
BADGE = boxed(spec.get('badge', 'قفزات الأسبوع · توب ٥'), AR(44), WHITE, INK, r=28, px=26, py=8)
IMG = {k: v for k, v in spec['images'].items()}
CARDS, BLURS = {}, {}
def card(k, w, blur=0):
    key = (k, w, blur)
    if key not in CARDS: CARDS[key] = cardimg(IMG[k], w, blur)
    return CARDS[key]
def stripes(dark, t, alt=False, spd=60):
    base = ((52, 20, 150) if alt else VIOL) if dark else ((200, 190, 246) if alt else LIGHT)
    b = Image.new('RGBA', (W, H), base + (255,)); d = ImageDraw.Draw(b)
    col = tuple(min(255, c + 14) for c in base) + (255,); off = int(t * spd) % 160
    for x in range(-H - 160, W + 160, 160): d.polygon([(x + off, 0), (x + off + 60, 0), (x + off + 60 + H, H), (x + off + H, H)], fill=col)
    return b
def money(v): return '$' + f'{v:,.0f}'
def pair(a, b, size, col):
    A = timg(money(a), NUM(size), col); B = timg(money(b), NUM(size), col); aw = int(size * .9)
    ar = Image.new('RGBA', (aw, A.height), (0, 0, 0, 0)); d = ImageDraw.Draw(ar); cy = A.height / 2; th = size * .09
    d.rectangle((size * .1, cy - th, aw - size * .38, cy + th), fill=TANG); d.polygon([(aw - size * .45, cy - size * .26), (aw - size * .08, cy), (aw - size * .45, cy + size * .26)], fill=TANG)
    im = Image.new('RGBA', (A.width + aw + B.width, A.height), (0, 0, 0, 0)); im.alpha_composite(A, (0, 0)); im.alpha_composite(ar, (A.width, 0)); im.alpha_composite(B, (A.width + aw, 0)); return im
def chrome(fr, t, dark):
    fr.alpha_composite(PILL, (30, 36))
    fr.alpha_composite(BADGE, (W - 30 - BADGE.width, 52))
# ---------- scenes ----------
def sc_hook(fr, t, S, lt):
    h = S['hook']; z = 1 + 0.025 * eo(lt / 3)
    paste(fr, timg(h['big'], NUM(300), TANG, 8, INK), W / 2, 450, z)
    paste(fr, timg(h['sub'], AR(104), INK), W / 2, 680)
    c = card(h['img'], 500, 26); paste(fr, c, W / 2, 1180, z)
    paste(fr, timg('?', NUM(330), WHITE, 10, VIOL), W / 2, 1180)
    paste(fr, timg(h['src'], TXT(40), MUT), W / 2, 1770)
def sc_title(fr, t, S, lt):
    for i, (wt, s, y, col, f) in enumerate(S['words']):
        if t < wt: continue
        k = ebk((t - wt) / 0.28); paste(fr, timg(s, f == 'num' and NUM(330) or AR(170 if len(s) < 10 else 112), col, 0), W / 2, y, 0.4 + 0.6 * k, min(1, (t - wt) / 0.12))
    thumbs = S['thumbs']; n = len(thumbs)
    for i, k in enumerate(thumbs):
        x = 150 + i * 195 + 40 * math.sin(t * 1.3 + i); x -= 120 * eo(lt / 2.5) - 120
        paste(fr, card(k, 170), x, 1640 + 18 * math.sin(t * 2 + i), 1, 1, -6 + 3 * i)
def roll(a, b, x): return a + (b - a) * eo(x)
def sc_rank(fr, t, S, lt):
    dk = S.get('dark', False); fg = WHITE if dk else INK; mut = (210, 200, 255) if dk else MUT
    r = S['rank']; x = eo(lt / 0.35)
    num = timg('#' + str(r['n']), NUM(380), (255, 255, 255, 60) if not dk else (255, 255, 255, 70), 0)
    paste(fr, timg('#' + str(r['n']), NUM(340), TANG if not dk else WHITE, 0), 250, 520 - 260 * (1 - x), 1, min(1, lt / .15))
    c = card(r['img'], 540); paste(fr, c, 690 + 400 * (1 - eo(lt / 0.45)), 860 + 14 * math.sin(lt * 4), 1 + 0.04 * lt / 2.4, 1, -5 + 4 * eo(lt / 2.4))
    if lt > 0.25:
        k = eo((lt - 0.25) / 0.3); paste(fr, timg(r['name'], NUM(84), fg), W / 2, 1360 + 40 * (1 - k), 1, k)
        paste(fr, timg(r['game'], TXT(42), mut), W / 2, 1450, 1, k)
    if lt > 0.5:
        k = eo((lt - 0.5) / 0.6); cur = roll(r['before'], r['now'], (lt - 0.5) / 0.9)
        paste(fr, pair(r['before'], cur, 104, fg), W / 2, 1580, 1, min(1, k * 2))
    if lt > r.get('stamp', 1.25):
        k = ebk((lt - r.get('stamp', 1.25)) / 0.25, 2.4)
        paste(fr, boxed('+' + money(r['now'] - r['before']), NUM(120), WHITE, TANG, 34, 40, 10), W / 2, 1745, 0.3 + 0.7 * k, 1, 4 * (1 - k) - 2)
def sc_pause(fr, t, S, lt):
    p = S['pause']
    paste(fr, timg(p['l1'], AR(220), TANG, 6, INK), W / 2, 430, 0.5 + 0.5 * ebk(lt / 0.3))
    paste(fr, timg(p['l2'], AR(120), INK), W / 2, 650)
    tk = (t - p['cd']) % 1 if t >= p['cd'] else 1; paste(fr, card(p['img'], 460, 30), W / 2, 1130, 1 + 0.06 * max(0, 1 - tk / .3), 1, 4 * math.sin(t * 7) if t >= p['cd'] else 0)
    cd0 = p['cd']; tt = t - cd0
    if 0 <= tt < 3:
        n = 3 - int(tt); fx = tt % 1
        ring = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(ring)
        d.ellipse((10, 10, 290, 290), fill=(255, 255, 255, 235)); d.arc((10, 10, 290, 290), -90, -90 + 360 * (1 - fx), fill=VIOL, width=22)
        paste(fr, ring, W / 2, 1130); paste(fr, timg(str(n), NUM(190), INK), W / 2, 1130, 1 + 0.15 * (1 - eo(fx / 0.25)))
    paste(fr, boxed(p['l3'], AR(70), WHITE, VIOL, 30), W / 2, 1640)
def sc_reveal(fr, t, S, lt):
    r = S['rank']; k = ebk(lt / 0.35)
    paste(fr, timg('#1', NUM(300), WHITE), W / 2, 400, 0.5 + 0.5 * k)
    paste(fr, card(r['img'], 600), W / 2, 960, 0.6 + 0.4 * k, 1, 3 * (1 - eo(lt / 1.2)))
    paste(fr, timg(r['name'], NUM(84), WHITE), W / 2, 1440)
    if lt > 0.6:
        cur = roll(r['before'], r['now'], (lt - 0.6) / 1.2)
        paste(fr, pair(r['before'], cur, 108, WHITE), W / 2, 1580)
    if lt > r.get('stamp', 1.9):
        kk = ebk((lt - r.get('stamp', 1.9)) / 0.25, 2.4); paste(fr, boxed('+' + money(r['now'] - r['before']), NUM(130), WHITE, TANG, 34, 40, 10), W / 2, 1760, 0.3 + 0.7 * kk)
def bookmark(size, col):
    im = Image.new('RGBA', (size, int(size * 1.3)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w, h = im.size
    d.polygon([(0, 0), (w, 0), (w, h), (w / 2, h * 0.72), (0, h)], fill=col); return im
def sc_cta(fr, t, S, lt):
    dk = S.get('dark', False)
    for wt, s, y, col, sz in S['lines']:
        if t < wt: continue
        k = ebk((t - wt) / 0.3); paste(fr, timg(s, AR(sz), tuple(col)), W / 2, y, 0.5 + 0.5 * k, min(1, (t - wt) / 0.12))
    if S.get('icon'):
        it = S['icon']
        if t >= it: k = ebk((t - it) / 0.35); paste(fr, bookmark(200, TANG), W / 2, 650, k, 1, 8 * math.sin((t - it) * 6) * max(0, 1 - (t - it)))
    if S.get('shop'):
        sh = boxed('أبحر الجنوبية · العليا سكوير', AR(74), WHITE, INK, 30); paste(fr, sh, W / 2, 1150, 1 + 0.03 * math.sin(t * 5))
        for i, k in enumerate(['ray', 'ahri', 'clef', 'gyar', 'mew']): paste(fr, card(k, 190), 150 + i * 195, 1560 + 16 * math.sin(t * 2 + i), 1, 1, -8 + 4 * i)
def sc_loop(fr, t, S, lt): sc_hook(fr, t, S, 3)
FN = dict(hook=sc_hook, title=sc_title, rank=sc_rank, pause=sc_pause, reveal=sc_reveal, cta=sc_cta, loop=sc_loop)
SUBF = TXT(44)
def sub(fr, t):
    for s in spec.get('subs', []):
        if s['s'] <= t < s['e']:
            im = boxed(s['t'], SUBF, WHITE, (0, 0, 0, 175), 18, 22, 6)
            if im.width > W - 60: im = im.resize((W - 60, int(im.height * (W - 60) / im.width)))
            paste(fr, im, W / 2, spec.get('sub_y', 1865))
FACE = spec.get('face'); FH = 690
if FACE:
    _fp = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(FACE['s0']), '-t', str(D + 1), '-i', FACE['src'], '-vf',
                            f"fps={FPS},crop=720:{FACE.get('h', 452)}:0:{FACE.get('y', 0)},scale={W}:{FH}", '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
def face_frame():
    b = _fp.stdout.read(W * FH * 3)
    if len(b) == W * FH * 3: face_frame.last = Image.frombytes('RGB', (W, FH), b).convert('RGBA')
    return face_frame.last
def split(fr, t, dk):
    # split-screen: Hadi's real face cam on top, the kinetic panel (scaled) below
    out = stripes(dk, t)
    pan = fr.crop((0, 300, W, H)).resize((int(W * .74), int((H - 300) * .74)), Image.LANCZOS)
    out.alpha_composite(pan, ((W - pan.width) // 2, H - pan.height - 8))
    f = face_frame(); out.alpha_composite(f, (0, 0))
    d = ImageDraw.Draw(out); d.rectangle((0, FH, W, FH + 10), fill=TANG + (255,)); d.rectangle((0, 0, 30, FH), fill=INK + (255,)); d.rectangle((W - 30, 0, W, FH), fill=INK + (255,))
    return out
def frame(i):
    t = i / FPS; S = next(s for s in spec['scenes'] if s['s'] <= t < s['e'] + 1e-6) if t < spec['scenes'][-1]['e'] else spec['scenes'][-1]
    lt = t - S['s']; dk = S.get('dark', False) or S['type'] in ('title', 'reveal')
    alt = any(a <= t < b for a, b in S.get('alt', [])); fr = stripes(dk, t, alt, S.get('spd', 60))
    FN[S['type']](fr, t, S, lt)
    for fl in spec.get('flashes', []):
        if fl <= t < fl + 0.2: fr.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - (t - fl) / 0.2)))))
    if FACE: fr = split(fr, t, dk)
    chrome(fr, t, dk)
    if SUBS: sub(fr, t)
    return fr.convert('RGB')
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', spec['audio'], '-af', 'alimiter=limit=0.85', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '9M', '-bufsize', '18M',
                      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(NF):
    p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait(); print('done', OUT)
