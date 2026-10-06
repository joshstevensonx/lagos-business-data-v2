import json
from pathlib import Path
from ..state import append_raw
from ..sources.osm import build_query,fetch_osm_sync,parse_elements

def discover_osm(run_dir, areas, logger=None):
    if not areas:return []
    south=min(a['lat'] for a in areas.values())-.025; north=max(a['lat'] for a in areas.values())+.025
    west=min(a['lng'] for a in areas.values())-.03; east=max(a['lng'] for a in areas.values())+.03
    query=build_query(south,west,north,east); payload=fetch_osm_sync(query); rows=parse_elements(payload)
    if payload.get('error') and logger: logger.log('source_failure',source='osm',error=payload['error'])
    append_raw(run_dir,'osm',rows)
    if logger:logger.log('search_complete',source='osm',term='all tagged POIs',area='wide bbox',raw_count=len(payload.get('elements',[])),kept_count=len(rows),attribution='© OpenStreetMap contributors')
    return rows

def read_raw(run_dir):
    rows=[]
    for path in sorted((Path(run_dir)/'raw').glob('*.jsonl')):
        with path.open(encoding='utf-8') as f:
            rows.extend(json.loads(line) for line in f if line.strip())
    return rows
