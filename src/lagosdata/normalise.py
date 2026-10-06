"""Approved normalisation helpers ported verbatim from the client reference."""
import re
import unicodedata


def norm_name(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii','ignore').decode().lower()
    s = re.sub(r'\b(ltd|limited|nig|nigeria|plc|enterprises|enterprise|ventures|venture|'
               r'company|co|and|the|services|service|int\'l|international|global)\b', ' ', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s)


def norm_addr(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii','ignore').decode().lower()
    s = re.sub(r'\b(street|st|road|rd|avenue|ave|close|cl|crescent|cres|drive|dr|lane|ln|'
               r'way|estate|est|shop|suite|plot|block|flat|no)\b', ' ', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s)


def clean_phone(p):
    if not p: return ''
    raw = str(p)
    for m in re.finditer(r'(?:\+?234|0)[\s\-]?([789]\d{2}[\s\-]?\d{3}[\s\-]?\d{4})', raw):
        d = re.sub(r'\D','', m.group(1))
        if len(d) == 10: return '+234' + d
    d = re.sub(r'\D','', raw)
    if d.startswith('0') and len(d) >= 11 and d[1] in '789':
        return '+234' + d[1:11]
    if d.startswith('234'):
        rest = d[3:]
        if rest[:1] in ('7','8','9') and len(rest) >= 10:
            return '+234' + rest[:10]
        if rest[:1] == '1' and 8 <= len(rest) <= 9:
            return '+234' + rest
    if d.startswith('01') and 9 <= len(d) <= 10:
        return '+234' + d[1:]
    return ''


def street_of(addr):
    a = (addr or '').split(',')[0].strip()
    a = re.sub(r'^(shop|suite|plot|block|flat|no\.?)\s*[\w/]*\s*,?\s*', '', a, flags=re.I)
    return a[:60]


NOT_A_BUSINESS = re.compile(r'\b(bus ?stop|busstop|bus-stop|roundabout|flyover|under ?bridge)\b', re.I)


def is_poi(record):
    name = (record.get('name') or '').strip()
    label = record.get('label') or ''
    if NOT_A_BUSINESS.search(name) and not label:
        return True
    return not label and bool(re.search(r'\b(street|crescent|close|avenue|road)\s*$', name, re.I))
