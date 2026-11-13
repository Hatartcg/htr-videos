#!/usr/bin/env python3
"""predict.py — "will it fly?" verdict before posting, learned from the account's own history.

Why: on HTR's posted reels (Oct–Nov 2026) the edit-quality score had NO link to views
(corr -0.23, 29% right). What did predict the 3-second hold rate (and with it the views):
  1. the FORMAT — an interactive challenge/game the viewer plays along with flies; product
     showcases and news recaps don't,
  2. FATIGUE — the same series again within 3 days drops hard (guess 25 Oct flew, 27/28 Oct flopped),
  3. a calm, readable 1–3 s (flyers move LESS there: median 0.7 vs 1.1 of the clip's motion).
Walk-forward test (each reel predicted only from reels posted before it): 33/36 = 92%,
6 of 8 flyers caught, 1 false alarm. Small sample — keep calibrating on every new post.

The history CSV is per account (HTR, Otaku Haven, each High Brand client): its rows teach the
format fly-rates for THAT audience. Columns used: date,file,watch_3s_pct[,format,series].
"""
import csv, datetime as dt, os

FORMATS = ["challenge", "opening", "event", "arrival", "product", "news", "educational", "promo", "behind", "other"]
LABELS = {"challenge": "تحدي/لعبة يشارك فيها المشاهد", "opening": "فتح باكات/بوكس حقيقي وردة فعل",
          "event": "فعالية/بطولة من المحل", "arrival": "وصول شحنة/منتج جديد", "product": "عرض منتج (موشن)",
          "news": "أخبار/ملخص", "educational": "تعليمي/نصائح", "promo": "إعلان/عرض", "behind": "كواليس/يوميات",
          "other": "أخرى"}
# What each platform rewards differs (HTR, Oct–Nov 2026): Instagram → interactive challenges;
# TikTok and YouTube Shorts → real footage (pack openings, store events). So every platform keeps
# its own history and the fly-rates are learned per platform, never shared.
FATIGUE_DAYS, FATIGUE_X, CALM_LIMIT, CALM_X, FLY_P = 3, 0.35, 1.6, 0.7, 0.4


def guess_format(path):
    p = path.replace("\\", "/").lower()
    if "/challenges/" in p or any(k in p for k in ("guess", "vs_", "challenge", "quiz", "top10")):
        return "challenge"
    if "/news" in p or "news_" in p:
        return "news"
    if "promo" in p or "offer" in p or "ad_" in p:
        return "promo"
    return "product"


def guess_series(path):
    return os.path.basename(path).split("_")[0].lower()


def load_history(csv_path, fly_hold=45.0, fly_views=None):
    """fly = 3-second hold ≥ fly_hold when the platform gives it (Instagram), else views ≥ fly_views."""
    rows = []
    if not csv_path or not os.path.exists(csv_path):
        return rows
    for r in csv.DictReader(open(csv_path, encoding="utf-8")):
        if r.get("watch_3s_pct"):
            fly = float(r["watch_3s_pct"]) >= fly_hold
        elif fly_views and r.get("views"):
            fly = float(r["views"]) >= fly_views
        else:
            continue
        rows.append({"date": dt.date.fromisoformat(r["date"][:10]),
                     "format": (r.get("format") or guess_format(r["file"])).strip(),
                     "series": (r.get("series") or guess_series(r["file"])).strip(), "fly": fly,
                     "dur": float(r.get("duration") or 0) or None})
    return rows


def best_formats(history):
    g = {}
    for h in history:
        g.setdefault(h["format"], []).append(h["fly"])
    rate = {k: (sum(v) + 1) / (len(v) + 3) for k, v in g.items() if len(v) >= 3}
    return sorted(rate, key=lambda k: -rate[k])


