"""Deterministic duplicate cascade with provenance and conflict audit."""
from __future__ import annotations
from .normalise import norm_name, norm_addr, is_poi

TRUST = {'places api': 5, 'google maps': 4, 'osm': 3, 'finelib': 2, 'ngex': 2,
         'cybo': 2, 'businesslist': 2, 'vconnect': 2, 'manual csv': 1}
FILL_FIELDS = ('phone','website','maps','rating','reviews','lat','lng','addr','street','label','legacy18',
               'email','whatsapp','instagram','facebook','twitter','linkedin','tiktok')


def _rank(source: str) -> int:
    source = (source or '').lower()
    return max((rank for marker, rank in TRUST.items() if marker in source), default=0)


def _keys(record):
    keys = []
    pid = record.get('place_id') or record.get('placeId') or ''
    if pid: keys.append(('id', str(pid)))
    phone = record.get('phone') or ''
    if phone: keys.append(('p', phone))
    name = norm_name(record.get('name'))
    if name:
        keys.append(('na', name + '|' + norm_addr(record.get('addr'))[:40]))
        keys.append(('n', name))
    return keys


def deduplicate(records, *, drop_pois=True, audit=None):
    by_key, order = {}, []
    for original in records:
        row = dict(original)
        if drop_pois and is_poi(row):
            if audit is not None: audit.append({'decision':'drop_poi','record':row,'reason':'non-business POI'})
            continue
        keys = _keys(row)
        hit = next((by_key[k] for k in keys if k in by_key), None)
        if hit is None:
            row.setdefault('sources_all', [row['source']] if row.get('source') else [])
            row.setdefault('conflicts', [])
            order.append(row)
            for key in keys: by_key.setdefault(key, row)
            continue
        incoming_source = row.get('source', '')
        existing_source = hit.get('source', '')
        for field in FILL_FIELDS:
            old, new = hit.get(field, ''), row.get(field, '')
            if (old in ('', None) and new not in ('', None)):
                hit[field] = new
            elif old not in ('', None) and new not in ('', None) and old != new:
                conflict = {'field':field,'kept':old,'rejected':new,'kept_source':existing_source,'rejected_source':incoming_source}
                existing_rank=max([_rank(s) for s in hit.get('sources_all',[])] or [_rank(existing_source)])
                if _rank(incoming_source) > existing_rank:
                    conflict.update(kept=new, rejected=old, kept_source=incoming_source, rejected_source=existing_source)
                    hit[field] = new
                hit.setdefault('conflicts', []).append(conflict)
        sources = hit.setdefault('sources_all', [])
        for source in (row.get('sources_all') or [incoming_source]):
            if source and source not in sources: sources.append(source)
        if incoming_source and incoming_source != existing_source:
            hit['source'] = 'Multiple sources (cross-verified)'
        for key in keys: by_key.setdefault(key, hit)
        if audit is not None: audit.append({'decision':'merge','kept':hit.get('name',''),'incoming':row.get('name',''),'sources':[existing_source,incoming_source],'conflicts':hit.get('conflicts',[])})
    return order
