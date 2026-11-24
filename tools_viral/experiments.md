
## 2026-11-23 — reel-coach (v6)
Data fix first: 28 Otaku Haven rows had been added again to calibration.csv (commit 9d1f9bdc); removed (all but one were
already in calibration_otaku.csv; that one moved). predict.py now prints a WARNING when OH rows appear in an HTR history.
Added 4 HTR reels of 22 Nov (song v1 122, song v2 151, Mew $4,000 news 232, OP-18 dead-boxes explainer 268) and 1 OH (AoT hoodie 73).

Walk-forward HTR IG, n=56 (honest, HTR only):
| variant | accuracy | flyers caught | false alarms |
|---|---|---|---|
| baseline v5 | 87.5% | 5/9 | 3 |
| A motion_learn (ad-pipeline motion vs original footage, blended with own motion fly-rate, M=2) | 89.3% | 5/9 | 2 | KEEP
| B extreme_usd ≥ $1,000,000 on frame 1 → floor 0.50 | 87.5% | 6/9 | 4 | KEEP (flyer +1, FA +1 allowed)
| B2 extreme_usd ≥ $4,000 | 85.7% | 6/9 | 5 | rejected
| A+B (shipped) | 89.3% | 6/9 | 3 |
Otaku IG n=34: 100% / 0 of 0 flyers / FA 0 before and after (no flyers yet — accuracy there means nothing).
Still missed: vs 23 Oct (first VS ever), pack_rarities_explainer 29 Oct (educational, real footage?), 30th UPC news 17 Nov (+$300 only — not extreme).
B caught Pikachu $5M (8 Nov) and raised Magikarp $1.1M (893 views, 15 Nov) as a false alarm.
Platform prior: platform_refs.csv (8 vidIQ IG outliers, Sep–Nov 2026): 8/8 real footage (hands/face), 6/8 show a dollar figure in the first 3 s.
Not tried yet / next: share trigger in caption (mixed on HTR: Pikachu yes-flew, Magikarp yes-flopped, Romance Dawn no-flew);
'real person on screen' feature for news (30th UPC had Hadi's character); completion = avg watch / length once a duration column is filled.

## 2026-11-24 — reel-coach (v7)
Data fix first: 8 Otaku Haven rows had been added AGAIN to calibration.csv (commit 2311401, "Metricool pull 24 Nov"); all 8
were already in calibration_otaku.csv → removed. The predict.py warning missed them (files start with "oh/", not "/oh/") — fixed.
No new HTR IG reel ≥24 h (nothing posted 23 Nov; the 23 Nov reels are still "PENDING owner approval"). 48h updates: OP-18
dead boxes 364 (shares 15 = 5.7% of reach, account best, but 3-s rate 40%), Mew $4,000 news 270, song v2 157. OH: Ichigo sword 120 (3-s 59.6%).

Walk-forward HTR IG, n=56:
| variant | accuracy | flyers caught | false alarms | decision |
|---|---|---|---|---|
| baseline v6 | 89.3% | 6/9 | 3 | |
| fly_p 0.35 / 0.45 | 89.3% | 6/9 | 3 | no change |
| momentum (a flyer in last 7 d ×1.25) | 89.3% | 6/9 | 3 | no change |
| cold account (no flyer in 14 d ×0.7) | 89.3% | 6/9 | 3 | no change |
| hold≥50% format blend | 85.7% | 6/9 | 5 | rejected |
| hold≥50% series blend | 89.3% | 5/9 | 2 | rejected (loses Pikachu $5M) |
| sends/reach of past series (platform signal) ×1.2/×0.85 | 89.3% | 6/9 | 3 | no change (only 19 rows have shares) |
| new format, real footage → floor .5 | 78.6% | 7/9 | 10 | rejected |
| A new_series_prior .45 (brand-new play-along series, real footage, BEFORE hour/fatigue penalties) | 91.1% | 7/9 | 3 | KEEP (catches first VS 23 Oct) |
| B edu_real_prior .45 (real-footage explainer, evening, not a repeat) | 91.1% | 7/9 | 3 | KEEP (catches pack-rarities explainer 29 Oct) |
| B without the fatigue guard | 89.3% | 7/9 | 4 | (collector_types_tip FA) — guard kept |
| A+B shipped | 92.9% | 8/9 | 3 | |
Otaku IG n=35: 100% / 0 of 0 flyers / FA 0 (no flyers yet — accuracy means nothing). Meta ads n=5: 60%, 0/2.
Still missed: 30th UPC news 17 Nov 13:06 (+$300 only). Still false alarms: elevator 31 Oct, market 4 Nov, Magikarp $1.1M 15 Nov (902 — near miss).
Caution: A and B each rest on ONE flyer; recheck them every run. Next: share trigger column from captions; duration column for completion.
