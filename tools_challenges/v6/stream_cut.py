"""stream_cut.py — HTR stream-reel compositor (20:30 slot). New 24 Nov 2026.
Cuts Hadi's vertical stream recordings (720x1280: face cam top, OLD «@HATAR_ANIME» ticker at y≈466–528, cards at the bottom)
into a 1080x1920 reel driven by an EDL spec: real-speed clips, speed ramps, freeze-frame push-ins, punch-ins on words,
kinetic Arabic text, HTR logo all the time and an HTR band that ALWAYS covers the old ticker (painted on the source frame,
so it stays covered under every zoom). Audio is mixed separately (see the spec's audio file).
python3 stream_cut.py spec.json out.mp4 [--subs]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
PAL = {k: tuple(v) for k, v in spec['palette'].items()}
def F(name, s): return ImageFont.truetype(FD + name, s)
AR = lambda s: F(spec.get('font_ar', 'font_rubik.ttf'), s)
NUM = lambda s: F('font_anton.ttf', s)
TXT = lambda s: F('font_cairo.ttf', s)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def text_img(s, f, fill=(255, 255, 255), stroke=0, sfill=None, pad=14, box=None, r=26):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); b = d.textbbox((0, 0), s, font=f, stroke_width=stroke); w, h = b[2] - b[0], b[3] - b[1]
    bx = 34 if box else 0
    im = Image.new('RGBA', (w + 2 * pad + 2 * bx, h + 2 * pad + bx), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if box: dr.rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=box)
    dr.text((pad + bx - b[0], pad + bx // 2 - b[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im
def paste(base, im, cx, cy, s=1.0, a=1.0, rot=0):
    if a <= 0 or s <= 0: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
# ---------- brand ----------
LOGO = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA').resize((220, 82), Image.LANCZOS)
PILL = Image.new('RGBA', (262, 112), (0, 0, 0, 0)); ImageDraw.Draw(PILL).rounded_rectangle((0, 0, 261, 111), 30, fill=(255, 255, 255, 236)); PILL.alpha_composite(LOGO, (21, 15))
BAND_Y0, BAND_Y1 = int(spec.get('band', [458, 536])[0] * 1.5), int(spec.get('band', [458, 536])[1] * 1.5)
_band = text_img(spec['band_text'] * 4, AR(46), fill=(255, 255, 255), pad=4)
def cover_band(img, t):
    bh = BAND_Y1 - BAND_Y0; band = Image.new('RGBA', (W, bh), PAL['band'] + (255,)); bd = ImageDraw.Draw(band)
    bd.rectangle((0, 0, W, 6), fill=PAL['accent'] + (255,)); bd.rectangle((0, bh - 6, W, bh), fill=PAL['accent'] + (255,))
    if spec.get('band_static', True):  # static, centred: a scrolling marquee is always cut at the frame edge (montage-qa OCR)
        lab = text_img(spec['band_text'].strip(' ·'), AR(44), fill=(255, 255, 255), pad=4)
        band.alpha_composite(lab, ((W - lab.width) // 2, (bh - lab.height) // 2))
    else:
        per = _band.width / 4; off = int((t * 140) % per)
        band.alpha_composite(_band.crop((off, 0, off + W, _band.height)), (0, (bh - _band.height) // 2))
    img.alpha_composite(band, (0, BAND_Y0))
# ---------- source readers ----------
class Reader:
    def __init__(self, s0, s1, fps):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(s0), '-t', str(s1 - s0), '-i', spec['src'], '-vf', f'fps={fps},scale={W}:{H}',
                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.i = -1; self.cur = None; self.fps = fps; self.s0 = s0
    def at(self, st):
        want = max(0, int(round((st - self.s0) * self.fps)))
        while self.i < want:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.cur = b; self.i += 1
        return Image.frombytes('RGB', (W, H), self.cur).convert('RGBA')
def grab(st):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(st), '-i', spec['src'], '-frames:v', '1', '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return Image.frombytes('RGB', (W, H), b).convert('RGBA')
def zoomed(img, z, cx, cy):
    if z <= 1.0001: return img
    w, h = W / z, H / z; x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
def ease_map(u, kind):
    if kind == 'ramp': return u ** 2.2           # slow start, faster and faster (speed ramp)
    if kind == 'rampdown': return 1 - (1 - u) ** 2.2
    return u
# ---------- overlays ----------
def draw_text(fr, t, o):
    k = (t - o['s']) / o.get('in', .28)
    if t < o['s'] or t >= o['e']: return
    out = (o['e'] - t) / .18 if o.get('out', True) else 1
    a = min(1, max(0, k), max(0, out)); sc = ebk(k) if o.get('pop', True) else 1
    f = {'ar': AR, 'num': NUM, 'txt': TXT}[o.get('font', 'ar')](o['size'])
    im = text_img(o['t'], f, fill=tuple(o.get('fill', PAL['text'])), stroke=o.get('stroke', 0), sfill=tuple(o.get('sfill', PAL['band'])),
                  box=tuple(o['box']) + (o.get('box_a', 235),) if o.get('box') else None)
    wob = o.get('wobble', 0) * math.sin(t * 9)
    paste(fr, im, o.get('x', W / 2), o['y'], max(.01, sc) * (1 + o.get('pulse', 0) * max(0, 1 - ((t - o['s']) % 1) / .3)), a, rot=wob)
def countdown(fr, t, c):
    if not c['s'] <= t < c['e']: return
    u = t - c['s']; n = 3 - int(u)
    ring = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(ring)
    d.ellipse((10, 10, 290, 290), fill=PAL['band'] + (230,)); d.arc((10, 10, 290, 290), -90, -90 + 360 * (1 - min(u, 3) / 3), fill=PAL['accent'], width=22)
    lab = text_img(str(max(1, n)), NUM(170), fill=(255, 255, 255), pad=0); ring.alpha_composite(lab, ((300 - lab.width) // 2, (300 - lab.height) // 2 - 6))
    paste(fr, ring, c.get('x', W / 2), c['y'], 1 + .14 * max(0, 1 - (u % 1) / .22))
def caption(fr, t):
    for c in spec.get('subs', []):
        if c['s'] <= t < c['e']:
            im = text_img(c['t'], TXT(40), fill=(255, 255, 255), pad=10, box=PAL['band'], r=22)
            if im.width > W - 80: im = im.resize((W - 80, int(im.height * (W - 80) / im.width)), Image.LANCZOS)
            paste(fr, im, W / 2, spec.get('sub_y', 1760))
# ---------- main ----------
segs = spec['segments']; D = spec['dur']; NF = int(round(D * FPS))
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', spec['audio'], '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M',
                      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
readers, stills = {}, {}
for i in range(NF):
    t = i / FPS
    sg = next(s for s in segs if s['o0'] <= t < s['o1'] or s is segs[-1])
    u = (t - sg['o0']) / (sg['o1'] - sg['o0'])
    if sg['type'] == 'freeze':
        key = sg['at']
        if key not in stills:
            im = grab(key)
            if sg.get('blur'): im = im.filter(ImageFilter.GaussianBlur(sg['blur']))
            stills[key] = im
        src = stills[key].copy()
    else:
        sid = id(sg)
        if sid not in readers:
            span = sg['s1'] - sg['s0']; dur = sg['o1'] - sg['o0']
            readers[sid] = Reader(sg['s0'], sg['s1'] + .2, min(30, max(4, math.ceil(span / dur * 30))))
        st = sg['s0'] + (sg['s1'] - sg['s0']) * ease_map(u, sg.get('map', 'lin'))
        src = readers[sid].at(st)
        if sg.get('blur'): src = src.filter(ImageFilter.GaussianBlur(sg['blur']))
    cover_band(src, t)
    z, cx, cy = 1.0, W / 2, H / 2
    if 'push' in sg:  # slow push-in [z0, z1, cx, cy]
        z0, z1, cx, cy = sg['push']; z = z0 + (z1 - z0) * eo(u) if sg.get('push_ease') else z0 + (z1 - z0) * u
    for pz in spec.get('punch', []):  # punch-in on a word/beat: [t, amount, dur, cx, cy]
        if pz[0] <= t < pz[0] + pz[2]: z *= 1 + pz[1]; cx, cy = pz[3], pz[4]
    fr = zoomed(src, z, cx, cy)
    if sg.get('dim'): fr = Image.alpha_composite(fr, Image.new('RGBA', (W, H), (0, 0, 0, int(255 * sg['dim']))))
    if sg.get('flash') and u * (sg['o1'] - sg['o0']) < .12:
        fr = Image.alpha_composite(fr, Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - u * (sg['o1'] - sg['o0']) / .12)))))
    rail = spec.get('rail', 18)  # thin brand frame: also keeps background text in the footage off the very edge
    if rail:
        d = ImageDraw.Draw(fr); d.rectangle((0, 0, rail, H), fill=PAL['band'] + (255,)); d.rectangle((W - rail, 0, W, H), fill=PAL['band'] + (255,))
        d.rectangle((rail, 0, rail + 4, H), fill=PAL['accent'] + (255,)); d.rectangle((W - rail - 4, 0, W - rail, H), fill=PAL['accent'] + (255,))
    fr.alpha_composite(PILL, (36, 36))
    for o in spec.get('texts', []): draw_text(fr, t, o)
    for c in spec.get('countdowns', []): countdown(fr, t, c)
    if SUBS: caption(fr, t)
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close(); p.wait()
for r in readers.values(): r.p.kill()
print('ok', OUT)
