from .base import DirectorySource
class NGEXSource(DirectorySource):
    name='NGEX'; selectors={'card':'.listing, .business-listing, .directory-item','name':'h2, h3, .business-name, a','address':'.address, .location','phone':'.phone, .telephone'}
