#!/usr/bin/env python3
"""montage_qa.py — «رقيب المونتاج»: strict second-by-second edit inspector (free, local).

Hard gate BEFORE a video is shown to Hadi. Verdict: مقبول / مرفوض. Any CRITICAL issue = مرفوض.
It does not replace reel_score.py (fly prediction); both must pass.

usage: python3 tools_viral/montage_qa.py video.mp4 [--words fetch/asr/x.json] [--brand htr|otaku]
          [--library videos ads reels] [--out qa.json] [--png qa.png] [--kind ad|challenge|news|reel]

Checks
  per second : frozen picture, dead second (no motion + no new speech), shot > 4 s, black/blank,
               silence, clipping, text touching the frame edge (OCR)
  whole video: length vs brand, voice starts <= 1 s, loudness, ending (fade/black/frozen),
               SAME STYLE as earlier videos (look + rhythm), SAME MUSIC as earlier videos
  speech (ASR words): forbidden words/forms, required lines (follow/like/save/comment,
               showroom location «العليا سكوير»), هتر heard as «هيتر/هاتر»
  on-screen  : the brand written «هتر» in Arabic letters (must be HTR)
"""
import argparse, glob, json, os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP_DB = os.path.join(ROOT, "tools_viral", "style_db.json")

def run(cmd):
    return subprocess.run(cmd, capture_output=True)

def duration(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).stdout or 0)

def frames(p, fps=10, w=90, h=160, color=False):
    pix, ch = ("rgb24", 3) if color else ("gray", 1)
    raw = run(["ffmpeg", "-v", "error", "-i", p, "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", pix,
               "-f", "rawvideo", "-"]).stdout
    a = np.frombuffer(raw, np.uint8)
    return a.reshape(-1, h, w, ch) if color else a.reshape(-1, h, w)

def audio(p, sr=16000):
    raw = run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]).stdout
    return np.frombuffer(raw, np.float32), sr

def loudness(p):
    err = run(["ffmpeg", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"]).stderr.decode("utf8", "ignore")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else None

# ---------- style / music fingerprints (compare with the library) ----------
def style_fp(p):
    c = frames(p, fps=2, w=36, h=64, color=True).astype(np.float32)
    if len(c) == 0:
        return None
    hsv_h = np.histogram(c.reshape(-1, 3) @ np.array([0.5, 0.3, 0.2]), bins=24, range=(0, 255))[0]
    hsv_h = hsv_h / (hsv_h.sum() + 1e-9)
    lay = c.mean(axis=0).mean(axis=2)                       # average layout (where things sit)
    lay = (lay - lay.mean()) / (lay.std() + 1e-6)
    g = frames(p, fps=10, w=72, h=128).astype(np.float32)
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2)) if len(g) > 1 else np.zeros(1)
    cut_rate = (d > max(18, 4 * np.median(d))).sum() / max(1, len(d) / 10)
    rhythm = np.histogram(d, bins=12, range=(0, 40))[0]
    rhythm = rhythm / (rhythm.sum() + 1e-9)
    return {"color": hsv_h.tolist(), "layout": lay.flatten().tolist(), "rhythm": rhythm.tolist(),
            "cut_rate": float(cut_rate)}

def music_fp(p):
    a, sr = audio(p)
    if a.size < sr:
        return None
    n = 2048
    k = a.size // n
    spec = np.abs(np.fft.rfft(a[: k * n].reshape(k, n) * np.hanning(n), axis=1))
    bands = np.logspace(np.log10(60), np.log10(6000), 33)
    f = np.fft.rfftfreq(n, 1 / sr)
    e = np.stack([spec[:, (f >= lo) & (f < hi)].mean(axis=1) for lo, hi in zip(bands[:-1], bands[1:])], 1)
    e = np.log(e + 1e-6)
    tempo = np.abs(np.diff(e.mean(axis=1)))
    ac = np.correlate(tempo - tempo.mean(), tempo - tempo.mean(), "full")[len(tempo) - 1:][:120]
    ac = ac / (ac[0] + 1e-9)
    return {"timbre": e.mean(axis=0).tolist(), "beat": ac.tolist()}

