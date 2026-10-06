"""Coordinate-first catchment assignment and centroid derivation."""
from __future__ import annotations
import math, statistics, yaml
from pathlib import Path

def distance_km(lat, lng, area):
    return math.hypot((float(lat)-area['lat'])*110.57,
                      (float(lng)-area['lng'])*110.32*math.cos(math.radians(area['lat'])))

def nearest_area(lat, lng, areas, address='', *, core_areas=()):
    if lat not in ('', None) and lng not in ('', None):
        found = [(distance_km(lat,lng,entry),name,entry) for name,entry in areas.items()]
        if found:
            dist,name,entry = min(found)
            if entry.get('corridor'):
                c=entry['corridor']; ax,ay=c['from']; bx,by=c['to']; px,py=float(lat),float(lng)
                dx,dy=bx-ax,by-ay; t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy or 1)))
                cross=math.hypot(px-(ax+t*dx),py-(ay+t*dy))*110.57
                if cross <= c.get('width_km',1)/2: return name, 'Core catchment' if name in core_areas else 'Ring area'
            if dist <= entry.get('radius_km',0): return name, 'Core catchment' if name in core_areas else 'Ring area'
        return 'Outside catchment', 'Ring area'
    hay=(address or '').casefold()
    match=next((name for name in areas if name.casefold() in hay),None)
    if match: return match, 'Core catchment' if match in core_areas else 'Ring area'
    return 'Unassigned',''

def derive_centroids(records, area_names, min_records=15):
    out={}
    for name in area_names:
        matches=[r for r in records if name.casefold() in (r.get('addr') or '').casefold()
                 and r.get('lat') not in ('',None) and r.get('lng') not in ('',None)]
        if matches:
            out[name]={'lat':statistics.median(float(r['lat']) for r in matches),
                       'lng':statistics.median(float(r['lng']) for r in matches),
                       'radius_km':1.3,'derived_from':f'{len(matches)} records',
                       'confidence':'review required' if len(matches)<min_records else 'derived'}
        else: out[name]={'derived_from':'0 records','confidence':'review required'}
    return out

def write_areas(path, areas):
    Path(path).write_text(yaml.safe_dump({'areas':areas},sort_keys=False,allow_unicode=True),encoding='utf-8')
