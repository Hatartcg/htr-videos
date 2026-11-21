# «المجمّع واللاعب» — faceless situation series (HTR). Stills from Gemini + Ken Burns + captions on the voice.
import sys, json, math, subprocess, numpy as np, cv2
sys.path.insert(0, '/home/claude/dr850')
_argv = sys.argv; sys.argv = ['x']
import render as R
sys.argv = _argv
from render import text_sprite, pill, blit, FL, FB, eo, ebk, cl, WHITE
W, H, FPS = 1080, 1920, 30
D = '/home/claude/htr-videos/tools_ads/faceless/'
BLACK = (15, 15, 20)
EP = {
 'v1': dict(voice='fl_v1', title='لما تفتح بوكس كامل', vdur=10.11,
   shots=[('v1a', 0, 2.75, 'in'), ('v1b', 2.75, 4.5, 'out'), ('v1c', 4.5, 6.5, 'in'), ('v1d', 6.5, 99, 'in')],
   caps=[(0.0, 1.2, 'بوكس كامل'), (1.24, 2.7, '36 باك'), (2.78, 4.5, 'ولا كرت واحد يستاهل!'), (4.56, 6.5, 'وخويك يضحك عليك'), (6.54, 7.4, 'صار فيك؟'), (7.48, 10.1, 'قول لنا كم باك فتحت 👇')]),
 'v2': dict(voice='fl_v2', title='لما تدوّر على كروتك القديمة', vdur=7.55,
   shots=[('v2b', 0, 2.9, 'in'), ('v2c', 2.9, 4.75, 'in'), ('v2a', 4.75, 99, 'in')],
   caps=[(0.0, 1.4, 'تدوّر على كروتك'), (1.44, 2.85, 'تلقاها بالزبالة!'), (2.9, 4.7, 'وواحد منها يسوى 2000!'), (4.76, 6.3, 'أمك سوّتها فيك؟'), (6.32, 7.5, 'اكتبها لنا 👇')]),
 'v3': dict(voice='fl_v3', title='لما تبيع الكرت بدري', vdur=8.44,
   shots=[('v3a', 0, 2.8, 'in'), ('v3b', 2.8, 4.75, 'in'), ('v3c', 4.75, 99, 'out')],
   caps=[(0.0, 1.8, 'بعته بـ200'), (1.82, 3.6, 'بعد أسبوع'), (3.66, 4.75, 'صار بـ500!'), (4.8, 6.05, 'وهو يرقص'), (6.1, 8.4, 'منشن خويك اللي باع بدري 👇')]),
}
VID = sys.argv[1]; E = EP[VID]; OFF = 0.35
TOTAL = OFF + E['vdur'] + 1.4
IMG = {}
for s, *_ in E['shots']:
    if s not in IMG: IMG[s] = cv2.imread(D + 'shots/' + s + '.jpg').astype(np.float32)
def kb(img, p, mode):
    z = 1.03 + .06 * p if mode == 'in' else 1.09 - .06 * p
    M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H * .45]])
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
def box_title(s):
    return pill(s, FL(92), (255, 255, 255), fg=BLACK, padx=50, pady=20)
TITLE = box_title(E['title'])
CAPS = [(a + OFF, b + OFF, text_sprite(t.replace(' 👇', ''), FL(96), fill=WHITE, stroke=9, stroke_fill=(10, 10, 10))) for a, b, t in E['caps']]
ARROW = text_sprite('⬇', FB(80), fill=WHITE, stroke=6, stroke_fill=(10, 10, 10))
FOLLOW = pill('تابع HTR', FL(78), (230, 40, 60), fg=WHITE, padx=50, pady=20)
TAG = text_sprite('HTR', FB(40), fill=(255, 255, 255), stroke=4, stroke_fill=(10, 10, 10))
def render(t):
    tt = t - OFF
    cur = E['shots'][0]
    for sh in E['shots']:
        if tt >= sh[1]: cur = sh
    name, a, b, mode = cur; b = min(b, E['vdur'] + 1.4)
    p = cl((tt - a) / max(.5, b - a))
    f = kb(IMG[name], eo(p), mode)
    # quick 3-frame white flash on each cut (cut on the word)
    # top title (from frame 1, hook)
    blit(f, TITLE, 540, 210, 1.0, 1.0)
    # caption on the voice
    for ca, cb, spr in CAPS:
        if ca - .05 <= t < cb:
            k = ebk((t - ca) / .18)
            blit(f, spr, 540, 1480, .94 + .06 * k, cl((t - ca) / .12))
    blit(f, TAG, 960, 1840, 1, .8)
    if t >= OFF + E['vdur']:
        k = ebk((t - OFF - E['vdur']) / .3)
        f = f * (1 - .35 * cl((t - OFF - E['vdur']) / .3))
        blit(f, FOLLOW, 540, 1000, k, 1)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'still':
        ts = [float(x) for x in sys.argv[3].split(',')]
        ims = [cv2.resize(render(x), (270, 480)) for x in ts]
        cv2.imwrite(D + f'sheet_{VID}.png', np.hstack(ims))
    else:
        n = int(TOTAL * FPS); out = D + f'tmp_{VID}.mp4'
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '19', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(n): p.stdin.write(render(i / FPS).tobytes())
        p.stdin.close(); p.wait(); json.dump({'total': TOTAL, 'off': OFF, 'vdur': E['vdur']}, open(D + f'meta_{VID}.json', 'w')); json.dump([OFF + a for _, a, _, _ in E['shots'] if a > 0], open(D + f'cuts_{VID}.json', 'w')); print('ok', out, n)
