from __future__ import annotations
import csv,json,sys
from datetime import datetime
from pathlib import Path
import typer
import yaml
from .config import load_config
from .state import RunState,append_raw
from .logging import RunLogger
from .areas import nearest_area,write_areas,derive_centroids
from .stages.discover import discover_osm,discover_directories,read_raw
from .stages.geo import assign_areas
from .stages.classify import classify_records
from .stages.enrich import enrich_websites,enrich_places_api
from .stages.scoring import score_records
from .stages.dedupe import run_dedupe
from .stages.report import write_master,build_report
from .stages.verify import verify_run
from .sources.osm import build_query,fetch_osm_sync,parse_elements
from .tree import ALL_TERMS
from .sources.gmaps_browser import collect_sweep,enrich_place_pages

app=typer.Typer(no_args_is_help=True,help='Lagos public business data pipeline')
def _run_dir(config,run_id=None):
    rid=run_id or datetime.now().strftime('%Y-%m-%d')+'-'+(config.run_id_prefix or config.pipeline)
    path=Path(config.output.dir)/rid;path.mkdir(parents=True,exist_ok=True);return rid,path
def _area_registry():
    path=Path('config/areas.yaml')
    if not path.exists():return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')).get('areas',{})

@app.command()
def validate(config: str=typer.Option(...,'--config')):
    cfg=load_config(config);typer.echo(f'valid: {cfg.pipeline}; {len(cfg.areas)} areas')

