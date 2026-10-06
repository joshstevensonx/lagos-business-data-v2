import asyncio
from ..sources.site_contacts.crawler import WebsiteCrawler

async def enrich_websites(records,cache_path='out/url_cache.sqlite3',max_sites=None):
    crawler=WebsiteCrawler(cache_path=cache_path); tasks=[]
    for row in records:
        if row.get('website') and (max_sites is None or len(tasks)<max_sites): tasks.append((row,asyncio.create_task(crawler.enrich(row['website']))))
    for row,task in tasks:
        data=await task
        row['email']='; '.join(data.get('emails',[])); row['whatsapp']=data.get('whatsapp','')
        row['delivery_text_signals']=data.get('delivery_signals',[])
        for field,key in [('instagram','instagram'),('facebook','facebook'),('twitter','twitter'),('linkedin','linkedin'),('tiktok','tiktok')]: row[field]=data.get('socials',{}).get(key,'')
        row['online_order']=data.get('online_order',False)
    return records
