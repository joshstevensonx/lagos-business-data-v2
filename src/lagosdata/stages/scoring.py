from collections import Counter
from ..score import score_business,band

def score_records(records):
    counts=Counter((r.get('name') or '').lower() for r in records)
    for row in records:
        score,components,category=score_business(row,counts)
        row['score']=score; row['score_components']=components; row['delivery_category']=category; row['band']=band(score)
        enriched=bool(row.get('additional_info') or row.get('delivery_text_signals'))
        row['score_basis']='Full' if enriched else 'Floor - not enriched'
    return records
