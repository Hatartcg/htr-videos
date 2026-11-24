"""split_vs.py — HTR «أي كرت أغلى؟» split-screen versus template. New 24 Nov 2026.
Look: two-colour diagonal split (coral | royal blue, mid brightness — differs from the dark 3D/VHS and the light paper templates),
card-flip entrances, white VS seal on the seam, name highlight on the spoken word, slam countdown 3-2-1, NO answer in the video.
python3 split_vs.py spec.json out.mp4 [--subs]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
def F(n, s): return ImageFont.truetype(FD + n, s)
AR = lambda s: F('font_cairo.ttf', s); NUM = lambda s: F('font_anton.ttf', s); TXT = lambda s: F('font_cairo.ttf', s)
L_COL, R_COL, INK, WHITE = (236, 78, 84), (52, 94, 214), (16, 18, 40), (255, 255, 255)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def text_img(s, f, fill=WHITE, stroke=0, sfill=INK, pad=14, box=None, r=24):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); b = d.textbbox((0, 0), s, font=f, stroke_width=stroke); w, h = b[2] - b[0], b[3] - b[1]
    bx = 30 if box else 0
    im = Image.new('RGBA', (w + 2 * pad + 2 * bx, h + 2 * pad + bx), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if box: dr.rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=box)
    dr.text((pad + bx - b[0], pad + bx // 2 - b[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill); return im
def paste(base, im, cx, cy, s=1.0, a=1.0, sx=None):
    if a <= 0 or s <= 0: return
    w, h = int(im.width * s * (sx if sx is not None else 1)), int(im.height * s)
    if w < 2 or h < 2: return
    if (w, h) != im.size: im = im.resize((w, h), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def mkcard(path, w):
    im = Image.open(path).convert('RGBA'); h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 22, fill=255); im.putalpha(m)
    base = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + w, 54 + h), 24, fill=(0, 0, 0, 120)); base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    fr = Image.new('RGBA', (w + 16, h + 16), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle((0, 0, w + 15, h + 15), 28, fill=WHITE)
    base.alpha_composite(fr, (32, 32)); base.alpha_composite(im, (40, 40)); return base
def mkback(w, h, col):
    im = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((32, 32, w + 47, h + 47), 28, fill=WHITE); d.rounded_rectangle((44, 44, w + 35, h + 35), 22, fill=INK)
    for k in range(0, w + h, 46): d.line((44 + k, 44, 44 + k - h, 44 + h), fill=col + (90,), width=10)
    lg = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA'); lg = lg.resize((int(w * .7), int(w * .7 * lg.height / lg.width)))
    pill = Image.new('RGBA', (lg.width + 30, lg.height + 24), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), 20, fill=WHITE); pill.alpha_composite(lg, (15, 12))
    im.alpha_composite(pill, ((im.width - pill.width) // 2, (im.height - pill.height) // 2)); return im
# ---------- background ----------
def mkbg(shift=0):
    bg = Image.new('RGBA', (W, H), R_COL + (255,)); d = ImageDraw.Draw(bg)
    x0, x1 = 560 + shift, 520 - shift
    d.polygon([(0, 0), (x0, 0), (x1, H), (0, H)], fill=L_COL + (255,))
    d = ImageDraw.Draw(bg)
    d.line((x0, 0, x1, H), fill=WHITE, width=10)
    return bg
BG = mkbg()
STR = Image.new('RGBA', (W + 400, H), (0, 0, 0, 0)); _ds = ImageDraw.Draw(STR)
for i in range(0, 3000, 90): _ds.line((i, 0, i - 900, H), fill=(255, 255, 255, 24), width=22)
def stripes(fr, t):  # drifting stripes: the background never stands still (montage-qa frozen-second check)
    o = int((t * 45) % 90); fr.alpha_composite(STR.crop((o, 0, o + W, H)))
def mkbg_swap():
    b = mkbg(); return b.transpose(Image.FLIP_LEFT_RIGHT)
BGS = mkbg_swap()
def closeup(fr, t, c):  # hard cut to one card full-size on the word that names it
    sd = c['side']; im = card(sd['img']); col = L_COL if c['i'] == 0 else R_COL
    bg = Image.new('RGBA', (W, H), col + (255,)); fr.alpha_composite(bg)
    st = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
    for i in range(0, 2600, 90): ds.line((i, 0, i - 900, H), fill=(255, 255, 255, 22), width=22)
    fr.alpha_composite(st)
    u = t - c['t']; paste(fr, im, W / 2, 860, 1.55 * (1 + .03 * u))
    paste(fr, text_img(sd['name'], NUM(110), fill=WHITE, pad=6), W / 2, 1560)
    paste(fr, text_img(sd['set'], TXT(46), fill=WHITE, pad=4), W / 2, 1680)
LOGO = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA').resize((220, 82), Image.LANCZOS)
PILL = Image.new('RGBA', (262, 112), (0, 0, 0, 0)); ImageDraw.Draw(PILL).rounded_rectangle((0, 0, 261, 111), 30, fill=WHITE); PILL.alpha_composite(LOGO, (21, 15))
VS = Image.new('RGBA', (230, 230), (0, 0, 0, 0)); dv = ImageDraw.Draw(VS); dv.ellipse((0, 0, 229, 229), fill=WHITE); dv.ellipse((14, 14, 215, 215), fill=INK)
vt = text_img('VS', NUM(120), fill=WHITE, pad=0); VS.alpha_composite(vt, ((230 - vt.width) // 2, (230 - vt.height) // 2 - 8))
CW = 430
cards, backs = {}, {}
def card(p):
    if p not in cards: cards[p] = mkcard(p, CW)
    return cards[p]
def back(h, col):
    k = (h, col)
    if k not in backs: backs[k] = mkback(CW, h, col)
    return backs[k]
XL, XR, CY = 285, 795, 900
def side(fr, t, s, i, sd, flip_t, hl, big=1.0):
    im = card(sd['img']); x = XL if i == 0 else XR
    # card flip: back → face (horizontal squash), staggered per side
    u = (t - flip_t - i * .18) / .45
    if u < 0: return
    if u < .5: face, sx = back(im.height - 80, L_COL if i == 0 else R_COL), max(.02, 1 - u * 2)
    else: face, sx = im, max(.02, (u - .5) * 2)
    if u >= 1: sx = 1
    sc = big
    if hl is not None and hl[i] is not None and hl[i] <= t < (hl[i] + 1.2): sc *= 1.07
    dim = hl is not None and hl[1 - i] is not None and hl[1 - i] <= t < hl[1 - i] + 1.2
    bob = 6 * math.sin(t * 2.1 + i * 1.9)
    paste(fr, face, x, CY + bob, sc, .55 if dim else 1, sx=min(1, sx))
    if u >= 1:
        lab = text_img(sd['name'], NUM(64), fill=WHITE, pad=6); paste(fr, lab, x, 1335)
        paste(fr, text_img(sd['set'], TXT(34), fill=WHITE, pad=4), x, 1405, 1, .92)
def sc_round(fr, t, s):
    r = s['round']; hl = s.get('hl')
    tb = text_img(s.get('title', 'أيهم أغلى؟'), AR(110), fill=WHITE, stroke=6, sfill=INK); paste(fr, tb, W / 2, 330)
    if s.get('label'):
        lb = text_img(s['label'], AR(52), fill=INK, box=WHITE + (255,), pad=8); paste(fr, lb, W / 2, 470, ebk((t - s['s']) / .3) if s.get('pop', True) else 1)
    for i in (0, 1): side(fr, t, s, i, r['sides'][i], s.get('flip', s['s'] - 10), hl, s.get('big', 1.0))
    paste(fr, VS, (XL + XR) / 2 + 0, CY, 1 + .05 * math.sin(t * 5))
    if 'cd' in s and t >= s['cd']:
        c = t - s['cd']
        if c < 3:
            n = 3 - int(c); k = max(0, 1 - (c % 1) / .2)
            dot = Image.new('RGBA', (260, 260), (0, 0, 0, 0)); dd = ImageDraw.Draw(dot); dd.ellipse((0, 0, 259, 259), fill=WHITE)
            dd.arc((8, 8, 251, 251), -90, -90 + 360 * (1 - c / 3), fill=INK, width=18)
            nl = text_img(str(n), NUM(160), fill=INK, pad=0); dot.alpha_composite(nl, ((260 - nl.width) // 2, (260 - nl.height) // 2 - 8))
            paste(fr, dot, W / 2, 1640, 1 + .25 * k)
            paste(fr, text_img('فكّر بسرعة…', AR(54), fill=WHITE, stroke=4), W / 2, 1820)
        else:
            paste(fr, text_img('ثبّت جوابك!', AR(96), fill=INK, box=WHITE + (255,)), W / 2, 1660, ebk((c - 3) / .25))
def sc_end(fr, t, s):
    for st, line, f, col, y, box in s['lines']:
        if t >= st:
            k = ebk((t - st) / .3); paste(fr, text_img(line, AR(f), fill=tuple(col), stroke=0 if box else 5, box=tuple(box) + (255,) if box else None), W / 2, y, max(.01, k), min(1, k))
    if 'thumbs' in s:
        for i, p in enumerate(s['thumbs']):
            kk = ebk((t - s['s'] - .1 - i * .07) / .3); x = 165 + i * 150
            paste(fr, card(p), x, 1180 + 14 * math.sin(t * 3 + i * .9), .33 * max(.01, kk), min(1, kk))
    if 'shop' in s and t >= s['shop']:
        k = eo((t - s['shop']) / .35); y = 1600 + (1 - k) * 260
        b = Image.new('RGBA', (960, 250), (0, 0, 0, 0)); ImageDraw.Draw(b).rounded_rectangle((0, 0, 959, 249), 40, fill=INK, outline=WHITE, width=6)
        y += 8 * math.sin(t * 4); paste(fr, b, W / 2, y); paste(fr, text_img('زورونا: معرض HTR', AR(64), fill=WHITE), W / 2, y - 50)
        paste(fr, text_img('أبحر الجنوبية · العليا سكوير', AR(54), fill=(255, 205, 210)), W / 2, y + 45)
FN = {'round': sc_round, 'end': sc_end}
def caption(fr, t):
    for c in spec.get('subs', []):
        if c['s'] <= t < c['e']:
            im = text_img(c['t'], TXT(38), fill=WHITE, pad=8, box=INK + (225,), r=20)
            if im.width > W - 80: im = im.resize((W - 80, int(im.height * (W - 80) / im.width)), Image.LANCZOS)
            paste(fr, im, W / 2, spec.get('sub_y', 1530))
D = spec['dur']; NF = int(round(D * FPS))
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', spec['audio'],
                      '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(NF):
    t = i / FPS; cur = [s for s in spec['scenes'] if s['s'] <= t < s['e']]
    sh = 0
    for w0 in spec.get('wipes', []):  # diagonal seam sweep on round change
        if w0 <= t < w0 + .35: sh = int(900 * math.sin(math.pi * (t - w0) / .35))
    swapped = sum(t >= x for x in spec.get('swaps', [])) % 2 == 1
    fr = (mkbg(sh) if sh else (BGS if swapped else BG)).copy()
    stripes(fr, t)
    cl = next((c for c in spec.get('closeups', []) if c['t'] <= t < c['t'] + c.get('d', .9)), None)
    if cl: closeup(fr, t, cl)
    else:
        for s in cur: FN[s['type']](fr, t, s)
    for z0, amt, dz in spec.get('punch', []):
        if z0 <= t < z0 + dz:
            k = 1 + amt; w2, h2 = W / k, H / k; fr = fr.resize((W, H), Image.BICUBIC, box=((W - w2) / 2, (H - h2) / 2, (W + w2) / 2, (H + h2) / 2))
    for f0 in spec.get('flashes', []):
        if f0 <= t < f0 + .1: fr = Image.alpha_composite(fr, Image.new('RGBA', (W, H), (255, 255, 255, int(210 * (1 - (t - f0) / .1)))))
    fr.alpha_composite(PILL, (30, 40))
    if SUBS: caption(fr, t)
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('ok', OUT)
