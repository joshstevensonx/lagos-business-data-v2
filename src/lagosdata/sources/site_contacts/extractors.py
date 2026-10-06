import re
from urllib.parse import urlparse,parse_qs
from ...normalise import clean_phone

SIGNALS=re.compile(r'\b(deliver(y|ies)?|dispatch|bulk order|corporate order|catering|wholesale|we deliver|free delivery)\b',re.I)
EMAIL=re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}')
SOCIALS={'instagram':('instagram.com',),'facebook':('facebook.com','fb.com'),'twitter':('twitter.com','x.com'),'linkedin':('linkedin.com',),'tiktok':('tiktok.com',)}

def extract_contacts(html,text='',base_url=''):
    found={'emails':[],'phones':[],'whatsapp':'','socials':{},'delivery_signals':[],'online_order':False}
    for email in EMAIL.findall(text+' '+html):
        if 'noreply@' not in email.lower() and 'example.com' not in email.lower() and not email.lower().endswith(('.png','.jpg','.jpeg','.webp')) and email not in found['emails']: found['emails'].append(email)
    for phone in re.findall(r'(?:\+?234|0)[\d\s()\-]{8,16}',text):
        p=clean_phone(phone)
        if p and p not in found['phones']: found['phones'].append(p)
    for u in re.findall(r'https?://[^\s"\'<>]+',html):
        host=urlparse(u).netloc.lower(); path=urlparse(u).path.strip('/')
        if 'wa.me' in host: found['whatsapp']=clean_phone(path.split('/')[0])
        if 'api.whatsapp.com' in host: found['whatsapp']=clean_phone(parse_qs(urlparse(u).query).get('phone',[''])[0])
        for name,domains in SOCIALS.items():
            if any(d in host for d in domains) and path and not path.startswith(('share','intent','plugins')): found['socials'].setdefault(name,u)
    found['delivery_signals']=list(dict.fromkeys(m.group(0).lower() for m in SIGNALS.finditer(text)))
    found['online_order']=bool(re.search(r'order online|online ordering',text,re.I) or '/order' in html.lower())
    return found
