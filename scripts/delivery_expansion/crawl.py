"""Free, robots-aware crawl of business websites for email / socials / delivery wording (repo's own crawler)."""
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0,'/home/user/lagos-business-data-v2/src')
from lagosdata.sources.site_contacts.crawler import WebsiteCrawler
OUT=Path('/home/user/lagos-business-data-v2/out/expand'); DONE=OUT/'crawl.jsonl'
async def main(items):
    done=set()
    if DONE.exists(): done={json.loads(l)['key'] for l in DONE.read_text().splitlines() if l.strip()}
    todo=[i for i in items if i['key'] not in done]; print('todo',len(todo),flush=True)
    cr=WebsiteCrawler(cache_path=str(OUT/'url_cache.sqlite3'),concurrency=5)
    sem=asyncio.Semaphore(8)
    async def one(i):
        async with sem:
            try: d=await asyncio.wait_for(cr.enrich(i['website']),60)
            except Exception as e: d={'error':str(e)[:100]}
        with DONE.open('a') as f: f.write(json.dumps({'key':i['key'],**d})+'\n')
    await asyncio.gather(*(one(i) for i in todo)); print('FINISHED',flush=True)
asyncio.run(main(json.load(open(sys.argv[1]))))
