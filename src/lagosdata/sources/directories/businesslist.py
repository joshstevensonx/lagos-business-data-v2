from .base import DirectorySource
class BusinessListSource(DirectorySource):
    name='BusinessList'; selectors={'card':'.company, .company-item, .listing-item','name':'h2, h3, .company-name, a','address':'.address, .location','phone':'.phone, .tel'}
