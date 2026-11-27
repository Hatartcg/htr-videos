
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

## 2026-11-25 — reel-coach (v8)
New HTR IG rows (Metricool pull 25 Nov 19:20 UTC): news_ep32 $660K fake-slab Rayquaza 24 Nov 13:04 → 648 (3-s 55.7%, tool 2% right);
Digimon pre-order v2 24 Nov 18:31 → 155 (3-s 29.5%; labeled promo — 6 s question + ad-style showcase; tool had said 83% as guess → wrong);
Rayquaza gold vs SIR 24 Nov 21:32 → 310 at 25 h (3-s 56.3%, tool 72% → wrong so far). Updates: OP-18 dead boxes 387, Mew 281, song v2 161.
OH: Tokyo Ghoul hoodie 127 (3-s 49.5%).

Walk-forward HTR IG, n=59 (each reel predicted only from reels before it):
| variant | accuracy | flyers caught | false alarms | decision |
|---|---|---|---|---|
| baseline v7 (with the 3 new rows) | 91.5% | 8/9 | 4 | |
| account momentum: median views of last 5 reels < 250 → ×0.5 | 88.1% | 6/9 | 4 | rejected |
| account momentum < 300 / 400 / 500 (×0.5 or ×0.35) | 81–83% | 1–2/9 | 2–3 | rejected — HTR flyers come straight out of slumps |
| A topic_fatigue ×0.5: same iconic item (Rayquaza, OP-18, Pikachu…) from ANOTHER series in the last 3 d (same-day only if earlier hour) | 93.2% | 8/9 | 3 | KEEP |
Topic window 1 d / 2 d / 3 d gave the same numbers; 3 d kept (= FATIGUE_DAYS). It fires on 2 rows, both flopped
(Rayquaza vs 8 h after the Rayquaza news; OP-18 dead boxes 3 d after the OP-18 news). Rests on 2 cases — recheck every run.
Platform basis: Instagram says it avoids showing people too many similar posts in a row / from one account (feed diversity),
and ranks Reels on watch time, likes and sends per reach — a second reel on the same card in one evening competes with itself.
Otaku IG n=36: 100% / 0 of 0 flyers / FA 0. Meta ads n=5: 60%, 0/2 (no new ad data — not reachable read-only this run).
Still missed: 30th UPC news 17 Nov 13:06. Still false alarms: elevator 31 Oct, market 4 Nov, Magikarp $1.1M 15 Nov (893).
reel_score.py: new --topic flag (default: guessed from the file name).
Sources checked by WebSearch 25 Nov: https://about.instagram.com/blog/announcements/instagram-ranking-explained (ranking signals; feed avoids too many posts from one account in a row),
https://about.instagram.com/blog/announcements/shedding-more-light-on-how-instagram-works , https://creators.instagram.com/blog/tips-for-improving-your-reach .
(The creators.instagram.com/blog/instagram-algorithm-reels-ranking link in commit c5ca52ca was not verified — use the links above.)

