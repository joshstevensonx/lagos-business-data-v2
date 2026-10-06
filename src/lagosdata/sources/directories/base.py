"""Directory parser base. Site selectors are intentionally local to each adapter."""
import asyncio
import httpx
from selectolax.parser import HTMLParser
from ..site_contacts.robots import Robots

class DirectorySource:
    name='directory'; selectors={'card':'','name':'','address':'','phone':''}
    def __init__(self,rate_per_second=1.0,user_agent='Lagos Local Business Data Collector/0.1'):
        self.delay=1/max(rate_per_second,0.05); self.ua=user_agent; self.robots=Robots(user_agent); self._last=0
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
        if not await self.robots.allowed(url): return []
        await asyncio.sleep(max(0,self.delay-(asyncio.get_event_loop().time()-self._last))); self._last=asyncio.get_event_loop().time()
        async with httpx.AsyncClient(timeout=15,follow_redirects=True,headers={'User-Agent':self.ua}) as client:
            response=await client.get(url); response.raise_for_status(); rows=self.parse(response.text,url)
        if not rows: raise ValueError(f'{self.name} parser found no records at {url}')
        return rows
