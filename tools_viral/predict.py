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
SERIES_M = 2
MOTION_M = 2      # v6 pseudo-count for the motion/ad-style blend
EXTREME_P = 0.5   # v6 floor for a hook with an extreme dollar number (rule extreme_usd)  # pseudo-count: how strongly the format rate pulls a series with few posts


def _fatigued(h, history):
    return any(o is not h and o["series"] == h["series"] and 0 < (h["date"] - o["date"]).days <= FATIGUE_DAYS for o in history)


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


def is_motion(r):
    """v6 (23 Nov 2026): ad-pipeline motion graphics (files under ads/, or column footage=motion) vs original
    footage. Instagram says it favours original content (Creators 'original content' update, Apr 2024; Mosseri
    on Reels ranking), and on HTR IG every ad-pipeline motion reel posted organically flopped."""
    f = (r.get("footage") or "").strip().lower()
    if f:
        return f == "motion"
    return (r.get("file") or "").replace("\\", "/").lower().startswith("ads/")


def load_history(csv_path, fly_hold=45.0, fly_views=None, fly_by=None, placement=None):
    """fly = 3-second hold ≥ fly_hold when the platform gives it (Instagram), else views ≥ fly_views.
    fly_by="views": the owner's rule (16 Nov 2026) — a reel under fly_views (1,000) views is rejected,
    whatever its hold rate, so views decide when the row has them.
    placement: keep only rows whose placement starts with it ("ig", "fb"); rows without one are kept."""
    rows = []
    if not csv_path or not os.path.exists(csv_path):
        return rows
    for r in csv.DictReader(open(csv_path, encoding="utf-8")):
        pl = (r.get("placement") or "").strip()
        if placement and pl and not pl.startswith(placement):
            continue
        if fly_by == "views" and fly_views and r.get("views"):
            fly = float(r["views"]) >= fly_views
        elif r.get("watch_3s_pct"):
            fly = float(r["watch_3s_pct"]) >= fly_hold
        elif fly_views and r.get("views"):
            fly = float(r["views"]) >= fly_views
        else:
            continue
        rows.append({"date": dt.date.fromisoformat(r["date"][:10]),
                     "format": (r.get("format") or guess_format(r["file"])).strip(),
                     "series": (r.get("series") or guess_series(r["file"])).strip(), "fly": fly,
                     "dur": float(r.get("duration") or 0) or None, "placement": pl,
                     "hour": int(r["hour"]) if (r.get("hour") or "").strip() else None,
                     "motion": is_motion(r),
                     "hook_usd": float(r["hook_usd"]) if (r.get("hook_usd") or "").strip() else None})
    return rows


def best_formats(history):
    g = {}
    for h in history:
        g.setdefault(h["format"], []).append(h["fly"])
    rate = {k: (sum(v) + 1) / (len(v) + 3) for k, v in g.items() if len(v) >= 3}
    return sorted(rate, key=lambda k: -rate[k])


