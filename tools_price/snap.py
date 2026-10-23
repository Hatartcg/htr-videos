"""Daily TCGplayer market-price snapshot (via tcgcsv.com) for HTR content: fetch/snap/YYYY-MM-DD.json.gz"""
import json, gzip, time, urllib.request, datetime, os
UA = {'User-Agent': 'HTR-TCG-content/1.0 (+https://hatartcg.com)'}
CATS = [3, 68, 2, 89, 71, 85]
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except Exception as e: err = e; time.sleep(2)
    print('ERR', u, err); return {'results': []}
day = open('https://tcgcsv.com/last-updated.txt'.replace('https://tcgcsv.com/', '/tmp/')).read()[:10] if False else None
lu = urllib.request.urlopen(urllib.request.Request('https://tcgcsv.com/last-updated.txt', headers=UA)).read().decode()[:10]
out = {'date': lu, 'cats': {}}
for c in CATS:
    groups = get(f'https://tcgcsv.com/tcgplayer/{c}/groups')['results']; d = {}
    for g in groups:
        time.sleep(.2)
        for r in get(f"https://tcgcsv.com/tcgplayer/{c}/{g['groupId']}/prices")['results']:
            mp = r.get('marketPrice')
            if mp and mp >= 1: d[f"{r['productId']}|{r['subTypeName']}"] = [mp, g['groupId']]
    out['cats'][str(c)] = d; print(c, len(groups), len(d))
os.makedirs('fetch/snap', exist_ok=True)
with gzip.open(f'fetch/snap/{lu}.json.gz', 'wt') as f: json.dump(out, f, separators=(',', ':'))
print('saved', lu)
