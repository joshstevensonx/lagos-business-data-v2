from .base import DirectorySource
class CyboSource(DirectorySource):
    name='Cybo'; selectors={'card':'.businessCard, .business-item, .search-result','name':'h2, h3, .name, a','address':'.address, .location','phone':'.phone, .tel'}
