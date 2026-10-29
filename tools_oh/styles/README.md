# OH reel styles (rotate, never the same style 2 days in a row)
Hadi (2026-10-23): reels all looked/sounded the same -> boring. Mix styles every day.
Hadi (2026-10-23): NEVER open with "يا عشاق ..." (he calls it a dumb opening). Write a fresh, product-specific hook every reel
(question, bold claim from page facts, or fan reference), e.g. "تبي ألترا رير في كل باك؟", "ملك اللعنات صار هودي!", "حس إنك صياد من رتبة إس!".
Caption first line = the same hook, not "يا عشاق".
Each script: OH=<key> python3 <script> stills t1 t2 ... | OH=<key> python3 <script> a b out.mp4 ; add a CFG entry per product (cue times from voice word timings, VO=0.5).
Work dir per product: /home/claude/work/<key>/ with main.png, alt.png (optional), voice.wav. helpers.py = shared drawing helpers (copy next to scripts).

| style | video script | music script | look | music |
|---|---|---|---|---|
| manga | reel_manga.py | music_rock.py | paper + halftone, speed lines, speech bubbles, ink-slab wipes | anime-opening rock guitars |
| holo unboxing | reel_holo.py | music_trap.py | black stage + spotlight, rainbow foil text, 3D box, card fan, floor reflection | dark trap (808, rolls, bells) |
| cinematic dark | reel_cine.py | music_taiko.py or music_gothic.py | letterbox, smoke, crimson/violet neon, grain, wipe reveals | taiko + shakuhachi-style flute + brass stabs |
| game system HUD | reel_sys.py | music_edm.py | grid, cyan UI windows ([ NOTIFICATION ] etc), typewriter, glitch | EDM four-on-floor, sidechain |
| classic (old) | ../reel_example.py | ../music_example.py | purple rays + stars | J-pop/future-bass |
Note (2026-10-29): Dandadan "T-shirt" page (p360516703) shows green earrings, not a T-shirt - skipped.
Ideas still unused: retro arcade/pixel, lofi/vlog, kinetic typography, VHS 90s anime, paper-cut collage.
Log the style in oh_log.md (6th column) so the next run picks a different one.