def predict(fmt, series, post_date, mot_1_3, history, fly_hold=45.0, rules=None, dur=None):
    rules = rules or {"fatigue": True, "calm": True}
    past = [h for h in history if h["date"] < post_date]
    same = [h for h in past if h["format"] == fmt]
    p = (sum(h["fly"] for h in same) + 1) / (len(same) + 3)
    why = [f"نوع الفكرة «{LABELS.get(fmt, fmt)}»: طار {sum(h['fly'] for h in same)} من {len(same)} في هالحساب"
           if same else f"نوع الفكرة «{LABELS.get(fmt, fmt)}» جديد على هالحساب: ما فيه تاريخ نقيس عليه"]
    recent = [h for h in past if h["series"] == series and 0 <= (post_date - h["date"]).days <= FATIGUE_DAYS] \
        if rules.get("fatigue") else []
    if recent:
        p *= FATIGUE_X
        why.append(f"نفس السلسلة «{series}» نزلت قبل {min((post_date - h['date']).days for h in recent)} يوم: الجمهور يتشبع، أبعدها {FATIGUE_DAYS + 1} أيام")
    short = rules.get("short_max")
    if short and dur:
        if dur <= short:
            p *= 1.3
        else:
            p *= 0.8
            why.append(f"الطول {dur:.0f} ث: على هالمنصة الفيديوهات اللي {short} ث أو أقل تجيب مشاهدات أكثر")
    calm_hit = rules.get("calm") and mot_1_3 is not None and mot_1_3 > CALM_LIMIT
    if calm_hit:
        p *= CALM_X
        why.append("الثانية 1–3 فيها حركة زايدة (%.1f× من معدل الفيديو)، والفيديوهات اللي طارت كانت أهدى وأوضح هنا" % mot_1_3)
    verdict = "بيفلير" if p >= FLY_P else "ما بيفلير"
    tips = []
    top = [f for f in best_formats(past) if f != fmt][:2]
    if verdict == "ما بيفلير" and top:
        tips.append("على هالمنصة الأنواع اللي تطير أكثر: " + " ثم ".join(f"«{LABELS.get(f, f)}»" for f in top))
    if recent:
        tips.append("أجّل هالحلقة أو غيّر السلسلة")
    if short and dur and dur > short:
        tips.append(f"قصّره لـ{short} ث أو أقل")
    if calm_hit:
        tips.append("ثبّت اللقطة من 1 إلى 3 ثواني عشان المشاهد يقرأ السؤال أو الرقم")
    return {"fly_probability": round(p, 2), "verdict": verdict, "format": fmt, "series": series,
            "history_n": len(past), "why": why, "to_make_it_fly": tips,
            "note": "تقدير من تاريخ هالحساب على هالمنصة نفسها، مو ضمان"}


def walk_forward(history, rules=None):
    """Honest test: each post predicted only from posts before it. Returns (accuracy, caught, flyers, false_alarms, n)."""
    ok = caught = fa = 0
    hs = sorted(history, key=lambda h: h["date"])
    for i, h in enumerate(hs):
        r = predict(h["format"], h["series"], h["date"], None, hs[:i], rules=rules, dur=h.get("dur"))
        pf = r["verdict"] == "بيفلير"
        ok += pf == h["fly"]; caught += pf and h["fly"]; fa += pf and not h["fly"]
    return ok / max(1, len(hs)), caught, sum(h["fly"] for h in hs), fa, len(hs)


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(description="walk-forward accuracy of a platform profile's history")
    ap.add_argument("profile")
    A = ap.parse_args()
    P = json.load(open(A.profile, encoding="utf-8"))
    hp = P["history"] if os.path.isabs(P["history"]) else os.path.join(os.path.dirname(os.path.abspath(A.profile)), P["history"])
    H = load_history(hp, P.get("fly_hold_pct", 45), P.get("fly_views"))
    acc, c, f, fa, n = walk_forward(H, P.get("rules"))
    print(f"{P['platform']}: {n} posts · accuracy {acc:.0%} · flyers caught {c}/{f} · false alarms {fa} · best formats {best_formats(H)[:3]}")
