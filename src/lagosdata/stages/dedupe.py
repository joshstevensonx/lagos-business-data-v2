from ..merge import deduplicate

def run_dedupe(records,logger=None,audit=None):
    rows=deduplicate(records,audit=audit)
    if logger: logger.log('stage_complete',stage='dedupe',input_count=len(records),output_count=len(rows),merges=len(audit or []))
    return rows
