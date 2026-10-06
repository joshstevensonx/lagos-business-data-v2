import csv,json,re,random
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
from ..tree import TREE

def verify_run(run_dir,config):
    root=Path(run_dir); records=json.loads((root/'master.json').read_text(encoding='utf-8')); errors=[]
    groups=set(TREE)|{'Other Local Services'}; subs={(g,s) for g,d in TREE.items() for s in d['subs']}
    for i,r in enumerate(records):
        if r.get('phone') and not re.fullmatch(r'\+234\d{10}',r['phone']): errors.append(f'record {i}: invalid phone {r["phone"]}')
        if r.get('group') not in groups: errors.append(f'record {i}: invalid group {r.get("group")}')
        if (r.get('group'),r.get('sub')) not in subs: errors.append(f'record {i}: invalid category pair')
        for k,v in r.items():
            if isinstance(v,str) and v is None: errors.append(f'record {i}: null {k}')
    unclassified=sum(r.get('sub')=='Unclassified (needs review)' for r in records)
    if records and unclassified/len(records)>=.05: errors.append(f'unclassified {unclassified}/{len(records)} is >=5%')
    for key in ('place_id','phone'):
        vals=[r.get(key) for r in records if r.get(key)]
        if len(vals)!=len(set(vals)):errors.append(f'duplicate {key}')
    samples=random.Random(0).sample(records,min(10,len(records))) if records else []
    with (root/'verify_sample.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['name','area','maps','source']);w.writeheader();w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in samples)
    manifest=root/'manifest.json'
    manifest.write_text(json.dumps({'verification_errors':errors,'records':len(records),'by_area':dict(Counter(r.get('area','') for r in records))},indent=2),encoding='utf-8')
    if errors: raise ValueError('verification failed:\n'+'\n'.join(errors))
    return {'records':len(records),'errors':errors}
