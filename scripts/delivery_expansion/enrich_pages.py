"""Free Google Maps place-page enrichment (address, category, website, phone, ordering link). Resumable."""
import asyncio, json, random, re, sys
from pathlib import Path
OUT=Path('/home/user/lagos-business-data-v2/out/expand'); DONE=OUT/'pages.jsonl'
JS=r'''()=>{const g=s=>document.querySelector(s);const o={};
o.h1=g('h1')?.innerText||'';
o.cat=g('button[jsaction*="category"]')?.innerText||'';
o.items={};document.querySelectorAll('[data-item-id]').forEach(e=>{const id=e.getAttribute('data-item-id');o.items[id]={t:(e.getAttribute('aria-label')||e.innerText||'').trim().slice(0,200),h:e.href||''}});
o.body=(document.body.innerText||'').slice(0,1200);return o}'''
async def visit(ctx,c):
    url=f"https://www.google.com/maps/place/?q=place_id:{c['place_id']}" if c['place_id'].startswith('ChI') else c['maps']
    page=await ctx.new_page()
    try:
        await page.goto(url,wait_until='domcontentloaded',timeout=40000)
        await page.wait_for_selector('h1',timeout=20000); await page.wait_for_timeout(1800)
        body=(await page.locator('body').inner_text(timeout=8000)).casefold()
        if 'unusual traffic' in body or 'captcha' in body: raise RuntimeError('CAPTCHA')
        return await page.evaluate(JS)
    finally: await page.close()
async def main(cands):
    done=set()
    if DONE.exists(): done={json.loads(l)['key'] for l in DONE.read_text().splitlines() if l.strip()}
    todo=[c for c in cands if c['key'] not in done]; print('todo',len(todo),flush=True)
    from playwright.async_api import async_playwright
    q=asyncio.Queue(); [q.put_nowait(c) for c in todo]; halt=asyncio.Event(); n=[0]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        async def worker():
            ctx=await b.new_context(viewport={'width':1500,'height':900},locale='en-US',user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36')
            while not q.empty() and not halt.is_set():
                c=await q.get()
                try:
                    d=await visit(ctx,c); d['key']=c['key']
                    with DONE.open('a') as f: f.write(json.dumps(d)+'\n')
                    n[0]+=1
                    if n[0]%25==0: print('done',n[0],'of',len(todo),flush=True)
                except Exception as e:
                    print('ERR',c['key'],str(e)[:100],flush=True)
                    if 'CAPTCHA' in str(e): halt.set()
                await asyncio.sleep(random.uniform(1,3))
            await ctx.close()
        await asyncio.gather(*(worker() for _ in range(4))); await b.close()
    print('FINISHED',flush=True)
if __name__=='__main__': asyncio.run(main(json.load(open(sys.argv[1]))))
