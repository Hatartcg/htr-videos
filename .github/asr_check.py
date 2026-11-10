# Pronunciation check v2 (free): Whisper large-v3, no prompt (so it can't "guess" the script),
# word confidence + diff against the expected script + speaking-rate + banned-forms check.
# fetch/asr.txt lines:  file.mp3 | expected text   (expected is optional)
import json, re, subprocess, difflib, numpy as np
from faster_whisper import WhisperModel
BANNED = ["هيتر", "هتير", "هايتر", "يوغي أوه"]
def norm(s):
    s = re.sub(r"[ً-ْـٰ]", "", s)          # tashkeel/tatweel
    s = re.sub("[إأآا]", "ا", s); s = s.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"[^\w\s]", " ", s).split()
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
for line in open("fetch/asr.txt", encoding="utf-8"):
    if not line.strip(): continue
    f, _, exp = [x.strip() for x in line.partition("|")]
    a = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i","fetch/"+f,"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout, np.float32)
    segs, info = m.transcribe(a, language="ar", word_timestamps=True, beam_size=5, temperature=0, condition_on_previous_text=False, vad_filter=False)
    words = [{"w": w.word.strip(), "s": round(w.start,2), "e": round(w.end,2), "p": round(w.probability,2)} for s in segs for w in s.words]
    dur = len(a)/16000
    rep = {"file": f, "words": words, "heard": " ".join(w["w"] for w in words)}
    rep["unclear"] = [w for w in words if w["p"] < 0.80]                     # badly articulated / mumbled
    rep["banned"] = [w for w in words if any(b in w["w"] for b in BANNED)]
    spoken = sum(w["e"]-w["s"] for w in words) or 1
    rep["chars_per_sec"] = round(sum(len(w["w"]) for w in words)/spoken, 1)  # >13 = too fast to articulate
    if exp:
        e, h = norm(exp), norm(rep["heard"])
        sm = difflib.SequenceMatcher(a=e, b=h)
        rep["match"] = round(sm.ratio(), 2)
        rep["diff"] = [{"op": op, "expected": " ".join(e[i1:i2]), "heard": " ".join(h[j1:j2])} for op,i1,i2,j1,j2 in sm.get_opcodes() if op != "equal"]
    ok = not rep["banned"] and len(rep["unclear"]) <= 1 and rep.get("match", 1) >= 0.85 and rep["chars_per_sec"] <= 13
    rep["verdict"] = "PASS" if ok else "FAIL"
    json.dump(rep, open(f"fetch/asr/{f}.v2.json","w"), ensure_ascii=False, indent=1)
    json.dump(words, open(f"fetch/asr/{f}.json","w"), ensure_ascii=False, indent=0)
    print(f, rep["verdict"], "match", rep.get("match"), "cps", rep["chars_per_sec"], "unclear", [(w["w"],w["p"]) for w in rep["unclear"]], "banned", rep["banned"], "diff", rep.get("diff"))
