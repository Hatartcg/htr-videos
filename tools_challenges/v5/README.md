# HTR challenge series — v5 (each format has its own identity)

| Format | Renderer | Look | Music STYLE |
|---|---|---|---|
| خمّن السعر | gameshow.py | TV game show: marquee bulbs, spotlights, buzzers, split-flap price board, confetti | swing |
| أكثر ٥ ارتفعوا | market.py | stock-exchange terminal: ticker tape, عاجل, live chart, $TICKER, old→new | news |
| أيهم أغلى؟ | fight.py | arcade fighting game: health bars, ROUND/FIGHT, K.O., CONTINUE? | chip |
| أغلى ١٠ | elevator.py | elevator ride: floor display 1→10, doors open on each card, PENTHOUSE | lounge |
| البوكسات (weekly) | sealed.py | cinematic documentary: letterbox, grain, 3D box, money rain, لا تفتح, choice split | cine |

Pipeline: write script.txt (Hadi voice, lines split by [pause]) → ElevenLabs eleven_v4 (2 takes) → fetch + asr workflows →
`python3 build.py KIND spec.json script.txt take.mp3 take.mp3.json STYLE KEY out.mp4` (vsplit.py splits lines from Whisper words + RMS silences;
`SWAP=alt.mp3:alt.json:8` swaps a line from the other take). Then ASR the final vo.wav again before sending.

Number rules (Hadi voice): ALWAYS write numbers as Saudi colloquial words (ميّة، ميتين، ثلاثميّة، إحدعش، خمسطعش، ثلاث آلاف).
Never digits (they come out فصحى «تسعة وأربعون») and avoid «بـ» glued to numbers. Check every number in the ASR before sending.
