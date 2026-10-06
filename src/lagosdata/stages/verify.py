import csv,json,re,random,shutil,subprocess,tempfile
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
from ..tree import TREE,GROUPS

STRING_FIELDS={'name','place_id','area','zone','street','addr','group','sub','legacy18','label','phone','phones_all','whatsapp','website','email','instagram','facebook','twitter','linkedin','tiktok','priority','package','contactable','verification','sales_status','notes','band','score_basis','delivery_category','source','maps','added'}

def verify_run(run_dir,config):
    root=Path(run_dir); records=json.loads((root/'master.json').read_text(encoding='utf-8')); errors=[]
    groups=set(GROUPS)|{'Other Local Services'}; subs={(g,s) for g,d in TREE.items() for s in d['subs']}|{('Other Local Services','Unclassified (needs review)')}
    for i,r in enumerate(records):
        for key in STRING_FIELDS:
            if r.get(key,'') is None: errors.append(f'record {i}: {key} is None')
        if r.get('phone') and not re.fullmatch(r'\+234\d{10}',r['phone']): errors.append(f'record {i}: invalid phone {r["phone"]}')
        if r.get('group') not in groups: errors.append(f'record {i}: invalid group {r.get("group")}')
        if (r.get('group'),r.get('sub')) not in subs: errors.append(f'record {i}: invalid category pair')
        valid_areas=set(config.areas)|{'Outside catchment','Unassigned'}
        if r.get('area') not in valid_areas: errors.append(f'record {i}: invalid area {r.get("area")}')
    unclassified=sum(r.get('sub')=='Unclassified (needs review)' for r in records)
    if records and unclassified/len(records)>=.05:
        labels=Counter((r.get('label') or '') for r in records if r.get('sub')=='Unclassified (needs review)')
        errors.append(f'unclassified {unclassified}/{len(records)} is >=5%; common labels: {labels.most_common(20)}')
    for key in ('place_id','phone'):
        vals=[r.get(key) for r in records if r.get(key)]
        if len(vals)!=len(set(vals)):errors.append(f'duplicate {key}')
    samples=random.Random(0).sample(records,min(10,len(records))) if records else []
    with (root/'verify_sample.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['name','area','maps','source']);w.writeheader();w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in samples)
    book=root/config.output.workbook
    if not book.exists():errors.append(f'workbook missing: {book}')
    else:
        wb=load_workbook(book,data_only=False,read_only=False)
        expected={'magazine':{'DASHBOARD','README','MASTER DATABASE','AREA SUMMARY','GROUP x AREA','CATEGORY TREE','RESEARCH MATRIX','SOURCE LOG'},
                  'delivery':{'DASHBOARD','README','TARGET LIST','SCORING METHOD'}}[config.pipeline]
        if set(wb.sheetnames)!=expected:errors.append(f'workbook tabs mismatch: {wb.sheetnames}')
        main=wb['MASTER DATABASE'] if config.pipeline=='magazine' else wb['TARGET LIST']
        if main.max_row-1!=len(records):errors.append(f'workbook row count {main.max_row-1} != master {len(records)}')
        formula_cells=[cell for sheet in wb for row in sheet.iter_rows() for cell in row if isinstance(cell.value,str) and cell.value.startswith('=')]
        if not formula_cells:errors.append('workbook has no live formulas')
        if any('#REF!' in cell.value or '#NAME?' in cell.value for cell in formula_cells):errors.append('workbook contains a broken formula reference')
        wb.close()
        soffice=shutil.which('soffice') or '/Users/joshuastevenson/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice'
        if Path(soffice).exists():
            with tempfile.TemporaryDirectory(prefix='lagosdata-recalc-') as temp:
                proc=subprocess.run([soffice,'--headless','--convert-to','xlsx','--outdir',temp,str(book)],capture_output=True,text=True,timeout=90)
                calc_path=Path(temp)/book.name
                if proc.returncode or not calc_path.exists():errors.append(f'LibreOffice recalculation failed: {(proc.stderr or proc.stdout).strip()}')
                else:
                    calc=load_workbook(calc_path,data_only=True,read_only=True)
                    formula_book=load_workbook(book,data_only=False,read_only=True)
                    for sheet in calc:
                        for row in sheet.iter_rows():
                            for cell in row:
                                if isinstance(cell.value,str) and cell.value.startswith('#'):
                                    errors.append(f'formula error {sheet.title}!{cell.coordinate}: {cell.value}')
                    expected_kpis=[]
                    if config.pipeline=='magazine':
                        expected_kpis=[('B3',len(records)),('B4',sum(bool(r.get('phone')) for r in records)),
                            ('B5',sum(r.get('zone')=='Core catchment' for r in records)),('B6',sum(r.get('zone')=='Ring area' for r in records))]
                    else:
                        expected_kpis=[('B7',len(records)),('B8',sum(bool(r.get('phone')) for r in records)),
                            ('B9',sum(bool(r.get('website')) for r in records)),('B10',sum(bool(r.get('email')) for r in records))]
                    dashboard=calc['DASHBOARD']
                    for cell_ref,expected in expected_kpis:
                        actual=dashboard[cell_ref].value
                        formula=formula_book['DASHBOARD'][cell_ref].value
                        if actual!=expected:errors.append(f'DASHBOARD!{cell_ref} expected {expected}, got {actual}; formula {formula}')
                    calc.close();formula_book.close()
        else:errors.append('LibreOffice is unavailable; workbook formulas were not recalculated')
    manifest=root/'manifest.json'
    data={'verification_errors':errors,'records':len(records),'by_area':dict(Counter(r.get('area','') for r in records)),
          'by_source':dict(Counter(r.get('source','') for r in records)),'by_group':dict(Counter(r.get('group','') for r in records)),
          'with_phone':sum(bool(r.get('phone')) for r in records),'with_website':sum(bool(r.get('website')) for r in records),
          'with_email':sum(bool(r.get('email')) for r in records),'score_basis':dict(Counter(r.get('score_basis','') for r in records))}
    if manifest.exists():
        try:data={**json.loads(manifest.read_text(encoding='utf-8')),'verification':data}
        except json.JSONDecodeError:pass
    manifest.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
    if errors: raise ValueError('verification failed:\n'+'\n'.join(errors))
    return {'records':len(records),'errors':errors}
