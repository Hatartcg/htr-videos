#!/usr/bin/env python3
"""reel_score.py — pre-publish reel check (free, local, no AI credits).

Scores a vertical video before posting and marks, second by second, where viewers are
likely to swipe away (red), may drift (yellow) or stay (green), so the weak moment can be
fixed BEFORE publishing. Heuristic, not a guarantee: use it to COMPARE versions/hooks,
and calibrate against the account's real Metricool numbers (calibration.csv).

usage: python3 reel_score.py video.mp4 [--words words.json] [--out report.json] [--png timeline.png]
  --words: optional word timings (the ASR workflow's fetch/asr/<file>.json: [{"w","s","e","p"}])
"""
import argparse, json, re, subprocess, sys
import numpy as np

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=False)

def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", path]).stdout
    return float(out.strip() or 0)

def motion_and_cuts(path, fps=10, w=72, h=128):
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h},format=gray",
               "-f", "rawvideo", "-"]).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    if len(fr) < 2:
        return np.zeros(1), [], fps
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))           # per-frame change
    # hard cut = big jump relative to local median
    med = np.median(d) + 1e-3
    cuts = [round((i + 1) / fps, 2) for i, v in enumerate(d) if v > max(18, 4 * med)]
    merged = []
    for c in cuts:
        if not merged or c - merged[-1] > 0.4:
            merged.append(c)
    return d, merged, fps

def audio_rms(path, sr=16000, win=0.5):
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]).stdout
    a = np.frombuffer(raw, np.float32)
    if a.size == 0:
        return np.zeros(1), 0.0
    n = int(sr * win)
    k = len(a) // n
    rms = np.sqrt((a[: k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    return db, float(20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--words"); ap.add_argument("--out"); ap.add_argument("--png")
    A = ap.parse_args()
    dur = probe(A.video)
    secs = max(1, int(np.ceil(dur)))
    d, cuts, fps = motion_and_cuts(A.video)
    db, overall_db = audio_rms(A.video)
    words = json.load(open(A.words, encoding="utf-8")) if A.words else []

    # per-second features
    mot = np.array([d[int(s * fps): int((s + 1) * fps)].mean() if int(s * fps) < len(d) else 0 for s in range(secs)])
    loud = np.array([db[2 * s: 2 * s + 2].max() if 2 * s < len(db) else -90 for s in range(secs)])
    speech = np.zeros(secs)
    for wd in words:
        for s in range(int(wd["s"]), min(secs, int(wd["e"]) + 1)):
            speech[s] = 1
    silent = loud < (overall_db - 18)
    mot_lo = np.percentile(mot, 30) if secs > 3 else 0

    timeline, last_cut = [], 0.0
    for s in range(secs):
        cs = [c for c in cuts if s <= c < s + 1]
        if cs:
            last_cut = cs[-1]
        since_cut = (s + 1) - last_cut
        issues = []
        if since_cut > 4: issues.append("لقطة طويلة بدون قطع (%.0f ث)" % since_cut)
        if mot[s] <= mot_lo and not cs: issues.append("حركة قليلة")
        if silent[s]: issues.append("صمت")
        elif words and not speech[s] and s > 0: issues.append("ما فيه كلام")
        level = "green" if not issues else ("yellow" if len(issues) == 1 else "red")
        timeline.append({"sec": s, "level": level, "issues": issues, "cut": bool(cs)})

    # hook (first 3 s) — the account's data: >50% watching past 3 s ⇒ 1,000+ views
    first_word = words[0]["s"] if words else None
    hook_cut = any(c < 3 for c in cuts)
    hook_motion = mot[: min(3, secs)].mean() >= np.median(mot)
    hook_audio = not silent[: min(2, secs)].any()
    hook = 0
    hook += 12 if (first_word is None or first_word <= 1.0) else (6 if first_word <= 2 else 0)
    hook += 9 if hook_cut else 0
    hook += 8 if hook_motion else 3
    hook += 6 if hook_audio else 0                      # /35
    reds = sum(t["level"] == "red" for t in timeline); yel = sum(t["level"] == "yellow" for t in timeline)
    pacing = max(0, 25 - reds * 4 - yel * 1.5)          # /25
    cps = len(cuts) / max(dur, 1)
    pacing = min(25, pacing + (3 if 0.25 <= cps <= 1.2 else 0))
    audio = 15 if -24 <= overall_db <= -8 else (9 if -30 <= overall_db <= -6 else 4)   # /15
    length = 15 if 7 <= dur <= 35 else (10 if dur <= 60 else (6 if dur <= 90 else 2))  # /15
    tail = mot[-2:].mean() >= np.median(mot) and not silent[-2:].all()
    ending = 10 if tail else 5                           # /10 (energy/loop at the end)
    score = int(round(hook + pacing + audio + length + ending))

    worst = [t for t in timeline if t["level"] == "red"][:5]
    fixes = []
    if first_word is not None and first_word > 1.0: fixes.append("الكلام يبدأ متأخر (%.1f ث) — خلي أقوى جملة/رقم في أول ثانية" % first_word)
    if not hook_cut: fixes.append("ما فيه قطع في أول ٣ ثواني — أضف قطع/زووم/نص كبير يتحرك")
    if not hook_audio: fixes.append("بداية صامتة — ابدأ بصوت أو مؤثر من أول فريم")
    for t in worst: fixes.append("ث %d: %s" % (t["sec"], "، ".join(t["issues"])))
    if dur > 60: fixes.append("الفيديو %.0f ث — جرّب نسخة أقصر (٢٠–٣٥ ث)" % dur)

    rep = {"file": A.video, "duration": round(dur, 1), "score_estimate": score,
           "breakdown": {"hook/35": hook, "pacing/25": round(pacing, 1), "audio/15": audio, "length/15": length, "ending/10": ending},
           "cuts": cuts, "cuts_per_sec": round(cps, 2), "first_word_at": first_word, "loudness_db": round(overall_db, 1),
           "timeline": timeline, "fix_first": fixes,
           "note": "تقدير بالقواعد — للمقارنة بين النسخ قبل النشر، مو ضمان. يتعاير مع أرقام Metricool الحقيقية."}
    js = json.dumps(rep, ensure_ascii=False, indent=1)
    if A.out: open(A.out, "w", encoding="utf-8").write(js)
    if A.png:
        try:
            from PIL import Image, ImageDraw
            W, H = 900, 60
            im = Image.new("RGB", (W, H), (20, 20, 24)); dr = ImageDraw.Draw(im)
            col = {"green": (34, 197, 94), "yellow": (249, 115, 22), "red": (239, 68, 68)}
            bw = W / secs
            for t in timeline:
                dr.rectangle([t["sec"] * bw + 1, 10, (t["sec"] + 1) * bw - 1, 50], fill=col[t["level"]])
            im.save(A.png)
        except Exception as e:
            print("png skipped:", e, file=sys.stderr)
    print(js if not A.out else f"score {score}/100 → {A.out}")

if __name__ == "__main__":
    main()
