"""Public Google Maps browser collector. Never bypasses walls or CAPTCHAs."""
from __future__ import annotations
import asyncio, random, re
from urllib.parse import quote

RESULT_JS = r'''async () => {
 const start=Date.now(), anchors=()=>document.querySelectorAll('div[role="feed"] a.hfpxzc');
 while(Date.now()-start<22000 && anchors().length<3) await new Promise(r=>setTimeout(r,500));
 let prev=anchors().length, stable=0;
 while(Date.now()-start<27000 && stable<2){const f=document.querySelector('div[role="feed"]'); if(f)f.scrollTop=f.scrollHeight; await new Promise(r=>setTimeout(r,1300)); const n=anchors().length; if(n===prev)stable++;else{stable=0;prev=n;}}
 return [...anchors()].map(a=>{const h=a.href||'',c=a.closest('div[jsaction]')||a.parentElement,txt=c?[...c.querySelectorAll('span,div')].map(x=>x.textContent.trim()).filter(Boolean):[],s=c?.querySelector('span[role="img"][aria-label]')?.getAttribute('aria-label')||'',m=s.match(/([\d.]+)\s*stars?\s*([\d,]+)?/),xy=h.match(/!3d(-?[\d.]+)!4d(-?[\d.]+)/),id=h.match(/!1s(0x[0-9a-f]+:0x[0-9a-f]+)/i);return{name:a.getAttribute('aria-label')||'',label:txt[1]||'',addr:txt[2]||'',phone:txt.find(x=>/^\+?\d[\d\s\-()]{7,}$/.test(x))||'',rating:m?Number(m[1]):'',reviews:m&&m[2]?Number(m[2].replace(/,/g,'')):'',lat:xy?Number(xy[1]):'',lng:xy?Number(xy[2]):'',place_id:id?id[1]:'',maps:h};});
}'''

def result_url(term, lat, lng, zoom=14):
    return f'https://www.google.com/maps/search/{quote(term)}/@{lat},{lng},{zoom}z'

async def collect_search(page, term, lat, lng, zoom=14, *, timeout=35):
    await page.goto(result_url(term,lat,lng,zoom),wait_until='domcontentloaded',timeout=timeout*1000)
    body=(await page.locator('body').inner_text(timeout=10000)).casefold()
    if 'captcha' in body or 'unusual traffic' in body or 'consent.google' in (page.url or ''):
        raise RuntimeError('Google Maps CAPTCHA/consent wall detected; source halted safely')
    rows=await page.evaluate(RESULT_JS)
    if not rows: raise RuntimeError('Google Maps result feed was empty')
    for row in rows: row['source']='Google Maps'
    return rows

async def collect_sweep(jobs, *, concurrency=3, delay=(2,6), max_searches=None, max_runtime=None, headless=True):
    if not 1<=concurrency<=6: raise ValueError('concurrency must be in 1..6')
    try: from playwright.async_api import async_playwright
    except ImportError as exc: raise RuntimeError('Install Playwright and browser binaries to use Google Maps') from exc
    jobs=list(jobs)[:max_searches] if max_searches else list(jobs)
    started=asyncio.get_running_loop().time(); queue=asyncio.Queue(); results=[]; errors=[]
    for job in jobs: queue.put_nowait(job)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=headless)
        async def worker(index):
            failures=0; context=await browser.new_context(viewport={'width':random.randint(1360,1920),'height':900},user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36')
            try:
                while not queue.empty():
                    if max_runtime and asyncio.get_running_loop().time()-started>=max_runtime*60: break
                    job=await queue.get()
                    try:
                        page=await context.new_page(); rows=await collect_search(page,job['term'],job['lat'],job['lng'],job.get('zoom',14)); results.append((job,rows)); failures=0
                    except Exception as exc:
                        failures+=1; errors.append((job,str(exc)))
                        if 'CAPTCHA' in str(exc) or failures>=3: break
                        await asyncio.sleep(min(60*2**(failures-1),600))
                    finally: queue.task_done()
                    await asyncio.sleep(random.uniform(*delay))
            finally: await context.close()
        await asyncio.gather(*(worker(i) for i in range(concurrency)))
        await browser.close()
    return results,errors