def predict(fmt, series, post_date, mot_1_3, history, fly_hold=45.0, rules=None, dur=None, post_hour=None,
            motion=None, hook_usd=None):
    rules = rules or {"fatigue": True, "calm": True}
    past = [h for h in history if h["date"] < post_date]
    same = [h for h in past if h["format"] == fmt]
    # v4 (17 Nov 2026): learn the format and SERIES rates only from "fresh" posts (not fatigued). Fatigued
    # repeats (same series ≤ FATIGUE_DAYS after the last one) flopped for a known reason and were dragging the
    # format rate down, so a fresh, proven series (guess: 3/3 fresh posts flew) could never reach 70%.
    fresh = [h for h in same if not _fatigued(h, past)] if rules.get("fatigue") else same
    kf, nf = sum(h["fly"] for h in fresh), len(fresh)
    p = (kf + 1) / (nf + 3)
    why = [f"نوع الفكرة «{LABELS.get(fmt, fmt)}»: طار {kf} من {nf} (بدون الحلقات المكررة ورا بعض) في هالحساب"
           if fresh else f"نوع الفكرة «{LABELS.get(fmt, fmt)}» جديد على هالحساب: ما فيه تاريخ نقيس عليه"]
    ser = [h for h in fresh if h["series"] == series]
    if ser:
        ks, ns = sum(h["fly"] for h in ser), len(ser)
        p = (ks + SERIES_M * p) / (ns + SERIES_M)
        why.append(f"سلسلة «{series}» نفسها: طارت {ks} من {ns} لما نزلت بعد راحة كافية")
    if rules.get("motion_learn") and motion:
        # v6: blend with the account's own fly-rate of motion/ad-style reels (learned from past rows only).
        mo = [h for h in past if h.get("motion")]
        km, nm = sum(h["fly"] for h in mo), len(mo)
        p = (km + MOTION_M * p) / (nm + MOTION_M)
        why.append(f"فيديو موشن/إعلاني مو تصوير أصلي: في هالحساب طار {km} من {nm} — انستقرام يقدّم المحتوى الأصلي")
    big = rules.get("extreme_usd")
    extreme = bool(big and hook_usd and hook_usd >= big)
    if extreme:
        why.append(f"رقم صادم على أول فريم (${hook_usd:,.0f}): أخبار الكروت المليونية تطير حتى قبل وقت المساء")
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
    # Posting hour (Riyadh). HTR Instagram 20 Oct–15 Nov 2026: reels posted 18:00–00:00 flew 7 of 17,
    # reels posted before 17:00 flew 1 of ~25 (the showroom audience is online in the evening).
    late = rules.get("evening_from")
    if late and post_hour is not None and post_hour < late:
        p *= 0.35
        why.append(f"وقت النشر {post_hour}:00 — في هالحساب الريلز اللي نزلت قبل {late}:00 طار منها 1 من 25، واللي نزلت من 6 المغرب طار 7 من 17")
    calm_hit = rules.get("calm") and mot_1_3 is not None and mot_1_3 > CALM_LIMIT
    if calm_hit:
        p *= CALM_X
        why.append("الثانية 1–3 فيها حركة زايدة (%.1f× من معدل الفيديو)، والفيديوهات اللي طارت كانت أهدى وأوضح هنا" % mot_1_3)
    if extreme:
        p = max(p, EXTREME_P)  # applied last: the hour/fatigue penalties do not hold a million-dollar hook back
    verdict = "بيفلير" if p >= rules.get("fly_p", FLY_P) else "ما بيفلير"
    tips = []
    top = [f for f in best_formats(past) if f != fmt][:2]
    if verdict == "ما بيفلير" and top:
        tips.append("على هالمنصة الأنواع اللي تطير أكثر: " + " ثم ".join(f"«{LABELS.get(f, f)}»" for f in top))
    if recent:
        tips.append("أجّل هالحلقة أو غيّر السلسلة")
    if short and dur and dur > short:
        tips.append(f"قصّره لـ{short} ث أو أقل")
    if late and post_hour is not None and post_hour < late:
        tips.append(f"انشره بين {late}:00 و 21:00")
    if calm_hit:
        tips.append("ثبّت اللقطة من 1 إلى 3 ثواني عشان المشاهد يقرأ السؤال أو الرقم")
    if fmt == "challenge":
        # Owner rule (16 Nov 2026): a challenge must make people engage — either the answer goes in the
        # comments (pinned comment / reply), or the video ends WITHOUT the answer and asks to share and comment.
        tips.append("تحدي: لا تعطي الجواب في الفيديو — يا تحطه في التعليقات (تعليق مثبّت/رد)، يا تنهي بدون جواب وتطلب «اكتب جوابك وأرسله لخويك»")
    return {"fly_probability": round(p, 2), "verdict": verdict, "format": fmt, "series": series,
            "history_n": len(past), "why": why, "to_make_it_fly": tips,
            "note": "تقدير من تاريخ هالحساب على هالمنصة نفسها، مو ضمان"}


def walk_forward(history, rules=None):
    """Honest test: each post predicted only from posts before it. Returns (accuracy, caught, flyers, false_alarms, n)."""
    ok = caught = fa = 0
    hs = sorted(history, key=lambda h: h["date"])
    for i, h in enumerate(hs):
        # v5 (18 Nov 2026): the posting hour (Riyadh, column "hour") is now part of the honest test, so the
        # evening rule is checked on history like the other rules (HTR IG: 87.8% → 89.8%, no flyer lost).
        r = predict(h["format"], h["series"], h["date"], None, hs[:i], rules=rules, dur=h.get("dur"), post_hour=h.get("hour"),
                    motion=h.get("motion"), hook_usd=h.get("hook_usd"))
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
    H = load_history(hp, P.get("fly_hold_pct", 45), P.get("fly_views"), P.get("fly_by"))
    if P.get("brand", "").upper() == "HTR":
        import csv as _c
        bad = [r for r in _c.DictReader(open(hp, encoding="utf-8")) if r.get("format") == "oh_reel" or "/oh/" in (r.get("file") or "") or (r.get("notes") or "").startswith("OH")]
        if bad:
            print(f"WARNING: {len(bad)} Otaku Haven rows inside {os.path.basename(hp)} — move them to calibration_otaku.csv (they inflate HTR accuracy)")
    acc, c, f, fa, n = walk_forward(H, P.get("rules"))
    print(f"{P['platform']}: {n} posts · accuracy {acc:.0%} · flyers caught {c}/{f} · false alarms {fa} · best formats {best_formats(H)[:3]}")