def cos(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def style_sim(x, y):
    return 0.35 * cos(x["color"], y["color"]) + 0.35 * cos(x["layout"], y["layout"]) + \
           0.2 * cos(x["rhythm"], y["rhythm"]) + 0.1 * (1 - min(1, abs(x["cut_rate"] - y["cut_rate"]) / 1.5))

def music_sim(x, y):
    t = np.asarray(x["timbre"]); u = np.asarray(y["timbre"])
    t = t - t.mean(); u = u - u.mean()
    return 0.6 * cos(t, u) + 0.4 * cos(x["beat"], y["beat"])

def load_db():
    try:
        return json.load(open(FP_DB))
    except Exception:
        return {}

def build_db(dirs):
    db = load_db()
    for d in dirs:
        for f in glob.glob(os.path.join(ROOT, d, "**", "*.mp4"), recursive=True):
            rel = os.path.relpath(f, ROOT)
            if rel in db:
                continue
            s, m = style_fp(f), music_fp(f)
            if s:
                db[rel] = {"style": s, "music": m}
    json.dump(db, open(FP_DB, "w"))
    return db

# ---------- OCR on screen ----------
def ocr_checks(p, dur):
    issues = []
    tmp = "/tmp/_qa_ocr"
    os.makedirs(tmp, exist_ok=True)
    for t in np.arange(0.5, dur, 1.0):
        img = f"{tmp}/f.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=720:-1", img])
        out = run(["tesseract", img, "-", "-l", "ara+eng", "--psm", "11", "tsv"]).stdout.decode("utf8", "ignore")
        for line in out.splitlines()[1:]:
            c = line.split("\t")
            if len(c) < 12 or not c[11].strip() or float(c[10] or -1) < 70:
                continue
            word, x, w = c[11].strip(), int(c[6]), int(c[8])
            if re.fullmatch(r"[وب]?هتر", word):
                issues.append((int(t), "critical", f"مكتوب «{word}» على الشاشة — البراند يكتب HTR بالإنجليزي"))
            if x < 6 or x + w > 714:
                issues.append((int(t), "major", f"نص لاصق بطرف الشاشة/مقصوص: «{word}»"))
    return issues

# ---------- speech rules ----------
FORBIDDEN = {
    r"هيتر|هاتر": "هتر طلعت «هيتر/هاتر» — لازم تنقال هتر طبيعي",
    r"بكتات": "الجمع «باكات» مو «بكتات»",
    r"\bكيس\b": "الكيس يقال case",
    r"ديكك": "«ديكك» غلط — استخدم ديكات",
    r"تقيلة": "تكتب «ثقيلة»",
    r"الذكاء الاصطناعي": "قل AI بالإنجليزي",
    r"دولارا|مئة|ثلاثمئة|خمسمئة": "أرقام فصحى — لازم سعودي (ميّة، ميتين...)",
    r"يصلك": "لازم «يوصلك» مو «يصلك»",
    r"يوغي أوه": "يوغي أوو (مو أوه)",
}
REQUIRED = {
    "follow": (r"تابع|اشترك|فولو", "ما فيه طلب متابعة/اشتراك"),
    "like_save": (r"لايك|احفظ|حفظ|سيف", "ما فيه طلب لايك/حفظ"),
    "comment": (r"علق|تعليق|كومنت|نقطة", "ما فيه طلب تعليق (ولو نقطة)"),
    "showroom": (r"العليا|عليا|أبحر|ابحر|معرض", "ما ذكر المعرض وموقعه (العليا سكوير) — HTR مو بس أونلاين"),
}

def speech_checks(words, brand, kind):
    issues = []
    text = " ".join(w["w"].strip() for w in words)
    for pat, msg in FORBIDDEN.items():
        for w in words:
            if re.search(pat, w["w"]):
                issues.append((int(w["s"]), "critical", msg + f" («{w['w'].strip()}» عند {w['s']:.1f}ث)"))
    if brand == "htr":
        for key, (pat, msg) in REQUIRED.items():
            if not re.search(pat, text):
                issues.append((-1, "critical", msg))
        if re.search(r"عليا", text) and not re.search(r"العليا\s*سك|عليا سكوير", text):
            issues.append((-1, "major", "«العليا» انقالت بدون «سكوير» أو انقطعت — راجعها بالأذن"))
        low = [w for w in words if re.search(r"عليا|هتر", w["w"]) and w.get("p", 1) < 0.6]
        for w in low:
            issues.append((int(w["s"]), "major", f"«{w['w'].strip()}» ثقة النطق منخفضة ({w['p']:.2f}) — اسمعها وتأكد من الضمة على العُليا"))
    if words and words[0]["s"] > 1.0:
        issues.append((0, "major", f"الصوت يبدأ متأخر ({words[0]['s']:.1f}ث) — لازم ≤ 1ث"))
    return issues

