"""words_from_plan.py — final-timeline word list for reel_score/montage_qa (zero credits). New 26 Nov 2026.
python3 words_from_plan.py plan.json out.json   — each plan piece may have asr (word json of its src), and cuts like mixplan.
Words are shifted by (at - s0) (and through the squeezed cuts); ElevenLabs takes get +shift (default 0.25 s, lesson 25 Nov)."""
import json, sys
plan = json.load(open(sys.argv[1])); out = []
for p in plan:
    if 'asr' not in p: continue
    W = json.load(open(p['asr'])); s0 = p.get('s0', 0); s1 = p.get('s1', 1e9); sh = p.get('shift', 0)
    if 'cuts' in p:
        off = p['at']
        for a, b in p['cuts']:
            for w in W:
                m = (w['s'] + w['e']) / 2 + sh
                if a <= m < b: out.append({**w, 's': round(off + w['s'] + sh - a, 2), 'e': round(off + w['e'] + sh - a, 2)})
            off += b - a
    else:
        for w in W:
            m = (w['s'] + w['e']) / 2 + sh
            if s0 <= m < s1 and 'هههه' not in w['w']: out.append({**w, 's': round(p['at'] + max(w['s'] + sh, s0) - s0, 2), 'e': round(p['at'] + min(w['e'] + sh, s1) - s0, 2)})
json.dump(sorted(out, key=lambda w: w['s']), open(sys.argv[2], 'w'), ensure_ascii=False)
print(len(out), 'words')
