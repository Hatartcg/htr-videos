# News episode builder (أخبار وأسعار TCG)

Builds a 1080x1920 episode in the fixed HTR news look (host character plate + top card panel).

1. Plate: `videos/news_ep11_ig.mp4` (host + background + footer). Copy it to `plate.mp4` in the work folder (or set env PLATE).
2. `img/` folder with the card/product images named in episode.json (official or TCGplayer images; never SAMPLE-watermarked).
3. `episode.json`: {"total": seconds, "date_label": "19 أكتوبر 2026", "imgdir": "img", "segs": [...]}.
   Each seg: s, e (seconds, from the voice word timings), accent (hex), chip (game label, optional), title, sub, img
   (file name, list of 2-4 file names for a fanned card row, "title" for the أخبار وأسعار TCG card, "cta" for the closing question).
   Order: hook seg → "title" seg (intro line) → news segs → "cta" seg.
4. Voice: Hadi HTR clone (eleven_v4). Insert the intro clip `fetch/ep10_htr.mp3` (0–3.0 s, "وهذه أخبار وأسعار TCG مع هتر") after the hook — never regenerate هتر.
5. Render: `EP=episode.json python3 build.py stills 1 5 15` to check, then `python3 build.py 0 T out.mp4`, mix a light music bed ducked under the voice, mux.
Example: see ep12 (2026-10-19).
