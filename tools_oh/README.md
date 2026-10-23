# Otaku Haven daily reel (template)
Example: reel_example.py (video, 1080x1920, 30fps) + music_example.py (bright J-pop/future-bass bed + SFX + ducked voice -> mix.wav).
Built for Yu-Gi-Oh! Rarity Collection booster box (2026-10-20) -> videos/oh/oh_yugioh_rarity_collection.mp4

Fonts: fetch/font_lalezar.ttf (Arabic), fetch/font_bungee.ttf (English display), fetch/font_cairo.ttf, fetch/font_anton.ttf -> copy to /home/claude/fonts/ (or edit FD).
Logo: fetch/bn_ohlogo.png. Product images: fetch from the Salla product page (cdn.salla.sa) with the fetch workflow.
Voice: ElevenLabs "Hana - Casual & Relatable" kdUY91gH5xyDHapxlthT, eleven_v4, one [excited] tag, ~12 s:
  hook (fresh per reel, NEVER "يا عشاق" - see styles/README.md) -> product -> 1-2 verified facts from the product page -> price -> "اطلبه الحين من أوتاكو هيفن!"
Voice starts at VO=0.5s; set the T_* cue times from the voice word timings / silencedetect.
Scenes: OH logo burst -> hook + game title slam -> product photo 3D fly-in + shine -> fact counter -> fact visual -> price slam -> CTA (logo, اطلبه الحين, otakkuhaveen.com).
Palette: deep purple + pink #ff3d9a + violet #8b5cf6 + cyan. No yellow. Must not look like HTR (no HTR logo/colours/music).
Render: python3 reel_example.py stills <t...>  |  python3 reel_example.py 0 7.3 pa.mp4 & python3 reel_example.py 7.3 14.6 pb.mp4
Then python3 music_example.py, concat pa/pb, mux mix.wav. Vary the music each day (tempo/key/progression/instrument).

STYLES: see tools_oh/styles/README.md - rotate manga / holo / cinematic / system-HUD (+ new ones); never the same style or music two days in a row.

TRIAL_REEL: on 2026-10-23 Instagram rejected the OH Trial Reel ("account does not meet the trial reel follower requirement"). Schedule the 19:00 REEL only until the account grows; tell Hadi.