## 2026-11-26 — reel-coach (v9)
Data (Metricool pull 26 Nov 19:25 UTC): removed 4 DUPLICATE rows added 26 Nov 04:10 (news_ep27/28/29/30 = ig/rayquaza_news,
ig/magikarp_news, ig/30th_upc_news, ig/op18_news) — they counted the 30th UPC flyer twice; 7d numbers merged into the originals.
LATE FLYERS: Rayquaza gold vs SIR 24 Nov 21:32 went 310 (25 h) → 1,279 (48 h); news_ep32 $660K fake slab 24 Nov 13:04 went
648 (33 h) → 1,185 (shares 14). Both were called «ما طار» at 24 h — a 24 h verdict is prelim only, re-check at 48 h before judging.
New: guess 25 Nov 21:21 (Kai'Sa / Umbreon / Exodia) → 1,142 at ~22 h (3-s 56.0%), tool 83% → right.
OH: Luffy Watermelon Oda card 25 Nov 19:06 → 122 (3-s 55.5%).

Walk-forward HTR IG, n=60 (each reel predicted only from reels before it):
| variant | accuracy | flyers caught | false alarms | decision |
|---|---|---|---|---|
| baseline v8 (deduped data) | 90.0% | 9/12 | 3 | |
| A remove topic_fatigue (alone) | 91.7% | 10/12 | 3 | KEEP — the only case it rescued now flew |
| B extreme_usd 1M → 500K (alone) | 91.7% | 10/12 | 3 | KEEP (rests on 1 case: $660K) |
| A + B | 93.3% | 11/12 | 3 | SHIPPED (v9) |
| B' extreme 600K + A | 93.3% | 11/12 | 3 | same; 500K kept (round, below $660K) |
| C platform signal: send trigger «أرسله» in caption (5–26 Nov, 18 reels, counted by hand) | — | — | — | REJECTED: with trigger 2/6 flew (33%), without 5/12 (42%) — no lift; not coded |
Still missed: 30th UPC news 17 Nov 13:06 ($300). Still false alarms: elevator 31 Oct, market 4 Nov, Magikarp $1.1M (905, 95 short).
Otaku IG n=37: 100% / 0 of 0 flyers / FA 0. Meta ads n=5: 60%, 0/2 (not reachable read-only this run — skipped).
Platform refs (vidIQ, 4 new rows): 3 of 5 TCG outliers in the last 30 days are fake/tampered-slab or scam STORIES (real hands/face,
253K–828K views, 22–824× median) — same angle as news_ep32. Next candidate: a 'story' hook flag (scam/fake/betrayal) for news.

## 2026-11-27 — reel-coach (v10)
New HTR IG rows (Metricool pull 27 Nov 19:20 UTC): news_ep33 $990K Charizard PSA 10, 26 Nov 13:08 → 239 at ~33 h (3-s 51.8%, reach 196,
0 likes/shares/saves; tool v9 50% → false alarm, PRELIM — re-check at 48 h, two reels flew late last week);
top5 kinetic +$950 (Hadi face cam split screen) 26 Nov 18:31 → 1,208 (3-s 71.9% = account best; tool 72% right);
top10 Ascended Heroes 26 Nov 21:11 → 1,437 (3-s 62.3%, avg 17.6 s; tool 72% right). Same series twice in one evening — both flew.
Updates: guess 25 Nov 1,606 · Rayquaza vs 1,306 · news_ep32 1,202 (stalled) · OP-18 412 · Mew 290 · Digimon v2 179 · song v2 165.
OH: anime quote posters 26 Nov 19:08 → 122 (3-s 43.0%); Luffy Oda card 131.

Walk-forward HTR IG, n=63 (each reel predicted only from reels before it):
| variant | accuracy | flyers caught | false alarms | decision |
|---|---|---|---|---|
| baseline v9 (with the 3 new rows) | 92.1% | 13/14 | 4 | FA: elevator, market, Magikarp $1.1M, Charizard $990K |
| A extreme floor needs a STORY hook (fake/scam/theft) unless ≥ $2M | 95.2% | 13/14 | 2 | KEEP — shipped v10 |
| A2 story gate with no $2M bypass | 93.7% | 12/14 | 2 | rejected (loses Pikachu $5M) |
| A3 extreme_usd $2M, no story check | 93.7% | 12/14 | 2 | rejected (loses $660K fake-slab story) |
| A4 story gate, bypass at $1.5M | 95.2% | 13/14 | 2 | same as A; $2M kept (no case between) |
| B fly_p 0.45 / 0.35 | 92.1% | 13/14 | 4 | no change |
Platform basis: Instagram ranks Reels on watch time, likes per reach and SENDS per reach
(https://about.instagram.com/blog/announcements/instagram-ranking-explained ; Mosseri on sends:
https://www.searchenginejournal.com/instagram-algorithm-shift-why-sends-matter-more-than-ever/521389/ ). Bare-price news holds viewers
(Charizard 51.8%, Magikarp 56%) but gets 0 sends; the fake-slab story got 14. vidIQ hook search «record-price card news» (27 Nov):
6 of 6 IG outliers were real-footage stories / openings / reactions, NONE a bare price headline (2 new rows in platform_refs.csv).
Caution: A rests on 3 cases (Magikarp, Charizard, $660K). If Charizard passes 1,000 at 48 h, A turns into a miss — recheck next run.
Otaku IG n=38: 100% / 0 of 0 flyers / FA 0. Meta ads n=5: 60%, 0/2 (not reachable read-only this run — skipped).
Still missed: 30th UPC news 17 Nov ($300). Still false alarms: elevator 31 Oct, market 4 Nov.
reel_score.py: new --hook-text flag (story words are read from it and from the file name).
