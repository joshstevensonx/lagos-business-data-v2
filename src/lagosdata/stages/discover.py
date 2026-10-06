import json
from pathlib import Path
import asyncio
from ..state import append_raw
from ..sources.osm import build_query,fetch_osm_sync,parse_elements
from ..sources.directories.finelib import FinelibSource
from ..sources.directories.cybo import CyboSource
from ..sources.directories.ngex import NGEXSource
from ..sources.directories.businesslist import BusinessListSource
from ..sources.directories.vconnect import VConnectSource

DIRECTORY_SOURCES={'finelib':FinelibSource,'cybo':CyboSource,'ngex':NGEXSource,
                   'businesslist':BusinessListSource,'vconnect':VConnectSource}

def discover_osm(run_dir, areas, logger=None, via_browser=False):
    if not areas:return []
    south=min(a['lat'] for a in areas.values())-.025; north=max(a['lat'] for a in areas.values())+.025
    west=min(a['lng'] for a in areas.values())-.03; east=max(a['lng'] for a in areas.values())+.03
    query=build_query(south,west,north,east); payload=fetch_osm_sync(query,via_browser=via_browser); rows=parse_elements(payload)
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

async def discover_directories(run_dir,options,state,logger,force_term=None,force_area=None):
    for site in options.sites:
        factory=DIRECTORY_SOURCES.get(site.casefold())
        if not factory:
            logger.log('source_failure',source=site,error='no adapter registered');continue
        pages=options.pages.get(site.casefold(),[])
        if not pages:
            logger.log('source_skipped',source=site,reason='no explicitly configured, robots-reviewable page URLs')
            continue
        source=factory(rate_per_second=options.rate_per_second,
                       user_agent=f'Lagos Local Business Data Collector/0.1 (+mailto:{options.contact_email})',
                       max_pages=options.max_pages)
        for page in pages:
            area=page.area or 'Unassigned';term=page.term or 'directory page'
            if force_term and term!=force_term:continue
            if force_area and area!=force_area:continue
            if not state.should_run(site,term,area):continue
            state.start(site,term,area)
            if not await source.robots.allowed(page.url):
                state.finish(site,term,area,'skipped',error='robots.txt disallows URL')
                logger.log('robots_skip',source=source.name,url=page.url,area=area,term=term);continue
            try:
                rows=await source.fetch(page.url)
                for row in rows:
                    row.update(area=area,term=term)
                append_raw(run_dir,site,rows)
                state.finish(site,term,area,'done',len(rows),len(rows))
                logger.log('search_complete',source=source.name,url=page.url,term=term,area=area,raw_count=len(rows),kept_count=len(rows))
            except Exception as exc:
                state.finish(site,term,area,'failed',error=str(exc))
                logger.log('parser_failure' if isinstance(exc,ValueError) else 'source_failure',source=source.name,url=page.url,term=term,area=area,error=str(exc))
