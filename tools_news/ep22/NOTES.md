# ep22 — 29 أكتوبر 2026 (Thursday)
Status: script + images ready; VOICE NOT GENERATED (ElevenLabs quota out on 2026-10-28: 96 credits left, 884 needed per take).
ElevenLabs flow: slLuj9L89Xipv2BtAlVl ("أخبار هتر 29 أكتوبر 2026") — the speech node GJAxm77COTxdo1Ul849M failed (quota); re-run generation once credits are back.
Next run: continue from the voice step with script.txt (voice fUlcn0iRlB3xyoBnhkUW, eleven_v4), then intro clip, episode.json, render → videos/news_ep22_ig.mp4 + _tt.mp4.
Images in img/: psa.jpg (PSA logo, ICv2 og:image), truck.jpg (FedEx truck, Dexerto article image), imph_pack.png (official Konami pack art). Magic segment still needs an image (no headshot of Dan Ayoub — use a Magic/WotC product or logo image).
Planned on-screen segs:
- hook: chip "PSA · سرقة" accent #ef4444, title "أكثر من 6,400 كرت مقيّم انسرقت", sub "والـ FBI يحقق", img psa.jpg
- title seg
- line 2: chip "PSA · سانتا آنا", title "13 أكتوبر", sub "من شاحنة توصيل عند مكاتب PSA", img truck.jpg
- line 3: chip "PSA", title "ألغت أرقام الشهادات", sub "ونشرت قائمة الكروت المسروقة", img psa.jpg
- line 4-5: chip "Magic: The Gathering" accent #f97316? (no yellow), title "دان أيوب رئيس Wizards of the Coast", sub "من 2 نوفمبر 2026"
- line 6-7: chip "Yu-Gi-Oh!" #a855f7, title "Immortal Phoenix", sub "29 يناير 2027 · 100 كرت" / "The Winged Dragon of Ra, Sun God of Darkness", img imph_pack.png
- cta: "لو عندك كرت مقيّم غالي، كيف تحفظه؟"
Sources:
- PSA heist: https://icv2.com/articles/news/view/63717/fbi-jumps-in-to-investigate-psa-fedex-pokemon-sports-cards-heist-more-information-revealed (Oct 26) + https://www.dexerto.com/entertainment/psa-confirms-fbi-investigating-1-million-pokemon-trading-card-heist-as-full-stolen-list-revealed-3421519/ (Oct 24)
- WotC president: https://investor.hasbro.com/news-releases/news-release-details/hasbro-names-dan-ayoub-president-wizards-coast-hasbro-digital (Oct 27, official) + https://icv2.com/articles/news/view/63733/people-move-d-d-head-dan-ayoub-named-president-wizards-coast-hasbro-digital-games
- Immortal Phoenix: https://www.yugioh-card.com/en/products/imph/ (official) + https://icv2.com/articles/news/view/63730/yu-gi-oh-tcg-2027-product-release-calendar (Oct 27) / https://www.yugiohmeta.com/articles/product-news/2026/september/imph-tcg

## Built Thu 29 Oct 2026 07:25 (scheduled-task run)
ElevenLabs flow slLuj9L89Xipv2BtAlVl, node KrNqU6Nf19aqYBOr3CFq, 1 take, 883.91 credits, 57.68 s. Voice fetch/ep22_voice.mp3, ASR fetch/asr/ep22_voice.mp3.json (all words correct).
Audio: hook 0–6.62 s + 0.15 s + ep10_htr.mp3 0–3.0 s + 0.3 s + rest from 7.35 s (gaps >0.4 s trimmed to 0.3 s), atempo 1.12 → 52.67 s (audio.py). Music: ep23 music.py, seed 22.
Magic image: img/wotc.png = plain text card (no headshot used). Hook = "+6,400 كرت" from frame 0.
Output videos/news_ep22_ig.mp4 (+ _tt identical). Scheduled Thu 29 Oct 13:00 IG / 13:05 TT / 13:10 YT.
