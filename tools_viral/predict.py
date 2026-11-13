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

FORMATS = ["challenge", "product", "news", "educational", "promo", "behind", "other"]
LABELS = {"challenge": "تحدي/لعبة يشارك فيها المشاهد", "product": "عرض منتج", "news": "أخبار/ملخص",
          "educational": "تعليمي/نصائح", "promo": "إعلان/عرض سعر", "behind": "كواليس/يوميات", "other": "أخرى"}
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


def load_history(csv_path, fly_hold):
    rows = []
    if not csv_path or not os.path.exists(csv_path):
        return rows
    for r in csv.DictReader(open(csv_path, encoding="utf-8")):
        if not r.get("watch_3s_pct"):
            continue
        rows.append({"date": dt.date.fromisoformat(r["date"][:10]),
                     "format": (r.get("format") or guess_format(r["file"])).strip(),
                     "series": (r.get("series") or guess_series(r["file"])).strip(),
                     "fly": float(r["watch_3s_pct"]) >= fly_hold})
    return rows


def predict(fmt, series, post_date, mot_1_3, history, fly_hold=45.0):
    past = [h for h in history if h["date"] < post_date]
    same = [h for h in past if h["format"] == fmt]
    p = (sum(h["fly"] for h in same) + 1) / (len(same) + 3)
    why = [f"نوع الفكرة «{LABELS.get(fmt, fmt)}»: طار {sum(h['fly'] for h in same)} من {len(same)} في هالحساب"
           if same else f"نوع الفكرة «{LABELS.get(fmt, fmt)}» جديد على هالحساب: ما فيه تاريخ نقيس عليه"]
    recent = [h for h in past if h["series"] == series and 0 <= (post_date - h["date"]).days <= FATIGUE_DAYS]
    if recent:
        p *= FATIGUE_X
        why.append(f"نفس السلسلة «{series}» نزلت قبل {min((post_date - h['date']).days for h in recent)} يوم: الجمهور يتشبع، أبعدها {FATIGUE_DAYS + 1} أيام")
    if mot_1_3 > CALM_LIMIT:
        p *= CALM_X
        why.append("الثانية 1–3 فيها حركة زايدة (%.1f× من معدل الفيديو)، والفيديوهات اللي طارت كانت أهدى وأوضح هنا" % mot_1_3)
    verdict = "بيفلير" if p >= FLY_P else "ما بيفلير"
    tips = []
    if fmt != "challenge":
        tips.append("حوّل الفكرة لتحدي يشارك فيه المشاهد (خمّن السعر، مين يفوز، اختار واحد) من أول ثانية")
    if recent:
        tips.append("أجّل هالحلقة أو غيّر السلسلة")
    if mot_1_3 > CALM_LIMIT:
        tips.append("ثبّت اللقطة من 1 إلى 3 ثواني عشان المشاهد يقرأ السؤال أو الرقم")
    return {"fly_probability": round(p, 2), "verdict": verdict, "format": fmt, "series": series,
            "history_n": len(past), "why": why, "to_make_it_fly": tips,
            "note": "تقدير من تاريخ هالحساب نفسه (اختبار سابق 92% على 36 ريل لـHTR وOtaku Haven)، مو ضمان"}
