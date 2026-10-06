"""Flatten raw sweep, assign areas, drop out-of-area rows and ones already in the master. Writes candidates.json."""
import json, re, math, sys
import openpyxl
ROOT='/home/user/lagos-business-data-v2/'
CENT={ # area: (lat,lng,max_km)
 'Lekki Phase 1':(6.4295,3.4506,3.2),'Surulere':(6.4831,3.3609,3.2),'Victoria Island':(6.4316,3.4204,3.0),
 'Ikoyi':(6.4548,3.4298,3.2),'Lekki / Ajah corridor':(6.4530,3.5579,3.5),'Yaba':(6.4892,3.3460,3.2),
 'Ikeja':(6.6018,3.3515,3.5),'Maryland / Mende':(6.5723,3.3672,2.2),'Ajah':(6.4700,3.6150,3.2),
 'Apapa':(6.4489,3.3594,3.0),'Lekki Phase 2':(6.4400,3.5200,2.2)}
def km(a,b,la,lo): return math.hypot((a-la)*110.57,(b-lo)*110.32*math.cos(math.radians(la)))
def area_of(lat,lng):
    best=min(((km(lat,lng,c[0],c[1])/c[2],n) for n,c in CENT.items()))
    return best[1] if best[0]<=1 else None
def chij(url):
    m=re.search(r'!19s(ChI[\w-]+)',url or '') or re.search(r'place_id:(ChI[\w-]+)',url or '')
    return m.group(1) if m else ''
def norm(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
def parse(r):
    lab=re.sub('[-]','',r.get('label') or '')
    return dict(name=r['name'].strip(),place_id=chij(r['maps']) or r['place_id'],hex_id=r['place_id'],lat=r['lat'],lng=r['lng'],
                rating=r['rating'],reviews=r['reviews'],phone=(r['phone'] or '').strip(),maps=r['maps'],blurb=lab)
def main():
    wb=openpyxl.load_workbook(ROOT+'data/Lagos_Business_Data_MASTER_DATABASE_v4.xlsx',read_only=True)
    ws=wb['MASTER DATABASE']; master_ids={}; master_name_xy=[]; basic=[]
    for r in ws.iter_rows(min_row=2,values_only=True):
        c=chij(r[12])
        meta=(r[0],r[26],r[34])
        if c: master_ids[c]=meta
        if r[16] and r[17]: master_name_xy.append((norm(r[1]),float(r[16]),float(r[17]),meta,c))
        if r[26]=='Delivery Prospects' and r[34] and str(r[34]).startswith('Basic'): basic.append(dict(key=c or f'row{r[0]}',place_id=c,maps=r[12],name=r[1],master_id=r[0]))
    seen={}; terms={}
    for line in open(ROOT+'out/expand/raw.jsonl'):
        d=json.loads(line)
        for r in d['rows']:
            if r['lat']=='' or r['lng']=='' or not r['name']: continue
            p=parse(r); k=p['place_id'] or p['hex_id']
            terms.setdefault(k,set()).add(d['job']['term'])
            if k not in seen: seen[k]=p
    out=[];dropped=dict(area=0,in_master=0)
    for k,p in seen.items():
        a=area_of(p['lat'],p['lng'])
        if not a: dropped['area']+=1; continue
        p['area']=a; p['terms']=sorted(terms[k]); p['key']=k
        mid=None
        if p['place_id'] in master_ids: mid=master_ids[p['place_id']]
        else:
            for nn,la,lo,i,c in master_name_xy:
                if nn==norm(p['name']) and abs(la-p['lat'])<0.0006 and abs(lo-p['lng'])<0.0006: mid=i;break
        p['in_master']=bool(mid); p['master']=mid; 
        if mid: dropped['in_master']+=1
        out.append(p)
    json.dump(basic,open(ROOT+'out/expand/basic_rows.json','w'))
    json.dump(out,open(ROOT+'out/expand/candidates.json','w'))
    print(len(seen),'unique;',len(out),'in target areas;',dropped)
    import collections; print(collections.Counter(p['area'] for p in out if not p['in_master']))
main()
