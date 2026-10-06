"""Polite, public OpenStreetMap Overpass source with non-fatal fallback."""
from __future__ import annotations
import json
import httpx
from ..classify import classify
from ..normalise import clean_phone

ENDPOINTS=('https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter')
ATTRIBUTION='© OpenStreetMap contributors'

def build_query(south,west,north,east):
    box=f'({south},{west},{north},{east})'
    return f'''[out:json][timeout:60];(node["shop"]{box};way["shop"]{box};node["amenity"~"restaurant|cafe|fast_food|pharmacy|bank|school|place_of_worship"]{box};way["amenity"~"restaurant|cafe|fast_food|pharmacy|bank|school|place_of_worship"]{box};node["office"]{box};way["office"]{box};node["healthcare"]{box};way["healthcare"]{box};);out center tags;'''

def parse_elements(payload):
    output=[]
    for item in payload.get('elements',[]):
        tags=item.get('tags') or {}
        name=tags.get('name','').strip()
        if not name: continue
        center=item.get('center') or {}
        lat=item.get('lat',center.get('lat','')); lng=item.get('lon',center.get('lon',''))
        label=' '.join(f'{k} {tags[k]}' for k in ('shop','amenity','office','healthcare') if tags.get(k))
        group,sub=classify(label,name)
        output.append({'name':name,'place_id':f"osm:{item.get('type','')}:{item.get('id','')}",
            'label':label,'group':group,'sub':sub,'addr':', '.join(x for x in (tags.get('addr:street'),tags.get('addr:suburb'),tags.get('addr:city')) if x),
            'phone':clean_phone(tags.get('phone') or tags.get('contact:phone')),
            'website':tags.get('website') or tags.get('contact:website') or '',
            'opening_hours':tags.get('opening_hours',''),'lat':lat,'lng':lng,
            'source':'OSM','attribution':ATTRIBUTION,'osm_tags':tags})
    return output

async def fetch_osm(query, *, via_browser=False, timeout=70, browser=None, client=None):
    if via_browser:
        if browser is None: raise ValueError('browser page required for browser transport')
        return await browser.evaluate('''async (q) => { const r=await fetch("https://overpass-api.de/api/interpreter", {method:"POST", headers:{"Content-Type":"application/x-www-form-urlencoded"}, body:"data="+encodeURIComponent(q)}); if(!r.ok) throw new Error("Overpass HTTP "+r.status); return await r.json(); }''',query)
    own=client is None
    client=client or httpx.AsyncClient(timeout=timeout,headers={'User-Agent':'LagosLocalBusinessDataCollector/0.1 (public OSM query)'})
    errors=[]
    try:
        for endpoint in ENDPOINTS:
            try:
                response=await client.post(endpoint,data={'data':query})
                response.raise_for_status(); return response.json()
            except (httpx.HTTPError,ValueError) as exc: errors.append(f'{endpoint}: {exc}')
    finally:
        if own: await client.aclose()
    raise RuntimeError('All Overpass endpoints failed: '+'; '.join(errors))

def fetch_osm_sync(query, *, timeout=70, via_browser=False):
    if via_browser:
        async def browser_request():
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=True);page=await browser.new_page()
                await page.goto('https://www.openstreetmap.org/',wait_until='domcontentloaded',timeout=timeout*1000)
                result=await page.evaluate('''async q=>{const r=await fetch("https://overpass-api.de/api/interpreter",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"data="+encodeURIComponent(q)});if(!r.ok)throw new Error("Overpass HTTP "+r.status);return await r.json()}''',query)
                await browser.close();return result
        try:
            import asyncio
            return asyncio.run(browser_request())
        except Exception as exc:
            return {'elements':[],'error':f'browser Overpass transport failed: {exc}','attribution':ATTRIBUTION}
    errors=[]
    with httpx.Client(timeout=timeout,headers={'User-Agent':'LagosLocalBusinessDataCollector/0.1 (public OSM query)'}) as client:
        for endpoint in ENDPOINTS:
            try:
                response=client.post(endpoint,data={'data':query}); response.raise_for_status(); return response.json()
            except (httpx.HTTPError,ValueError) as exc: errors.append(str(exc))
    return {'elements':[],'error':' ; '.join(errors),'attribution':ATTRIBUTION}
