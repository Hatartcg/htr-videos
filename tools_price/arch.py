"""Builds price history for chosen TCGplayer categories from tcgcsv daily archives, computes weekly movers, fetches product info for top movers."""
import sys, os, json, glob, urllib.request
root, out = sys.argv[1], sys.argv[2]
CATS = {'3': 'Pokemon', '68': 'One Piece', '2': 'Yu-Gi-Oh!', '89': 'Riftbound', '71': 'Lorcana'}
dates = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
print('dates', dates)
hist = {c: {} for c in CATS}   # cat -> key(productId|subType) -> {date: price, group}
for d in dates:
    for c in CATS:
        base = os.path.join(root, d, c)
        if not os.path.isdir(base): continue
        for g in os.listdir(base):
            f = os.path.join(base, g, 'prices')
            if not os.path.isfile(f): continue
            try: R = json.load(open(f))['results']
            except Exception: continue
            for r in R:
                mp = r.get('marketPrice')
                if mp is None: continue
                k = f"{r['productId']}|{r['subTypeName']}"
                e = hist[c].setdefault(k, {'g': g, 'p': {}}); e['p'][d] = mp
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'HTR-TCG-content/1.0 (+https://hatartcg.com)'}); return json.load(urllib.request.urlopen(req, timeout=60))
pcache = {}
def product(c, g, pid):
    if (c, g) not in pcache:
        try: pcache[(c, g)] = {p['productId']: p for p in get(f'https://tcgcsv.com/tcgplayer/{c}/{g}/products')['results']}
        except Exception: pcache[(c, g)] = {}
    return pcache[(c, g)].get(int(pid))
groups = {}
def gname(c, g):
    if c not in groups:
        try: groups[c] = {str(x['groupId']): x['name'] for x in get(f'https://tcgcsv.com/tcgplayer/{c}/groups')['results']}
        except Exception: groups[c] = {}
    return groups[c].get(str(g), '')
last = dates[-1]; wk = [d for d in dates if d <= dates[-1]]
# 7 days before last
import datetime
dl = datetime.date.fromisoformat(last); d7 = (dl - datetime.timedelta(days=7)).isoformat()
movers = {}
for c, H in hist.items():
    rows = []
    for k, e in H.items():
        p = e['p']
        if last not in p or d7 not in p: continue
        a, b = p[d7], p[last]
        if b < 15 or a < 5: continue
        ch = (b - a) / a
        if ch <= 0.08 or ch > 3: continue
        # sanity: intermediate points should not exceed 2x of final (avoid spikes)
        series = [p[d] for d in dates if d in p]
        if max(series) > b * 1.6: continue
        rows.append((ch, k, a, b))
    rows.sort(reverse=True)
    res = []
    for ch, k, a, b in rows[:40]:
        pid, st = k.split('|'); g = H[k]['g']; pr = product(c, g, pid)
        if not pr: continue
        ext = {x['name']: x['value'] for x in pr.get('extendedData', [])}
        if 'Number' not in ext and 'Rarity' not in ext: continue   # singles only
        res.append(dict(pct=round(ch * 100, 1), before=a, now=b, name=pr['name'], number=ext.get('Number'), rarity=ext.get('Rarity'), sub=st, set=gname(c, g), productId=int(pid), image=pr['imageUrl'].replace('_200w', '_in_1000x1000'), series={d: H[k]['p'].get(d) for d in dates}))
        if len(res) >= 15: break
    movers[CATS[c]] = res
json.dump(dict(dates=dates, last=last, d7=d7, movers=movers), open(os.path.join(out, 'movers.json'), 'w'), ensure_ascii=False, indent=1)
# sealed watch: specific productIds
watch = {'242436': 'Evolving Skies Booster Box'}
sealed = {}
for c, H in hist.items():
    for k, e in H.items():
        pid = k.split('|')[0]
        if pid in watch: sealed[watch[pid] + ' | ' + k] = e['p']
json.dump(sealed, open(os.path.join(out, 'sealed.json'), 'w'), indent=1)
print('done', {k: len(v) for k, v in movers.items()})
