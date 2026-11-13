#!/usr/bin/env python3
"""train_hook.py — learn, from real posted reels, how the first 3 seconds predict the
3-second hold rate (the share of viewers who keep watching past 3 s).

Data: calibration CSV rows `date,file,score_estimate,hook,views,watch_3s_pct,notes`.
Output: model JSON (feature means/stds + ridge weights + "flies" threshold) used by reel_score.py.
Accuracy is measured honestly with leave-one-out (each reel predicted by a model that never saw it).

  python3 tools_viral/train_hook.py --csv tools_viral/calibration.csv --out tools_viral/hook_model.json
  # client data stays private: --csv clients/<name>/calibration.csv --out clients/<name>/hook_model.json
"""
import argparse, csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from hook_features import extract, FEATURES

FLY_HOLD = 45.0   # % holding past 3 s. HTR data (Oct–Nov 2026): every reel ≥ 50% got 1,000+ views.


def fit(X, y, lam):
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return mu, sd, w, y.mean()


def predict(m, X):
    mu, sd, w, b = m
    return ((X - mu) / sd) @ w + b


def loo(X, y, lam):
    p = np.zeros(len(y))
    for i in range(len(y)):
        k = np.arange(len(y)) != i
        p[i] = predict(fit(X[k], y[k], lam), X[i:i + 1])[0]
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--root", default="."); ap.add_argument("--cache")
    ap.add_argument("--fly", type=float, default=FLY_HOLD)
    A = ap.parse_args()
    cache = json.load(open(A.cache)) if A.cache and os.path.exists(A.cache) else {}
    rows, X, y, views = [], [], [], []
    for r in csv.DictReader(open(A.csv, encoding="utf-8")):
        f = os.path.join(A.root, r["file"])
        if not r.get("watch_3s_pct") or not os.path.exists(f):
            continue
        if f not in cache:
            cache[f] = extract(f)
            print("features:", r["file"], file=sys.stderr)
        rows.append(r); X.append([cache[f][k] for k in FEATURES]); y.append(float(r["watch_3s_pct"]))
        views.append(float(r["views"]))
    if A.cache:
        json.dump(cache, open(A.cache, "w"), indent=0)
    X, y = np.array(X), np.array(y)
    if len(y) < 8:
        sys.exit("need at least 8 posted reels with 3-second hold data")
    best = None
    for lam in (1, 3, 10, 30, 100):
        p = loo(X, y, lam)
        acc = float(((p >= A.fly) == (y >= A.fly)).mean())
        mae = float(np.abs(p - y).mean())
        if best is None or (acc, -mae) > (best[1], -best[2]):
            best = (lam, acc, mae, p)
    lam, acc, mae, p = best
    mu, sd, w, b = fit(X, y, lam)
    order = np.argsort(-np.abs(w))
    model = {"features": FEATURES, "mu": mu.tolist(), "sd": sd.tolist(), "w": w.tolist(), "b": float(b),
             "lambda": lam, "fly_hold_pct": A.fly, "n": int(len(y)),
             "loo_accuracy": round(acc, 3), "loo_mae_pct": round(mae, 1),
             "top_drivers": [[FEATURES[i], round(float(w[i]), 2)] for i in order[:8]],
             "trained_on": os.path.basename(A.csv)}
    json.dump(model, open(A.out, "w"), indent=1)
    print(json.dumps({k: model[k] for k in ("n", "lambda", "loo_accuracy", "loo_mae_pct", "top_drivers")}, ensure_ascii=False))
    for r, yy, pp, v in sorted(zip(rows, y, p, views), key=lambda t: -t[1]):
        ok = "✓" if (pp >= A.fly) == (yy >= A.fly) else "✗"
        print(f"{ok} real {yy:5.1f}%  pred {pp:5.1f}%  views {int(v):5d}  {os.path.basename(r['file'])}")


if __name__ == "__main__":
    main()
