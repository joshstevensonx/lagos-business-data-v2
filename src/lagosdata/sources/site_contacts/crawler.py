"""HTTP-first same-host business website contact extraction with cache and robots."""
import asyncio
from urllib.parse import urljoin,urlparse
import httpx
from selectolax.parser import HTMLParser
from .robots import Robots
from .cache import URLCache
from .extractors import extract_contacts

PATHS=('/contact','/contact-us','/about','/order','/delivery')
class WebsiteCrawler:
    def __init__(self,cache_path='out/url_cache.sqlite3',concurrency=5,timeout=10,max_bytes=2*1024*1024):
        self.cache=URLCache(cache_path); self.sem=asyncio.Semaphore(concurrency); self.host_locks={}; self.timeout=timeout; self.max_bytes=max_bytes; self.robots=Robots()
    async def _fetch(self,url):
        cached=self.cache.get(url)
        if cached is not None:return cached
        host=urlparse(url).netloc; lock=self.host_locks.setdefault(host,asyncio.Lock())
        async with self.sem,lock:
            if not await self.robots.allowed(url): return {'skipped':'robots.txt'}
            async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True,headers={'User-Agent':'LagosLocalBusinessDataCollector/0.1'}) as client:
                async with client.stream('GET',url) as response:
                    if response.status_code>=400:return {'skipped':f'http {response.status_code}'}
                    chunks=[]; size=0
                    async for chunk in response.aiter_bytes():
                        size+=len(chunk)
                        if size>self.max_bytes:break
                        chunks.append(chunk)
            body=b''.join(chunks).decode('utf-8','replace'); tree=HTMLParser(body); text=tree.text(separator=' ',strip=True)
            value=extract_contacts(body,text,url); self.cache.put(url,value); return value
    async def enrich(self,url):
        if not url:return {}
        home=await self._fetch(url); combined=dict(home)
        if home.get('skipped'):return home
        base=urlparse(url); same=[]
        for path in PATHS:
            candidate=urljoin(url.rstrip('/')+'/',path.lstrip('/'))
            if urlparse(candidate).netloc==base.netloc:same.append(candidate)
        for candidate in same[:3]:
            extra=await self._fetch(candidate)
            if not extra.get('skipped'):
                for key in ('emails','phones','delivery_signals'):
                    combined[key]=list(dict.fromkeys(combined.get(key,[])+extra.get(key,[])))
                combined['socials']={**combined.get('socials',{}),**extra.get('socials',{})}
                combined['whatsapp']=combined.get('whatsapp') or extra.get('whatsapp','')
                combined['online_order']=combined.get('online_order') or extra.get('online_order',False)
        return combined
