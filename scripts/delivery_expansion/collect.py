"""Resumable free Google Maps sweep for the Lagos delivery-prospect expansion.
Uses the repo's own browser collector (no paid services). Halts on CAPTCHA/consent walls."""
import asyncio, json, random, sys, re
from pathlib import Path
sys.path.insert(0, '/home/user/lagos-business-data-v2/src')
from lagosdata.sources.gmaps_browser import collect_search

OUT = Path(__file__).parent
RAW = OUT / 'raw.jsonl'
VIEWPORTS = {
 'Lekki Phase 1': [(6.4350,3.4300),(6.4400,3.4600),(6.4480,3.4800)],
 'Surulere': [(6.4900,3.3450),(6.4780,3.3600),(6.4950,3.3750)],
 'Victoria Island': [(6.4250,3.4100),(6.4450,3.4300),(6.4350,3.4500)],
 'Ikoyi': [(6.4480,3.4000),(6.4560,3.4300),(6.4600,3.4550)],
 'Lekki / Ajah corridor': [(6.4420,3.5300),(6.4550,3.5600),(6.4700,3.5900)],
 'Yaba': [(6.4800,3.3450),(6.5000,3.3650),(6.5200,3.3600)],
 'Ikeja': [(6.6018,3.3515),(6.6150,3.3750),(6.5900,3.3400)],
 'Maryland / Mende': [(6.5723,3.3672),(6.5600,3.3600)],
 'Ajah': [(6.4698,3.5852),(6.4720,3.6300),(6.4600,3.6050)],
 'Apapa': [(6.4489,3.3594),(6.4380,3.3700),(6.4650,3.3500)],
 'Lekki Phase 2': [(6.4380,3.5100),(6.4420,3.5350)],
}
CORE = ['restaurant','fast food restaurant','supermarket','grocery store','pharmacy','chemist','mini mart','provision store','nigerian restaurant','hypermarket']
NEW = ['bakery','cafe','catering service','liquor store','frozen food store','ice cream shop','pizza restaurant','chicken restaurant','shawarma']

def jobs():
    out = []
    for terms in (CORE, NEW):
        for term in terms:
            for area, vps in VIEWPORTS.items():
                for i, (la, ln) in enumerate(vps):
                    out.append({'term': term, 'area': area, 'vp': i, 'lat': la, 'lng': ln, 'zoom': 14})
    return out

def key(j): return f"{j['term']}|{j['area']}|{j['vp']}"

async def main():
    done = set()
    if RAW.exists():
        for line in RAW.read_text().splitlines():
            if line.strip(): done.add(json.loads(line)['key'])
    todo = [j for j in jobs() if key(j) not in done]
    print('jobs total', len(jobs()), 'todo', len(todo), flush=True)
    from playwright.async_api import async_playwright
    q = asyncio.Queue()
    for j in todo: q.put_nowait(j)
    halt = asyncio.Event(); lock = asyncio.Lock(); count = [0]
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        async def worker(i):
            ctx = await browser.new_context(viewport={'width': 1500, 'height': 900}, locale='en-US',
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36')
            fails = 0
            while not q.empty() and not halt.is_set():
                j = await q.get()
                page = await ctx.new_page()
                try:
                    try:
                        rows = await collect_search(page, j['term'], j['lat'], j['lng'], j['zoom'])
                    except RuntimeError as e:
                        if 'empty' in str(e): rows = []
                        else: raise
                    async with lock:
                        with RAW.open('a') as f: f.write(json.dumps({'key': key(j), 'job': j, 'rows': rows}) + '\n')
                        count[0] += 1
                        if count[0] % 10 == 0: print('done', count[0], 'of', len(todo), flush=True)
                    fails = 0
                except Exception as e:
                    fails += 1; print('ERR', key(j), str(e)[:120], flush=True)
                    if 'CAPTCHA' in str(e) or 'consent' in str(e).lower(): halt.set(); print('HALT wall', flush=True)
                    elif fails >= 4: break
                    else: await asyncio.sleep(20 * fails)
                finally:
                    await page.close()
                await asyncio.sleep(random.uniform(1.5, 4))
            await ctx.close()
        await asyncio.gather(*(worker(i) for i in range(4)))
        await browser.close()
    print('FINISHED', flush=True)
asyncio.run(main())
