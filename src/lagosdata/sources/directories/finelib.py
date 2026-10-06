from .base import DirectorySource
class FinelibSource(DirectorySource):
    name='Finelib'; selectors={'card':'.business-listing, .listing-item, .company-listing','name':'h2, h3, .title, a','address':'.address, .location','phone':'.phone, .telephone'}
