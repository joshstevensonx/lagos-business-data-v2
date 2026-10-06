"""Directory parser base. Site selectors are intentionally local to each adapter."""
import asyncio
from urllib.parse import urlparse,urljoin
import httpx
from selectolax.lexbor import LexborHTMLParser as HTMLParser
from ..site_contacts.robots import Robots

class DirectorySource:
    name='directory'; selectors={'card':'','name':'','address':'','phone':''}
    def __init__(self,rate_per_second=1.0,user_agent='Lagos Local Business Data Collector/0.1',max_pages=5):
        self.delay=1/max(rate_per_second,0.05); self.ua=user_agent; self.robots=Robots(user_agent); self._last=0;self.max_pages=max_pages
    def parse(self,html,url=''):
        doc=HTMLParser(html); cards=doc.css(self.selectors['card']); out=[]
        for card in cards:
            def text(key):
                node=card.css_first(self.selectors.get(key,'')) if self.selectors.get(key) else None
                return node.text(strip=True) if node else ''
            name=text('name')
            if name: out.append({'name':name,'addr':text('address'),'phone':text('phone'),'source':self.name,'source_url':url})
        return out
    async def fetch(self,url):
        rows=[];next_url=url;seen=set()
        async with httpx.AsyncClient(timeout=15,follow_redirects=True,headers={'User-Agent':self.ua}) as client:
            for _ in range(self.max_pages):
                if not next_url or next_url in seen:break
                seen.add(next_url)
                if not await self.robots.allowed(next_url):
                    if not rows: return []
                    break
                await asyncio.sleep(max(0,self.delay-(asyncio.get_event_loop().time()-self._last))); self._last=asyncio.get_event_loop().time()
                response=await client.get(next_url); response.raise_for_status();doc=HTMLParser(response.text)
                rows.extend(self.parse(response.text,str(response.url)))
                link=doc.css_first('a[rel="next"]')
                candidate=urljoin(str(response.url),link.attributes.get('href','')) if link else ''
                next_url=candidate if candidate and urlparse(candidate).netloc==urlparse(url).netloc else ''
        if not rows: raise ValueError(f'{self.name} parser found no records at {url}')
        return rows
