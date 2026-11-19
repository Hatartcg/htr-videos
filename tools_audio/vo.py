"""Shared voice-line tools for every HTR video script (owner/audience note, 19 Nov 2026:
«احيانا يقطع ... والصوت نبرته تختلف»).

Use these instead of ad-hoc trimming and RMS levelling:
    from tools_audio.vo import load, line, qa
    x = line(load(path), cut=(0.10, 3.03))      # trims only inside a pause, matches loudness, soft edges
    ...place lines...
    qa(placed)                                  # prints problems; exits non-zero on a cut word or overlap

Rules it enforces:
- every voice line is matched to the same loudness (-16 LUFS, ITU BS.1770 gating), so no line jumps;
- a trim point is moved to the nearest pause (±0.25 s) instead of cutting a sounding word;
- 15 ms fades on every edge (no clicks);
- qa(): no line may overlap the next, a cut may not land on speech, and the spoken gap between
  lines must be at least 0.18 s (a breath), otherwise the join sounds chopped.
"""
import subprocess
import sys

import numpy as np

SR = 48000
TARGET_LUFS = -16.0
EDGE_DB = -38.0      # louder than this at a cut = a word is being cut
MIN_GAP = 0.18       # seconds of silence between two spoken lines


def load(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def _db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def lufs(x, sr=SR):
    """Integrated loudness, BS.1770 (K-weighting + absolute and relative gating)."""
    from scipy.signal import lfilter
    # K-weighting filters for 48 kHz
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x))
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if len(y) < blk:
        return _db(y) - 0.691
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[lk > -70]
    if not len(g):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    g2 = ms[(lk > -70) & (lk > rel)]
    return -0.691 + 10 * np.log10(np.mean(g2 if len(g2) else g))


def match(x, target=TARGET_LUFS):
    gain = 10 ** ((target - lufs(x)) / 20)
    return x * np.clip(gain, 0.25, 4.0)


def env(x, sr=SR, win=0.02):
    w = max(1, int(win * sr))
    return np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same"))


def quiet_point(x, t, sr=SR, search=0.25):
    """The quietest moment within ±search s of t (where a cut does not hit a word)."""
    e = env(x, sr)
    a, b = max(0, int((t - search) * sr)), min(len(x) - 1, int((t + search) * sr))
    if b <= a:
        return t
    return (a + int(np.argmin(e[a:b]))) / sr


def fade(x, f=0.015, sr=SR):
    k = min(int(f * sr), len(x) // 2)
    x = x.copy()
    if k:
        x[:k] *= np.linspace(0, 1, k)
        x[-k:] *= np.linspace(1, 0, k)
    return x


def speech_bounds(x, sr=SR, thr_db=-45.0):
    """First and last moment the line is actually speaking (seconds)."""
    e = 20 * np.log10(env(x, sr) + 1e-12)
    idx = np.where(e > thr_db)[0]
    if not len(idx):
        return 0.0, len(x) / sr
    return idx[0] / sr, idx[-1] / sr


def line(x, cut=None, sr=SR, target=TARGET_LUFS):
    """Prepare one voice line: optional trim moved into a pause, loudness match, soft edges."""
    if cut is not None:
        a, b = cut
        a = quiet_point(x, a, sr) if a > 0.03 else 0.0
        b = quiet_point(x, b, sr) if b is not None and b < len(x) / sr - 0.03 else len(x) / sr
        x = x[int(a * sr):int(b * sr)]
    return fade(match(x, target), sr=sr)


def qa(placed, sr=SR, strict=True):
    """placed: list of (name, offset_seconds, prepared_array[, trimmed]). trimmed=True for a clip cut out of
    a longer recording (voice-bank clips, re-cut lines): only those are checked for a cut word at the edges.
    Also flags a clip whose 'silence' is not silent (music or room under it = it will sound like another take).
    Prints a report; exits on hard problems."""
    rows = sorted([(r[0], r[1], r[2], (r[3] if len(r) > 3 else False)) for r in placed], key=lambda r: r[1])
    hard, out = 0, []
    louds = []
    for i, (name, off, x, trimmed) in enumerate(rows):
        s0, s1 = speech_bounds(x, sr)
        start, end = off + s0, off + s1
        head, tail = _db(x[:int(0.06 * sr)]), _db(x[-int(0.06 * sr):])
        L = lufs(x, sr)
        louds.append(L)
        flags = []
        if trimmed and head > EDGE_DB:
            flags.append("cut starts on sound (%.0f dB)" % head)
            hard += 1
        if trimmed and tail > EDGE_DB:
            flags.append("cut ends on sound (%.0f dB)" % tail)
            hard += 1
        floor = np.percentile(20 * np.log10(env(x, sr) + 1e-12), 5)
        if floor > -50:
            flags.append("background under the voice (floor %.0f dB: music/room from another recording, sounds like a different take)" % floor)
            hard += 1
        if i + 1 < len(rows):
            n_name, n_off, n_x, _ = rows[i + 1]
            if off + len(x) / sr > n_off + 0.01:
                n0, _ = speech_bounds(n_x, sr)
                if end > n_off + n0:
                    flags.append("talks over %s" % n_name)
                    hard += 1
            n0, _ = speech_bounds(n_x, sr)
            gap = (n_off + n0) - end
            if gap < MIN_GAP:
                flags.append("only %.2fs before %s (needs a breath ≥%.2fs)" % (gap, n_name, MIN_GAP))
        out.append("%-4s %6.2f-%6.2f  %5.1f LUFS  %s" % (name, start, end, L, "; ".join(flags) or "ok"))
    print("\n".join(out))
    spread = max(louds) - min(louds) if louds else 0
    print("voice loudness spread: %.1f LU (should be ≤ 1.0)" % spread)
    if hard and strict:
        print("VOICE QA FAILED: %d hard problem(s). Fix before rendering." % hard)
        sys.exit(2)
    return hard
