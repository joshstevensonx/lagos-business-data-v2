from .base import DirectorySource
class FinelibSource(DirectorySource):
    # Selectors match the public Lagos area listing card markup.
    name='Finelib'; selectors={'card':'.box-682','name':'.box-headings a[href*="/listing/"]','address':'.listing-info-img .cmpny-lstng-1','phone':'.tel-no-div .cmpny-lstng-1'}

    def parse(self,html,url=''):
        rows=[]
        from selectolax.lexbor import LexborHTMLParser as HTMLParser
        from urllib.parse import urljoin
        for card in HTMLParser(html).css(self.selectors['card']):
            title=card.css_first(self.selectors['name'])
            address=card.css_first(self.selectors['address'])
            phone=card.css_first(self.selectors['phone'])
            name=title.text(strip=True) if title else ''
            if not name: continue
            rows.append({'name':name,'addr':address.text(strip=True) if address else '',
                         'phone':phone.text(strip=True) if phone else '',
                         'source':self.name,'source_url':urljoin(url,title.attributes.get('href','')) if title else url})
        return rows
