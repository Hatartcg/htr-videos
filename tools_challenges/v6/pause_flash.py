"""pause_flash.py — «وقّف الفيديو» card-flash reel (zero credits). New 26 Nov 2026 (idea-bank 20261123b-pause-generator).
Real TCGplayer card images flash like a slot machine; the viewer pauses and «the card you stop on is yours». Calm, readable
hook (1–3 s), accelerating/decelerating flash runs with landings, #1 slam, CTA. Brand: HTR logo all the time, no yellow.
python3 pause_flash.py spec.json out.mp4 [--subs]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
P = {k: tuple(v) for k, v in spec['palette'].items()}
def F(n, s): return ImageFont.truetype(FD + n, s)
AR = lambda s: F(spec.get('font_ar', 'font_tajawal.ttf'), s); NUM = lambda s: F('font_anton.ttf', s); TXT = lambda s: F('font_cairo.ttf', s)
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def text_img(s, f, fill, box=None, pad=16, r=28):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); b = d.textbbox((0, 0), s, font=f); w, h = b[2] - b[0], b[3] - b[1]; bx = 30 if box else 0
    im = Image.new('RGBA', (w + 2 * pad + 2 * bx, h + 2 * pad + bx), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if box: dr.rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=box)
    dr.text((pad + bx - b[0], pad + bx // 2 - b[1]), s, font=f, fill=fill); return im
def paste(base, im, cx, cy, s=1.0, a=1.0, rot=0):
    if a <= 0 or s <= 0: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
LOGO = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA').resize((220, 82), Image.LANCZOS)
PILL = Image.new('RGBA', (262, 112), (0, 0, 0, 0)); ImageDraw.Draw(PILL).rounded_rectangle((0, 0, 261, 111), 30, fill=(255, 255, 255, 240)); PILL.alpha_composite(LOGO, (21, 15))
CH = 880  # card height on screen
def load_card(p):
    im = Image.open(p).convert('RGB'); bg = Image.new('RGB', im.size, (255, 255, 255))
    bb = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 18 else 0).getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bb).convert('RGBA'); im = im.resize((int(im.width * CH / im.height), CH), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 26, fill=255); im.putalpha(m)
    sh = Image.new('RGBA', (im.width + 80, im.height + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((40, 52, im.width + 40, im.height + 52), 30, fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh
cards = spec['cards']
for c in cards: c['im'] = load_card(c['img']); c['blur'] = c['im'].filter(ImageFilter.GaussianBlur(30))
BG = Image.new('RGBA', (W, H), P['bg'] + (255,))
def background(t):
    col = P['bg']; scol = P['stripe']
    for ct, c1, c2 in spec.get('bg_cycle', []):  # whole-frame colour change on each beat/phase = a real cut for viewers and montage_qa
        if t >= ct: col, scol = tuple(c1), tuple(c2)
    bg = Image.new('RGBA', (W, H), col + (255,)); d = ImageDraw.Draw(bg); off = (t * 60) % 160
    for k in range(-4, 20):
        x = k * 160 + off; d.polygon([(x, 0), (x + 60, 0), (x - 900, H), (x - 960, H)], fill=scol + (255,))
    return bg
def which(t):
    """returns (card index, mode, local u) from the timeline events"""
    for e in spec['timeline']:
        if e['s'] <= t < e['e']:
            if e['type'] == 'flash':   # runs through cards, speed from rate0 to rate1 (cards/s)
                u = t - e['s']; r0, r1, L = e['rate0'], e['rate1'], e['e'] - e['s']
                n = r0 * u + (r1 - r0) * u * u / (2 * L)
                return int(n + e.get('start', 0)) % len(cards), 'flash', u
            return e['card'], e['type'], t - e['s']
    return 0, 'hold', 0
def draw_text(fr, t, o):
    if not (o['s'] <= t < o['e']): return
    k = (t - o['s']) / o.get('in', .25); out = (o['e'] - t) / .16 if o.get('out', True) else 1
    a = min(1, max(0, k), max(0, out)); sc = ebk(k) if o.get('pop', True) else 1
    f = {'ar': AR, 'num': NUM, 'txt': TXT}[o.get('font', 'ar')](o['size'])
    im = text_img(o['t'], f, tuple(o.get('fill', P['ink'])), tuple(o['box']) + (240,) if o.get('box') else None)
    if im.width > W - 90: im = im.resize((W - 90, int(im.height * (W - 90) / im.width)), Image.LANCZOS)
    paste(fr, im, o.get('x', W / 2), o['y'], max(.01, sc) * (1 + o.get('pulse', 0) * max(0, 1 - ((t - o['s']) % .6) / .25)), a)
D = spec['dur']; NF = int(round(D * FPS))
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', spec['audio'], '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M',
                      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
prev = None; since = 0
for i in range(NF):
    t = i / FPS; fr = background(t)
    ci, mode, u = which(t); c = cards[ci]
    if ci != prev: since = t; prev = ci
    cy = spec.get('card_y', 1010); sc = 1.0; rot = 0
    if mode == 'flash': sc = 1.0 + .05 * max(0, 1 - (t - since) / .08)
    elif mode in ('land', 'slam'): sc = ebk((t - since) / .3) if mode == 'slam' else 1 + .06 * max(0, 1 - (t - since) / .2); rot = 0
    elif mode == 'hold': sc = 1 + .015 * u
    im = c['blur'] if mode == 'mystery' else c['im']
    paste(fr, im, W / 2, cy, max(.05, sc), 1, rot)
    if mode != 'mystery':
        # price ribbon across the card's middle (it also sits over the publisher's SAMPLE band of the official image)
        cw = c['im'].width - 80; rb = Image.new('RGBA', (cw + 90, 232), (0, 0, 0, 0)); dr = ImageDraw.Draw(rb)
        dr.rounded_rectangle((0, 0, rb.width - 1, rb.height - 1), 26, fill=P['accent'] + (250,))
        rk = text_img('#' + str(c['rank']), NUM(96), P['accent'], (255, 255, 255, 255), pad=4, r=24); rb.alpha_composite(rk, (22, (232 - rk.height) // 2))
        pr = text_img(c['price'], NUM(124), (255, 255, 255), pad=0); rb.alpha_composite(pr, (rb.width - pr.width - 34, (232 - pr.height) // 2 - 2))
        pop = 1 + (.08 * max(0, 1 - (t - since) / .15) if mode == 'flash' else 0)
        paste(fr, rb, W / 2, cy - CH / 2 + .472 * CH, pop, 1, rot=-4)
        nm = text_img(c['label'], TXT(40), P['ink'], (255, 255, 255, 235), pad=8, r=20)
        if nm.width > W - 120: nm = nm.resize((W - 120, int(nm.height * (W - 120) / nm.width)), Image.LANCZOS)
        paste(fr, nm, W / 2, cy + CH / 2 + 70)
    if mode == 'flash':  # slot-machine frame lines
        d = ImageDraw.Draw(fr); d.rectangle((60, cy - CH / 2 - 26, W - 60, cy - CH / 2 - 16), fill=P['accent']); d.rectangle((60, cy + CH / 2 + 130, W - 60, cy + CH / 2 + 140), fill=P['accent'])
    fl = spec.get('flashes', [])
    for ft in fl:
        if ft <= t < ft + .25: fr = Image.alpha_composite(fr, Image.new('RGBA', (W, H), (255, 255, 255, int(250 * (1 - (t - ft) / .25)))))
    fr.alpha_composite(PILL, (36, 36))
    for o in spec['texts']: draw_text(fr, t, o)
    if SUBS:
        for s in spec.get('subs', []):
            if s['s'] <= t < s['e']:
                im = text_img(s['t'], TXT(38), (255, 255, 255), P['ink'] + (235,), pad=10, r=20)
                if im.width > W - 80: im = im.resize((W - 80, int(im.height * (W - 80) / im.width)), Image.LANCZOS)
                paste(fr, im, W / 2, spec.get('sub_y', 1855))
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('ok', OUT)
