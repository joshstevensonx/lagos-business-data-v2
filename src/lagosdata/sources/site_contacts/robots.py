from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx

class Robots:
    def __init__(self, user_agent='LagosLocalBusinessDataCollector/0.1', timeout=10):
        self.ua=user_agent; self.timeout=timeout; self.cache={}
    async def allowed(self,url):
        p=urlparse(url); origin=f'{p.scheme}://{p.netloc}'
        if origin not in self.cache:
            rp=RobotFileParser(); rp.set_url(origin+'/robots.txt')
            try:
                async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True) as c:
                    r=await c.get(origin+'/robots.txt',headers={'User-Agent':self.ua})
                if r.status_code < 400: rp.parse(r.text.splitlines())
                else: rp.parse(['User-agent: *','Allow: /'])
            except httpx.HTTPError: rp.parse(['User-agent: *','Disallow: /'])
            self.cache[origin]=rp
        return self.cache[origin].can_fetch(self.ua,url)
