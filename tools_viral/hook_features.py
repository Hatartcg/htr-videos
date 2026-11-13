#!/usr/bin/env python3
"""hook_features.py — measurable features of a reel's first 3 seconds (the part that decides
whether people keep watching). Brand-agnostic: works for HTR, Otaku Haven and High Brand clients.

Used by reel_score.py (prediction) and train_hook.py (calibration against real 3-second hold rates).
"""
import subprocess
import numpy as np

FEATURES = ["mot_0_1", "mot_1_3", "mot_rest", "cuts_0_3", "first_cut", "cps",
            "audio_onset", "loud_0_1", "loud_rel", "bright0", "contrast0", "sat0",
            "edges0", "color0", "face0", "face_0_3", "dur", "text0", "change_0_1"]


def _run(cmd):
    return subprocess.run(cmd, capture_output=True).stdout


def probe(path):
    return float(_run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                       "-of", "default=nk=1:nw=1", path]).strip() or 0)


def frames(path, fps=10, w=144, h=256, gray=True, limit=None):
    fmt = "gray" if gray else "rgb24"
    vf = f"fps={fps},scale={w}:{h},format={fmt}"
    cmd = ["ffmpeg", "-v", "error"] + (["-t", str(limit)] if limit else []) + ["-i", path, "-vf", vf, "-f", "rawvideo", "-"]
    raw = _run(cmd)
    c = 1 if gray else 3
    n = len(raw) // (w * h * c)
    return np.frombuffer(raw[: n * w * h * c], np.uint8).reshape((n, h, w) if gray else (n, h, w, 3))


def audio_db(path, sr=16000, win=0.1):
    a = np.frombuffer(_run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
                            "-f", "f32le", "-"]), np.float32)
    if a.size == 0:
        return np.full(1, -90.0), -90.0
    n = int(sr * win); k = max(1, len(a) // n)
    rms = np.sqrt((a[: k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-9), float(20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9))


def _faces(rgb_frames):
    try:
        import cv2
        cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        hits = [len(cas.detectMultiScale(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), 1.1, 4, minSize=(30, 30))) > 0
                for f in rgb_frames]
        return hits
    except Exception:
        return [False] * len(rgb_frames)


def _text_area(rgb):
    """Share of the first frame covered by big on-screen text (OCR words, any language)."""
    try:
        import pytesseract  # optional
    except Exception:
        pytesseract = None
    try:
        import cv2, tempfile, os
        tmp = tempfile.mktemp(suffix=".png")
        cv2.imwrite(tmp, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        out = subprocess.run(["tesseract", tmp, "-", "-l", "ara+eng", "--psm", "11", "tsv"],
                             capture_output=True, text=True).stdout
        os.unlink(tmp)
        area = 0
        for ln in out.splitlines()[1:]:
            p = ln.split("\t")
            if len(p) == 12 and p[11].strip() and float(p[10] or -1) > 60:
                area += int(p[8]) * int(p[9])
        return area / (rgb.shape[0] * rgb.shape[1])
    except Exception:
        return 0.0


def extract(path, cuts=None):
    dur = probe(path)
    g = frames(path).astype(np.float32)
    if len(g) < 3:
        return dict.fromkeys(FEATURES, 0.0) | {"dur": dur}
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    if cuts is None:
        med = np.median(d) + 1e-3
        raw = [(i + 1) / 10 for i, v in enumerate(d) if v > max(18, 4 * med)]
        cuts = []
        for c in raw:
            if not cuts or c - cuts[-1] > 0.4:
                cuts.append(c)
    norm = np.median(d) + 1e-3
    seg = lambda a, b: float(d[int(a * 10): int(b * 10)].mean() / norm) if int(a * 10) < len(d) else 0.0
    db, overall = audio_db(path)
    on = np.where(db > overall - 12)[0]
    rgb = frames(path, fps=4, w=270, h=480, gray=False, limit=3.2)
    f0 = rgb[0].astype(np.float32)
    hsv_s = (f0.max(axis=2) - f0.min(axis=2)) / (f0.max(axis=2) + 1e-3)
    gy, gx = np.gradient(f0.mean(axis=2))
    rg, yb = f0[..., 0] - f0[..., 1], 0.5 * (f0[..., 0] + f0[..., 1]) - f0[..., 2]
    faces = _faces(list(rgb))
    return {
        "mot_0_1": seg(0, 1), "mot_1_3": seg(1, 3), "mot_rest": seg(3, dur),
        "cuts_0_3": float(sum(c < 3 for c in cuts)),
        "first_cut": float(min([c for c in cuts] + [dur])),
        "cps": len(cuts) / max(dur, 1),
        "audio_onset": float(on[0] * 0.1) if len(on) else dur,
        "loud_0_1": float(db[:10].max() - overall) if len(db) else -30.0,
        "loud_rel": overall,
        "bright0": float(f0.mean() / 255), "contrast0": float(f0.std() / 255),
        "sat0": float(hsv_s.mean()), "edges0": float(np.hypot(gx, gy).mean() / 255),
        "color0": float((np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)) / 255),
        "face0": float(faces[0]) if faces else 0.0,
        "face_0_3": float(np.mean(faces)) if faces else 0.0,
        "dur": dur,
        "text0": _text_area(rgb[0]),
        "change_0_1": float(np.abs(g[min(10, len(g) - 1)] - g[0]).mean() / 255),
    }


if __name__ == "__main__":
    import json, sys
    print(json.dumps(extract(sys.argv[1]), indent=1))