# ---------- main ----------
LEN = {"htr": (20, 35), "otaku": (10, 20)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--words")
    ap.add_argument("--brand", default="htr", choices=["htr", "otaku"])
    ap.add_argument("--kind", default="reel")
    ap.add_argument("--library", nargs="*", default=["videos", "ads", "reels"])
    ap.add_argument("--out")
    ap.add_argument("--png")
    ap.add_argument("--no-ocr", action="store_true")
    a = ap.parse_args()

    dur = duration(a.video)
    g = frames(a.video).astype(np.float32)
    fps = 10
    diff = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2)) if len(g) > 1 else np.zeros(1)
    med = np.median(diff) + 1e-3
    cuts = [(i + 1) / fps for i, v in enumerate(diff) if v > max(18, 4 * med)]
    snd, sr = audio(a.video)
    words = json.load(open(a.words)) if a.words else []
    secs = int(np.ceil(dur))
    issues = []

    # per second
    for s in range(secs):
        d = diff[s * fps:(s + 1) * fps]
        fr = g[s * fps:(s + 1) * fps]
        seg = snd[s * sr:(s + 1) * sr]
        rms = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9) if seg.size else -90
        speech = any(s <= w["s"] < s + 1 for w in words)
        if len(fr) and fr.mean() < 12:
            issues.append((s, "critical", "شاشة سودا"))
        if len(d) and d.max() < 0.6:
            issues.append((s, "critical", "صورة مجمّدة — ولا شي يتحرك"))
        elif len(d) and d.mean() < 1.5 and not speech:
            issues.append((s, "major", "ثانية ميتة: حركة ضعيفة وما فيه كلام جديد"))
        if rms < -45:
            issues.append((s, "major", "صمت"))
        if seg.size and np.abs(seg).max() > 0.995:
            issues.append((s, "minor", "تشويش/قص بالصوت (clipping)"))
    edges = [0.0] + cuts + [dur]
    for x, y in zip(edges[:-1], edges[1:]):
        if y - x > 4.0:
            issues.append((int(x), "major", f"لقطة طويلة {y - x:.1f}ث بدون قطع ({x:.1f}→{y:.1f})"))

    # whole video
    lo, hi = LEN[a.brand]
    if not lo - 2 <= dur <= hi + 5:
        issues.append((-1, "major", f"الطول {dur:.1f}ث — المطلوب {lo}–{hi}ث"))
    L = loudness(a.video)
    if L is not None and not -18 <= L <= -9:
        issues.append((-1, "major", f"مستوى الصوت {L:.1f} LUFS — المطلوب بين -16 و -10"))
    tail = diff[-2 * fps:]
    if len(tail) and tail.mean() < 1.0:
        issues.append((secs - 1, "major", "النهاية ميتة/فيد — لازم طاقة لآخر فريم"))

    # repetition vs library
    db = build_db(a.library)
    me_rel = os.path.relpath(os.path.abspath(a.video), ROOT)
    sfp, mfp = style_fp(a.video), music_fp(a.video)
    style_hits, music_hits = [], []
    for k, v in db.items():
        if k == me_rel or os.path.basename(k).split("_v")[0] == os.path.basename(a.video).split("_v")[0]:
            continue
        ss = style_sim(sfp, v["style"])
        if ss > 0.80:
            style_hits.append((round(ss, 2), k))
        if mfp and v.get("music"):
            ms = music_sim(mfp, v["music"])
            if ms > 0.93:
                music_hits.append((round(ms, 2), k))
    style_hits.sort(reverse=True); music_hits.sort(reverse=True)
    if style_hits:
        issues.append((-1, "critical", f"نفس ستايل فيديوهات سابقة ({len(style_hits)}): " +
                       "، ".join(f"{os.path.basename(k)} {s:.0%}" for s, k in style_hits[:3]) + " — غيّر الستايل"))
    if music_hits:
        issues.append((-1, "critical", "نفس الموسيقى/الإيقاع: " +
                       "، ".join(f"{os.path.basename(k)} {s:.0%}" for s, k in music_hits[:3])))

    if words:
        issues += speech_checks(words, a.brand, a.kind)
    else:
        issues.append((-1, "critical", "ما فيه فحص نطق (ASR) — شغّل fetch/asr وأعد الفحص بـ --words"))
    if not a.no_ocr:
        issues += ocr_checks(a.video, dur)

    crit = [i for i in issues if i[1] == "critical"]
    major = [i for i in issues if i[1] == "major"]
    verdict = "مرفوض" if crit or len(major) >= 3 else "مقبول"
    timeline = []
    for s in range(secs):
        lv = [i[1] for i in issues if i[0] == s]
        timeline.append("red" if "critical" in lv or "major" in lv else "yellow" if lv else "green")
    rep = {"video": a.video, "duration": round(dur, 2), "verdict": verdict,
           "critical": len(crit), "major": len(major), "cuts": len(cuts),
           "issues": [{"sec": s, "level": l, "msg": m} for s, l, m in sorted(issues, key=lambda x: (x[0], x[1]))],
           "timeline": timeline, "style_matches": style_hits[:5], "music_matches": music_hits[:5]}
    if a.out:
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1)
    if a.png:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(max(6, secs * 0.35), 1.2))
        col = {"red": "#e5484d", "yellow": "#f5a524", "green": "#30a46c"}
        for s, c in enumerate(timeline):
            ax.add_patch(plt.Rectangle((s, 0), 0.95, 1, color=col[c]))
            ax.text(s + 0.47, 0.45, str(s), ha="center", va="center", fontsize=7, color="white")
        ax.set_xlim(0, secs); ax.set_ylim(0, 1); ax.axis("off")
        ax.set_title(f"montage QA: {verdict}  (critical {len(crit)}, major {len(major)})", fontsize=9)
        plt.savefig(a.png, dpi=150, bbox_inches="tight")
    print(f"الحكم: {verdict} — حرجة {len(crit)}، كبيرة {len(major)}")
    for s, l, m in sorted(issues, key=lambda x: (x[1] != "critical", x[0])):
        print(f"  [{l}] {'عام' if s < 0 else f'ث {s}'}: {m}")
    sys.exit(0 if verdict == "مقبول" else 2)

if __name__ == "__main__":
    main()
