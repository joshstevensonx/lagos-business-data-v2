import asyncio
from ..sources.site_contacts.crawler import WebsiteCrawler
from ..sources.places_api import PlacesAPI

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

async def enrich_places_api(records, options, *, logger=None, pipeline='magazine'):
    """Use the explicitly enabled Enterprise field mask on top delivery prospects."""
    if not options.enabled:
        return records
    if pipeline != 'delivery':
        if logger: logger.log('source_skipped', source='places_api', reason='targeted enrichment is delivery-only')
        return records
    if 'enterprise' not in [sku.casefold() for sku in options.skus]:
        if logger: logger.log('source_skipped', source='places_api', reason='Enterprise SKU not enabled in config')
        return records
    api=PlacesAPI(ceiling_pct=options.monthly_ceiling_pct)
    candidates=[r for r in records if r.get('place_id') and r.get('source')]
    candidates.sort(key=lambda r:int(r.get('reviews') or 0),reverse=True)
    # The API enrichment is deliberately narrow. The list size is configured by
    # the existing place-page visit cap, with 100 as a conservative fallback.
    limit=options.max_records
    for row in candidates[:limit]:
        try:
            remaining=api.remaining('enterprise')
            if logger: logger.log('api_budget',source='places_api',sku='enterprise',remaining=remaining)
            data=await api.enrich(str(row['place_id']),enabled=True)
            row['places_api']=data
            for dest,src in [('phone','nationalPhoneNumber'),('website','websiteUri'),
                             ('rating','rating'),('reviews','userRatingCount')]:
                if not row.get(dest) and data.get(src) not in (None,''):
                    row[dest]=data[src]
            if logger: logger.log('api_enrichment',source='places_api',name=row.get('name',''),remaining=api.remaining('enterprise'))
        except Exception as exc:
            if logger: logger.log('source_failure',source='places_api',place_id=row.get('place_id'),error=str(exc))
            if 'ceiling reached' in str(exc): break
    return records
