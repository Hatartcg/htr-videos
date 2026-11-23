"""vhs_sealed.py — HTR sealed-box reel in a RETRO VHS tape look (new template, 23 Nov 2026).
Scanlines, grain, RGB split, OSD «▶ PLAY» + tape date, tracking-glitch cuts, hot pink / cyan on deep plum.
python3 vhs_sealed.py spec.json out.mp4 [--subs]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
def vf(name, s, var=None):
    f = ImageFont.truetype(FD + name, s)
    if var: f.set_variation_by_name(var)
    return f
AR = lambda s: vf('font_readex.ttf', s, 'Bold')
KU = lambda s: vf('font_reemkufi.ttf', s, 'Bold')
OSD = lambda s: vf('font_vt323.ttf', s)
NUM = lambda s: vf('font_anton.ttf', s)
# bright VHS palette (light tape-blue / candy pink backgrounds, deep ink text) — the dark VHS version matched old dark reels at 90%
BG0, PINK, CYAN, WHITE, DIM = (21, 14, 30), (176, 0, 104), (14, 42, 150), (26, 12, 44), (70, 60, 100)
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
D = spec['dur']; NF = int(D * FPS); rng = np.random.default_rng(5)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def T(s, f, fill=WHITE, glow=None, pad=14):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); b = d.textbbox((0, 0), s, font=f)
    im = Image.new('RGBA', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, font=f, fill=fill)
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).text((pad - b[0], pad - b[1]), s, font=f, fill=glow)
        g = g.filter(ImageFilter.GaussianBlur(10)); g.alpha_composite(im); im = g
    return im
def P(base, im, cx, cy, s=1.0, a=1.0):
    if a <= 0 or s <= 0: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
_c = {}
def BOX(key, w, blur=0):
    k = (key, w, blur)
    if k not in _c:
        im = Image.open(spec['images'][key]).convert('RGBA'); h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
        # cut the white product-photo background into a soft glow card
        a = np.array(im).astype(np.int16); white = (a[..., :3].min(axis=2) > 238)
        a[..., 3] = np.where(white, 0, 255); im = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.SMOOTH)
        if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
        glow = Image.new('RGBA', (w + 120, h + 120), (0, 0, 0, 0)); sh = Image.new('RGBA', glow.size, (0, 0, 0, 0))
        sh.paste(Image.new('RGBA', im.size, PINK + (150,)), (60, 60), im); glow.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
        glow.alpha_composite(im, (60, 60)); _c[k] = glow
    return _c[k]
LOGO = Image.open('/home/claude/htr-videos/brand/htr_holo_sig.png').convert('RGBA').resize((250, 103), Image.LANCZOS)
SCAN = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(SCAN)
for y in range(0, H, 4): sd.line((0, y, W, y), fill=(0, 0, 0, 70), width=2)
yy, xx = np.mgrid[0:H, 0:W]; vig = np.clip(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2, 0, 1)
VIG = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (vig * 110).astype(np.uint8)]), 'RGBA')
def mkbg(c, line):
    b = Image.new('RGBA', (W, H), c + (255,)); d = ImageDraw.Draw(b)
    for y in range(0, H, 6): d.line((0, y, W, y), fill=line, width=1)
    return b
BGS = {'blue': mkbg((96, 146, 246), (110, 158, 250)), 'black': mkbg((255, 160, 208), (255, 175, 216))}
def rollbar(fr, t):
    y = int((t * 260) % (H + 300)) - 150; band = Image.new('RGBA', (W, 160), (255, 255, 255, 48)); fr.alpha_composite(band, (0, max(-119, min(H - 1, y))))
def osd(fr, t, s):
    if int(t * 2) % 2 == 0: P(fr, T('▶', NUM(44), fill=WHITE), W - 250, 92); P(fr, T('PLAY', OSD(64), fill=WHITE), W - 150, 90)
    tape = s.get('tape2') if s.get('cut') and t >= s['cut'] else s.get('tape', '')
    P(fr, T(tape or '', OSD(58), fill=CYAN), W - 190, 150)
    P(fr, T('SP  ' + '%02d:%02d:%02d' % (0, int(t) // 60, int(t) % 60), OSD(48), fill=DIM), 150, 1800)
def glitch(img, k):
    a = np.array(img); h = a.shape[0]
    for _ in range(int(6 + 10 * k)):
        y = rng.integers(0, h - 60); hh = rng.integers(8, 60); dx = int(rng.integers(-50, 50) * k)
        a[y:y + hh] = np.roll(a[y:y + hh], dx, axis=1)
    n = rng.integers(0, 255, a.shape[:2], dtype=np.uint8); a[..., :3] = np.clip(a[..., :3] * (1 - .35 * k) + n[..., None] * .35 * k, 0, 255)
    return Image.fromarray(a)
def post(img):
    a = np.array(img.convert('RGB')).astype(np.int16)
    a[..., 0] = np.roll(a[..., 0], 4, axis=1); a[..., 2] = np.roll(a[..., 2], -4, axis=1)
    a += rng.integers(-10, 10, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# ---------------- scenes ----------------
def sc_box(fr, t, s):
    tt = t - s['s']; z = 1 + .03 * tt; cut = s.get('cut', 99)
    if t >= cut: z *= 1.1
    P(fr, BOX(s['img'], s.get('w', 640)), W * .40, 800 if t < cut else 760, z * (1 if s['s'] == 0 else ebk(tt / .35)))
    P(fr, T('SEALED · ' + s['year'], OSD(84), fill=PINK), W / 2, 235)
    if 'price_at' in s and t >= s['price_at']:
        k = ebk((t - s['price_at']) / .25)
        P(fr, T(s['price'], NUM(210), fill=WHITE, glow=PINK), W * .60, 1440, max(.01, k * (1 + .03 * math.sin(t * 6))))
        P(fr, T(s.get('price_sub', 'سعره اليوم'), AR(64), fill=WHITE), W * .60, 1600, min(1, k))
    P(fr, T(s['name'], OSD(62), fill=DIM), W / 2, 1700)
def sc_packs(fr, t, s):
    tt = t - s['s']; n = 36; cols = 6
    for i in range(n):
        x = 190 + (i % cols) * 140; y = 470 + (i // cols) * 150; k = eo((tt - i * .02) / .2)
        hot = i == 14
        r = Image.new('RGBA', (100, 128), (0, 0, 0, 0)); ImageDraw.Draw(r).rounded_rectangle((0, 0, 99, 127), 12, fill=(PINK if hot else (60, 44, 80)) + (255,), outline=CYAN if hot else None, width=4)
        P(fr, r, x, y, ((1.25 if t > s['rev'] else 1.05) + (.07 * math.sin(t * 7) if hot else 0) if hot else 1) * max(.01, k))
    P(fr, T('36 باك', AR(96), fill=WHITE), W / 2, 1400)
    if t > s['rev']:
        P(fr, T('$96', NUM(220), fill=WHITE, glow=PINK), W / 2 + 150, 1620, ebk((t - s['rev']) / .25))
        P(fr, T('للباك!', AR(90), fill=CYAN), W / 2 - 230, 1630, ebk((t - s['rev'] - .1) / .25))
def sc_mystery(fr, t, s):
    tt = t - s['s']
    if s.get('rew'):
        P(fr, T('REW', OSD(120), fill=PINK), W / 2 + 40 * math.sin(t * 20), 1350)
        for k in range(6): fr.alpha_composite(Image.new('RGBA', (W, 18), (255, 255, 255, 120)), (0, int((t * 3000 + k * 330) % H)))
    zz = s.get('zoom', 1.0)
    P(fr, BOX(s['img'], 760, blur=28), W / 2 + 6 * math.sin(t * 9), s.get('my', 760), zz * (1 + .02 * tt))
    P(fr, T('?', NUM(420), fill=WHITE, glow=PINK), W / 2, s.get('my', 760), zz * (1 + .06 * math.sin(t * 5)))
    for st, line, f, col, y in s['lines']:
        if t >= st: k = ebk((t - st) / .3); P(fr, T(line, AR(f), fill=tuple(col), glow=(PINK if col == list(WHITE) else None)), W / 2, y, max(.01, k), min(1, k))
    if s.get('bar'):
        c = min(1, tt / (s['e'] - s['s'])); b = Image.new('RGBA', (820, 60), (0, 0, 0, 0)); ImageDraw.Draw(b).rectangle((0, 0, 819, 59), outline=CYAN, width=4)
        ImageDraw.Draw(b).rectangle((8, 8, 8 + int(803 * c * .92), 51), fill=PINK); fr.alpha_composite(b, ((W - 820) // 2, 1650))
        P(fr, T('UNLOCKING...  %d%%' % int(92 * c), OSD(52), fill=CYAN), W / 2, 1745)
def sc_text(fr, t, s):
    for st, line, f, col, y in s['lines']:
        if t >= st: k = ebk((t - st) / .3); P(fr, T(line, AR(f), fill=tuple(col)), W / 2, y, max(.01, k), min(1, k))
    if 'row' in s:
        for i, (key, bl) in enumerate(s['row']):
            k = ebk((t - s['s'] - .15 - i * .1) / .3); P(fr, BOX(key, 250, blur=bl), 215 + i * 325, s.get('row_y', 1300), max(.01, k), min(1, k))
    if 'icons' in s and t >= s['icons']:
        for i, (lab, col) in enumerate([('تابع', WHITE), ('لايك', WHITE), ('احفظ', WHITE)]):
            k = ebk((t - s['icons'] - i * .12) / .3); b = Image.new('RGBA', (260, 150), (0, 0, 0, 0))
            ImageDraw.Draw(b).rectangle((0, 0, 259, 149), outline=(CYAN, PINK, CYAN)[i], width=6); P(fr, b, 220 + i * 320, 1150, max(.01, k), min(1, k))
            P(fr, T(lab, AR(70), fill=col), 220 + i * 320, 1150, max(.01, k), min(1, k))
    if 'shop' in s and t >= s['shop']:
        k = eo((t - s['shop']) / .35); y = 1420 + (1 - k) * 200
        b = Image.new('RGBA', (960, 250), (0, 0, 0, 0)); ImageDraw.Draw(b).rectangle((0, 0, 959, 249), fill=(255, 255, 255, 240), outline=PINK, width=6); P(fr, b, W / 2, y)
        P(fr, T('معرض HTR · أبحر الجنوبية · العليا سكوير', AR(42), fill=WHITE), W / 2, y - 45)
        P(fr, T('htrtcg.com', OSD(80), fill=CYAN), W / 2, y + 50)
FN = {'box': sc_box, 'packs': sc_packs, 'mystery': sc_mystery, 'text': sc_text}
def caption(fr, t):
    for c in spec['subs']:
        if c['s'] <= t < c['e']:
            im = T(c['t'], vf('font_cairo.ttf', 40, 'Bold') if False else vf('font_readex.ttf', 40, 'Medium'), fill=(255, 255, 255), pad=10)
            if im.width > W - 120: im = im.resize((W - 120, int(im.height * (W - 120) / im.width)), Image.LANCZOS)
            w = im.width + 40; box = Image.new('RGBA', (w, im.height + 20), (0, 0, 0, 200)); box.alpha_composite(im, (20, 10))
            cy = next((sc.get('cap_y') for sc in spec['scenes'] if sc['s'] <= t < sc['e'] and sc.get('cap_y')), 1700)
            fr.alpha_composite(box, ((W - w) // 2, int(cy - box.height / 2)))
cuts = [s['s'] for s in spec['scenes']][1:] + [s.get('bgcut', s['cut']) for s in spec['scenes'] if s.get('cut')]
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', spec['audio'], '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], stdin=subprocess.PIPE)
for i in range(NF):
    t = i / FPS; cur = [s for s in spec['scenes'] if s['s'] <= t < s['e']]
    bgk = (cur[0].get('bg') if cur else None) or 'blue'
    if cur and cur[0].get('bg2') and t >= cur[0].get('bgcut', cur[0].get('cut', 99)): bgk = cur[0]['bg2']
    fr = BGS[bgk].copy(); rollbar(fr, t)
    for s in cur: FN[s['type']](fr, t, s)
    j = int(round(5 * math.sin(t * 11) + 3 * math.sin(t * 2.3)))   # VHS tape jitter: the picture breathes up/down
    if j: fr = Image.fromarray(np.roll(np.array(fr), j, axis=0))
    fr.alpha_composite(LOGO, (40, 40)); osd(fr, t, cur[0] if cur else {})
    fr.alpha_composite(SCAN); fr.alpha_composite(VIG); fr.alpha_composite(LOGO, (40, 40))
    if SUBS: caption(fr, t)
    g = [t - c for c in cuts if 0 <= t - c < .14]
    img = glitch(fr.convert('RGB'), 1 - g[0] / .14) if g else fr.convert('RGB')
    p.stdin.write(post(img).tobytes())
p.stdin.close(); p.wait(); print('ok', OUT)
