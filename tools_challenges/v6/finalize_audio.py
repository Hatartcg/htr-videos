"""finalize_audio.py in.wav out.wav [lufs=-14] — loudness to target, then a hard true-peak-safe scale (max 0.93). 26 Nov 2026:
ffmpeg loudnorm+alimiter left 1.13 peaks in the wav (montage_qa flagged clipping every second), so the last step is numeric."""
import sys, subprocess, numpy as np, scipy.io.wavfile as w
src, out = sys.argv[1], sys.argv[2]; L = float(sys.argv[3]) if len(sys.argv) > 3 else -14
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', f'loudnorm=I={L}:TP=-2:LRA=11', '-ar', '48000', '-c:a', 'pcm_f32le', '/tmp/_ln.wav'], check=True)
sr, a = w.read('/tmp/_ln.wav'); a = a.astype(np.float32)
# soft-knee limiter: tanh above 0.7, then scale to 0.93 peak
k = .7; m = np.abs(a) > k; a[m] = np.sign(a[m]) * (k + (1 - k) * np.tanh((np.abs(a[m]) - k) / (1 - k)))
a = a.mean(axis=1) if a.ndim > 1 else a  # mono: ffmpeg -ac 1 sums identical L/R to 1.41x (false clipping in montage_qa)
a *= .93 / max(1e-6, np.abs(a).max()); w.write(out, sr, a)
