"""punch.py in.mp4 report.json out.mp4 [zoom=1.09] [maxgap=2.6] [trim_end_sec] [endzoom_sec=3]
Hard punch-in cuts (zoom toggles about the HTR logo so it stays in frame) wherever the reel_score
report shows a gap > maxgap s without a cut; slow push-in over the last endzoom_sec s."""
import sys, json, subprocess, numpy as np, cv2
src, rep, out = sys.argv[1:4]
Z = float(sys.argv[4]) if len(sys.argv) > 4 else 1.09
MG = float(sys.argv[5]) if len(sys.argv) > 5 else 2.6
TRIM = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != '-' else None
EZ = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0
R = json.load(open(rep)); dur = R['duration'] if TRIM is None else TRIM
cuts = sorted([0.0] + [c for c in R['cuts'] if c < dur] + [dur])
beats = []
if not any(0 < c < 3 for c in R['cuts']): beats.append(1.2)
for a, b in zip(cuts, cuts[1:]):
    g = b - a
    if g > MG:
        n = int(np.ceil(g / MG)) - 1
        beats += [a + g * (k + 1) / (n + 1) for k in range(n)]
import os
beats = [x for x in beats if x < dur - EZ - .3]
for e in filter(None, os.environ.get('EXTRA', '').split(',')):
    e = float(e)
    if all(abs(e - b) > .5 for b in beats): beats.append(e)
beats += [dur - 1.7, dur - 0.9]
beats = sorted(round(x * 30) / 30 for x in beats)
print('beats', beats)
W, H, FPS = 1080, 1920, 30; CX, CY = 540, 70
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', src, '-map', '0:v', '-map', '1:a', '-t', f'{dur:.3f}', '-af', f'afade=t=out:st={dur-0.6:.3f}:d=0.6',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
nf = int(round(dur * FPS)); i = 0
while i < nf:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    t = i / FPS
    z = Z if sum(b <= t for b in beats) % 2 else 1.0
    if t > dur - EZ: z = max(z, 1.0) * (1 + 0.07 * (t - (dur - EZ)) / EZ)
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    if z != 1.0:
        M = np.float32([[z, 0, CX - z * CX], [0, z, CY - z * CY]])
        f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    enc.stdin.write(f.tobytes()); i += 1
enc.stdin.close(); enc.wait(); dec.kill()
print('done', out, dur)
