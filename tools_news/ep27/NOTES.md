# ep27 — Tuesday 10 Nov 2026, 13:00 — BLOCKED (not built)
Run Sun 8 Nov 07:xx (news-guard scheduled run). Estimate 599.94 credits OK, but generation FAILED: ElevenLabs quota exceeded — 28 credits remaining. No voice → no video, nothing scheduled for Tue 10 Nov 13:00.
Flow 4OzNCdvxTIwK2pVIsUSk (voice fUlcn0iRlB3xyoBnhkUW, eleven_v4, 1 take). Script = script.txt (ready). Re-run once credits are topped up.
Images: pokemontcg/tcgdex/TCGplayer image hosts unreachable from the sandbox → use text cards (like ep25 cards.py).
Facts (prices as "more than" floors):
- HOOK: Mega Rayquaza ex SIR 138/103 (Delta Reign) +$300 — TCGplayer median of latest sales $448, 5 sales Nov 4–6 ($383–449) (https://nerdsnack.com/delta-reign-chase-cards/, checked Nov 6) + TCGplayer $320 on Nov 7 (https://billsarchive.com/delta-reign.html)
- Gold Mega Rayquaza ex Mega Hyper Rare 141/103 +$280 — Bill's Archive TCGplayer $285 (Nov 7); NerdSnack cheapest listing $395 (no sales yet, Nov 6)
- Raikou ex SIR 136/103 = #3 in both lists, +$75 — Bill's $79.74 (Nov 7); NerdSnack listed from $95
- Delta Reign out Nov 6, 2026 (pokemon.com); 141 cards = 103 + 38 secret rares (Bill's Archive)
- Tip: listing price ≠ sold price (gold card: listed $395 vs market $285)
Rejected: 2005 Emerald reverse holo Rayquaza PSA 10 $384,000 (Fanatics, Nov 2) — only ComicBook.com, not on PriceCharting/SportsCardPro → unverified.

## Run Mon 9 Nov 06:5x (news scheduled run) — still BLOCKED
- Prices re-checked Nov 9: PriceCharting #138 ungraded $333.97, eBay sales Nov 8 $285–384 (pricecharting.com/game/pokemon-delta-reign/mega-rayquaza-ex-138); folio.fyi 7-day medians (Nov 7): #138 $396, #141 $395, Raikou #136 $109, ranked 1-2-3 (folio.fyi/blog/delta-reign-chase-cards); Bill's Archive TCGplayer Nov 7: $320 / $285 / $79.74. All floors (+$300 / +$280 / +$75) still hold.
- Dropped the "out Nov 6" release line (already in news_log 2026-11-03 → repeat). Line 2 now "حسب المبيعات الأخيرة". script.txt updated (6 lines).
- Flow OiCDECL6LuqH2JkKvp1E: generation FAILED — quota: 28 credits remaining, 501 needed. No voice/video. Re-run once credits are topped up (estimate ~501).

## Run Mon 9 Nov 07:1x (news-guard scheduled run) — still BLOCKED
- Metricool 9–12 Nov: no scheduled posts at all (nothing to move, Tue 10 Nov 13:00 empty).
- Estimate 500.95 credits; flow 07zLLUeHe2EwyT4S3agI generation FAILED again: 28 credits remaining. Owner notified to top up.

## Run Tue 10 Nov 06:4x (news scheduled run) — still BLOCKED
- Metricool Tue 10 Nov: nothing scheduled; no videos/news_ep27 in repo → priority build attempted.
- Estimate 500.95 credits; flow T70MLdw7rZnfovwF2cpB generation FAILED: 28 credits remaining (quota 156,802). No voice/video. Owner notified.

## Run Tue 10 Nov 07:1x (news-guard scheduled run) — still BLOCKED
- Metricool 10–13 Nov: nothing scheduled (Tue 10 + Thu 12 news slots empty; ep22–ep26 all already published, none reusable).
- Estimate 500.95; flow DAVsSbscD6p1UCmmfWmM generation FAILED: 28 credits remaining. No voice/video.

## Run Wed 11 Nov 06:5x (news scheduled run) — BUILT for Thursday 12 Nov 13:00
- Credits topped up. Estimate 500.95 → generated flow FWpa776JQejqEhatwrlp (voice fUlcn0iRlB3xyoBnhkUW, eleven_v4, 1 take) 475 credits, 33.04 s → fetch/ep27_voice.mp3.
- Line 2 changed: dropped "وهو أغلى كرت في المجموعة" (Rare Candy ranks #141 above #138 → ranking not 2-source certain).
- ASR: main take OK except end "دلتا ريم" → redid last line only (78 credits) → fetch/ep27_end.mp3, ASR "ديلترين" OK. Total 553 credits.
- Prices re-checked Nov 11: folio.fyi (sold medians, table updated Nov 10) #138 $338.21, #141 $324.99, #136 $89.99; Bill's Archive TCGplayer Nov 7: $320 / $285 / $79.74; Rare Candy Nov 6: $331.84 / $349.34 / $81.56. Floors +$300/+$280/+$75 hold; Raikou #3 in all three.
- Images: official card scans via Limitless (tpci DLR_138/141/136_R_EN_LG.png).
- Audio: hook 0–4.06 + 0.15 + intro + 0.3 + rest 4.56–28.45 (gaps>0.4 → 0.3) + 0.3 + end line, atempo 1.08 → 33.18 s (audio.py). Music: synth pluck arpeggio Dm–Bb–F–C 100 bpm, seed 27 (music.py).