@app.command()
def run(config: str=typer.Option(...,'--config'),stages: str|None=typer.Option(None,'--stages'),
        max_searches: int|None=typer.Option(None,'--max-searches'),max_runtime: int|None=typer.Option(None,'--max-runtime'),
        force_term: str|None=typer.Option(None,'--force-term'),force_area: str|None=typer.Option(None,'--force-area'),
        dedupe_report: bool=typer.Option(False,'--dedupe-report'),import_csv: str|None=typer.Option(None,'--import-csv'),
        osm_via_browser: bool=typer.Option(False,'--osm-via-browser'),_run_id: str|None=typer.Option(None,hidden=True)):
    cfg=load_config(config);rid,root=_run_dir(cfg,_run_id);logger=RunLogger(root/'run.log');state=RunState(root/'state.sqlite3')
    (root/'manifest.json').write_text(json.dumps({'run_id':rid,'config':cfg.model_dump(mode='json'),'config_path':str(Path(config).resolve()),'started_at':datetime.now().isoformat()},indent=2),encoding='utf-8')
    requested=[s.strip() for s in stages.split(',')] if stages else ['discover','geo','classify','enrich','score','dedupe','report','verify']
    allowed={'discover','geo','classify','enrich','score','dedupe','report','verify'}
    if set(requested)-allowed:raise typer.BadParameter(f'unknown stages: {set(requested)-allowed}')
    try:
        if 'discover' in requested:
            if cfg.sources.osm.enabled and state.should_run('osm','all tagged POIs','wide bbox',force=bool(force_area)):
                state.start('osm','all tagged POIs','wide bbox')
                osm_rows=discover_osm(root,_area_registry(),logger,via_browser=osm_via_browser or cfg.sources.osm.via_browser)
                state.finish('osm','all tagged POIs','wide bbox','done' if osm_rows else 'failed',len(osm_rows),len(osm_rows),error='' if osm_rows else 'OSM returned no usable records; retry permitted')
            if cfg.sources.gmaps_browser.enabled:
                registry=_area_registry(); source_cfg=cfg.sources.gmaps_browser
                sweeps=source_cfg.sweeps or [{'center':[registry[a]['lat'],registry[a]['lng']],'zoom':source_cfg.zoom,'covers':[a]} for a in cfg.areas if a in registry]
                terms=cfg.taxonomy.terms or ALL_TERMS
                jobs=[]
                for si,sweep in enumerate(sweeps):
                    center=sweep.get('center') or sweep.get('centroid')
                    if not center or len(center)!=2:continue
                    area=sweep.get('id') or ','.join(sweep.get('covers',[])) or f'sweep-{si+1}'
                    for term in terms:
                        if force_term and term!=force_term:continue
                        if force_area and force_area not in area and force_area not in sweep.get('covers',[]):continue
                        if not state.should_run('gmaps',term,area,force=bool(force_term or force_area)):
                            continue
                        jobs.append({'term':term,'lat':center[0],'lng':center[1],'zoom':sweep.get('zoom',source_cfg.zoom),'area':area})
                async def persist(job,rows):
                    append_raw(root,'gmaps',rows)
                    state.finish('gmaps',job['term'],job['area'],'done',len(rows),len(rows))
                    logger.log('search_complete',source='gmaps',term=job['term'],area=job['area'],raw_count=len(rows),kept_count=len(rows))
                ceiling=max_searches if max_searches is not None else source_cfg.max_searches
                runtime=max_runtime if max_runtime is not None else source_cfg.max_runtime_minutes
                if jobs and ceiling is not None:jobs=jobs[:ceiling]
                for job in jobs:state.start('gmaps',job['term'],job['area'])
                if jobs:
                    logger.log('source_notice',source='gmaps',message='Reads public listing pages; keep volumes low and respect service limits.')
                    results,errors=asyncio.run(collect_sweep(jobs,concurrency=source_cfg.concurrency,delay=source_cfg.delay_seconds,max_searches=ceiling,max_runtime=runtime,on_result=persist))
                    for job,error in errors:
                        state.finish('gmaps',job['term'],job['area'],'failed',error=error);logger.log('source_failure',source='gmaps',term=job['term'],area=job['area'],error=error)
            if cfg.sources.directories.enabled:
                import asyncio
                asyncio.run(discover_directories(root,cfg.sources.directories,state,logger,force_term,force_area))
            if import_csv:
                with open(import_csv,newline='',encoding='utf-8-sig') as f:
                    rows=list(csv.DictReader(f))
                for r in rows:r.setdefault('source','Manual CSV')
                append_raw(root,'manual_csv',rows)
            records=read_raw(root)
        else:records=json.loads((root/'master.json').read_text(encoding='utf-8')) if (root/'master.json').exists() else read_raw(root)
        if 'geo' in requested:assign_areas(records,_area_registry(),cfg.core_areas)
        if 'classify' in requested:classify_records(records)
        if 'enrich' in requested and cfg.sources.site_contacts.enabled:
            import asyncio
            records=asyncio.run(enrich_websites(records,root/'url_cache.sqlite3',cfg.sources.site_contacts.max_sites or None))
        if 'enrich' in requested and cfg.pipeline=='delivery' and cfg.enrich.place_pages.enabled:
            records=asyncio.run(enrich_place_pages(records,cfg.enrich.place_pages.max_place_visits,cfg.enrich.place_pages.order_by))
        if 'enrich' in requested:
            records=asyncio.run(enrich_places_api(records,cfg.sources.places_api,logger=logger,pipeline=cfg.pipeline))
        if 'score' in requested and cfg.pipeline=='delivery':score_records(records)
        audit=[]
        if 'dedupe' in requested:records=run_dedupe(records,logger,audit)
        if dedupe_report:
            with (root/'dedupe_report.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['decision','kept','incoming','sources','conflicts','reason']);w.writeheader();w.writerows(audit)
        write_master(root,records)
        if 'report' in requested:build_report(root,records,cfg,state.searches())
        if 'verify' in requested:verify_run(root,cfg)
        logger.log('run_complete',run_id=rid,records=len(records),stages=requested);typer.echo(rid)
    except KeyboardInterrupt:
        state.db.commit();logger.log('interrupted',run_id=rid);typer.echo('Interrupted safely; run can resume.');raise typer.Exit(0)
    finally:state.close()

@app.command()
def resume(run_id: str=typer.Option(...,'--run-id'),config: str|None=typer.Option(None,'--config')):
    if config is None:
        manifest=Path('out')/run_id/'manifest.json'
        if not manifest.exists():raise typer.BadParameter('run manifest not found; pass --config')
        config=json.loads(manifest.read_text(encoding='utf-8')).get('config_path')
        if not config:raise typer.BadParameter('run manifest has no config_path; pass --config')
    run(config=config,stages=None,max_searches=None,max_runtime=None,force_term=None,force_area=None,dedupe_report=False,import_csv=None,osm_via_browser=False,_run_id=run_id)

@app.command()
def discover(config: str=typer.Option(...,'--config'),area: str=typer.Option(...,'--area'),term: str=typer.Option(...,'--term'),osm_via_browser: bool=typer.Option(False,'--osm-via-browser')):
    cfg=load_config(config);rid,root=_run_dir(cfg);registry=_area_registry();entry=registry.get(area)
    if not entry:raise typer.BadParameter(f'area {area!r} has no reviewed centroid in config/areas.yaml')
    delta=entry.get('radius_km',1.3)/110;query=build_query(entry['lat']-delta,entry['lng']-delta,entry['lat']+delta,entry['lng']+delta)
    rows=parse_elements(fetch_osm_sync(query,via_browser=osm_via_browser or cfg.sources.osm.via_browser))
    rows=[r for r in rows if term.casefold() in (r.get('label','')+' '+r.get('name','')).casefold()]
    append_raw(root,'osm',rows);typer.echo(f'{rid}: {len(rows)} OSM records for {area} / {term}')

@app.command()
def report(run_id: str=typer.Option(...,'--run-id'),config: str=typer.Option('config/magazine.yaml','--config')):
    cfg=load_config(config);root=Path(cfg.output.dir)/run_id;records=json.loads((root/'master.json').read_text());build_report(root,records,cfg);typer.echo(str(root/cfg.output.workbook))

@app.command()
def verify(run_id: str=typer.Option(...,'--run-id'),config: str=typer.Option('config/magazine.yaml','--config')):
    cfg=load_config(config);result=verify_run(Path(cfg.output.dir)/run_id,cfg);typer.echo(f"verified {result['records']} records")

@app.command('derive-centroids')
def derive_centroids_command(config: str=typer.Option(...,'--config')):
    cfg=load_config(config);records=[]
    for path in Path(cfg.output.dir).glob('*/raw/*.jsonl'):
        records.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line)
    write_areas('config/areas.yaml',derive_centroids(records,cfg.areas));typer.echo('Wrote config/areas.yaml; low-confidence areas require review.')

if __name__=='__main__':app()
