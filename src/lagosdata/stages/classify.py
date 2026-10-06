from ..classify import classify
from ..taxonomy import normalise
from ..normalise import clean_phone

def classify_records(records):
    for row in records:
        row['phone']=clean_phone(row.get('phone',''))
        row['phones_all']=row.get('phones_all') or row['phone']
        group,sub=classify(row.get('label',''),row.get('name','')); row['group'],row['sub']=group,sub
        row['legacy18']=row.get('legacy18') or normalise(row.get('label',''),row.get('name',''))
        row.setdefault('sources_all',[row.get('source','')] if row.get('source') else [])
    return records
