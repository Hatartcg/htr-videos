"""report_html.py — client-ready reel check report (one self-contained HTML file, Arabic + English).
Looks: "highbrand" (black / platinum / gold — High Brand client work), "htr" (purple / teal), "neutral".
No internal data goes in it: no other accounts' numbers, no file paths, no sales."""
import html

LOOKS = {
    "highbrand": {"bg": "#0B0B0D", "card": "#16161A", "ink": "#ECECEF", "mut": "#9A9AA3", "acc": "#C9A55C", "acc2": "#D9DCE3", "sign": "High Brand"},
    "htr": {"bg": "#14121F", "card": "#1E1B2E", "ink": "#F4F1FA", "mut": "#A9A3C2", "acc": "#8E75FF", "acc2": "#2EC4B6", "sign": "HTR"},
    "neutral": {"bg": "#111418", "card": "#1A1F26", "ink": "#EEF1F5", "mut": "#97A1AE", "acc": "#4F8DF7", "acc2": "#3CC6A8", "sign": ""},
}
LV = {"green": ("#22C55E", "يكملون"), "yellow": ("#F97316", "ممكن يطلعون"), "red": ("#EF4444", "يطلعون")}


def write_report(rep, prof, out_path, png=None):
    L = LOOKS.get(prof.get("look", "neutral"), LOOKS["neutral"])
    p = rep["prediction"]; e = html.escape
    fly = p["verdict"] == "بيفلير"
    secs = "".join(
        f'<div class="s" style="background:{LV[t["level"]][0]}" title="ث {t["sec"]}: {e("، ".join(t["issues"]) or LV[t["level"]][1])}"></div>'
        for t in rep["timeline"])
    reds = [t for t in rep["timeline"] if t["level"] == "red"]
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs) or "<li>—</li>"
    b = rep["breakdown"]
    rows = "".join(f'<tr><td>{k}</td><td>{e(str(v))}</td></tr>' for k, v in [
        ("الهوك · Hook", b["hook/35"]), ("الإيقاع · Pacing", b["pacing/25"]), ("الصوت · Audio", b["audio/15"]),
        ("الطول · Length", b["length/15"]), ("النهاية · Ending", b["ending/10"])])
    doc = f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Reel Check · {e(prof.get('brand',''))}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:{L['bg']};--card:{L['card']};--ink:{L['ink']};--mut:{L['mut']};--acc:{L['acc']};--acc2:{L['acc2']}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 'IBM Plex Sans Arabic',system-ui,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:32px 16px 56px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid #ffffff1a;padding-bottom:14px}}
.sign{{letter-spacing:.18em;text-transform:uppercase;color:var(--acc);font-weight:700;font-size:13px}}
h1{{font-size:26px;margin:0}}.en{{color:var(--mut);font-size:13px}}
.hero{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:22px 0}}
.card{{background:var(--card);border:1px solid #ffffff12;border-radius:14px;padding:18px}}
.big{{font-size:34px;font-weight:700;color:{'#22C55E' if fly else '#EF4444'}}}.num{{font-size:34px;font-weight:700;color:var(--acc2)}}
.lab{{color:var(--mut);font-size:13px}}
.tl{{display:flex;gap:2px;height:34px;margin:10px 0 6px;direction:ltr}}.s{{flex:1;border-radius:3px}}
.legend{{display:flex;gap:16px;font-size:13px;color:var(--mut)}}.legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-inline-end:6px}}
h2{{font-size:18px;margin:26px 0 8px;color:var(--acc)}}ul{{margin:0;padding-inline-start:20px}}li{{margin:4px 0}}
table{{width:100%;border-collapse:collapse}}td{{padding:7px 4px;border-bottom:1px solid #ffffff10}}td:last-child{{text-align:left;font-weight:600}}
.foot{{margin-top:30px;color:var(--mut);font-size:12px}}
@media(max-width:600px){{.hero{{grid-template-columns:1fr}}}}
</style></head><body><main>
<div class="top"><div><h1>فحص الريل قبل النشر</h1><div class="en">Pre-publish reel check · {e(prof.get('platform','').title())} · {rep['duration']}s</div></div>
<div class="sign">{e(L['sign'])}</div></div>
<div class="hero">
 <div class="card"><div class="lab">التوقع · Prediction</div><div class="big">{e(p['verdict'])}</div>
  <div class="lab">احتمال يطير تقريبًا {int(p['fly_probability']*100)}% · est. {int(p['fly_probability']*100)}% chance to take off</div></div>
 <div class="card"><div class="lab">جودة المونتاج · Edit quality</div><div class="num">{rep['score_estimate']}/100</div>
  <div class="lab">{len(reds)} ثواني حمراء · red seconds</div></div>
</div>
<div class="card"><div class="lab">وين المشاهد يكمل ووين يطلع، ثانية بثانية · Second-by-second drop-off map</div>
<div class="tl">{secs}</div>
<div class="legend"><span><i style="background:#22C55E"></i>يكملون</span><span><i style="background:#F97316"></i>ممكن يطلعون</span><span><i style="background:#EF4444"></i>يطلعون</span></div></div>
<h2>ليش هالتوقع · Why</h2><ul>{li(p['why'])}</ul>
<h2>عشان يطير · To make it take off</h2><ul>{li(p['to_make_it_fly'])}</ul>
<h2>أصلح أول · Fix first</h2><ul>{li(rep['fix_first'])}</ul>
<h2>تفاصيل المونتاج · Edit breakdown</h2><div class="card"><table>{rows}</table></div>
<p class="foot">التوقع مبني على أداء منشورات هالحساب نفسه، وهو تقدير مو ضمان. · Estimate based on this account's own past posts; not a guarantee.</p>
</main></body></html>"""
    open(out_path, "w", encoding="utf-8").write(doc)
