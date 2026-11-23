
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
