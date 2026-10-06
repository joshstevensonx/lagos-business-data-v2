from .base import DirectorySource
class VConnectSource(DirectorySource):
    name='VConnect'; selectors={'card':'.listing-card, .business-card, .search-result','name':'h2, h3, .business-name, a','address':'.address, .location','phone':'.phone, .telephone'}
